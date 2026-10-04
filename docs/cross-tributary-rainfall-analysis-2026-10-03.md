# Limburg cross-tributary rainfall analysis: first empirical pass

Status: internal first-pass analysis, corrected for pre-rain discharge timing
on 2026-10-03. See the subsequent full-audit note for adjusted results. Brian writes dissertation
prose. This does not replace the completed case-crossover fit or make a new
protocol claim. Reproduce with `python3.12 scripts/53_cross_tributary_rain_episodes.py`;
the ignored outputs, source hashes, script hash, and year-block draws are in
`results/event_study/cross_tributary_rain_v1/`.

## Question and measurement

For rainfall episodes defined without looking at discharge, how many of the
six Dutch watercourses exceed their own era-specific p99 discharge threshold,
and how does that footprint vary with the spatial precipitation footprint and the
flow state in the hour before the first wet hour? This is a high-discharge comparison, not an analysis
of water-level warning thresholds or forecast skill. The sites are not all
hydrologically independent: Gulp and Eyserbeek belong to the Geul network,
though the selected Geul gauge at Cottessen is above their confluence. Do not
interpret crossing order as flood-wave travel between sites.

Regional wet hours have at least 0.2 mm/h in one of six RADOLAN catchment
series. The main diagnostic joins wet hours separated by at most 12 hours and
retains episodes with at least 10 mm in a rolling 24-hour period in any one
catchment. The observation window runs from first wet hour through 24 hours
after the last wet hour, cut off before the next raw rain episode. This is an
exploratory definition, not a calibrated hydrologic lag. Sensitivities vary
the gap (12/24 hours) and rain qualification (5/10/20 mm).

The main high-water footprint counts sites with any admissible observed hour
above p99 during the window. Separately, reviewed *new onsets* count exact
crossings under the existing 72-hour local declustering rule. The high-water
state is the appropriate main footprint: an onset-only count misses a site
that is already above p99 or re-crosses within its existing local event.
Eyserbeek in July 2021 demonstrates this: it is above p99 during the regional
event although it has no new reviewed onset in that rainfall window.

## Observed result

The main rule finds 444 precipitation episodes over 2010–2025. There are 359 with
at least 90% admissible discharge hours at each of the six sites, complete
rainfall for all six, and no site already above p99 at the start. This
observability screen allows a clean comparison; the all-episode and fully
observed counts remain available in the outputs.

| Sites above p99 | Episodes among 359 observable episodes |
| ---: | ---: |
| 0 | 149 |
| 1 | 64 |
| 2 | 31 |
| 3 | 33 |
| 4 | 28 |
| 5 | 19 |
| 6 | 35 |

Thus 146/359 episodes (41%) show high water at two or more sites, and 35/359
(10%) at all six. New reviewed onsets occur at two or more sites in 132 of
these episodes. Where at least two such onsets occur, the median spread from
first to last onset is 4 hours. These times are threshold crossings affected
by catchment and threshold differences; they are not storm arrival or
independently measured flood-wave travel times.

The number of sites receiving at least 10 mm in 24 hours and the number with
high water have descriptive Spearman correlation 0.504 (calendar-year block
bootstrap percentile interval 0.425–0.590, 999 draws). Within the 175
episodes with a mixed high-water footprint (one to five sites), high-water
sites received a median 2.24 mm more peak 24-hour precipitation than other sites; the
difference is positive in 139/175 episodes (79%; year-block interval 73–86%;
median-difference interval 1.53–2.94 mm). This is an event-level spatial
association, not a causal estimate. Overlapping catchments, threshold
differences, and radar error complicate attribution.

Rain alone does not determine the footprint. Among 165 clean episodes with
at least 10 mm at all six sites, 34 have no site above p99 and 31 have all
six above p99. Their median regional peak site-24-hour rainfall is 16.72
versus 23.77 mm; the median six-site discharge/p99 ratio in the preceding hour is
0.138 versus 0.244. Across all 359 episodes, prior-hour flow ratio has Spearman
correlation 0.377 with high-water footprint, while prior-hour flow and peak precipitation
have correlation −0.053. Initial flow is an observed state proxy; it does not
directly measure soil moisture or establish a causal antecedent-wetness
mechanism. Season and storm severity remain possible confounders.

## Sensitivity and measurement limits

| Gap / rainfall rule | Rain episodes | At least two sites high | All six high |
| --- | ---: | ---: | ---: |
| 12 h / 5 mm | 878 | 184 | 44 |
| 12 h / 10 mm | 444 | 173 | 44 |
| 12 h / 20 mm | 133 | 89 | 28 |
| 24 h / 5 mm | 664 | 167 | 44 |
| 24 h / 10 mm | 385 | 162 | 44 |
| 24 h / 20 mm | 129 | 90 | 29 |

Raw counts change with event definition, as expected; multi-site high water
persists. A 24-hour separation can merge rain for up to 358 hours, so the
12-hour rule is easier to interpret. Even it has episodes lasting up to 122
hours; inspect long and multi-pulse episodes before formal inference. Under
the main rule, 325 episodes have 100% admissible discharge coverage at all six
sites; their footprint distribution is 0:130, 1:61, 2:25, 3:31, 4:26,
5:18, 6:34. Perfect coverage is not required to see the pattern, but avoids
mistaking a data gap for no flood.

The 10-mm rule captures 677/724 existing reviewed Dutch onsets. A 5-mm rule
captures 712; with no material-rain cutoff, 723. The remaining onsets are not
measurement failures by definition. The rainfall qualification and window
explain most nonmatches. These episodes are not a complete census of high
water.

The 13–15 July 2021 rainfall episode has all six watercourses above p99 but
only five new reviewed onsets. Geul and Worm have less than 90% admissible
discharge coverage in this window, and four of five reviewed onsets carry a
measurement-concern flag. July 2021 supports a descriptive regional
high-water statement, not a reliable comparison of six peak magnitudes or
fine onset order. Source QA and rating-domain limits still apply.

The four German LANUK exports are not pooled into these numbers. Their clock
and sampling conventions are compatible for a candidate extension, but
reconstructed periods and provisional rating validity await Jens's answer;
Herzogenrath 1 and Randerath also share the Wurm rather than adding two
independent tributaries.

## Interpretation and subsequent analysis

This pass finds substantial variation in cross-tributary high-water footprint
during independently defined rain episodes. Spatial rainfall and initial
observed flow each carry descriptive information; a simple “it rained, so
streams rose” account misses the all-rain/no-high and all-rain/all-high
contrast. The subsequent event-level adjusted model, long multi-pulse episode
review, measurement audit and event-definition sensitivities are complete in
`cross-tributary-current-data-analysis-2026-10-03.md`. They use held data and
do not require a predictive model or another data request.

The event-footprint framing is consistent with flood spatial-dependence work
that treats co-occurrence and timing across catchments as substantive
outcomes: [Brunner et al. 2021](https://hess.copernicus.org/articles/25/105/2021/),
[Brunner et al. 2019](https://hess.copernicus.org/articles/23/107/2019/),
and [Brunner 2023](https://hess.copernicus.org/articles/27/2479/2023/).
These sources do not validate this pilot's specific 12-hour/10-mm rule; its
sensitivity and hydrologic interpretation remain this project's responsibility.
