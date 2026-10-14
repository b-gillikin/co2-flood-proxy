# Limburg event-definition robustness: results

Internal evidence and interpretation aid for Brian, not dissertation prose.

## What changes, and what does not

Two authorized one-factor checks of the main retrospective analogue analysis:
**p95 with 72h local linkage**, and **p99 with 120h local linkage**, against
p99/72h. All candidate episodes are included in the catalogues; no event sample.

P99 remains the common rating-era discharge normalizer and verification
reference. The 512h histories, frozen ordered TTM/state representation, raw
and conventional controls, AlphaEarth/context controls, 72h response window,
regional 72h grouping, pooled archive policy and five/ten-donor reporting remain
fixed. No new checkpoint, training, imputation, data request or threshold search.
Local linkage groups threshold **crossings**, with unbounded single linkage;
it is not five complete days below threshold and does not establish independent
meteorological storms. Regional groups are recomputed after changing the local
catalogue, while their grouping rule stays fixed.

The p95 run tests a broader/earlier event selection, while reporting the same
p99-scaled response endpoints. Do not interpret a lower error across different
catalogues as a model improvement. The same 72h period after different onsets
may capture different phases of a longer flood. This remains retrospective:
full-era quantiles, finalized records and frozen representations do not recreate
what an operator knew in real time.

