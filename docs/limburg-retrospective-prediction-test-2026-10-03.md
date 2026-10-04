# Limburg six-hour rain-trigger prediction test

Status: internal exploratory current-data analysis, 2026-10-03. This is a
retrospective test of whether observed river state adds predictive information
to observed rainfall. It is not dissertation prose, an operational warning
evaluation, or a replacement for the recorded case-crossover design. Brian
writes all manuscript text.

## Question and fixed decision

At the end of the sixth hourly RADOLAN period after a new regional wet spell,
can the observed discharge at a tributary help identify whether it will be
above its era-specific p99 in the following 24 hours, beyond rainfall observed
up to that hour? A wet spell starts with at least 0.2 mm/h in any of the six
catchment series after at least 12 fully dry regional hours. The main decision
requires at least 2 mm over the first six hours in any catchment. This is an
issue-time trigger: future event totals and future rainfall are **not** used
for eligibility or features. It is one sampled decision per wet spell, with
selected decisions at least 24 hours apart.

All six gauges must be observed and below p99 at issue time. Each must have
at least 90% admissible discharge hours in the next 24 hours for outcome
verification. The target is a site-specific occurrence of high discharge in
those next 24 hours, not damage, an official warning threshold, or a regional
six-site flood. Entire six-site decision windows are excluded if the future
observability screen fails. That screen uses future data only to verify the
outcome; it cannot be part of a live trigger.

Both models use the same site identity, warm-season indicator, site-specific
six-hour observed rain, regional maximum six-hour observed rain, and the
number of catchments with at least 2 mm in six hours. The comparison model
adds only that site's issue-time discharge divided by its retrospectively
defined era-p99. Both are regularized logistic models with the same fitting
settings. Each test year from 2014 through 2025 is predicted using **only
earlier calendar years** for fitting. The comparison uses the same rows and
future labels in both models. Training labels whose 24-hour target windows
extend into a test year are excluded. The training-years positive rate is a reference
baseline. The 2-mm trigger was selected after inspecting event and outcome
counts but before fitting these prediction models. This outcome-informed
choice is another reason to treat the test as exploratory; the trigger is
not a validated warning threshold.

## Result

The main forward test contains 584 six-site decisions, or 3,504 site decisions,
across 12 held-out years. There are 291 positive site outcomes (8.3%) and 65
decision windows with at least two positive sites.

| Held-out metric | Training prevalence | Rain only | Rain plus issue-time flow |
| --- | ---: | ---: | ---: |
| Brier score, lower is better | 0.0764 | 0.0756 | 0.0738 |
| ROC AUC, higher is better | 0.446 | 0.628 | 0.679 |
| Average precision, higher is better | 0.076 | 0.144 | 0.184 |

The flow model improves ranking: ROC AUC rises by 0.051 (95% held-out-year
resampling interval +0.010 to +0.087), and average precision rises by 0.040
(+0.013 to +0.079). The absolute Brier improvement is 0.0019, with an
interval of −0.0003 to +0.0042. Thus the main test does **not** resolve an
improvement in probability accuracy. The flow model's Brier score is only
about 3.5% below the training-prevalence reference. This is a modest
information gain, not a demonstrated useful warning system.

Held-out-year intervals resample the existing forward predictions in whole
calendar-year blocks (999 draws); they do not refit the models within each
bootstrap draw and should not be presented as full model-development
uncertainty. Performance varies by year and tributary. Flow worsens Brier
score at Eyserbeek and worsens the overall score in 2014 and 2020. Omitting
2024 from the **evaluation summary** leaves an AUC gain of about 0.031 and a
Brier gain of about 0.0011; 2024 contributes materially but is not the only
source of the ranking gain.

## Sensitivity and measurement limits

The AUC gain is +0.079 if every wet spell is eligible, +0.038 with a 5-mm
issue-time rain trigger, +0.050 with 100% rather than 90% future coverage,
and +0.053 after removing 15 whole decision windows containing a provider-
or review-flagged onset. The 5-mm subset's year-block AUC interval includes
zero. The measurement-concern exclusion also removes many otherwise usable
site outcomes, so it is a conservative quality check, not a claim that every
removed tributary reading was wrong. Brier improvement intervals include zero
in the main, all-wet, and measurement-clean analyses; the full-coverage
interval barely clears zero.

The 13–15 July 2021 crisis does not enter the main prediction evaluation:
at the eligible 2021-07-13 10:00 UTC decision, Geul has 88% admissible future
hours, below the fixed 90% six-site requirement. This test therefore cannot
claim skill for that defining event. The decision at the preceding July 12
wet spell also fails the 2-mm issue-time rain trigger.

The historical Waterschap discharge series and era-p99 thresholds are
retrospectively verified; some rating relations were adjusted after the
observations. Era-p99 thresholds were calculated over the full available
series, including held-out years; the model fitting is forward-year, but the
outcome definition is retrospective rather than an as-issued threshold.
The archived RADOLAN rainfall series is likewise used as a
historical data product, not proven to be the exact values displayed in real
time. Archived as-issued forecast rain and unrevised gauge snapshots are not
inputs. The test uses **observed rain through hour six** and therefore
evaluates conditional short-horizon prediction after rain has begun, not a
day-ahead weather forecast. It does not evaluate an alert threshold, false
alarms at an operational threshold, response time, or reduced risk.

## Interpretation and reproduction

There is evidence that the river state known at a chosen decision time
contains some incremental information about which tributary will reach high
discharge over the next day. The evidence is strongest for ranking outcomes,
weaker for calibrated probabilities, and heterogeneous by site and year.
It supports a bounded FEWS-relevant research direction but does not by itself
justify an operational or committee-facing warning-skill claim. A future
as-issued evaluation would need appropriate archived forecasts and original
real-time gauge versions, as well as an explicit decision threshold and
lead-time definition. Those additional data are **not** needed to report
this retrospective result with its proper limits.

Reproduce with `scripts/58_test_tributary_prediction.py` in the chapter
Python environment. Its ignored results under
`results/event_study/cross_tributary_rain_v1/prediction_6h/` contain all
site-level forward predictions, score tables, year/site breakdowns, paired
year-block draws and an input-hash manifest. Issue-time and chronological
fit tests are in `tests/test_tributary_prediction_timing.py`.
