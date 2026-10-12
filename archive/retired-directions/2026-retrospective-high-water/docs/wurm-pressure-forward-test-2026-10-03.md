# Wurm-only pressure-change test (2026-10-03)

Internal exploratory research aid, not dissertation prose or a revision of the live Limburg protocol. Reproduce with `/Users/briangillikin/miniforge3/bin/python3.12 scripts/61_test_wurm_pressure.py`. The ignored `results/event_study/cross_tributary_rain_v1/prediction_6h/wurm_pressure_only_site/` directory contains all decisions, forward predictions, scores, 999 paired year-block resamples and a manifest with input hashes. The project's `environment.yml` specifies scikit-learn; the default shell Python on this machine does not currently have it.

## The question tested

After six observed hourly periods of a regional rain-defined wet spell, does the six-hour ERA5-Land surface-pressure change improve Wurm/Rimburg next-24-hour p99 high-water classification beyond rain observed so far and current Wurm discharge? This takes the atmospheric feature motivated by Eryilmaz, but the outcome is river high water rather than Eryilmaz's indoor CO2 threshold. A pressure fall is treated as a possible **storm-development cue**, not a cause of flooding.

This is a Wurm-only fit. The wet-spell start and at-least-2-mm first-six-hour regional rain trigger are the same as the prior six-tributary exploratory test. Eligibility now requires only Wurm's current and future gauge quality; other tributaries cannot delete a Wurm decision. Both models use the same 894 eligible decisions in 2010–2025, including 113 positive next-day Wurm outcomes. The baseline features are Wurm six-hour rain, regional maximum six-hour rain, number of rainy catchments, warm season, and current Wurm discharge divided by its era-p99. The comparison adds only p(t) − p(t−6 h), joined at the exact issue hour. Both are equally regularized logistic fits. Each test year 2014–2025 is predicted using earlier years only; training targets ending in the test year are excluded.

There are 164 reviewed Wurm p99 onsets in 2010–2025. This rain-trigger design has a decision window preceding 97 of them, including 78 of 134 in the test years. Others are outside the selected rain starts, already high at issue time, or lack the required decision support. Thus the result is about the defined decision population, **not all Wurm high-water onsets**.

## Forward-year result

The held-out years contain 668 decisions and 92 positives.

| Model | Brier ↓ | Log loss ↓ | ROC AUC ↑ | Average precision ↑ |
| --- | ---: | ---: | ---: | ---: |
| Training-period prevalence | 0.1196 | 0.4047 | 0.466 | 0.126 |
| Rain + current Wurm flow | 0.1069 | 0.3722 | 0.680 | 0.355 |
| Add six-hour pressure change | 0.1061 | 0.3629 | 0.722 | 0.365 |

Pressure raises ROC AUC by 0.041 (year-block resampling interval +0.017 to +0.070). Its average-precision gain is +0.010 (−0.021 to +0.042), Brier improvement 0.0008 (−0.0034 to +0.0049), and log-loss improvement 0.0093 (−0.0043 to +0.0232). The latter three intervals include no improvement. The intervals resample the already-fitted forward predictions by whole year, not the model-development process. All 999 resamples had both outcome classes.

ROC AUC gain is positive in 11 of 12 individual test years; 2021 is the exception (−0.026). Omitting 2024 from the evaluation leaves +0.041 AUC gain but Brier improvement becomes −0.0002. Only one test decision contains the reviewed Wurm July 2021 measurement-concern onset; omitting it from evaluation leaves +0.042 AUC gain and Brier +0.0008. Those are evaluation-only sensitivity summaries, not refitted analyses.

**Independent-episode check:** The exceedance outcome can count a second rise within an already catalogued episode. Remove 73 decisions made within 72 hours after a reviewed Wurm onset and two further high-water windows with no new reviewed onset in their target period, then refit each forward-year model. This leaves 819 decisions overall and 609 held-out decisions, 77 positive. Baseline versus pressure ROC AUC is 0.661 versus 0.709, a gain of +0.048 (year-resampled interval +0.022 to +0.073). Brier improvement is 0.0019 (−0.0014 to +0.0053); average-precision gain is +0.034 (−0.003 to +0.061); log-loss improvement is 0.0128 (+0.0008 to +0.0247). Pressure's ranking signal persists when the target is more clearly a new episode, but Brier and average precision remain unresolved. This is an exploratory sensitivity, not a separate precommitted analysis.

The Wurm-only selection **does include** the July 2021 decision at 13 July 10:00 UTC, six hours before the reviewed p99 crossing, with complete future Wurm coverage. The baseline assigns probability 0.099 and adding pressure lowers it to 0.089. Neither model highlights that defining event. The previously reported six-tributary test omitted this decision because another watercourse lacked its required future coverage.

## What the signal may represent

Among test decisions, median pressure change is more negative before a positive next-day Wurm outcome than before a negative one (means −1.93 versus −0.52 hPa over six hours). Pressure change has Spearman correlation −0.306 with **subsequent** 24-hour Wurm catchment rain, but −0.011 with the preceding six-hour Wurm rain. Future rain was used only in this post-outcome diagnostic, never for eligibility or model fitting. This is consistent with falling pressure identifying developing weather that the already-observed rainfall cannot yet show. It does not demonstrate an independent pressure-to-runoff mechanism or prove that pressure beats an actual rainfall forecast.

The gain is therefore real for **retrospective ranking under this particular decision setup**, but small and not yet decision-relevant: probability accuracy, alert thresholds, false alarms and response times are not resolved. ERA5-Land is retrospective reanalysis; RADOLAN and verified Wurm discharge are also archived products, not established as the values available at issue time. Era-p99 outcomes use the full retrospectively verified record. No as-issued FEWS skill or flood causation claim follows.

## Implication

The Eryilmaz-to-atmospheric-signal idea survives a Wurm-only forward-year test as a modest ranking result across multiple high-water episodes. It is stronger than trying to transfer a Kerkrade building's CO2 residual. Yet it does not by itself rescue the Limburg chapter: July 2021 is missed, Brier and average-precision gains remain uncertain, and the pressure cue may largely anticipate later rain. Treat this as a candidate mechanism for a tightly defined retrospective chapter question, not as a settled result or a reason to add more model families or data sources.
