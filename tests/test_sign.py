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


class TestValidSetAndGammaMin(unittest.TestCase):
    def test_zero_mass_stratum_not_forced_in_D(self):
        from msid.observation import build, required_positive_rhos, valid_set_eta
        J, q, LA, LB, D = primary()
        pi = mcar_policy(J, q)
        # give mask (0,0) zero mass everywhere -> no sample, mu undefined
        for c in pi:
            row = dict(pi[c]); row[(1, 1)] += row[(0, 0)]; row[(0, 0)] = Q(0); pi[c] = row
        t = truth_from_policy(J, pi)
        b = build(t, "D_conditionals", Q(1))
        req = required_positive_rhos(b, "D_conditionals")
        self.assertNotIn("rho(0, 0)", req)
        self.assertEqual(len(req), 3)  # rho_full + two sampled strata
        eta, ok = valid_set_eta(b, req)
        self.assertTrue(ok and eta > 0)

    def test_gamma_min_closed_form_matches_lp_feasibility(self):
        from msid.environments import interaction_policy
        from msid.observation import build, gamma_min_closed_form, interval, gamma_cc_squared
        J, q, LA, LB, D = primary()
        t = truth_from_policy(J, interaction_policy(J, q, "label", "missing_x2", Q(3, 2)))
        g2, reason = gamma_min_closed_form(t)
        self.assertIsNone(reason)
        self.assertLessEqual(g2, gamma_cc_squared(t))
        # C is infeasible just below and feasible at the closed-form threshold
        from fractions import Fraction as F
        below = g2 * F(99, 100)
        import math
        g_at = F(math.isqrt(int(g2.numerator * 10**12 // g2.denominator)) + 1, 10**6)  # rational >= sqrt(g2)
        self.assertEqual(interval(build(t, "C_cc_plus_unlab", g_at), D).status, "OPTIMAL")
        g_below = F(math.isqrt(int(below.numerator * 10**12 // below.denominator)), 10**6)
        self.assertEqual(interval(build(t, "C_cc_plus_unlab", g_below), D).status, "INFEASIBLE")

    def test_classify_empty_valid(self):
        from msid.observation import classify_sign
        self.assertEqual(classify_sign(Q(0), Q(1, 100), False, False, valid=False), "EMPTY_VALID")
