"""Finite-sample layer for setting C (one i.i.d. sample, labels iff complete).

The observable multinomial has K cells: (c, complete) for every full-data cell
and (r, o) for every incomplete mask r and observed tuple o.  A simultaneous
confidence box is built from Hoeffding's inequality with a Bonferroni split:

    eps = sqrt( log(2K / alpha) / (2 n) ),   P(all |theta_hat_k - theta_k| < eps) >= 1 - alpha.

Endpoints are rounded OUTWARD to a 1e-6 grid so that the exact LP uses
rational numbers without shrinking the box.  Optimising Delta over the outer
relaxation in observation.build(..., theta_box, obs_box) then gives an outer
confidence interval: on the event that the box contains the true
probabilities, every point of the population identified set is feasible
(paper/main.tex, Proposition "Outer confidence interval", label prop:outer;
``eps`` is increased by 1e-9 before the outward rounding to absorb
floating-point error in the float products, which only enlarges the box).  The plug-in interval (theta_hat treated as
exact) is an estimate, not a confidence set, and may be infeasible.
"""

from __future__ import annotations

import bisect
import math
import random
from fractions import Fraction
from typing import Dict, Tuple

from .observation import Truth

Q = Fraction
GRID = 10 ** 6


def observable_cells(t: Truth):
    keys = [("cc", c) for c in t.joint.cells()]
    keys += [("inc", k) for k in sorted(t.obs, key=str)]
    probs = [t.theta[c] for c in t.joint.cells()] + [t.obs[k] for k in sorted(t.obs, key=str)]
    return keys, probs


def draw(t: Truth, n: int, rng: random.Random) -> Dict:
    keys, probs = observable_cells(t)
    cum, acc = [], 0.0
    for p in probs:
        acc += float(p)
        cum.append(acc)
    cum[-1] = 1.0
    counts = {k: 0 for k in keys}
    for _ in range(n):
        counts[keys[bisect.bisect_right(cum, rng.random())]] += 1
    return counts


def _floor(x: float) -> Fraction:
    return Q(math.floor(x * GRID), GRID)


def _ceil(x: float) -> Fraction:
    return Q(math.ceil(x * GRID), GRID)


def hoeffding_box(counts: Dict, n: int, alpha: float):
    K = len(counts)
    eps = math.sqrt(math.log(2 * K / alpha) / (2 * n)) + 1e-9
    theta_box, obs_box, point_theta, point_obs = {}, {}, {}, {}
    for (kind, key), k in counts.items():
        ph = k / n
        lo, hi = max(Q(0), _floor(ph - eps)), min(Q(1), _ceil(ph + eps))
        if kind == "cc":
            theta_box[key] = (lo, hi)
            point_theta[key] = Q(k, n)
        else:
            obs_box[key] = (lo, hi)
            point_obs[key] = Q(k, n)
    return eps, theta_box, obs_box, point_theta, point_obs
