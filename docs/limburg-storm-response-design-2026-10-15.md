# Three linked storm-response analyses

2026-10-15. Brian authorized all three prongs of the event-insight review.
Internal analytical specification written before the new results; exploratory
research after substantial earlier development, not preregistration or prose.

## Question and population

Why do similar storms develop differently across the monitored tributaries,
and when does another river's response help explain escalation? The predecessor
work establishes conditional analogue performance, not event mechanisms.

Use all qualifying rainfall episodes in the held 2010–2025 record and all eight
NL/DE gauges, retaining nonresponses and incomplete cases in the inventory.
Define regional wet hours as any of the six core NL catchment means >=0.2 mm/h.
Join wet hours unless separated by at least 12 consecutive observed dry hours.
A missing regional hour interrupts certainty: the affected episode is flagged,
not silently joined across the gap. Retain episodes delivering >=10 mm to at
least one core catchment, independent of discharge. These are practical hourly
radar definitions, not disciplinary constants or a definition of all storms.
Reconstruct a 24-dry-hour catalogue as a segmentation sensitivity.

Each gauge has a pre-rain baseline at start−1h and a landmark at start+5h,
after six hourly rainfall accumulations. Record the full episode forcing,
antecedent 72h/168h rain, early 6h rise, response hours 1–72 after landmark,
and the intervening rainfall. Primary continuous outcome: maximum future
Q/p99 minus landmark Q/p99. Also report peak time, duration above p99 and
mean future excess over pre-rain flow. Full-era p99 is a retrospective scale,
not a forecast input or a flood threshold. Future rain is used explicitly for
explanatory conditioning, so these analyses are not as-issued forecasts.
For episodes longer than follow-up, truncate explanatory episode rainfall and
its duration at the outcome end; retain the natural episode duration and flag
continuing storms. Rain falling after the outcome cannot explain that outcome.

Spatial radar descriptors: rainfall-weighted wet-area fraction (cells >=0.2
mm/h) and rainfall-weighted within-catchment coefficient of variation over
the regional episode. Use exact area weights and fail incomplete affected
catchments; these are spatial-coverage measures, not drainage-distance moments
or storm velocity. No new terrain or satellite download.

## Three estimands

1. **Event divergence:** compare all eligible storms with up to five completed
   earlier storms on the same gauge, matched by log rainfall total, maximum
   hourly intensity, duration, spatial coverage and season. Then compare that
   rainfall-only retrieval with rainfall plus initial flow/6h rise, and with
   rainfall/state plus standardized raw 512h history or frozen ordered TTM.
   Use the same complete-history queries/donors for these representation arms;
   a broader rainfall/state contrast remains visible separately. Scales use
   only eligible earlier donors. Report actual case pairs and outcome errors,
   not only averages. Matching residuals and conditional regression estimate
   associations, not causal effects. Realized full-episode rain informs the
   explanatory match. No future Q enters retrieval.
2. **Changing relationships:** for each directed gauge pair, compare fixed
   ridge regressions using target forcing/state, adding peer rainfall, and
   adding peer pre-rain flow/6h rise. Fit expanding prior-year archives;
   purge training outcomes extending into the test year. Evaluate complete
   common rows in each arm. Report paired changes in absolute error by pair,
   broad/local storm and season, with year-block intervals.
   Peer eligibility requires its rainfall and initial flow observations, not
   its unused future discharge outcome; quality flags for peers concern the
   input interval. The target still needs its own exact outcome window.
   These are conditional hindcasts given realized rain, not operational forecast skill.
   Broad means >=10 mm at >=4 of six core catchments; local <=2; three is mixed.
   Current curated topology does not assert exact Wurm station order: name
   serial same-watercourse relationships without claiming measured travel
   times or confluence amplification. Country is confounded with river/site.
3. **Escalation/recovery:** identify local rain pulses separated by >=6 dry
   hours within the fixed landmark+72h observation span. For repeat pulses,
   identify whether more than half the initial 6h rise remains immediately
   before the pulse (only if that initial rise exceeds 0.02 p99). Compare the
   subsequent 24h rise, adjusting for pulse/next-24h rain, intensity, baseline
   flow, initial rise, gauge and season. Also fit a storm-level conditional
   association between repeat rain before recovery and the primary 72h outcome,
   controlling full-window rain. All definitions are operational proxies;
   they do not establish saturation, exhausted storage or floodplain inundation.

Ridge penalty =1 after training-only standardization; no tuning or model-family
search. Conditional explanatory coefficients use ordinary least squares with
gauge effects and year-block bootstrap. Seed 20261015; 1,999 year draws.
The same whole years are resampled across gauges and paired contrasts to
preserve regional storms, overlapping windows and reused-donor dependence.
Report actual years and folds; interval precision is conditional on this
exploratory design, not the full development history.

## Measurement and interpretation

Preserve raw observations, domain flags, period changes and provisional values.
Exact outcome comparisons need complete response windows, stable rating
periods and no out-of-domain values; uncertain cases remain in the inventory
and plots. A stricter sensitivity also excludes documented calibration/July
2021 concerns and provisional German periods. No interpolation. A gap prevents
a pulse-recovery label. Threshold crossings use current Dutch thresholds only;
hourly crossings are not the separate native-quarter-hour census.

| Result | Reading |
| --- | --- |
| Stable conditional state/peer increment | State or peer evidence helps distinguish responses in the measured setting; not proof of a physical mechanism. |
| Increment only under some storm regimes | A conditional relationship to investigate and report, not a universal neighbour ranking. |
| No increment | Rainfall/local state already account for the information captured here, or the chosen representation is uninformative at this resolution. |
| TTM no better than raw/state | Retain the hydrological analysis without an AI superiority claim. |
| Incomplete/censored extreme | Event-specific evidence is limited; do not substitute a false negative or stop the other analyses. |

Outputs: common catalogue/coverage, hourly source-bound arrays, all comparisons,
case browser and figures, coefficients/intervals, forward-year relationship
contrasts, pulse ledger, internal results and independent audit. No new model
weight training, RAG, field request, hydraulic model or simulated-state experiment.
Conditional storm/state simulation remains the later option described in the
literature review, rather than a fourth analysis in this implementation.
