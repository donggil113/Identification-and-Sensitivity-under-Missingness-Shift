# RESEARCH_PACKET — P2: When Can Modality-Dropout Rankings Transfer?

Last updated: 2026-09-26 (after P2-FR1 and P2-FR2; manuscript v1).
**All experiments in this packet are EXPLORATORY/DEVELOPMENT**: the single
population was examined in a smoke test before FR1 was pre-registered.
Sections 1-7 describe FR1 as run (with corrections flagged in §8); §9-§10 add
the observation models and FR2.
Status labels used below: PROVED (a complete written proof is given here; it is
elementary and has only been self-checked, not externally reviewed),
CONJECTURE / UNPROVED, NOT_RUN, ABSTRACT_ONLY (literature).
Numerical checks and unit tests are **not** proofs; they are cited only as
consistency checks.

## 1. Question and scope

**Central question.** A model ranking is obtained by evaluating two *fixed*
predictors under *artificial random dropout*. For which range of *natural*
missingness policies does that ranking stay the same, and can that range be
described by partial identification and sensitivity analysis?

**In scope for the first run.** Exact population analysis on a finite support
(binary features, binary label), two fixed models, Brier loss, a known
full-data law, and an unknown deployment policy constrained by a sensitivity
box plus marginal information. No new imputer, no training, no real data.

**Explicitly not claimed.** No statement about how *often* rankings reverse in
practice (the environments in the run are hand-specified, not sampled); no
safety certification (every interval is conditional on untestable
assumptions listed in Section 3.4); no high-dimensional or plug-in result is
called a population sharp bound.

## 2. Objects that must not be conflated

| Object | Symbol | Where it lives |
|---|---|---|
| Natural (deployment) mask | `R ~ pi(. \| x, y)` | unknown policy; the object of partial identification |
| Artificial deletion mask | `M ~ q`, `M ⟂ (X, Y)` | chosen by the evaluator (random modality dropout) |
| Full-data population law | `w_c = P(X=x, Y=y)` | assumed known in FR1 (exact) |
| Complete-data sample | `ŵ = counts / n` | plug-in only (FR1 part F) |
| Complete-case law | `P(c \| R = 1…1) ∝ w_c pi(1…1 \| c)` | differs from `w` under MNAR (FR1 part A, diagnostic column) |
| Exact population constraint | e.g. `Σ_c w_c pi(r\|c) = q(r)` | used for all "sharp" statements |
| Empirical estimate of a constraint | same with `ŵ` | plug-in; no sharpness or coverage guarantee |
| Oracle quantity | `Δ(pi*)` using the true policy and target labels | used **only** to score coverage |
| Available method | intervals computed from `w`, `q`, marginals, unlabelled deployment law | never uses target labels |

## 3. Setting

### 3.1 Notation
Cells `c = (x, y)`, `x ∈ {0,1}^d`, `y ∈ {0,1}`; masks `r ∈ {0,1}^d` with
`r_j = 1` meaning *observed*. A fixed predictor `f` sees `x_r` (missing
coordinates removed) and the mask. Mask-specific loss
`L_f(c, r) = ℓ(f(x_r, r), y)`; loss difference `D(c, r) = L_A(c, r) − L_B(c, r)`.

Risk under a policy: `R_f(pi) = Σ_c w_c Σ_r pi(r|c) L_f(c, r)`.
Deployment risk difference (both models under the **same** policy):

    Δ(pi) = Σ_{c,r} g_{c,r} pi(r|c),      g_{c,r} = w_c D(c, r).

Random-dropout estimand: `Δ(q)` (policy `pi(r|c) = q(r)`).

### 3.2 Policy sets
`Π(Γ; K)` = policies with (i) `pi(·|c)` a distribution for every cell,
(ii) the **Γ-box** `q(r)/Γ ≤ pi(r|c) ≤ min(1, Γ q(r))` (`Γ = ∞`: `[0,1]`), and
(iii) constraint family `K`:

* `none`;
* `feature`: `Σ_c w_c P_pi(R_j = 0 | c) = p_j` (per-feature missing rates);
* `pattern`: `Σ_c w_c pi(r|c) = q(r)` (pattern rates; implies `feature`);
* `observed_law`: `Σ_{c: x_r(c)=v} w_c pi(r|c) = P_obs(r, v)` for all `(r, v)` —
  the law of unlabelled deployment data `(R, X_R)`; implies `pattern`.

Interpretation of Γ under `pattern`: `pi(r|c)/q(r) = P(c | R=r)/P(c)`, i.e. Γ
bounds the density ratio between the full-data law inside a natural mask and
the population law (a bounded-selection / Γ-biased-sampling type assumption;
related work in RELATED_WORK.md).

### 3.3 Estimands of the analysis
* Joint interval `[Δ_min(Γ;K), Δ_max(Γ;K)] = [min, max]_{pi ∈ Π(Γ;K)} Δ(pi)` (two exact LPs).
* Ranking-transfer threshold `Γ*(K) = inf{Γ ≥ 1 : 0 ∈ [Δ_min, Δ_max]}`.
  For `Γ < Γ*` the sign of `Δ(q)` holds for every policy in `Π(Γ;K)`.
* Baselines: `Δ(q)` alone; per-mask stress tests `Δ_r = Σ_c w_c D(c,r)`;
  a scenario grid (min/max of `Δ` over a few hand-specified MNAR policies);
  separate bounds `[min R_A − max R_B, max R_A − min R_B]`; the closed-form
  bound of Prop. 3.

