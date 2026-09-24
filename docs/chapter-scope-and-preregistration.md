# Case-Crossover Analysis Protocol

Version: **draft 0.10, not locked** (2026-09-24).

This is an internal analysis plan, not a commitment to formal preregistration.
Record the data version, analysis choices and any changes in `decisions.md`.
Before estimating signal associations, audit available inputs and state the
claim scale they support. An unavailable or weak data component narrows that
claim; it does not automatically cancel the research question.

## Changes from draft 0.8

Draft 0.9 is a redesign recorded in `decisions.md` (2026-09-18). It replaces the
recurrence-plus-distance event study with a time-stratified case-crossover
study of seasonal lag structure.

| draft 0.8 | draft 0.9 |
| --- | --- |
| Recurrence plus a log-distance slope over ordered receiver-donor pairs | Recurrence and seasonal lag structure; the distance slope survives only as a conditional module (§9.5) |
| Conditional Kerkrade CO2 case | Removed; Viefhues and Eryilmaz become motivation only |
| Five nearest quiet hours per event, with p95/storm exclusion over seven days | Time-stratified at-risk hours (§5) |
| Event-minus-quiet medians and sign counts | Conditional quasi-Poisson distributed-lag models (§7) |
| Storm resampling | Calendar year-month block bootstrap; storms remain an information floor (§8) |
| Eight signals, including temperature, pressure level and all donor pairs | Hourly rainfall, relative humidity and six-hour pressure change; network state becomes descriptive (§6) |
| At least 10 watercourses | At least 5 for the core, and 6 for the cross-watercourse sign test, with stated rationales (§2) |
| Events censored when the peak exceeded the rating domain | Events censored only when the onset hour itself is missing or out of domain (§3) |

The draft 0.8 text remains in Git history.

## 1. Question and estimands

> Across natural Limburg tributaries, how are public hydrometeorological
> signals in the 72 hours before independently defined high-water onset
> associated with that onset, and does the timing of that association differ
> between warm-season and cold-season events?

The unit of analysis is the watercourse-hour. The outcome is a high-water onset
(§4). Signals are compared with the same watercourse's own at-risk hours from the
same year, month and hour of day (§5).

**Primary estimand.** The seasonal difference, warm season (May–October) minus
cold season (November–April), in the hourly-rainfall lag-response over lags 1–72
hours. The seasons are the hydrological half-years of DIN 4049-1, as used for
the Geul by Tsiokanos et al. (2024), who find most extreme hourly rainfall in
the summer half-year but most extreme flows in winter (decision D4,
2026-09-18). It is summarised by two quantities:

1. **cumulative association:** the rate ratio for onset accumulated over lags
   1–72 at the fixed rainfall contrast defined in §7; and
2. **median association lag:** the smallest lag ℓ at which the cumulative log
   rate ratio over lags 1..ℓ reaches half of its 1–72 total. A smaller value
   means the association is concentrated close to onset. It is reported as not
   estimable when the 1–72 cumulative association is not positive.

**Secondary estimands**, reported with intervals but interpreted descriptively:

- S1: the pooled, all-season rainfall lag-response;
- S2: relative-humidity and pressure-change lag-responses, adjusted for
  rainfall, asking whether the Eryilmaz atmospheric block carries association
  beyond rainfall;
- S3: watercourse-specific cumulative associations and their sign count;
- S4: temporal stability, 2010–2017 against 2018–2025;
- S5: the Fase comparison, conditional on receiving the thresholds (§9.2).

The seasonal contrast is the planned primary estimand when both seasons have
adequate information; otherwise lead with the pooled association and describe
the seasonal contrast with its uncertainty. This is an
associational study. "Lag" and "association lag" describe when signals depart
from normal before onset. They are not operational warning lead times.

## 2. Input validity and information audit

Run:

```bash
python scripts/31_event_study_gates.py
```

The executable audit distinguishes input-validity failures from descriptive
information benchmarks. A failure of essential source semantics or geometry
prevents the affected estimate until resolved. Counts and coverage percentages
describe precision, temporal representation and the supported claim scale; they
are not automatic chapter-stopping rules.