The exact rationale, literature, eligibility conventions and numerical checks
are in [the execution note](limburg-event-definition-sensitivity-2026-10-14.md).
[Tsiokanos et al. 2024](https://hess.copernicus.org/articles/28/3327/2024/)
provide local p99/five-day precedent using daily maxima; [Tuel & Martius 2021](https://nhess.copernicus.org/articles/21/2949/2021/)
compare daily p95/p99 definitions. Neither paper implements our exact hourly
rating-era adaptation.

## Catalogue and availability

| Definition | Dutch candidate episodes | German candidate episodes | Dutch scorable 72h responses | German scorable 72h responses |
| --- | ---: | ---: | ---: | ---: |
| p99 / 72h | 724 | 338 | 614 | 237 |
| p95 / 72h | 1,646 | 720 | 1,350 | 526 |
| p99 / 120h | 638 | 294 | 544 | 208 |

Three Dutch p95 entries have censored onsets and remain visible in the candidate
catalogue, outside the exact-onset model inventory. Missing histories, response
completeness and provider/rating uncertainty remain explicit. Archive availability
and cohort restrictions reduce the actual scored query counts further.
The held Dutch primary-eligibility convention includes its inherited 72h prior
rain-availability check even in the Q-only comparison. This sensitivity preserves
that convention rather than changing another factor. No new weather requirement
is introduced. The official H1/H2/H3 thresholds and completed H1 escalation
analysis are unaffected; additional p95 events are not additional confirmed floods.

## What survives the definition checks

**The small TTM increment in individual response-shape matching is not confined
to p99/72h.** It remains favorable in direction in both countries under both
alternatives. This does not establish universal superiority, prediction skill,
or usefulness to a human analyst.

Main pooled, all-river, five-donor Q-only comparison; each row is a separate
matched query population. Shape error is the mean individual donor
peak-normalized response RMSE, not a forecast error of an averaged curve.

| Definition | Country | Queries | Raw + state | TTM + state | Relative reduction | Paired difference, 95% regional-group interval |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| p99 / 72h | NL | 610 | 0.20029 | 0.19622 | 2.0% | -0.00407 [-0.00706, -0.00120] |
| p95 / 72h | NL | 1,348 | 0.23690 | 0.23334 | 1.5% | -0.00357 [-0.00537, -0.00177] |
| p99 / 120h | NL | 540 | 0.19748 | 0.19412 | 1.7% | -0.00336 [-0.00694, +0.00014] |
| p99 / 72h | DE | 235 | 0.20113 | 0.19569 | 2.7% | -0.00543 [-0.01078, -0.00049] |
| p95 / 72h | DE | 524 | 0.23497 | 0.22997 | 2.1% | -0.00500 [-0.00769, -0.00217] |
| p99 / 120h | DE | 206 | 0.20118 | 0.19469 | 3.2% | -0.00649 [-0.01232, -0.00098] |

The Dutch 120h all-river group interval narrowly includes zero; its year
interval excludes zero, as do its cross-river group/year intervals. Quality
filtering retains the favorable point estimate but does not make the Dutch
all-river group interval conclusive. P95 Q-only shape differences remain
favorable across the reported country, river restriction, quality and 5/10
settings. Report these distinctions rather than declaring every interval a pass.

**Conventional hydrology remains a strong benchmark.** At p95, rainfall/Q
summaries retrieve closer response shapes than TTM/state on matched inputs:

| Country | Matched p95 queries | Conventional R0 shape error | TTM/state shape error | TTM minus R0, regional-group interval |
| --- | ---: | ---: | ---: | --- |
| NL | 1,197 | 0.22763 | 0.23910 | +0.01147 [+0.00849, +0.01460] |
| DE | 451 | 0.22630 | 0.23722 | +0.01092 [+0.00594, +0.01592] |

Year-resampled shape intervals also favor R0. Its mean-donor peak estimate has
lower point error, but p95 year intervals for that difference include zero.
This supports a modest representation increment over the matched raw control,
not a general claim that a foundation model beats hydrological information.
No alternate population or sensitivity is used to select a winning model.

**AlphaEarth's timing contribution depends on the selected event population.**
Difference below is annual context minus the same TTM/state temporal arm in
mean individual donor peak-time mismatch, in hours; negative favors context.
These are retrospective donor timings, not available warning lead time.

| Definition | Country | Matched context queries | Timing difference | Regional-group 95% interval |
| --- | --- | ---: | ---: | --- |
| p99 / 72h | NL | 294 | -0.92h | [-1.79, -0.06] |
| p95 / 72h | NL | 606 | +0.58h | [-0.10, +1.27] |
| p99 / 120h | NL | 252 | -0.83h | [-1.72, +0.03] |
| p99 / 72h | DE | 71 | +0.50h | [-0.68, +1.75] |
| p95 / 72h | DE | 138 | -1.79h | [-2.86, -0.75] |
| p99 / 120h | DE | 60 | +0.62h | [-0.64, +2.03] |

P95 German annual context also improves on area and identity timing controls,
but its increment over fixed-2017 context remains uncertain (group interval
-1.81 to +0.08h). The Dutch p95 cross-river point difference is favorable
(-0.36h), with a group interval spanning zero. Thus neither universal geographic
benefit nor a unique annual-landscape effect is established. National labels
are also confounded with rivers and coverage: DE is the held Wurm network,
not a representative sample of Germany. Do not compare significance labels
across populations as a formal test of their differences.

**The casebook-versus-prediction distinction also survives.** Across these
Q-only populations, TTM-selected individual donor shapes are closer than the
group-balanced unranked archive (about 11–16% lower mean individual shape
error). Averaging selected responses does not establish better mean trajectories
or duration estimates; generic-archive duration estimates have lower point
error in every main country/definition row. The added evidence concerns
retrieved precedents, not a validated forecasting or escalation system.

## Membership and assessment timing

Changing the percentile generally changes the assessment hour, not just which
of the original onsets are kept. Only 64 Dutch and 19 German original onsets
remain at exactly the same hour in the p95 catalogue. The scored Q-only
shared-onset comparison has just 51 NL and 15 DE queries. Those small subsets
are not representative substitutes for the full p95 analysis; they do not
show a uniform TTM advantage. Retain both tables, including unfavorable changes.

A separate descriptive mapping assigns every baseline episode to the latest
alternative episode start at or before it in the same gauge. For p95 this is
the pooled chain containing the lower-threshold active excursion; for 120h
it is the wider chain containing the same p99 crossing. This mapping followed
membership inspection before reviewing alternative model errors; it changes
no catalogue, model or score. The CSV is separately produced by the audit in
`results/basin_ai_event_definition_audit/baseline_episode_mapping.csv`.

| Alternative | Country | Baseline episodes mapped | Alternative chains containing them | Median earlier start | Baseline onsets outside the alternative's first 72h |
| --- | --- | ---: | ---: | ---: | ---: |
| p95 / 72h | NL | 724 | 688 | 4h | 86 |
| p95 / 72h | DE | 338 | 321 | 4h | 35 |
| p99 / 120h | NL | 724 | 638 | 0h | 86 |
| p99 / 120h | DE | 338 | 294 | 0h | 44 |

At p95, approximately 40% of scorable responses reach p99 within 72h, versus
87–91% in the baseline. Median response peak/p99 falls from 1.46 to 0.84 in NL
and 1.40 to 0.88 in DE. A smaller fraction peaks at response hour 1. These are
substantially different assessment phases and severity mixtures. The four-hour
median shift is not four hours of demonstrated operational warning benefit.
Wider linkage removes later repeat assessments; the response horizon itself
is still 72h and is not a complete flood-duration reconstruction.

The existing p99/72h definition can remain the main readout: p95 and five-day
linkage are transparent sensitivity evidence. Preserve them without switching
the primary definition to whichever produces the strongest result. The next
work is synthesis and Brian's case review/writing, not another model roster.

## Reproduction and audit

```bash
python scripts/88_event_definition_sensitivity.py
python scripts/89_audit_event_definition_sensitivity.py
```

Local outputs: `results/basin_ai_event_definition_sensitivity/`, with separate
`p99_72/`, `p95_72/` and `p99_120/` folders. Each contains all candidate episodes,
thresholds and fixed p99 normalizers, input/response eligibility, frozen vectors,
selected donors, event scores, archive coverage, country summaries and paired
intervals. At the root, `query_membership_changes.csv` and
`common_onset_summaries.csv` distinguish full-population and shared-onset results.
`definition_shape_comparison.png` labels its changing full populations explicitly.

The exact-row cache is a computational optimization: only eligible prior unique
rows set a query's distance scale. Unit checks cover duplicate histories,
robust state scaling and future outliers. The entire baseline is rerun through
this implementation and checked against held donor IDs, distances and metrics.
Independent audit reconstructs the full source catalogues, p99 scales, input
histories, responses, selected-pair/set metrics, generic archive references and
summary arithmetic. Hashes bind sources, inputs, weights and saved results.
Sampling intervals use 9,999 regional-group/year draws with seed 20261013;
undefined sparse intervals stay explicit. These are exploratory robustness
checks, not preregistered confirmation, and do not account for every source of
development or measurement uncertainty.

Validation completed: **160 tests pass**; repository lint and changed-file
format/whitespace checks pass. Independent reconstruction verifies 4,360
candidate episode records across the three definitions, 1,144,553 selected
donor rows and 233,632 event-score rows. Maximum numerical discrepancy is
2.85e-14. Input/source/output hashes match. The baseline replay selects identical
donor IDs, with maximum distance discrepancy 1.51e-14 and scored metrics within
1e-12 of the held pooled results. The comparison figure received visual QA.
Original results and independent human-review fields remain untouched.
