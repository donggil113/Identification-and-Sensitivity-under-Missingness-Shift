
## v4.1 pass (2026-10-02): two-paper comparison table for the manuscript
Scope strictly limited to Subbaswamy et al. (AISTATS 2021) and Guerdan et al.
(ICML 2024); no citation sweep. Done by a read-only agent that text-extracted
the arXiv/ar5iv HTML locally (no summariser) and grep-checked key sentences in
the PMLR PDFs. Read levels: Guerdan — PARTIAL_TEXT (Sec. 3–8 and App. B.1, B.2,
B.6 read; Sec. 1–2, 9 and App. A, C, D, E only grepped); Subbaswamy —
PARTIAL_TEXT (Sec. 2–4 and the appendix DRO section read; proofs/data appendix
not read). Verified facts used in the table: Guerdan Def. 4.1 vs 4.2 (separate
vs joint difference bounds), Asm. 5.1 / Lemma 5.2 (sharp given τ) / Thm. 5.3
(minimal set given τ) and the App. B.1/B.6.2 caveat that this does not give the
tightest regret interval under the causal assumption; cross-fitted plug-in
(Thm. 6.1), doubly robust variant, bootstrap CIs. Subbaswamy Eq. (1)–(4)
(worst (1−α)-subsample, conditional-quantile dual), appendix Eq. (11)–(12)
(one-sided ratio q/p ≤ 1/(1−α)), Thm. 1 (√N-normality, Wald CIs), Remark 6
(discrete W needs noise augmentation), sepsis study with separate worst-case
curves per model (Fig. 4a) and a same-subsample comparison of a baseline
score on one model's worst subsamples. Table: `paper/tab_relatedwork.tex`
(App. "Comparison with the Two Closest Works"); read log and caveats:
`results/derived/p2_relatedwork_readlog_v41.json`.
Novelty status unchanged: the ingredients tagged [UNVERIFIED novelty]
(closure/attainment characterisation with the η check, closed-form Γ_min(o),
unlabelled observed law as linear constraints in the ratio model) were not
found in these two papers; no forward-citation or 2025–2026 search was done.
LP machinery, direct-difference bounding and bounded-ratio sensitivity models
are reused prior art.
