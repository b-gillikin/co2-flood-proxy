# Prospective Event-Study Protocol

Version: **draft 0.7, not locked** (2026-08-11).

This protocol locks only after every core regional data gate passes and the
supervisor approves the remaining numerical floors. The Kerkrade case is added
only if its separate gate passes. No prospective outcome table may be inspected
before the version, input hashes and lock timestamp are recorded in §13. This
is a repository protocol, not an externally registered study.

## 1. Question and estimands

> Across Limburg tributaries, which public hydrometeorological signals recur
> during the 72 hours before independently defined high-water onset, and how
> do the direction and magnitude of their event-minus-quiet contrasts change
> with distance from the affected watercourse? If the source data support a
> Kerkrade case, does
> pressure-adjusted CO2 recur there as a local manifestation of that regional
> state?

The first estimand is the local event-minus-matched-quiet contrast for each
fixed signal. The second is the slope relating the median contrast of every
ordered receiver-donor pair to `log(1 + distance_km)`. Here transferability
means **spatial extent across the observed network**. It does not mean
prediction, gauge substitution, physical propagation, an operational radius
or performance in ungauged basins.

The regional record must contain July 2021, but no missing local peak or onset
is invented. CO2 recurrence is a conditional case, not a prerequisite for the
regional estimands.

## 2. Hard gates and input contracts

Run:

```bash
python scripts/31_event_study_gates.py
```

The executable audit covers the binding regional inputs only. Any failure
causes a nonzero exit.

| component | file | minimum contract |
| --- | --- | --- |
| core | `data/interim/event_study_discharge_hourly.csv` | unique regular hourly UTC index plus one column per primary gauge |
| core | `data/interim/event_study_gauges.csv` | gauge/watercourse identity, coordinates, cohort/QA flags and July 2021 status |
| core | `data/interim/radolan_catchment_hourly.csv` | unique regular hourly UTC index plus one catchment-average column per primary watercourse |
| core | `data/interim/event_study_catchments.gpkg` | polygons used for the RADOLAN spatial average |
| core | `data/interim/event_study_weather_hourly.csv` | regular tidy hourly UTC temperature, relative humidity and pressure for every primary watercourse |
| core | `data/interim/event_study_weather_sources.csv` | one pre-outcome source and spatial-assignment record per primary watercourse |

The core cohort must contain at least 10 natural tributary watercourses, 10
common years across discharge, RADOLAN and weather, 20 joint-period p99
episodes per watercourse and 40 regional storms. Rating curves, coordinates,
timezone, units, zero-sentinel and missingness semantics, weather assignment
and July 2021 gauge status must be documented. The joint period must include 15
July 2021.

Within the joint period, every discharge, RADOLAN and weather series must have
at least 80% observed hourly cells overall and 70% in every calendar year. At
least 80% of possible receiver-event-donor combinations must have donor flow
observed throughout the -13 to -1 hour window needed for level and a gap-honest
12-hour change; availability must be at least 70% within every receiver and
empirical distance third, and every ordered pair must have at least 10 complete
receiver events. Distances must be positive for every ordered pair.

These numerical floors are provisional author-chosen information safeguards,
not accepted hydrological standards. They must be frozen after a blinded audit
of dates, missingness, event counts and geometry, and before any signal
contrast is inspected. Ten years means at least 3,650 days between the first
and last common hourly endpoints; missing cells remain visible on that grid.
The GeoPackage must contain one unique, valid, non-empty polygon per primary
watercourse in a projected CRS.

The conditional Kerkrade case is assessed separately. It requires
source-native CO2 and pressure throughout July 2021; at least 100 complete quiet
calibration hours in that sensor era; documented device, calibration and ABC
status; Worm/Wurm or a documented hydrological pair; independently supported
July 2021 lower and upper bounds; and at least three later exact pair-gauge p99
onsets with complete CO2 and pressure from -72 to -1. If any requirement fails,
report **Kerkrade case not available**. Do not call missing recurrence evidence
a null and do not stop the regional chapter.

If any core gate fails, stop. Do not substitute the rolling 2024–2026
Waterschap file. Groundwater is not a gate.

## 3. Population and time axis

Use one predeclared representative gauge for each natural tributary
watercourse. Exclude main stems, canals, managed structures, reversing or
controlled flow series and gauges without documented QA. Selection cannot use
event contrasts. NRW is an extension only if records pass the same gates.

All analytical series use a complete hourly UTC grid. Missing observations
remain missing. Do not interpolate discharge, bridge a missing hour when
identifying a crossing or turn a missing RADOLAN code into zero.

## 4. Episodes and regional storms

For each receiver, calculate p99 and p95 from observed discharge during the
fixed qualifying joint period. Receiver flow defines its outcome and
contamination periods only; it is not a signal for its own event.

