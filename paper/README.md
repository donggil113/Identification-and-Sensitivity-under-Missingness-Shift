# paper/ — manuscript v4 (P2)

v4 = v3 + split repair: empirical pilot table replaced by P2-PILOT-CLEAN1; PILOT1/2 moved to appendix as DEVELOPMENT_WITH_PROFILE_OVERLAP.

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
* **COMPILE_NOT_RUN**: no LaTeX compiler is available here. Static checks only
  (all citation keys resolve in `references.bib`; all `\ref`/`\cref` labels are
  defined; braces and environments balance; main body ~4.3k words + 2 full-width tables (figure moved to appendix); may still EXCEED ICML 2026's 8-page main-body limit — PAGE_LIMIT_UNVERIFIED).
* Build (when the kit and a TeX distribution are available):
  `python3 ../scripts/make_paper_tables.py && latexmk -pdf main.tex`
* `generated/` is produced from `results/raw/` by `scripts/make_paper_tables.py`;
  do not edit by hand.
* `claims.csv` maps every claim to evidence files, experiment IDs, assumptions and status.
* `references.bib` contains only fields verified on PMLR/publisher/Crossref/arXiv/OpenReview pages.
