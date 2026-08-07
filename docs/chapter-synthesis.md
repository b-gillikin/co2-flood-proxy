# Chapter Synthesis — Prospective Design

Status: **data-gated; no new chapter result exists** (2026-08-07). This is the
canonical description of the proposed chapter. Estimator details belong in
`chapter-scope-and-preregistration.md`; current session state belongs in
`HANDOFF.md`.

## 1. Research question

> Across Limburg tributaries, which public hydrometeorological signals recur
> during the 72 hours before independently defined high-water onset, and do
> those signals remain detectable at unseen watercourses and periods? At
> Kerkrade, does pressure-adjusted CO2 recur as a local manifestation of that
> regional state?

This is an event-recurrence and transferability chapter. It is not an early
warning system, a flood predictor or a search for an unusual model.

## 2. Intellectual sequence

1. **Viefhues (2022)** documented indoor CO2 and other hydrological responses at
   one Kerkrade house around the July 2021 flood. That is a rich single-site,
   single-event observation.
2. **Eryilmaz (2025)** found that public outdoor weather reproduced much of the
   information in indoor variables for predicting high indoor CO2 at the same
   site outside the flood period. That is same-site feature substitution, not
   spatial transfer.
3. **This chapter** asks which components recur before independently defined
   high-water episodes and survive transfer to a new watercourse and a new time
   period. It separates regional public signal from event-, sensor- and
   building-specific response.

The sequence is cumulative: event observation -> public-signal explanation ->
out-of-place and out-of-time recurrence test.

## 3. Intended contribution

The chapter has one analysis: **event-minus-quiet signal contrasts**. It first
asks which fixed signals recur across independently defined high-water episodes.
It then asks whether the direction and magnitude learned from other
watercourses and periods remain visible in a held-out watercourse-period. No
outcome classifier is fitted.

Statistically, this is a matched event study with robust median/MAD contrasts
and blocked external validation. In plain terms: compare each event with similar
quiet times, summarize within watercourse, learn the usual signal from the other
watercourses and periods, and check whether it appears in the hidden one. The
only fitted equation is the Kerkrade pressure baseline used to adjust CO2.

July 2021 is a required, interval-censored Kerkrade anchor. It is described but
excluded from calculations that require an exact local high-water onset. Later
exact-onset Kerkrade events test whether pressure-adjusted CO2 recurs. A null is
substantive: it would distinguish portable hydrometeorological state from a
building-specific 2021 response.

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
six-hour change; and the nearest other-watercourse flow relative to its
reference-period p99 plus its 12-hour change. Receiver flow defines the outcome
and is not analysed as a candidate signal.

Kerkrade adds raw CO2, pressure-adjusted CO2 and, where available, groundwater
level/change. Pressure baselines are fitted separately for the documented
2020–2021 and 2025–2026 sensor eras, on quiet calibration hours only, using
pressure level and 1/3/6/12/24-hour changes. Residuals are standardised within
era against quiet calibration hours. Seasonal/diurnal adjustment is a sensitivity.

Validation holds out one entire receiver watercourse and one of five contiguous
time blocks. For each signal, its expected direction is the median of the other
watercourses' median contrasts outside the held period. The observed held-out
contrast, its direction, magnitude difference and event counts are reported.
Fold summaries are aggregated within watercourse before the network is
described. There is no predictive score or arbitrary transfer threshold.

## 5. Hard feasibility gates

The design is not final and the protocol is not frozen until all of these pass:

- original August 2020–September 2021 Kerkrade IoT CO2 and pressure, with
  device identity, calibration and ABC-processing information;
- at least 10 natural tributary watercourses with 10 common years of hourly
  discharge, at least 20 p99 episodes each and at least 40 regional storms;
- Worm/Wurm, or a hydrologically defensible and documented Kerkrade pair;
- at least three later exact-onset events at that pair with complete CO2 and
  pressure in the primary 72-hour window;
- hourly 1-km RADOLAN rainfall averaged over verified catchment polygons;
- at least 10 common years of temperature, humidity and pressure assigned to
  each watercourse by a source/rule fixed before outcome inspection;
- documented rating-curve changes, timezones, units, zero sentinels and July
  2021 gauge failures.

The executable audit is `scripts/31_event_study_gates.py`. On 2026-08-07 it
fails because the contracted long discharge, RADOLAN catchment, long public
weather and original IoT files are absent. This is a stop, not permission to
lower the gate to the current two-year record. Groundwater is secondary
mechanism evidence and cannot block the chapter.

## 6. July 2021 treatment

The Kerkrade figure will show CO2, rainfall, pressure and available groundwater,
with the high-water onset represented as an interval wherever gauge damage or
uncertainty prevents exact timing. The chapter will not impute a peak, treat
the failure as random missingness or include the episode in pooled exact-onset
calculations.

## 7. Pre-committed readings

| result | reading |
| --- | --- |
| rainfall recurs and transfers | antecedent rainfall is a portable pre-high-water signal |
| temperature, humidity or pressure recur and transfer | an E-derived public signal is portable in its own right |
| public-weather contrasts are null or heterogeneous | those signals do not show stable pre-high-water recurrence at this grain |
| donor-flow level/change recur and transfer | neighbouring flow reflects a portable regional high-water state |
| donor-flow contrasts are null or heterogeneous | neighbouring flow does not travel consistently under the fixed distance rule |
| CO2 residual recurs in later Kerkrade events | the indoor residual may be a repeatable local manifestation |
| CO2 residual does not recur | the 2021 indoor response was event-, sensor- or building-specific |
| all fixed contrasts are weak/heterogeneous | no stable pre-high-water signature is detectable under the design |

Null or heterogeneous results do not trigger new lags, thresholds or model
families.

## 8. Existing Kerkrade context

The retained Eryilmaz re-evaluation is same-site predecessor context only. It
does not estimate pre-high-water recurrence or spatial transfer and cannot
substitute for the gated event study.

## 9. Claims ruled out

The manuscript will make no claim about flood prediction, causal effects,
operational warning lead time, FEWS performance, alert thresholds, monitoring
placement or ungauged catchments generally. p99 denotes relative high water,
not damage or a statutory flood stage.

## 10. Required products

If the gates pass and the protocol is frozen before outcome inspection, the
analysis will generate tidy event, control, contrast and held-out-transfer
tables and four figures:

1. July 2021 Kerkrade trajectory with censored high-water interval;
2. event-time public-signal profiles across watercourses;
3. watercourse-level contrast forest plots;
4. held-out signal direction and magnitude by watercourse and period.

Every manuscript number must regenerate from those tidy artifacts.
