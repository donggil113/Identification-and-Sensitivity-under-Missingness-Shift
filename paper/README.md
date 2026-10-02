# paper/ — manuscript v4.1 (P2)

v4.1 = v4 + mathematical/editorial corrections on the frozen CLEAN1 result
(Gamma_true vs Gamma_min(o); Hoeffding wording; empty valid sets in setting D;
hypotheses of the setting-C proposition; scope of the outer-coverage
proposition; two-paper related-work table). No new experiment.
v4 = v3 + split repair: empirical pilot table replaced by P2-PILOT-CLEAN1;
PILOT1/2 moved to appendix as DEVELOPMENT_WITH_PROFILE_OVERLAP.

## Build status (v4.1, 2026-10-02)
* **PDF built locally** (`main.pdf`): TeX Live 2026 scheme-basic + packages in a
  user directory (`/home/user/texlive-local`, no sudo), official ICML 2026 kit
  (`icml2026.sty`, `icml2026.bst`, `algorithm.sty`, `algorithmic.sty`,
  `fancyhdr.sty` vendored here **unmodified**, sha256 of icml2026.zip
  8b29290f5828e176debb57ea9cc00252502973d55ea561a2f18a7f0a326bfc6c).
  `latexmk -pdf -interaction=nonstopmode main.tex`: 0 errors, 0 undefined
  references/citations, 0 overfull boxes, 15 pages. Last sentence of the
  Conclusion (label `end:main`) is on **page 8**; Impact Statement and
  references follow; appendices pp. 10–15 (two-paper comparison table
  `tab_relatedwork.tex`, App. E, floats to p. 15). Fonts embedded (Nimbus/Times + CM
  subsets). PDF metadata: Author "Anonymous Authors" (template review mode).
* Page rasterisation NOT_RUN: no rasteriser is available within the approved
  install scope (TeX Live + ICML kit only); checks were made from the .aux page
  map, the log, and a stdlib content-stream inspector (table text >= 7 pt).
* SUBMISSION_READY = false (TARGET_YEAR 2027, TEMPLATE_YEAR 2026; proofs
  self-checked only; novelty UNVERIFIED).

v3 = v2 + D positivity correction, pilot provenance, expected-mask comparison (P2-PILOT2), narrowed title.

v2 = v1 + sign/closure/coverage/zero corrections + P2-PILOT1 (UCI Adult, semi-synthetic masks).

* Title: *What Can Missing-Modality Evaluations Identify under Selective Observation?*
* TARGET_YEAR = 2027, TEMPLATE_YEAR = 2026, **SUBMISSION_READY = false**.
* Style: official ICML 2026 kit, review/anonymous mode (`\usepackage{icml2026}`,
  no `[accepted]`). No official ICML 2027 kit was found on 2026-09-26
  (icml.cc 2027 pages returned 404). The style files are **not included**:
  downloading them (https://media.icml.cc/Conferences/ICML2026/Styles/icml2026.zip)
  was not approved in this environment. Put `icml2026.sty`, `icml2026.bst` (and
  any files shipped with the kit) next to `main.tex` before compiling. Margins,
  fonts and the style name were not modified.
* Earlier versions (v1–v4) were COMPILE_NOT_RUN; the page-limit estimate from word counts is superseded by the v4.1 build above.
* Build (when the kit and a TeX distribution are available):
  `python3 ../scripts/make_paper_tables.py && latexmk -pdf main.tex`
* `generated/` is produced from `results/raw/` by `scripts/make_paper_tables.py`;
  do not edit by hand.
* `claims.csv` maps every claim to evidence files, experiment IDs, assumptions and status.
* `references.bib` contains only fields verified on PMLR/publisher/Crossref/arXiv/OpenReview pages.