A primary episode starts when discharge moves from at or below p99 to above p99
on adjacent observed hours. Merge re-crossings whose consecutive onsets are at
most 72 hours apart. This is unbounded single linkage: a chain may span more
than 72 hours if every consecutive gap remains within 72 hours. Save the first
and last crossing, number of crossings and chain span. Apply the same rule to
episode onsets across watercourses to define regional storms.

Exact crisis-plan Fase crossings at named leading gauges are a sparse
sensitivity. Inventory thresholds at other points are not treated as
equivalent.

The primary precursor window is -72 to -1 hours. Sensitivity windows are -24 to
-1 and -168 to -1. The event timestamp is excluded from signal summaries.

## 5. Matched quiet references

For each event, candidate references are hours on the same receiver, calendar
month and UTC hour. Candidates require every principal public signal and must
be more than seven days from any receiver p95 exceedance and any regional storm
onset.

Rank candidates deterministically by absolute time from the event, then by
timestamp; take the first five. Exclude an event with fewer than three. Save
the selected timestamps before computing contrasts.

Evaluate each fixed rolling signal at the end of the precursor window (`onset
- 1 hour`) and at the matched reference hour. Event-time trajectories are
descriptive figure data and do not create additional tested lags.

Control selection depends on receiver-side availability only, not on which
donor gives a stronger or more complete result. A spatial pair contrast
requires its donor event summary and at least three of the five saved donor
control summaries. Before values are summarised, audit that every ordered pair
still has at least 10 fully estimable event contrasts; otherwise the spatial
gate fails.

## 6. Fixed signals

The fixed hierarchy is:

**Principal hydrological signals**

- catchment-average RADOLAN rainfall totals over 24 and 72 hours;
- donor flow divided by its joint-period p99 and its 12-hour change on that
  scale.

**Eryilmaz-derived atmospheric block**

- public temperature and relative-humidity means over 24 hours;
- pressure level and six-hour pressure change.

The local recurrence analysis uses receiver-catchment rainfall and the
atmospheric block. The spatial analysis applies all fixed signals at every
other eligible watercourse at receiver event and control times. No nearest
donor is selected and no pair or signal is removed because of its result.

ERA5-Land is the sole regional source for temperature, humidity and pressure.
Acquire hourly 2 m temperature, 2 m dew-point temperature and surface pressure
for 2001–2025 over the fixed Limburg/cross-border extract. After cohort and
catchment polygons are fixed, assign the nearest 0.1-degree grid cell to each
catchment centroid and derive relative humidity with one documented formula.
Record shared cells as shared exposures. Visual Crossing is predecessor
context only.

If its case gate passes, Kerkrade-only signals are raw CO2,
pressure-adjusted CO2 and available groundwater level/change. CO2 uses the
median hourly value over each precursor window and requires every hour;
groundwater remains secondary mechanism evidence.

## 7. Pressure adjustment

This section applies only if the Kerkrade gate passes. Fit separate linear
pressure baselines in the documented 2020–2021 and 2025–2026 sensor eras.
Features are pressure level and 1/3/6/12/24-hour changes. Fit only on at least
100 complete quiet calibration hours. Apply the era model to all complete
hours, then subtract the quiet-calibration median and divide by its MAD. Save
the feature table, quiet mask, coefficients and residual series.

A seasonal/diurnal baseline is sensitivity-only. Do not choose between
baselines from event performance.

## 8. Local event contrasts: recurrence

For event `e`, signal `s` and valid controls `c`, calculate:

`contrast(e, s) = event_summary(e, s) - median(control_summary(e, c, s))`.

Express summaries relative to the median and MAD of eligible quiet hours in
the fixed joint period. If MAD is zero, use the quiet-period population
standard deviation; if that too is zero, the signal is not estimable. Save the
reference values used for scaling.

Report every event contrast. Aggregate to one median per watercourse before
describing the network distribution. For each signal report watercourse
medians, IQR and sign count. Resample complete regional storms, recompute the
watercourse and network summaries and report percentile intervals. Never
resample event rows independently.

## 9. Spatial extent

For receiver event `e` on watercourse `r`, evaluate each fixed signal at every
other watercourse `d` at `e - 1 hour` and at the receiver's saved control times:

`pair_contrast(e, r, d, s) = donor_event_summary - median(donor_control_summary)`.

Distance is the great-circle distance between the predeclared representative
gauge coordinates. Catchment-centroid distance is a sensitivity only. Retain
every ordered receiver-donor pair with complete inputs.

For each signal:

1. aggregate event-level pair contrasts to one median for each ordered
   receiver-donor pair;
2. fit the prespecified ordinary least-squares model
   `pair_median_contrast ~ 1 + log(1 + distance_km)`, giving each ordered pair
   equal weight;
3. resample complete regional storms, rebuild the pair medians and refit the
   line for percentile intervals;