### 3.4 Maintained assumptions (all untestable or only partly testable)
A1. The deployment full-data law equals the known `w` (no covariate/label shift).
A2. The deployment policy lies in the Γ-box around `q` (Γ is a sensitivity parameter, not estimated).
A3. The marginal information used by `K` is known exactly (population level).
A4. Models are fixed; their predictions on every mask are known.
Violations of A1–A3 are outside every interval reported here. A2 is partly
testable when `K = observed_law` (Prop. 4); nothing else is.

## 4. Formal results

### Prop. 1 (endpoint attainability; sharpness relative to Π) — PROVED
If `Π(Γ;K) ≠ ∅` then `{Δ(pi) : pi ∈ Π(Γ;K)} = [Δ_min, Δ_max]`; both endpoints
are attained at vertices of `Π`, and every intermediate value is attained by a
policy in `Π`.

*Proof.* `Π` is defined by finitely many linear equalities and bounds inside
`[0,1]^{C×𝓡}`, hence a non-empty compact convex polytope. `Δ` is linear, so
its image is a compact convex subset of ℝ, i.e. a closed interval; the
minimum and maximum of a linear function over a polytope are attained at
vertices; any intermediate value is attained on the segment between the two
optimisers, which lies in `Π` by convexity. ∎

*Consequence.* Under A1–A4, the set of deployment policies compatible with the
available information is exactly `Π(Γ;K)` (the constraints encode all of it),
so `[Δ_min, Δ_max]` is the **sharp identified set** for `Δ` *relative to those
assumptions*. It is not sharp for a larger class of policies and says nothing
when A1–A3 fail. The implementation (`src/msid/exact_lp.py`) certifies each
endpoint exactly (primal–dual gap 0) and each empty set with a Farkas vector;
this is an instance-level certificate, not a proof of Prop. 1.

### Prop. 2 (point identification ⇔ row-space condition) — PROVED
Write the equalities of `Π` as `Aπ = b` and append a row `e_j^T` for every
coordinate whose box is degenerate (`lower_j = upper_j`). Suppose `Π` contains
`π°` with `lower_j < π°_j < upper_j` for every non-degenerate coordinate.
Then `Δ` is constant on `Π` **iff** `g ∈ rowspace(A)`.

*Proof.* (⇐) If `g = A^T λ`, then `Δ(π) = λ^T A π = λ^T b` on `Π`.
(⇒) Otherwise write `g = A^T λ + h` with `0 ≠ h ∈ null(A)`. `h` vanishes on
degenerate coordinates, so for small `t > 0` both `π° ± t h` satisfy the
equalities and stay strictly inside the box, hence lie in `Π`, and
`Δ(π° + t h) − Δ(π° − t h) = 2t‖h‖² > 0`. ∎

For `Γ > 1` (or `Γ = ∞`) and `0 < q(r) < 1`, the random-dropout policy `π° = q`
satisfies the interior condition for `K ∈ {none, feature, pattern}` and for
`K = observed_law` with the unlabelled law generated by `q`. Computing the row
spaces (cells with `w_c > 0`):

* (2a) `K = none`: `Δ` constant iff `D(c, r)` does not depend on `r`.
* (2b) `K = pattern`: iff `D(c, r) = a(c) + b(r)` (additively separable).
* (2c) `K = observed_law`: iff `D(c, r) = a(c) + b(r, x_r(c))`.
* (2d) `K = feature`: iff `D(c, r) = a(c) + Σ_j β_j 1[r_j = 0]`.

Only the **cell × mask interaction** of the loss difference can move `Δ` away
from `Δ(q)`; the matched marginals remove exactly the mask main effect.

### Corollary 2′ (Brier loss: generic non-identification) — PROVED
Assume `w_{(x,0)}, w_{(x,1)} > 0` for all `x` and `q(r) > 0` for all `r`
including the all-missing mask `∅`. With Brier loss,
`D(c, r) = u(o) − 2y v(o)` where `o = x_r`, `u = f_A² − f_B²`, `v = f_A − f_B`.

* Under `K = observed_law`, `Δ` is identified iff `f_A − f_B` is constant on all observed tuples.
* Under `K = pattern`, `Δ` is identified iff `f_A ≡ f_B`, or `f_A − f_B ≡ κ ≠ 0`
  and `f_B` (hence `f_A`) depends on the observed tuple only through the mask.

*Proof.* By (2c), identification requires `D(c,r) = a(x,y) + b(r,o)`.
Differencing `y = 1` and `y = 0` at fixed `(x, r)` gives
`−2 v(x_r) = a(x,1) − a(x,0) =: −2α(x)`, independent of `r`. Taking `r = ∅`
gives `α(x) = v(∅)` for all `x`, so `v ≡ v(∅)`. Conversely, if `v ≡ κ` then
`a(x,y) = −2κy`, `b(r,o) = u(o)` works. For (2b) the same differencing gives
`v ≡ κ`; then `u(x_r) = a(x,0) + b(r)`; comparing `r = ∅` across `x` shows
`a(x,0)` is constant, so `u` depends on the mask only; with `u = κ(2f_B + κ)`
this forces `κ = 0` or `f_B` depending on the mask only. ∎

Reading: unlabelled deployment data can never rule out label-dependent
missingness, so two models whose difference is not a constant cannot be
ranked by point identification; the useful object is the interval and Γ*.
This is close to classical results on non-identification of MNAR outcome
dependence (Manski; see RELATED_WORK.md); the model-comparison form is the
only part that may be new, and novelty is **UNVERIFIED**.

### Prop. 3 (closed-form outer bound for the pattern set) — PROVED
For `K = pattern` (target `q`) and any functions `a(c)`, `b(r)`:

    |Δ(π) − Δ(q)| ≤ (Γ − 1) Σ_{c,r} w_c q(r) |D(c,r) − a(c) − b(r)|   for all π ∈ Π(Γ; pattern).

