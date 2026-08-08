# Prospective Event-Study Protocol

Version: **draft 0.5, not locked** (2026-08-08).

This protocol becomes locked only after (a) every **core regional** data gate
passes and (b) the supervisor approves the research question. The separate
Kerkrade case is included only if its own gate passes. No new event-study
outcome table may be inspected before the version, input hashes and lock
timestamp are added to §13. This is a repository protocol, not an externally
registered study.

## 1. Question and estimands

> Across Limburg tributaries, which public hydrometeorological signals recur
> during the 72 hours before independently defined high-water onset, and how
> does their event-minus-quiet signal change with distance from the affected
> watercourse? If the source data support a Kerkrade case, does
> pressure-adjusted CO2 recur there as a local manifestation of that regional
> state?

The first estimand is the local event-minus-matched-control contrast for each
fixed signal. The second is its spatial gradient: the change in all-donor
contrast magnitude per unit change in `log(1 + distance_km)` from the receiver.
Here **transferability means spatial extent**, not sign agreement, prediction
at an ungauged basin or substitution of one gauge for another.

Spatial extent is primary. The regional record must contain July 2021, but no
missing local peak or onset is invented. CO2 recurrence is a conditional case,
not a prerequisite for the regional estimand.

## 2. Hard gates and input contracts

Run:

```bash
python scripts/31_event_study_gates.py
```

The audit reports two components. Only **core** failures cause a nonzero exit.

| component | file | minimum contract |
| --- | --- | --- |
| core | `data/interim/event_study_discharge_hourly.csv` | unique regular hourly UTC index plus one column per primary gauge |
| core | `data/interim/event_study_gauges.csv` | gauge/watercourse identity, coordinates, cohort/QA flags and July 2021 status |
| core | `data/interim/radolan_catchment_hourly.csv` | unique regular hourly UTC index plus one catchment-average column per primary watercourse |
| core | `data/interim/event_study_catchments.gpkg` | polygons used for the RADOLAN spatial average |
| core | `data/interim/event_study_weather_hourly.csv` | regular tidy hourly UTC temperature, relative humidity and pressure for every primary watercourse |
| core | `data/interim/event_study_weather_sources.csv` | one pre-outcome source and spatial-assignment record per primary watercourse |
| Kerkrade case | `data/interim/viefhues_iot.csv` | 2020–2021 CO2 and pressure including July 2021 |
| Kerkrade case | `data/interim/iot_hourly.csv` | retained later-era CO2 and pressure |
| Kerkrade case | `data/interim/kerkrade_iot_eras.csv` | non-overlapping device, calibration, ABC-processing and resolution records for both eras |

The core cohort must contain at least 10 natural tributary watercourses, 10
common years across discharge, RADOLAN and public weather, 20 joint-period p99
episodes per watercourse and 40 regional storms. Rating curve, coordinates,
timezone, unit, zero-sentinel, sampling/missingness semantics, public-weather
assignment and July 2021 gauge status must be complete. The joint period must
contain 15 July 2021. Within it, every primary discharge, RADOLAN and
public-weather series must have at least 80% observed hourly cells overall and
70% in every calendar year. These draft density values reuse the prior
chapter's 80% floor and add an annual backstop against multi-year gaps; they
require supervisor approval before lock. Gate event and storm counts use only
this joint period. The coordinate table must yield positive distances for every
ordered receiver-donor pair and populate empirical near, middle and far thirds.
At least 80% of all possible receiver-event/donor combinations must have donor
flow observed throughout the -13 to -1 hour window required for level and a
gap-honest 12-hour change. Availability must also be at least 70% within every
receiver and distance third. These draft spatial floors require supervisor
approval.

The conditional Kerkrade case additionally requires Worm/Wurm or a documented
hydrological pair, independently supported July 2021 lower/upper bounds and at
least three later exact pair-gauge p99 onsets with every CO2 and pressure hour
observed from -72 to -1. If any case requirement fails, report **Kerkrade case
not available**. Do not call missing recurrence data a null, and do not stop the
regional chapter.

