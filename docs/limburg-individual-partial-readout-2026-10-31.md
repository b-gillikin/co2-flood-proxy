# Individual encoder experiments: partial evidence review, 31 October 2026

Internal interpretation aid for Brian; not dissertation prose. Eight completed experiments, 23 distinct primary model/scenario jobs, and four completed matched configuration comparisons were reviewed. Presto and Galileo remain pending. This is a dated snapshot, not the final ten-experiment conclusion. It does not replace the earlier negative retrieval findings.

## What the completed work says

There is no broad improvement over the matched raw-input correction in the completed experiments. Chronological selection frequently chooses the conventional trajectory, the raw correction, or an alternative raw-only regularization. The small differences between fitted arms must therefore not all be called encoder contributions. Positive EO use is an explicit case-level mode in the saved ledger. Selection/fallback is part of the evaluated procedure, not a reason to discard assessments or optimize on the favorable subset.

The table concerns **local-Q absence**, paired source-supported assessments, and equal-site/storm/available-issue weighting. Negative differences favor the encoder arm. Intervals are the existing exploratory, conditional, 999 shared whole-year bootstrap intervals; they are not multiplicity-adjusted. Assessment rows include repeated issue times; the storm count is also shown. Positive EO percentages use all 15,392 ledger rows per regime, including early/no-training and unavailable-outcome rows, and describe utilization rather than efficacy. Different support and DOFA's separate transfer question preclude a leaderboard.

| Experiment | Supported assessments / storms | Encoder − raw MAE, mm/h (95% year-block interval) | Positive EO selected, % of full ledger |
|---|---:|---:|---:|
| anysat | 9,112 / 303 | -7.37e-06 [-3.28e-05, 6.62e-06] | 5.6% |
| copernicus_fm | 9,112 / 303 | 5.15e-06 [-3.35e-07, 1.2e-05] | 3.8% |
| croma | 10,351 / 333 | 1.46e-06 [0, 4.58e-06] | 1.6% |
| dofa | 7,791 / 252 | -4.06e-05 [-0.000181, 9.01e-05] | 29.8% |
| olmoearth | 10,351 / 333 | 1.36e-05 [-3.71e-08, 4.31e-05] | 2.3% |
| prithvi | 11,557 / 377 | 2.39e-05 [0, 8.31e-05] | 1.3% |
| satmae | 8,034 / 293 | 2.43e-07 [-3.69e-06, 4.05e-06] | 3.4% |
| terramind | 9,112 / 303 | 5.72e-06 [-4.79e-07, 1.34e-05] | 3.8% |

DOFA's held-watercourse high-water subset has encoder-minus-raw MAE −0.000283 mm/h [−0.000534, −0.0000348], across 1,509 assessments/154 storms. Its all-assessment and documented-flood intervals include zero; its all-Q-absent high-water point difference reverses direction. This is a conditional transfer signal worth reporting, not a general winner or evidence for never-monitored catchments. There are only six independent watercourse groups.

AnySat's local-Q-absent high-water difference is −0.0000559 mm/h [−0.000171, +0.00000977]. Its documented-flood difference is −0.000845 [−0.001014, 0]; the upper endpoint is zero, and the German example below has a verification flag. Under all-Q absence its high-water/flood point differences become positive. Keep the regime and measurement qualifications attached. The other same-gauge experiments provide no clear general incremental benefit here. Exact ties in many flood subsets reflect selected fallbacks/raw-only predictions; they do not establish that imagery is intrinsically uninformative.

## NL and DE evidence

All eight experiments include both countries. Local-Q-absent high-water increments are exactly zero for DE in six same-gauge experiments (Copernicus-FM, CROMA, OlmoEarth, Prithvi, SatMAE, TerraMind). Their DE heads do not select a positive EO contribution there. AnySat's DE high-water difference is −0.000209 mm/h [−0.000688, 0], versus NL −0.00000492 with an interval crossing zero. DOFA's DE high-water interval also crosses zero. These patterns concern held gauges, histories and fitted selection, not country-level institutional performance or an absence of satellite information over Germany.

## Actual event corrections

The accompanying [event examples](reviews/individual-partial-2026-10-31/event-examples.csv) select the largest positive and negative error changes **among positive-EO predictions**, separately per model/country under local-Q absence. They are post-hoc illustrations; no subgroup is selected for a new confirmatory claim. Full-census effects remain in the [effects table](reviews/individual-partial-2026-10-31/effects.csv).

