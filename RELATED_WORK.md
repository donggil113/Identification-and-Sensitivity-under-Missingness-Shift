# RELATED_WORK — P2 (missingness-policy shift and model-ranking transfer)

Checked 2026-09-26. **How this was read.** A literature sub-agent searched the
web and read pages through a fetch tool that returns *model-generated
summaries* of the page, so even "PARTIAL_TEXT" means "targeted questions
answered by a summariser from the full text", not a line-by-line reading. The
lead author of this file (the P2 session) personally re-checked only the rows
marked **[lead-checked]**. No PDF was stored in the repository; nothing was
installed or uploaded.

Read levels: FULL_TEXT (none), PARTIAL_TEXT, ABSTRACT_ONLY, SEARCH_SNIPPET_ONLY.

## 1. Closest prior work and what remains different

| Paper | Read level | What it already establishes | Remaining difference from P2 |
|---|---|---|---|
| Subbaswamy, Adams, Saria. *Evaluating Model Robustness and Stability to Dataset Shift.* AISTATS 2021. arXiv:2010.15100 | PARTIAL_TEXT **[lead-checked: abstract + case-study text via summariser]** | Worst-case risk of a fixed model when a user-chosen conditional distribution shifts; includes a **lab-test-ordering** case study where W = test-ordered indicator and Z = demographics **and disease status** (label-dependent missingness policy); worst (1−α) subsample (one-sided ratio); two sepsis models compared by their **separate** worst-case risks. | P2 bounds the **difference** under the same policy, uses a two-sided Γ-box around the dropout law, adds matched pattern/feature marginals and the unlabelled observed law, and characterises point identification. Their set can express P2's with W = R, Z = (X, Y) minus those constraints. |
| Guerdan, Coston, Holstein, Wu. *Predictive Performance Comparison of Decision Policies Under Confounding.* ICML 2024. arXiv:2404.00848 | ABSTRACT_ONLY **[lead-checked]**; sub-agent PARTIAL_TEXT | Bounds the **performance difference** (regret interval) of two policies directly under MSM / Rosenbaum / IV / proximal assumptions; shared uncertainty cancels; minimal uncertainty set (per sub-agent). | Label/decision confounding, not feature masks; no matched marginals or observed-law constraints; no row-space characterisation. **Consequence for P2:** "bound the difference jointly, not separately" (FR1 H2) is *known* and must not be counted as a P2 contribution. |
| Choi, Jeanselme, Elias, Joshi. *ICYM²I: The illusion of multimodal informativeness under missingness.* ICLR 2026. arXiv:2505.16953 | ABSTRACT_ONLY **[lead-checked]**; sub-agent PARTIAL_TEXT | Source/target modality availability differs; naive estimates of a modality's value are biased; IPW correction. Per sub-agent: identification under MAR + positivity, "no theoretical guarantees under MNAR". | P2 targets MNAR (value- and label-dependent) policies via partial identification, not IPW point identification. |
| Zhou, Balakrishnan, Lipton. *Domain Adaptation under Missingness Shift.* AISTATS 2023. arXiv:2211.02093 | PARTIAL_TEXT (sub-agent) | Same P(X,Y), different missingness mechanism; identification results for MCAR underreporting; MNAR left to future work. | Adaptation (learning a predictor), no bounds, no comparison of fixed models. |
| Rockenschaub et al. *Robust prediction under missingness shifts.* arXiv:2406.16484 (preprint) | PARTIAL_TEXT (sub-agent) | Bayes predictor is invariant only under ignorable shifts; Y-dependent shifts are non-ignorable; source performance may not be a good selection criterion. | No bounds or sensitivity model for non-ignorable shifts — P2's target. |

**Verdict (sub-agent search, not exhaustive).** No paper was found that bounds
the risk difference of two fixed masked-input predictors under an unknown,
possibly MNAR missing-*feature* policy with a Γ-box around the dropout law plus
matched marginals / unlabelled observed law, or that characterises point
identification of that difference by additive separability of D(cell, mask).
Caveats: web search only; no systematic Google Scholar / Semantic Scholar /
forward-citation search; 2025–2026 preprints may be missed. Before any novelty
claim, check forward citations of Subbaswamy 2021, Guerdan 2024, Zhou 2023,
ICYM²I.

## 2. Known ingredients (not to be counted as P2 contributions)

