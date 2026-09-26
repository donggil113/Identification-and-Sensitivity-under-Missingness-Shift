import unittest
from fractions import Fraction as Q

from msid.environments import correlated_mcar, independent_dropout, interaction_policy
from msid.finite_model import (feature_missing_rates, mcar_policy, observed_law,
                               pattern_marginal, validate_policy)
from msid.policy_sets import (PolicySetSpec, membership, policy_gamma,
                              support_violations)

from fixtures import primary


class TestPolicySets(unittest.TestCase):
    def setUp(self):
        self.J, self.q, _, _, self.D = primary()

    def test_mcar_in_every_set(self):
        pi = mcar_policy(self.J, self.q)
        for g in (Q(1), Q(3, 2), None):
            for kind in ("none", "feature", "pattern"):
                self.assertTrue(membership(self.J, PolicySetSpec(q=self.q, gamma=g, kind=kind), pi).in_set)
            spec = PolicySetSpec(q=self.q, gamma=g, kind="observed_law",
                                 target_observed=observed_law(self.J, pi))
            self.assertTrue(membership(self.J, spec, pi).in_set)

    def test_gamma_one_box_is_q(self):
        spec = PolicySetSpec(q=self.q, gamma=Q(1), kind="none")
        for r in self.J.patterns():
            self.assertEqual(spec.box(r), (self.q[r], self.q[r]))

    def test_interaction_policy_preserves_law_and_marginals(self):
        for s in ("x2", "label", "x1"):
            for eps in (Q(3, 2), Q(-3, 2)):
                pi = interaction_policy(self.J, self.q, s, "missing_x2", eps)
                self.assertEqual(validate_policy(self.J, pi), [])
                self.assertEqual(pattern_marginal(self.J, pi), self.q)
                self.assertNotEqual(pi, mcar_policy(self.J, self.q))

    def test_policy_gamma_matches_membership(self):
        pi = interaction_policy(self.J, self.q, "x2", "missing_x2", Q(3, 2))
        g = policy_gamma(pi, self.q)
        self.assertEqual(g, Q(400, 211))
        self.assertTrue(membership(self.J, PolicySetSpec(q=self.q, gamma=g), pi).in_set)
        self.assertFalse(membership(self.J, PolicySetSpec(q=self.q, gamma=g - Q(1, 1000)), pi).in_set)

    def test_correlated_mcar_changes_patterns_not_features(self):
        pi = correlated_mcar(self.J, self.q, Q(1, 10))
        self.assertEqual(feature_missing_rates(self.J, pi), (Q(1, 5), Q(3, 10)))
        self.assertNotEqual(pattern_marginal(self.J, pi), self.q)
        self.assertTrue(membership(self.J, PolicySetSpec(q=self.q, gamma=None, kind="feature"), pi).in_set)
        self.assertFalse(membership(self.J, PolicySetSpec(q=self.q, gamma=None, kind="pattern"), pi).in_set)

    def test_support_violation_detection(self):
        q_ex = {(1, 1): Q(1, 2), (1, 0): Q(3, 10), (0, 1): Q(1, 5), (0, 0): Q(0)}
        dep = mcar_policy(self.J, independent_dropout(2, [Q(1, 5), Q(3, 10)]))
        self.assertEqual(support_violations(q_ex, pattern_marginal(self.J, dep)), [(0, 0)])
        self.assertIsNone(policy_gamma(dep, q_ex))
        for g in (Q(2), Q(100)):
            self.assertFalse(membership(self.J, PolicySetSpec(q=q_ex, gamma=g, kind="feature"), dep).in_set)


if __name__ == "__main__":
    unittest.main()
