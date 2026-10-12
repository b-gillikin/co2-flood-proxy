# Limburg cross-tributary current-data analysis

Status: internal scientific analysis of the currently held data, 2026-10-03.
This supersedes the initial-flow interpretation in
`cross-tributary-rainfall-analysis-2026-10-03.md`: antecedent discharge is
measured at the **hour ending before** the first wet radar hour. It is not
dissertation prose or a prospective protocol. The design followed inspection
of the earlier case-crossover result; all inference is exploratory. Brian
writes the manuscript.

## Question and inputs

During precipitation episodes defined independently of discharge, how many
of the six Dutch watercourses are observed above their era-specific p99
discharge threshold? Do spatial precipitation extent, episode amount, and
antecedent observed flow each describe variation in that six-site high-water
footprint? The outcome is within-episode high discharge, not a new threshold
crossing, official warning level, inundation, damage, forecast, or causal
effect. The sites are not six independent basins: Gulp and Eyserbeek lie in
the Geul system, although Cottessen is upstream of their confluence.

The inputs remain the held 2010–2025 Waterschap quarter-hour discharge,
RADOLAN hourly catchment precipitation, rating-era metadata, and provider
notes. ERA5-Land 2 m temperature, already held for the chapter, is used only
for a freezing-precipitation sensitivity. No new data request or model family
was introduced.

## Event and measurement audit

The main event rule identifies regional wet hours when at least one RADOLAN
catchment has 0.2 mm/h, joins them across up to 12 dry hours, and retains an
episode if any catchment receives at least 10 mm in a rolling 24 hours. The
observation window ends 24 hours after the last wet hour or immediately
before the next raw rain episode, whichever is earlier. The 12-hour dry gap
and 10-mm qualification are operational choices, not site-calibrated
hydrologic constants. We vary both and the post-rain window.

The rule yields 444 episodes. For the six-site descriptive comparison, 359
have at least 90% admissible discharge hours at every site, complete radar
precipitation at every site, and no site already above p99 in the hour before
rain. The event-level model also requires an observed pre-rain hour at all six
sites, leaving 357 episodes in 16 calendar years. This is an observability
restriction, not a claim that the omitted episodes were dry or unimportant.

Across the 359 comparable episodes, the number of high-water sites is
0:149, 1:64, 2:31, 3:33, 4:28, 5:19, 6:35. Thus 146 have at least two high
sites; 35 have all six. Reviewed new onsets appear at at least two sites in
132 episodes. Ninety-four site-episodes are high without a new reviewed
onset, often because high water continues or reappears within the existing
72-hour local episode. The outcome uses observed hours above p99 for that
reason. Seventy-eight high site-episodes last only one hour; a sensitivity
requires at least three consecutive hours above p99.

All 16 precipitation episodes lasting at least 72 hours were inspected in
the generated rain–discharge contact sheets. Each contains two or more rain
pulses separated by at least six dry hours. The hydrographs show plausible
multi-pulse response or nonresponse; none was removed as a demonstrated data
error. Excluding these long episodes is a sensitivity because assigning one
rainfall summary to several pulses can obscure their timing. The 12-hour rule
has a 122-hour maximum event; the 24-hour gap rule can merge up to 358 hours.

Only one main-rule rain episode has a site-hour above its documented rating
domain: the July 2021 event. Twenty-two rain episodes include Gulp discharge
above its approximately 3 m³/s documented calibration extent. Gulp p99 is
around 1.27–1.32 m³/s, below that extent, so the **side** of the threshold
can remain known even where peak magnitude is uncertain. Provider notes and
the review flags still warrant a sensitivity omitting affected episodes. That
omission does not change the model association directions. In July 2021 all
six sites are above p99, but Geul and Worm have poor admissible coverage and
four of five reviewed onsets have a measurement concern. July is descriptive,
not a six-peak-magnitude or fine-order validation case.

The eight largest model residual episodes were also inspected as
rain–discharge plots. They include real-looking, coherent multi-site rises
after moderate precipitation and substantial precipitation without a p99
crossing. They are not automatically invalid measurements. The 2010-01-31
nonresponse occurred during potentially freezing precipitation (regional
ERA5-Land rain-weighted median temperature −0.44 °C); the 2023-01-14
nonresponse was around 8.14 °C, so freezing cannot explain all divergence.
ERA5 temperature is a coarse phase indicator, not a rain/snow observation.

## Adjusted association

One bounded event-level working-binomial **mean** model relates the number of
high sites (0–6) to four terms: number of sites with at least 10 mm in 24
hours, log2 of the largest site-24-hour precipitation amount, median six-site
discharge/p99 in the hour *before* rain, and warm season (May–October).
The six sites are dependent, so naive binomial standard errors are discarded.
Uncertainty uses 999 bootstrap resamples of whole calendar years. All 999
main draws converged. This is a conditional descriptive model; the event
precipitation summaries include hours after some high-water crossings and
therefore cannot be used as forecast predictors at episode onset.

Model-standardized differences in expected number of high sites, averaging
over the observed event covariates, are:

| Comparison | Difference in expected high sites | 95% year-block interval |
| --- | ---: | ---: |
| Rain footprint: 3 to 6 sites with at least 10 mm | +0.63 | +0.36 to +0.95 |
| Regional peak site-24-hour precipitation: 12.56 to 21.01 mm | +1.26 | +1.06 to +1.46 |
| Median pre-rain discharge/p99: 0.125 to 0.207 | +0.76 | +0.55 to +0.92 |
| Warm versus cold, at measured covariates | −0.93 | −1.31 to −0.62 |

