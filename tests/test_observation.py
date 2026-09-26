import unittest
from fractions import Fraction as Q

from msid.environments import interaction_policy
from msid.finite_model import mcar_policy
from msid.observation import (SETTINGS, build, gamma_cc_squared, interval,
                              truth_from_policy, truth_in_model, truth_value)

from fixtures import primary


class TestObservationModels(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.J, cls.q, cls.LA, cls.LB, cls.D = primary()
        cls.t0 = truth_from_policy(cls.J, mcar_policy(cls.J, cls.q))
        cls.t1 = truth_from_policy(cls.J, interaction_policy(cls.J, cls.q, "label", "missing_x2", Q(3, 2)))

    def test_gamma_one_mcar(self):
        # C: point identified at the truth; B/D: interval over unknown mask weights.
        iv = interval(build(self.t0, "C_cc_plus_unlab", Q(1)), self.D)
        self.assertTrue(iv.certified)
        self.assertEqual((iv.lo, iv.hi), (truth_value(self.t0, self.D),) * 2)
        per_mask = [sum(self.t0.v[c] * self.D[(c, r)] for c in self.J.cells()) for r in self.J.patterns()]
        for s in ("B_cc_only", "D_conditionals"):
            iv = interval(build(self.t0, s, Q(1)), self.D)
            self.assertEqual((iv.lo, iv.hi), (min(per_mask), max(per_mask)))

    def test_information_and_gamma_nesting(self):
        order = ["A_oracle_w", "C_cc_plus_unlab", "D_conditionals", "B_cc_only"]
        for t in (self.t0, self.t1):
            for g in (Q(2), "NO_MODEL"):
                ivs = [interval(build(t, s, g), self.D) for s in order]
                for a, b in zip(ivs, ivs[1:]):
                    self.assertTrue(b.lo <= a.lo and a.hi <= b.hi)
            prev = None
            for g in (Q(3, 2), Q(2), Q(3), "SUPPORT_ONLY", "NO_MODEL"):
                iv = interval(build(t, "C_cc_plus_unlab", g), self.D)
                if prev is not None:
                    self.assertTrue(iv.lo <= prev.lo and prev.hi <= iv.hi, g)
                prev = iv

    def test_truth_contained_when_gamma_large_enough(self):
        g2 = gamma_cc_squared(self.t1)
        self.assertIsNotNone(g2)
        g = Q(3)
        self.assertLessEqual(g2, g * g)
        for s in SETTINGS:
            iv = interval(build(self.t1, s, g), self.D)
            self.assertTrue(iv.certified)
            self.assertTrue(iv.contains(truth_value(self.t1, self.D)), s)

    def test_outer_box_contains_population(self):
        d = Q(1, 200)
        tb = {c: (max(Q(0), v - d), v + d) for c, v in self.t1.theta.items()}
        ob = {k: (max(Q(0), v - d), v + d) for k, v in self.t1.obs.items()}
        for g in (Q(3, 2), Q(2)):
            pop = interval(build(self.t1, "C_cc_plus_unlab", g), self.D)
            out = interval(build(self.t1, "C_cc_plus_unlab", g, tb, ob), self.D)
            self.assertTrue(out.certified)
            self.assertTrue(out.lo <= pop.lo and pop.hi <= out.hi)

    def test_structural_zero_support_only_vs_no_model(self):
        pi = mcar_policy(self.J, self.q)
        c0 = ((1, 1), 1)
        pi[c0] = dict(pi[c0])
        pi[c0][(1, 0)] += pi[c0][(1, 1)]
        pi[c0][(1, 1)] = Q(0)
        t = truth_from_policy(self.J, pi)
        self.assertIsNone(gamma_cc_squared(t))
        truth = truth_value(t, self.D)
        nm = interval(build(t, "C_cc_plus_unlab", "NO_MODEL"), self.D)
        self.assertTrue(nm.contains(truth))
        so = interval(build(t, "C_cc_plus_unlab", "SUPPORT_ONLY"), self.D)
        # The support restriction excludes p*, deleting it re-admits p*;
        # the interval itself need not change (other cells absorb the mass).
        self.assertFalse(truth_in_model(t, "SUPPORT_ONLY"))
        self.assertTrue(truth_in_model(t, "NO_MODEL"))
        self.assertFalse(truth_in_model(t, Q(1000)))
        self.assertTrue(so.status == "INFEASIBLE" or (nm.lo <= so.lo and so.hi <= nm.hi))


if __name__ == "__main__":
    unittest.main()
