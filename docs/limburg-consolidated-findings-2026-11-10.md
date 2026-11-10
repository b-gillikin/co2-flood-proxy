# Consolidated findings review — 10 November 2026

Internal evidence/interpretation aid for Brian; not dissertation prose. No models refitted or configurations selected in this review.

The completed study does not establish a general advantage from satellite foundation models. It does establish distinct outcomes by task and adaptation: Copernicus-FM radar change retains performance as training labels are reduced and improves on the physical change control, while the tested TerraMind, Galileo and Prithvi adaptations generally lose against trained same-input controls. Local reference agreement is substantially constrained by observability, reference timing and domain transfer. These results apply to the tested checkpoints, frozen/adapted configurations, training procedures and populations, not every possible use of these model families.

## Benchmark findings

Scores below are mean event intersection-over-union (IoU; higher is better), after averaging optimization seeds within events. They are not percentages of correctly classified pixels. Binary-water tasks have 11 held-out events; the separate radar-change task has 20 event IDs. Comparisons belong within rows/tasks; different inputs, resolutions and targets prevent a cross-task model ranking.

| Task | Model, full training labels | Compact U-Net, full labels | Standard U-Net, full labels | Model, 20% training | Model, 5% training |
|---|---:|---:|---:|---:|---:|
| TerraMind multimodal water | .745 | .764 | .776 | .661 | .580 |
| Galileo radar water | .496 | .541 | .512 | .456 | .151 |
| Prithvi optical water | .636 | .721 | .698 | .620 | .562 |
| Copernicus-FM radar flood change | .574 | .580 | .581 | .565 | .558 |

### TerraMind

Full-label native minus standard U-Net is −.031 IoU, exploratory event-bootstrap interval [−.050, −.005]. The gap expands to −.094 at 20% training and −.153 at 5%; the model wins on only one of 11 events at each budget. At full labels it exceeds the physical control by .043, but that interval spans zero. This tested frozen multimodal representation/decoder does not demonstrate an accuracy or label-efficiency advantage over trained raw-input controls.

### Galileo

It substantially improves over a raw pixel-linear radar classifier at full labels (+.326 IoU) and 20% (+.270), demonstrating useful spatial representation relative to that limited comparator. However, compact U-Net is better at both budgets; the full-label difference from standard U-Net is −.016 [−.053, .013], which is not an equivalence result. At 5%, native IoU falls to .151 versus .466 for standard U-Net, and the deficit occurs in all 11 events and all three seeds. This is a reproducible limitation of this configuration/training procedure, not proof that Galileo intrinsically fails with sparse labels.

### Prithvi

Full-label native minus standard U-Net is −.061 [−.104, −.002]; against pixel-linear optical inputs it is −.113. Standard U-Net remains better at both reduced budgets. There is no demonstrated accuracy, label or runtime advantage for this tested adaptation. These optical water results cannot be generalized to other Prithvi checkpoints, fine-tuning routes or applications.

### Copernicus-FM

The clearest favorable result is against the physical radar-change control: +.099 [.052, .152] at full labels, +.089 [.045, .138] at 20%, and +.082 [.022, .149] at 5%. Its absolute mean IoU changes only from .574 to .558 across the full-to-5% training range. At 5% it also improves on pixel-linear change classification by .085 [.033, .145].

Differences from standard U-Net are −.007 [−.038, .024], +.016 [−.026, .069], and +.024 [−.025, .077] across the three budgets. Thus the results suggest retained performance under reduced training labels, but do not establish superiority or equivalence to trained U-Net. At 5% only 10 of 20 event differences favor the encoder, despite the positive overall mean. The comparison with the physical control concerns the implemented calibrated physical method, not all operational radar mapping systems.

## Label and optimization qualifications

The 20%/5% settings reduce **training chips**, while validation labels remain available for tuning, selection and stopping. They are not 20%/5% total annotation budgets. At 5% training, combined train-plus-validation use is approximately 28.5–31.5% of the available train-plus-validation chip pool for the binary-water tasks and 17.1–57.1% for radar change, depending on fold. Pixels/chips are not independent annotations or annotation-hours. This materially narrows any policy claim about reducing local labeling cost.

Some validation-selected rates lie at tuning-grid boundaries. All 15 Galileo 20%-budget selected fits have their best epoch at the ceiling; all five seed-42 native Galileo selections are at a rate boundary at each budget. Reduced-budget TerraMind and Copernicus selections also frequently reach rate boundaries. These diagnostics limit claims that each model's attainable performance was exhausted. They do not invalidate the completed configuration comparison or automatically justify expanding tuning after seeing test results. Any follow-up must be separately declared, validation-led, budget-matched, and reported alongside the original results rather than replacing them.

The 999 event-bootstrap intervals describe exploratory event variability after seed averaging. There are only 11 or 20 event units and 48 contrasts; no multiplicity-adjusted superiority or general model-family ranking is claimed. Seeds/folds/pixels are not independent floods. Event-wise results and seed variation remain available in the companion tables.

## Local evidence

