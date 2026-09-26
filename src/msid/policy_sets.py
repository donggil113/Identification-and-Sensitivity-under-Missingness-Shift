"""Policy sets Pi(Gamma; K) for the unknown deployment missingness policy.

Pi(Gamma; K) = { pi :  pi(. | c) is a distribution over masks for every cell c,
                       q(r)/Gamma <= pi(r | c) <= min(1, Gamma q(r))   (Gamma-box),
                       K-constraints }

* ``q`` is the evaluator's artificial dropout law (the centre of the box).
  Under a matched pattern marginal, pi(r|c)/q(r) = P(c | R=r)/P(c): Gamma
  bounds the density ratio of the full-data law inside each natural mask
  relative to the population.  Gamma is an ASSUMPTION, not identified.
* ``gamma=None`` means no box (only 0 <= pi <= 1).
* K in {"none", "feature", "pattern", "observed_law"}:
    - "feature":  sum_c w_c P(R_j = 0 | c) = target per-feature missing rate
    - "pattern":  sum_c w_c pi(r | c) = target pattern rate (default q)
    - "observed_law": sum_{c : x_r(c) = v} w_c pi(r | c) = P_obs(r, v) for all
      (r, v); this is the unlabelled deployment law and implies "pattern".

All constraints are exact population constraints for the supplied ``joint``;
passing an empirical joint turns them into plug-in constraints.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Dict, List, Optional, Tuple

from .finite_model import (Cell, FiniteJoint, Obs, Pattern, Policy, all_x,
                           observe)

Q = Fraction
KINDS = ("none", "feature", "pattern", "observed_law")


@dataclass(frozen=True)
class PolicySetSpec:
    q: Dict[Pattern, Fraction]
    gamma: Optional[Fraction]
    kind: str = "pattern"
    target_pattern: Optional[Dict[Pattern, Fraction]] = None
    target_feature: Optional[Tuple[Fraction, ...]] = None
    target_observed: Optional[Dict[Tuple[Pattern, Obs], Fraction]] = None

    def __post_init__(self):
        if self.kind not in KINDS:
            raise ValueError(self.kind)
        if self.gamma is not None and Q(self.gamma) < 1:
            raise ValueError("gamma must be >= 1")
        if sum(self.q.values()) != 1 or any(v < 0 for v in self.q.values()):
            raise ValueError("q must be a distribution over masks")
        if self.kind == "observed_law" and self.target_observed is None:
            raise ValueError("observed_law needs target_observed")

    def box(self, r: Pattern) -> Tuple[Fraction, Fraction]:
        qr = Q(self.q[r])
        if self.gamma is None:
            return Q(0), Q(1)
        g = Q(self.gamma)
        return qr / g, min(Q(1), g * qr)

    def pattern_target(self) -> Dict[Pattern, Fraction]:
        return self.target_pattern if self.target_pattern is not None else self.q

    def feature_target(self, d: int) -> Tuple[Fraction, ...]:
        if self.target_feature is not None:
            return self.target_feature
        return tuple(sum((v for r, v in self.q.items() if r[j] == 0), Q(0)) for j in range(d))

    def label(self) -> str:
        g = "inf" if self.gamma is None else str(self.gamma)
        return f"{self.kind}@Gamma={g}"


@dataclass
class LinearSystem:
    var_index: List[Tuple[Cell, Pattern]]
    A: List[List[Fraction]]
    b: List[Fraction]
    lower: List[Fraction]
    upper: List[Fraction]
    row_names: List[str] = field(default_factory=list)


def build_system(joint: FiniteJoint, spec: PolicySetSpec) -> LinearSystem:
    cells = joint.cells()
    pats = joint.patterns()
    var_index = [(c, r) for c in cells for r in pats]
    pos = {v: i for i, v in enumerate(var_index)}
    n = len(var_index)
    A, b, names = [], [], []

    for c in cells:
        row = [Q(0)] * n
        for r in pats:
            row[pos[(c, r)]] = Q(1)
        A.append(row)
        b.append(Q(1))
        names.append(f"simplex{c}")

    w = joint.prob
    if spec.kind == "pattern":
        tgt = spec.pattern_target()
        for r in pats:
            row = [Q(0)] * n
            for c in cells:
                row[pos[(c, r)]] = w[c]
            A.append(row)
            b.append(Q(tgt[r]))
            names.append(f"pattern{r}")
    elif spec.kind == "feature":
        tgt = spec.feature_target(joint.d)
        for j in range(joint.d):
            row = [Q(0)] * n
            for c in cells:
                for r in pats:
                    if r[j] == 0:
                        row[pos[(c, r)]] = w[c]
            A.append(row)
            b.append(Q(tgt[j]))
            names.append(f"feature{j}")
    elif spec.kind == "observed_law":
        tgt = spec.target_observed
        for r in pats:
            values = []
            for x in all_x(joint.d, joint.levels):
                o = observe(x, r)
                if o not in values:
                    values.append(o)
            for o in values:
                row = [Q(0)] * n
                for c in cells:
                    if observe(c[0], r) == o:
                        row[pos[(c, r)]] = w[c]
                A.append(row)
                b.append(Q(tgt[(r, o)]))
                names.append(f"obs{r}{o}")

    lower, upper = [], []
    for (c, r) in var_index:
        lo, up = spec.box(r)
        lower.append(lo)
        upper.append(up)
    return LinearSystem(var_index=var_index, A=A, b=b, lower=lower, upper=upper,
                        row_names=names)


def policy_from_vector(var_index, x) -> Policy:
    pi: Policy = {}
    for (c, r), v in zip(var_index, x):
        pi.setdefault(c, {})[r] = v
    return pi


def policy_to_vector(var_index, pi: Policy) -> List[Fraction]:
    return [Q(pi[c][r]) for (c, r) in var_index]


@dataclass
class Membership:
    in_set: bool
    violations: List[str]


def membership(joint: FiniteJoint, spec: PolicySetSpec, pi: Policy) -> Membership:
    """Exact check of pi against every constraint of Pi(Gamma; K)."""
    sysm = build_system(joint, spec)
    x = policy_to_vector(sysm.var_index, pi)
    viol = []
    for (c, r), v, lo, up in zip(sysm.var_index, x, sysm.lower, sysm.upper):
        if v < lo or v > up:
            viol.append(f"box{c}{r}: {v} not in [{lo}, {up}]")
    for name, row, bi in zip(sysm.row_names, sysm.A, sysm.b):
        lhs = sum((a * v for a, v in zip(row, x) if a and v), Q(0))
        if lhs != bi:
            viol.append(f"{name}: {lhs} != {bi}")
    return Membership(in_set=not viol, violations=viol)


def policy_gamma(pi: Policy, q: Dict[Pattern, Fraction]) -> Optional[Fraction]:
    """Smallest Gamma whose box around q contains pi (None = infinite).

    Pattern/feature/observed-law constraints are NOT part of this number.
    """
    g = Q(1)
    for row in pi.values():
        for r, p in row.items():
            qr = Q(q[r])
            if qr == 0 and p == 0:
                continue
            if qr == 0 or p == 0:
                return None
            g = max(g, p / qr, qr / p)
    return g


def support_violations(q: Dict[Pattern, Fraction], deployment_rates: Dict[Pattern, Fraction]) -> List[Pattern]:
    """Masks used at deployment that the artificial dropout law never produces.

    Any Gamma-box around q forces pi(r|c) = 0 for these masks, so no finite
    Gamma can contain the deployment policy.
    """
    return [r for r, v in deployment_rates.items() if v > 0 and Q(q.get(r, 0)) == 0]
