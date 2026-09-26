# STATUS — P2: What Can Missing-Modality Evaluations Identify under Selective Observation?

Date: 2026-09-26 (second session). Branch: `claude/keen-franklin-ua0v00`.

## Starting state of this session (verified)
Checkout at `0eb7bab` (FR1 code/results/docs, related-work pass 1). No
CLAUDE.md. Remote branch identical. No LaTeX compiler, no matplotlib/numpy;
Python stdlib only. Nothing installed or downloaded (ICML style kit not downloaded).

## Labels that stay in force
* **All P2 experiments are EXPLORATORY/DEVELOPMENT**: the only population was
  seen in a smoke test before FR1 pre-registration (disclosed in both configs).
* FR1 is an exact computation on one *known* population (oracle observation model).
* No new-method claim; novelty of the observation-model account is UNVERIFIED.
* No STOP/FAIL existed to preserve; no check has failed in FR1 or FR2.
* **Withdrawn**: the FR2 "decision rule" in the previous STATUS (Γ* < 1.05 →
  stop; relative improvement ≤ 1.1 → stop the independent-contribution claim)
  is no longer used as a novelty/publishability criterion (instruction of this
  session). FR2 reports what information identifies and whether it survives
  sampling, descriptively.

## Experiment register
| ID | What | Status |
|---|---|---|
| P2-FR1-A…F | oracle (w known) finite-support analysis | DONE (exploratory), raw unchanged |
| P2-FR2-A | truths, dropout estimands, Γ_cc per environment | DONE |
| P2-FR2-B | settings A–D × Γ grid, direct vs separate, MCAR truth | DONE |
| P2-FR2-C | secondary truths, settings A and C | DONE |
| P2-FR2-D | Γ* brackets (A, C) | DONE |
| P2-FR2-E | structural-zero support check | DONE |
| P2-FR2-F | finite sample: plug-in vs outer CI, 2 draws × n ∈ {1e3, 1e4, 1e5} | DONE (illustration; no MC coverage) |
| P2-FR2-G | identification-criterion audit on FR1 sets | DONE |
| P2-FR1-loss | 0–1 / log loss | NOT_RUN |
| P2-FR3 | less conservative valid inference; coverage study | NOT_RUN |
| P2-S | label availability independent of the mask | NOT_RUN (not analysed) |
| P2-real | real multimodal data with natural missingness | NOT_RUN (needs approval) |

FR2 run: pre-registration commit `b5225f6`, `results/raw/p2_fr2_manifest.json`,
33.3 s wall, 2-CPU affinity, 0 uncertified LPs, 6/6 engineering checks PASS.

## Cost log (all CPU, 2-thread affinity, stdlib)
FR1 smoke (<5 s, before pre-registration), FR1 official 9.9 s, FR1 rerun ~10 s,
FR2 timing smoke ~2 s (12 intervals, numbers seen, disclosed), FR2 official
33.3 s, unit tests ~7 s per invocation (32 tests). Also recorded in `run_manifest.json`.

## Engineering vs science vs novelty
* **Engineering: PASS** (certificates, nesting, containment-when-in-model,
  support check, outer-CI containment, criterion audit; 32 unit tests).
* **Toy-population science (exploratory, n_units = 1)**: setting C point-
  identifies at Γ = 1 but loses the sign by Γ ≈ 1.447; B/D are undetermined even
  at Γ = 1; the oracle certifies the sign without any model; complete-case
  dropout misranks E2m; a too-small Γ certifies the wrong sign; plug-in
  refutes MCAR spuriously in 6/6 draws; the outer CI keeps the sign only at n = 1e5.
* **Real-model results / external utility**: none (NOT_RUN).
* **Novelty**: UNVERIFIED; known ingredients listed in RELATED_WORK.md and
  excluded from the contribution list.

## Proof status (manuscript App. A)
Exact linearisation, closure in B/D, MCAR-boundary proposition, setting-C Brier
characterisation, support proposition, outer-CI validity: PROVED (written,
elementary, self-checked only). Oracle-A remark: PROVED (sketch). General
criterion: KNOWN. Open: closure removal (UNPROVED), outer-CI width (UNPROVED),
mask-independent label availability (NOT STARTED).

## Manuscript v1
`paper/main.tex` (ICML 2026 anonymous style, provisional; TARGET_YEAR 2027,
TEMPLATE_YEAR 2026, SUBMISSION_READY = false). **COMPILE_NOT_RUN** (no
compiler; style kit not vendored). Sections complete: Abstract, Introduction,
Related Work, Problem Setup, Identification, Counterexamples, Sampling
Uncertainty, Experiments, Limitations, Conclusion, Impact Statement,
Appendices A–D. Remaining `\todo`: P2-real (×2), P2-S, P2-FR3, RW
forward-citation search, P2-FR1-loss. Claims ↔ evidence: `paper/claims.csv`.

## Next decision experiment (one)
**P2-real pilot.** Pre-register one public multimodal dataset whose natural
modality missingness co-occurs with labels for *incomplete* units as well, so
that Δ_nat is computable as a held-out check. Hide the labels of incomplete
units to emulate setting C, fit two fixed simple models on complete cases,
discretise features by a pre-registered rule, and report: complete-case
dropout ranking, setting-C identified intervals and outer CIs at pre-registered
Γ values, and the label-revealed Δ_nat. The question it decides: do the
phenomena shown on the toy population (loss of sign at small Γ, dropout
misranking, sampling-driven indeterminacy) appear on real data, or do real
rankings stay determined over the Γ range an analyst would defend?
**Unapproved resources needed:** dataset download and license review; possibly
additional CPU budget beyond 120 s per run; any use of patient data would need
ethics approval and must stay local. No GPU or paid API is needed.
