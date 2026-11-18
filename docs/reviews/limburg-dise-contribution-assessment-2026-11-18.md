# Contribution assessment after DISE Steps 1–3

18 November 2026. Internal research judgment for Brian, who writes dissertation
prose. Based on the completed multiyear/repeatability outputs, the existing
design and audit, the dissertation scope benchmark, and a fresh check of primary
literature. This assessment introduces no new model, acquisition, analysis queue
or condition requiring a favourable result. The existing RQs remain in place.

## Judgment

**There is enough empirical substance for a focused applied dissertation chapter.
The paper has modest-to-moderate empirical novelty and little methodological
novelty.** Its strongest contribution is an independent test of the portability
and high-water limitations of an emerging satellite-conditioned correction
method. That is a credible specialist-paper candidate; acceptance and committee
judgment cannot be guaranteed. It is not a new hydrological algorithm or a
demonstrated improvement in flood warnings.

I recommend finishing the saved Step 4 and developing this study into a paper,
rather than restarting model selection. This is a judgment based on the
evidence and comparator literature, not a statement that any numerical gain
automatically makes a doctoral contribution. The earlier conversation's
unqualified declaration that the chapter was definitively secured was too strong.

## What the closest literature already establishes

| Source | Existing contribution | Implication for our novelty |
| --- | --- | --- |
| Lin et al., DISE, 2026 preprint | Pooled log-residual XGBoost correction, global discharge, weather and AlphaEarth; comparisons beyond land-cover descriptors; 41 Yangtze gauges, all fitting/tuning/testing in 2017 | Our estimator family and basic embedding-correction idea are adaptations. DISE explicitly asks for cross-year and cross-basin transfer testing, which our experiment addresses in another product/river domain. |
| Liu et al., GRL 2026 | AlphaEarth/StefaLand catchment descriptors; 531 CAMELS temporal cases and 3,434 global PUB basins; stronger embedding value under spatial transfer; conventional controls, multiple fusion strategies and extreme-flow diagnostics | The temporal-versus-spatial contrast is already established. High-flow evaluation and careful conventional controls are not novel in themselves. Our question concerns whether that capability carries into a particular transferred global-model correction. |
| Qu et al., arXiv v3, November 2026 | AlphaEarth versus conventional descriptors, in/out-of-sample testing, donor-pool size/composition and withheld basin clusters | Catchment-dependent benefit and sensitivity to the donor domain are established questions. River heterogeneity alone is not an original mechanism. |
| Ou and Zheng, GRL 2026 | Satellite embeddings improve temporal/spatial runoff generalization in Australian catchments; representation and human disturbance are examined | Neither a new country nor an average embedding improvement establishes a new conceptual claim. |
| Hales et al., SABER 2022 | Model-agnostic bias correction, donor transfer and ungauged-location application | Correcting a global model without target calibration is established hydrological practice. Our donor-FDC is a reference, not a reproduced SABER implementation. |

DISE PDF §§2.2 and 4.2/5 and Table 1 were re-read from the held full PDF.
Its conventional-control experiment includes forest/cropland/urban fractions;
we add terrain, area, soil-storage/climate and location descriptors under common
definitions. This strengthens the local test, but Liu et al. already have rich
CAMELS controls. We should not portray the wider literature as relying only on
weak land-cover baselines.

Liu et al. are particularly consequential for our assessment. Their §4 already
explains the weak temporal/stronger PUB contrast in terms of historical basin
responses being learned during fitting. Their §3.3 reports limited extreme-flow
bias gains from simple concatenation and larger gains with gated LSTM fusion.
Consequently, our high-water result neither refutes that paper nor shows that
AlphaEarth is intrinsically unable to help with extremes. It concerns our
fixed-2017 descriptors, GEOGLOWS product, residual target, XGBoost learner,
training/selection regime and European catchments. Their high-flow volume-bias
diagnostic and our daily p99 MAE are different endpoints.

## What this study adds

The defensible contribution is the **combination** of the following evidence,
rather than claiming that any one comparison is unprecedented:

1. **An independent, chronological portability test of a DISE-inspired correction.**
   The local river-withheld tests span 2021–2025, with earlier-year validation,
   regional donor training and whole-river withholding, including all three
   Wurm gauges together. Reserved Ahr/Erft/Sieg observations provide a separate
   external correction-transfer test for 2021–2024. This extends the direct
   one-year DISE reconstruction experiment and tests a different global product.
2. **A repeatable but bounded positive result.** Incremental AlphaEarth all-day
   MAE reduction is 13.86% on held local rivers (0.3839 to 0.3307 mm/day), positive in all five years and
   four of five rivers. It survives removing any one year/river. The 95%
   whole-year percentile range is 11.90–16.64% for these fixed predictions and
   rivers. This is more than one favourable case or a gain over an uncorrected
   model alone. Voer's 8.31% worsening remains a substantive counterexample.
3. **A quantified limit on extrapolating that gain to the high-water purpose.**
   Local spatial high-water MAE slightly worsens (1.06%); the exploratory joint-
   year reduction range spans −5.36% to +1.63%, with 993/999 draws defined. The
   corresponding all-day improvement cannot be used as evidence of an added
   high-water gain. Clean-only/selection sensitivities and largest-flow cases
   reinforce the limitation. This is a result about the tested method, not a
   universal failure of satellite embeddings or an equivalence proof.
4. **A test of external benefit that exposes its concentration.** External
   all-day improvement is 4.67%, largely Erft-driven; omitting Erft leaves 0.18%.
   Ahr improves slightly, Sieg worsens slightly. This limits a claim of broadly
   transferable benefit and gives an empirically supported boundary to a
   promising spatial-representation approach.

