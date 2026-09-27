# P2 manuscript v4 — source bundle and build instructions

Status: COMPILE_NOT_RUN. No PDF was produced in the authoring environment
(no LaTeX compiler; installing one was not approved). Do NOT use an external
web compilation service for this anonymous manuscript.

TARGET_YEAR = 2027, TEMPLATE_YEAR = 2026, SUBMISSION_READY = false.
Style: official ICML 2026 kit in anonymous review mode (`\usepackage{icml2026}`,
no `[accepted]`). The kit is not included (not downloaded here).

## Build on an approved machine with TeX Live (pgfplots, cleveref, mathtools, microtype)
1. Obtain the official kit: https://media.icml.cc/Conferences/ICML2026/Styles/icml2026.zip
   and copy `icml2026.sty`, `icml2026.bst` (and any other kit files it needs, e.g.
   `algorithm.sty`, `algorithmic.sty`, `fancyhdr.sty` if shipped) next to `paper/main.tex`.
   Do not edit them.
2. `cd paper && latexmk -pdf -interaction=nonstopmode main.tex`
3. Checks to run on the PDF: main text ends by page 8 (Impact Statement,
   references and appendix may follow); no `??` references or `[?]` citations
   (`grep -n "undefined" main.log`); overfull boxes (`grep -n Overfull main.log`);
   table text legible at 100%; anonymity (no names/affiliations; PDF metadata:
   `pdfinfo main.pdf`).
4. Tables are regenerated from raw with `python3 scripts/make_paper_tables.py`
   (repository root) — already done for this bundle.

## Contents
paper/ (main.tex, references.bib, generated/*.tex, claims.csv, README.md),
configs/, src/msid/, scripts/, tests/, results/raw/*.json, results/derived/*.json,
run_manifest.json, STATUS.md, RESEARCH_PACKET.md, RELATED_WORK.md.
Excluded: data/external (UCI Adult, CC BY 4.0 — re-download from
https://archive.ics.uci.edu/dataset/2/adult; sha256 in results/raw/p2_pilot_results.json).

## v4 packages
* `p2_v4_internal.tar.gz` — internal evidence package: paper sources, claims.csv,
  configs, code, tests, small raw/derived JSON (incl. CLEAN1 models + results),
  manifests, STATUS/RESEARCH_PACKET/RELATED_WORK. No data files, no PDF.
* `p2_v4_anon_source.tar.gz` — anonymous submission source only: main.tex,
  references.bib, generated/*.tex, BUILD_ANON.md. Tar owner/group stripped; no git
  remote, no claims/STATUS, no user names or local paths (grep-checked).
  The ICML kit is not included.
* `p2_v3_bundle.tar.gz` — previous bundle, kept unchanged.
