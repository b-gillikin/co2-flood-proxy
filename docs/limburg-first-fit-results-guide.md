# Limburg first real-data fit: internal results guide

Analysis date: 2026-09-29. This is a research aid for Brian, not dissertation
prose or a formal preregistration. The reproducible run manifest and all
machine-readable tables/figures are in the ignored local directory
`results/event_study/real_data_v1/`. The event review is recorded separately in
`limburg-first-fit-review.md`.

## What the data support

- Six natural-tributary representative gauges, 2010–2025; 724 candidate exact
  p99 onsets in 240 regional storms. All 724 onset pairs are within their
  documented rating domain; three *later episode peaks* exceed a domain
  maximum. Provider-identified July 2021 high-flow uncertainty remains.
- The 72-hour rainfall-history requirement retains 721 onsets from 239 storms
  (131 warm, 108 cold). Three onsets lose complete rainfall histories. The
  model uses 16,716 rows in 708 informative matched strata, drawn from 754,254
  at-risk watercourse-hours. Full denominators by site/season are in
  `sample_flow.csv` and `storm_analysis_status.csv`.
- All primary and secondary models completed 999 joint calendar year-month
  bootstrap attempts with zero numerical failures. Input and code hashes, the
  seed and fit statuses are in `analysis_run.json`.

## Result-to-reading table

| Evidence | Reading for discussion, not draft prose |
| --- | --- |
| Warm median lag 17 h (95% bootstrap interval 12–21); cold 19 h (15–25); difference −2 h (−10 to +4) | No clear seasonal difference in *where the observed rainfall association is concentrated* across lags 1–72. This is not a warning lead-time comparison. |
| The fixed-contrast cumulative log association is 24.40 warm, 49.23 cold; warm-minus-cold −24.83 (−39.77 to −13.63) | The fitted index is stronger in cold months, but its literal exposure contrast lies outside observed 72-hour rainfall histories. Do not exponentiate or describe these as realistic storm risk ratios. |
| Pooled rainfall and all six watercourse-specific cumulative indices are positive | Rainfall preceding onset departs strongly from same-site comparison hours. Shared storms prevent interpreting six same-signed site estimates as six independent replications. |
| Adjusted humidity index positive; pressure-change interval includes zero and its median lag is undefined in the point fit (only 29% of bootstrap draws define it) | Humidity adds model association beyond rainfall; no clear added pressure-change association or timing. The pressure median-lag interval spans its full admissible range (1–72 h). |
| 2010–17 versus 2018–25 cumulative difference interval includes zero | No detectable change in that model summary between record halves. |
| Omitting 58 measurement-concern events leaves 663 fitted onsets; median-lag difference becomes +1 h (−7 to +7) | The absence of a clear seasonal timing difference is stable. The flagged-event comparison is exploratory because two peak-domain flags were added after the first fit. |
| Literal rating eras, 168-hour window and six-degree lag basis give median-lag difference intervals that all include zero | The central timing conclusion survives the specified sensitivity analyses; the point difference varies from −8 to +1 h. |
| Omitting July 2021 event hours or its whole month changes the primary median-lag point difference from −2 to −3 h | The motivated 2021 event is not the sole source of the timing result. This is an exploratory influence check, without new bootstrap inference. |

## Main scientific caution

The protocol's fixed rainfall contrast is the exposure-only 95th percentile of
positive *hourly* catchment rainfall: **2.236 mm/h**. Its cumulative
distributed-lag summary mathematically compares 2.236 mm/h at *every* one of
72 lags against zero at every lag, a 161 mm/72 h sustained pattern. In the
held rainfall files, no catchment sustains that hourly intensity for 72 hours;
the longest uninterrupted run is 8–10 hours. The enormous cumulative log-rate
ratios are thus an extrapolative model index, not a credible effect size for an
observed storm. The per-lag curves in `figure_3_seasonal_lags.png` and the
median-lag comparison are more direct evidence for the chapter's timing
question. Any later re-expression of cumulative association using an observed
rainfall history should be recorded as a new, outcome-informed descriptive
summary, not silently substituted for the first fit.

The conditional Pearson dispersion is very large in several specifications.
`least_expected_onsets.csv` locates the influential residual: a Geleenbeek
onset on 2021-07-04 has very low conditional probability in its stratum when
the extreme mid-July event is also represented. This diagnostic does not
establish that either gauge reading is invalid. Removing July 2021 changes the
primary point timing comparison only from −2 to −3 hours
(`july_2021_influence.csv`). Bootstrap intervals, rather than the model-based
quasi-Poisson covariance, are the reported uncertainty. The extreme residual
and extrapolative contrast should be discussed with a supervisor before
presenting the cumulative magnitude as a substantive chapter finding.

## Boundary for Brian's interpretation

The analysis concerns observed high-water onset relative to matched at-risk
hours. It does not estimate prediction skill, usable warning lead time,
causation, damage, historical H1/H2/H3 crossings, or whether day-ahead action
is feasible. The five figures are internal analytical figures. The July 2021
trajectory omits discharge portions above documented domains or Gulp's stated
calibration range; it does not reconstruct those peaks.
