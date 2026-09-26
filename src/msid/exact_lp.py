"""Exact rational linear programming for small finite-support problems.

Solves   min (or max) c^T x   s.t.   A x = b,   l <= x <= u   (all bounds finite)
with a two-phase bounded-variable primal simplex over ``fractions.Fraction``
using Bland's rule.  Every returned answer carries an exact certificate that is
re-checked independently of the pivoting code:

* OPTIMAL: a primal point x (checked feasible exactly) and a dual vector y such
  that the weak-duality lower bound
      b^T y + sum_j [ l_j * max(d_j, 0) - u_j * max(-d_j, 0) ],  d = c - A^T y
  equals c^T x exactly.  Weak duality holds for *any* y, so equality proves
  optimality for this instance.
* INFEASIBLE: a Farkas vector y with  y^T b > max_{l <= x <= u} y^T A x.

The certificates are instance-level exact checks, not proofs of any general
statement about the missingness problem.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import List, Optional, Sequence

Q = Fraction
ZERO = Fraction(0)
ONE = Fraction(1)


@dataclass
class LPResult:
    status: str  # "OPTIMAL" or "INFEASIBLE"
    sense: str
    value: Optional[Fraction] = None
    x: Optional[List[Fraction]] = None
    y: Optional[List[Fraction]] = None
    certificate_ok: bool = False
    certificate_gap: Optional[Fraction] = None
    iterations: int = 0
    notes: List[str] = field(default_factory=list)


def _dot(a: Sequence[Fraction], b: Sequence[Fraction]) -> Fraction:
    s = ZERO
    for ai, bi in zip(a, b):
        if ai and bi:
            s += ai * bi
    return s


def box_max_linear(coef: Sequence[Fraction], lower: Sequence[Fraction],
                   upper: Sequence[Fraction]) -> Fraction:
    """max_{l <= x <= u} coef^T x (finite bounds)."""
    s = ZERO
    for a, lo, up in zip(coef, lower, upper):
        s += a * (up if a > 0 else lo)
    return s


def dual_lower_bound(c, A, b, lower, upper, y) -> Fraction:
    """Weak-duality lower bound on min c^T x over {Ax=b, l<=x<=u} for any y."""
    n = len(c)
    m = len(A)
    bound = _dot(b, y)
    for j in range(n):
        aty = ZERO
        for i in range(m):
            if A[i][j] and y[i]:
                aty += A[i][j] * y[i]
        d = c[j] - aty
        if d > 0:
            bound += d * lower[j]
        elif d < 0:
            bound += d * upper[j]
    return bound


def primal_feasible(A, b, lower, upper, x) -> bool:
    for j, xj in enumerate(x):
        if xj < lower[j] or xj > upper[j]:
            return False
    for i, row in enumerate(A):
        if _dot(row, x) != b[i]:
            return False
    return True


def farkas_certifies_infeasible(A, b, lower, upper, y) -> bool:
    """True iff y proves {Ax=b, l<=x<=u} is empty (either sign of y)."""
    n = len(lower)
    m = len(A)
    aty = [sum((A[i][j] * y[i] for i in range(m) if A[i][j] and y[i]), ZERO)
           for j in range(n)]
    yb = _dot(y, b)
    hi = box_max_linear(aty, lower, upper)
    lo = -box_max_linear([-a for a in aty], lower, upper)
    return yb > hi or yb < lo


class _Simplex:
    """Bounded-variable primal simplex on a dense tableau (internal)."""

    def __init__(self, A, b, lower, upper, max_iter):
        self.m = len(A)
        self.n = len(lower)
        self.max_iter = max_iter
        self.iterations = 0
        m, n = self.m, self.n
        # Nonbasic structural variables start at their lower bound.
        self.val = [Q(v) for v in lower] + [ZERO] * m
        self.lo = [Q(v) for v in lower] + [ZERO] * m
        self.up: List[Optional[Fraction]] = [Q(v) for v in upper] + [None] * m
        resid = [Q(b[i]) - _dot(A[i], self.val[:n]) for i in range(m)]
        self.sign = [ONE if r >= 0 else -ONE for r in resid]
        # Tableau T = B^{-1} [A | S] with initial basis S = diag(sign).
        self.T = []
        for i in range(m):
            s = self.sign[i]
            row = [s * Q(a) for a in A[i]] + [ZERO] * m
            row[n + i] = ONE
            self.T.append(row)
        self.basis = [n + i for i in range(m)]
        self.is_basic = [False] * n + [True] * m
        for i in range(m):
            self.val[n + i] = abs(resid[i])
        self.at_upper = [False] * (n + m)

    def _reduced_costs(self, cost):
        m, n = self.m, self.n
        cb = [cost[self.basis[i]] for i in range(m)]
        red = list(cost)
        for i in range(m):
            if cb[i]:
                row = self.T[i]
                for j in range(n + m):
                    if row[j]:
                        red[j] -= cb[i] * row[j]
        return red

    def _pivot(self, p, j):
        row_p = self.T[p]
        piv = row_p[j]
        width = self.n + self.m
        inv = ONE / piv
        for k in range(width):
            if row_p[k]:
                row_p[k] *= inv
        for i in range(self.m):
            if i == p:
                continue
            f = self.T[i][j]
            if f:
                row_i = self.T[i]
                for k in range(width):
                    if row_p[k]:
                        row_i[k] -= f * row_p[k]
        leaving = self.basis[p]
        self.is_basic[leaving] = False
        self.is_basic[j] = True
        self.basis[p] = j

    def run(self, cost, allow_enter):
        """Iterate until no improving direction; cost is minimized."""
        m = self.m
        while True:
            self.iterations += 1
            if self.iterations > self.max_iter:
                raise RuntimeError("simplex iteration cap exceeded")
            red = self._reduced_costs(cost)
            enter = None
            for j in range(self.n + m):
                if self.is_basic[j] or not allow_enter(j):
                    continue
                if self.up[j] is not None and self.up[j] == self.lo[j]:
                    continue  # fixed variable can never move
                if (not self.at_upper[j] and red[j] < 0) or (self.at_upper[j] and red[j] > 0):
                    enter = j
                    break  # Bland: smallest improving index
            if enter is None:
                return
            j = enter
            sigma = -ONE if self.at_upper[j] else ONE
            # Step t >= 0 moves x_j by sigma*t and x_B by -sigma*t*alpha.
            best_t = None
            best_row = None
            best_to_upper = False
            for i in range(m):
                alpha = self.T[i][j]
                if not alpha:
                    continue
                delta = -sigma * alpha
                bi = self.basis[i]
                if delta < 0:
                    t = (self.val[bi] - self.lo[bi]) / (-delta)
                    to_upper = False
                else:
                    if self.up[bi] is None:
                        continue
                    t = (self.up[bi] - self.val[bi]) / delta
                    to_upper = True
                if (best_t is None or t < best_t
                        or (t == best_t and bi < self.basis[best_row])):
                    best_t, best_row, best_to_upper = t, i, to_upper
            flip_t = None if self.up[j] is None else self.up[j] - self.lo[j]
            if best_t is None and flip_t is None:
                raise RuntimeError("unbounded direction (should not occur with finite bounds)")
            if flip_t is not None and (best_t is None or flip_t <= best_t):
                t = flip_t
                for i in range(m):
                    alpha = self.T[i][j]
                    if alpha:
                        self.val[self.basis[i]] -= sigma * t * alpha
                self.at_upper[j] = not self.at_upper[j]
                self.val[j] = self.up[j] if self.at_upper[j] else self.lo[j]
                continue
            t = best_t
            p = best_row
            for i in range(m):
                alpha = self.T[i][j]
                if alpha:
                    self.val[self.basis[i]] -= sigma * t * alpha
            self.val[j] += sigma * t
            leaving = self.basis[p]
            self.at_upper[leaving] = best_to_upper
            self.val[leaving] = self.up[leaving] if best_to_upper else self.lo[leaving]
            self._pivot(p, j)
            self.at_upper[j] = False

    def duals(self, cost):
        """y^T = c_B^T B^{-1}, with B^{-1} = T[:, art] * diag(sign)."""
        m, n = self.m, self.n
        y = []
        for k in range(m):
            s = ZERO
            for i in range(m):
                cb = cost[self.basis[i]]
                if cb and self.T[i][n + k]:
                    s += cb * self.T[i][n + k]
            y.append(s * self.sign[k])
        return y


def solve_lp(c, A, b, lower, upper, sense: str = "min", max_iter: int = 20000) -> LPResult:
    """Solve an LP exactly; see module docstring."""
    if sense not in ("min", "max"):
        raise ValueError(sense)
    c = [Q(v) for v in c]
    A = [[Q(v) for v in row] for row in A]
    b = [Q(v) for v in b]
    lower = [Q(v) for v in lower]
    upper = [Q(v) for v in upper]
    n, m = len(c), len(A)
    if any(len(row) != n for row in A) or len(lower) != n or len(upper) != n or len(b) != m:
        raise ValueError("dimension mismatch")
    for j in range(n):
        if lower[j] > upper[j]:
            # Empty box: certify with y = 0 is impossible; report directly.
            return LPResult(status="INFEASIBLE", sense=sense, certificate_ok=True,
                            notes=[f"empty box for variable {j}: lower > upper"])
    cmin = c if sense == "min" else [-v for v in c]
    if m == 0:
        x = [lower[j] if cmin[j] >= 0 else upper[j] for j in range(n)]
        val = _dot(c, x)
        return LPResult(status="OPTIMAL", sense=sense, value=val, x=x, y=[],
                        certificate_ok=True, certificate_gap=ZERO)

    sx = _Simplex(A, b, lower, upper, max_iter)
    # Phase 1: minimise the sum of artificials; artificials never re-enter.
    cost1 = [ZERO] * n + [ONE] * m
    sx.run(cost1, allow_enter=lambda j: j < n)
    infeas = sum((sx.val[n + i] for i in range(m)), ZERO)
    if infeas > 0:
        y1 = sx.duals(cost1)
        # Phase-1 duals give  y^T b - max_box y^T A x = phase-1 optimum > 0.
        ok = farkas_certifies_infeasible(A, b, lower, upper, y1)
        return LPResult(status="INFEASIBLE", sense=sense, y=y1, certificate_ok=ok,
                        iterations=sx.iterations,
                        notes=[f"phase-1 residual {infeas}"])
    # Drive zero-valued artificials out of the basis where possible.
    for i in range(m):
        if sx.basis[i] >= n:
            for j in range(n):
                if not sx.is_basic[j] and sx.T[i][j]:
                    art = sx.basis[i]
                    sx.val[j] = sx.val[j]  # degenerate pivot: value unchanged
                    sx._pivot(i, j)
                    sx.val[art] = ZERO
                    sx.at_upper[art] = False
                    break
    # Phase 2: artificials fixed at zero.
    for k in range(n, n + m):
        sx.up[k] = ZERO
        sx.lo[k] = ZERO
    cost2 = cmin + [ZERO] * m
    sx.run(cost2, allow_enter=lambda j: j < n)
    x = [sx.val[j] for j in range(n)]
    y = sx.duals(cost2)
    val_min = _dot(cmin, x)
    lb = dual_lower_bound(cmin, A, b, lower, upper, y)
    feas = primal_feasible(A, b, lower, upper, x)
    gap = val_min - lb
    res = LPResult(status="OPTIMAL", sense=sense, value=_dot(c, x), x=x,
                   y=y if sense == "min" else [-v for v in y],
                   certificate_ok=feas and gap == 0, certificate_gap=gap,
                   iterations=sx.iterations)
    if not feas:
        res.notes.append("primal point failed exact feasibility check")
    return res


def greedy_simplex_box(costs: Sequence[Fraction], lower: Sequence[Fraction],
                       upper: Sequence[Fraction], sense: str = "min"):
    """Closed-form optimum of  min/max sum_r p_r costs_r  s.t. sum p = 1, l <= p <= u.

    Used as an independent cross-check of the simplex when rows decouple.
    Returns (value, p) or None if infeasible.
    """
    costs = [Q(v) for v in costs]
    lower = [Q(v) for v in lower]
    upper = [Q(v) for v in upper]
    if sum(lower) > 1 or sum(upper) < 1:
        return None
    p = list(lower)
    rem = ONE - sum(lower)
    order = sorted(range(len(costs)), key=lambda r: costs[r], reverse=(sense == "max"))
    for r in order:
        add = min(rem, upper[r] - lower[r])
        p[r] += add
        rem -= add
    return _dot(costs, p), p
