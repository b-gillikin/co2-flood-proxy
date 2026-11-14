# Limburg: short research account

14 November 2026. Internal synthesis for Brian, not dissertation prose or a new research plan. This account draws on completed work, including corrected interpretations. It introduces no new analysis, selected model or experimental commitment.

## The problem we have been trying to understand

How can AI contribute useful, trustworthy information about developing high water and flooding in Limburg and nearby Germany? We assembled long gauge records, rainfall and weather data, satellite observations and published model assets. The experiments examined historical precedents, river-response estimation under limited information, and satellite flood mapping. Those tasks answer different questions; their results cannot be combined into one model leaderboard.

## What the experiments taught us

**1. Familiar-looking events are not necessarily informative precedents.** Hydrological matching retrieves closer response shapes than generic archive membership, and TTM modestly improves shape matching in the broader discharge-history census. But better resemblance does not consistently yield better peak, trajectory or probability estimates. In reviewed cases, useful severe precedents were absent from the eligible archive, missed by retrieval, or diluted by averaging. These are distinct failures, not one universal failure of analogues. Retrospective matching results are not demonstrated warning lead time.

**2. Additional environmental information can help particular comparisons, without establishing a general AI advantage.** Pressure change modestly improved Wurm high-water ranking, but probability-score improvements were uncertain and the July 2021 decision remained poorly identified. The building CO2 diagnostic did not establish a repeatable transferable precursor. AlphaEarth did not provide consistent added value beyond temporal and simpler geographic controls. AnySat had a favorable German snapshot analogue result, but that exploratory result concerned two gauges on one river and was sensitive to the transfer/comparison setting. These are qualified results worth retaining, not established operational capabilities.

**3. Simulated scarcity did not establish that the tested EO representations could replace missing ground information.** Removing discharge information worsened the conventional analogue assessment, especially when all current gauge inputs disappeared. Adding EO did not improve average performance in the original fixed-fusion scarcity comparison. Later model-specific discharge-correction experiments also found no broad benefit over matched raw-input controls, although some contrasts favored Presto or DOFA. This evidence concerns the tested representations, archives and learning procedures. It does not establish that satellite information or AI is generally unhelpful in poorly monitored rivers.

**4. Spatial mapping gave clearer task-specific results, but no general foundation-model winner.** In the completed source-label-budget comparison, Copernicus-FM radar change improved on the implemented physical comparator and retained much of its performance with fewer training chips. It did not clearly outperform trained U-Net; several other tested encoders lost to strong same-input controls. The reduced-chip experiments retained validation labels, so they did not demonstrate equivalent reductions in total annotation effort. In the later external study, geometry-compatible Copernicus versus U-Net differed by +0.008 IoU, with an interval spanning −0.023 to +0.037: no clear average advantage, and no equivalence established.

**5. What the observations and labels mean materially changes the answer.** A newer reference image did not universally improve flood-map agreement, but the apparent average deterioration weakened and became uncertain after geometry/timing restrictions. The populations also changed, so that attenuation does not identify a sole cause. Recognizing water differs from identifying new inundation, and an instantaneous image differs from maximum flood extent. Gauge p99, current warning-threshold crossings and documented inundation likewise identify different things. Measurement limits sometimes affect the most consequential peaks. None of these distinctions can be repaired by a higher model score alone.

## Where that leaves the research

We have evidence about particular capabilities and failures, not a demonstrated agency-ready warning improvement. The work has not shown which intervention would materially improve an authority's flood-information capability. It also has not justified abandoning AI, satellite mapping or the regional data.

The substantive lesson to carry forward is that **usefulness depends on the specific information task, available observations and comparison—not model sophistication alone**. That is an interpretation across our experiments, not a newly discovered universal principle. The unresolved chapter problem is to identify one consequential capability question that this evidence can answer convincingly. No next direction is selected by this account.

## Evidence pointers

These preserve populations, exact estimates, uncertainty and qualifications; they are not additional required results sections.

- [Analogue synthesis, including TTM, AlphaEarth, AnySat and actual cases](limburg-findings-consolidated-2026-10-27.md); [distributional evaluation](limburg-analogue-distribution-results-2026-10-15.md); [flood-case review](limburg-flood-case-review-2026-10-27.md).
- [Wurm pressure forward-year test](../archive/retired-directions/2026-retrospective-high-water/docs/wurm-pressure-forward-test-2026-10-03.md); [building CO2 diagnostic](../archive/retired-directions/2026-retrospective-high-water/docs/wurm-co2-small-diagnostic-2026-10-03.md).
- [Controlled scarcity results](limburg-scarcity-results-2026-10-29.md); [completed ten model-specific discharge experiments](limburg-completed-discharge-readout-2026-11-02.md).
- [Task-specific spatial benchmark and label-budget findings](limburg-consolidated-findings-2026-11-10.md); [latest mapping validity resolution](limburg-study-consolidation-2026-11-11.md).
- [Warning-threshold census](limburg-warning-threshold-results-2026-10-14.md); [measurement review](../archive/retired-directions/2026-retrospective-high-water/docs/limburg-first-fit-review.md).

Later validity corrections govern the relevant interpretation; earlier numerical outputs remain preserved. Exploratory positive comparisons are not promoted to confirmatory findings. Completed results, scientific limits and research judgments are kept separate. No new data need, model, run or supervisor dependency follows from this synthesis.