Local summaries retain all complete fold/seed models rather than selecting whichever looks best locally. Descriptive case averages cover 24 TerraMind, 25 Prithvi, and 16 cases each for Galileo/Copernicus. These are acquisition/AOI combinations, not independent flood events. Binary water and newly flooded land also differ in target semantics.

- **Optical observability:** 13/24 TerraMind and 14/25 Prithvi cases have zero common-support coverage. Undefined scores remain undefined, not zero accuracy. Remaining optical cases can have partial coverage and substantial reference-date offsets.
- **Timing:** the radar case offsets span approximately −77 to +84 hours relative to the reference; optical offsets span roughly −48 to +77 hours. An apparent omission or false positive may reflect actual water change, reference incompleteness, persistent-water semantics, or model error. The summaries alone do not distinguish those explanations.
- **Venlo, near-zero reference offset:** Galileo radar water IoU averages about .652/.687 for two overlapping acquisitions, versus .683/.683 for standard U-Net. Copernicus radar-change agreement on those cases is .175/.373 versus .249/.505 for standard U-Net. Their different targets and spatial support preclude direct ranking. The reference/imagery dependence also limits independence claims even at zero offset.
- **Eschweiler, +6.6-hour radar case:** Copernicus averages .150 versus .089 for standard U-Net; at Wassenberg with the same approximate offset it averages .156 versus .218. This demonstrates case-dependent transfer, not a general local improvement.
- **Prithvi:** several assessable local cases have much poorer reference agreement than optical raw-input controls. Its benchmark disadvantage is not rescued by a consistent local advantage.

No local overall winner or NL–DE performance ranking is defensible from these dependent July 2021 cases. Current outputs support reference-map agreement and observability analysis, not independent field-accuracy or peak-inundation claims. The numerical review has not independently adjudicated each predicted polygon against field observations.

## Computing findings

Caching frozen spatial representations and reusing validation-selected full-label learning rates across seed repeats made the planned census feasible. Reuse did not introduce test-based selection; reduced-label runs selected rates independently. This implementation is worth reporting transparently as part of the methods and resource account.

Recorded head-only/scoring timings cannot be treated as end-to-end operational latency. TerraMind, Galileo and Copernicus use shared feature preparation; Prithvi follows a different adaptation/runtime path. The shared preparation records are approximately 789 s/10.5 GiB, 55 s/.87 GiB and 895 s/11.2 GiB respectively. Concurrent device load, caching, data reading and unequal head architectures matter. The present evidence does not establish that an encoder delivers equal accuracy more cheaply. Prithvi and Copernicus have higher recorded fitting/scoring costs than their compact controls; any formal cost comparison must account for preparation and reuse consistently.

## Relationship to the completed discharge work

The ten model-specific discharge experiments remain a separate result: no broad advantage over matched raw-input corrections. Some Presto and DOFA high-water contrasts are favorable, with heterogeneous effects and different designs/support; DOFA uses held-watercourse transfer. Sparse documented-flood contrasts and shared fallback behavior prevent a sweeping flood-prediction claim. Mapping results neither repair nor contradict that result: they evaluate a different property at a different stage of assessment.

## What the chapter can support

1. Task-appropriate satellite AI can improve on particular simple assessment methods; the most consistent positive contrast here is Copernicus radar change versus the implemented physical control.
2. Pretraining does not guarantee improvement over properly trained raw-input spatial controls or greater robustness to reduced training labels.
3. Local applicability depends on acquisition availability, usable pixels, reference timing and target semantics in addition to benchmark accuracy. More sophisticated image interpretation cannot recover an unobserved flood peak.
4. Resource-efficient experimental execution and potentially resource-efficient deployment are separate questions. The first is documented; the second is not established.

For FEWS/DRR, this informs the choice and verification of an assessment component. It does not establish warning lead time, live feed reliability, improved agency decisions or reduced losses. The study remains useful without claiming any of those outcomes.

Recommended next work is synthesis and selected spatial-error inspection using the retained predictions and references, especially the Galileo low-label failure and local change-versus-water discrepancies. Do not launch another general model sweep or silently replace completed comparisons. A claim of lower annotation cost or cheaper equivalent operation would require a separately specified comparison that the present outputs do not provide.

## Evidence

- Audited final source: `results/applied_study_v5/ready-v2/synthesis/final/benchmark.json` and `local/*-reference-agreement.json`.
- [All 48 benchmark contrasts](reviews/limburg-consolidated-findings-2026-11-10/benchmark-contrasts.csv).
- [Every local case](reviews/limburg-consolidated-findings-2026-11-10/local-cases.csv).
- [Numerical summaries](reviews/limburg-consolidated-findings-2026-11-10/summary.json), including absolute event scores, tuning flags, costs and support.
- [Completed discharge readout](limburg-completed-discharge-readout-2026-11-02.md).
- [Completion/recovery audit](reviews/limburg-completion-recovery-audit-2026-11-10.md).

Source benchmark SHA256: c71b71be331021fc0e72e40aafb006caf45b4994c70a0b28753ca84062ae69b0. Review is additive; final source outputs and prior dated findings are unchanged.