*Proof.* `Σ_r (π(r|c) − q(r)) = 0` for each `c` and `Σ_c w_c (π(r|c) − q(r)) = 0`
for each `r`, so `Δ(π) − Δ(q) = Σ w_c (π − q)(D − a − b)`. On the box,
`π − q ≤ (Γ−1) q` and `q − π ≤ q(1 − 1/Γ) ≤ (Γ−1) q`. ∎

Hence `Γ_cf = 1 + |Δ(q)| / E_{w⊗q}|D_int| ≤ Γ*(pattern)` for any valid
`(a, b)`; the code uses the weighted two-way ANOVA decomposition. `D_int` is
computable from complete data by artificial masking, without deployment data.

### Prop. 4 (unlabelled data bound Γ from below only) — PROVED
Under A1–A2 with `K = observed_law`: (i) `Γ_min := inf{Γ : Π_obs(Γ) ≠ ∅} ≤ Γ(π*)`
(because `π* ∈ Π_obs(Γ(π*))`), so infeasibility of `Π_obs(Γ)` refutes that Γ;
(ii) if some `x` has both labels with positive mass and there are ≥ 2 masks, no
finite upper bound on `Γ(π*)` is identified.

*Proof of (ii).* Shift `+δ/w_{(x,1)}` and `−δ/w_{(x,0)}` inside mask `r`, and the
opposite inside mask `r′`, at the same `x`: all simplex and observed-law rows
are unchanged. Moving along this direction from any feasible point until a
coordinate reaches 0 gives an observationally equivalent policy with
`Γ(π) = ∞`. ∎

### Example CX1 (hand-checkable non-identification with sign reversal) — PROVED by direct computation
`d = 1`, `P(X=x) = 1/2`, `P(Y=1|X=0) = 1/4`, `P(Y=1|X=1) = 3/4`, dropout rate
`1/4`. `A` = Bayes under MCAR (`f_A(∅) = 1/2`), `B` = mode imputation
(`f_B(∅) = P(Y=1|X=0) = 1/4`). Then `D(c, observed) = 0`,
`D((x,0), ∅) = 3/16`, `D((x,1), ∅) = −5/16`, and with `M_y = Σ_x w_{x,y} π(∅|x,y)`,
`Δ(π) = (3/16) M_0 − (5/16) M_1` with `M_0 + M_1 = 1/4` fixed by the
unlabelled law. Hence `Δ(q) = −1/64` and, over all policies reproducing the
MCAR unlabelled law, `Δ ∈ [−5/64, 3/64]`: both signs occur with *identical*
unlabelled deployment data. (The LP reproduces these values exactly; see
`results/raw/p2_fr1_D_identification.json`.) This is an existence example, not
a frequency.

### Open items — CONJECTURE / UNPROVED
* C1 (UNPROVED): with the complete-case source (development data with natural
  missingness, `w` unknown), the problem remains an LP in `f(c,r) = P(c, R=r)`
  and the identified set is non-degenerate under the analogous row-space
  condition. Not derived.
* C2 (CONJECTURE): the ANOVA choice of `(a,b)` is within a constant factor of
  the optimal L1 decomposition for Γ_cf. No argument yet.
* Any statement for continuous / high-dimensional features: none is made. A
  plug-in or discretised version would be an estimate, not a population sharp bound.

## 5. Experiment P2-FR1 (FIRST RUN)

Config: `configs/p2_first_run.json` (hypotheses, primary metric, unit, budget,
stop conditions fixed and committed in `a762fc3` before the official run; a
smoke test on the same scenario preceded the commit — disclosed in the config).
Driver: `scripts/run_p2_first_run.py`. Manifest: `run_manifest.json`.

**Scenario (single, hand-specified; n_units = 1).** `d = 2`;
`P(x)`: (0,0) 2/5, (0,1) 3/20, (1,0) 3/20, (1,1) 3/10;
`P(Y=1|x)`: 1/10, 3/5, 2/5, 9/10. `A` = Bayes predictor under MCAR dropout
(idealised dropout-trained model); `B` = mode imputation (both modes 0) + full-data
Bayes predictor. `q` = independent dropout, rates 1/5 (X1) and 3/10 (X2).
Environments E1–E3 are `q(r)(1 + ε (s(c) − E s)(t(r) − E t))` with `s ∈ {x2, y}`,
`t = 1[X2 missing]`; they share `w` and the pattern marginal `q` exactly.

### 5.1 Engineering results (all PASS; `run_manifest.json`)
| Check | Result |
|---|---|
| every LP has an exact certificate (gap 0 / Farkas) | PASS (0 uncertified) |
| Γ = 1 gives the point `Δ(q)` for none/feature/pattern/observed-law | PASS |
| nesting in Γ and in constraint strength | PASS |
| `π* ∈ Π ⇒ Δ(π*) ∈ interval` over the full hand grid | PASS (0 violations) |
| support violation flagged; pattern-rate LP reported INFEASIBLE with certificate | PASS |
| Prop. 2 row-space test agrees with LP width = 0 (36/36 cases) | PASS |
| CX1 hand values reproduced exactly | PASS |
| unit tests (`python -m unittest`, 27 tests) | PASS |
| wall time / CPU | 9.9 s, 2-CPU affinity, no installs, no downloads |

### 5.2 Scientific results (population-exact; single scenario)
`Δ(q) = −12633/500000 ≈ −0.02527` (A better under random dropout).
Per-mask stress tests: `Δ_r = 0, −0.0602, −0.0217, −0.1296` for masks
11, 10, 01, 00 — A is weakly better on every mask.