For the executable gate, 10 years means at least 3,650 days between the
inclusive first and last common hourly endpoints. Missing values remain visible
on that grid and cannot be hidden by endpoint span or event counts. The
catchment GeoPackage must open successfully and contain one unique, valid,
non-empty polygon per primary watercourse in a projected CRS.

If any core gate fails, stop. Do not use the rolling 2024–2026 Waterschap file
as a substitute. Case-gate failure removes the Kerkrade analysis only.
Groundwater is not a gate.

## 3. Population and time axis

Use one pre-declared representative gauge for each natural tributary
watercourse. Exclude main stems, canals, managed structures, reversing or
controlled flow series and gauges without documented QA. Selection cannot use
event contrasts.

All analytical series use a complete hourly UTC grid. Missing observations
remain missing. Do not interpolate discharge, bridge a missing hour when
identifying a crossing, or turn a missing RADOLAN code into zero.

## 4. Episodes and regional storms

For each crossed validation fold, estimate the receiver's p99 and p95 from its
observations outside the held time block. The receiver series is used only to
define its outcome and contamination periods; receiver flow is not a candidate
signal.

A primary episode starts when discharge moves from at or below p99 to above p99
on adjacent observed hours. Merge re-crossings whose consecutive onsets are at
most 72 hours apart. This is unbounded single-linkage: a chain can span more
than 72 hours if every consecutive gap remains within 72 hours. Save the first
and last crossing, number of crossings and chain span for every episode. Across
watercourses, apply the same consecutive-onset rule to regional storms and
report their chain length.

Exact crisis-plan Fase crossings at the named leading gauges are a sparse
sensitivity. Inventory thresholds at other points are not treated as
equivalent.

The primary precursor window is -72 to -1 hours. Sensitivity windows are -24 to
-1 and -168 to -1. The event timestamp itself is excluded from signal summaries.

## 5. Matched quiet references

For each event, candidate reference times are hours on the same receiver,
calendar month and UTC hour. Candidates require every primary public signal and
must be more than seven days from any receiver p95 exceedance and any regional
storm onset.

Rank eligible candidates deterministically by absolute distance from the event
time, then timestamp; take the first five. Exclude an event with fewer than
three. The selected timestamps are saved before signal contrasts are computed.

Control values cannot cross the temporal holdout. For a held-out event, controls
must lie in the same held time block; for a reference event, controls must lie
outside that block. Thus no reference event or control summary reads a held-time
observation.

Each fixed rolling signal is evaluated at the end of the precursor window
(`onset - 1 hour`) and at the matched reference hour. Event-time trajectories
remain descriptive figure data and do not create additional tested lags.

## 6. Fixed signals

Fixed public signals:

- catchment-average RADOLAN rainfall totals over 24 and 72 hours;
- public temperature and relative-humidity means over 24 hours;
- pressure level and six-hour pressure change;
- flow divided by its reference-period p99 and its 12-hour change on that scale.

The local recurrence analysis uses the receiver's catchment rainfall and public
weather. Receiver flow is used only to define its event. The spatial-extent
analysis evaluates every other eligible watercourse as a donor and applies all
fixed signals—including donor flow—at the receiver's event and control times.
No nearest donor is selected and no pair is removed because its contrast is
weak, strong or inconvenient.

The source and spatial assignment for temperature, humidity and pressure are
chosen and documented before the protocol lock. The held Visual Crossing and
KNMI tables are source candidates/context, not an automatic assignment to the
primary watercourses.

If the case gate passes, Kerkrade-only signals are raw CO2, pressure-adjusted
CO2 and available groundwater level/change. CO2 contrasts use the median hourly
value over each specified precursor window and require every hour in that
window; public rolling signals use their `-1 hour` values. Groundwater reporting
is secondary mechanism evidence.

## 7. Pressure adjustment

