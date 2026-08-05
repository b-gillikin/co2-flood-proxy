# Chapter Direction

Status date: 2026-08-05

Supersedes the research question and claim structure in
`docs/chapter-readiness-plan.md` and `chapter/chapter-draft.md`.

## The question

> Does low-cost indoor CO2 at a post-mining site carry precursor information
> about high-flow events in Maas tributaries, beyond what barometric pressure
> and rainfall already provide?

The chapter is an early-warning feasibility study. It asks whether a cheap
indoor sensor could contribute lead time, and it is designed so that a negative
answer is as reportable as a positive one.

## Why tributaries

The site sits in the Wurm catchment, and the available gauges are all tributary
gauges: Wurm at Rimburg, Geul at Hommerich, Geul at Meerssen. The Wurm drains
the Kerkrade area and reaches the Maas via the Roer; the Geul joins the Maas
directly. None of them is the Maas main stem.

Tributaries receive less attention than the main river and are often absorbed
into basin-scale treatments, yet they are where small, flashy catchments
generate local flooding and where a building-scale sensor could plausibly be
relevant. Treating the tributary as the object of study, rather than as a
component of the Maas, is a deliberate framing choice of this chapter.

It also matches the instrument. A basement sensor in Kerkrade cannot say
anything about the Maas at Borgharen. It can only be about the catchment it
sits in.

## What counts as an event

Events come from `data/processed/event_catalogue.csv`, built by
`scripts/03_build_event_catalogue.py` from `data/interim/discharge_hourly.csv`.

Definition: a contiguous run of hours in which a gauge equals or exceeds a
percentile threshold of its own discharge distribution, lasting at least six
hours. Thresholds are the 90th, 95th and 99th percentiles. One row is written
per gauge and per threshold, so a single physical episode can appear up to nine
times; `src.eval.deduplicate_event_episodes` merges overlapping or touching
windows into independent episodes.

These are high-flow events, not disasters. Peaks in the usable set run from
2.7 to 33.0 m3/s. The July 2021 catastrophe is the extreme tail of this
distribution and is not in the discharge record held here, which begins
2025-01-01.

Usable set, requiring observed CO2 during the event and at least 60 observed
hours in the 72 hours before onset:

- 49 catalogue rows with any CO2 coverage during the event
- 44 rows also meeting the pre-event coverage requirement
- **19 independent episodes** after deduplication, spanning 2025-07-02 to
  2026-03-30, almost all inside the unbroken 104-day Blynk block

This is the event set the chapter analyses. It requires no data that is not
already held.

### Coverage accounting was wrong until 2026-08-05

The catalogue previously reported 175 events with IoT overlap. The true number
is 49. `annotate_event_overlap` had been passed the full hourly grid rather than
observed hours, so it credited coverage throughout the 2025-10 to 2026-03 sensor
outage. Fixed in `src/eval.py` and `scripts/03_build_event_catalogue.py`, which
now also record `iot_pre_event_hours`. Any earlier statement about event
coverage should be treated as wrong.

## The precursor mechanism, and its validity condition

The hydrological route would be: rainfall infiltrates, the water table rises,
rising water compresses the gas-filled void in the fractured post-mining
subsurface, and gas is displaced into the building. For this to support
warning, the subsurface has to move before the river does.

There is a competing route. Storms arrive with falling barometric pressure, and
falling pressure draws gas out of the ground regardless of any hydrology. This
route will produce a pre-event CO2 rise whether or not the water table does
anything.

**A barometric precursor is useless for early warning.** Atmospheric pressure is
already measured everywhere and forecast days ahead; nobody needs a basement CO2
sensor to detect an approaching low. So separating the two routes is not a side
analysis. It is the condition under which any positive result would mean
something, and it is why the chapter's principal instrument is barometric
decomposition.

## Evidence so far: the subsurface does not lead the river

`scripts/05c_groundwater_event_lag.py`, output in
`results/groundwater/event_lead_lag.txt`.

Seven episodes fall within the groundwater record. Across barometrically
corrected levels at all three wells:

- **Amplitude is 1 to 3 cm.** Event-related movement is 0.01-0.03 m in wells
  that span 1.67-2.91 m over 2021-2025.
- **No pre-event rise.** In both raw and locally detrended composites the water
  table sits at a local minimum at onset and recovers afterwards, reaching
  +0.019 to +0.024 m by 48 hours after onset. The response follows the river.
- **Cross-correlations are weak and inconsistent.** Peak absolute correlations
  of 0.13-0.29, with no coherent lag across gauges; the Geul gauges peak near
  zero lag with negative sign, the Wurm at +132 h on a much smaller sample.

On this evidence the hydrological precursor route has **no support** at these
wells.

The test is genuinely weak, and the limits belong with the result: all seven
episodes fall in a single July-August 2025 summer recession with dry antecedent
conditions and minimal recharge; the episodes cluster within five weeks so the
detrending windows overlap; the wells are shallow phreatic, 2.85-3.60 km away,
and are not a connected mine-water compartment. Nothing here tests winter, wet
antecedent states, or mine water.

## Finding: indoor CO2 carries no precursor skill

`scripts/18_precursor_skill.py`, output in `results/precursor/`.

Framed as forecasting: at each hour, does an episode onset fall within the next
24 hours? Predictors are rolling summaries available to a forecaster at that
moment. Hours inside events are excluded, because detecting a flood while it is
happening is not a precursor. 19 episodes, 3,492 scored hours, 445 of them
pre-event.

