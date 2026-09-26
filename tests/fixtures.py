"""Shared small instances for tests (mirrors configs/p2_first_run.json)."""

from fractions import Fraction as Q

from msid.environments import independent_dropout
from msid.finite_model import (FiniteJoint, bayes_under_mcar, difference_table,
                               feature_modes, impute_then_predict, loss_table)


def primary():
    px = {(0, 0): Q(2, 5), (0, 1): Q(3, 20), (1, 0): Q(3, 20), (1, 1): Q(3, 10)}
    py = {(0, 0): Q(1, 10), (0, 1): Q(3, 5), (1, 0): Q(2, 5), (1, 1): Q(9, 10)}
    J = FiniteJoint.from_px_py1(2, px, py)
    A = bayes_under_mcar(J)
    B = impute_then_predict(J, feature_modes(J))
    LA, LB = loss_table(J, A), loss_table(J, B)
    q = independent_dropout(2, [Q(1, 5), Q(3, 10)])
    return J, q, LA, LB, difference_table(LA, LB)


def d1_counterexample():
    px = {(0,): Q(1, 2), (1,): Q(1, 2)}
    py = {(0,): Q(1, 4), (1,): Q(3, 4)}
    J = FiniteJoint.from_px_py1(1, px, py)
    A = bayes_under_mcar(J)
    B = impute_then_predict(J, feature_modes(J))
    LA, LB = loss_table(J, A), loss_table(J, B)
    q = independent_dropout(1, [Q(1, 4)])
    return J, q, LA, LB, difference_table(LA, LB)
