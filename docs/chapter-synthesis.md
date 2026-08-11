# Chapter Synthesis — Prospective Design

Status: **data-gated; no new chapter result exists** (2026-08-11). This is the
canonical description of the proposed chapter. Estimator details belong in
`chapter-scope-and-preregistration.md`; current session state belongs in
`HANDOFF.md`.

## 1. Research question

> Across Limburg tributaries, which public hydrometeorological signals recur
> during the 72 hours before independently defined high-water onset, and how
> do the direction and magnitude of their event-minus-quiet contrasts change
> with distance from the affected watercourse? If the source data support a
> Kerkrade case, does
> pressure-adjusted CO2 recur there as a local manifestation of that regional
> state?

This is an event-recurrence and spatial-extent chapter. It is not an early
warning system, a flood predictor or a search for an unusual model.

## 2. Intellectual sequence

1. **Viefhues (2022)** documented indoor CO2 and other hydrological responses at
   one Kerkrade house around the July 2021 flood: one site and one exceptional
   event.
2. **Eryilmaz (2025)** found that public outdoor weather reproduced much of the
   information in indoor variables for predicting high indoor CO2 at the same
   site outside the flood period: a public-signal explanation at that site.
3. **This chapter** asks which public signals recur before independently defined
   high-water episodes and how their event-related contrasts vary over space.
   It separates a regional public signal from event-, sensor- and
   building-specific response.

The sequence is therefore: event observation -> public-signal explanation ->
recurrence and spatial-extent test.

## 3. Intended contribution

The chapter uses one transparent quantity throughout:
**signal during the pre-high-water window minus that signal at matched quiet
times**.

The analysis has two linked stages:

1. At the affected watercourse, estimate which fixed public signals recur
   before high water.
2. At every other eligible watercourse, estimate the same contrast at the same
   times, aggregate to one median per ordered receiver-donor pair, and relate
   that pair contrast to geographic distance.

The quantitative analysis is a matched event study plus one prespecified
distance slope per signal. Complete regional storms, rather than individual
pair rows, are resampled for uncertainty. Leave-one-watercourse-out refits show
whether the slope depends on one member of the network; they are influence
checks, not predictions of an unseen basin.

No classifier, time-series filter, mixed-effects model, model-family search or
cross-validation framework is part of the prospective chapter. The only other
fitted equation, if the conditional Kerkrade case is available, is a
pressure-only baseline used to adjust CO2.

July 2021 must lie within the regional study period and is described without an
invented local peak or onset. The Viefhues IoT reanalysis and later-event CO2
recurrence test are conditional. If that case gate fails, the published
observation still motivates the chapter but no new CO2 result is claimed.

## 4. Fixed study design

The primary outcome is an upward crossing of a watercourse-specific p99 with
observations on both adjacent hours. Re-crossings within 72 hours are one
episode; episodes across watercourses within 72 hours form a regional storm.
The primary precursor window is -72 to -1 hours, with -24 to -1 and -168 to -1
sensitivities.

Each episode receives five deterministic quiet reference times from the same
watercourse, calendar month and UTC hour. A control cannot lie within seven
days of a receiver p95 exceedance or regional storm. Events with fewer than
three valid controls are excluded.

The signal hierarchy is fixed before outcomes are inspected:

- **principal hydrological signals:** catchment-average RADOLAN rainfall over
  24 and 72 hours, and donor flow relative to its p99 plus its 12-hour change;
- **Eryilmaz-derived atmospheric block:** 24-hour temperature and
  relative-humidity means, pressure level and six-hour pressure change;
- **conditional Kerkrade case:** raw CO2, pressure-adjusted CO2 and available
  groundwater.

Receiver flow defines its own outcome and is never a predictor or signal for
that event. Spatial contrasts use every other eligible watercourse; no donor,
signal or distance function is selected from the result.

ERA5-Land is the sole regional weather source. The fixed acquisition period is
2001–2025; after the cohort is fixed, each watercourse receives the grid cell
nearest its verified catchment centroid. Visual Crossing remains predecessor
context only.

For each signal, aggregate event-level donor contrasts to one median per
ordered receiver-donor pair. Fit one ordinary least-squares line:

`pair_median_contrast ~ 1 + log(1 + distance_km)`.

Each ordered pair receives equal weight. Report the intercept, distance slope,
storm-bootstrap intervals, fitted contrasts at the empirical distance
quartiles and the observed distance range. Refit after omitting each
watercourse and all pairs in which it is receiver or donor. The result describes
spatial coherence in this observed network; it does not establish an
operational radius, physical propagation, a causal effect of distance, gauge
substitution or performance in ungauged basins.

