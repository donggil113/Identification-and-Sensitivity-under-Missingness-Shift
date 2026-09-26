import unittest
from fractions import Fraction as Q

from msid.finite_model import mcar_policy
from msid.observation import (build, classify_sign, endpoint_attained, interval,
                              truth_from_policy)

from fixtures import primary


class TestSignInterpretation(unittest.TestCase):
    def test_categories(self):
        self.assertEqual(classify_sign(Q(-2), Q(-1)), "STRICT_A")
        self.assertEqual(classify_sign(Q(1), Q(2)), "STRICT_B")
        self.assertEqual(classify_sign(Q(-1), Q(0)), "WEAK_A")
        self.assertEqual(classify_sign(Q(-1), Q(0), hi_attained=False), "A_NO_MARGIN")
        self.assertEqual(classify_sign(Q(-1), Q(1)), "BOTH_ORDERS")
        self.assertEqual(classify_sign(Q(0), Q(0)), "TIE")
        self.assertEqual(classify_sign(None, None), "INFEASIBLE")

    def test_setting_B_gamma1_endpoints(self):
        # [-0.1296, 0]: 0 is attained (rho_full = 1, all complete) so A is
        # weakly better; the lower end needs rho_full = 0 (closure only).
        J, q, LA, LB, D = primary()
        t = truth_from_policy(J, mcar_policy(J, q))
        b = build(t, "B_cc_only", Q(1))
        iv = interval(b, D)
        self.assertEqual(iv.hi, 0)
        self.assertTrue(endpoint_attained(b, D, iv.hi))
        self.assertFalse(endpoint_attained(b, D, iv.lo))
        self.assertEqual(classify_sign(iv.lo, iv.hi, False, True), "WEAK_A")
        bc = build(t, "C_cc_plus_unlab", Q(1))
        self.assertIsNone(endpoint_attained(bc, D, interval(bc, D).lo))

    def test_zero_kappa_lower_is_not_structural_zero(self):
        J, q, LA, LB, D = primary()
        t = truth_from_policy(J, mcar_policy(J, q))
        tb = {c: (Q(0), v + Q(1, 100)) for c, v in t.theta.items()}
        ob = {k: (max(Q(0), v - Q(1, 100)), v + Q(1, 100)) for k, v in t.obs.items()}
        iv = interval(build(t, "C_cc_plus_unlab", Q(2), tb, ob), D)
        self.assertEqual(iv.status, "OPTIMAL")
        self.assertTrue(iv.lo <= -Q(12633, 500000) <= iv.hi)


if __name__ == "__main__":
    unittest.main()


class TestReverseMap(unittest.TestCase):
    def test_lp_solutions_are_models_or_closure(self):
        from msid.observation import recover_model, solve_endpoint
        J, q, LA, LB, D = primary()
        t = truth_from_policy(J, mcar_policy(J, q))
        seen = set()
        for s in ("A_oracle_w", "B_cc_only", "C_cc_plus_unlab", "D_conditionals"):
            for g in (Q(1), Q(2), "SUPPORT_ONLY"):
                b = build(t, s, g)
                for sense in ("min", "max"):
                    res = solve_endpoint(b, D, sense)
                    status, info = recover_model(t, b, res.x, g)
                    self.assertNotEqual(status, "VIOLATION", (s, g, sense, info))
                    seen.add((s, status))
        self.assertIn(("B_cc_only", "CLOSURE_ONLY"), seen)
        self.assertIn(("C_cc_plus_unlab", "PROBABILITY_MODEL"), seen)
