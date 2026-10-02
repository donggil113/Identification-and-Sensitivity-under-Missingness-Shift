# P2 manuscript v4 — source bundle and build instructions

Status (v4.1): PDF BUILT LOCALLY on 2026-10-02 with a user-directory TeX Live 2026
(scheme-basic + required packages) and the official ICML 2026 kit; see
paper/README.md for the checks. Do NOT use an external web compilation service
for this anonymous manuscript.

TARGET_YEAR = 2027, TEMPLATE_YEAR = 2026, SUBMISSION_READY = false.
Style: official ICML 2026 kit in anonymous review mode (`\usepackage{icml2026}`,
no `[accepted]`). The kit is not included (not downloaded here).

## Build on an approved machine with TeX Live (pgfplots, cleveref, mathtools, microtype)
1. The official kit files (`icml2026.sty`, `icml2026.bst`, `algorithm.sty`,
   `algorithmic.sty`, `fancyhdr.sty`) are vendored unmodified in `paper/`
   (source: https://media.icml.cc/Conferences/ICML2026/Styles/icml2026.zip). Do not edit them.
   Extra TeX packages needed beyond scheme-basic: pgf pgfplots cleveref mathtools
   microtype booktabs xcolor natbib url fancyhdr algorithms latexmk psnfss times
   collection-fontsrecommended etoolbox caption float eso-pic forloop.
2. `cd paper && latexmk -pdf -interaction=nonstopmode main.tex`
3. Checks to run on the PDF: main text ends by page 8 (Impact Statement,
   references and appendix may follow); no `??` references or `[?]` citations
   (`grep -n "undefined" main.log`); overfull boxes (`grep -n Overfull main.log`);
   table text legible at 100%; anonymity (no names/affiliations; PDF metadata:
   `pdfinfo main.pdf`).
4. Tables are regenerated from raw with `python3 scripts/make_paper_tables.py`
   (repository root) — already done for this bundle.

## Contents
paper/ (main.tex, main.pdf, references.bib, generated/*.tex, tab_relatedwork.tex,
icml2026 kit files unmodified, claims.csv, README.md),
configs/, src/msid/, scripts/, tests/, results/raw/*.json, results/derived/*.json,
run_manifest.json, STATUS.md, RESEARCH_PACKET.md, RELATED_WORK.md.
Excluded: data/external (UCI Adult, CC BY 4.0 — re-download from
https://archive.ics.uci.edu/dataset/2/adult; sha256 in results/raw/p2_pilot_results.json).

## v4.1 packages (2026-10-02)
* `p2_v4_1_internal.tar.gz` — internal evidence package incl. the built PDF,
  derived validity/threshold JSON, read log of the related-work pass.
* `p2_v4_1_anon_source.tar.gz` — anonymous source + PDF (main.tex, main.pdf,
  references.bib, generated/*.tex, tab_relatedwork.tex, icml2026 kit files,
  BUILD_ANON.md); tar owner stripped; identity-string grep = 0 hits (a string
  check, not a proof of anonymity).

## v4 packages
* `p2_v4_internal.tar.gz` — internal evidence package: paper sources, claims.csv,
  configs, code, tests, small raw/derived JSON (incl. CLEAN1 models + results),
  manifests, STATUS/RESEARCH_PACKET/RELATED_WORK. No data files, no PDF.
* `p2_v4_anon_source.tar.gz` — anonymous submission source only: main.tex,
  references.bib, generated/*.tex, BUILD_ANON.md. Tar owner/group stripped; no git
  remote, no claims/STATUS, no user names or local paths (grep-checked).
  The ICML kit is not included.
* `p2_v3_bundle.tar.gz` — previous bundle, kept unchanged.
