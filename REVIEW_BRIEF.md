# REVIEW_BRIEF — P2, manuscript v4.2 (for an external statistical reviewer)

Status labels: NUMERICAL_IMPLEMENTATION_CHECKED_WITHIN_SCOPE ·
HUMAN_REVIEW_UNASSIGNED · NOVELTY_NOT_ESTABLISHED.
Snapshot: branch `claude/keen-franklin-ua0v00`; files cited by path and line
number as in the commit that ships this brief (`git log -1` of the bundle).
Independent human review is recommended quality control; no reviewer has been
assigned, contacted, or has accepted.

## 0. What the paper claims (two sentences)
With labels on complete cases only, the natural-missingness Brier-risk
difference of two fixed predictors is point-identified from complete cases plus
the unlabelled law of incomplete units only if the predictors agree on every
incomplete input that occurs (for a sensitivity parameter above the true one);
otherwise conclusions depend on an unverifiable sensitivity parameter, and
random dropout on complete cases can rank the predictors opposite to the
natural-missingness risk difference (toy population; grouped-feature
semi-synthetic pilot CLEAN1).

## 1. Common setting (paper §3, `paper/main.tex` lines 215–355)
* Cells c = (x, y), finite; masks r; joint mass p(c, r); w_c = Σ_r p; ρ_r = Σ_c p.
* Assumption (Labels), line 244: S = 1[R = complete].
* Observation models: B (complete-case law v only), C (θ_c = p(c, complete) with
  labels + ω(r, o) = P(R = r, X_r = o) without labels), D (v and μ_r(o) = P(X_r = o | R = r),
  selection fractions unknown), A (oracle, w known).
* Sensitivity model M_cc(Γ), eq. (eq:mcc): λ_r/Γ ≤ P(C = c | R = r)/v_c ≤ λ_r Γ for
  v_c > 0, P(C = c | R = r) = 0 if v_c = 0, free λ_r > 0, Γ ≥ 1.
* Lemma (Exact linearisation), line 292; proof lines 830–848
  (`src/msid/observation.py::build`, `recover_model`). Reparametrisation
  b_r = ρ_r λ_r (κ = v) or ρ_r λ_r/ρ_complete (κ = θ); no other strict inequality;
  reverse map λ_r = b_r/ρ_r when ρ_r > 0.
* Estimand Δ_nat = Σ p(c, r) D(c, r), Brier loss, D = u − 2yδ.

## 2. The three propositions to review

### T1 — Proposition 5 (Setting C: identification requires agreement), lines 427–443; proof 873–894
Statement. Setting C; θ_c > 0 ∀c; ρ_r > 0 for every incomplete mask; Γ² > max_r
max_c e_r(c)/min_c e_r(c), e_r(c) = p*(c, r)/θ_c (i.e. Γ > Γ_true, a property of the
hidden law). Then Δ_nat is identified iff D(·, r) is constant on every group
G(r, o); under Brier, iff f_A(o, r) = f_B(o, r) for every incomplete input.
Assumptions to check: interiority construction b*_r ∈ (M_r/Γ, m_r Γ); groups with
both labels follow from θ_c > 0; zero-mass masks impose nothing; the "iff" is NOT
claimed at Γ = 1 or for Γ ∈ [Γ_min(o), Γ_true].
Code: `observation.build(..., "C_cc_plus_unlab", Γ)`, `identification.py`
(general criterion), `tests/test_identification.py`, `tests/test_sign.py`.
Known result used: Theorem 2 (general criterion), a standard polyhedral fact.

### T2 — Proposition 3 (MCAR boundary), lines 379–404, Remark 4 (lines 406–425); proofs 859–871, 896–907
Statement (ii), B vs D at Γ = 1. B: identified set {Σ ρ_r Δ^cc_r : ρ_complete > 0},
never refuted. D: the rows force b_r(Σ_{G(r,o)} v_c − μ_r(o)) = 0, so a valid law
exists iff every given μ_r equals the complete-case marginal; otherwise D refutes
M_cc(1) although the relaxed LP is feasible. Attained vs closure-only endpoints
(weak vs no-margin) when valid laws exist.
Remark 4: B/D programs always feasible (ρ = e_complete); Γ_min(o)² = max_r
max_o r_r(o)/min_o r_r(o) with r_r = μ_r/V_r (conditional quantities; scope cases
V = 0 < μ, V > 0 = μ, V = μ = 0 handled in the text), attained, Γ_min(o) ≤ Γ_true.
Order of the analysis (lines 320–336): valid-set non-empty (max η over P_Γ) →
bounds (inf/sup over F_Γ) → endpoint attainment (max η at the endpoint).
Code: `observation.analyse`, `required_strata` (B: {ρ_full}; D: {ρ_full} ∪ given
strata), `valid_set_eta`, `endpoint_eta`, `gamma_min_scoped`;
fixtures `tests/test_ordered_analysis.py` (6), `tests/test_sign.py`.

