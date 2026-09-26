import random
import unittest
from fractions import Fraction as Q

from msid.bounds import (closed_form_gamma, closed_form_interval, dropout_delta,
                         gamma_star, joint_interval, separate_interval)
from msid.environments import interaction_policy
from msid.exact_lp import greedy_simplex_box
from msid.finite_model import mcar_policy, observed_law, risk
from msid.policy_sets import PolicySetSpec, membership

from fixtures import primary

GRID = [Q(1), Q(5, 4), Q(3, 2), Q(2), Q(3), Q(5), None]


def _le(a, b):
    """Gamma order with None = infinity."""
    if b is None:
        return True
    if a is None:
        return False
    return a <= b


class TestBounds(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.J, cls.q, cls.LA, cls.LB, cls.D = primary()
        cls.dq = dropout_delta(cls.J, cls.q, cls.D)
        cls.iv = {}
        for g in GRID:
            for kind in ("none", "feature", "pattern"):
                cls.iv[(g, kind)] = joint_interval(cls.J, PolicySetSpec(q=cls.q, gamma=g, kind=kind), cls.D)

    def test_all_certified(self):
        for key, iv in self.iv.items():
            self.assertEqual(iv.status, "OPTIMAL", key)
            self.assertTrue(iv.certified, key)

    def test_gamma_one_is_point(self):
        for kind in ("none", "feature", "pattern"):
            iv = self.iv[(Q(1), kind)]
            self.assertEqual((iv.lo, iv.hi), (self.dq, self.dq))

    def test_nesting_in_gamma(self):
        for kind in ("none", "feature", "pattern"):
            for g1 in GRID:
                for g2 in GRID:
                    if _le(g1, g2):
                        a, b = self.iv[(g1, kind)], self.iv[(g2, kind)]
                        self.assertTrue(b.lo <= a.lo and a.hi <= b.hi, (g1, g2, kind))

    def test_nesting_in_constraint_strength(self):
        mcar = mcar_policy(self.J, self.q)
        for g in GRID:
            obs = joint_interval(self.J, PolicySetSpec(q=self.q, gamma=g, kind="observed_law",
                                                       target_observed=observed_law(self.J, mcar)), self.D)
            chain = [obs, self.iv[(g, "pattern")], self.iv[(g, "feature")], self.iv[(g, "none")]]
            for inner, outer in zip(chain, chain[1:]):
                self.assertTrue(outer.lo <= inner.lo and inner.hi <= outer.hi, g)

    def test_endpoints_attained_by_valid_policies(self):
        for (g, kind), iv in self.iv.items():
            spec = PolicySetSpec(q=self.q, gamma=g, kind=kind)
            self.assertTrue(membership(self.J, spec, iv.argmin).in_set)
            self.assertTrue(membership(self.J, spec, iv.argmax).in_set)
            self.assertEqual(risk(self.J, iv.argmin, self.D), iv.lo)
            self.assertEqual(risk(self.J, iv.argmax, self.D), iv.hi)

    def test_decoupled_lp_matches_greedy(self):
        for g in GRID:
            spec = PolicySetSpec(q=self.q, gamma=g, kind="none")
            for sense, attr in (("min", "lo"), ("max", "hi")):
                total = Q(0)
                for c in self.J.cells():
                    pats = self.J.patterns()
                    costs = [self.D[(c, r)] for r in pats]
                    lo = [spec.box(r)[0] for r in pats]
                    up = [spec.box(r)[1] for r in pats]
                    total += self.J.prob[c] * greedy_simplex_box(costs, lo, up, sense)[0]
                self.assertEqual(getattr(self.iv[(g, "none")], attr), total)

    def test_joint_inside_separate(self):
        for g in GRID:
            for kind in ("none", "feature", "pattern"):
                spec = PolicySetSpec(q=self.q, gamma=g, kind=kind)
                sep = separate_interval(self.J, spec, self.LA, self.LB)
                jt = self.iv[(g, kind)]
                self.assertTrue(sep.lo <= jt.lo and jt.hi <= sep.hi)

    def test_closed_form_contains_lp(self):
        for g in GRID:
            if g is None:
                continue
            cf = closed_form_interval(self.J, self.q, self.D, g)
            lp = self.iv[(g, "pattern")]
            self.assertTrue(cf.lo <= lp.lo and lp.hi <= cf.hi, g)

    def test_gamma_star_bracket_and_cf(self):
        gs = gamma_star(self.J, self.q, self.D, "pattern", bisect_steps=8)
        self.assertEqual(gs.status, "BRACKETED")
        lo_iv = joint_interval(self.J, PolicySetSpec(q=self.q, gamma=gs.lo), self.D)
        hi_iv = joint_interval(self.J, PolicySetSpec(q=self.q, gamma=gs.hi), self.D)
        self.assertFalse(lo_iv.lo <= 0 <= lo_iv.hi)
        self.assertTrue(hi_iv.lo <= 0 <= hi_iv.hi)
        self.assertLessEqual(closed_form_gamma(self.J, self.q, self.D), gs.hi)

    def test_random_in_set_policies_are_contained(self):
        rng = random.Random(5)
        for _ in range(40):
            s = rng.choice(["x1", "x2", "label"])
            t = rng.choice(["missing_x1", "missing_x2", "any_missing"])
            eps = Q(rng.randint(-15, 15), 10)
            try:
                pi = interaction_policy(self.J, self.q, s, t, eps)
            except ValueError:
                continue
            v = risk(self.J, pi, self.D)
            for (g, kind), iv in self.iv.items():
                if membership(self.J, PolicySetSpec(q=self.q, gamma=g, kind=kind), pi).in_set:
                    self.assertTrue(iv.lo <= v <= iv.hi)


if __name__ == "__main__":
    unittest.main()