This section applies only if the Kerkrade gate passes. Fit separate linear
pressure baselines in the documented 2020–2021 and 2025–2026 sensor eras.
Features are pressure level and 1/3/6/12/24-hour pressure changes. Fit only on
complete quiet calibration hours and require at least 100. Apply the era model
to all complete hours, then subtract the quiet-calibration median and divide by
its MAD within that era. Save the feature table, calibration mask, coefficients
and residual series.

A seasonal/diurnal baseline is sensitivity-only. Do not choose between
baselines from event performance.

## 8. Event contrasts: recurrence

For event `e`, signal `s` and each valid control `c`, calculate the fixed signal
summary. The contrast is:

`event summary(e, s) - median control summary(e, c, s)`.

Before the contrast, express public summaries—and conditional Kerkrade
summaries if available—relative to the quiet-period median and MAD estimated
outside the held time block. Do not use test-period values to define a threshold
or scale.

Report every event-level contrast. Aggregate event contrasts to one median per
watercourse before describing the network distribution. For each signal report
the watercourse median, IQR and sign count. Resample entire regional storms,
recompute watercourse and network summaries, and report percentile intervals;
do not resample event rows independently.

Events, controls, quiet scaling and contrasts are constructed separately for
every held-watercourse-by-held-block validation fold. Each contrast row carries
`fold_heldout_watercourse` and `fold_heldout_time_block`; a globally thresholded
or globally scaled table is invalid input to the held-out validation.

## 9. Spatial extent and held-out validation

For receiver event `e` on watercourse `r`, evaluate each fixed signal at every
other watercourse `d` at `e - 1 hour` and at the receiver's saved matched-control
times. Use the same fixed summaries and training-only median/MAD scaling as in
§8. The spatial pair contrast is:

`donor event summary(e, r, d, s) - median donor control summary(e, r, d, s)`.

Distance is the great-circle distance in kilometres between the pre-declared
representative gauge coordinates. Catchment-centroid distance is a sensitivity
only and is not chosen from fit. Retain every ordered receiver-donor pair with
complete inputs.

Fit the following prespecified linear mixed-effects model separately for each
signal:

`contrast ~ 1 + log(1 + distance_km) + (1 | receiver) + (1 | donor) + (1 | regional storm)`.

`beta` is the spatial-gradient estimand. Report `alpha`, `beta`, their
storm-resampled percentile intervals and the model-implied contrast at the
empirical 25th, 50th and 75th percentiles of distance. Resample whole regional
storms and refit the complete model; never resample pair-event rows
independently. Report the observed distance range. Do not derive a maximum-reach
cutoff or search alternative distance functions.

External validation crosses one entire receiver watercourse with one of five
contiguous equal-duration time blocks. Training removes the held watercourse
both as a receiver and as a donor, and removes every event and signal/control
observation in the held time block. For the hidden receiver, estimate p99/p95
from its own history outside the held block solely to define test events and
contamination; none of its events or signal values enter training. Reconstruct
all other thresholds, events, controls and scales from training data. Apply the
training fixed-effect distance curve—with no receiver or donor random
intercept—to complete pair contrasts in the held receiver-by-block
intersection. Emit every planned fold with event, pair and distance-stratum
counts. A draft eligible fold requires at least three receiver events and at
least one complete pair contrast in each empirical distance third. Report
observed-minus-predicted contrast, median absolute error and calibration by
distance quartile. Aggregate fold errors within receiver before describing the
network. These occupancy rules require supervisor approval before lock.

This estimates spatial coherence over the observed network. It does not prove
physical propagation, gauge substitutability, an ungauged-catchment result or a
monitoring radius. Kerkrade-only CO2 and groundwater signals do not enter this
network model because they exist at one site and sensor era.

## 10. Pre-committed readings

