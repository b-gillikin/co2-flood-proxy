# Supervisor Decision Memo

Updated 2026-08-11 from the student-reported supervisor response and subsequent
single-source weather decision. The meeting date and supervisor name were not
supplied. No prospective signal outcome has been calculated.

## Proposed chapter

> Across Limburg tributaries, which fixed public hydrometeorological signals
> recur during the 72 hours before independently defined high-water onset, and
> how does their event-minus-quiet magnitude change with distance from the
> affected watercourse? If the source data support a Kerkrade case, does
> pressure-adjusted CO2 recur there as a local manifestation of that regional
> state?

The sequence is Viefhues's July 2021 observation -> Eryilmaz's same-site
public-weather explanation -> this chapter's recurrence and spatial-extent
test. Local and all-donor event-minus-matched-quiet contrasts feed one
prespecified distance model per signal. There is no classifier, warning-system
evaluation or model-family search.

## Response record

| item | supervisor response | current status |
| --- | --- | --- |
| 1. contribution | “sounds good” | approved |
| 2. transferability | chapter is not about substitution, propagation, an operational radius or ungauged-basin performance | approved |
| 3. population | Limburg tributaries primary; NRW only if the same gates pass | approved |
| 4. data floor | asked whether the values are arbitrary, accepted or data-derived | not approved; answer below |
| 5. coverage floor | asked where the percentages came from | not approved; answer below |
| 6. public weather | accepted proceeding with ERA5-Land and requested the period and assignment rule | approved; implementation below |
| 7. held-out evidence | three events acceptable for now, but any retained or revised value must be justified | provisionally accepted; clarification below |
| 8. July 2021 and conditional CO2 | yes | approved |

The protocol remains unlocked. Items 4–5 need an explicit follow-up decision;
item 7 needs the clarified wording accepted before lock.

## 4. Where the data-floor numbers come from

They are **not accepted hydrological thresholds**, and they were **not chosen
from the prospective outcome data**, which are still absent. They are
author-chosen minimum-information rules tied to this design:

- **10 watercourses** supplies a minimally useful network rather than a few
  case studies. Ten watercourses give 90 ordered receiver-donor pairs before
  missingness and approximately 30 pairs in each empirical distance third.
- **10 common years** prevents the chapter from being driven by the rolling
  two-year public record, retains July 2021 inside a genuinely historical
  sample and provides interannual rather than single-storm replication. Ten is
  a round scope choice, not a field standard.
- **20 p99 episodes per watercourse** is derived from the five-block validation
  design: 20 episodes average four per block, leaving a one-event buffer above
  the proposed three-event test-fold minimum before controls and completeness
  exclusions. It does not guarantee four in every block.
- **40 regional storms** concerns the independent uncertainty unit. Pair and
  watercourse rows within a storm are not independent; with materially fewer
  storms, storm-resampled intervals would be dominated by a small number of
  weather systems. Forty is a conservative design judgement, not a formal
  power result.

Recommendation: retain these as **provisional floors**, describe them exactly
as design-derived rather than canonical, and run one blinded feasibility table
after the data arrive. That table may use timestamps, gauge identities,
missingness, event counts and network geometry, but no rainfall, weather,
donor-flow or CO2 contrasts. If the supervisor revises a floor after seeing
that table, amend the unlocked protocol before any outcome inspection. Do not
silently lower a floor to admit the available data.

## 5. Where the coverage percentages come from

The **80% overall** value was inherited from the prior chapter workflow. The
**70% per-year** backstop was added during the event-study redesign so that a
dense subset of years could not make a ten-year endpoint span look complete.
The **80% overall/70% by receiver and distance third** donor-window rules were
added to stop missing donor flow from selectively removing particular
receivers or long-distance pairs. None is an externally accepted cutoff.

Recommendation: keep them provisional as transparent missing-data safeguards,
not literature-based standards. Before outcomes are calculated, show a blinded
availability table at 70%, 80% and 90% that reports only:

- retained watercourses and common years;
- missing hours by series and year;
- eligible event/control windows;
- eligible receiver-donor windows by receiver and distance third; and
- whether missingness is concentrated around documented gauge failures.

Then obtain one supervisor decision and freeze it. Missing hours remain
missing under every option; the audit is not permission to interpolate. If no
candidate rule leaves adequate support, the result is a failed data gate, not
a reason to tune percentages against signal results.

## 6. Public-weather decision and period

Decision: use **ERA5-Land as the sole regional public-weather source**. The
student reported the supervisor's approval to proceed on 2026-08-10.

ERA5-Land supplies one consistent hourly field across Dutch Limburg and any
later NRW extension. The retained variables are 2 m temperature, 2 m dew-point
temperature and surface pressure; relative humidity is derived from temperature
and dew point using one fixed published formula. The product is reanalysis at
0.1° (about 9 km), so call it
reanalysis rather than a station observation. Assign the nearest ERA5-Land
grid cell to each predeclared catchment centroid. Record watercourses sharing a
cell; do not present duplicated cells as independent weather measurements.

Download **1 January 2001 through 31 December 2025** so weather does not limit
the currently plausible radar/discharge intersection. The final analysis
period is the longest qualifying common interval across discharge, RADKLIM and
weather, must contain July 2021 and must include at least ten complete years.
It is fixed after input QA and before event contrasts.

Boundary with the predecessor:

- **Visual Crossing** remains faithful to Eryilmaz's predecessor analysis, but
  it is a commercial aggregation/interpolation product and the held four-city
  files sit near the ten-year boundary. Keep it only in the predecessor check.

Official records:

- ERA5-Land: <https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land?tab=overview>
- Visual Crossing source documentation: <https://www.visualcrossing.com/resources/documentation/weather-data/weather-data-sources-and-attribution/>

The source was selected before the prospective event contrasts. It cannot be
replaced later because another product produces a stronger pre-high-water
contrast.

## 7. Held-out evidence clarification

The proposed minimum of **three receiver events** is connected to the data
floor rather than being a conventional validation sample size: 20 events over
five blocks average four per block, and three is the minimum retained after
event/control completeness exclusions. Three remains sparse, so every fold
will report its event count and no single fold will support a reach claim.

Clarify the distance rule as follows: each of the at least three retained test
events must have at least one complete donor contrast in each training-defined
distance third. Thus an eligible fold has at least three pair-event rows per
third and spatial support is not supplied by one event or one isolated far
pair. Empty and sparse folds remain in the output as ineligible.

Any revision is allowed only after the blinded availability audit and before
outcome inspection. “Adjust if needed” must not become post-result tuning.

## Approved substantive readings

Transferability means spatial extent over the observed tributary network. It
does not mean gauge substitution, physical propagation, an operational radius
or ungauged-basin performance. July 2021 is a required regional anchor with no
invented local onset or peak. The Kerkrade CO2 analysis is conditional: if its
separate evidence contract fails, the regional chapter continues and no new
CO2 result is claimed.

## Approval record

- [x] question and contribution approved;
- [x] all-donor distance gradient accepted as spatial transferability;
- [x] Limburg natural-tributary population approved;
- [ ] numerical data floors approved after the explanation in §4;
- [ ] coverage and donor-availability floors approved after the blinded audit plan in §5;
- [x] ERA5-Land primary source and 2001–2025 acquisition approved;
- [ ] clarified held-out event/distance support approved;
- [x] regional July 2021 treatment approved;
- [x] conditional Kerkrade-case rule approved.
