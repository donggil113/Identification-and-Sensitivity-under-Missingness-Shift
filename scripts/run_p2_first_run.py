"""P2 FIRST RUN driver (experiment P2-FR1).

Usage (from the repository root):
    PYTHONPATH=src timeout 120 taskset -c 0,1 python3 scripts/run_p2_first_run.py \
        --config configs/p2_first_run.json --out results/raw

Writes results/raw/p2_fr1_*.json and run_manifest.json.  Every population
number is exact (Fraction) and every LP endpoint carries an exact certificate.
Parts that do not finish inside the wall budget are recorded as NOT_RUN.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import random
import subprocess
import sys
import time
from datetime import datetime, timezone
from fractions import Fraction as Q

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from msid import __version__  # noqa: E402
from msid.bounds import (anova_interaction, closed_form_gamma,  # noqa: E402
                         closed_form_interval, dropout_delta, gamma_star,
                         interaction_mass, joint_interval, objective_in_rowspace,
                         per_pattern_differences, separate_interval)
from msid.empirical import empirical_joint, sample_counts  # noqa: E402
from msid.environments import (correlated_mcar, independent_dropout,  # noqa: E402
                               interaction_policy)
from msid.finite_model import (FiniteJoint, TableModel, bayes_under_mcar,  # noqa: E402
                               complete_case_joint, difference_table,
                               feature_missing_rates, feature_modes,
                               impute_then_predict, loss_table, mcar_policy,
                               observed_law, pattern_marginal, risk)
from msid.io_utils import frac, key, policy_json  # noqa: E402
from msid.policy_sets import (PolicySetSpec, membership, policy_gamma,  # noqa: E402
                              support_violations)


def parse_q(s):
    return None if s == "inf" else Q(s)


def gkey(g):
    return "inf" if g is None else str(g)


def bits(s):
    return tuple(int(ch) for ch in s)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def git_info():
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                         stderr=subprocess.DEVNULL).decode().strip()
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain", "--", "src", "scripts", "configs", "tests"],
                                             cwd=ROOT).decode().strip())
    except Exception:  # noqa: BLE001
        commit, dirty = None, None
    return commit, dirty


def wilson(k, n, z=1.96):
    if n == 0:
        return None
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [max(0.0, centre - half), min(1.0, centre + half)]


def iv_json(iv, with_policies=False):
    out = {"status": iv.status, "lo": frac(iv.lo), "hi": frac(iv.hi),
           "width": frac(iv.width) if iv.lo is not None else None,
           "certified": iv.certified, "sign_decision": iv.sign_decision()}
    if with_policies and iv.argmin is not None:
        out["argmin_policy"] = policy_json(iv.argmin)
        out["argmax_policy"] = policy_json(iv.argmax)
    return out


# ----------------------------------------------------------------------------


def build_scenario(cfg):
    sc = cfg["scenario"]
    d = sc["d"]
    px = {bits(k): Q(v) for k, v in sc["px"].items()}
    py = {bits(k): Q(v) for k, v in sc["py1"].items()}
    J = FiniteJoint.from_px_py1(d, px, py)
    A = bayes_under_mcar(J, name="A_dropout_bayes")
    B = impute_then_predict(J, feature_modes(J), name="B_mode_impute")
    q = independent_dropout(d, [Q(v) for v in sc["dropout_q"]["drop_rates"]])
    LA, LB = loss_table(J, A), loss_table(J, B)
    return J, A, B, q, LA, LB, difference_table(LA, LB)


def build_envs(cfg, J, q):
    envs = {}
    for e in cfg["environments"]:
        if e["type"] == "mcar":
            envs[e["id"]] = mcar_policy(J, q)
        elif e["type"] == "interaction":
            envs[e["id"]] = interaction_policy(J, q, e["s"], e["t"], Q(e["eps"]))
        elif e["type"] == "correlated_mcar":
            envs[e["id"]] = correlated_mcar(J, q, Q(e["kappa"]))
        else:
            raise ValueError(e["type"])
    return envs


class Budget:
    def __init__(self, seconds):
        self.t0 = time.time()
        self.seconds = seconds

    def elapsed(self):
        return time.time() - self.t0

    def left(self):
        return self.seconds - self.elapsed()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=os.path.join(ROOT, "configs", "p2_first_run.json"))
    ap.add_argument("--out", default=os.path.join(ROOT, "results", "raw"))
    ap.add_argument("--manifest", default=os.path.join(ROOT, "run_manifest.json"))
    args = ap.parse_args()

    with open(args.config) as f:
        cfg = json.load(f)
    budget = Budget(cfg["preregistration"]["budget"]["wall_seconds"] - 8)  # margin for writing
    start = datetime.now(timezone.utc).isoformat()
    commit, dirty = git_info()
    os.makedirs(args.out, exist_ok=True)

    J, A, B, q, LA, LB, D = build_scenario(cfg)
    grid = [parse_q(g) for g in cfg["gamma_grid"]]
    g_pre = parse_q(cfg["gamma_pre"])
    kinds = cfg["kinds"]
    envs = build_envs(cfg, J, q)
    dq = dropout_delta(J, q, D)
    true_delta = {eid: risk(J, pi, D) for eid, pi in envs.items()}

    parts = {}
    checks = {}
    outputs = []
    uncertified = []

    def dump(name, obj):
        path = os.path.join(args.out, name)
        with open(path, "w") as f:
            json.dump(obj, f, indent=1)
        outputs.append(os.path.relpath(path, ROOT))

    def note_cert(tag, iv):
        if iv.status == "OPTIMAL" and not iv.certified:
            uncertified.append(tag)
        if iv.status == "INFEASIBLE" and not iv.certified:
            uncertified.append(tag)

    # ------------------------------------------------------------------ A
    t = time.time()
    scen = {
        "experiment_id": "P2-FR1-A",
        "what": "Population scenario, fixed models, artificial dropout law q, and hand-specified deployment policies with identical full-data law.",
        "full_data_law": {f"x={key(c[0])},y={c[1]}": frac(p) for c, p in J.prob.items()},
        "dropout_q_artificial_mask_M": {key(r): frac(v) for r, v in q.items()},
        "model_A": {key(o): frac(p) for o, p in A.table.items()},
        "model_B": {key(o): frac(p) for o, p in B.table.items()},
        "loss": "brier",
        "delta_random_dropout": frac(dq),
        "per_pattern_delta": {key(r): frac(v) for r, v in per_pattern_differences(J, D).items()},
        "risk_A_dropout": frac(risk(J, mcar_policy(J, q), LA)),
        "risk_B_dropout": frac(risk(J, mcar_policy(J, q), LB)),
        "environments": {},
    }
    for eid, pi in envs.items():
        cc = complete_case_joint(J, pi)
        scen["environments"][eid] = {
            "policy_natural_mask_R": policy_json(pi),
            "pattern_marginal_equals_q": pattern_marginal(J, pi) == q,
            "feature_missing_rates": [frac(v) for v in feature_missing_rates(J, pi)],
            "policy_gamma_vs_q": frac(policy_gamma(pi, q)),
            "oracle_delta_uses_target_labels": frac(true_delta[eid]),
            "oracle_risk_A": frac(risk(J, pi, LA)),
            "oracle_risk_B": frac(risk(J, pi, LB)),
            "complete_case_random_dropout_delta": frac(dropout_delta(cc, q, D)) if cc else None,
        }
    dump("p2_fr1_A_scenario.json", scen)
    parts["A"] = {"status": "DONE", "seconds": round(time.time() - t, 3)}

    # ------------------------------------------------------------------ B
    t = time.time()
    rows = []
    for g in grid:
        for kind in kinds:
            spec = PolicySetSpec(q=q, gamma=g, kind=kind)
            jt = joint_interval(J, spec, D)
            sep = separate_interval(J, spec, LA, LB)
            note_cert(f"B:{kind}:{gkey(g)}:joint", jt)
            note_cert(f"B:{kind}:{gkey(g)}:separate", sep)
            in_set = {eid: membership(J, spec, pi).in_set for eid, pi in envs.items()}
            vals_in = [true_delta[e] for e, ok in in_set.items() if ok]
            row = {
                "gamma": gkey(g), "kind": kind,
                "joint": iv_json(jt, with_policies=(g == g_pre and kind == "pattern")),
                "separate": iv_json(sep),
                "separate_over_joint_width": (float(sep.width / jt.width) if jt.width else None),
                "scenario_grid_all": [frac(min(true_delta.values())), frac(max(true_delta.values()))],
                "scenario_grid_in_set": [frac(min(vals_in)), frac(max(vals_in))] if vals_in else None,
                "envs_in_set": in_set,
            }
            if kind == "pattern" and g is not None:
                cf = closed_form_interval(J, q, D, g)
                row["closed_form"] = iv_json(cf)
            rows.append(row)
    obs_rows = []
    for eid, pi in envs.items():
        law = observed_law(J, pi)
        for g in grid:
            spec = PolicySetSpec(q=q, gamma=g, kind="observed_law", target_observed=law)
            iv = joint_interval(J, spec, D)
            note_cert(f"B:obs:{eid}:{gkey(g)}", iv)
            obs_rows.append({"env": eid, "gamma": gkey(g), "interval": iv_json(iv),
                             "true_policy_in_set": membership(J, spec, pi).in_set,
                             "oracle_delta": frac(true_delta[eid]),
                             "oracle_delta_contained": iv.contains(true_delta[eid])})
    dump("p2_fr1_B_intervals.json", {
        "experiment_id": "P2-FR1-B",
        "what": "Joint (same unknown policy) vs separate vs closed-form vs scenario-grid ranges; population-exact.",
        "delta_random_dropout": frac(dq),
        "rows": rows,
        "observed_law_rows": obs_rows,
        "note": "scenario_grid_* are min/max over the hand-specified environments only (inner approximations when in the set); they are not frequencies.",
    })
    parts["B"] = {"status": "DONE", "seconds": round(time.time() - t, 3)}

    # ------------------------------------------------------------------ C
    t = time.time()
    iv_by = {(r["gamma"], r["kind"]): r["joint"] for r in rows}
    # Gamma = 1
    g1_ok = all(iv_by[("1", k)]["lo"] == frac(dq) and iv_by[("1", k)]["hi"] == frac(dq) for k in kinds)
    mcar_law = observed_law(J, mcar_policy(J, q))
    ob1 = joint_interval(J, PolicySetSpec(q=q, gamma=Q(1), kind="observed_law", target_observed=mcar_law), D)
    g1_ok = g1_ok and ob1.lo == dq and ob1.hi == dq
    checks["gamma_one_point_equals_dropout_delta"] = "PASS" if g1_ok else "FAIL"

    # Nesting in Gamma and in constraint strength
    def exact_iv(g, kind):
        return joint_interval(J, PolicySetSpec(q=q, gamma=g, kind=kind), D)
    ivs = {(gkey(g), k): exact_iv(g, k) for g in grid for k in kinds}
    nest_ok = True
    order = [gkey(g) for g in grid]
    for k in kinds:
        for a, b in zip(order, order[1:]):
            x, y = ivs[(a, k)], ivs[(b, k)]
            nest_ok &= (y.lo <= x.lo and x.hi <= y.hi)
    for g in grid:
        chain = [joint_interval(J, PolicySetSpec(q=q, gamma=g, kind="observed_law", target_observed=mcar_law), D)]
        chain += [ivs[(gkey(g), k)] for k in ("pattern", "feature", "none")]
        for inner, outer in zip(chain, chain[1:]):
            nest_ok &= (outer.lo <= inner.lo and inner.hi <= outer.hi)
    checks["nesting_gamma_and_constraint_strength"] = "PASS" if nest_ok else "FAIL"

    # Membership => containment over every (env, Gamma, kind) cell of the grid
    table = []
    impl_viol = 0
    for eid, pi in envs.items():
        for g in grid:
            for k in kinds:
                spec = PolicySetSpec(q=q, gamma=g, kind=k)
                m = membership(J, spec, pi)
                iv = ivs[(gkey(g), k)]
                cont = iv.contains(true_delta[eid])
                if m.in_set and not cont:
                    impl_viol += 1
                table.append({"env": eid, "gamma": gkey(g), "kind": k, "in_set": m.in_set,
                              "contained": cont, "first_violation": m.violations[0] if m.violations else None})
    for r in obs_rows:
        if r["true_policy_in_set"] and not r["oracle_delta_contained"]:
            impl_viol += 1
    checks["membership_implies_containment"] = "PASS" if impl_viol == 0 else f"FAIL({impl_viol})"
    counts = {"in_set": sum(r["in_set"] for r in table),
              "not_in_set_contained": sum((not r["in_set"]) and r["contained"] for r in table),
              "not_in_set_not_contained": sum((not r["in_set"]) and (not r["contained"]) for r in table)}

    # Support violation SV1
    sv = cfg["support_violation"]
    q_ex = {bits(k): Q(v) for k, v in sv["q_evaluator"].items()}
    dep = mcar_policy(J, q)  # deployment: independent dropout with primary rates
    rho = pattern_marginal(J, dep)
    sv_out = {"id": sv["id"], "q_evaluator": {key(r): frac(v) for r, v in q_ex.items()},
              "deployment_pattern_rates": {key(r): frac(v) for r, v in rho.items()},
              "support_violations": [key(r) for r in support_violations(q_ex, rho)],
              "policy_gamma_vs_q_evaluator": frac(policy_gamma(dep, q_ex)),
              "delta_dropout_q_evaluator": frac(dropout_delta(J, q_ex, D)),
              "oracle_delta_deployment": frac(risk(J, dep, D)), "rows": []}
    sv_ok = sv_out["support_violations"] == ["(0,0)"]
    for g in grid:
        for k, tgt in (("feature", None), ("pattern", rho)):
            spec = PolicySetSpec(q=q_ex, gamma=g, kind=k, target_pattern=tgt)
            iv = joint_interval(J, spec, D)
            note_cert(f"C:SV1:{k}:{gkey(g)}", iv)
            m = membership(J, spec, dep)
            sv_out["rows"].append({"gamma": gkey(g), "kind": k,
                                   "target": "deployment pattern rates" if tgt else "q_evaluator feature rates",
                                   "interval": iv_json(iv), "deployment_in_set": m.in_set,
                                   "oracle_delta_contained": iv.contains(risk(J, dep, D))})
            if g is not None:
                sv_ok &= not m.in_set
                if k == "pattern":
                    sv_ok &= iv.status == "INFEASIBLE" and iv.certified
            elif k == "pattern":
                sv_ok &= iv.status == "OPTIMAL" and m.in_set
    checks["support_violation_flagged_and_infeasible_reported"] = "PASS" if sv_ok else "FAIL"
    dump("p2_fr1_C_checks.json", {"experiment_id": "P2-FR1-C", "checks": dict(checks),
                                  "membership_table": table,
                                  "membership_counts_over_hand_grid": counts,
                                  "support_violation": sv_out,
                                  "note": "counts are over the hand-specified (env, Gamma, kind) grid only; they are not frequencies of any real-world event."})
    parts["C"] = {"status": "DONE", "seconds": round(time.time() - t, 3)}

    # ------------------------------------------------------------------ D
    t = time.time()
    dq_, dint = anova_interaction(J, q, D)
    d_add = {k: D[k] - dint[k] for k in D}
    kappa = Q(cfg["controls"]["C2_constant_shift_B"]["kappa"])
    B_shift = TableModel("B_shift", {o: p + kappa for o, p in A.table.items()})
    d_shift = difference_table(LA, loss_table(J, B_shift))
    rank_rows = []
    rank_ok = True
    for name, DD in (("primary_brier", D), ("C1_additive", d_add), ("C2_constant_shift", d_shift)):
        for g in (Q(3, 2), g_pre, None):
            for k in ("none", "feature", "pattern", "observed_law"):
                spec = PolicySetSpec(q=q, gamma=g, kind=k,
                                     target_observed=mcar_law if k == "observed_law" else None)
                iv = joint_interval(J, spec, DD)
                note_cert(f"D:{name}:{k}:{gkey(g)}", iv)
                in_rs = objective_in_rowspace(J, spec, DD)
                consistent = (in_rs == (iv.width == 0))
                rank_ok &= consistent  # Prop. 2 applies: 0 < q < 1 lies strictly inside every box
                rank_rows.append({"D": name, "gamma": gkey(g), "kind": k, "objective_in_rowspace": in_rs,
                                  "interval": iv_json(iv), "prop2_consistent": consistent})
    checks["prop2_rank_condition_matches_lp_width"] = "PASS" if rank_ok else "FAIL"

    cx = cfg["counterexample_d1"]
    J1 = FiniteJoint.from_px_py1(1, {bits(k): Q(v) for k, v in cx["px"].items()},
                                 {bits(k): Q(v) for k, v in cx["py1"].items()})
    A1, B1 = bayes_under_mcar(J1), impute_then_predict(J1, feature_modes(J1))
    D1 = difference_table(loss_table(J1, A1), loss_table(J1, B1))
    q1 = independent_dropout(1, [Q(v) for v in cx["dropout_q"]["drop_rates"]])
    law1 = observed_law(J1, mcar_policy(J1, q1))
    iv1 = joint_interval(J1, PolicySetSpec(q=q1, gamma=None, kind="observed_law", target_observed=law1), D1)
    note_cert("D:CX1", iv1)
    cx1_ok = (dropout_delta(J1, q1, D1) == Q(cx["expected_by_hand"]["delta_q"])
              and [iv1.lo, iv1.hi] == [Q(v) for v in cx["expected_by_hand"]["observed_law_interval_gamma_inf"]]
              and observed_law(J1, iv1.argmin) == law1 and observed_law(J1, iv1.argmax) == law1)
    checks["CX1_hand_values_reproduced"] = "PASS" if cx1_ok else "FAIL"

    ivx = joint_interval(J, PolicySetSpec(q=q, gamma=g_pre, kind="observed_law", target_observed=mcar_law), D)
    note_cert("D:CX2", ivx)
    cx2 = {"gamma": gkey(g_pre), "interval": iv_json(ivx, with_policies=True),
           "sign_reversal_exists_within_set": bool(ivx.lo < 0 < ivx.hi),
           "argmin_policy_gamma": frac(policy_gamma(ivx.argmin, q)),
           "argmax_policy_gamma": frac(policy_gamma(ivx.argmax, q)),
           "both_reproduce_mcar_unlabelled_law": observed_law(J, ivx.argmin) == mcar_law == observed_law(J, ivx.argmax)}
    dump("p2_fr1_D_identification.json", {
        "experiment_id": "P2-FR1-D",
        "interaction_mass_E_wq_abs_Dint": frac(interaction_mass(J, q, D)),
        "rank_test": rank_rows,
        "CX1_d1_counterexample": {"delta_q": frac(dropout_delta(J1, q1, D1)), "interval": iv_json(iv1, with_policies=True),
                                  "model_A": {key(o): frac(p) for o, p in A1.table.items()},
                                  "model_B": {key(o): frac(p) for o, p in B1.table.items()}},
        "CX2_primary_observed_law_of_mcar": cx2,
        "note": "CX1/CX2 are constructed existence examples (LP endpoints), not frequencies of ranking reversal.",
    })
    parts["D"] = {"status": "DONE", "seconds": round(time.time() - t, 3)}

    # ------------------------------------------------------------------ E
    t = time.time()
    gs_cfg = cfg["gamma_star"]
    gstars = {}
    for k in gs_cfg["kinds"] + ["observed_law"]:
        if budget.left() < 20:
            gstars[k] = {"status": "NOT_RUN", "reason": "budget"}
            continue
        gs = gamma_star(J, q, D, kind=k, cap=Q(gs_cfg["cap"]), bisect_steps=gs_cfg["bisect_steps"],
                        target_observed=mcar_law if k == "observed_law" else None)
        gstars[k] = {"status": gs.status, "bracket_lo_excludes_0": frac(gs.lo), "bracket_hi_contains_0": frac(gs.hi),
                     "lp_evaluations": gs.evaluations, "notes": gs.notes}
    gcf = closed_form_gamma(J, q, D)
    h1 = "NOT_RUN"
    if gstars.get("pattern", {}).get("status") == "BRACKETED":
        h1 = "SUPPORTED" if gcf <= Q(gstars["pattern"]["bracket_hi_contains_0"]["exact"]) else "NOT_SUPPORTED"
    dump("p2_fr1_E_gamma_star.json", {"experiment_id": "P2-FR1-E", "delta_random_dropout": frac(dq),
                                      "gamma_star": gstars, "gamma_closed_form_pattern": frac(gcf),
                                      "note": "observed_law uses the unlabelled law generated by MCAR q (deployment data that look exactly MCAR)."})
    parts["E"] = {"status": "DONE", "seconds": round(time.time() - t, 3)}

    # ------------------------------------------------------------------ F
    t = time.time()
    emp = cfg["empirical"]
    g_emp = parse_q(emp["gamma"])
    pop = joint_interval(J, PolicySetSpec(q=q, gamma=g_emp, kind=emp["kind"]), D)
    env_in = [e for e, pi in envs.items() if membership(J, PolicySetSpec(q=q, gamma=g_emp, kind=emp["kind"]), pi).in_set]
    f_out = {"experiment_id": "P2-FR1-F", "population_interval": iv_json(pop), "envs_in_population_set": env_in,
             "gamma": gkey(g_emp), "kind": emp["kind"], "seed": emp["seed"], "by_n": {}}
    f_status = "DONE"
    for n in emp["n"]:
        rng = random.Random(emp["seed"] + n)
        reps = []
        for rep in range(emp["replications"]):
            if budget.left() < 5:
                f_status = "PARTIAL"
                break
            counts = sample_counts(J, n, rng)
            Jh = empirical_joint(J, counts)
            ivh = joint_interval(Jh, PolicySetSpec(q=q, gamma=g_emp, kind=emp["kind"]), D)
            note_cert(f"F:n={n}:rep={rep}", ivh)
            reps.append({
                "lo": float(ivh.lo), "hi": float(ivh.hi),
                "contains_population_interval": bool(ivh.lo <= pop.lo and pop.hi <= ivh.hi),
                "contains_oracle": {e: bool(ivh.lo <= true_delta[e] <= ivh.hi) for e in env_in},
                "sign_decision": ivh.sign_decision(),
                "zero_count_cells": sum(1 for v in counts.values() if v == 0),
                "delta_q_hat": float(dropout_delta(Jh, q, D)),
            })
        R = len(reps)
        k_pop = sum(r["contains_population_interval"] for r in reps)
        summ = {"replications_done": R,
                "contains_population_interval": {"k": k_pop, "R": R, "wilson95": wilson(k_pop, R)},
                "contains_oracle": {e: {"k": sum(r["contains_oracle"][e] for r in reps), "R": R,
                                        "wilson95": wilson(sum(r["contains_oracle"][e] for r in reps), R)} for e in env_in},
                "sign_decision_matches_population": sum(r["sign_decision"] == pop.sign_decision() for r in reps),
                "reps_with_empirical_support_violation": sum(r["zero_count_cells"] > 0 for r in reps),
                "lo_mean": sum(r["lo"] for r in reps) / R if R else None,
                "hi_mean": sum(r["hi"] for r in reps) / R if R else None}
        f_out["by_n"][str(n)] = {"summary": summ, "replications": reps}
    f_out["note"] = "Plug-in intervals replace the population joint by the empirical complete-data joint; they are estimates, not population sharp bounds. Models are fixed (not refit)."
    dump("p2_fr1_F_plugin.json", f_out)
    parts["F"] = {"status": f_status, "seconds": round(time.time() - t, 3)}

    # ------------------------------------------------------------------ verdicts
    checks["all_lps_certified"] = "PASS" if not uncertified else f"FAIL({len(uncertified)})"
    widths_ok = all((r["separate"]["width"]["exact"] != r["joint"]["width"]["exact"])
                    for r in rows if r["gamma"] == gkey(g_pre))
    pos_width = all(r["interval"]["width"] is not None and r["interval"]["width"]["float"] > 0
                    for r in rank_rows if r["D"] == "primary_brier" and r["gamma"] != "inf")
    h3 = "SUPPORTED" if (pos_width and rank_ok) else "NOT_SUPPORTED"
    hyp = {
        "H-ENG": "PASS" if all(v == "PASS" for v in checks.values()) else "FAIL",
        "H1": h1,
        "H2": "SUPPORTED" if widths_ok else "NOT_SUPPORTED",
        "H3": h3,
        "H4": "REPORTED (descriptive; see p2_fr1_F_plugin.json)" if parts["F"]["status"] != "NOT_RUN" else "NOT_RUN",
    }
    end = datetime.now(timezone.utc).isoformat()
    manifest = {
        "experiment_id": cfg["experiment_id"],
        "config": os.path.relpath(args.config, ROOT),
        "config_sha256": sha256_file(args.config),
        "git_commit_at_run": commit,
        "git_tracked_code_dirty_at_run": dirty,
        "msid_version": __version__,
        "python": sys.version.split()[0],
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "cpu_affinity_count": len(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else None,
        "start_utc": start, "end_utc": end,
        "wall_seconds": round(budget.elapsed(), 3),
        "budget_wall_seconds": cfg["preregistration"]["budget"]["wall_seconds"],
        "parts": parts,
        "engineering_checks": checks,
        "uncertified_lps": uncertified[:20],
        "hypotheses": hyp,
        "outputs": {p: sha256_file(os.path.join(ROOT, p)) for p in outputs},
        "data_sources": "Synthetic finite population hand-specified in the config; no external data, models or code were downloaded.",
        "software": "Python standard library only (fractions, random, json); msid package in this repository.",
        "rng": "random.Random (Mersenne Twister), seed = empirical.seed + n",
        "not_run": ["real data", "GPU training", "complete-case-source partial identification (w unknown)", "empirical observed-law plug-in (infeasibility study)"],
    }
    with open(args.manifest, "w") as f:
        json.dump(manifest, f, indent=1)
    print(json.dumps({"wall_seconds": manifest["wall_seconds"], "checks": checks, "hypotheses": hyp,
                      "parts": parts}, indent=1))


if __name__ == "__main__":
    main()
