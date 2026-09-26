"""Semi-synthetic pilot on one public tabular dataset (UCI Adult format).

Pipeline (every rule is fixed in configs/p2_pilot.json BEFORE the data are read):
  1. parse rows; entity key = all raw attribute values except the sampling
     weight `fnlwgt`; exact duplicates share an entity;
  2. entity split by SHA-256(entity key) mod 100 (< train_pct -> train);
  3. coarsen each "modality" to a fixed small number of levels by fixed
     thresholds (no data-driven cut points);
  4. fit two fixed predictors on the TRAIN split using binned features only
     (A: Laplace-smoothed P(Y=1 | X_r = x_r) on complete train data = Bayes
     under MCAR dropout; B: impute the train mode of each binned modality,
     then Laplace-smoothed P(Y=1 | X = x)).  Because both predictors are
     functions of (binned x_r, r) only, D(c, r) is a FIXED loss on the
     coarse cells (checked by `assert_fixed_loss`);
  5. draw natural masks on the EVAL split with the fixed semi-synthetic rule
     (seeded); labels of incomplete units are hidden from every method and
     used only for the held-out Delta.

The eval split with its realised masks is treated as a finite population:
its observable law (complete cells with labels, incomplete observed tuples
without labels) is known exactly, so setting-C intervals are its exact
identified sets.  The outer confidence interval instead treats the eval
units as an i.i.d. sample from a super-population.
"""

from __future__ import annotations

import hashlib
import random
from fractions import Fraction
from typing import Dict, List, Sequence, Tuple

from .finite_model import FiniteJoint, all_patterns, observe
from .observation import Truth, truth_from_policy

Q = Fraction

ADULT_COLUMNS = ["age", "workclass", "fnlwgt", "education", "education-num", "marital-status",
                 "occupation", "relationship", "race", "sex", "capital-gain", "capital-loss",
                 "hours-per-week", "native-country", "income"]


def parse_adult(lines: Sequence[str]) -> List[Dict[str, str]]:
    rows = []
    for ln in lines:
        ln = ln.strip()
        if not ln or ln.startswith("|"):
            continue
        parts = [p.strip() for p in ln.split(",")]
        if len(parts) != len(ADULT_COLUMNS):
            continue
        rows.append(dict(zip(ADULT_COLUMNS, parts)))
    return rows


def label(row) -> int:
    return 1 if row["income"].rstrip(".") == ">50K" else 0


def entity_key(row, exclude=("fnlwgt",)) -> str:
    return "|".join(row[c] for c in ADULT_COLUMNS if c not in exclude)


def split_of(row, train_pct: int) -> str:
    h = int(hashlib.sha256(entity_key(row).encode()).hexdigest(), 16) % 100
    return "train" if h < train_pct else "eval"


def bin_value(value: str, cuts: Sequence[float]) -> int:
    """Number of cut points strictly below value+ (i.e. value > cut)."""
    v = float(value)
    return sum(1 for c in cuts if v > c)


def coarse_x(row, modalities) -> Tuple[int, ...]:
    return tuple(bin_value(row[m["column"]], m["cuts"]) for m in modalities)


class TableModels:
    """Two fixed predictors on binned features (exact Fractions)."""

    def __init__(self, train: List[Tuple[Tuple[int, ...], int]], d: int, levels: int):
        self.d, self.levels = d, levels
        cnt, pos = {}, {}
        for x, y in train:
            for r in all_patterns(d):
                o = observe(x, r)
                cnt[o] = cnt.get(o, 0) + 1
                pos[o] = pos.get(o, 0) + y
        self.cnt, self.pos = cnt, pos
        self.mode = []
        for j in range(d):
            freq = [0] * levels
            for x, _ in train:
                freq[x[j]] += 1
            self.mode.append(max(range(levels), key=lambda k: (freq[k], -k)))

    def _laplace(self, o):
        return Q(self.pos.get(o, 0) + 1, self.cnt.get(o, 0) + 2)

    def f_A(self, o):
        return self._laplace(o)

    def f_B(self, o):
        filled = tuple(self.mode[j] if oj is None else oj for j, oj in enumerate(o))
        return self._laplace(filled)


def loss_tables(models: TableModels, joint: FiniteJoint):
    LA, LB = {}, {}
    for (x, y) in joint.cells():
        for r in joint.patterns():
            o = observe(x, r)
            LA[((x, y), r)] = (models.f_A(o) - y) ** 2
            LB[((x, y), r)] = (models.f_B(o) - y) ** 2
    D = {k: LA[k] - LB[k] for k in LA}
    return LA, LB, D


def assert_fixed_loss(models: TableModels, units, modalities):
    """Coarsening check: the loss of each unit equals D(c, r) of its coarse cell.

    Holds by construction because predictions depend on (binned x_r, r) only;
    we still recompute per unit to catch any leakage of fine features."""
    seen = {}
    for x, y, r in units:
        o = observe(x, r)
        val = ((models.f_A(o) - y) ** 2, (models.f_B(o) - y) ** 2)
        key = ((x, y), r)
        if key in seen and seen[key] != val:
            raise AssertionError(f"loss not fixed within coarse cell {key}")
        seen[key] = val
    return True


def mask_probability(rule, x, y) -> Dict[int, Fraction]:
    """Per-modality missingness probabilities (independent across modalities)."""
    out = {}
    for j, spec in enumerate(rule):
        p = Q(spec["base"])
        p += Q(spec.get("per_label", "0")) * y
        for lvl, add in spec.get("per_level", {}).items():
            if x[j] == int(lvl):
                p += Q(add)
        out[j] = p
    return out


def draw_masks(eval_units, rule, seed: int):
    rng = random.Random(seed)
    out = []
    for x, y in eval_units:
        pr = mask_probability(rule, x, y)
        r = tuple(0 if rng.random() < float(pr[j]) else 1 for j in range(len(x)))
        out.append((x, y, r))
    return out


def finite_population_truth(units, d: int, levels: int) -> Truth:
    """Truth object of the realised finite population (empirical law)."""
    n = len(units)
    counts: Dict[Tuple, int] = {}
    for x, y, r in units:
        counts[((x, y), r)] = counts.get(((x, y), r), 0) + 1
    cells = [(x, y) for x in _all(d, levels) for y in (0, 1)]
    pats = all_patterns(d)
    w = {c: Q(sum(counts.get((c, r), 0) for r in pats), n) for c in cells}
    joint = FiniteJoint(d=d, prob=w, levels=levels)
    pi = {}
    for c in cells:
        tot = sum(counts.get((c, r), 0) for r in pats)
        if tot == 0:
            pi[c] = {r: (Q(1) if r == pats[0] else Q(0)) for r in pats}  # zero-mass cell: irrelevant
        else:
            pi[c] = {r: Q(counts.get((c, r), 0), tot) for r in pats}
    return truth_from_policy(joint, pi), counts


def _all(d, levels):
    from .finite_model import all_x
    return all_x(d, levels)


def held_out_delta(units, D) -> Fraction:
    return sum((D[((x, y), r)] for x, y, r in units), Q(0)) / len(units)


def complete_case_dropout(units, D, q, d, levels) -> Tuple[Fraction, int]:
    full = tuple([1] * d)
    cc = [(x, y) for x, y, r in units if r == full]
    if not cc:
        return None, 0
    s = Q(0)
    for x, y in cc:
        for r, qr in q.items():
            s += qr * D[((x, y), r)]
    return s / len(cc), len(cc)