- **AnySat, Randerath, issued 7 February 2021 03:00 UTC:** next-24h MAE improves by 1.68 m³/s. Observed peak is 24.09 m³/s; raw predicts 11.84 and encoder 14.01. Both peaks occur at hour 2 versus observed hour 7. This corrects magnitude partway; it does not recover the peak or timing. The verification-clean flag is true.
- **AnySat, Randerath, 4 February 2021 10:00 UTC:** MAE worsens by 1.76 m³/s. An observed peak of 10.80 is compared with raw 11.15 and encoder 12.92. A correction useful in one event overstates another.
- **Eys, 22 December 2023 11:00 UTC:** AnySat, Copernicus-FM and TerraMind each improve MAE by roughly 0.02 m³/s. Peaks remain about 0.28–0.29 versus observed 0.68; predicted hour 1 versus observed hour 8. Shared failure to capture development remains more consequential than the small improvement.
- **DOFA, Mesch, 9 January 2025 03:00 UTC:** MAE improves by 0.75 m³/s; raw/encoder peaks fall from 3.03 to 2.15 against observed 1.28. Both peak too early. Conversely, Azijnfabriek on 18 May 2024 worsens by 0.52 m³/s as an already excessive peak increases from 6.27 to 6.80 against observed 2.15.
- **Prithvi, Azijnfabriek, 30 November 2015 10:00 UTC:** MAE improves by 0.09 m³/s, but its peak of 0.82 remains below observed 1.54 and at hour 1 versus observed hour 24. A better error score does not establish better progression-to-flood assessment.
- **OlmoEarth, Mesch, 10 September 2025 00:00 UTC:** MAE improves by 0.18 m³/s by reducing an overprediction; predicted peak timing remains hour 15 against observed hour 1. The neighboring 11 September assessment worsens by 0.13 m³/s.
- **CROMA's extreme local examples and DOFA's German July 2021 example have verification-clean=false.** Retain them with the uncertainty flag; do not use them as clean confirmation of reconstructed peak magnitude. CROMA's 13 July gain is only 0.009 m³/s while predicting a peak near 0.38 against observed 11.43.
- **SatMAE, Brommelen, 22 May 2018 17:00 UTC:** MAE improves by 0.04 m³/s, while a predicted peak of 3.94 still exceeds observed 2.12. Copernicus-FM and TerraMind worsen their respective raw-control errors for the same assessment. Their raw predictions differ slightly because controls follow each model's exact inputs.

These are forecast-trajectory diagnostics under controlled missing information, not verified inundation or H-stage transitions. Observed and predicted maxima refer only to the next 24-hour window. Flat/tied maxima use the first hour for descriptive examples, not the primary scoring rule. Retrieving analogous events is the conventional baseline; these individual experiments test learned corrections, not a new analogue-retrieval system.

## Configuration comparisons and supporting work

Completed local-Q-absent, matched-support comparisons: AnySat spatial versus global is essentially tied; Copernicus-FM metadata versus no-metadata is exactly tied; TerraMind ordered versus temporal-mean has a small favorable point difference but an interval crossing zero; Prithvi spatial versus pooled has a positive (worse) point difference and an interval crossing zero. These comparisons do not support a general mechanism claim. Galileo and Presto mechanism checks await their runs. Copernicus-FM/TerraMind have identical selection-mode counts but different saved trajectories/effects; matching counts alone are not duplicate results.

[Supporting preparation](limburg-individual-supporting-preparation-2026-10-31.md) freezes the exact combined-mask definitions and verifies all 204 soil/snow source checksums. C+E attribution and SatMAE product/support comparisons remain separate supporting tasks. This preparation is not an implemented fit runner or completed supporting analysis. Nothing new was submitted to the queue.

## Reproduce and maintain

`scripts/174_snapshot_individual_review.py --output NEW_DIRECTORY` verifies each reviewed job's saved output and source hashes and records the snapshot inputs. It reads completed outputs only, performs no fit and leaves the active queue unchanged. The [manifest](reviews/individual-partial-2026-10-31/manifest.json) identifies the exact included evidence. Pending jobs must be reviewed and included in a new snapshot before making a ten-experiment conclusion. Do not overwrite this partial record or silently reinterpret earlier retrieval tests as these residual experiments.