| result | reading |
| --- | --- |
| local rainfall or public weather recurs | that signal is repeatedly elevated or depressed before receiver high water |
| public-weather contrasts are null or heterogeneous | those signals do not show stable pre-high-water recurrence at this grain |
| a nonzero curve declines in absolute magnitude with distance without changing sign | the signal is spatially coherent but strongest near the affected watercourse |
| a nonzero curve is stable in absolute magnitude with distance | the signal has a broad regional footprint across the observed distance range |
| the fitted curve changes sign within the observed range | the spatial pattern changes across the network; the crossing is not labelled maximum reach |
| spatial contrast is centred near zero | no spatially coherent pre-high-water signal is detectable at this grain |
| gradient or held-out calibration is heterogeneous | spatial extent is storm- or watercourse-specific rather than stable |
| donor-flow level/change has stable spatial extent | other-watercourse flow reflects a regional high-water state over the observed range |
| donor-flow spatial contrast is null | donor flow does not provide a stable regional signature under the fixed design |
| conditional CO2 residual recurs in later Kerkrade events | the indoor residual may be a repeatable local manifestation |
| conditional CO2 residual does not recur | the 2021 indoor response was event-, sensor- or building-specific |
| Kerkrade gate does not pass | no new CO2 recurrence claim is estimable; this is not a null |
| all fixed contrasts are weak or heterogeneous | no stable pre-high-water signature is detectable under the design |

Null or heterogeneous results do not trigger new lags, thresholds, baselines or
model families. These readings commit interpretation; they do not impose an
arbitrary success or reach threshold.

## 11. July 2021 and Kerkrade recurrence

The core July 2021 figure shows observed regional rainfall, weather and
available discharge without imputing a missing local peak. If the Kerkrade gate
passes, add CO2, pressure and available groundwater, represent local high-water
timing as an independently supported interval, and quantify observed
trajectories and missingness. Do not include the episode in a calculation
requiring exact onset.

Only with a passed case gate, estimate raw and adjusted CO2 contrasts for later
exact-onset Kerkrade events and compare them with the observed 2021 trajectory.
A nonrecurring residual is a planned substantive conclusion, not grounds to
alter the pressure baseline. If the case gate fails, cite Viefhues as motivation
and report no new CO2 result.

## 12. Outputs and tests

Required tidy tables: `events.csv`, `controls.csv`, `local_signal_contrasts.csv`,
`watercourse_contrasts.csv`, `spatial_pair_contrasts.csv`,
`spatial_decay_estimates.csv` and `heldout_spatial_validation.csv`.

Required figures: July 2021 regional trajectory, public-signal event-time
profiles, watercourse contrast forests and spatial contrast-by-distance curves
with held-out observations. The first figure gains a Kerkrade CO2/pressure
overlay only if the case gate passes.

Before execution, tests must cover adjacent-hour p99 crossings, episode/storm
single-linkage diagnostics, joint-period event counting, observation density,
censored exclusion, control contamination, reference-only thresholds and
scaling, all-pair distance construction, spatial-window availability, explicit
crossed holdout exclusion, empty/sparse fold reporting, GeoPackage contents,
RADOLAN missing/spatial handling, the core/case gate split and sensor-era
pressure residuals. Before the outcome script is run, add synthetic tests for a
decaying magnitude, a flat nonzero curve, a null curve, storm-dominated
heterogeneity and held-out
fixed-effect prediction. Those estimators do not yet exist and are not claimed
as implemented.

## 13. Lock and amendments

Current state: **unlocked because the core regional data gates fail and
supervisor approval is not recorded**. The Kerkrade case is currently not
available, but that alone will not prevent a future core lock.

At lock, record:

- supervisor approval date;
- gate-audit path and hash;
- hashes of all analytical inputs;
- Git commit;
- protocol lock timestamp;
- any resolution of ambiguity made before outcome inspection.

Outstanding supervisor approvals for draft 0.5 are the spatial-gradient model,
study population, public-weather assignment, density and all-donor availability
values, held-out occupancy and acceptability of the July 2021 regional
treatment. Record separately whether the conditional Kerkrade evidence is
adequate for its case study.

After lock, append amendments here with date, change, reason and whether any new
outcome table had been viewed. Never rewrite the prior entry.
