"""P2-FR2 driver: observation models A-D, sensitivity model M_cc(Gamma).

    PYTHONPATH=src timeout 120 taskset -c 0,1 python3 scripts/run_p2_fr2.py

Reuses the FR1 population, models and environments (configs/p2_first_run.json).
Writes results/raw/p2_fr2_*.json and results/raw/p2_fr2_manifest.json.
"""

from __future__ import annotations

import argparse
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
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from run_p2_first_run import (bits, build_envs, build_scenario, git_info,  # noqa: E402
                              sha256_file)
from msid.bounds import dropout_delta  # noqa: E402
from msid.finite_model import mcar_policy, observed_law  # noqa: E402
from msid.finite_sample import draw, hoeffding_box  # noqa: E402
from msid.identification import (identified_explicit_only,  # noqa: E402
                                 identified_general)
from msid.io_utils import frac, key  # noqa: E402
from msid.observation import (SETTINGS, build, gamma_cc_squared, interval,  # noqa: E402
                              truth_from_policy, truth_in_model, truth_value)
from msid.policy_sets import PolicySetSpec, build_system, policy_gamma  # noqa: E402


def pg(s):
    return s if s in ("SUPPORT_ONLY", "NO_MODEL") else Q(s)


def gk(g):
    return str(g)


def ivj(iv):
    return {"status": iv.status, "lo": frac(iv.lo), "hi": frac(iv.hi),
            "width": frac(iv.hi - iv.lo) if iv.lo is not None else None,
            "certified": iv.certified, "decision": iv.decision()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=os.path.join(ROOT, "configs", "p2_fr2.json"))
    ap.add_argument("--fr1-config", default=os.path.join(ROOT, "configs", "p2_first_run.json"))
    ap.add_argument("--out", default=os.path.join(ROOT, "results", "raw"))
    args = ap.parse_args()
    cfg = json.load(open(args.config))
    cfg1 = json.load(open(args.fr1_config))
    t_start = time.time()
    deadline = t_start + cfg["preregistration"]["budget"]["wall_seconds"] - 8
    start = datetime.now(timezone.utc).isoformat()
    commit, dirty = git_info()

    J, A, B, q, LA, LB, D = build_scenario(cfg1)
    envs = build_envs(cfg1, J, q)
    zc = cfg["structural_zero_check"]
    pz = {c: dict(row) for c, row in mcar_policy(J, q).items()}
    c0 = (bits(zc["cell_x"]), zc["cell_y"])
    full, dest = tuple([1] * J.d), bits(zc["move_full_mask_mass_to"])
    pz[c0][dest] += pz[c0][full]
    pz[c0][full] = Q(0)
    truths = {e: truth_from_policy(J, pi) for e, pi in envs.items()}
    truths[zc["id"]] = truth_from_policy(J, pz)
    grid = [pg(g) for g in cfg["gamma_grid"]]
    uncert, outputs, parts, checks = [], [], {}, {}

    def dump(name, obj):
        path = os.path.join(args.out, name)
        json.dump(obj, open(path, "w"), indent=1)
        outputs.append(os.path.relpath(path, ROOT))

    def run_iv(tag, t, s, g, table, **kw):
        iv = interval(build(t, s, g, **kw), table)
        if not iv.certified:
            uncert.append(tag)
        return iv

    # ---------------------------------------------------------------- A truths
    t0 = time.time()
    summ = {}
    for e, t in truths.items():
        g2 = gamma_cc_squared(t)
        per_mask_cc = {key(r): frac(sum((t.v[c] * D[(c, r)] for c in J.cells()), Q(0))) for r in J.patterns()}
        cc_joint = J.with_prob(t.v)
        summ[e] = {"oracle_delta_nat": frac(truth_value(t, D)),
                   "oracle_risk_A": frac(truth_value(t, LA)), "oracle_risk_B": frac(truth_value(t, LB)),
                   "mask_frequencies_rho": {key(r): frac(v) for r, v in t.rho.items()},
                   "gamma_cc_squared": frac(g2), "gamma_cc_float": (float(g2) ** 0.5 if g2 is not None else None),
                   "complete_case_dropout_delta_q": frac(dropout_delta(cc_joint, q, D)),
                   "population_dropout_delta_q": frac(dropout_delta(J, q, D)),
                   "per_mask_complete_case_delta": per_mask_cc}
    dump("p2_fr2_A_truths.json", {"experiment_id": "P2-FR2-A", "label": cfg["status_label"], "truths": summ,
                                  "note": "oracle_* use target labels and the true policy; for scoring only."})
    parts["A"] = {"status": "DONE", "seconds": round(time.time() - t0, 3)}

    # ---------------------------------------------------------------- B primary truth
    t0 = time.time()
    tp = truths[cfg["truth_primary"]]
    rows, ivs = [], {}
    for s in SETTINGS:
        for g in grid:
            jt = run_iv(f"B:{s}:{g}", tp, s, g, D)
            ra = run_iv(f"B:{s}:{g}:RA", tp, s, g, LA)
            rb = run_iv(f"B:{s}:{g}:RB", tp, s, g, LB)
            sep = None
            if ra.status == "OPTIMAL" and rb.status == "OPTIMAL":
                sep = {"lo": frac(ra.lo - rb.hi), "hi": frac(ra.hi - rb.lo), "width": frac((ra.hi - rb.lo) - (ra.lo - rb.hi))}
            ivs[(s, gk(g))] = jt
            rows.append({"setting": s, "gamma": gk(g), "joint": ivj(jt), "separate": sep,
                         "separate_over_joint_width": (float(Q(sep["width"]["exact"]) / (jt.hi - jt.lo))
                                                       if sep and jt.lo is not None and jt.hi > jt.lo else None),
                         "truth_in_model": truth_in_model(tp, g),
                         "oracle_contained": jt.contains(truth_value(tp, D))})
    nest = True
    order = ["A_oracle_w", "C_cc_plus_unlab", "D_conditionals", "B_cc_only"]
    for g in grid:
        chain = [ivs[(s, gk(g))] for s in order]
        for a, b in zip(chain, chain[1:]):
            nest &= a.status == "OPTIMAL" and b.lo <= a.lo and a.hi <= b.hi
    for s in SETTINGS:
        chain = [ivs[(s, gk(g))] for g in grid]
        for a, b in zip(chain, chain[1:]):
            nest &= b.lo <= a.lo and a.hi <= b.hi
    checks["nesting_information_and_gamma"] = "PASS" if nest else "FAIL"
    dump("p2_fr2_B_primary.json", {"experiment_id": "P2-FR2-B", "truth": cfg["truth_primary"], "rows": rows})
    parts["B"] = {"status": "DONE", "seconds": round(time.time() - t0, 3)}

    # ---------------------------------------------------------------- C secondary truths
    t0 = time.time()
    sec, viol, cstatus = [], 0, "DONE"
    for e, t in truths.items():
        if e == zc["id"]:
            continue
        for s in cfg["truth_secondary_settings"]:
            for g in grid:
                if time.time() > deadline - 40:
                    cstatus = "PARTIAL"
                    break
                iv = run_iv(f"C:{e}:{s}:{g}", t, s, g, D)
                inm = truth_in_model(t, g)
                cont = iv.contains(truth_value(t, D))
                if inm and not cont:
                    viol += 1
                sec.append({"truth": e, "setting": s, "gamma": gk(g), "interval": ivj(iv),
                            "truth_in_model": inm, "oracle_contained": cont,
                            "oracle_delta_nat": frac(truth_value(t, D))})
    checks["truth_in_model_implies_contained"] = "PASS" if viol == 0 else f"FAIL({viol})"
    dump("p2_fr2_C_secondary.json", {"experiment_id": "P2-FR2-C", "rows": sec,
                                     "note": "hand-specified environments; not a sample of mechanisms."})
    parts["C"] = {"status": cstatus, "seconds": round(time.time() - t0, 3)}

    # ---------------------------------------------------------------- D Gamma*
    t0 = time.time()
    gs_out = {}
    gcfg = cfg["gamma_star"]
    for s in gcfg["settings"]:
        def zero_in(g):
            iv = run_iv(f"D:{s}:{g}", tp, s, g, D)
            return iv.status == "OPTIMAL" and iv.lo <= 0 <= iv.hi
        if zero_in(Q(1)):
            gs_out[s] = {"status": "ZERO_AT_GAMMA_1"}
            continue
        lo, hi, status = Q(1), Q(2), "BRACKETED"
        while not zero_in(hi):
            lo, hi = hi, hi * 2
            if hi > Q(gcfg["cap"]):
                status = "ABOVE_CAP"
                break
        if status == "BRACKETED":
            for _ in range(gcfg["bisect_steps"]):
                mid = (lo + hi) / 2
                if zero_in(mid):
                    hi = mid
                else:
                    lo = mid
        gs_out[s] = {"status": status, "lo_excludes_0": frac(lo), "hi_contains_0": frac(hi) if status == "BRACKETED" else None}
    for s in ("B_cc_only", "D_conditionals"):
        iv = ivs[(s, "1")]
        gs_out[s] = {"status": "ZERO_AT_GAMMA_1" if iv.lo <= 0 <= iv.hi else "SEE_ROWS",
                     "note": "mask frequencies unknown: interval at Gamma=1 is the hull of per-mask complete-case differences (LP closure; the endpoint needing rho_full = 0 is not attained)"}
    dump("p2_fr2_D_gamma_star.json", {"experiment_id": "P2-FR2-D", "truth": cfg["truth_primary"], "gamma_star": gs_out,
                                      "note": "Gamma here is the M_cc parameter; not comparable to FR1's Gamma (different sensitivity model)."})
    parts["D"] = {"status": "DONE", "seconds": round(time.time() - t0, 3)}

    # ---------------------------------------------------------------- E structural zero
    t0 = time.time()
    tz = truths[zc["id"]]
    zrows = []
    for s in ("A_oracle_w", "C_cc_plus_unlab"):
        for g in (Q(2), Q(1000), "SUPPORT_ONLY", "NO_MODEL"):
            iv = run_iv(f"E:{s}:{g}", tz, s, g, D)
            zrows.append({"setting": s, "gamma": gk(g), "interval": ivj(iv), "truth_in_model": truth_in_model(tz, g),
                          "oracle_contained": iv.contains(truth_value(tz, D))})
    sv_ok = (not truth_in_model(tz, Q(1000))) and (not truth_in_model(tz, "SUPPORT_ONLY")) and truth_in_model(tz, "NO_MODEL")
    sv_ok &= all(r["oracle_contained"] for r in zrows if r["gamma"] == "NO_MODEL")
    checks["structural_zero_support_vs_gamma_limit"] = "PASS" if sv_ok else "FAIL"
    dump("p2_fr2_E_structural_zero.json", {"experiment_id": "P2-FR2-E", "check": zc, "gamma_cc_squared": frac(gamma_cc_squared(tz)),
                                           "rows": zrows})
    parts["E"] = {"status": "DONE", "seconds": round(time.time() - t0, 3)}

    # ---------------------------------------------------------------- F finite sample
    t0 = time.time()
    fs = cfg["finite_sample"]
    frows, fstatus, box_ok = [], "DONE", True
    for n in fs["n"]:
        rng = random.Random(fs["seed"] + n)
        for d in range(fs["draws_per_n"]):
            if time.time() > deadline - 12:
                fstatus = "PARTIAL"
                break
            counts = draw(tp, n, rng)
            eps, tb, ob, pt, po = hoeffding_box(counts, n, float(fs["alpha"]))
            truth_in_box = all(tb[c][0] <= tp.theta[c] <= tb[c][1] for c in tb) and \
                all(ob[k][0] <= tp.obs[k] <= ob[k][1] for k in ob)
            for g in fs["gammas"]:
                g = pg(g)
                plug = run_iv(f"F:{n}:{d}:{g}:plug", tp, fs["setting"], g, D,
                              theta_box={c: (v, v) for c, v in pt.items()},
                              obs_box={k: (v, v) for k, v in po.items()})
                outer = run_iv(f"F:{n}:{d}:{g}:outer", tp, fs["setting"], g, D, theta_box=tb, obs_box=ob)
                pop = ivs[(fs["setting"], gk(g))]
                if truth_in_box:
                    box_ok &= outer.status == "OPTIMAL" and outer.lo <= pop.lo and pop.hi <= outer.hi
                frows.append({"n": n, "draw": d, "gamma": gk(g), "eps": eps, "truth_in_box": truth_in_box,
                              "plug_in": ivj(plug), "outer_ci": ivj(outer), "population": ivj(pop)})
    checks["outer_ci_contains_population_when_box_holds"] = "PASS" if box_ok else "FAIL"
    dump("p2_fr2_F_finite_sample.json", {"experiment_id": "P2-FR2-F", "config": fs, "rows": frows,
                                         "note": "Two draws per n are illustrations; coverage is argued (paper prop:outer, Outer confidence interval), not estimated."})
    parts["F"] = {"status": fstatus, "seconds": round(time.time() - t0, 3)}

    # ---------------------------------------------------------------- G criterion audit on FR1 systems
    t0 = time.time()
    audit = []
    e1p = envs["E1p_self_x2"]
    cases = [("pattern", Q(1), None), ("pattern", Q(2), None),
             ("observed_law(E1p)", policy_gamma(e1p, q), observed_law(J, e1p)),
             ("observed_law(E1p)", Q(2), observed_law(J, e1p))]
    for name, g, law in cases:
        if time.time() > deadline - 3:
            break
        spec = PolicySetSpec(q=q, gamma=g, kind="observed_law" if law else "pattern", target_observed=law)
        sysm = build_system(J, spec)
        gv = [J.prob[c] * D[(c, r)] for (c, r) in sysm.var_index]
        from msid.bounds import joint_interval
        iv = joint_interval(J, spec, D)
        audit.append({"set": name, "gamma": gk(g), "width_zero": iv.width == 0, "width": frac(iv.width),
                      "explicit_rowspace_test": identified_explicit_only(sysm.A, gv),
                      "general_test": identified_general(sysm.A, sysm.b, sysm.lower, sysm.upper, gv)})
    checks["general_criterion_matches_width"] = "PASS" if all(a["general_test"] == a["width_zero"] for a in audit) else "FAIL"
    dump("p2_fr2_G_criterion_audit.json", {"experiment_id": "P2-FR2-G", "rows": audit,
                                           "note": "explicit_rowspace_test needs the relative-interior assumption; general_test adds constant coordinates."})
    parts["G"] = {"status": "DONE" if len(audit) == len(cases) else "PARTIAL", "seconds": round(time.time() - t0, 3)}

    checks["all_lps_certified"] = "PASS" if not uncert else f"FAIL({len(uncert)})"
    man = {"experiment_id": cfg["experiment_id"], "label": cfg["status_label"],
           "config": os.path.relpath(args.config, ROOT), "config_sha256": sha256_file(args.config),
           "fr1_config_sha256": sha256_file(args.fr1_config),
           "git_commit_at_run": commit, "git_tracked_code_dirty_at_run": dirty,
           "python": sys.version.split()[0], "platform": platform.platform(),
           "cpu_affinity_count": len(os.sched_getaffinity(0)), "start_utc": start,
           "end_utc": datetime.now(timezone.utc).isoformat(), "wall_seconds": round(time.time() - t_start, 3),
           "parts": parts, "engineering_checks": checks, "uncertified_lps": uncert[:20],
           "outputs": {p: sha256_file(os.path.join(ROOT, p)) for p in outputs},
           "software": "Python standard library only; msid package in this repository"}
    json.dump(man, open(os.path.join(args.out, "p2_fr2_manifest.json"), "w"), indent=1)
    print(json.dumps({"wall": man["wall_seconds"], "parts": parts, "checks": checks}, indent=1))


if __name__ == "__main__":
    main()
