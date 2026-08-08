# Supervisor Decision Memo

Prepared 2026-08-08. The prospective signal outcomes have not been calculated.
This memo asks for design approval before the protocol is locked.

## Proposed chapter

> Across Limburg tributaries, which fixed public hydrometeorological signals
> recur during the 72 hours before independently defined high-water onset, and
> do their direction and magnitude remain visible at an unseen watercourse and
> period? At Kerkrade, does pressure-adjusted CO2 recur as a local manifestation
> of that regional state?

The sequence is Viefhues's July 2021 single-site observation -> Eryilmaz's
same-site public-weather explanation -> this chapter's recurrence and spatial
transfer test. The sole primary analysis is an event-minus-matched-quiet
contrast. There is no classifier, warning-system evaluation or model-family
search.

## Decisions requested

### 1. Does the held-out contrast satisfy the transferability requirement?

**Recommendation: yes.** The design hides one whole receiver watercourse and
one time period, learns the usual signal direction/magnitude from the remaining
watercourses and periods, and evaluates whether it is present in the hidden
intersection. This is external validation of a descriptive signal. It does not
measure distance decay, geographic reach or performance at an ungauged basin;
the manuscript will say so explicitly.

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
series over the joint study period, plus complete donor level/change inputs for
at least 80% of each receiver's events. The joint period must contain July 2021.
This prevents endpoint span and events from a few dense years from masquerading
as a ten-year record. A draft LANUK request asks whether its irregular
timestamps are true missing hours or a valid compressed/hold-forward series;
the rule should be confirmed after the reply but before signal outcomes.

### 4. How much evidence is required in a held-out fold?

**Draft recommendation:** retain every planned receiver-by-five-block row, but
mark a fold eligible only with at least three held-out event contrasts for that
signal and a nonempty reference set. Require at least three eligible blocks
within a receiver before making a receiver-level transfer statement. Report all
empty and sparse folds. This is an evidence floor, not a success threshold.

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

### 6. Is July 2021 supportable as the Kerkrade anchor?

**Recommendation: retain it only as interval-censored and require independent
evidence for the interval.** Archive termination or a multi-year data gap does
not itself bound onset. The original Viefhues IoT record, gauge damage/reliability
documentation and any defensible water-level or hydraulic evidence must supply
the lower and upper bounds. Without those, the anchor can be contextual prose
but cannot meet the current figure contract.

## Pre-agreed readings

The lockable protocol now states how positive, null and heterogeneous rainfall,
public-weather, neighbouring-flow and CO2 results will be read. A null CO2
residual means the 2021 indoor response may have been event-, sensor- or
building-specific; it does not trigger a new pressure baseline. Weak or
heterogeneous public signals remain a substantive finding under the fixed
design.

## Approval record

Record the meeting date and decisions here or in meeting notes, then copy the
resolved choices into protocol §13 before lock:

- [ ] question and contribution approved;
- [ ] held-out contrast accepted as transferability;
- [ ] population approved;
- [ ] density rule approved;
- [ ] fold-occupancy rule approved;
- [ ] public-weather source and assignment approved;
- [ ] July 2021 evidence requirement approved.
