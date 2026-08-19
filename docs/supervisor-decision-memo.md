# Supervisor Decision Memo

Updated 2026-08-19 from the student-reported supervisor response and the first
blind Waterschap availability audit. The meeting date and supervisor name were
not supplied. No prospective signal outcome has been calculated.

## Proposed chapter

> Across Limburg tributaries, which fixed public hydrometeorological signals
> recur during the 72 hours before independently defined high-water onset, and
> how do the direction and magnitude of their event-minus-quiet contrasts
> change with distance from the affected watercourse? If the source data
> support a Kerkrade case, does
> pressure-adjusted CO2 recur there as a local manifestation of that regional
> state?

The sequence is Viefhues's July 2021 observation -> Eryilmaz's same-site public-
weather explanation -> this chapter's recurrence and spatial-extent test.
Local and all-donor event-minus-quiet contrasts use the same definition.
Spatial event contrasts are aggregated to one median per ordered receiver-
donor pair and one fixed distance line is estimated per signal. There is no
classifier, warning-system evaluation, held-out prediction exercise or model-
family search.

## Response record

| item | supervisor response | current status |
| --- | --- | --- |
| 1. contribution | “sounds good” | approved |
| 2. transferability | not substitution, propagation, an operational radius or ungauged-basin performance | approved |
| 3. population | Limburg tributaries primary; NRW only if the same gates pass | approved |
| 4. data floor | asked whether the values are arbitrary, accepted or data-derived | not approved; explanation below |
| 5. coverage floor | asked where the percentages came from | not approved; explanation below |
| 6. public weather | accepted proceeding with ERA5-Land; requested period and assignment rule | approved; implementation below |
| 7. held-out evidence | three events acceptable for now if justified | superseded by the simpler non-predictive design below |
| 8. July 2021 and conditional CO2 | yes | approved |

The protocol remains unlocked. Items 4–5 still need an explicit decision. The
retirement of held-out prediction should be reported before lock so the
supervisor sees the final estimator that implements the approved contribution.

## 4. Where the data-floor numbers come from

The values are **not accepted hydrological thresholds** and were **not chosen
from prospective signal outcomes**, which do not yet exist. They are
author-chosen minimum-information safeguards:

- **10 watercourses** avoids reducing spatial extent to a few case studies. It
  yields 90 ordered receiver-donor pairs before missingness and roughly 30 per
  empirical distance third.
- **10 common years** rejects the rolling two-year record, keeps July 2021
  within a genuinely historical period and provides interannual replication.
  Ten is a round scope choice, not a field standard.
- **20 p99 episodes per watercourse** keeps a watercourse median and sign count
  from representing only a handful of episodes. Over ten years it corresponds
  to roughly two episodes per watercourse-year before control/completeness
  exclusions. It is a descriptive-stability judgement, not a power result.
- **40 regional storms** concerns the uncertainty unit. Pair and watercourse
  observations within one storm are dependent; materially fewer storms would
  make storm-resampled intervals depend on very few weather systems. Forty is
  a conservative design judgement, not a conventional cutoff.

Recommendation: retain these as provisional, run one blinded feasibility table
after data receipt and freeze the values before inspecting rainfall, weather,
donor-flow or CO2 contrasts. The table may use timestamps, gauge identities,
missingness, event counts and geometry only. If no defensible floor leaves a
cohort, stop and return to the supervisor; do not silently lower a floor to
admit the data.

## 5. Where the coverage percentages come from

The **80% overall** rule was inherited from the prior workflow. The **70% per-
year** backstop prevents a dense subset of years from making a ten-year endpoint
span look complete. The **80% overall/70% by receiver and distance third**
donor-window rules prevent missing flow from selectively removing particular
receivers or spatial ranges. The proposed **10 complete events per ordered
pair** prevents an equal-weighted pair median from representing one or two
episodes; it is half the 20-event watercourse floor. None is an externally
accepted cutoff.

Recommendation: treat them as provisional missing-data safeguards. Before
outcomes, show a blinded 70/80/90 availability table containing only:

- retained watercourses and common years;
- missing hours by series and year;
- eligible event/control windows;
- eligible receiver-donor windows by receiver and distance third; and
- complete event/control contrasts per ordered pair; and
- concentration of missingness around documented gauge failures.

Then obtain one supervisor decision and freeze it. Missing hours remain missing
under every option; the audit is not permission to interpolate or tune against
signal results.

**First blind availability result, 2026-08-19:** the delivery contains 15
series columns but only eight named watercourse labels. Requiring all four
quarter-hours for an observed hour, nine series across those eight labels pass
the provisional 80% overall/70% every-year rule. Seven series across seven
labels pass when both the overall and every-year cutoff is 80% or 90%. These
counts remain upper bounds: branch structure, 91.6% zeros at Selzerbeek
Molentak, threshold-only Munstergeleen measurements, duplicate Oud-Roosteren
columns, July 2021 range exceedance/failure and missing rating-curve metadata
may remove candidates. Do not freeze or lower the watercourse floor from these
counts alone.