| component | file | minimum contract |
| --- | --- | --- |
| core | `data/interim/event_study_discharge_hourly.csv` | unique regular hourly UTC index plus one column per primary gauge |
| core | `data/interim/event_study_gauges.csv` | gauge/watercourse identity, independence unit, coordinates, cohort/QA flags and July 2021 status |
| core | `data/interim/event_study_rating_eras.csv` | non-overlapping rating eras per gauge (an era may span several intervals), with validity periods, rating domain, the discharge from which merged versions agree, and source document |
| core | `data/interim/radolan_catchment_hourly.csv` | unique regular hourly UTC index plus one catchment-average rainfall column per primary watercourse |
| core | `data/interim/event_study_catchments.gpkg` | one valid polygon per primary watercourse, delineated across national borders, naming its DEM |
| core | `data/interim/event_study_weather_hourly.csv` | regular tidy hourly UTC relative humidity and surface pressure for every primary watercourse |
| core | `data/interim/event_study_weather_sources.csv` | one pre-outcome source and spatial-assignment record per primary watercourse |

**Information benchmarks for the intended regional claim:**

- at least **5** natural, hydrologically independent tributary watercourses,
  with 20 joint-period p99 episodes per watercourse as a descriptive stability
  benchmark;
- 10 common years across discharge, rainfall and weather; and
- 40 regional storms in the joint period.

Fifteen regional storms per season is a benchmark for the seasonal contrast. If
one season contains few independent storms, lead with S1 and report the seasonal
contrast descriptively if estimable. July 2021 is a motivated historical case,
not a condition for analysing the other years.

Report hourly coverage for each series overall and by calendar year, with 80%
overall and 70% annually as reference values, not automatic exclusions. Report
complete event/control windows and whether missingness concentrates around high
water. Retain missing cells on the hourly grid; do not manufacture observations.

**Why these values were proposed.** They are author-chosen reference values, not
accepted hydrological standards or power calculations:

- **Five watercourses (core).** The primary estimand pools onsets across
  watercourses, and its information comes from storms, not from the number of
  watercourses. Five motivates the intended regional breadth; fewer may still
  support a multi-site or site-specific analysis with narrower language.
- **Cross-watercourse signs.** Report S3 signs and estimates descriptively.
  An exact binomial sign test assumes independent signs, which shared regional
  storms do not establish, even if the streams are hydrologically distinct.
- **Forty storms.** Regional storms are the independent weather systems behind
  the sample. Inference from few clusters is unreliable (Cameron, Gelbach and
  Miller 2008).
- **Fifteen storms per season.** Keeps the seasonal contrast from resting on a
  handful of weather systems.
- **Twenty episodes per watercourse.** Keeps a watercourse's own S3 estimate
  from resting on a handful of events.
- **Ten years** rejects the rolling two-year record and gives interannual
  replication.

Use the audit of dates, missingness, event counts and geometry to label the
supported result as a regional seasonal comparison, a pooled multi-watercourse
association, a narrower site/period analysis, or an evidence/feasibility result.
Show the event counts and uncertainty that justify the choice. Record any
change after inspecting signal associations and label it exploratory. The
rolling 2024–2026 Waterschap file may support a separately labelled shorter-
period analysis; it cannot silently replace the historical record or establish
interannual replication.

## 3. Population, events and time axis

**Population.** Use one predeclared representative gauge for each natural,
hydrologically independent tributary watercourse. Exclude main stems, canals,
managed structures, reversing or controlled flow series, composite estimates,
and gauges without documented QA. Selection cannot use signal associations.

Watercourses are independent only if their high flows are not routed into one
another. Branches of one split system count once. In particular, Waterschap
reports that Geleenbeek flow above 1 m³/s at Millen passes to the Vloedgraaf.
Geleenbeek (Brommelen) and Vloedgraaf (Nieuwstadt) therefore enter as one
watercourse if Brommelen lies upstream of that split, with the representative
gauge chosen on QA grounds before events are built.