Intervals are moving-block bootstrap with one-week blocks, roughly 20
independent blocks. Resampling hours instead would have produced intervals
several times too narrow, since hourly observations are strongly autocorrelated.

| Predictor | AUROC | 95% CI | False alarms at 50% hit rate |
| --- | --- | --- | --- |
| Rainfall, 72 h | 0.835 | [0.737, 0.912] | 0.074 |
| Rainfall, 24 h | 0.794 | [0.695, 0.867] | 0.142 |
| Pressure level | 0.250 | [0.135, 0.377] | — |
| Raw CO2, 24 h | 0.523 | [0.399, 0.656] | 0.421 |
| Pressure change, 24 h | 0.470 | [0.371, 0.562] | 0.591 |
| **CO2 residual, 24 h** | **0.409** | **[0.267, 0.551]** | 0.638 |
| CO2 residual, 72 h | 0.405 | [0.234, 0.605] | 0.766 |

Rainfall and pressure level show clear skill; their intervals exclude 0.5.
Every CO2 predictor has an interval spanning 0.5, in raw or pressure-separated
form, at 24 or 72 hours. There is no detectable precursor skill in either
direction.

The three episodes with no pre-onset pressure fall — the only cases where a CO2
signature could not have been barometric — show no positive residual excursion
either (z of -0.58, -0.16, -0.13 against the quiet-hour baseline).

**Detectability bound.** The CO2 residual interval is about 0.14 wide either
side of the point estimate, so this design could have resolved a strong
precursor (AUROC beyond roughly 0.65) but not a modest one around 0.55-0.60.
The result is a bounded negative, not a demonstration of absence, and must be
reported that way.

## What the chapter now says

A low-cost indoor CO2 sensor at this site detects approaching **weather**, not
approaching **water**, and adds nothing to a rain gauge. The physical and
statistical evidence agree: the subsurface follows the river rather than leading
it, and the CO2 record carries no skill the barometer and rain gauge do not
already provide.

This is the chapter's result, not a failure to find one. It is a quantified
negative answer to a stated early-warning premise, with an explicit comparator,
an explicit false-alarm rate, and an explicit detectability bound. Very little
low-cost environmental sensing work reports any of the three.

## Design, and what remains

1. **Events.** 19 independent episodes. Done.
2. **Signal.** Pressure-separated residual before onset. Done.
3. **False-alarm rate.** Swept across all non-event hours. Done.
4. **Lead time.** Not pursued; there is no signature whose lead time could be
   measured.
5. **Skill baseline.** Rainfall and pressure, done, and they are what the
   chapter's conclusion rests on.

Remaining analytical work is characterisation rather than testing: the
barometric response function and its seasonal behaviour, and the figures.

## Data status

| Input | Status |
| --- | --- |
| IoT CO2, 2025-01-31 onward | Held. 96.9% and 99.0% hourly coverage in the two Blynk blocks; 30.7% in the 2026 Azure block |
| Discharge, 3 tributary gauges, hourly, from 2025-01-01 | Held |
| KNMI 06380 pressure, from 2020-01-01 | Held |
| Groundwater, 3 wells, 6-hourly, 2021-01-01 to 2025-08-27 | Held; barometrically corrected before use |
| Provincial wells within 2 km, mine-water network, pumping schedules | Requested 2026-08-05, awaiting reply |
| Viefhues IoT record, 2020-08 to 2021-09 | Not held. Valuable, not blocking |

The chapter can proceed with what is held. The Viefhues record would add the
July 2021 event as a single extreme case and would overlap the groundwater
already in the repository by roughly 243 days; it is worth pursuing, but the
early-warning question is answered by the 19 episodes, not by one catastrophe.

## Open questions

1. **Season.** Every usable episode falls in July-October 2025 or late March
   2026. There are no winter events, and winter is when antecedent wetness
   governs flood generation. Both the lead/lag and precursor results are
   summer-weighted, and this is the most serious limitation in the chapter.
2. **Magnitude.** Only three episodes reach the 99th percentile; the largest is
   33 m3/s. Nothing here approaches July 2021. A precursor could exist for
   extreme events and be absent for moderate ones.
3. **Compartment.** The wells are shallow phreatic, 2.85-3.60 km away, not a
   connected mine-water compartment. A mine-water series could behave
   differently; requested from Provincie Limburg 2026-08-05.
4. Whether the Viefhues 2020-2021 record can be obtained, which would add
   July 2021 as a single extreme case against groundwater already held.

Resolved since the previous revision: the 2026 device does not have a coverage
problem. Its 30.7% figure reflects one outage of 87.7 days
(2026-04-13 to 2026-07-09), not intermittent sampling; only two other gaps
exceed an hour, and coverage since restoration is 100%.

## Method retained

Pressure decomposition; barometric response function estimation by regression
deconvolution; well barometric efficiency correction; gap-honest coverage
accounting; local-level state-space modelling for the drifting indoor baseline;
SARIMAX as a residual-structure diagnostic only.

## Method retired

Ensemble anomaly detection: Isolation Forest, cross-detector agreement,
synthetic injection, rolling-origin detector evaluation. Anomaly detection finds
abrupt departures against no labels; this chapter has labelled events and a
defined pre-event window, which is a detection problem with a ground truth and
does not need them.

Also withdrawn: the four-branch claim machinery, the 60-paired-day gate, the
two-block sign criterion, and the seven-day future-water placebo. These were
scaffolding artifacts rather than chosen criteria, and two were defective; see
`docs/decisions.md` (2026-08-05).