### T3 — Proposition 8 (Outer confidence interval), lines 535–556; proof 912–930
Statement. n i.i.d. units with the Labels assumption; K observable cells (all,
incl. zero counts); Σθ > 0; Hoeffding/Bonferroni box with ε = √(log(2K/α)/(2n)),
rounded outward (implementation adds 1e-9 before rounding — numeric margin, not
part of the statement); relaxed rows with κ_lo/κ_hi and b_r ≤ Γ/Σκ_lo (Σκ_lo = 0
branch: support restriction only). On {ϑ ∈ B_α} (prob ≥ 1 − α) the relaxed program
contains the identified set I(Γ; P_obs) for every Γ simultaneously; it covers
Δ_nat only for Γ ≥ Γ_true. It does not validate Γ; emptiness rejects
"p* ∈ M_cc(Γ)" at level α; exact infeasibility for a finite population and plug-in
infeasibility are different statements; plug-in with n_complete = 0 is
constructed-infeasible (implementation outcome, no estimand).
Code: `src/msid/finite_sample.py::hoeffding_box`, `observation.build(theta_box, obs_box)`;
run `scripts/run_p2_fr2.py` part F (frozen raw `results/raw/p2_fr2_F_finite_sample.json`).

## 3. The correction this brief exists for (v4.1 → v4.2)
Defect: v3 reported relaxed-LP intervals for settings B/D and only afterwards
checked endpoint attainment with ρ_complete alone. For the CLEAN1 MNAR law, D at
Γ_cc ∈ {1, 5/4} has a feasible relaxed program but NO valid law (every given
stratum must have positive mass; max η = 0). The reported "B strictly better
without margin" was an interval of the closure of an empty set.
Fix: validity-first order (`analyse`), per-setting required strata, exact
rational certificates; category ∅ᶜ in Table 2. Standard fact relied on: if
F_Γ ≠ ∅ then cl(F_Γ) = P_Γ (closed convex P_Γ, linear ρ); if F_Γ = ∅ then cl(F_Γ) = ∅.
Applied examples (`results/derived/p2_validity_eta.json`):
* CLEAN1 MNAR, D, Γ_cc = 1 and 5/4 → EMPTY_VALID_MODEL (no bounds reported);
  Γ_cc = 3/2 → OK, both orders, both endpoints closure-only.
* CLEAN1 MNAR, B, Γ_cc = 1 → OK, "B weakly better" (tie attained at ρ_complete = 1),
  lower endpoint closure-only; B cannot refute.
* FR2 toy E0, D, Γ_cc = 1 → OK, max η = 1/4, A strictly better without uniform margin.
* Γ_true = 2.38 (hidden expected joint) vs Γ_min(o) = 1.3108 (closed form; LP grid:
  5/4 infeasible, 3/2 feasible) — different quantities.

## 4. Status of prior check findings (not evidence of correctness)
18 findings from a read-only check of T1–T3 against the v4 manuscript: 11
VALID_FIXED (original defect real, now corrected, with both planned confirmations
run); 7 PENDING (confirmations not run; fixes applied by the author and recorded
in RESEARCH_PACKET §15). None were rejected as wrong. Unit tests (45) and exact
LP certificates are instance checks, not proofs.

## 5. Unresolved questions for a human reviewer (max 3)
1. T1: is the restriction "Γ > Γ_true (hidden)" the right hypothesis to state,
   or should the proposition be stated under the checkable condition "the
   feasible set has a point strictly inside every Γ bound on every positive-mass
   mask", with the hidden condition as a corollary?
2. T2/Remark 4: the closed form Γ_min(o) is proved for C and D under free scale
   and positive support; is the treatment of the V > 0 = μ case (NO_FINITE_GAMMA)
   complete when a sampled stratum has an observed tuple of zero mass but the
   complete-case group mass is positive (i.e. is any finite Γ ever compatible)?
3. T3: the outer box is a Bonferroni/Hoeffding construction with no width
   analysis; should the paper state it only as a validity device and remove any
   implication of practical usefulness at n ≈ 2×10⁴ (where it admitted both
   orders everywhere in PILOT1)?

## 6. Scope limits the reviewer should hold us to
One toy population (results seen during development); one public dataset with
synthetic masks, two grouped tabular features, record-profile split (not
persons), unweighted record population; CLEAN1 frozen and conditional on the
selected records (no population CI); Brier loss only; no natural modality
missingness; novelty not established (two-paper comparison only, App. E).