Cohort (decision D3, 2026-09-18): Eyserbeek (Eys), Geul (Cottessen), Gulp
(Azijnfabriek), Voer (Mesch), Worm (Rimburg) and Geleenbeek (Brommelen).
Brommelen lies upstream of the Millen split and represents the
Geleenbeek/Vloedgraaf system; Nieuwstadt's flow depends on the split.
Selzerbeek is excluded: Partij fails coverage and Molentak is weir-controlled.

**Time axis.** All analytical series use a complete hourly UTC grid. Missing
observations remain missing. Do not interpolate discharge, bridge a missing
hour when identifying a crossing, or turn a missing rainfall code into zero.

**Waterschap semantics.** A source value is the mean of the preceding 15
minutes; a blank means unavailable data. Populate an hourly value only when all
four quarter-hours are present and admissible after source QA and a verified
timezone conversion.

**Rating eras.** Where rating-curve validity periods show a revision, compute the
p99 threshold separately within each documented era. Era boundaries come from
the provider's rating documentation and are fixed before any event is built.
An era boundary falls only where a version changes the relation at or above
p99. Versions that agree there, such as a datum re-levelling with the same
hydraulics or a low-flow-only revision, share one era. A short version that
changes the relation there is excluded rather than given its own p99
(decision D8, 2026-09-18). The merge is checked: each era's p99 must lie at or
above the discharge from which its versions agree to within 1%. Every version
as its own era is a sensitivity analysis.
Because every hydrological quantity is a within-gauge, within-era rank, the
design depends on the rating curve's stability, not its absolute accuracy.

**Censoring.** Censor an event's onset only when the onset hour or the hour
before it is missing, falls inside a documented failure interval, or lies
outside the valid rating domain in a way that leaves its side of p99 uncertain.
A value below the domain minimum is certainly at or below p99 when that minimum
is at or below p99, and a value above the domain maximum is certainly above p99
when that maximum is at or above p99. Such hours are kept (decision D6,
2026-09-18). A peak that later exceeds the rating domain
does not censor an onset observed within the domain. A record that resumes
above p99 after a gap, at a rating-era boundary or next to an inadmissible hour
starts a censored episode. That entry blocks at-risk hours for 72 hours like
any crossing. Censored onsets are retained as descriptive evidence and excluded
from estimation. p99 ranks every observed value in the era, including values
outside the rating domain, whose rank is certain even where their magnitude is
not.

**Stage, conditional.** If Waterschap supplies water-level records with datum
and sensor history, a censored discharge onset may be recovered from stage.
The recovered onset is the first adjacent-hour crossing of the stage
corresponding to that era's discharge p99 under the valid rating curve. Only
onset timing is recovered this way. Stage never substitutes for a discharge
history.

## 4. Episodes and regional storms

For each receiver and rating era, calculate p99 from observed discharge in the
fixed joint period. Receiver flow defines its outcome and is never a signal for
its own onset.

An episode starts when discharge moves from at or below p99 to above p99 on
adjacent observed hours. Re-crossings whose consecutive onsets are at most 72
hours apart merge into one episode by unbounded single linkage. Save the first
and last crossing, the number of crossings and the chain span. Apply the same
rule to episode onsets across watercourses to define regional storms.

The primary lag window is 1–72 hours. The onset hour itself is excluded from
every signal. A sensitivity analysis extends the maximum lag to 168 hours.

## 5. At-risk hours and time strata

The design is a time-stratified case-crossover design (Maclure 1991; Janes,
Sheppard and Lumley 2005), analysed in its equivalent time-series form
(Armstrong, Gasparrini and Tobias 2014).

An hour *t* is **at risk** for watercourse *w* when:

- discharge is observed at *t* and *t* − 1;
- discharge at *t* − 1 is at or below that era's p99; and
- no upward p99 crossing for *w* was observed in the preceding 72 hours.

