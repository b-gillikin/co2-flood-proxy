# Chapter Synthesis — Prospective Design

Status: **data-gated; no chapter result exists** (2026-09-18). This is the
canonical description of the chapter. Estimator details belong in
`chapter-scope-and-preregistration.md` (draft 0.9); session state belongs in
`HANDOFF.md`; the redesign rationale is in `decisions.md` (2026-09-18).

## 1. Research question

> Across natural Limburg tributaries, how are public hydrometeorological
> signals in the 72 hours before independently defined high-water onset
> associated with that onset, and does the timing of that association differ
> between warm-season and cold-season events?

This is a time-stratified case-crossover study. It is not an early-warning
system, a flood predictor or a search for an unusual model.

## 2. Intellectual sequence

1. **Viefhues (2022)** documented an indoor CO2 response at one Kerkrade house
   around the July 2021 flood: one site and one exceptional event.
2. **Eryilmaz (2025)** found that public outdoor weather reproduced much of the
   information in the indoor variables at the same site: a public-signal
   explanation.
3. **This chapter** asks how public signals behave before independently defined
   high water across many events and watercourses, and when they depart from
   normal.

Viefhues and Eryilmaz motivate the question. The chapter analyses no CO2.

## 3. Intended contribution

The chapter measures **how far ahead of high-water onset public regional
signals depart from normal on small tributaries, and whether that differs
between convective summer and frontal winter regimes.**

That question has a policy consequence. If summer association concentrates
within hours of onset, public regional data cannot support day-ahead
anticipatory action for small tributaries in summer, and warning there depends
on nowcasting and prepared responses. If winter association builds over days,
anticipatory action is feasible then. Either way, warning for small catchments
should be season-specific. The chapter supports claims about **feasibility**,
not about **what works**.

Methodologically, the chapter brings the standard design for short-term
exposures preceding acute events in environmental epidemiology into hydrology:
the time-stratified case-crossover, analysed with conditional Poisson
distributed-lag models.

## 4. Fixed study design

- **Outcome:** an upward crossing of the watercourse's own p99 (per rating era)
  on adjacent observed hours. Re-crossings within 72 hours are one episode;
  episodes across watercourses within 72 hours form a regional storm.
- **Comparison:** at-risk hours from the same watercourse, year, month and hour
  of day. An hour is at risk when flow in the previous hour was at or below p99
  and no upward crossing occurred in the preceding 72 hours.
- **Signals:** hourly catchment rainfall from radar, operational RADOLAN RW unless decided otherwise (principal);
  hourly relative humidity and six-hour pressure change from ERA5-Land. Network
  state (other watercourses' percentile rank) is descriptive only.
- **Model:** conditional quasi-Poisson regression with distributed-lag
  cross-bases over lags 1–72 hours.
- **Primary estimand:** the warm-minus-cold-season difference in the rainfall
  lag-response, summarised as the cumulative association and the median
  association lag.
- **Uncertainty:** calendar year-month block bootstrap.
- **Secondary:** the pooled lag-response; whether humidity and pressure change
  add association beyond rainfall; watercourse-specific replication; stability
  across 2010–2017 and 2018–2025; exposure-response shape; the Fase comparison
  where thresholds are supplied.

Because every hydrological quantity is a within-gauge, within-era rank, the
design depends on rating-curve **stability**, not absolute accuracy.

## 5. Feasibility gates

The protocol is not frozen until these core gates pass:

- at least 5 natural, hydrologically independent watercourses, each with at
  least 20 joint-period episodes, and 6 for the cross-watercourse sign test;
- at least 10 common years including July 2021;
- at least 40 regional storms, and at least 15 per season for the primary
  estimand, with a fixed fallback to the pooled estimand;
- at least 80% hourly coverage overall and 70% in every year for every series;
- documented rating eras, sampling semantics, timezone, units, zero semantics
  and July 2021 status;
- radar rainfall averaged over catchments delineated across borders, and
  ERA5-Land assigned by the fixed centroid rule.

Each floor has a stated rationale in protocol §2. Six is the smallest cohort in
which unanimous sign agreement is distinguishable from chance.

## 6. Current evidence state

- **Discharge:** Waterschap Limburg delivered 2010–2025 quarter-hour data for
  15 series and eight named watercourses, with rating curves and July 2021
  station status. Timezone/DST, zero semantics and numerical coordinates are
  still open; a follow-up went to Waterschap on 2026-09-17.
- **Candidate cohort:** Eyserbeek, Geul (Cottessen), Gulp, Voer, Worm (Rimburg),
  and Geleenbeek or Vloedgraaf, which count as one watercourse if their high
  flows are shared. That is six candidates: one to spare for the core floor,
  and none for the sign test.
- **Weather:** the ERA5-Land 2001–2025 archive is complete and audited.
- **Rainfall and catchments:** catchments were delineated across borders on
  2026-09-18, with seven area checks within ±4.4%. RADKLIM cannot observe the
  Voer, so operational RADOLAN RW is being acquired. The ERA5-Land weather
  table is built.
- **Estimator:** implemented in Python. On synthetic data it reproduces the R
  reference to within 1e-13, and coverage of the primary estimand is close to
  nominal (93–97.5%).
- **LANUK:** the 15-minute export was offered on 2026-09-11, and a follow-up
  went to LANUK on 2026-09-17. It enters only through the conditional distance
  module, if it arrives before lock.
- **No threshold, event, storm or association has been calculated.**

## 7. July 2021 treatment

July 2021 must lie in the joint period. It is described without an invented
local peak or onset. Onsets observed within the rating domain are kept even
where the later peak exceeded it. The event is located against the fitted
pooled relationship descriptively.

## 8. Existing context

The Province of Limburg's 2026 DeepWaive test in the Selzerbeek is
contemporary institutional context. Its official register says the model is
still being researched and is not used for warnings. Retrospective signal
evidence, rapid flood information and an authorised operational FEWS are
different evidentiary objects.

## 9. Claims ruled out

No claims about flood prediction, causal effects, operational warning lead
time, FEWS performance, recommended alert thresholds, trigger skill, damage,
monitoring placement or ungauged catchments. "Association lag" describes when
signals depart from normal; it is not a warning lead time. p99 denotes relative
high water, not damage or a statutory flood stage.

## 10. Required products

Tidy event, storm, at-risk-hour, cross-basis, primary-estimand, secondary and
bootstrap tables, and five figures:

1. study network and cross-border catchments;
2. July 2021 regional trajectory;
3. seasonal rainfall lag-response curves;
4. watercourse forest plot;
5. network-state event-time profiles.

Every manuscript number must regenerate from those tidy artifacts.
