"""v4.2 boundary fixtures (6): valid set first, then bounds, then endpoints."""
import unittest
from fractions import Fraction as Q

from msid.environments import interaction_policy
from msid.finite_model import mcar_policy
from msid.observation import (STATUS_ATTAINED, STATUS_CLOSURE, STATUS_EMPTY, analyse,
                              build, gamma_min_scoped, interval, truth_from_policy)

from fixtures import primary


def _mcar_truth():
    J, q, LA, LB, D = primary()
    return J, q, D, truth_from_policy(J, mcar_policy(J, q))


class TestOrderedAnalysis(unittest.TestCase):
    def test_f1_B_gamma1_weak_with_closure_lower(self):
        J, q, D, t = _mcar_truth()
        r = analyse(build(t, "B_cc_only", Q(1)), D, "B_cc_only")
        self.assertEqual(r["status"], "OK"); self.assertEqual(r["required_strata"], ["rho_full"])
        self.assertEqual(r["hi_status"], STATUS_ATTAINED); self.assertEqual(r["lo_status"], STATUS_CLOSURE)
        self.assertEqual(r["category"], "WEAK_A")

    def test_f2_D_gamma1_valid_nonempty_no_margin(self):
        J, q, D, t = _mcar_truth()
        r = analyse(build(t, "D_conditionals", Q(1)), D, "D_conditionals")
        self.assertEqual(r["status"], "OK"); self.assertEqual(len(r["required_strata"]), 4)
        self.assertGreater(r["eta_max"], 0); self.assertEqual(r["category"], "A_NO_MARGIN")

    def test_f3_D_empty_valid_model_stops_before_bounds(self):
        # label-dependent policy: stratum conditionals differ from the complete-case marginal
        J, q, LA, LB, D = primary()
        t = truth_from_policy(J, interaction_policy(J, q, "label", "missing_x2", Q(3, 2)))
        b = build(t, "D_conditionals", Q(1))
        r = analyse(b, D, "D_conditionals")
        self.assertEqual(r["status"], STATUS_EMPTY); self.assertNotIn("lo", r)
        # the relaxed LP itself is feasible: that interval must NOT be reported
        self.assertEqual(interval(b, D).status, "OPTIMAL")
        # B on the same law cannot refute
        self.assertEqual(analyse(build(t, "B_cc_only", Q(1)), D, "B_cc_only")["status"], "OK")

    def test_f4_C_no_required_strata_endpoints_attained(self):
        J, q, D, t = _mcar_truth()
        r = analyse(build(t, "C_cc_plus_unlab", Q(2)), D, "C_cc_plus_unlab")
        self.assertEqual(r["required_strata"], []); self.assertEqual(r["lo_status"], STATUS_ATTAINED)
        self.assertEqual(r["category"], "BOTH_ORDERS")

    def test_f5_gamma_min_scoped_cases(self):
        J, q, D, t = _mcar_truth()
        self.assertEqual(gamma_min_scoped(t)["gamma_min_squared"], 1)
        # V>0, mu=0 within a sampled stratum -> no finite Gamma
        pi = mcar_policy(J, q); c0 = ((1, 1), 1)
        for c in pi:
            if c[0][0] == 1:  # no x with x1=1 ever has mask (1,0) -> mu_(1,0)(o=(1,_)) = 0 while V>0
                row = dict(pi[c]); row[(1, 1)] += row[(1, 0)]; row[(1, 0)] = Q(0); pi[c] = row
        t2 = truth_from_policy(J, pi)
        self.assertEqual(gamma_min_scoped(t2)["status"], "NO_FINITE_GAMMA")
        self.assertEqual(analyse(build(t2, "C_cc_plus_unlab", Q(1000)), D, "C_cc_plus_unlab")["status"], "LP_INFEASIBLE")

    def test_f6_zero_mass_stratum_excluded(self):
        J, q, D, t = _mcar_truth()
        pi = mcar_policy(J, q)
        for c in pi:
            row = dict(pi[c]); row[(1, 1)] += row[(0, 0)]; row[(0, 0)] = Q(0); pi[c] = row
        t3 = truth_from_policy(J, pi)
        r = analyse(build(t3, "D_conditionals", Q(1)), D, "D_conditionals")
        self.assertEqual(len(r["required_strata"]), 3); self.assertEqual(r["status"], "OK")
        self.assertEqual(gamma_min_scoped(t3)["status"], "OK")


if __name__ == "__main__":
    unittest.main()