The local temporal all-day contrast is −1.44%, consistent with limited added
descriptor value when historical target-river labels are permitted. Our data
support a comparison of these two fitting settings; they do not isolate a
causal effect of spending money on gauges. Training populations and fitted
models change between regimes. The distinction agrees with prior work and
should be presented as corroboration, not a new discovery.

## Is the evidence strong enough for those claims?

**Yes for a bounded empirical validation.** Identical rows, common model/weather
inputs, explicit attribute and embedding arms, matched tuning budgets, expanded
capacity checks, whole-river withholding, temporal order, external labels excluded from
fitting and selection, all eligible verification and paired dependence-aware
analysis make the comparisons meaningful. The source/input checks and numerical
tests support correctness; they are not themselves evidence of scientific novelty.

Both learned arms fit a log residual and use all-day reconstructed-discharge
RMSE for primary selection. This is a controlled test of the specified
correction, not a search for the best possible extreme-flow objective. Its
failure to add high-water skill cannot establish that a separately designed
high-water learner would fail. Conversely, that limitation does not invalidate
testing whether whole-record gains carry into high water. No causal explanation
of the tail errors follows from the choice of loss alone.

The effective population is smaller than the row counts suggest: seven local
gauges on five named river groups and external observations in three nested
river systems. Five local test years are not independent climate replications;
rolling fits share training history. Some high-water observations are qualified,
and external row-level QA is unknown. Clean-only and external uncertainty lose
required gauges in many draws. Those failures remain reported, with conditional
intervals labelled. Main estimates are not discarded merely because quality or
support is imperfect.

The primary high-water question receives a largely negative/uncertain answer.
The all-day result was an existing secondary outcome and can be reported fully.
It should not silently replace the primary outcome or turn the study into a
claim of reliable extreme-flow reconstruction. The broader chapter has had many
exploratory iterations; that history should be disclosed concisely. The current
design and split specifications were fixed before the multiyear output, but
that does not make the whole project a blinded confirmatory investigation.

## DRR, FEWS, people and policy

The concrete application is an agency or model consumer considering whether
to transfer a global discharge correction to a river without local correction
labels. The study supplies evidence about expected daily reconstruction error,
river-specific harms, and the need to verify high-water performance separately
from whole-record performance. That is relevant to the reliability of inputs
that may later be used for risk and warning work.

The present work does **not** measure as-issued forecast skill, operational
threshold decisions, missed warning rates, public actions, avoided losses or
the return on a monitoring investment. Flood-warning benefits and resource
allocation effects must remain implications/questions for subsequent adoption
work. No interviews, social dataset or welfare model is needed to present this
bounded contribution honestly. The portfolio's Peja and other chapters provide
additional adaptation/risk applications; each chapter need not independently
demonstrate the whole chain to human welfare.

For UNU-MERIT, my judgment is that this can contribute as an empirical study of
technology transfer and limits of environmental-information capability. Its
policy discussion must stay grounded in the measured information task. Calling
it an institutional-adoption study would require evidence we do not have.

## Recommended finish, with no new experiment programme

Proceed with the already saved Step 4:

- Present the primary high-water answer alongside the repeatable all-day
  transfer finding, with raw/conventional/embedding effects distinguished.
- Use the complete year/river results and supported symmetric event examples
  to show where aggregate performance conceals harm. Explanations that have
  not been identified remain hypotheses; log residuals, routing mismatch,
  regulation or training support cannot be declared the cause from an error plot.
- State how this result extends DISE's one-year setting and where it replicates
  Liu/Qu rather than claiming their questions were unasked.
- Keep the paper sized as one applied validation study. The dissertation scope
  benchmark supplies no reason to add another model family or geography.

No new acquisition or architecture is necessary for this recommendation.
Liu's gated model is relevant literature and a limit on generalization, not a
requirement to start another tournament. A new method or causal mechanism would
be a different, larger contribution; neither is mandatory to report this
original, carefully bounded empirical test.

**Overall: worth writing and defensible as an applied empirical chapter;
plausibly publishable with incremental novelty; stronger claims about novel
mechanisms or improved flood warnings are not supported.** This recommendation
does not depend on finding an additional positive flood result.

## Primary sources checked

- [Lin et al., DISE preprint](https://doi.org/10.5194/egusphere-2026-1834).
  Held full PDF: `data/raw/foundation_assets/documents/dise-review-2026-11-16/lin-et-al-2026-dise-preprint.pdf`.
  §§2.2, 3.2–3.3, discussion and conclusions checked; single-year and future
  cross-year/cross-basin statements verified. Remains a preprint on the page inspected.
- [Liu et al., GRL](https://doi.org/10.1029/2026GL122814).
  Primary full text §§2–5 checked, including extreme-flow endpoints, concatenation
  versus gating and explicit limitations of random global spatial folds.
- [Qu et al., v3](https://arxiv.org/abs/2601.01558v3).
  Primary abstract and PDF methods/design checked; submitted manuscript, not
  treated as a peer-reviewed finding. No dedicated extremes claim inferred from it.
- [Ou and Zheng, GRL](https://doi.org/10.1029/2025GL121604).
  Primary abstract/introduction checked; 455 Australian catchments, temporal and
  spatial representation claims. No more detailed methodological claim made here.
- [Hales et al., SABER](https://doi.org/10.3390/hydrology9070113).
  Primary article checked for existing bias-correction/regionalization context.
- [Completed Step 3 evidence](../limburg-dise-repeatability-2026-11-18.md).
- [Dissertation chapter-size benchmark](../../../dissertation-manuscript/docs/reviews/chapter-scope-benchmark-audit-2026-11-11.md).
