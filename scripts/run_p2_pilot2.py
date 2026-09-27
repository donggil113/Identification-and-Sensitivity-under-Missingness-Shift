"""P2-PILOT2-EXPECTED-MASK (exploratory analysis of the fixed PILOT1).

    PYTHONPATH=src timeout 120 taskset -c 0,1 python3 scripts/run_p2_pilot2.py

Writes results/raw/p2_pilot2_results.json and results/raw/p2_pilot_models_frozen.json.
Reads PILOT1/FR2 raw without modifying them.  No new masks, data or models.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from dataclasses import replace
from datetime import datetime, timezone
from fractions import Fraction as Q

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from run_p2_first_run import build_envs, build_scenario  # noqa: E402
from msid.environments import independent_dropout  # noqa: E402
from msid.finite_model import FiniteJoint  # noqa: E402
from msid.io_utils import frac, key  # noqa: E402
from msid.observation import (build, classify_sign, endpoint_eta, gamma_cc_squared,  # noqa: E402
                              interval, required_positive_rhos, truth_from_policy,
                              truth_value)
from msid.pilot import (ADULT_COLUMNS, TableModels, coarse_x, complete_case_dropout,  # noqa: E402
                        draw_masks, entity_key, held_out_delta, label, loss_tables,
                        mask_probability, parse_adult, split_of)

TIMES = {}


class Timer:
    def __init__(self, name):
        self.name = name

    def __enter__(self):
        self.w, self.c = time.time(), time.process_time()

    def __exit__(self, *a):
        TIMES[self.name] = {"wall_s": round(time.time() - self.w, 3), "cpu_s": round(time.process_time() - self.c, 3)}


def pg(s):
    return s if s in ("SUPPORT_ONLY", "NO_MODEL") else Q(s)


def main():
    cfg = json.load(open(os.path.join(ROOT, "configs", "p2_pilot2.json")))
    pcfg = json.load(open(os.path.join(ROOT, "configs", "p2_pilot.json")))
    raw = os.path.join(ROOT, "results", "raw")
    pilot1 = json.load(open(os.path.join(raw, "p2_pilot_results.json")))
    out = {"experiment_id": cfg["experiment_id"], "label": cfg["status_label"]}
    t_all = (time.time(), time.process_time())

    # ------------------------------------------------ 1. D endpoint attainment (FR2 E0)
    with Timer("D_endpoint"):
        cfg1 = json.load(open(os.path.join(ROOT, "configs", "p2_first_run.json")))
        J, _, _, q1, _, _, D1 = build_scenario(cfg1)
        tp = truth_from_policy(J, build_envs(cfg1, J, q1)["E0_MCAR"])
        rows = []
        for r in json.load(open(os.path.join(raw, "p2_fr2_B_primary.json")))["rows"]:
            if r["setting"] not in ("B_cc_only", "D_conditionals"):
                continue
            lo, hi = Q(r["joint"]["lo"]["exact"]), Q(r["joint"]["hi"]["exact"])
            b = build(tp, r["setting"], pg(r["gamma"]))
            req = required_positive_rhos(b, r["setting"])
            (elo, ok1), (ehi, ok2) = endpoint_eta(b, D1, lo, req), endpoint_eta(b, D1, hi, req)
            rows.append({"setting": r["setting"], "gamma_cc": r["gamma"], "lo": frac(lo), "hi": frac(hi),
                         "required_positive": req, "eta_lo": frac(elo), "eta_hi": frac(ehi),
                         "certified": ok1 and ok2,
                         "category": classify_sign(lo, hi, elo > 0, ehi > 0)})
        out["D_endpoint"] = {"truth": "FR2 E0_MCAR", "rows": rows,
                             "note": "B requires rho_full > 0 only; D requires rho > 0 for every stratum whose conditional law is given. v2's helper checked rho_full only."}

    # ------------------------------------------------ 2. provenance
    with Timer("provenance"):
        ddir = os.path.join(ROOT, pcfg["data"]["local_dir"])
        prov = {"files": {}}
        lines = []
        for f in pcfg["data"]["files"]:
            txt = open(os.path.join(ddir, f), encoding="utf-8", errors="replace").read().splitlines()
            rows_f = parse_adult(txt)
            prov["files"][f] = {"sha256": hashlib.sha256(open(os.path.join(ddir, f), "rb").read()).hexdigest(),
                                "raw_lines": len(txt), "blank_or_comment": sum(1 for x in txt if not x.strip() or x.strip().startswith("|")),
                                "parsed_rows": len(rows_f)}
            lines += txt
        allrows = parse_adult(lines)
        used_cols = [m["column"] for m in pcfg["modalities"]]
        prov["parsed_rows_total"] = len(allrows)
        prov["rows_with_any_question_mark"] = sum(1 for r in allrows if any(r[c] == "?" for c in ADULT_COLUMNS))
        prov["rows_with_question_mark_in_used_columns"] = sum(1 for r in allrows if any(r[c] == "?" for c in used_cols))
        prov["rows_excluded_for_missingness"] = 0
        seen, train, evalu, groups = set(), [], [], {}
        for r in allrows:
            k = entity_key(r)
            groups[k] = groups.get(k, 0) + 1
            if k in seen:
                continue
            seen.add(k)
            (train if split_of(r, pcfg["entity"]["train_pct"]) == "train" else evalu).append((coarse_x(r, pcfg["modalities"]), label(r)))
        norm = {}
        for r in allrows:
            k2 = "|".join(r[c].rstrip(".") if c == "income" else r[c] for c in ADULT_COLUMNS if c != "fnlwgt")
            norm[k2] = 1
        prov.update({"dedup_groups": len(seen), "rows_dropped_as_duplicates": len(allrows) - len(seen),
                     "groups_with_size_gt1": sum(1 for v in groups.values() if v > 1),
                     "max_group_size": max(groups.values()),
                     "groups_if_income_suffix_normalised (not used)": len(norm),
                     "train_records": len(train), "eval_records": len(evalu),
                     "unit_definition": "dedup group = identical attribute tuple excluding fnlwgt (raw income string incl. the '.' of adult.test); first occurrence kept (adult.data before adult.test). Not a verified person; no person ID exists, so person-level isolation is UNVERIFIED.",
                     "weighting": "unweighted empirical record population; fnlwgt (survey weight) ignored; deduplication changes record frequencies relative to the source files."})
        out["provenance"] = prov

    # ------------------------------------------------ 3. frozen predictors (re-derived + verified)
    with Timer("frozen_predictors"):
        d, L = len(pcfg["modalities"]), pcfg["levels"]
        models = TableModels(train, d, L)
        q = independent_dropout(d, [Q(v) for v in pcfg["evaluator_dropout_q"]["drop_rates"]])
        frozen = {"source": "re-derived deterministically from PILOT1 code/config/data",
                  "train_modes": models.mode,
                  "counts": {key(o): [models.pos.get(o, 0), models.cnt[o]] for o in models.cnt}}
        verify = {}
        for mech, rule in pcfg["mask_rules"].items():
            units = draw_masks(evalu, rule, pcfg["mask_seed"])
            from msid.pilot import finite_population_truth
            t_real, _ = finite_population_truth(units, d, L)
            _, _, Dm = loss_tables(models, t_real.joint)
            held = held_out_delta(units, Dm)
            cc, _ = complete_case_dropout(units, Dm, q, d, L)
            rec = pilot1["results"][mech]
            verify[mech] = (frac(held) == rec["held_out_delta_uses_hidden_labels"]
                            and frac(cc) == rec["complete_case_dropout_delta"])
        frozen["reproduces_pilot1_exactly"] = verify
        json.dump(frozen, open(os.path.join(raw, "p2_pilot_models_frozen.json"), "w"), indent=1)
        if not all(verify.values()):
            raise SystemExit("re-derived predictors do not reproduce PILOT1: STOP")

    # ------------------------------------------------ 4. expected-mask law and comparison
    with Timer("expected_law"):
        n = len(evalu)
        cnt = {}
        for x, y in evalu:
            cnt[(x, y)] = cnt.get((x, y), 0) + 1
        cells = [(x, y) for x in __import__("msid.finite_model", fromlist=["all_x"]).all_x(d, L) for y in (0, 1)]
        J_emp = FiniteJoint(d=d, prob={c: Q(cnt.get(c, 0), n) for c in cells}, levels=L)
        comp = {}
        for mech, rule in pcfg["mask_rules"].items():
            pi = {}
            for (x, y) in cells:
                pr = mask_probability(rule, x, y)
                pi[(x, y)] = {}
                for r in J_emp.patterns():
                    v = Q(1)
                    for j in range(d):
                        v *= pr[j] if r[j] == 0 else 1 - pr[j]
                    pi[(x, y)][r] = v
            tb = truth_from_policy(J_emp, pi)
            LA, LB, Dm = loss_tables(models, J_emp)
            full = tb.full
            # Gamma_cc: free scale (code) vs fixed scale lambda = 1
            g2 = gamma_cc_squared(tb)
            fixed = Q(1)
            for r in J_emp.patterns():
                if r == full or tb.rho[r] == 0:
                    continue
                for c in cells:
                    if tb.v[c] > 0:
                        e = (tb.p[(c, r)] / tb.rho[r]) / tb.v[c]
                        if e == 0 or fixed is None:
                            fixed = None
                        else:
                            fixed = max(fixed, e, 1 / e)
            cc_exp = sum((tb.v[c] * q[r] * Dm[(c, r)] for c in cells for r in J_emp.patterns()), Q(0))
            ident = []
            blind = replace(tb, p={k: Q(1, len(tb.p)) for k in tb.p},
                            joint=FiniteJoint(d=d, prob={c: Q(1, len(cells)) for c in cells}, levels=L))
            schema_ok = True
            for g in cfg["gamma_grid"]:
                iv = interval(build(tb, "C_cc_plus_unlab", pg(g)), Dm)
                ivb = interval(build(blind, "C_cc_plus_unlab", pg(g)), Dm)
                schema_ok &= (iv.status, iv.lo, iv.hi) == (ivb.status, ivb.lo, ivb.hi)
                ident.append({"gamma_cc": g, "status": iv.status, "lo": frac(iv.lo), "hi": frac(iv.hi),
                              "certified": iv.certified, "category": classify_sign(iv.lo, iv.hi),
                              "expected_delta_contained": iv.contains(truth_value(tb, Dm))})
            p1 = pilot1["results"][mech]
            comp[mech] = {
                "A_expected_true_delta": frac(truth_value(tb, Dm)),
                "B_expected_cc_dropout": frac(cc_exp),
                "C_identified_from_expected_observables": ident,
                "expected_gamma_cc_free_scale": (None if g2 is None else float(g2) ** 0.5),
                "expected_gamma_cc_squared": frac(g2),
                "expected_gamma_fixed_scale_lambda1": frac(fixed) if fixed else None,
                "expected_mask_rates": {key(r): frac(v) for r, v in tb.rho.items()},
                "schema_check_blinded_equal": schema_ok,
                "D_pilot1_realised": {"held_out_delta": p1["held_out_delta_uses_hidden_labels"],
                                      "cc_dropout": p1["complete_case_dropout_delta"],
                                      "realised_gamma_cc_squared": p1["gamma_cc_squared_of_realised_population"],
                                      "identified": p1["identified"], "outer_ci": p1["outer_ci"]},
                "note": "Conditional on the 22,275 eval records; oracle quantities (A, pi with labels) are for scoring only; the setting-C evaluator receives complete-case cells and incomplete observed-tuple masses only."}
        out["expected_mask_comparison"] = comp
    out["timing"] = TIMES
    out["total"] = {"wall_s": round(time.time() - t_all[0], 3), "cpu_s": round(time.process_time() - t_all[1], 3),
                    "threads": "single Python process pinned to 2 CPUs (taskset); CPU-s is process time"}
    out["utc"] = datetime.now(timezone.utc).isoformat()
    json.dump(out, open(os.path.join(raw, "p2_pilot2_results.json"), "w"), indent=1)
    print(json.dumps({"timing": TIMES, "total": out["total"]}, indent=1))


if __name__ == "__main__":
    main()
