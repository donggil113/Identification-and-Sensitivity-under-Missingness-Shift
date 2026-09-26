import random
import unittest
from fractions import Fraction as Q

from msid.exact_lp import (dual_lower_bound, farkas_certifies_infeasible,
                           greedy_simplex_box, primal_feasible, solve_lp)


class TestExactLP(unittest.TestCase):
    def test_small_known_optimum(self):
        # min x1 + 2 x2  s.t. x1 + x2 = 1, 0 <= x <= 1  -> 1 at (1, 0)
        r = solve_lp([1, 2], [[1, 1]], [1], [0, 0], [1, 1], "min")
        self.assertEqual(r.status, "OPTIMAL")
        self.assertEqual(r.value, 1)
        self.assertTrue(r.certificate_ok)
        r = solve_lp([1, 2], [[1, 1]], [1], [0, 0], [1, 1], "max")
        self.assertEqual(r.value, 2)
        self.assertTrue(r.certificate_ok)

    def test_nontrivial_bounds(self):
        # min -x1 - x2 - x3, x1 + x2 + x3 = 2, x1 - x2 = 0, 0 <= x <= 1 -> x = (1,1,0)
        r = solve_lp([-1, -1, -1], [[1, 1, 1], [1, -1, 0]], [2, 0], [0, 0, 0], [1, 1, 1])
        self.assertEqual(r.value, -2)
        self.assertTrue(r.certificate_ok)
        # max x3 with same constraints -> x3 = 1 needs x1 = x2 = 1/2
        r = solve_lp([0, 0, 1], [[1, 1, 1], [1, -1, 0]], [2, 0], [0, 0, 0], [1, 1, 1], "max")
        self.assertEqual(r.value, 1)
        self.assertEqual(r.x, [Q(1, 2), Q(1, 2), Q(1)])

    def test_infeasible_has_farkas_certificate(self):
        A, b, lo, up = [[1, 1]], [3], [0, 0], [1, 1]
        r = solve_lp([1, 1], A, b, lo, up)
        self.assertEqual(r.status, "INFEASIBLE")
        self.assertTrue(r.certificate_ok)
        self.assertTrue(farkas_certifies_infeasible(
            [[Q(1), Q(1)]], [Q(3)], [Q(0), Q(0)], [Q(1), Q(1)], r.y))

    def test_redundant_rows(self):
        A = [[1, 1, 0], [1, 1, 0], [0, 0, 1], [1, 1, 1]]
        b = [1, 1, Q(1, 3), Q(4, 3)]
        r = solve_lp([3, 1, 5], A, b, [0, 0, 0], [1, 1, 1])
        self.assertEqual(r.status, "OPTIMAL")
        self.assertEqual(r.value, 1 + Q(5, 3))
        self.assertTrue(r.certificate_ok)

    def test_negative_rhs_and_fixed_variables(self):
        A = [[-1, -1, 0], [0, 0, 1]]
        b = [-1, Q(1, 2)]
        r = solve_lp([1, -1, 7], A, b, [0, 0, Q(1, 2)], [1, 1, Q(1, 2)])
        self.assertEqual(r.value, -1 + Q(7, 2))
        self.assertTrue(r.certificate_ok)

    def test_random_decoupled_matches_greedy(self):
        rng = random.Random(7)
        for _ in range(60):
            k_rows = rng.randint(1, 4)
            k = rng.randint(2, 5)
            c, A, b, lo, up = [], [], [], [], []
            expected = {"min": Q(0), "max": Q(0)}
            ok = True
            blocks = []
            for i in range(k_rows):
                costs = [Q(rng.randint(-20, 20), rng.randint(1, 9)) for _ in range(k)]
                lows = [Q(rng.randint(0, 3), 20) for _ in range(k)]
                ups = [lw + Q(rng.randint(0, 20), 20) for lw in lows]
                ups = [min(u, Q(1)) for u in ups]
                blocks.append((costs, lows, ups))
            n = k_rows * k
            for i, (costs, lows, ups) in enumerate(blocks):
                row = [Q(0)] * n
                for r_ in range(k):
                    row[i * k + r_] = Q(1)
                A.append(row)
                b.append(Q(1))
                c += costs
                lo += lows
                up += ups
                for sense in ("min", "max"):
                    g = greedy_simplex_box(costs, lows, ups, sense)
                    if g is None:
                        ok = False
                    else:
                        expected[sense] += g[0]
            for sense in ("min", "max"):
                res = solve_lp(c, A, b, lo, up, sense)
                if ok:
                    self.assertEqual(res.status, "OPTIMAL")
                    self.assertEqual(res.value, expected[sense])
                    self.assertTrue(res.certificate_ok)
                else:
                    self.assertEqual(res.status, "INFEASIBLE")
                    self.assertTrue(res.certificate_ok)

    def test_random_coupled_certificates_and_random_points(self):
        # Transportation-type LPs; check certificate and that random feasible
        # mixtures of optimal vertices never beat the optimum.
        rng = random.Random(11)
        for _ in range(30):
            m, k = rng.randint(2, 4), rng.randint(2, 4)
            w = [Q(rng.randint(1, 5)) for _ in range(m)]
            tot = sum(w)
            w = [v / tot for v in w]
            qv = [Q(rng.randint(1, 5)) for _ in range(k)]
            tq = sum(qv)
            qv = [v / tq for v in qv]
            n = m * k
            A, b = [], []
            for i in range(m):
                row = [Q(0)] * n
                for j in range(k):
                    row[i * k + j] = Q(1)
                A.append(row)
                b.append(Q(1))
            for j in range(k):
                row = [Q(0)] * n
                for i in range(m):
                    row[i * k + j] = w[i]
                A.append(row)
                b.append(qv[j])
            g = Q(rng.randint(1, 4))
            lo = [qv[j] / g for i in range(m) for j in range(k)]
            up = [min(Q(1), qv[j] * g) for i in range(m) for j in range(k)]
            c = [Q(rng.randint(-9, 9), 7) for _ in range(n)]
            rmin = solve_lp(c, A, b, lo, up, "min")
            rmax = solve_lp(c, A, b, lo, up, "max")
            self.assertTrue(rmin.certificate_ok and rmax.certificate_ok)
            self.assertLessEqual(rmin.value, rmax.value)
            center = [qv[j] for i in range(m) for j in range(k)]
            self.assertTrue(primal_feasible(A, b, lo, up, center))
            cval = sum(ci * xi for ci, xi in zip(c, center))
            self.assertTrue(rmin.value <= cval <= rmax.value)
            for _ in range(5):
                t = Q(rng.randint(0, 10), 10)
                mix = [t * a + (1 - t) * bb for a, bb in zip(rmin.x, rmax.x)]
                self.assertTrue(primal_feasible(A, b, lo, up, mix))
                v = sum(ci * xi for ci, xi in zip(c, mix))
                self.assertTrue(rmin.value <= v <= rmax.value)

    def test_weak_duality_any_y(self):
        rng = random.Random(3)
        A = [[Q(1), Q(1), Q(1)], [Q(1), Q(0), Q(-1)]]
        b = [Q(1), Q(0)]
        lo, up = [Q(0)] * 3, [Q(1)] * 3
        c = [Q(2), Q(-1), Q(3)]
        opt = solve_lp(c, A, b, lo, up).value
        for _ in range(50):
            y = [Q(rng.randint(-30, 30), 7) for _ in range(2)]
            self.assertLessEqual(dual_lower_bound(c, A, b, lo, up, y), opt)


if __name__ == "__main__":
    unittest.main()
