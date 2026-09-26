import unittest
from fractions import Fraction as Q

from msid.bounds import (anova_interaction, dropout_delta, joint_interval,
                         objective_in_rowspace)
from msid.environments import independent_dropout
from msid.finite_model import (TableModel, difference_table, loss_table,
                               mcar_policy, observed_law, pattern_marginal, risk)
from msid.policy_sets import PolicySetSpec, membership

from fixtures import d1_counterexample, primary


class TestD1Counterexample(unittest.TestCase):
    """Hand-derived instance (RESEARCH_PACKET.md, Example CX1)."""

    def test_hand_values(self):
        J, q, _, _, D = d1_counterexample()
        self.assertEqual(dropout_delta(J, q, D), Q(-1, 64))
        mcar = mcar_policy(J, q)
        spec = PolicySetSpec(q=q, gamma=None, kind="observed_law",
                             target_observed=observed_law(J, mcar))
        iv = joint_interval(J, spec, D)
        self.assertTrue(iv.certified)
        self.assertEqual((iv.lo, iv.hi), (Q(-5, 64), Q(3, 64)))
        # Both endpoint policies reproduce the unlabelled MCAR law exactly yet
        # order the two models differently.
        self.assertEqual(observed_law(J, iv.argmin), observed_law(J, mcar))
        self.assertEqual(observed_law(J, iv.argmax), observed_law(J, mcar))
        self.assertLess(risk(J, iv.argmin, D), 0)
        self.assertGreater(risk(J, iv.argmax, D), 0)


class TestIdentification(unittest.TestCase):
    def setUp(self):
        self.J, self.q, self.LA, self.LB, self.D = primary()
        self.mcar = mcar_policy(self.J, self.q)

    def _specs(self, g):
        return {
            "none": PolicySetSpec(q=self.q, gamma=g, kind="none"),
            "feature": PolicySetSpec(q=self.q, gamma=g, kind="feature"),
            "pattern": PolicySetSpec(q=self.q, gamma=g, kind="pattern"),
            "observed_law": PolicySetSpec(q=self.q, gamma=g, kind="observed_law",
                                          target_observed=observed_law(self.J, self.mcar)),
        }

    def test_rank_condition_matches_zero_width(self):
        # Prop. 2: with pi = q strictly inside the box (Gamma > 1, q > 0),
        # width == 0 iff the objective lies in the constraint row space.
        _, dint = anova_interaction(self.J, self.q, self.D)
        d_add = {k: self.D[k] - dint[k] for k in self.D}
        kappa = Q(1, 20)
        A = self.LA  # reuse loss of A; build B' = A + kappa
        from msid.finite_model import bayes_under_mcar
        fa = bayes_under_mcar(self.J)
        fb = TableModel("B_shift", {o: p + kappa for o, p in fa.table.items()})
        d_shift = difference_table(A, loss_table(self.J, fb))
        for name, D in (("brier", self.D), ("additive", d_add), ("shift", d_shift)):
            for g in (Q(3, 2), Q(2)):
                for kind, spec in self._specs(g).items():
                    iv = joint_interval(self.J, spec, D)
                    in_rs = objective_in_rowspace(self.J, spec, D)
                    self.assertEqual(in_rs, iv.width == 0, (name, g, kind))
        # Specific predictions of Prop. 2 / Cor. 2b.
        self.assertFalse(objective_in_rowspace(self.J, self._specs(Q(2))["observed_law"], self.D))
        self.assertTrue(objective_in_rowspace(self.J, self._specs(Q(2))["pattern"], d_add))
        self.assertTrue(objective_in_rowspace(self.J, self._specs(Q(2))["observed_law"], d_shift))
        self.assertFalse(objective_in_rowspace(self.J, self._specs(Q(2))["pattern"], d_shift))

    def test_support_violation_is_infeasible_not_a_number(self):
        q_ex = {(1, 1): Q(1, 2), (1, 0): Q(3, 10), (0, 1): Q(1, 5), (0, 0): Q(0)}
        dep = mcar_policy(self.J, independent_dropout(2, [Q(1, 5), Q(3, 10)]))
        rho = pattern_marginal(self.J, dep)
        for g in (Q(1), Q(2), Q(1000)):
            spec = PolicySetSpec(q=q_ex, gamma=g, kind="pattern", target_pattern=rho)
            iv = joint_interval(self.J, spec, self.D)
            self.assertEqual(iv.status, "INFEASIBLE")
            self.assertTrue(iv.certified)
            self.assertIsNone(iv.lo)
        # Removing the box (Gamma = inf) restores feasibility and coverage.
        spec = PolicySetSpec(q=q_ex, gamma=None, kind="pattern", target_pattern=rho)
        iv = joint_interval(self.J, spec, self.D)
        self.assertEqual(iv.status, "OPTIMAL")
        self.assertTrue(membership(self.J, spec, dep).in_set)
        self.assertTrue(iv.contains(risk(self.J, dep, self.D)))


if __name__ == "__main__":
    unittest.main()
