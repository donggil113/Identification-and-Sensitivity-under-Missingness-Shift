"""P2-PILOT1 driver (semi-synthetic, one public dataset).

    PYTHONPATH=src timeout 120 taskset -c 0,1 python3 scripts/run_p2_pilot.py \
        --data-dir data/external/adult [--out results/raw] [--tag pilot]

Nothing is downloaded by this script.  With --pipeline-test it runs on a
generated fake file instead (engineering check only; outputs go to --out).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import random
import sys
import time
from datetime import datetime, timezone
from fractions import Fraction as Q

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from msid.environments import independent_dropout  # noqa: E402
from msid.finite_sample import draw as _unused  # noqa: E402,F401
from msid.finite_sample import hoeffding_box  # noqa: E402
from msid.io_utils import frac, key  # noqa: E402
from msid.observation import (build, classify_sign, gamma_cc_squared, interval,  # noqa: E402
                              truth_value)
from msid.pilot import (TableModels, assert_fixed_loss, coarse_x,  # noqa: E402
                        complete_case_dropout, draw_masks, finite_population_truth,
                        held_out_delta, label, loss_tables, parse_adult, split_of)


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def fake_lines(n, seed=1):
    rng = random.Random(seed)
    out = []
    for i in range(n):
        edu = rng.randint(1, 16)
        hrs = rng.randint(10, 80)
        y = ">50K" if rng.random() < (0.1 + 0.03 * edu + 0.003 * hrs) else "<=50K"
        out.append(f"{rng.randint(17, 90)}, Private, {rng.randint(10000, 999999)}, X, {edu}, M, O, R, W, S, 0, 0, {hrs}, C{i % 7}, {y}")
    return out


def pg(s):
    return s if s in ("SUPPORT_ONLY", "NO_MODEL") else Q(s)


def ivj(iv):
    return {"status": iv.status, "lo": frac(iv.lo), "hi": frac(iv.hi), "certified": iv.certified,
            "category": classify_sign(iv.lo, iv.hi)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=os.path.join(ROOT, "configs", "p2_pilot.json"))
    ap.add_argument("--data-dir", default=None)
    ap.add_argument("--out", default=os.path.join(ROOT, "results", "raw"))
    ap.add_argument("--pipeline-test", action="store_true")
    args = ap.parse_args()
    cfg = json.load(open(args.config))
    t0 = time.time()
    deadline = t0 + cfg["preregistration"]["budget"]["wall_seconds"] - 6
    os.makedirs(args.out, exist_ok=True)

    if args.pipeline_test:
        lines = fake_lines(4000)
        data_hashes = {"FAKE": "generated"}
        tag = "pipelinetest"
    else:
        lines, data_hashes = [], {}
        for f in cfg["data"]["files"]:
            p = os.path.join(args.data_dir, f)
            data_hashes[f] = sha(p)
            lines += open(p, encoding="utf-8", errors="replace").read().splitlines()
        tag = "pilot"
    rows = parse_adult(lines)
    mods, L, d = cfg["modalities"], cfg["levels"], len(cfg["modalities"])

    # entity split, dedup within split by entity key (one unit per entity)
    seen, train, evalu = set(), [], []
    from msid.pilot import entity_key
    for row in rows:
        k = entity_key(row)
        if k in seen:
            continue
        seen.add(k)
        unit = (coarse_x(row, mods), label(row))
        (train if split_of(row, cfg["entity"]["train_pct"]) == "train" else evalu).append(unit)
    models = TableModels(train, d, L)
    q = independent_dropout(d, [Q(v) for v in cfg["evaluator_dropout_q"]["drop_rates"]])
    parts, uncert, results = {}, [], {}
    for mech, rule in cfg["mask_rules"].items():
        units = draw_masks(evalu, rule, cfg["mask_seed"])
        t, counts = finite_population_truth(units, d, L)
        LA, LB, D = loss_tables(models, t.joint)
        assert_fixed_loss(models, units, mods)
        n = len(units)
        full = tuple([1] * d)
        n_complete = sum(1 for _, _, r in units if r == full)
        cc_drop, _ = complete_case_dropout(units, D, q, d, L)
        held = held_out_delta(units, D)
        g2 = gamma_cc_squared(t)
        res = {"n_eval_units": n, "n_complete": n_complete,
               "mask_counts": {key(r): sum(1 for _, _, rr in units if rr == r) for r in t.joint.patterns()},
               "held_out_delta_uses_hidden_labels": frac(held),
               "held_out_category": "A_better" if held < 0 else ("B_better" if held > 0 else "tie"),
               "complete_case_dropout_delta": frac(cc_drop),
               "complete_case_dropout_category": None if cc_drop is None else ("A_better" if cc_drop < 0 else ("B_better" if cc_drop > 0 else "tie")),
               "gamma_cc_squared_of_realised_population": frac(g2),
               "empty_complete_cells": sum(1 for c in t.joint.cells() if t.theta[c] == 0),
               "identified": [], "outer_ci": []}
        for g in cfg["gamma_grid"]:
            if time.time() > deadline:
                res["identified"].append({"gamma_cc": g, "status": "NOT_RUN"})
                continue
            iv = interval(build(t, cfg["setting"], pg(g)), D)
            if not iv.certified:
                uncert.append(f"{mech}:{g}")
            res["identified"].append({"gamma_cc": g, **ivj(iv), "held_out_contained": iv.contains(held)})
        ob_counts = {("cc", c): counts.get((c, full), 0) for c in t.joint.cells()}
        for k2 in t.obs:
            r, o = k2
            ob_counts[("inc", k2)] = sum(v for (c, rr), v in counts.items() if rr == r and tuple(
                xj if rj else None for xj, rj in zip(c[0], r)) == o)
        eps, tb, obx, _, _ = hoeffding_box(ob_counts, n, float(cfg["outer_ci"]["alpha"]))
        res["hoeffding_eps"] = eps
        for g in cfg["outer_ci"]["gammas"]:
            if time.time() > deadline:
                res["outer_ci"].append({"gamma_cc": g, "status": "NOT_RUN"})
                continue
            iv = interval(build(t, cfg["setting"], pg(g), tb, obx), D)
            if not iv.certified:
                uncert.append(f"{mech}:outer:{g}")
            res["outer_ci"].append({"gamma_cc": g, **ivj(iv)})
        results[mech] = res
    man = {"experiment_id": cfg["experiment_id"], "tag": tag, "config_sha256": sha(args.config),
           "data_sha256": data_hashes, "n_rows_parsed": len(rows), "n_entities": len(seen),
           "n_train": len(train), "n_eval": len(evalu), "train_modes": models.mode,
           "python": sys.version.split()[0], "platform": platform.platform(),
           "cpu_affinity_count": len(os.sched_getaffinity(0)),
           "utc": datetime.now(timezone.utc).isoformat(), "wall_seconds": round(time.time() - t0, 2),
           "uncertified_lps": uncert, "coarsening_check": "PASS"}
    json.dump({"manifest": man, "results": results}, open(os.path.join(args.out, f"p2_{tag}_results.json"), "w"), indent=1)
    print(json.dumps(man, indent=1))
    for mech, r in results.items():
        print(mech, "held", r["held_out_delta_uses_hidden_labels"]["float"], "cc", r["complete_case_dropout_delta"]["float"] if r["complete_case_dropout_delta"] else None)
        for x in r["identified"] + r["outer_ci"]:
            print("  ", x.get("gamma_cc"), x.get("status"), x.get("lo") and round(x["lo"]["float"], 4), x.get("hi") and round(x["hi"]["float"], 4), x.get("category"))


if __name__ == "__main__":
    main()
