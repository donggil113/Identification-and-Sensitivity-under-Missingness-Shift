"""Finite-support full-data law, masks, fixed predictors and mask-specific losses.

Conventions
-----------
* A cell is ``c = (x, y)`` with ``x`` in {0,1}^d and ``y`` in {0,1}.
* A mask/pattern is ``r`` in {0,1}^d with ``r[j] == 1`` meaning feature j is
  OBSERVED.  The same object type is used for the artificial deletion mask M
  (drawn by the evaluator, independent of (X, Y)) and for the natural
  deployment mask R (drawn by an unknown policy pi(r | x, y)); the two are kept
  apart by where they come from (``dropout_q`` vs a deployment ``Policy``).
* ``observe(x, r)`` returns the tuple seen by a predictor, with ``None`` in
  missing coordinates.
* All probabilities, predictions and losses are exact ``Fraction`` values.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass
from fractions import Fraction
from typing import Callable, Dict, List, Optional, Sequence, Tuple

Q = Fraction
X = Tuple[int, ...]
Cell = Tuple[X, int]
Pattern = Tuple[int, ...]
Obs = Tuple[Optional[int], ...]


def all_x(d: int, levels: int = 2) -> List[X]:
    return [tuple(v) for v in itertools.product(range(levels), repeat=d)]


def all_patterns(d: int) -> List[Pattern]:
    """All masks, fully observed first: (1,..,1), ..., (0,..,0)."""
    return [tuple(v) for v in itertools.product((1, 0), repeat=d)]


def observe(x: X, r: Pattern) -> Obs:
    return tuple(xj if rj else None for xj, rj in zip(x, r))


def all_obs(d: int) -> List[Obs]:
    out = []
    for r in all_patterns(d):
        for x in all_x(d):
            o = observe(x, r)
            if o not in out:
                out.append(o)
    return out


@dataclass(frozen=True)
class FiniteJoint:
    """Full-data law P(X = x, Y = y) on a finite support (the population)."""

    d: int
    prob: Dict[Cell, Fraction]
    levels: int = 2  # values per feature (2 = binary, as in FR1/FR2)

    def __post_init__(self):
        expected = {(x, y) for x in all_x(self.d, self.levels) for y in (0, 1)}
        if set(self.prob) != expected:
            raise ValueError("prob must list every (x, y) cell (use 0 for no mass)")
        if any(p < 0 for p in self.prob.values()):
            raise ValueError("negative probability")
        if sum(self.prob.values()) != 1:
            raise ValueError("probabilities must sum to exactly 1")

    @classmethod
    def from_px_py1(cls, d: int, px: Dict[X, Fraction], py1: Dict[X, Fraction]) -> "FiniteJoint":
        prob = {}
        for x in all_x(d):
            prob[(x, 1)] = Q(px[x]) * Q(py1[x])
            prob[(x, 0)] = Q(px[x]) * (1 - Q(py1[x]))
        return cls(d=d, prob=prob)

    def cells(self) -> List[Cell]:
        return [(x, y) for x in all_x(self.d, self.levels) for y in (0, 1)]

    def patterns(self) -> List[Pattern]:
        return all_patterns(self.d)

    def mass_consistent(self, o: Obs, y: Optional[int] = None) -> Fraction:
        s = Q(0)
        for (x, yy), p in self.prob.items():
            if y is not None and yy != y:
                continue
            if all(oj is None or oj == xj for oj, xj in zip(o, x)):
                s += p
        return s

    def p_y1_given_obs(self, o: Obs) -> Optional[Fraction]:
        den = self.mass_consistent(o)
        if den == 0:
            return None
        return self.mass_consistent(o, y=1) / den

    def feature_mean(self, j: int) -> Fraction:
        return sum((p for (x, _), p in self.prob.items() if x[j] == 1), Q(0))

    def label_mean(self) -> Fraction:
        return sum((p for (_, y), p in self.prob.items() if y == 1), Q(0))

    def with_prob(self, prob: Dict[Cell, Fraction]) -> "FiniteJoint":
        return FiniteJoint(d=self.d, prob=dict(prob), levels=self.levels)


@dataclass(frozen=True)
class TableModel:
    """A fixed predictor: observed tuple -> predicted P(Y = 1)."""

    name: str
    table: Dict[Obs, Fraction]

    def predict(self, o: Obs) -> Fraction:
        return self.table[o]


def bayes_under_mcar(joint: FiniteJoint, name: str = "A_dropout_bayes",
                     fallback: Optional[Fraction] = None) -> TableModel:
    """f(x_r) = P(Y=1 | X_r = x_r) under the full-data law.

    Under MCAR dropout this is the Bayes predictor for every mask, i.e. the
    idealised model one would obtain by training with random modality dropout
    on infinite complete data.  Zero-mass observed tuples get ``fallback``
    (default: the label mean).
    """
    fb = joint.label_mean() if fallback is None else Q(fallback)
    table = {}
    for o in all_obs(joint.d):
        v = joint.p_y1_given_obs(o)
        table[o] = fb if v is None else v
    return TableModel(name=name, table=table)


def impute_then_predict(joint: FiniteJoint, impute: Sequence[int],
                        name: str = "B_mode_impute") -> TableModel:
    """Fill missing coordinates with fixed values, then apply P(Y=1 | X = x)."""
    table = {}
    for o in all_obs(joint.d):
        filled = tuple(impute[j] if oj is None else oj for j, oj in enumerate(o))
        v = joint.p_y1_given_obs(tuple(filled))
        table[o] = joint.label_mean() if v is None else v
    return TableModel(name=name, table=table)


def feature_modes(joint: FiniteJoint) -> Tuple[int, ...]:
    """Population mode of each binary feature (ties -> 0)."""
    return tuple(1 if joint.feature_mean(j) > Q(1, 2) else 0 for j in range(joint.d))


def brier(p: Fraction, y: int) -> Fraction:
    return (Q(p) - y) ** 2


LossFn = Callable[[Fraction, int], Fraction]
LossTable = Dict[Tuple[Cell, Pattern], Fraction]


def loss_table(joint: FiniteJoint, model: TableModel, loss: LossFn = brier) -> LossTable:
    """L_f(c, r) = loss(f(observe(x, r)), y) for every cell and mask."""
    out = {}
    for (x, y) in joint.cells():
        for r in joint.patterns():
            out[((x, y), r)] = loss(model.predict(observe(x, r)), y)
    return out


def difference_table(la: LossTable, lb: LossTable) -> LossTable:
    return {k: la[k] - lb[k] for k in la}


# ----------------------------------------------------------------------------
# Policies: pi(r | c) as {cell: {pattern: prob}}
# ----------------------------------------------------------------------------

Policy = Dict[Cell, Dict[Pattern, Fraction]]


def mcar_policy(joint: FiniteJoint, q: Dict[Pattern, Fraction]) -> Policy:
    return {c: {r: Q(q[r]) for r in joint.patterns()} for c in joint.cells()}


def validate_policy(joint: FiniteJoint, pi: Policy) -> List[str]:
    errs = []
    for c in joint.cells():
        row = pi[c]
        if set(row) != set(joint.patterns()):
            errs.append(f"cell {c}: patterns missing")
            continue
        if any(v < 0 or v > 1 for v in row.values()):
            errs.append(f"cell {c}: entry outside [0,1]")
        if sum(row.values()) != 1:
            errs.append(f"cell {c}: row sums to {sum(row.values())}")
    return errs


def risk(joint: FiniteJoint, pi: Policy, table: LossTable) -> Fraction:
    """sum_c w_c sum_r pi(r|c) table(c, r)."""
    s = Q(0)
    for c, w in joint.prob.items():
        if w == 0:
            continue
        for r, p in pi[c].items():
            if p:
                s += w * p * table[(c, r)]
    return s


def pattern_marginal(joint: FiniteJoint, pi: Policy) -> Dict[Pattern, Fraction]:
    out = {r: Q(0) for r in joint.patterns()}
    for c, w in joint.prob.items():
        for r, p in pi[c].items():
            out[r] += w * p
    return out


def feature_missing_rates(joint: FiniteJoint, pi: Policy) -> Tuple[Fraction, ...]:
    pm = pattern_marginal(joint, pi)
    return tuple(sum((v for r, v in pm.items() if r[j] == 0), Q(0)) for j in range(joint.d))


def observed_law(joint: FiniteJoint, pi: Policy) -> Dict[Tuple[Pattern, Obs], Fraction]:
    """Unlabelled deployment law P(R = r, X_r = x_r) (labels never enter)."""
    out: Dict[Tuple[Pattern, Obs], Fraction] = {}
    for r in joint.patterns():
        for x in all_x(joint.d, joint.levels):
            out.setdefault((r, observe(x, r)), Q(0))
    for (x, y), w in joint.prob.items():
        for r, p in pi[(x, y)].items():
            out[(r, observe(x, r))] += w * p
    return out


def complete_case_joint(joint: FiniteJoint, pi: Policy) -> Optional[FiniteJoint]:
    """Law of (X, Y) among units whose natural mask is fully observed."""
    full = tuple([1] * joint.d)
    den = sum((w * pi[c][full] for c, w in joint.prob.items()), Q(0))
    if den == 0:
        return None
    return joint.with_prob({c: w * pi[c][full] / den for c, w in joint.prob.items()})
