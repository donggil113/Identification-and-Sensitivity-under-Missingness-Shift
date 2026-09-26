"""Bounds on the deployment risk difference Delta(pi) = R_A(pi) - R_B(pi).

Both models are evaluated under the SAME unknown policy pi, so the joint
interval  [min_pi Delta(pi), max_pi Delta(pi)]  is computed directly as one LP
per endpoint.  It is compared with

* ``separate_interval``: [min R_A - max R_B, max R_A - min R_B], which lets the
  two models face different policies (never tighter than the joint interval);
* ``closed_form_interval``: an ANOVA/Lagrangian relaxation valid for the
  pattern-marginal set (see RESEARCH_PACKET.md, Prop. 3);
* ``scenario_range``: min/max over a finite list of hand-specified policies,
  which is an INNER approximation of the joint interval when they lie in the set.

All population-level numbers are exact given the supplied joint.  If an
empirical joint is supplied the result is a plug-in estimate, not a
population sharp bound.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

from .exact_lp import LPResult, solve_lp
from .finite_model import (FiniteJoint, LossTable, Pattern, Policy, mcar_policy,
                           risk)
from .policy_sets import PolicySetSpec, build_system, policy_from_vector

Q = Fraction


@dataclass
class Interval:
    status: str  # "OPTIMAL" or "INFEASIBLE"
    lo: Optional[Fraction] = None
    hi: Optional[Fraction] = None
    argmin: Optional[Policy] = None
    argmax: Optional[Policy] = None
    certified: bool = False
    iterations: int = 0
    notes: List[str] = field(default_factory=list)

    @property
    def width(self) -> Optional[Fraction]:
        return None if self.lo is None else self.hi - self.lo

    def contains(self, v: Fraction) -> Optional[bool]:
        if self.status != "OPTIMAL":
            return None
        return self.lo <= v <= self.hi

    def sign_decision(self) -> str:
        """'A_better' (hi < 0), 'B_better' (lo > 0) or 'undetermined'."""
        if self.status != "OPTIMAL":
            return "infeasible"
        if self.hi < 0:
            return "A_better"
        if self.lo > 0:
            return "B_better"
        return "undetermined"


def _objective(joint: FiniteJoint, sysm, table: LossTable) -> List[Fraction]:
    return [joint.prob[c] * table[(c, r)] for (c, r) in sysm.var_index]


def linear_interval(joint: FiniteJoint, spec: PolicySetSpec, table: LossTable) -> Interval:
    """[min, max] of sum_c w_c sum_r pi(r|c) table(c,r) over Pi(spec)."""
    sysm = build_system(joint, spec)
    c = _objective(joint, sysm, table)
    lo = solve_lp(c, sysm.A, sysm.b, sysm.lower, sysm.upper, sense="min")
    if lo.status != "OPTIMAL":
        return Interval(status="INFEASIBLE", certified=lo.certificate_ok,
                        iterations=lo.iterations, notes=lo.notes)
    hi = solve_lp(c, sysm.A, sysm.b, sysm.lower, sysm.upper, sense="max")
    return Interval(status="OPTIMAL", lo=lo.value, hi=hi.value,
                    argmin=policy_from_vector(sysm.var_index, lo.x),
                    argmax=policy_from_vector(sysm.var_index, hi.x),
                    certified=lo.certificate_ok and hi.certificate_ok,
                    iterations=lo.iterations + hi.iterations)


def joint_interval(joint, spec, D: LossTable) -> Interval:
    return linear_interval(joint, spec, D)


def separate_interval(joint, spec, LA: LossTable, LB: LossTable) -> Interval:
    ia = linear_interval(joint, spec, LA)
    ib = linear_interval(joint, spec, LB)
    if ia.status != "OPTIMAL" or ib.status != "OPTIMAL":
        return Interval(status="INFEASIBLE", certified=ia.certified and ib.certified)
    return Interval(status="OPTIMAL", lo=ia.lo - ib.hi, hi=ia.hi - ib.lo,
                    certified=ia.certified and ib.certified,
                    iterations=ia.iterations + ib.iterations)


# ----------------------------------------------------------------------------
# Closed-form relaxation for the pattern-marginal set
# ----------------------------------------------------------------------------

def anova_interaction(joint: FiniteJoint, q: Dict[Pattern, Fraction], D: LossTable):
    """D_int(c,r) = D - Dbar_c - Dbar_r + Dbar with weights w (cells) and q (masks).

    Returns (Delta_q, D_int).  Delta_q = sum_c sum_r w_c q_r D(c,r) is the
    random-dropout estimand.
    """
    cells = joint.cells()
    pats = joint.patterns()
    w = joint.prob
    dbar_c = {c: sum((Q(q[r]) * D[(c, r)] for r in pats), Q(0)) for c in cells}
    dbar_r = {r: sum((w[c] * D[(c, r)] for c in cells), Q(0)) for r in pats}
    dbar = sum((w[c] * dbar_c[c] for c in cells), Q(0))
    dint = {(c, r): D[(c, r)] - dbar_c[c] - dbar_r[r] + dbar for c in cells for r in pats}
    return dbar, dint


def interaction_mass(joint: FiniteJoint, q, D: LossTable) -> Fraction:
    """E_{w x q} |D_int|."""
    _, dint = anova_interaction(joint, q, D)
    return sum((joint.prob[c] * Q(q[r]) * abs(v) for (c, r), v in dint.items()), Q(0))


def closed_form_interval(joint: FiniteJoint, q, D: LossTable, gamma: Optional[Fraction]) -> Interval:
    """Outer bound for Pi(Gamma; pattern marginal = q):
        |Delta(pi) - Delta(q)| <= (Gamma - 1) * E_{w x q} |D_int|.
    Valid because |pi - q| <= (Gamma - 1) q on the box and both the row and
    column sums of w_c (pi - q) vanish (Prop. 3 in RESEARCH_PACKET.md).
    """
    dq, _ = anova_interaction(joint, q, D)
    if gamma is None:
        return Interval(status="OPTIMAL", lo=None, hi=None, notes=["unbounded (Gamma = inf)"])
    hw = (Q(gamma) - 1) * interaction_mass(joint, q, D)
    return Interval(status="OPTIMAL", lo=dq - hw, hi=dq + hw, certified=True)


def closed_form_gamma(joint, q, D: LossTable) -> Optional[Fraction]:
    """Gamma_cf = 1 + |Delta(q)| / E|D_int|: sign of Delta(q) is certified to
    transfer for every Gamma < Gamma_cf (pattern-marginal set).  None = inf."""
    dq, _ = anova_interaction(joint, q, D)
    mass = interaction_mass(joint, q, D)
    if mass == 0:
        return None
    return 1 + abs(dq) / mass


# ----------------------------------------------------------------------------
# Ranking-transfer threshold Gamma*
# ----------------------------------------------------------------------------

@dataclass
class GammaStar:
    delta_q: Fraction
    status: str  # "BRACKETED", "ABOVE_CAP", "NEVER_WITHIN_BOX", "ZERO_AT_MCAR"
    lo: Optional[Fraction] = None  # interval excludes 0 at lo
    hi: Optional[Fraction] = None  # interval contains 0 at hi
    evaluations: int = 0
    notes: List[str] = field(default_factory=list)


def gamma_star(joint: FiniteJoint, q, D: LossTable, kind: str = "pattern",
               cap: Fraction = Q(1024), bisect_steps: int = 14,
               target_pattern=None, target_feature=None,
               target_observed=None) -> GammaStar:
    """Smallest Gamma at which the joint interval over Pi(Gamma; kind) contains 0.

    Uses monotonicity of the interval in Gamma (nested sets).  Returns an exact
    bracket [lo, hi] (LP evaluated exactly at both ends), not a closed form.
    """
    dq, _ = anova_interaction(joint, q, D)
    if dq == 0:
        return GammaStar(delta_q=dq, status="ZERO_AT_MCAR", lo=Q(1), hi=Q(1))
    evals = 0
    # Note: for kind="observed_law" the set is feasible at Gamma = 1 only if the
    # target law equals the law generated by q; callers pass the MCAR law.

    def contains_zero(g):
        nonlocal evals
        evals += 1
        spec = PolicySetSpec(q=q, gamma=g, kind=kind, target_pattern=target_pattern,
                             target_feature=target_feature, target_observed=target_observed)
        iv = joint_interval(joint, spec, D)
        if iv.status != "OPTIMAL" or not iv.certified:
            raise RuntimeError(f"uncertified or infeasible LP at Gamma={g}")
        return iv.lo <= 0 <= iv.hi

    if not contains_zero(None):
        return GammaStar(delta_q=dq, status="NEVER_WITHIN_BOX", evaluations=evals,
                         notes=["interval excludes 0 even with Gamma = inf (box [0,1])"])
    lo, hi = Q(1), Q(2)
    while not contains_zero(hi):
        lo = hi
        hi = hi * 2
        if hi > cap:
            return GammaStar(delta_q=dq, status="ABOVE_CAP", lo=lo, hi=None, evaluations=evals)
    for _ in range(bisect_steps):
        mid = (lo + hi) / 2
        if contains_zero(mid):
            hi = mid
        else:
            lo = mid
    return GammaStar(delta_q=dq, status="BRACKETED", lo=lo, hi=hi, evaluations=evals)


# ----------------------------------------------------------------------------
# Identification (rank) test
# ----------------------------------------------------------------------------

def _rank(rows: List[List[Fraction]]) -> int:
    M = [list(r) for r in rows]
    rank = 0
    ncols = len(M[0]) if M else 0
    for col in range(ncols):
        piv = None
        for i in range(rank, len(M)):
            if M[i][col] != 0:
                piv = i
                break
        if piv is None:
            continue
        M[rank], M[piv] = M[piv], M[rank]
        pv = M[rank][col]
        for i in range(len(M)):
            if i != rank and M[i][col] != 0:
                f = M[i][col] / pv
                M[i] = [a - f * b for a, b in zip(M[i], M[rank])]
        rank += 1
    return rank


def objective_in_rowspace(joint: FiniteJoint, spec: PolicySetSpec, D: LossTable) -> bool:
    """True iff the objective vector g_{c,r} = w_c D(c,r) lies in the row space
    of the equality constraints of Pi(spec).  By Prop. 2 (RESEARCH_PACKET.md)
    this is equivalent to Delta being constant on Pi whenever Pi has a feasible
    point with every entry strictly inside its box (e.g. pi = q, Gamma > 1)."""
    sysm = build_system(joint, spec)
    g = _objective(joint, sysm, D)
    return _rank(sysm.A + [g]) == _rank(sysm.A)


def scenario_range(joint: FiniteJoint, policies: Dict[str, Policy], D: LossTable) -> Tuple[Fraction, Fraction]:
    vals = [risk(joint, pi, D) for pi in policies.values()]
    return min(vals), max(vals)


def per_pattern_differences(joint: FiniteJoint, D: LossTable) -> Dict[Pattern, Fraction]:
    """Delta_r = sum_c w_c D(c, r): 'everyone has mask r' stress tests."""
    return {r: sum((joint.prob[c] * D[(c, r)] for c in joint.cells()), Q(0))
            for r in joint.patterns()}


def dropout_delta(joint: FiniteJoint, q, D: LossTable) -> Fraction:
    return risk(joint, mcar_policy(joint, q), D)
