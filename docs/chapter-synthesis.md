# Chapter Synthesis — Prospective Design

Status: **data-gated; no new chapter result exists** (2026-08-11). This is the
canonical description of the proposed chapter. Estimator details belong in
`chapter-scope-and-preregistration.md`; current session state belongs in
`HANDOFF.md`.

## 1. Research question

> Across Limburg tributaries, which public hydrometeorological signals recur
> during the 72 hours before independently defined high-water onset, and how
> does their event-minus-quiet signal change with distance from the affected
> watercourse? If the source data support a Kerkrade case, does
> pressure-adjusted CO2 recur there as a local manifestation of that regional
> state?

This is an event-recurrence and spatial-extent chapter. It is not an early
warning system, a flood predictor or a search for an unusual model.

## 2. Intellectual sequence

1. **Viefhues (2022)** documented indoor CO2 and other hydrological responses at
   one Kerkrade house around the July 2021 flood. That is a rich single-site,
   single-event observation.
2. **Eryilmaz (2025)** found that public outdoor weather reproduced much of the
   information in indoor variables for predicting high indoor CO2 at the same
   site outside the flood period. That is same-site feature substitution, not
   spatial extent.
3. **This chapter** asks which components recur before independently defined
   high-water episodes and measures how far their spatial coherence extends
   across other watercourses. It separates regional public signal from event-,
   sensor- and building-specific response.

The sequence is cumulative: event observation -> public-signal explanation ->
recurrence and spatial-extent test.

## 3. Intended contribution

The chapter has two linked estimands built from the same
**event-minus-matched-quiet contrasts**. First, local contrasts establish which
fixed signals recur at the affected watercourse. Second, all-donor contrasts
measure the same signals at every other eligible watercourse at those event and
control times, then estimate how contrast magnitude changes with geographic
distance. No outcome classifier is fitted.

Statistically, this is a matched event study plus one prespecified spatial
gradient per signal. In plain terms: compare each event with similar quiet
times; then ask whether rain, weather or flow at other watercourses shows the
same event-related departure, and whether that departure weakens with distance.
Receiver, donor and regional-storm random intercepts account for repeated
observations.
The distance curve is checked at receiver-period intersections excluded from
fitting. The only other fitted equation, if the Kerkrade case is available, is
the pressure baseline used to adjust CO2.

July 2021 must lie within the regional study period and is described without an
invented local peak or onset. The Viefhues IoT reanalysis and later-event CO2
recurrence test are a conditional Kerkrade case. If its data gate fails, the
published observation still motivates the chapter but no new CO2 result is
claimed and the regional analysis proceeds.

## 4. Fixed study design

The primary outcome is an upward crossing of a watercourse-specific p99 with
observations on both adjacent hours. Re-crossings within 72 hours are one
episode; episodes across watercourses within 72 hours form a regional storm.
The primary precursor window is -72 to -1 hours, with -24 to -1 and -168 to -1
sensitivities.

Each episode receives five deterministic quiet reference candidates from the
same watercourse, calendar month and UTC hour. A control cannot lie within
seven days of a receiver p95 exceedance or regional storm. Events with fewer
than three valid controls are excluded.

Fixed public signals are catchment-average RADOLAN rainfall over 24 and 72
hours; 24-hour temperature and relative-humidity means; pressure level and
six-hour change; and flow relative to the donor's reference-period p99 plus its
12-hour change. Receiver flow defines the outcome and is never a signal for its
own event. Spatial contrasts use every other eligible watercourse; no donor is
selected from its outcome or apparent fit.

ERA5-Land is the approved primary weather source. The fixed acquisition period
is 2001–2025; after the cohort is fixed, each watercourse receives the grid cell
nearest its verified catchment centroid. Visual Crossing remains predecessor
context only.

If its separate gate passes, Kerkrade adds raw CO2, pressure-adjusted CO2 and,
where available, groundwater level/change. Pressure baselines are fitted
separately for the documented 2020–2021 and 2025–2026 sensor eras, on quiet
calibration hours only, using pressure level and 1/3/6/12/24-hour changes.
Residuals are standardised within era against quiet calibration hours.
Seasonal/diurnal adjustment is a sensitivity.

For each signal, one fixed model relates the contrast to
`log(1 + distance_km)`, with receiver, donor and regional-storm random
intercepts.
Uncertainty resamples complete regional storms. Results are predicted at the
empirical distance quartiles; the observed distance range, rather than an
invented cutoff, defines the scope of inference. Validation holds out one
receiver watercourse and one of five time blocks, fits on the remainder and
reports fixed-effect prediction error in the hidden intersection. The held
watercourse enters training neither as receiver nor donor. There is no
predictive score, nearest-donor rule or arbitrary definition of maximum reach.

