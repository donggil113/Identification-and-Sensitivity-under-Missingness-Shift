"""Re-aggregate FR1/FR2 raw intervals with the corrected sign interpretation.

Raw files are read, never modified.  For FR2 settings B/D (where the LP admits
rho_full = 0) each endpoint's attainment by a valid model is checked with one
auxiliary exact LP; FR1 and FR2 settings A/C are closed sets whose endpoints
are attained by valid models (Prop. 1 / rho_full fixed), so no LP is needed.
Output: results/derived/p2_sign_reclassification.json
"""
import json
import os
import sys
import time
from fractions import Fraction as Q

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from run_p2_first_run import build_envs, build_scenario  # noqa: E402
from msid.observation import build, classify_sign, endpoint_attained, truth_from_policy  # noqa: E402

t0 = time.time()
raw = os.path.join(ROOT, "results", "raw")
ex = lambda v: None if v is None else Q(v["exact"])  # noqa: E731
cfg1 = json.load(open(os.path.join(ROOT, "configs", "p2_first_run.json")))
J, A, B, q, LA, LB, D = build_scenario(cfg1)
envs = build_envs(cfg1, J, q)
tp = truth_from_policy(J, envs["E0_MCAR"])

out = {"fr2_primary": [], "fr1_pattern": [], "notes": []}
for r in json.load(open(os.path.join(raw, "p2_fr2_B_primary.json")))["rows"]:
    j = r["joint"]
    lo, hi = ex(j["lo"]), ex(j["hi"])
    la = ha = None
    if lo is not None and r["setting"] in ("B_cc_only", "D_conditionals"):
        g = r["gamma"] if r["gamma"] in ("SUPPORT_ONLY", "NO_MODEL") else Q(r["gamma"])
        b = build(tp, r["setting"], g)
        la, ha = endpoint_attained(b, D, lo), endpoint_attained(b, D, hi)
    out["fr2_primary"].append({"setting": r["setting"], "gamma_cc": r["gamma"], "old_decision": j["decision"],
                               "lo_attained": la, "hi_attained": ha,
                               "category": classify_sign(lo, hi, la, ha),
                               "margin": (str(-hi) if hi is not None and hi < 0 else (str(lo) if lo is not None and lo > 0 else "0"))})
for r in json.load(open(os.path.join(raw, "p2_fr1_B_intervals.json")))["rows"]:
    if r["kind"] != "pattern":
        continue
    j = r["joint"]
    out["fr1_pattern"].append({"gamma_box": r["gamma"], "old_decision": j["sign_decision"],
                               "category": classify_sign(ex(j["lo"]), ex(j["hi"]))})
out["notes"] = ["gamma_cc (FR2, reference = complete-case law, free scale) and gamma_box (FR1, reference = dropout law q / population law w) are different parameters; do not compare their values.",
                "attained=None means the endpoint is attained by construction (closed set of valid models)."]
out["seconds"] = round(time.time() - t0, 2)
json.dump(out, open(os.path.join(ROOT, "results", "derived", "p2_sign_reclassification.json"), "w"), indent=1)
for r in out["fr2_primary"]:
    print(r["setting"][:8], r["gamma_cc"], r["old_decision"], "->", r["category"], r["lo_attained"], r["hi_attained"])
print(out["seconds"], "s")
