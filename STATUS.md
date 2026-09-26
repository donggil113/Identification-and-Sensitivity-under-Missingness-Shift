# STATUS — P2: When Can Modality-Dropout Rankings Transfer?

Date: 2026-09-26. Branch: `claude/keen-franklin-ua0v00`.

## Starting state (verified)
* The checkout had **no commits and no files**; the remote had no branches.
  No CLAUDE.md, STATUS.md, RESEARCH_PACKET.md, configs or results existed, so
  there were no prior STOP/ARCHIVE decisions and no Work IDs. P2 is **not**
  mapped to any Work ID.
* Environment: Python 3.11.15, standard library only (numpy, scipy, pytest,
  cvxpy are **not** installed; nothing was installed or downloaded).
* No server, GPU, dataset, or patient data was accessed.

## Experiment register
| ID | What | Status |
|---|---|---|
| P2-FR1-A | scenario, fixed models, same-`w`/same-marginal environments, complete-case diagnostic | DONE |
| P2-FR1-B | joint vs separate vs closed-form vs scenario-grid intervals; observed-law intervals | DONE |
| P2-FR1-C | Γ=1, nesting, membership⇒containment, support violation | DONE (all PASS) |
| P2-FR1-D | row-space identification test, controls C1/C2, counterexamples CX1/CX2 | DONE (all PASS) |
| P2-FR1-E | Γ* brackets (none/feature/pattern/observed law) and Γ_cf | DONE |
| P2-FR1-F | plug-in vs population, n ∈ {100, 1000}, 100 reps each | DONE |
| P2-FR1-loss | 0–1 / log loss | NOT_RUN |
| P2-FR2 | complete-case source (w unknown) | NOT_RUN (proposed next) |
| P2-FR3 | valid inference for interval endpoints | NOT_RUN |
| P2-real | real multimodal data with natural missingness | NOT_RUN (needs approval, data license) |

Official run: commit `a762fc3` (code + config committed before running),
`run_manifest.json`, 9.9 s wall, CPU affinity 2, 0 uncertified LPs.
Disclosure: a smoke test on the same scenario was run before the config was
committed; no scenario parameter changed afterwards.

## Engineering vs science (kept separate)
* **Engineering: PASS.** Exact rational LP with primal–dual/Farkas
  certificates; 27 unit tests pass; all FR1 checks pass (see
  RESEARCH_PACKET.md §5.1).
* **Science (one hand-specified population, n_units = 1):**
  H1 supported (Γ*(pattern) ∈ (1.43903, 1.43909], Γ_cf = 1.2689 ≤ Γ*);
  H2 supported (separate bounds 1.7–2.3× wider than the joint interval);
  H3 supported (positive width for Brier D under every constraint kind,
  zero width for the additive and constant-shift controls, as Prop. 2 predicts);
  H4 reported descriptively (plug-in contains the population interval in
  8/100 and 5/100 replications).
  None of this generalises beyond the single population.

## Proof status
Prop. 1 (attainability/sharpness relative to Π), Prop. 2 (row-space
characterisation), Cor. 2′ (Brier), Prop. 3 (closed-form bound), Prop. 4
(unlabelled data bound Γ from below only), Example CX1: PROVED
(written, elementary, self-checked only). C1 (complete-case source) UNPROVED;
C2 (ANOVA vs optimal decomposition) CONJECTURE.

## Stop-rule assessment
FR1 produced identification/evaluation statements beyond "random dropout is
bad" (only the interaction of D moves Δ; label dependence is never identified
from unlabelled data; small Γ can be refuted by unlabelled data). They are
elementary and novelty is unverified (RELATED_WORK.md), so **no new-method
claim** is made. The project continues only as an analysis framework, and only
if P2-FR2 shows it stays informative in the realistic data structure.

## Next decision experiment (one)
**P2-FR2 — complete-case source.** Realistic pipeline: labelled data exist
only for complete cases (the usual curated test set); incomplete units are
observed without labels; `w` is unknown. Parametrise `f(c, r) = P(C = c, R = r)`:
`f(c, 1…1)` is known from the labelled complete cases, `Σ_{c: x_r(c)=v} f(c, r)`
is known from the unlabelled incomplete units, and the Γ-box becomes the linear
constraint `(ρ(r)/Γ) Σ_{r′} f(c, r′) ≤ f(c, r) ≤ Γ ρ(r) Σ_{r′} f(c, r′)` with
`ρ` the observed mask rates. `Δ` is linear in `f`, so the sharp interval is
again two exact LPs.
* Hypothesis: on the FR1 population (each FR1 environment in turn as the true
  policy), Γ*_FR2 stays well above 1.
* Primary metric: Γ*_FR2 (pattern information) vs Γ*_FR1 = 1.439.
* Decision rule (fix before running): if Γ*_FR2 < 1.05 for the MCAR truth,
  stop the framework claim and write P2 up as a negative identification note;
  otherwise proceed to a pre-registered real-data pilot (needs approval).
* Budget: same (2 CPU threads, 120 s, no installs).