| Ingredient used in P2 | Prior work (read level) |
|---|---|
| Sharp LP bounds for discrete missing-data / partially identified problems | Manski 2003 book (SEARCH_SNIPPET_ONLY); Horowitz & Manski, JASA 2000 (ABSTRACT_ONLY); Horowitz, Manski, Ponomareva, Stoye 2003 (SEARCH_SNIPPET_ONLY; sharp bounds with missing covariates are non-convex when P(X,Y) is unknown — P2 is linear only because A1 fixes P(X,Y)); Balke & Pearl, JASA 1997 (SEARCH_SNIPPET_ONLY); Chen, Simchi-Levi, Xiong arXiv:2602.16061 (ABSTRACT_ONLY, LP bounds for MNAR outcomes) |
| Bounded density-ratio sensitivity models (Γ) | Rosenbaum, Biometrika 1987 (SNIPPET); Tan, JASA 2006 MSM (SNIPPET); Zhao, Small, Bhattacharya, JRSSB 2019 — applies MSM to missing data (ABSTRACT_ONLY); Dorn & Guo, JASA 2023 (ABSTRACT_ONLY); Sahoo, Lei, Wager, *Learning from a Biased Sample*, arXiv:2209.01754 — Γ-biased sampling P(S=1\|x,y)/P(S=1\|x) ∈ [1/Γ, Γ] (PARTIAL_TEXT) |
| Worst-case evaluation over conditional shifts / subpopulations | Subbaswamy et al. 2021 (above); Li, Namkoong, Xia, NeurIPS 2021 (ABSTRACT_ONLY); Thams, Oberst, Sontag, NeurIPS 2022 (ABSTRACT_ONLY) |
| Bounding a comparison/regret directly | Guerdan et al. 2024 (above); Kallus & Zhou, NeurIPS 2018 (ABSTRACT_ONLY); Kallus, Mao, Zhou arXiv:1906.00285 (ABSTRACT_ONLY; venue unverified) |
| Tipping-point summary (Γ* style) | VanderWeele & Ding, E-value, Ann Intern Med 2017 (SNIPPET); Rosenbaum sensitivity values |
| "Constant on a transportation polytope iff cost = u_i + v_j" (Prop. 2b) | Follows in one line from rank p+q−1 / dimension (p−1)(q−1) of transportation polytopes — De Loera & Kim arXiv:1307.0124 (PARTIAL_TEXT; statement not seen verbatim). Peyré & Cuturi 2019 (ABSTRACT_ONLY; location of the identity **not verified — do not cite a location**). Capacity-constrained OT: Korman & McCann (ABSTRACT_ONLY). |
| Per-instance adversarial feature deletion | Globerson & Roweis, ICML 2006 (PARTIAL_TEXT); Dekel & Shamir, ICML 2008 (PARTIAL_TEXT) — unconstrained adversary, learning one model |
| Missingness mechanism changes between development and deployment (clinical) | Sperrin et al., J Clin Epidemiol 2020 (ABSTRACT_ONLY); Groenwold, Diagn Progn Res 2020 (PARTIAL_TEXT); Sisk et al., SMMR 2023 (PARTIAL_TEXT; simulation incl. MNAR-Y); Li et al., Stat Med 2021 (PARTIAL_TEXT; "all methods are biased under MNAR"); Tsvetanova et al. arXiv:2504.06799 (ABSTRACT_ONLY) |
| Prediction with missing values (same mechanism train/test) | Josse et al. arXiv:1902.06931 (ABSTRACT_ONLY; venue from snippet); Le Morvan et al. NeurIPS 2020/2021 (ABSTRACT_ONLY); Zaffran et al. ICML 2023 conformal with missing values (ABSTRACT_ONLY); Catoire et al. arXiv:2603.17599 (PARTIAL_TEXT) |
| MNAR evaluation of rankings (labels/ratings missing) | Marlin & Zemel, RecSys 2009 (PARTIAL_TEXT); Schnabel et al., ICML 2016 (ABSTRACT_ONLY); Steck KDD 2010 (SNIPPET); Lakkaraju et al. KDD 2017 (ABSTRACT_ONLY); Coston et al. FAT* 2020 (ABSTRACT_ONLY); Rambachan, Coston, Kennedy arXiv:2212.09844 (ABSTRACT_ONLY) |
| Missing-modality robustness (random / empirical protocols, no mechanism theory) | Ma et al. CVPR 2022 (ABSTRACT_ONLY); ModDrop, Neverova et al. TPAMI 2016 (ABSTRACT_ONLY); SMIL, AAAI 2021 (SNIPPET); MuteBench arXiv:2605.15235 (ABSTRACT_ONLY); Yin et al. arXiv:2602.23614 (ABSTRACT_ONLY). No benchmark found that reports rankings flipping between random dropout and natural missingness. |
| Contrast: rankings often do transfer under natural shift | Miller et al., *Accuracy on the Line*, ICML 2021 (SNIPPET) |

## 3. What P2 may still add (moderate confidence; not yet a claim)
1. The estimand/policy set for **feature masks**: Δ(π) for two fixed predictors
   under the same unknown π(r | x, y), Γ-box around the dropout law, with
   matched marginals and/or the unlabelled deployment law.
2. The identification reading of a known linear-algebra fact: only the
   cell × mask interaction of D moves Δ; with unlabelled deployment data and
   Brier loss, Δ is identified iff f_A − f_B is constant (Cor. 2′).
   Low novelty as mathematics; possibly new as an evaluation statement.
3. Prop. 4 (unlabelled data refute small Γ but never bound it above) —
   close to standard testable-implication arguments; novelty unverified.

FR1 evidence relevant to (1): in the single FR1 population, adding matched
pattern rates to the no-constraint difference bound moves Γ* only from 1.397
to 1.439; the unlabelled observed law moves it to 2.069. The distinctive
ingredient that carries information is therefore the observed-law constraint,
not the matched marginal (one population; not general).

## 4. Not checked in this session (to verify before writing)
* Inference for partially identified parameters (e.g. Imbens & Manski 2004;
  Stoye 2009) — needed for P2-FR3; NOT_CHECKED.
* Citation details unverified: Sperrin 2020 volume/pages; Josse et al. venue;
  Stempfle et al. (arXiv:2505.03393) venue; Lakkaraju/Dekel–Shamir pages;
  Li–Namkoong–Xia journal version; Kallus–Mao–Zhou venue; Sahoo–Lei–Wager final
  venue; De Loera–Kim venue; Robins–Rotnitzky–Scharfstein 2000 pages;
  Rockenschaub et al. status; all SEARCH_SNIPPET_ONLY rows.
