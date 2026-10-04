# Limburg atmospheric-variable increment to the six-hour test

Status: internal exploratory analysis, 2026-10-03. This extends only the
retrospective rain-trigger test in
`limburg-retrospective-prediction-test-2026-10-03.md`. It is not dissertation
prose or an operational warning evaluation.

## Bounded comparison

The same 584 held-out six-site decisions and 3,504 site outcomes (291 positive)
are used in each model. The fixed reference is the earlier rainfall-plus-
issue-time-discharge logistic model. Add the two atmospheric variables already
built for this chapter from ERA5-Land at each catchment's nearest centroid
cell: six-hour **surface-pressure change** p(t) − p(t−6 h), and **relative
humidity** at issue time. Test pressure alone, humidity alone and both together,
with the same model settings and earlier-year training. The weather table is
joined by exact UTC issue timestamp and watercourse; no future weather enters
predictors. ERA5-Land is a retrospective reanalysis, not a record of what was
available to forecasters at that hour.

## Held-out results

| Model | Brier ↓ | ROC AUC ↑ | Average precision ↑ |
| --- | ---: | ---: | ---: |
| Rain + issue-time flow | 0.0738 | 0.679 | 0.184 |
| Add pressure change | 0.0718 | 0.729 | 0.225 |
| Add humidity | 0.0731 | 0.680 | 0.196 |
| Add both | 0.0713 | 0.727 | 0.234 |

Against rain plus flow, pressure change improves pooled ROC AUC by 0.050
(95% held-out-year resampling interval +0.032 to +0.072) and average precision
by 0.041 (+0.010 to +0.088). The Brier-score gain is 0.0020, with an interval
of −0.0011 to +0.0053: **probability accuracy is not resolved**. Humidity
alone has essentially no AUC gain (+0.001, interval −0.019 to +0.019).
Adding humidity to the pressure model does not resolve further improvement:
the joint model's AUC change is −0.002 (−0.021 to +0.014), and its Brier
improvement is +0.0005 (−0.0010 to +0.0018). These are exploratory paired
comparisons among related specifications, without multiplicity adjustment.

The pooled pressure AUC gain remains positive when 2024 is omitted from the
evaluation summary (about +0.053). After removing 15 decision windows that
contain a measurement-concern onset **and refitting** each forward-year model,
pressure's AUC gain is +0.034 (+0.016 to +0.047); the Brier interval still
includes zero. Some individual years have worse probability scores with
pressure, including 2014, 2017, 2018 and 2023.

## What the extra ranking means

The pooled result is mainly about distinguishing **different storm decisions**.
Among the 92 decisions with both positive and negative tributaries, the mean
within-decision probability that a high-water site is ranked above a non-high
site is 0.757 for rain plus flow and 0.751 after adding pressure. Their
difference is −0.006 (year-block interval −0.019 to +0.005). Pressure has not
improved selection of *which tributary within the same storm* crosses p99.

At issue time, greater pressure falls are associated with more rainfall in
the following 24 hours: across held-out decisions, regional mean six-hour
pressure change and future maximum site rainfall have Spearman correlation
about −0.31, while its correlation with the preceding six-hour rain maximum
is about +0.05. **Inference:** pressure change may partly summarize storm
development that observed rainfall so far has not captured. This is a
post-outcome diagnostic, not proof of a physical pressure-to-runoff mechanism
or an evaluation of an issued rain forecast. Future rain appears only in this
diagnostic, never in model eligibility or features.

The earlier case-crossover analysis did not find a clear pressure-change
lag association at high-water onset. These two results answer different
questions: one compares exposure histories at onsets versus matched hours;
this one compares future high-water rankings after a rain-trigger decision.
Neither alone establishes that pressure is an independent causal driver or
an actionable warning indicator. The hydrological literature more directly
supports rainfall and antecedent hydrological state as core inputs, for
example [Berthet et al. (2009)](https://hess.copernicus.org/articles/13/819/2009/).

Do not add a larger atmospheric feature search on the strength of this test.
Temperature remains useful to flag possible rain/snow phase issues, as in
`cross-tributary-current-data-analysis-2026-10-03.md`; a new temperature
prediction feature is not required by this result.

## Reproduction

Run `scripts/59_test_atmospheric_increment.py` using the held rainfall,
discharge, rating and `data/interim/event_study_weather_hourly.csv` files.
Outputs under ignored
`results/event_study/cross_tributary_rain_v1/prediction_6h/atmospheric_increment/`
include exact forward predictions, score and paired bootstrap tables,
measurement-clean results, within-decision ranks, the future-rain diagnostic
and an input-hash manifest. `tests/test_atmospheric_increment.py` protects
the issue-time weather join and mixed-event rank calculation.