That definition is the exact complement of the episode-merging rule: under
72-hour single linkage, a crossing starts a new episode exactly when no
crossing occurred in the preceding 72 hours. Every at-risk hour that is a
crossing is therefore an onset. It removes
the draft 0.8 exclusions around p95 exceedances and other watercourses' storms.
Hours with high but sub-threshold flow, and hours during storms on other
watercourses, are legitimate non-onset hours and are kept.

The outcome is 1 for an at-risk hour that is an onset, and 0 otherwise.

**Strata:** watercourse × calendar year × calendar month × hour of day. Each
stratum holds roughly 30 at-risk hours. Only within-stratum comparisons inform
the estimates, so seasonal, interannual, diurnal and watercourse-level
differences in baseline onset rates are controlled by design.

## 6. Fixed signals

| signal | source | role |
| --- | --- | --- |
| hourly catchment rainfall | RADKLIM-RW, or operational RADOLAN RW throughout (see below) | principal exposure |
| hourly relative humidity | ERA5-Land 2 m temperature and dew point, one documented formula | atmospheric block, S2 |
| six-hour surface-pressure change | ERA5-Land surface pressure | atmospheric block, S2 |
| network state | median within-era percentile rank of the other cohort watercourses' discharge | descriptive only |

**Rainfall product.** Use RADKLIM-RW, the reprocessed climatology-grade radar
product, if it covers the full joint period. Otherwise use operational RADOLAN
RW for the whole period. Never splice the two. Before acquisition, verify
coverage quality over South Limburg. The nearest radars are Essen and
Neuheilenbach. The check of 2026-09-18 found RADKLIM-RW masked outside a band
around Germany: the Voer catchment is never observed and 45% of the Gulp
catchment is not. Operational RADOLAN RW observes every candidate catchment.
**Decided (D2, 2026-09-18): operational RADOLAN RW throughout**, built and
checked for 2010–2025 (`data/interim/radolan_catchment_hourly.csv`).

**Catchments.** Delineate from a DEM that crosses national borders. The Geul,
Gulp and Voer rise in Belgium and the Worm drains Aachen, so Dutch-only
catchment layers would truncate them.

**Weather assignment.** Assign the ERA5-Land 0.1° cell nearest each fixed
catchment centroid. Record shared cells as shared exposures. Visual Crossing is
predecessor context only.

**Dropped from draft 0.8.** Temperature is dropped: it mainly tracks season,
which is now the contrast of interest. Pressure level is dropped in favour of
pressure change. Donor-flow pairs are replaced by the network-state description.
Network state is part of the same flood process, a co-symptom rather than an
exposure, so it is shown as event-time profiles and never modelled as a cause.

## 7. Model

For each specification, fit a conditional quasi-Poisson regression of the onset
indicator on the stratum structure, using a distributed-lag cross-basis for each
exposure (Gasparrini, Armstrong and Kenward 2010).

- **Lag dimension:** natural cubic spline over lags 1–72 hours with 4 degrees of
  freedom, knots equally spaced on the log scale. There is no degree-of-freedom
  search; one sensitivity analysis uses 6.
- **Exposure dimension:** linear in the primary model. The non-linear
  exposure-response is a secondary analysis (§9.1).
- **Fixed rainfall contrast:** the pooled 95th percentile of positive hourly
  catchment rainfall in the joint period, against zero. It is computed from
  exposure data only, before any model is fitted.
- **Season:** the rainfall cross-basis interacted with a warm-season indicator.
  Season main effects are absorbed by the strata.

Model specifications:

1. **Primary:** rainfall cross-basis × season.
2. **S1:** rainfall cross-basis alone.
3. **S2:** rainfall, relative-humidity and pressure-change cross-bases jointly.
4. **S3:** specification 2 fitted separately for each watercourse.
5. **S4:** rainfall cross-basis × period indicator (2010–2017 against
   2018–2025).