## 5. Feasibility gates

The regional chapter is not final and the protocol is not frozen until these
core gates pass:

- at least 10 natural tributary watercourses with 10 common years of hourly
  discharge, at least 20 joint-period p99 episodes each and at least 40
  regional storms;
- hourly 1-km RADOLAN rainfall averaged over verified catchment polygons;
- at least 10 common years of ERA5-Land temperature, humidity and pressure
  assigned to each watercourse by the fixed centroid-cell rule;
- at least 80% hourly coverage overall and 70% in every calendar year for each
  primary series over a joint period containing July 2021;
- documented rating-curve changes, sampling semantics, timezones, units, zero
  sentinels and July 2021 gauge status.
- complete flow level/change windows for at least 80% of all possible
  receiver-event/donor combinations overall and at least 70% within every
  receiver and empirical distance third.

These numerical floors are still provisional. They are author-chosen
minimum-information safeguards, not accepted hydrological standards. The
supervisor has asked for their provenance. Before any signal contrast is read,
a blinded availability audit will show the consequences of 70%, 80% and 90%
coverage rules and the supervisor will freeze the final choice.

The optional Kerkrade case has its own gate: source-native CO2 and pressure
throughout July 2021 plus adequate quiet calibration hours and
device/calibration/ABC metadata; Worm/Wurm or a documented hydrological pair;
independently supported July 2021 bounds; and at least three later exact-onset
pair events with complete CO2 and pressure over the primary window. Failure
means **case not available**, not core chapter failure and not a CO2 null.

The executable audit is `scripts/31_event_study_gates.py`. It still reports the
regional core as failed. ERA5-Land is approved and its fixed raw source grid is
being acquired; the analysis-ready catchment assignment and other binding
regional tables are absent. A
Viefhues source package has been delivered locally and
contains a cleaned August 2020–September 2021 table, raw May–September 2021 IoT
files and ABC-processing code. Its source-native K4 record is now normalised
and has all 744 July hours, but the pre-May lineage, sensor-era metadata,
hydrological pair, onset bounds and later-event support remain incomplete. The
regional audit deliberately does not turn those optional case requirements
into software gates; the case is assessed separately before any CO2 contrast.
Core failure is a stop, not permission to lower the gate to the current
two-year record. Groundwater cannot block either component.

The held LANUK archive was audited separately without signal outcomes. Under
the draft density and episode rules, its strongest tested decade supplies only
three qualifying gauges across two verified watercourses. Moreover,
`herzogenrath_2` and `honsdorf` are officially assigned to Broicher Bach and
Beeckflies rather than the Wurm. LANUK remains a source lead, not a qualifying
German cohort. The two officially matched Wurm gauges also have no observations
in the later IoT era, so the held archive provides zero later exact Wurm events;
events on Broicher Bach or Beeckflies cannot substitute. See
`lanuk-feasibility.md`.

## 6. July 2021 treatment

The core chapter will show the observed regional rainfall, weather and
available discharge trajectory without inventing a missing local peak. If the
Kerkrade gate passes, the figure additionally shows CO2, pressure and available
groundwater, with local onset represented as an independently supported
interval. Without that evidence, Viefhues's published finding remains context
and no new Kerkrade trajectory is presented.

## 7. Pre-committed readings

The complete result-to-interpretation table lives in §10 of the protocol, the
document that will be locked. It distinguishes a local distance decay, a broad
regional footprint, no spatial coherence and storm-specific heterogeneity.
None triggers new lags, thresholds or model families.

## 8. Existing Kerkrade context

The retained Eryilmaz re-evaluation is same-site predecessor context only. It
does not estimate pre-high-water recurrence or spatial extent and cannot
substitute for the gated event study.

## 9. Claims ruled out

The manuscript will make no claim about flood prediction, causal effects,
operational warning lead time, FEWS performance, alert thresholds, monitoring
placement or ungauged catchments generally. p99 denotes relative high water,
not damage or a statutory flood stage.

## 10. Required products

If the core gates pass and the protocol is frozen before outcome inspection,
the analysis will generate tidy event, control, local-contrast, spatial-pair,
distance-estimate and held-out-validation tables and four figures:

1. July 2021 regional trajectory, with the conditional Kerkrade overlay only if
   its gate passes;
2. event-time public-signal profiles across watercourses;
3. watercourse-level contrast forest plots;
4. spatial contrast by distance, with held-out receiver-period observations.

Every manuscript number must regenerate from those tidy artifacts.