| Quantity | Value |
|---|---|
| Γ*(none) | ∈ (1.39661, 1.39667] |
| Γ*(feature) | ∈ (1.42426, 1.42432] |
| **Γ*(pattern)** (primary) | **∈ (1.43903, 1.43909]** |
| Γ*(observed law of MCAR) | ∈ (2.06921, 2.06934] |
| Γ_cf (Prop. 3, ANOVA) | 1.26893 (≤ Γ*(pattern): H1 supported) |
| joint interval, pattern, Γ = 2 | [−0.07069, 0.01919] (contains 0) |
| separate interval, pattern, Γ = 2 | [−0.12143, 0.05681] (1.98× wider) |
| scenario grid within Π(2; pattern) | [−0.05803, −0.02527] (all "A better") |
| joint vs separate, Γ = 5/4, pattern | joint [−0.04302, −0.00919] decides A; separate [−0.05591, 0.00279] does not |

Oracle values (use target labels; for scoring only): E2m (label-dependent,
Γ(π) = 2.31) gives `Δ = +0.00750`; E3m (self-masking, Γ(π) = 26.7) gives
`+0.00947`; both reverse the random-dropout ranking while keeping `w` and
all pattern rates identical. E1m (Γ(π) = 2.37) gives `−0.00442`. These are
hand-specified cases, **not** a reversal rate.

Unlabelled deployment law (`observed_law`): infeasible for Γ below each
environment's feasibility threshold (e.g. E1p infeasible for Γ ≤ 3/2),
illustrating Prop. 4(i); for E2m (B truly better) every feasible interval
contains 0, so unlabelled data never reveal B's advantage (Cor. 2′).

Plug-in (part F, Γ = 2, pattern, 100 replications per n): the plug-in
interval contained the population interval in 8/100 (n = 100; Wilson 95%
[0.04, 0.15]) and 5/100 (n = 1000; [0.02, 0.11]) replications; it contained the
oracle Δ of in-set environments in 98–100/100. Plug-in endpoints are close to
the population endpoints but have no coverage guarantee (H4 as expected).

### 5.3 Interpretation (what the run does and does not show)
* Engineering success (exact, certified LP machinery; checks pass) is separate
  from scientific support. Scientific support comes from **one** hand-specified
  population and cannot be generalised.
* In this population, a random-dropout ranking that also holds on every
  per-mask stress test is guaranteed only for density-ratio deviations below
  ≈ 1.44 (pattern rates matched). Matching pattern rates barely helps over no
  constraint (1.397 → 1.439); unlabelled deployment data help more (→ 2.07).
* A small hand-specified MNAR scenario grid overstates robustness relative to
  the sharp interval at the same Γ; separate per-model bounds understate it.
* Stop-rule check: the run yields identification/evaluation statements beyond
  "random dropout is bad" (Prop. 2/Cor. 2′: only the cell × mask interaction
  matters and label-dependence is never identified; Prop. 3 certificate; Prop. 4
  falsification of small Γ). All are elementary and their novelty is
  unverified, so **no new-method claim is made**. The contribution candidate
  is an analysis framework, pending FR2.
* Literature consequences (RELATED_WORK.md): bounding the difference jointly
  rather than separately is known (Guerdan et al., ICML 2024), so H2 is a
  sanity check, **not** a P2 contribution; Γ* is a tipping-point summary of the
  E-value / sensitivity-value kind; Prop. 2(b) is a one-line consequence of the
  rank of transportation polytopes; label-dependent test-ordering shifts with
  separate worst-case bounds already appear in Subbaswamy et al. (AISTATS 2021).
  What remains is the feature-mask estimand with the unlabelled observed-law
  constraint and its identification reading. In FR1 the matched pattern rates
  add little (Γ* 1.397 → 1.439) while the unlabelled observed law adds more
  (→ 2.069); one population only.

## 6. Threats to validity
* A1 (no full-data shift) is strong; in practice complete cases are selected
  (see the complete-case column in `p2_fr1_A_scenario.json`: random dropout on
  complete cases gives different `Δ` under MNAR).
* Γ is not estimable; any "safe" Γ is a modelling choice. Wide intervals are
  not safety certificates; narrow intervals hold only inside `Π(Γ;K)`.
* Brier loss only; 0–1 and log loss not run (log loss is irrational — would
  need floating-point LPs with tolerance).
* Two binary modalities; no claim for larger supports.

## 7. Next decision experiment (single)
See STATUS.md §"Next decision experiment".


## 8. Audit of the FR1 statements (2026-09-26, second pass)
Raw FR1 outputs are unchanged; corrections are documentary.

| Item | Finding | Action |
|---|---|---|
| Γ = 1 / binding bounds | Prop. 2's "iff" needs the relative-interior condition. At Γ = 1 the explicit row-space test says "not identified" while the width is exactly 0 (P2-FR2-G audit, pattern set). | General criterion added (Thm. "general" in the manuscript): the loss contrast must be orthogonal to span{π − π′ : π, π′ ∈ Π}, i.e. lie in the row space augmented with e_j for coordinates constant on Π. Implemented in `src/msid/identification.py`; agrees with LP width in all 4 audited cases. |
| Structural zeros | If q(r) = 0 or a cell has zero mass, coordinates are fixed; the explicit test is again only sufficient. | Covered by the general criterion. |
| Cor. 2′ (Brier iff) | Support conditions were stated (both labels at every x, all-missing mask with q > 0), but two were implicit: the interior condition (Γ > 1) and that the observation model is FR1's (w known, **no labels anywhere**). Without the all-missing mask only a weaker condition follows. | Stated explicitly; the corollary is restricted to the FR1 observation model. |
| "Γ = ∞" rows | FR1's `inf` is the **no-box** set. With q > 0 it equals the closure of ∪_{Γ<∞} Π(Γ) (endpoints are generally not attained at any finite Γ). In SV1 (q(00) = 0) it deletes the support restriction; that is **not** the Γ → ∞ limit, under which π(00|c) = 0 persists. §5.1 and `p2_fr1_C_checks.json` wording "removing the box" should be read that way. | Documented; FR2 separates SUPPORT_ONLY from NO_MODEL. |
| LP certificates vs theorems | Certificates verify instances only. | Kept separate everywhere. |
| Plug-in "containment" (FR1-F) | 8/100 and 5/100 are containment frequencies of an estimate, not CI coverage. | Wording kept; FR2 adds a valid (conservative) outer CI. |
| Prop. 1 attainability | Holds for the closed polytope. In FR2 settings B/D the LP admits ρ_full = 0 (not a valid population), so the LP interval is the **closure** of the identified set. | Stated in FR2 notes. |
| Observation model | FR1 assumed w known — equivalent to treating the full-data law as observed. P(C | R = complete) must not be substituted for P(C). | FR2 relaxes this. |

