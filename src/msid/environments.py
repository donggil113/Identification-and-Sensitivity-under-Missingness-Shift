"""Deployment policies that share the full-data law and the marginal missing rates.

``interaction_policy`` builds
    pi(r | c) = q(r) * (1 + eps * (s(c) - E_w s) * (t(r) - E_q t))
for a cell score s (e.g. the value of a feature -> MNAR self-masking, or the
label -> label-dependent missingness) and a mask score t (e.g. "feature j is
missing").  Because the centred scores have zero mean under w and q
respectively, every cell row still sums to 1 and the pattern marginal
sum_c w_c pi(r|c) equals q(r) exactly, so these environments are
indistinguishable from random dropout by their marginal missing rates.

These policies are hand-specified illustrations.  They are NOT a sample from
any distribution over real-world missingness mechanisms, so no frequency of
"ranking reversal" can be computed from them.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Callable, Dict

from .finite_model import Cell, FiniteJoint, Pattern, Policy, validate_policy

Q = Fraction


def cell_score(kind: str, joint: FiniteJoint) -> Callable[[Cell], Fraction]:
    if kind == "label":
        return lambda c: Q(c[1])
    if kind.startswith("x"):
        j = int(kind[1:]) - 1
        return lambda c: Q(c[0][j])
    raise ValueError(kind)


def mask_score(kind: str) -> Callable[[Pattern], Fraction]:
    if kind.startswith("missing_x"):
        j = int(kind[len("missing_x"):]) - 1
        return lambda r: Q(1 - r[j])
    if kind == "any_missing":
        return lambda r: Q(0 if all(r) else 1)
    raise ValueError(kind)


def interaction_policy(joint: FiniteJoint, q: Dict[Pattern, Fraction], s_kind: str,
                       t_kind: str, eps: Fraction) -> Policy:
    s = cell_score(s_kind, joint)
    t = mask_score(t_kind)
    es = sum((w * s(c) for c, w in joint.prob.items()), Q(0))
    et = sum((Q(q[r]) * t(r) for r in joint.patterns()), Q(0))
    pi: Policy = {}
    for c in joint.cells():
        pi[c] = {r: Q(q[r]) * (1 + Q(eps) * (s(c) - es) * (t(r) - et)) for r in joint.patterns()}
    errs = validate_policy(joint, pi)
    if errs:
        raise ValueError(f"eps={eps} gives an invalid policy: {errs[:3]}")
    return pi


def correlated_mcar(joint: FiniteJoint, q: Dict[Pattern, Fraction], kappa: Fraction) -> Policy:
    """d = 2 only: add kappa to (1,1) and (0,0), remove it from (1,0), (0,1).

    Keeps both per-feature missing rates, changes the pattern marginal; the
    policy is still MCAR (independent of the cell).
    """
    if joint.d != 2:
        raise ValueError("correlated_mcar is defined for d = 2")
    k = Q(kappa)
    q2 = dict(q)
    q2[(1, 1)] += k
    q2[(0, 0)] += k
    q2[(1, 0)] -= k
    q2[(0, 1)] -= k
    pi = {c: dict(q2) for c in joint.cells()}
    errs = validate_policy(joint, pi)
    if errs:
        raise ValueError(errs[:3])
    return pi


def independent_dropout(d: int, drop_rates) -> Dict[Pattern, Fraction]:
    """q(r) = prod_j p_j^{1 - r_j} (1 - p_j)^{r_j}."""
    from .finite_model import all_patterns
    out = {}
    for r in all_patterns(d):
        v = Q(1)
        for j, rj in enumerate(r):
            p = Q(drop_rates[j])
            v *= (1 - p) if rj else p
        out[r] = v
    return out
