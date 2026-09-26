"""General point-identification criterion for a linear functional on a polytope.

F = {x : A x = b, l <= x <= u} (non-empty).  The functional g^T x is constant
on F  iff  g is orthogonal to span{x - x' : x, x' in F}.  That span equals the
null space of A augmented with e_j for every coordinate that is constant on F
(the implicit equalities of the bound system), so the test is

    g in rowspace( A  stacked with  {e_j : min_F x_j = max_F x_j} ).

``explicit_only`` omits the constant-coordinate rows: it agrees with the
general test only when F has a point strictly inside every non-degenerate
bound (relative-interior assumption).  It can fail at Gamma = 1, with
structural zeros, or when bounds bind at every feasible point.

This is a computational check for a given instance (exact LPs + exact rank),
not a proof of any general statement.
"""

from __future__ import annotations

from fractions import Fraction
from typing import List

from .bounds import _rank
from .exact_lp import solve_lp

Q = Fraction


def constant_coordinates(A, b, lower, upper) -> List[int]:
    n = len(lower)
    out = []
    for j in range(n):
        if lower[j] == upper[j]:
            out.append(j)
            continue
        e = [Q(0)] * n
        e[j] = Q(1)
        lo = solve_lp(e, A, b, lower, upper, "min")
        if lo.status != "OPTIMAL":
            raise ValueError("empty feasible set")
        hi = solve_lp(e, A, b, lower, upper, "max")
        if not (lo.certificate_ok and hi.certificate_ok):
            raise RuntimeError("uncertified LP")
        if lo.value == hi.value:
            out.append(j)
    return out


def identified_general(A, b, lower, upper, g) -> bool:
    n = len(lower)
    rows = [list(r) for r in A]
    for j in constant_coordinates(A, b, lower, upper):
        e = [Q(0)] * n
        e[j] = Q(1)
        rows.append(e)
    if not rows:
        return all(v == 0 for v in g)
    return _rank(rows + [list(g)]) == _rank(rows)


def identified_explicit_only(A, g) -> bool:
    if not A:
        return all(v == 0 for v in g)
    return _rank([list(r) for r in A] + [list(g)]) == _rank([list(r) for r in A])