| source series | watercourse / gauge | complete hours overall | lowest annual coverage | complete July 2021 hours | provisional 80/70 availability |
| --- | --- | ---: | ---: | ---: | --- |
| 11.Q.32 | Eyserbeek / Eys | 99.6% | 97.4% | 741/744 | pass |
| 6.Q.18 | Geleenbeek / Brommelen | 98.0% | 77.0% | 739/744 | pass |
| 6.Q.24 | Geleenbeek / Millen | 99.1% | 95.3% | 744/744 | pass; split/cap unresolved |
| 6.Q.22 | Geleenbeek / Munstergeleen | 63.6% | 5.8% | 744/744 | fail; threshold-labelled |
| 10.Q.29 | Geul / Cottessen | 96.2% | 75.3% | 371/744 | pass |
| 10.Q.30 | Geul / Hommerich | 92.9% | 22.3% | 62/744 | fail |
| 13.Q.34 | Gulp / Azijnfabriek | 99.3% | 96.2% | 744/744 | pass |
| 12.Q.31 | Selzerbeek / Partij | 86.2% | 45.4% | 329/744 | fail |
| 6.Q.25 | Vloedgraaf / Nieuwstadt | 99.0% | 95.5% | 744/744 | pass; split/mixed flow unresolved |
| 15.Q.41 | Voer / Mesch | 99.0% | 93.3% | 741/744 | pass |
| 18.Q.45 | Worm / Rimburg | 99.3% | 97.4% | 717/744 | pass |
| 6.Q.27 indicator | Geleenbeek / Oud-Roosteren | 77.1% | 0.0% | 744/744 | fail; meaning unresolved |
| 12.Q.46 | Selzerbeek / Molentak | 99.5% | 97.3% | 744/744 | pass; 91.6% observed zeros |
| 6.Q.27 | Geleenbeek / Oud-Roosteren | 87.7% | 6.1% | 744/744 | fail; duplicate ID unresolved |
| 10.Q.36 | Geul / Meerssen | 89.4% | 42.2% | 388/744 | fail; gravel-bar warning |

“Complete” here means that all four source quarter-hours exist. It does not
mean that the measurement was within range or otherwise valid. The provider's
July 2021 warning therefore overrides any inference from populated cells until
per-gauge quality intervals arrive.

## 6. Public-weather decision and period

Use **ERA5-Land as the sole regional public-weather source**. The student
reported the supervisor's approval to proceed on 2026-08-10.

Retain 2 m temperature, 2 m dew-point temperature and surface pressure. Derive
relative humidity with one fixed documented formula. ERA5-Land is 0.1-degree
reanalysis, not a station observation. Assign the nearest grid cell to each
predeclared catchment centroid and record shared cells as shared exposures.

Acquire **1 January 2001 through 31 December 2025**. The final period is the
longest qualifying common interval across discharge, RADOLAN and ERA5-Land,
contains July 2021 and includes at least ten years. Fix it after input QA and
before event contrasts. Visual Crossing remains part of the description of
Eryilmaz's predecessor data; no Visual Crossing pipeline or weather sensitivity
is retained for this chapter.

Official record: <https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land?tab=overview>

The source was selected before prospective outcomes and cannot be replaced
because another product later produces a stronger contrast.

## 7. Why the held-out fold was retired

The crossed receiver-by-time-block design answered a prediction question: how
well a fitted distance curve predicts a hidden receiver-period intersection.
The supervisor-approved meaning of transferability is narrower and clearer:
how the observed event-minus-quiet signal changes with distance across the
observed tributary network. Prediction error and calibration were therefore
unnecessary machinery.

The final proposed spatial estimator is:

1. compute all fixed event-level receiver-donor contrasts;
2. aggregate to one median per ordered receiver-donor pair;
3. fit `pair_median_contrast ~ 1 + log(1 + distance_km)` with equal pair
   weights;
4. resample complete regional storms for uncertainty; and
5. omit each watercourse and all of its receiver/donor pairs in turn to show
   influence.

The last step is a robustness check, not validation at an ungauged basin. The
earlier three-event fold minimum and per-fold distance-third occupancy rule are
therefore no longer applicable. Donor coverage is audited overall, by
receiver/distance third and per ordered pair before analysis.

## Approved substantive boundaries

Transferability means spatial extent over the observed network. It does not
mean gauge substitution, physical propagation, an operational radius or
ungauged-basin performance. July 2021 is a required regional anchor with no
invented local onset or peak. The Kerkrade CO2 analysis is conditional: if its
separate contract fails, the regional chapter continues and no new CO2 result
is claimed.

## Approval record

- [x] question and contribution approved;
- [x] all-donor spatial extent accepted as transferability;
- [x] Limburg natural-tributary population approved;
- [ ] numerical data floors approved after the explanation in §4;
- [ ] coverage and donor-availability floors approved after the blinded audit plan in §5;
- [x] ERA5-Land source and 2001–2025 acquisition approved;
- [ ] simplified pair-median distance estimator reported to supervisor before lock;
- [x] regional July 2021 treatment approved;
- [x] conditional Kerkrade-case rule approved.