These comparisons are model descriptions, not intervention effects. The
pre-rain discharge ratio is a practical antecedent-flow proxy, not a direct
soil-moisture measurement. Rainfall spatial extent and amount are moderately
correlated; their fitted terms distinguish patterns *conditional on this
specific working mean*, not isolated physical mechanisms. The warm-season
contrast may reflect unmodeled seasonally varying processes as well as
antecedent state.

The fitted mean is reasonably aligned with observed counts across eight
groups of fitted values, but individual events can differ by more than four
sites; mean absolute error is 0.95 site. Pearson dispersion under the naive
six-trial binomial variance is about 2.05, another reason to use year-block
intervals and not call this a calibrated prediction model. Omitting any one
year keeps the pre-rain-flow coefficient positive (0.98–1.17 logit units per
0.1 of p99) and the rain-extent coefficient positive (0.21–0.27 per added
site), but 16 years remain a modest uncertainty base.

## Robustness and its limit

The adjusted terms retain their directions with 100% rather than 90%
discharge coverage (325 episodes); exclusion of episodes at least 72 or 48
hours long (343/304); exclusion of onset concerns, rating-domain exceedance
and above-calibration Gulp episodes (323); a three-consecutive-hour high-water
outcome (357); 5-mm rain qualification (708); 24-hour dry gap (319); and
12- or 48-hour post-rain response windows (358/357). Omitting July 2021
changes the fitted coefficients negligibly because its major event already
fails the main coverage screen.

Adding log2 episode duration to the working mean, to check whether longer
observation opportunities explain the pattern, also leaves the three rainfall
and pre-rain-flow coefficients essentially unchanged. Its duration coefficient
is +0.007 logit units per doubling, with a 95% year-block interval of −0.118
to +0.121. This is a sensitivity, not evidence that duration never matters in
other event definitions.

The 20-mm rain-only selection leaves 102 comparable episodes. The pre-rain
flow coefficient remains positive in the point fit but its year-block
interval includes zero (−0.06 to +1.68 logit units per 0.1 of p99), and one
of 999 bootstrap fits fails. A claim that initial flow has a resolved
conditional role **among only the heavier rain episodes** is therefore not
supported. The spatial-rain and amount terms remain positive there, with
wider intervals.

Thirteen of 444 episodes have a wet hour whose six-cell median ERA5-Land 2 m
temperature is at or below 0 °C. Removing those from the main model leaves
346 episodes; requiring rain-weighted median temperature above 2 °C leaves
348. Rain-extent, precipitation-amount and pre-rain-flow terms stay positive
with year-block intervals above zero in both sensitivities. This checks a
likely snow/phase confound without claiming ERA5 can observe precipitation
phase directly.

## German candidate extension

The four September LANUK discharge exports each have 560,929 quarter-hour
timestamps and align to fixed UTC+1, right-edge hourly means. The separate
source audit finds 140,232 complete hours for Herzogenrath 1 and Randerath,
140,229 for Herzogenrath 2 and Honsdorf. All four have complete hours in the
July 2021 Dutch rain window and exceed their **provisional full-series** p99
there. This is clock and coverage compatibility only. The German candidate
gauges lack matching prepared catchment-rainfall series and provider-verified
reconstruction/rating periods. Herzogenrath 1 and Randerath are nested Wurm
stations, not two independent tributaries. Do not pool their provisional
labels into the Dutch model while Jens's answers remain outstanding.

## Scientific interpretation

The held Dutch data support a nontrivial retrospective chapter about the
**regional footprint of high discharge**, with distinct descriptive roles
for precipitation amount/extent and antecedent observed flow. It is stronger
than the claim that rain precedes high water, yet it does not identify a
causal runoff mechanism or demonstrate warning lead time, warning skill,
forecast transfer, or flood damage. The episode definitions, p99 thresholds,
six-site network composition and observational model should be discussed
with supervisors before manuscript claims are fixed. No additional data
source is needed for the Dutch analysis; an optional German extension depends
on the pending source answers.

Relevant primary research treats flood spatial dependence as an outcome and
shows that precipitation structure and catchment state can shape it:
[Brunner et al. 2020](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2020GL088000),
[Brunner et al. 2021](https://hess.copernicus.org/articles/25/105/2021/).
For the operational rain-event separation trade-off and pre-event flow as a
wetness proxy, see [this 2019 event-separation study](https://hess.copernicus.org/articles/23/4869/2019/)
and [this 2021 rainfall–streamflow study](https://hess.copernicus.org/articles/25/2301/2021/).
Those studies motivate checks; they do not validate our exact thresholds.

## Reproduction

Run scripts 53, 54, 55 and 57 in order with the chapter Python environment,
then script 56 for the temperature sensitivity. All output CSVs, audit plots,
failed-draw records and manifests are ignored under
`results/event_study/cross_tributary_rain_v1/`; source inputs retain their
existing provenance. Scientific unit checks are in
`tests/test_cross_tributary_rain_episodes.py`,
`tests/test_cross_tributary_model.py`, and
`tests/test_german_candidate_clock.py`.
