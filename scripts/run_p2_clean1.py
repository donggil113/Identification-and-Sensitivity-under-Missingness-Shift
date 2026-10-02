"""P2-PILOT-CLEAN1: repair validation of the PILOT1 split/label defect.

    PYTHONPATH=src timeout 120 taskset -c 0,1 python3 scripts/run_p2_clean1.py

Writes results/raw/p2_clean1_models.json (before evaluation) and
results/raw/p2_clean1_results.json.  PILOT1/PILOT2 raw files are not touched.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from fractions import Fraction as Q

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from msid.environments import independent_dropout  # noqa: E402
from msid.finite_model import FiniteJoint, all_x  # noqa: E402
from msid.io_utils import frac, key  # noqa: E402
from msid.observation import (build, classify_sign, endpoint_eta, gamma_cc_squared,  # noqa: E402
                              interval, required_positive_rhos, truth_from_policy,
                              truth_value, valid_set_eta)
from msid.pilot import (ADULT_COLUMNS, TableModels, coarse_x, entity_key, label,  # noqa: E402
                        loss_tables, mask_probability, parse_adult)

NUMERIC = ["age", "education-num", "capital-gain", "capital-loss", "hours-per-week"]


def parse_label_strict(tok, allowed):
    t = tok.strip()
    if t not in allowed:
        return None
    return 1 if t.rstrip(".") == ">50K" else 0


def canonical_key(row):
    parts = []
    for c in ADULT_COLUMNS:
        if c in ("fnlwgt", "income"):
            continue
        v = row[c].strip()
        parts.append(str(int(v)) if c in NUMERIC else v)
    return "|".join(parts)


def split_clean(ck, pct):
    return "train" if int(hashlib.sha256(ck.encode()).hexdigest(), 16) % 100 < pct else "eval"


def pg(s):
    return s if s in ("SUPPORT_ONLY", "NO_MODEL") else Q(s)


def main():
    t0w, t0c = time.time(), time.process_time()
    cfg = json.load(open(os.path.join(ROOT, "configs", "p2_clean1.json")))
    pcfg = json.load(open(os.path.join(ROOT, "configs", "p2_pilot.json")))
    raw = os.path.join(ROOT, "results", "raw")
    ddir = os.path.join(ROOT, pcfg["data"]["local_dir"])
    lines, hashes = [], {}
    for f in pcfg["data"]["files"]:
        p = os.path.join(ddir, f)
        hashes[f] = hashlib.sha256(open(p, "rb").read()).hexdigest()
        lines += open(p, encoding="utf-8", errors="replace").read().splitlines()
    rows = parse_adult(lines)

    # membership: identical to PILOT1 (first occurrence per PILOT1 key)
    seen, members = set(), []
    for r in rows:
        k = entity_key(r)
        if k not in seen:
            seen.add(k)
            members.append(r)
    allowed = cfg["label_parsing"]["allowed"]
    checks, unresolved, units = {}, 0, []
    label_equiv = True
    for r in members:
        y = parse_label_strict(r["income"], allowed)
        if y is None:
            unresolved += 1
            continue
        label_equiv &= (y == label(r))
        ck = canonical_key(r)
        units.append((ck, split_clean(ck, cfg["split_key"]["train_if_below"]), coarse_x(r, pcfg["modalities"]), y))
    split_of_group = {}
    for ck, sp, _, _ in units:
        split_of_group.setdefault(ck, set()).add(sp)
    leakage = sum(1 for v in split_of_group.values() if len(v) > 1)
    labels_by_group = {}
    for ck, _, _, y in units:
        labels_by_group.setdefault(ck, []).append(y)
    multi = {k: v for k, v in labels_by_group.items() if len(v) > 1}
    checks.update({
        "membership_rows": len(members), "unresolved_labels": unresolved,
        "strict_label_equals_pilot1_label": label_equiv,
        "canonical_groups": len(split_of_group), "group_leakage_train_eval": leakage,
        "groups_with_multiple_rows": len(multi),
        "groups_with_conflicting_labels": sum(1 for v in multi.values() if len(set(v)) > 1),
        "rows_in_multi_row_groups": sum(len(v) for v in multi.values()),
        "predictor_input_columns": [m["column"] for m in pcfg["modalities"]],
        "target_or_path_in_inputs": any(c in ("income", "fnlwgt") for c in [m["column"] for m in pcfg["modalities"]]),
        "binning": "fixed thresholds from config (not estimated); mode imputation from train only",
        "unit_note": "record-profile split (canonical covariate profile); not person identity",
    })
    train = [(x, y) for _, sp, x, y in units if sp == "train"]
    evalu = [(x, y) for _, sp, x, y in units if sp == "eval"]
    checks["train_records"], checks["eval_records"] = len(train), len(evalu)
    if leakage or not label_equiv or checks["target_or_path_in_inputs"]:
        raise SystemExit(f"repair checks failed: {checks}")

    # refit once and persist BEFORE evaluation
    d, L = len(pcfg["modalities"]), pcfg["levels"]
    models = TableModels(train, d, L)
    tables = {"train_modes": models.mode,
              "counts": {key(o): [models.pos.get(o, 0), models.cnt[o]] for o in sorted(models.cnt, key=str)}}
    blob = json.dumps(tables, sort_keys=True).encode()
    tables["sha256_of_tables"] = hashlib.sha256(blob).hexdigest()
    json.dump(tables, open(os.path.join(raw, "p2_clean1_models.json"), "w"), indent=1)
    t_fit = time.time() - t0w

    # expected-mask evaluation (no new masks)
    n = len(evalu)
    cnt = {}
    for x, y in evalu:
        cnt[(x, y)] = cnt.get((x, y), 0) + 1
    cells = [(x, y) for x in all_x(d, L) for y in (0, 1)]
    J = FiniteJoint(d=d, prob={c: Q(cnt.get(c, 0), n) for c in cells}, levels=L)
    q = independent_dropout(d, [Q(v) for v in pcfg["evaluator_dropout_q"]["drop_rates"]])
    res = {}
    for mech, rule in pcfg["mask_rules"].items():
        pi = {}
        for (x, y) in cells:
            pr = mask_probability(rule, x, y)
            pi[(x, y)] = {}
            for r in J.patterns():
                v = Q(1)
                for j in range(d):
                    v *= pr[j] if r[j] == 0 else 1 - pr[j]
                pi[(x, y)][r] = v
        tb = truth_from_policy(J, pi)
        _, _, D = loss_tables(models, J)
        true_d = truth_value(tb, D)
        cc = sum((tb.v[c] * q[r] * D[(c, r)] for c in cells for r in J.patterns()), Q(0))
        g2 = gamma_cc_squared(tb)
        out = {"expected_true_delta_oracle": frac(true_d), "expected_cc_dropout_delta": frac(cc),
               "sign_relation": "same" if (true_d < 0) == (cc < 0) and (true_d > 0) == (cc > 0) else "opposite",
               "expected_gamma_cc": None if g2 is None else float(g2) ** 0.5,
               "settings": {}}
        for s in ("C_cc_plus_unlab", "B_cc_only", "D_conditionals"):
            rows_s = []
            for g in cfg["gamma_grid"]:
                b = build(tb, s, pg(g))
                iv = interval(b, D)
                row = {"gamma_cc": g, "status": iv.status, "lo": frac(iv.lo), "hi": frac(iv.hi), "certified": iv.certified}
                if iv.status == "OPTIMAL":
                    req = required_positive_rhos(b, s)
                    elo, ehi = endpoint_eta(b, D, iv.lo, req), endpoint_eta(b, D, iv.hi, req)
                    emax, _ = valid_set_eta(b, req)  # v4.1: existence of a valid law
                    valid = True if emax is None else emax > 0
                    la = None if elo[0] is None else elo[0] > 0
                    ha = None if ehi[0] is None else ehi[0] > 0
                    row.update({"eta_lo": frac(elo[0]), "eta_hi": frac(ehi[0]), "eta_max": frac(emax),
                                "category": classify_sign(iv.lo, iv.hi, la, ha, valid),
                                "expected_true_delta_contained": iv.contains(true_d)})
                else:
                    row["category"] = "INFEASIBLE"
                rows_s.append(row)
            out["settings"][s] = rows_s
        res[mech] = out
    result = {"experiment_id": cfg["experiment_id"], "label": cfg["status_label"], "data_sha256": hashes,
              "checks": checks, "models_file": "results/raw/p2_clean1_models.json",
              "models_sha256": tables["sha256_of_tables"], "expected_mask": res,
              "note": "Conditional on the clean eval records; oracle quantities use labels inside pi and are for scoring only. Not comparable as the same population to PILOT1/PILOT2 (split and fitted predictors changed).",
              "timing": {"wall_s_total": round(time.time() - t0w, 3), "cpu_s_total": round(time.process_time() - t0c, 3),
                         "wall_s_until_models_saved": round(t_fit, 3),
                         "threads": "one Python process, 2-CPU affinity"},
              "utc": datetime.now(timezone.utc).isoformat()}
    json.dump(result, open(os.path.join(raw, "p2_clean1_results.json"), "w"), indent=1)
    print(json.dumps({"checks": checks, "timing": result["timing"]}, indent=1))


if __name__ == "__main__":
    main()