## 9. Observation models (FR2)
Unknown joint mass p(c, r) = P(C = c, R = r); label indicator S with
assumption L1: S = 1[R = complete] (a separate, mask-independent S is not analysed).
Rows derived from the observables:

* normalisation: Σ_{c,r} p(c, r) = 1.
* **A (oracle)**: C-rows plus Σ_r p(c, r) = w_c (w known).
* **B (complete cases only)**: p(c, 1) − ρ_1 v_c = 0 (v known, ρ_1 unknown).
* **C (one sample)**: p(c, 1) = θ_c; Σ_{c: x_r(c)=o} p(c, r) = ω(r, o) for incomplete r (fixes ρ).
* **D (conditionals, selection fractions unknown)**: p(c, 1) − ρ_1 v_c = 0; Σ_{c: x_r(c)=o} p(c, r) − μ_r(o) ρ_r = 0.

Sensitivity model M_cc(Γ) (pattern mixture relative to complete cases):
λ_r/Γ ≤ P(c | R=r)/v_c ≤ λ_r Γ. Constants: Γ (analyst), κ_c = v_c (B, D) or
θ_c (A, C). Unknowns: p, b_r. The product ρ_r λ_r of two unknowns is replaced
by the free scalar b_r = ρ_r λ_r — exact because λ_r appears nowhere else
(Lemma "exact linearisation"). In the finite-sample outer relaxation the
product b_r·p(c, 1) with p(c, 1) uncertain is replaced by κ_lo/κ_hi bounds — an
OUTER relaxation, not an exact LP.

SUPPORT_ONLY (closure of the Γ → ∞ union) ≠ NO_MODEL (Manski) exactly when
the complete-case support misses a cell.

Formal statements (proofs in `paper/main.tex`, App. A; PROVED = written,
elementary, self-checked only):
* General criterion — KNOWN standard polyhedral fact; stated for correctness.
* MCAR boundary (Γ = 1): C point-identifies and M_cc(1) is refutable; B/D give
  the hull of per-mask complete-case differences (closure). PROVED.
* Setting C, interior truth: Brier Δ_nat identified iff f_A = f_B on every
  incomplete input whose group has both labels. PROVED.
* Oracle A: Brier identified iff f_A − f_B is constant on incomplete inputs. PROVED (sketch).
* Support: no Γ repairs a positivity violation. PROVED.
* Outer CI (Hoeffding + Bonferroni box, relaxed rows): coverage ≥ 1 − α of the
  identified interval, simultaneously over Γ. PROVED under iid, L1, correct M_cc(Γ).
  Width/sharpness: UNPROVED.
* Removing the closure caveat with a known lower bound on ρ_1: UNPROVED.

## 10. P2-FR2 results (exploratory; one population; `configs/p2_fr2.json`)
Pre-registration commit before the run; a 12-interval timing smoke preceded it
(disclosed). Official run 33.3 s, 2-CPU affinity, 0 uncertified LPs; all six
engineering checks PASS (`results/raw/p2_fr2_manifest.json`).

MCAR truth (Δ_nat = −0.0253):
| setting | Γ=1 | Γ=3/2 | Γ=2 | no model |
|---|---|---|---|---|
| A oracle w | point, A | [−0.033, −0.018] A | [−0.038, −0.013] A | [−0.051, −0.002] A |
| C one sample | point, A | [−0.047, 0.003] ? | [−0.064, 0.023] ? | [−0.111, 0.078] ? |
| D conditionals | [−0.130, 0] ? | [−0.272, 0.010] ? | [−0.355, 0.075] ? | [−0.518, 0.202] ? |
| B complete cases | [−0.130, 0] ? | [−0.272, 0.014] ? | [−0.355, 0.075] ? | [−0.518, 0.378] ? |

