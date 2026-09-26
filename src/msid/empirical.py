"""Plug-in (empirical) versions of the population quantities.

A complete-data sample of n cells is drawn i.i.d. from the population joint w;
the empirical joint w_hat = counts / n replaces w in every constraint and in
the objective.  The resulting intervals are PLUG-IN ESTIMATES: they are not
population sharp bounds, carry no coverage guarantee, and may even omit cells
that have positive population mass (empirical support violation).
"""

from __future__ import annotations

import bisect
import random
from fractions import Fraction
from typing import Dict

from .finite_model import Cell, FiniteJoint

Q = Fraction


def sample_counts(joint: FiniteJoint, n: int, rng: random.Random) -> Dict[Cell, int]:
    cells = joint.cells()
    cum, acc = [], 0.0
    for c in cells:
        acc += float(joint.prob[c])
        cum.append(acc)
    cum[-1] = 1.0
    counts = {c: 0 for c in cells}
    for _ in range(n):
        u = rng.random()
        counts[cells[bisect.bisect_right(cum, u)]] += 1
    return counts


def empirical_joint(joint: FiniteJoint, counts: Dict[Cell, int]) -> FiniteJoint:
    n = sum(counts.values())
    return joint.with_prob({c: Q(k, n) for c, k in counts.items()})
