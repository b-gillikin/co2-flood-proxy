# Supervisor Decision Memo

Prepared 2026-08-08. The prospective signal outcomes have not been calculated.
This memo asks for design approval before the protocol is locked.

## Proposed chapter

> Across Limburg tributaries, which fixed public hydrometeorological signals
> recur during the 72 hours before independently defined high-water onset, and
> how does their event-minus-quiet magnitude change with distance from the
> affected watercourse? If the source data support a Kerkrade case, does
> pressure-adjusted CO2 recur there as a local manifestation of that regional
> state?

The sequence is Viefhues's July 2021 single-site observation -> Eryilmaz's
same-site public-weather explanation -> this chapter's recurrence and spatial-
extent test. Local and all-donor event-minus-matched-quiet contrasts feed one
prespecified distance model per signal. There is no classifier, warning-system
evaluation or model-family search. The regional chapter does not depend on the
conditional Kerkrade case.

## Decisions requested

### 1. Does spatial extent satisfy the transferability requirement?

**Decision requested:** approve transferability as the distance relationship in
all-donor event contrasts. For each receiver event, the analysis measures the
same fixed signal at every other eligible watercourse at the event and matched
quiet times. One mixed-effects model per signal estimates the change in
contrast with `log(1 + distance_km)`, allowing receiver, donor and
regional-storm random intercepts.

The curve is reported at empirical distance quartiles and validated at
receiver-period intersections excluded from fitting; the held watercourse is
absent from training as both receiver and donor. This directly estimates
spatial extent within the observed network. It does not identify physical
propagation, a hard geographic reach, gauge substitution or an ungauged-basin
effect.

### 2. What is the study population?

**Recommendation: retain Limburg tributaries as primary while the historical
Waterschap request is pending. Do not reframe around NRW yet.** A reproducible
audit of the held LANUK archive found that its strongest tested ten-year window
has only three gauges across two verified watercourses passing the draft
density and episode rules. Natural/managed status and timestamp semantics also
remain unresolved.

Official metadata correct a consequential earlier claim:
`herzogenrath_2` is on Broicher Bach and `honsdorf` on Beeckflies. The Wurm
gauges are `herzogenrath_1` and `randerath`, and neither supplies the July 2021
event window or overlaps the later IoT era in the held archive. The apparent
later events occur on Broicher Bach and Beeckflies and are not Wurm recurrence
evidence. NRW should become the population only if a clarified/reconstructed
archive passes the same gates and the transboundary framing is substantively
approved.

### 3. What observation-density rule should lock?

**Draft recommendation:** at least 80% observed hourly cells overall and 70% in
every calendar year for every primary discharge, RADOLAN and public-weather
series over the joint study period. Complete donor level/change windows must
cover at least 80% of all receiver-event/donor combinations and 70% within
every receiver and empirical distance third. The joint period must contain
July 2021.
This prevents endpoint span and events from a few dense years from masquerading
as a ten-year record. A draft LANUK request asks whether its irregular
timestamps are true missing hours or a valid compressed/hold-forward series;
the rule should be confirmed after the reply but before signal outcomes.

### 4. How much evidence is required in a held-out fold?

**Draft recommendation:** retain every planned receiver-by-five-block row, but
mark a fold eligible only with at least three receiver events and at least one
complete pair contrast in every empirical distance third. Report all empty and
sparse folds. This is an evidence floor for validating magnitude, not a success
or reach threshold.

### 5. Which long public-weather source and spatial rule should be fixed?

**Recommendation for discussion:** use one cross-border gridded source rather
than choosing different national station networks after cohort selection.
ERA5-Land offers hourly 2 m temperature, 2 m dew point and surface pressure from
1950 onward; relative humidity can be derived from temperature, dew point and
pressure. Assign values by a fixed catchment-area average or, if the grid is too
coarse for meaningful averaging, the catchment centroid. Describe it as public
reanalysis, not a gauge observation. Use nearest official DWD/KNMI stations as
a sensitivity only if adequate common coverage is established.

This option provides consistent transboundary coverage but weakens the direct
observational link to Eryilmaz's public weather source. Approval should therefore
be substantive, not based on which source gives stronger event contrasts.

Official product description:
<https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land-timeseries?tab=overview>.

### 6. Should the Kerkrade CO2 analysis be conditional?

**Recommendation: yes.** A Viefhues source package has now been delivered
locally, including a cleaned hourly 2020–2021 table, raw 2021 IoT files and ABC
processing code, but it is not yet a passed analytical input. Require the
regional record to contain July 2021 and show only observed
public/hydrological trajectories in the core figure. Add the Viefhues
reanalysis and later CO2 recurrence only if the original IoT,
sensor-era provenance, valid hydrological pair, independently supported local
onset interval and at least three later complete event windows pass their
separate gate. Archive termination or a multi-year gap does not itself bound
onset. If the case gate fails, cite Viefhues as motivation and make no new CO2
claim; do not stop the regional chapter.

## Pre-agreed readings

The lockable protocol now states how local decay, a broad regional footprint,
no spatial coherence and storm-specific heterogeneity will be read for
rainfall, public weather and donor flow. If the conditional case is available,
a null CO2 residual means the 2021 indoor response may have
been event-, sensor- or building-specific; it does not trigger a new pressure
baseline. An unavailable case is missing evidence, not a null. Weak or
heterogeneous public signals remain a substantive finding under the fixed
design.

## Approval record

Record the meeting date and decisions here or in meeting notes, then copy the
resolved choices into protocol §13 before lock:

- [ ] question and contribution approved;
- [ ] all-donor distance gradient accepted as spatial transferability;
- [ ] population approved;
- [ ] density rule approved;
- [ ] fold-occupancy rule approved;
- [ ] public-weather source and assignment approved;
- [ ] regional July 2021 treatment approved;
- [ ] conditional Kerkrade-case rule approved.