* Γ*(C) ∈ (1.4463, 1.4473] (M_cc parameter; not comparable to FR1's Γ).
  Γ*(A): interval excludes 0 even without a model.
* Separate-risk / direct-difference width ratio 1.6–3.5 (known idea).
* Complete-case random dropout vs truth: E2m truth +0.0075 (B better) vs
  −0.0436; E2p truth −0.058 vs −0.007.
* Misspecified Γ: E2m (Γ_cc ≈ 2.32) in C at Γ = 3/2 → non-empty set certifying
  the wrong sign ("A better"); oracle A at Γ = 2 → [0.0018, 0.0025], excludes the truth.
* Structural zero (constructed): oracle infeasible under every M_cc(Γ) and
  SUPPORT_ONLY; C remains feasible and contains the truth although p* is
  excluded; NO_MODEL contains it in both.
* Finite sample (C, MCAR truth, 2 draws per n): plug-in infeasible at Γ = 1 in
  6/6 draws; outer 95% CI keeps the sign at Γ = 1 only at n = 10^5.

Interpretation: engineering PASS ≠ scientific support. The statements above
are exact for this one population; they show possibility, not prevalence.
Novelty of the observation-model account remains UNVERIFIED.

## 11. v2 corrections (estimand and sign interpretation) — before any new bound or loss
Raw FR1/FR2 files unchanged; corrections are re-aggregations or documentation.

1. **Sign categories.** For Δ = R_A − R_B with identified interval [ℓ, u]:
   STRICT (u < 0 or ℓ > 0, margin min(|ℓ|,|u|)); WEAK (a zero endpoint attained
   by a valid model: never worse, tie compatible); NO_MARGIN (zero endpoint only
   in the closure); BOTH_ORDERS (ℓ < 0 < u; interior values always attained, the
   valid set being convex); TIE. Attainment: max ρ_full s.t. objective = endpoint.
   Re-aggregation (`results/derived/p2_sign_reclassification.json`): FR2 settings
   B/D at Γ_cc ∈ {1, 5/4} are **WEAK_A** (0 attained at ρ_full = 1; lower end
   closure-only), not "undetermined" as written in v1. Γ_cc ≥ 3/2: BOTH_ORDERS
   with both endpoints closure-only. Settings A/C unchanged (STRICT_A / BOTH_ORDERS).
2. **b_r reverse map / positivity.** From (p, b) with ρ_full > 0: v = p(·,1)/ρ_full,
   λ_r = b_r/ρ_r (×ρ_full when κ = θ) for ρ_r > 0 gives a law in M_cc(Γ) incl.
   absolute continuity. ρ_full = 0 points are CLOSURE_ONLY. Checked on all LP
   endpoints of FR2-type systems (`recover_model`, tests): A/C endpoints are
   probability models; B has closure-only endpoints; 0 violations.
   The v1 definition of M_cc omitted absolute continuity (P(c|R=r) = 0 if v_c = 0),
   which the LP always imposed — definition corrected.
3. **Γ_box vs Γ_cc.** FR1: reference = dropout law q (with matched pattern rates,
   P(c|R=r)/w_c ∈ [1/Γ_box, Γ_box], scale fixed at 1). FR2: reference = complete-case
   law, free scale λ_r, spread ≤ Γ_cc². Different parameters; numbers not compared.
4. **Coverage.** Restated as feasible-set inclusion for one confidence region R of
   the common observed-data law: on {P_obs ∈ R}, I(Γ; P_obs) ⊆ O(Γ; R) for all Γ.
   This covers identified sets only; it does not validate Γ. Emptiness of O(Γ; R)
   rejects M_cc(Γ) at level α; non-emptiness is not evidence for Γ.
5. **Zeros and stratum sizes.** The box uses joint cell probabilities with fixed n
   (random stratum sizes need no conditioning). Empirical zeros keep κ_lo = 0 < κ_hi
   and are not structural; all-zero κ_lo (incl. n_complete = 0) now reduces exactly
   to the support restriction on κ_hi (v1 raised an error). Plug-in treats empirical
   zeros as structural and is undefined when n_complete = 0 — reported as such.

## 12. P2-PILOT1 (semi-synthetic, public data) — pre-registered at 1291cc4
Data: UCI Adult (Becker & Kohavi 1996, DOI 10.24432/C5XW20, CC BY 4.0 verified on
the UCI page; download approved by the user this session; adult.zip sha256
7537312d…21bb; local only, git-ignored). 44,355 entities (all attributes except
fnlwgt), hash split 22,080 / 22,275. Two binned "modalities" (education years,
weekly hours; fixed thresholds, 3 levels). Predictors on binned inputs only →
D(c, r) fixed (unit-level check PASS). Masks synthetic: M1 missing 0.15; M2 missing
0.15 + 0.25·Y + 0.10·[hours > 45] (primary) or 0.30 (control); seed fixed.
One run, 12.7 s, 0 uncertified LPs.

| rule | held-out Δ_nat (hidden labels) | complete-case dropout | agree | identified (setting C) | outer 95% |
|---|---|---|---|---|---|
| MNAR | −0.0038 (A) | +0.0006 (B) | **no** | ∅ for Γ_cc ≤ 5/4; BOTH_ORDERS for Γ_cc ≥ 3/2 | BOTH_ORDERS at all Γ_cc incl. 1 |
| MCAR control | −0.0025 (A) | −0.0020 (A) | yes | ∅ at Γ_cc = 1; BOTH_ORDERS otherwise | BOTH_ORDERS at all Γ_cc |

Realised finite-population Γ_cc: 2.85 (MNAR) and 1.79 (MCAR control) — sampling
variation of the masks inflates it; not a mechanism-strength measure.
Held-out value contained in every non-empty identified set. Magnitudes are small.
Interpretation: one real-covariate instance of dropout-vs-truth sign disagreement;
the observable information did not determine the ranking at any Γ_cc considered.
Not a frequency; not natural modality missingness.

## 13. P2-PILOT2-EXPECTED-MASK (exploratory analysis of the fixed PILOT1; commit 43d5d97)
Post hoc: designed after PILOT1 results were seen. Same data, split, bins,
predictors, mask rules, q and Γ_cc grid. No new masks, data, loss, CI or bins.
Run: 16.5 s wall / 16.4 CPU-s (one Python process, 2-CPU affinity).

**D endpoint (definition-based positivity).** B's information (complete-case
law only) needs ρ_full > 0; D's information includes each incomplete stratum's
conditional law μ_r, which is defined and sampled only if ρ_r > 0, so D needs
ρ_full > 0 and ρ_r > 0 for every given stratum. max η LP (all required ρ ≥ η,
objective = endpoint), FR2 E0 truth: B at Γ_cc ∈ {1,5/4}: η_hi = 1 → **WEAK_A**
(tie at ρ_full = 1). D: η_hi = 0 → **A_NO_MARGIN** (strict for every valid law,
no uniform margin). v2's WEAK_A for D (ρ_full-only check) was wrong. All lower
endpoints η = 0 (closure-only). Γ_cc ≥ 3/2: BOTH_ORDERS in both.

