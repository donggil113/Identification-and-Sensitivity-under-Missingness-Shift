"""Derived re-aggregation (v4.1 math review): existence of a VALID law in
settings B/D for every frozen B/D row of P2-FR2 (E0 truth) and P2-PILOT-CLEAN1.

    PYTHONPATH=src python3 scripts/derive_validity_eta.py

Raw files are read only.  Output: results/derived/p2_validity_eta.json.
A row with eta_max == 0 has an empty valid set: the LP interval is the closure
of nothing and the information refutes M_cc(Gamma); its sign category is
replaced by EMPTY_VALID.
"""
import json, os, sys, time
from fractions import Fraction as Q

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src")); sys.path.insert(0, os.path.join(ROOT, "scripts"))
from run_p2_first_run import build_scenario, build_envs
from run_p2_clean1 import parse_label_strict, canonical_key, split_clean
from msid.pilot import parse_adult, entity_key, coarse_x, TableModels, loss_tables, mask_probability
from msid.finite_model import FiniteJoint, all_x
from msid.observation import build, truth_from_policy, required_positive_rhos, valid_set_eta, gamma_min_closed_form, gamma_cc_squared
from msid.io_utils import frac

t0, c0 = time.time(), time.process_time()
pg = lambda s: s if s in ("SUPPORT_ONLY", "NO_MODEL") else Q(s)  # noqa: E731
out = {"what": "max eta over the whole LP feasible set with every definition-required rho >= eta (B: rho_full; D: rho_full and every given stratum)", "rows": []}

def rows_for(tag, truth, D, grid):
    g2, reason = gamma_min_closed_form(truth)
    gt = gamma_cc_squared(truth)
    out.setdefault("gamma_thresholds", {})[tag] = {
        "gamma_min_obs_squared": frac(g2), "gamma_min_obs": (float(g2) ** 0.5 if g2 is not None else None),
        "gamma_true_squared": frac(gt), "gamma_true": (float(gt) ** 0.5 if gt is not None else None),
        "note": reason or "closed form for settings C and D (same value); Gamma_min(o) <= Gamma_true"}
    for s in ("B_cc_only", "D_conditionals"):
        for g in grid:
            b = build(truth, s, pg(g))
            eta, ok = valid_set_eta(b, required_positive_rhos(b, s))
            out["rows"].append({"source": tag, "setting": s, "gamma_cc": g, "eta_max": frac(eta), "certified": ok,
                                "valid_set": "EMPTY" if eta == 0 else "NONEMPTY"})

cfg1 = json.load(open(os.path.join(ROOT, "configs", "p2_first_run.json")))
J1, _, _, q1, _, _, D1 = build_scenario(cfg1)
rows_for("P2-FR2:E0_MCAR", truth_from_policy(J1, build_envs(cfg1, J1, q1)["E0_MCAR"]), D1,
         json.load(open(os.path.join(ROOT, "configs", "p2_fr2.json")))["gamma_grid"])

cfg = json.load(open(os.path.join(ROOT, "configs", "p2_clean1.json"))); pcfg = json.load(open(os.path.join(ROOT, "configs", "p2_pilot.json")))
lines = []
for f in pcfg["data"]["files"]:
    lines += open(os.path.join(ROOT, pcfg["data"]["local_dir"], f), encoding="utf-8", errors="replace").read().splitlines()
seen, members = set(), []
for r in parse_adult(lines):
    k = entity_key(r)
    if k not in seen:
        seen.add(k); members.append(r)
units = [(split_clean(canonical_key(r), 50), coarse_x(r, pcfg["modalities"]), parse_label_strict(r["income"], cfg["label_parsing"]["allowed"])) for r in members]
train = [(x, y) for s, x, y in units if s == "train"]; evalu = [(x, y) for s, x, y in units if s == "eval"]
d, L = 2, 3
models = TableModels(train, d, L)
n = len(evalu); cnt = {}
for x, y in evalu:
    cnt[(x, y)] = cnt.get((x, y), 0) + 1
cells = [(x, y) for x in all_x(d, L) for y in (0, 1)]
J = FiniteJoint(d=d, prob={c: Q(cnt.get(c, 0), n) for c in cells}, levels=L)
for mech, rule in pcfg["mask_rules"].items():
    pi = {}
    for (x, y) in cells:
        pr = mask_probability(rule, x, y); pi[(x, y)] = {}
        for r in J.patterns():
            v = Q(1)
            for j in range(d):
                v *= pr[j] if r[j] == 0 else 1 - pr[j]
            pi[(x, y)][r] = v
    tb = truth_from_policy(J, pi)
    _, _, D = loss_tables(models, J)
    rows_for(f"P2-PILOT-CLEAN1:{mech}", tb, D, cfg["gamma_grid"])
out["timing"] = {"wall_s": round(time.time() - t0, 2), "cpu_s": round(time.process_time() - c0, 2), "threads": "one process"}
os.makedirs(os.path.join(ROOT, "results", "derived"), exist_ok=True)
json.dump(out, open(os.path.join(ROOT, "results", "derived", "p2_validity_eta.json"), "w"), indent=1)
print(json.dumps(out["gamma_thresholds"], indent=1))
for r in out["rows"]:
    if r["valid_set"] == "EMPTY":
        print("EMPTY valid set:", r["source"], r["setting"], r["gamma_cc"])
print(out["timing"])