4. report the intercept, distance slope, fitted contrast at the empirical 25th,
   50th and 75th distance percentiles and the observed distance range; and
5. repeat the fit after omitting each watercourse and every pair in which it is
   receiver or donor.

The leave-one-watercourse-out results are influence checks. They do not claim
prediction at a held-out or ungauged watercourse, and the slope is a descriptive
network association rather than a causal effect of distance. Do not search
alternative distance functions, derive a maximum-reach cutoff or condition the
spatial analysis on whether a local result is statistically significant.

## 10. Pre-committed readings

| result | reading |
| --- | --- |
| local rainfall or atmospheric signal recurs | that signal is repeatedly elevated or depressed before receiver high water |
| local contrasts are centred near zero or heterogeneous | that signal does not show stable pre-high-water recurrence at this grain |
| fitted pair contrast moves toward zero with distance | spatial coherence weakens over the observed distance range |
| fitted pair contrast remains similar over distance | the signal has a broad footprint over the observed network |
| fitted pair contrast changes sign | the spatial pattern changes; the crossing is not labelled maximum reach |
| pair contrasts are centred near zero | no spatially coherent pre-high-water signal is detectable at this grain |
| leave-one-watercourse-out slopes vary materially | the distance result depends on network composition and is not stable across watercourses |
| donor-flow level/change has a stable spatial pattern | other-watercourse flow reflects a regional high-water state over the observed range |
| donor-flow pair contrasts are null or heterogeneous | donor flow has no stable regional signature under the fixed design |
| conditional CO2 residual recurs later | the indoor residual may be a repeatable local manifestation |
| conditional CO2 residual does not recur | the 2021 response was event-, sensor- or building-specific |
| Kerkrade gate does not pass | no new CO2 recurrence claim is estimable; this is not a null |
| all fixed contrasts are weak or heterogeneous | no stable pre-high-water signature is detectable under the design |

Null or heterogeneous results do not trigger new lags, thresholds, baselines or
model families. No success or reach threshold is imposed.

## 11. July 2021 and Kerkrade recurrence

The core July 2021 figure shows observed regional rainfall, weather and
available discharge without imputing a missing local peak. If the Kerkrade
gate passes, add CO2, pressure and available groundwater, represent local
high-water timing as an independently supported interval and quantify observed
trajectories and missingness. Do not include the episode in calculations
requiring exact onset.

Only with a passed case gate, estimate raw and adjusted CO2 contrasts for later
exact-onset Kerkrade events and compare them with the observed 2021 trajectory.
A nonrecurring residual is a planned result, not grounds to alter the pressure
baseline. If the gate fails, cite Viefhues as motivation and report no new CO2
result.

## 12. Outputs and scientific checks

Required tidy tables: `events.csv`, `controls.csv`,
`local_signal_contrasts.csv`, `watercourse_contrasts.csv`,
`spatial_pair_contrasts.csv`, `spatial_pair_summaries.csv`,
`spatial_decay_estimates.csv` and `spatial_influence.csv`.

Required figures: July 2021 regional trajectory, public-signal event-time
profiles, watercourse contrast forests and ordered-pair median contrast by
distance. The first figure gains a Kerkrade CO2/pressure overlay only if its
case gate passes.

Before execution, scientific checks must cover adjacent-hour p99 crossings,
episode/storm single linkage, joint-period event counting, observation density,
censored-event exclusion, control contamination, fixed-period thresholds and
scaling, all-pair distances, spatial-window availability, GeoPackage contents,
RADOLAN missing/spatial handling and sensor-era pressure residuals. The
source-native Viefhues ingest is checked against its real-file QC. Add only the
synthetic estimator checks needed to protect the implemented claims: a
distance-decaying contrast, a flat nonzero contrast, a null contrast,
storm-resampling integrity and leave-one-watercourse-out pair removal. Those
estimators do not yet exist and are not claimed as implemented.

## 13. Lock and amendments

Current state: **unlocked because the core regional data gates fail and the
numerical data/coverage floors remain under supervisor review**. The question,
meaning of spatial extent, Limburg population, ERA5-Land source, July 2021
treatment and conditional-case rule are approved.

At lock, record:

- supervisor approval date;
- gate-audit path and hash;
- hashes of all analytical inputs;
- Git commit;
- protocol lock timestamp;
- any ambiguity resolved before outcome inspection.

Outstanding approvals for draft 0.7 are the numerical cohort, density and
all-donor availability floors, including the 10-complete-event pair minimum.
The earlier three-event held-out-fold proposal is retired because the chapter
no longer makes a held-out prediction claim.
Record separately whether the conditional Kerkrade evidence passes its case
gate.

After lock, append amendments here with date, change, reason and whether any new
outcome table had been viewed. Never rewrite a prior amendment.