**Provenance.** 32,561 + 16,281 = 48,842 parsed records; 3,620 contain "?"
(none in the two used columns); no exclusions. 44,355 attribute-tuple groups
(excl. fnlwgt, incl. raw income string), 4,487 duplicates dropped, 2,788 groups
of size > 1 (max 16). Hash split 22,080 / 22,275. Groups are not verified
persons; person isolation UNVERIFIED. Read-only addendum: 956 tuples that differ
only in the '.' income suffix cross the split (derived file). Unweighted record
population after dedup (fnlwgt ignored).

**Frozen predictors.** PILOT1 did not persist tables; re-derived
deterministically and accepted because they reproduce PILOT1's held-out Δ and
cc-dropout exactly; now saved (`results/raw/p2_pilot_models_frozen.json`).

**Expected mask law** p̄(c,r) = n⁻¹ Σ_i 1{C_i=c} π_r(C_i) (exact rationals; conditional on the 22,275 eval records):
| rule | expected true Δ | expected cc dropout | Γ_cc (free scale / fixed λ=1) | expected-law setting C | realised (PILOT1) |
|---|---|---|---|---|---|
| MNAR | −0.00332 | +0.00060 | 2.38 / 3.27 | ∅ Γ≤5/4; BOTH ≥3/2 | Δ −0.0038, cc +0.0006, ∅ ≤5/4, BOTH; outer BOTH |
| MCAR | −0.00204 | −0.00204 | 1 / 1 | STRICT_A at 1; BOTH ≥5/4 | Δ −0.0025, cc −0.0020, ∅ at 1; outer BOTH |

Interpretation (one dataset, exploratory): the MNAR sign disagreement is not a
mask-draw artefact; the MNAR ambiguity is information-limited; the MCAR Γ=1
ambiguity is noise-driven. Effects are small; no practical-importance claim.
Schema check: setting-C intervals identical when hidden joint/full-data law are
replaced by placeholders (evaluator sees only allowed observables).

## 14. P2-PILOT-CLEAN1 (repair validation on already-seen Adult; config/script commit c980ca2; one run)
Defect: PILOT1/2 split key contained the raw income string (target); 956 covariate
profiles crossed train/eval. PILOT1/2 kept as DEVELOPMENT_WITH_PROFILE_OVERLAP
(valid algebraic finite-population examples for their fixed predictors, not clean
held-out evidence). Theory and LP certificates are unaffected.
Repair: same 44,355 records (weight 1); strict label parser (only the trailing '.'
of allowed tokens removed; 0 unresolved; equal to PILOT1 labels); split key =
canonical non-label covariate profile (excl. fnlwgt, income; integers canonical);
same SHA-256 mod 100 < 50 rule. 41,439 profile groups, **0 leakage**; 2,475
multi-record groups, 1,029 with conflicting labels (kept). Train 22,188 / eval
22,167. Predictors refit once on clean train, tables + hash saved before
evaluation (`results/raw/p2_clean1_models.json`). Expected-mask law only (no new
draw; no population CI because no sampling model is specified for these records — see §15.2; the original wording here, 'no Hoeffding CI on fractional masses', was wrong). Run: 49.1 s wall / 49.1 CPU-s.

| rule | expected true Δ | expected cc dropout | sign | C (Γ_cc=1, 5/4, ≥3/2) | B / D at Γ_cc=1 |
|---|---|---|---|---|---|
| MNAR (law needs Γ_cc 2.38) | −0.0028 | +0.0004 | opposite | ∅, ∅, both orders | WEAK_B / B_NO_MARGIN (wrong sign under misspecified MCAR) |
| MCAR | −0.0020 | −0.0020 | same | STRICT_A, both, both | WEAK_A / A_NO_MARGIN |

Interpretation: the dropout-vs-truth sign disagreement survives the repair;
MNAR ambiguity is information-limited. Small effects; one dataset; synthetic masks;
not comparable as the same population to PILOT1/2 (split and predictors changed).

## 15. v4.1 (2026-10-02): mathematical/editorial corrections on the frozen CLEAN1 result
No new experiment, mask draw, Γ grid, training or data. CLEAN1 raw unchanged.

1. **Γ_true vs Γ_min(o).** Γ_true = inf{Γ : the full hidden joint ∈ M_cc(Γ)};
   Γ_min(o) = inf{Γ : some joint in M_cc(Γ) matches the observable law o}.
   Γ_min(o) ≤ Γ_true when o is generated by that joint. CLEAN1 MNAR expected
   law: Γ_true = 2.38 (sqrt of the stored Γ² = 17/3) while setting C is infeasible
   at Γ_cc ∈ {1, 5/4} and feasible at 3/2, so on the pre-registered grid
   5/4 ≤ Γ_min(o) ≤ 3/2 — no contradiction, and no finer bracket was computed.
   (Side remark, PROVED-self-checked, not used in the paper: the set of feasible Γ
   is closed by compactness of the lifted polytope and continuity of the rows in
   Γ, so infeasibility at 5/4 actually gives Γ_min(o) > 5/4.) Earlier wording
   "the law itself needs Γ_cc = 2.38" conflated the two thresholds — corrected.