## 5. Feasibility gates

The regional chapter is not final and the protocol is not frozen until these
core gates pass:

- at least 10 natural tributary watercourses with 10 common years of hourly
  discharge, at least 20 joint-period p99 episodes each and at least 40
  regional storms;
- hourly 1-km RADOLAN rainfall averaged over verified catchment polygons;
- at least 10 common years of ERA5-Land temperature, humidity and pressure
  assigned by the fixed centroid-cell rule;
- at least 80% hourly coverage overall and 70% in every calendar year for each
  primary series over a joint period containing July 2021;
- documented rating-curve changes, sampling semantics, timezones, units, zero
  sentinels and July 2021 gauge status;
- complete flow level/change windows for at least 80% of possible
  receiver-event-donor combinations overall and 70% within every receiver and
  empirical distance third, with at least 10 complete events per ordered pair.

These numerical floors are provisional author-chosen minimum-information
safeguards, not accepted hydrological standards. Ten watercourses and ten
years prevent the chapter from collapsing into a few case studies; twenty
episodes prevents a watercourse summary from representing only a handful of
events; forty storms protects the storm-level uncertainty calculation from
being based on very few weather systems. Ten complete pair events prevents an
equal-weighted pair median from representing only one or two episodes. The
coverage floors prevent endpoint
span or a dense subset of years and distances from hiding major gaps. Before
any signal contrast is read, a blinded availability audit will show the
consequences of 70%, 80% and 90% coverage rules and the supervisor will freeze
the final values.

The optional Kerkrade case has its own gate: source-native CO2 and pressure
throughout July 2021 plus adequate quiet calibration hours and
device/calibration/ABC metadata; Worm/Wurm or a documented hydrological pair;
independently supported July 2021 bounds; and at least three later exact-onset
pair events with complete CO2 and pressure. Failure means **case not
available**, not core chapter failure and not a CO2 null.

The executable audit is `scripts/31_event_study_gates.py`. It still reports the
regional core as failed. ERA5-Land is approved and its fixed raw source grid is
being acquired; the analysis-ready catchment assignment and other binding
regional tables are absent. The delivered Viefhues package provides a
source-native K4 record with all 744 July 2021 hours, but broader device
provenance, a defensible hydrological pair, onset bounds and later-event support
remain incomplete. The regional audit deliberately keeps those optional case
requirements separate. Core failure is a stop, not permission to use the
rolling two-year record. Groundwater cannot block either component.

The held LANUK archive was audited without signal outcomes. Under the draft
density and episode rules, its strongest tested decade supplies only three
qualifying gauges across two verified watercourses. LANUK remains a source
lead, not a qualifying German cohort. See `lanuk-feasibility.md`.

## 6. July 2021 treatment

The core chapter will show observed regional rainfall, weather and available
discharge without inventing a missing local peak. If the Kerkrade gate passes,
the figure additionally shows CO2, pressure and available groundwater, with
local high-water timing represented as an independently supported interval.
Without that evidence, Viefhues's published finding remains context and no new
Kerkrade trajectory is presented.

## 7. Pre-committed readings

The complete result-to-interpretation table lives in §10 of the protocol, the
document that will be locked. It distinguishes recurring local signals,
distance decay, broad regional coherence, no spatial coherence and
storm/watercourse sensitivity. None triggers new lags, thresholds or model
families.

## 8. Existing Kerkrade context

Eryilmaz's supplied manuscript is same-site predecessor evidence only. It does
not estimate pre-high-water recurrence or spatial extent and cannot substitute
for the gated event study. No separate later-era re-fit is part of this chapter.

## 9. Claims ruled out

The manuscript will make no claim about flood prediction, causal effects,
operational warning lead time, FEWS performance, alert thresholds, monitoring
placement or ungauged catchments generally. p99 denotes relative high water,
not damage or a statutory flood stage.

## 10. Required products

If the core gates pass and the protocol is frozen before outcome inspection,
the analysis will generate tidy event, control, local-contrast, watercourse,
spatial-pair, distance-estimate and influence tables and four figures:

1. July 2021 regional trajectory, with the conditional Kerkrade overlay only if
   its gate passes;
2. event-time public-signal profiles across watercourses;
3. watercourse-level contrast forest plots;
4. ordered-pair median contrast by distance with the fixed fitted line.

Every manuscript number must regenerate from those tidy artifacts.