**Implementation.** The R reference is `dlnm` for the cross-basis and
predictions, with coefficients from a Poisson GLM with one fixed effect per
stratum. That GLM has the same coefficients as the conditional likelihood, and
`gnm`'s faster `eliminate=` fit diverged on one simulated dataset. **Decided
(D1, 2026-09-18): the analysis runs in Python** (`src/case_crossover.py`),
which reproduces the R reference to within 1e-13 on synthetic data
(`results/estimator_validation/`); the R script stays as a standing
cross-check, not the analysis path.

## 8. Uncertainty

Resample calendar year-month blocks jointly across all watercourses: 999
replicates, percentile intervals. Blocks preserve within-month serial
dependence and the dependence between watercourses that share storms. Every
at-risk hour belongs to a block, whereas only onset hours belong to storms,
which is why blocks replace storms as the resampling unit. Storm counts remain
the information floor in §2.

Report the primary estimand's two summaries with intervals. Secondary estimands
receive intervals but no confirmatory tests.

**Undefined median lags (decision D7, 2026-09-18).** A bootstrap draw whose
1–72 cumulative association is not positive has no median lag. Such a draw
counts as possibly any lag in the admissible range: 1–72 hours for a season,
−71 to 71 for the difference. It enters the lower percentile at the range
minimum and the upper percentile at the range maximum. An interval endpoint
at the range bound therefore means the data do not bound the lag on that side,
and it is reported as such, not suppressed. This follows the results of
Gleser and Hwang (1987) and Dufour (1997): for a parameter that is undefined
where another is zero, a valid confidence set must sometimes cover the whole
admissible range. The share of estimable draws is reported with every
median-lag interval.

## 9. Secondary and descriptive analyses

### 9.1 Exposure-response shape

Refit S1 with a natural-spline exposure dimension, knots at the pooled 50th and
90th percentiles of positive hourly rainfall. The analysis describes the
rainfall accumulations at which onset association rises steeply. It does not
propose, calibrate or evaluate a warning trigger.

### 9.2 Fase comparison (conditional)

This analysis is conditional on Waterschap supplying current and historical
Fase thresholds for their exact crisis-plan leading gauges. Where a cohort gauge
is such a leading gauge:

1. locate each Fase threshold on that gauge's within-era discharge distribution
   relative to p99; and
2. refit S1 with Fase-crossing onsets as the outcome, as a sensitivity analysis.

Thresholds are never transferred to gauges they were not defined for.

### 9.3 Temporal stability

S4 describes whether the rainfall lag structure differs between the two halves
of the record. It is a stability description, not a prediction test.

### 9.4 July 2021

Describe observed rainfall, weather, network state and available discharge
around 14–15 July 2021, and locate the event's pre-onset rainfall against the
fitted S1 relationship. Invent no local peak or onset; censored onsets stay
descriptive.

### 9.5 Conditional distance module

If LANUK supplies enough identified, temporally comparable observations and
reconstruction information, the ordered-pair log-distance analysis of draft
0.8 §9 may be considered as a separate, labelled secondary module.
Reconstructed values include those filled from neighbouring gauges. The
decision and available information are recorded before estimating that module;
adding it later remains possible when labelled exploratory.

### 9.6 Two-stage pooling sensitivity

Fit S3 per watercourse and pool the reduced cumulative associations by
multivariate meta-analysis (Gasparrini and Armstrong 2013). With six
watercourses the between-watercourse variance is weakly identified. The
analysis is therefore a sensitivity check on S1, reported with its
heterogeneity estimate. It uses fixed-effect pooling if the random-effects fit
does not converge.

## 10. Pre-committed readings

| result | reading |
| --- | --- |
| warm-season median association lag clearly shorter than cold-season | rainfall association before summer onsets is concentrated closer to onset than before winter onsets |
| seasonal difference interval includes zero | no detectable seasonal difference in lag structure at this grain |
| median-lag interval reaches the admissible range bound | the data do not locate the association lag on that side |
| cumulative rainfall association positive in both seasons | rainfall in the preceding 72 hours is associated with onset in both regimes |
| atmospheric block associated after rainfall adjustment | humidity or pressure change carries association beyond rainfall |
| atmospheric block null after rainfall adjustment | the Eryilmaz-derived signals add no detectable association beyond rainfall |
| watercourse estimates share sign | descriptive consistency across the observed watercourses; shared storms preclude an independent-sign p-value |
| watercourse estimates heterogeneous | the association depends on the watercourse and is not a network-wide regularity |
| lag structure differs between periods | the relationship is not stable over 2010–2025 |
| Fase thresholds lie well above or below p99 | statistically defined and operationally defined high water differ at that gauge |