2. **Hoeffding wording.** The sentence "expected masses are not integer counts, so
   Hoeffding does not apply" (v4 paper; §14 above, line "no Hoeffding CI on
   fractional masses"; the frozen pre-registration file configs/p2_clean1.json,
   `not_done` entry "would be invalid", left untouched and superseded by this note;
   the previous chat report) was wrong as a general statement: Hoeffding applies to independent bounded summands regardless of
   integrality. The correct reason for attaching no population CI to CLEAN1 is
   that it is an exact computation conditional on the selected, development-reused
   records with no sampling model specified. Paper text replaced accordingly.
3. **Valid-set existence in D (new finding, derived).** Beyond endpoint attainment
   (v3 η-LP), the whole feasible set must contain a point with every
   definition-required ρ > 0. `valid_set_eta` (max η without objective constraint),
   `results/derived/p2_validity_eta.json`: CLEAN1 MNAR, setting D, Γ_cc ∈ {1, 5/4}:
   η_max = 0 → **no valid D law**; D refutes M_cc(1), M_cc(5/4) like C does; the LP
   interval ([0, 0.0019] at Γ=1) is a closure artefact. Table category ∅ᶜ replaces
   "B_NO_MARGIN". Algebra: at Γ=1 the D rows give b_r(Σ_{G(r,o)} v_c − μ_r(o)) = 0.
   FR2-E0 D rows (η_max = 0.25) and all B rows (η_max = 1) unaffected. Prop. (MCAR
   boundary)(ii), Lemma (closure) and the proofs restated with this condition.
4. **prop:C hypotheses.** Added ρ_r > 0 for every incomplete mask and the explicit
   interiority construction b*_r ∈ (M_r/Γ, m_rΓ); "every group has both labels"
   follows from θ_c > 0; zero-mass masks impose no condition.
5. **prop:outer scope.** Coverage of the identified interval I(Γ; P_obs) holds for
   all Γ on one event; coverage of Δ_nat only for Γ ≥ Γ_true. Level-α rejection,
   exact finite-population infeasibility and plug-in infeasibility distinguished.
6. **1,029 conflicting-label profile groups** are not asserted to be errors.
7. **Review status.** Self-checked only; independent statistical reviewer UNASSIGNED.
8. **Build.** Local TeX Live 2026 scheme-basic + packages (user dir, 302 MB disk,
   ≈107 MiB container downloads + 5 MB installer + 0.2 MB ICML kit; install 213 s
   wall) and the official icml2026 kit (unmodified, vendored in paper/). PDF built
   locally: 14 pages, 0 errors, 0 undefined refs/cites, 0 overfull boxes; main text
   (last sentence of Conclusion, label end:main) ends on page 8; fonts embedded;
   PDF Author = "Anonymous Authors". Page rasterisation NOT_RUN (no rasteriser in
   the approved scope); checks done via .aux page map, log and a stdlib content
   inspector (table text ≥ 7 pt).
9. **Agent review round (3 propositions, read-only; not an independent human
   review).** Two of three reviewers returned before this entry; their findings
   agreed with items 1–5 and added: (a) the abstract/introduction/conclusion
   stated "identified only if the predictors agree" without the interiority
   hypothesis (false at Γ=1, where C point-identifies with disagreeing predictors)
   — qualified; (b) the spread hypothesis of the setting-C proposition is Γ > Γ_true,
   a property of the hidden law — stated; (c) a redundant clause in the MCAR
   proposition — removed; (d) B and D programs are always feasible (ρ = e_full),
   so LP feasibility there is uninformative — stated; (e) **closed form of the
   observable threshold**: for C and D, Γ_min(o)² = max_r max_o r_r(o)/min_o r_r(o),
   r_r(o) = μ_r(o)/V_r(o) (necessity by group sums, sufficiency by P_r(c) = v_c r_r(o(c))),
   the infimum is attained and Γ_min(o) ≤ Γ_true. CLEAN1 MNAR: Γ_min(o) = 1.3108
   (exact 181181891/105442197 squared), consistent with the grid (5/4 infeasible,
   3/2 feasible); MCAR control and FR2-E0: 1. Implemented as
   `gamma_min_closed_form` (unit-tested against LP feasibility) and stored in
   `results/derived/p2_validity_eta.json`. PROVED (self-checked + agent cross-check;
   human reviewer UNASSIGNED). This is an identity about the existing model, not a
   new bound or sensitivity model; the Γ grid was not extended. (f) code: a stratum
   with zero mass in the truth no longer receives μ = 0 rows in D (which would force
   structural zero); `classify_sign` gained `valid`; `endpoint_attained` deprecated;
   future runs store η_max. Frozen raw/derived values unchanged (η rows identical).
   Refutation stage: 22 of 36 planned verdicts were obtained before the run was
   stopped (the related-work table was produced by a separate run); all 22 were
   "refuted" in the sense that the working tree already contained the fix, i.e.
   none of the 18 findings stood against the corrected manuscript, and none was
   rejected as wrong. This is an AI cross-check only.
   Third reviewer (outer coverage): proposition sound; fixed the proof's
   Σκ_lo = 0 branch, the Zeros paragraph (Hoeffding box has κ_hi ≥ ε > 0, so the
   all-zero branch coincides with No-model on incomplete masks; plug-in with
   n_complete = 0 is infeasible by construction, not "undefined"), the statement's
   hypotheses (K counts every cell, L1, Σθ > 0, the 10⁻⁹ slack), the rejected
   hypothesis (p* ∈ M_cc(Γ)), and a dangling code reference "Prop. FR2-4"
   (finite_sample.py docstring, run_p2_fr2.py note for future runs; the frozen
   p2_fr2_F_finite_sample.json keeps the old note text).
   §9's wording "whose group has both labels" is superseded by "every group has
   both labels because θ_c > 0".
