# STATUS — P2: What Can Missing-Modality Evaluations Identify under Selective Observation?

## Update (sixth session, 2026-10-02): CLEAN1 frozen; math/statistics corrections; manuscript v4.1 PDF built
* State read: HEAD 2517b32 = origin, clean tree; Adult hashes unchanged. CLEAN1 is
  frozen as the empirical result (no new training, mask draw, Γ grid or data).
* Corrections (RESEARCH_PACKET §15): Γ_true (hidden joint, 2.38 for CLEAN1 MNAR)
  vs Γ_min(o) (observable threshold; closed form, 1.311; grid 5/4 infeasible, 3/2
  feasible); Hoeffding wording (integrality is not the issue; no sampling model is);
  **setting D has no valid law at Γ_cc ≤ 5/4 for the CLEAN1 MNAR law** (η_max = 0;
  table category ∅ᶜ; D refutes MCAR like C; B never can); setting-C proposition
  hypotheses (ρ_r > 0, hidden Γ_true, interiority construction); outer-coverage
  proposition scope (Δ_nat covered only for Γ ≥ Γ_true; Σκ_lo = 0 branch); 1,029
  conflicting-label groups not asserted to be errors. Human statistical reviewer
  UNASSIGNED.
* Review method: three read-only reviewer agents (one per proposition) with partial
  adversarial refutation (see packet §15.9); this is an AI cross-check, not an
  independent human review.
* Derived (no raw change): `results/derived/p2_validity_eta.json` (η_max per B/D row,
  Γ_min(o) and Γ_true per law; 5.6 s). Code: `valid_set_eta`, `gamma_min_closed_form`,
  D build no longer forces structural zero for unsampled strata, `classify_sign(valid=)`;
  39 unit tests PASS (8 s). Frozen results reproduced identically.
* Build (approved limited scope): user-dir TeX Live 2026 scheme-basic + packages
  (install 210 s + 3 s; ≈107 MiB container downloads + 5 MB installer + 0.2 MB ICML
  kit; 302 MB disk) and the official icml2026 kit vendored unmodified. `paper/main.pdf`:
  14 pages, 0 errors, 0 undefined refs/cites, 0 overfull; last Conclusion sentence
  on **page 8** (label end:main); fonts embedded; Author metadata "Anonymous Authors";
  no identity strings. Page rasterisation NOT_RUN (no rasteriser within the approved
  scope). Each latexmk run 2–4 s.
* SUBMISSION_READY = false (TARGET_YEAR 2027 / TEMPLATE_YEAR 2026; proofs self-checked;
  novelty UNVERIFIED).
* Next decision (one): whether to commission an independent human statistical review
  of the three propositions (App. A) before any submission step.

---

## Update (fifth session, 2026-09-27): split repair (P2-PILOT-CLEAN1), manuscript v4
* State read: HEAD 8bf9da8 = origin, clean; Adult hashes unchanged; no compiler.
  No new download/install. Sandbox checkout (no /nvmedata).
* PILOT1/PILOT2 → DEVELOPMENT_WITH_PROFILE_OVERLAP (split key contained the target
  string; 956 profiles crossed). Raw preserved.
* P2-PILOT-CLEAN1 (repair validation, not independent confirmation): config+script
  committed c980ca2 before the single run (49.1 s wall / 49.1 CPU-s, one process on
  2 CPUs). 0 unresolved labels, 0 profile leakage, predictors refit once and hashed.
  MNAR: cc dropout +0.0004 vs true −0.0028 (opposite); MCAR agree. RESEARCH_PACKET §14.
* Manuscript v4: pilot section rewritten on CLEAN1 (Table clean1); PILOT1/2 table
  moved to the appendix dev log; abstract/limitations/conclusion updated.
  COMPILE_NOT_RUN. Bundles in export_bundle/ (internal evidence vs anonymous source).
* Next decision: whether to build the PDF on an approved TeX environment
  (TeX Live + ICML 2026 kit) — needs approval; no new research started.

---

## Update (fourth session, 2026-09-27): P2-PILOT2, D positivity, provenance, manuscript v3
* Actual state read: branch `claude/keen-franklin-ua0v00` at ed75cfc (clean, = origin);
  Adult files present locally with hashes equal to PILOT1's manifest.
  Approvals: the user's explicit approval (previous session, AskUserQuestion answer
  "Adult 다운로드 승인") covered downloading UCI Adult only. Nothing new was
  downloaded or installed this session. No compiler exists; LaTeX install not approved.
  The sandbox checkout was not moved to /nvmedata (not reachable from here).
* P2-PILOT2 (post hoc, exploratory; code/config committed 43d5d97 before running;
  16.5 s wall / 16.4 CPU-s): D endpoint η-LP (B WEAK_A kept; D corrected to
  A_NO_MARGIN), provenance flow, frozen-predictor reproduction, expected-mask law
  comparison, schema check. See RESEARCH_PACKET §13.
* Corrected interpretations: D positivity (v2 wrong); "entity" → attribute-tuple
  group (not persons; 956 near-duplicates cross the split); pilot "modalities" →
  grouped tabular features; population = unweighted deduplicated records.
* Preserved: FR1/FR2/PILOT1 raw, configs, exploratory labels; no STOP/FAIL existed.
* Manuscript v3: `paper/main.tex` (title narrowed with "A Finite-Support Analysis";
  COMPILE_NOT_RUN; source bundle + exact build command in `export_bundle/`).
* Costs this session: tests ~7 s; PILOT2 16.5 s wall; provenance addendum 0.9 s;
  table generation <1 s. No failed or repeated runs.
* Next decision: whether a natural-missingness dataset meeting the admission
  conditions (App. of the paper) exists — selection/licence/download need approval.

---

## Update (third session, 2026-09-26): corrections, pilot, manuscript v2
* Corrections before any new bound/loss (RESEARCH_PACKET §11): sign categories with
  endpoint attainment; FR2 B/D at Γ_cc ∈ {1,5/4} re-labelled **WEAK_A** (v1 said
  "undetermined" — interpretation error, raw unchanged); b_r reverse map and
  CLOSURE_ONLY points; M_cc absolute continuity added to the definition; Γ_box vs
  Γ_cc separated; coverage restated as confidence-region feasible-set inclusion
  (does not validate Γ); empirical zeros / n_complete = 0 handled.
* P2-PILOT1 (UCI Adult, semi-synthetic masks) pre-registered at `1291cc4`, data
  download approved by the user, run once (12.7 s): MNAR rule → complete-case
  dropout +0.0006 vs held-out −0.0038 (sign disagreement); control agrees;
  identified sets/outer CIs BOTH_ORDERS or empty everywhere (RESEARCH_PACKET §12).
* No new bound or loss added. FR1/FR2 raw preserved; FR2 re-run bit-identical after
  the `levels` generalisation.
* Manuscript v2: `paper/main.tex` (COMPILE_NOT_RUN; page limit unverified — main
  body ≈ 4.3k words + 5 tables + 1 figure may exceed 8 pages). 35 unit tests PASS.
* Cost log additions: attainment re-aggregation 1.3 s; FR2 bit-repro check ~33 s;
  pilot pipeline test on fake data 8.6 s; pilot run 12.7 s; download 0.6 MB.
* Next decision experiment (single): P2-real — a dataset with *natural* modality
  missingness where incomplete units also have labels (so Δ_nat is checkable);
  needs dataset selection, license and download approval (and ethics approval if
  clinical). Everything else about the pilot pipeline can be reused.

---
(Previous session status below, kept for the record.)


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