Null or heterogeneous results do not trigger new lags, bases, thresholds or
model families. No success threshold is imposed.

## 11. Claims ruled out

No claims about:

- flood prediction or causal effects;
- operational warning lead time or FEWS performance;
- recommended alert thresholds or trigger skill;
- damage or statutory flood stage (p99 denotes relative high water);
- monitoring placement or ungauged catchments.

Policy discussion may identify temporal constraints suggested by the observed
lag structure and questions for a separate forecast evaluation. It may not
declare day-ahead action feasible or infeasible, prescribe a warning strategy,
or translate association lags into operational lead time. Contemporary systems
such as DeepWaive are case context, not validation or comparators.

## 12. Outputs and scientific checks

**Required tidy tables:**

- `events.csv`, `storms.csv`, `at_risk_hours.parquet`;
- `crossbasis_estimates.csv`, `primary_estimand.csv`;
- `secondary_estimates.csv`, `watercourse_estimates.csv`, `bootstrap_draws.csv`.

**Required figures:**

- study network and cross-border catchments;
- July 2021 regional trajectory;
- seasonal rainfall lag-response curves with intervals;
- watercourse forest plot of cumulative association;
- network-state event-time profiles.

**Scientific checks before execution:**

- adjacent-hour crossings and onset-only censoring;
- episode and storm single linkage;
- rating-era thresholds and the at-risk definition;
- stratum construction and cross-basis alignment, so that lag 1 means the hour
  before onset;
- block-bootstrap integrity;
- RADOLAN/RADKLIM missing-value and spatial-average handling.

**Synthetic estimator checks**, on data with a known structure:

- a known lag-response is recovered;
- a null produces intervals covering zero;
- a known seasonal difference in median association lag is recovered.

## 13. Lock and amendments

Current state: **unlocked**. Discharge source semantics remain unresolved. A
version record is internal documentation, not formal preregistration.

At lock, record:

- the date and `decisions.md` entry recording the cohort and supported claim scale;
- the modelling implementation choice (§7) and the distance-module decision
  (§9.5);
- the gate-audit path and hash;
- hashes of all analytical inputs;
- the Git commit;
- the analysis-version timestamp;
- any ambiguity resolved before outcome inspection.

After a version is recorded, append changes here with date, reason and whether
signal associations had been viewed. Label outcome-informed analyses exploratory;
never rewrite a prior decision.

## References for the design

- Armstrong, B. G., Gasparrini, A. and Tobias, A. (2014). Conditional Poisson
  models: a flexible alternative to conditional logistic case cross-over
  analysis. *BMC Medical Research Methodology* 14, 122.
- Cameron, A. C., Gelbach, J. B. and Miller, D. L. (2008). Bootstrap-based
  improvements for inference with clustered errors. *Review of Economics and
  Statistics* 90(3), 414–427.
- Gasparrini, A. and Armstrong, B. (2013). Reducing and meta-analysing estimates
  from distributed lag non-linear models. *BMC Medical Research Methodology*
  13, 1.
- Gasparrini, A., Armstrong, B. and Kenward, M. G. (2010). Distributed lag
  non-linear models. *Statistics in Medicine* 29(21), 2224–2234.
- Janes, H., Sheppard, L. and Lumley, T. (2005). Case-crossover analyses of air
  pollution exposure data: referent selection strategies and their
  implications for bias. *Epidemiology* 16(6), 717–726.
- Maclure, M. (1991). The case-crossover design: a method for studying transient
  effects on the risk of acute events. *American Journal of Epidemiology*
  133(2), 144–153.
