---
title: "Pressure, Hydrological State, and Low-Cost CO2 Observations at a Post-Mining Site"
status: "Working draft: stable prose with frozen-result fields"
bibliography: ../chapter-prework/chapter-references.bib
link-citations: true
---

# Introduction

Flood generation is not governed by rainfall alone. Antecedent storage, drainage,
catchment connectivity, and the timing of successive inputs can change the response
to a similar meteorological forcing. These relationships are difficult to observe in
real time, particularly where subsurface pathways have been altered by mining. The
exceptional recent European flood record and the July 2021 disaster underline both
the practical importance of antecedent conditions and the danger of generalizing
from a single event [@Bloeschl2019; @Bloeschl2020; @Kron2022; @Thieken2024]. In
South Limburg, the Geul system and its surroundings also show that flood drivers
must be interpreted at the scale of the local hydrological setting [@Asselman2024].

Former coal districts present an additional observational problem. Mine closure,
mine-water recovery, connected voids, and heterogeneous overburden can reorganize
subsurface pressure and flow pathways over long periods [@Bekendam1995;
@Heitfeld2002; @CaroCuenca2013; @Vervoort2021; @Vervoort2022]. Gas movement through
such systems may respond strongly to atmospheric pressure. A high-frequency indoor
CO2 record can therefore contain a large barometric component even if a hydrological
component is also present [@Wrona2016; @Forde2019; @Wrona2025]. Treating raw CO2 as
a water-level proxy would confound those processes.

This chapter asks a deliberately narrower question:

> After atmospheric-pressure effects are separated, do low-cost CO2 observations
> at the Kerkrade post-mining site contain reproducible information about directly
> measured antecedent hydrological state?

The question separates signal detection from mechanism confirmation. First, the
analysis identifies the part of the CO2 series that is not explained by the locked
barometric specification. Second, three detector families characterize unusual
behavior in that residual. Third, time-aware evaluation asks whether those behaviors
recur outside their fitting windows. Finally, direct groundwater or mine-water
observations determine whether the residual is associated with hydrological state
under prespecified inference, replication, and placebo criteria. Precipitation,
discharge, synthetic anomalies, and cross-site data provide supporting or boundary
evidence; none substitutes for the direct-state test.

The contribution is therefore methodological as well as empirical. It shows how a
gappy, low-cost environmental sensor record can be analyzed without interpolating
long outages, silently changing model families, scoring unobserved periods, or
selecting a favorable conclusion after seeing the result. A supported, site-specific,
coverage-inconclusive, or null outcome is scientifically admissible. Causal language
is not warranted by this observational design.

# Study Context and Predecessor Evidence

The calibration site is a residential building in Kerkrade, in the former South
Limburg coal district near the Dutch-German border. Regional evidence establishes
that mine-water recovery and post-mining deformation are physically relevant to the
setting, but it does not identify the pathway responsible for a particular indoor
CO2 fluctuation [@Voncken2019; @CaroCuenca2013]. The building-scale observations are
accordingly treated as a site record embedded in a complex regional system, not as a
representative measurement of the entire Meuse basin or coalfield.

Two predecessor studies motivate the present design. Viefhues analyzed the Kerkrade
setting around the July 2021 flood using CO2 and available mine- or groundwater
information from approximately August 2020 through September 2021. That study
provided event-specific evidence and a candidate water-state interpretation, but one
site and one exceptional event cannot establish temporal replication
[@Viefhues2022]. Eryilmaz analyzed same-site observations from approximately
September 2020 through May 2021 and compared a model using indoor measurements with
a model using publicly available weather variables [@Eryilmaz2025]. The present
chapter reproduces that procedure as an inherited benchmark, while distinguishing it
from the confirmatory analysis.

The predecessor replication uses random cross-validation only because that choice is
part of the procedure being reproduced. Random folds mix nearby observations and can
overstate performance when a time series is autocorrelated. They are not used as
evidence of future-period performance or cross-site transfer. The chapter's official
evaluation instead preserves temporal order and evaluates later blocks after fitting
on earlier data.

The present empirical record is also distinct from the 2020--2021 predecessor
record. Historical findings motivate mechanisms and specifications; they are not
counted as observations in the current confirmatory sample. This separation prevents
the July 2021 event from being treated simultaneously as the source of the hypothesis
and an independent validation of it.

# Data and Provenance

## Source record

The primary sensor record consists of timestamped Kerkrade IoT observations,
including CO2, indoor pressure, temperature, and relative humidity where available.
Source-native exports and cloud blobs are retained. The normalized analysis grid is
hourly UTC, and every value carries its observed or missing status. The frozen source
table will report provider, native time basis, units, transformations, first and last
observation, observed-hour share, and the hashes recorded by run
`{{FROZEN:manifest.run_id}}` with cutoff `{{FROZEN:manifest.data_cutoff_utc}}`.

Reference meteorology comes from KNMI station 06380 and from the locally cached
weather source used in the predecessor-style analysis. Station 06380 is the primary
external meteorological reference for the post-restoration Kerkrade block. Discharge
and precipitation records provide event and distributed-lag context. RIVM air-quality
sites are retained only for the secondary transfer stress test.

Groundwater or mine-water files are handled under a separate data contract. On
receipt, source-native files are preserved and each series must document its provider,
measurement meaning, unit, vertical datum, orientation, spatial relationship to the
site, quality flags, and known sensor or operational changes. Values are normalized
to a hydrologically oriented level, such that the reported sign has a consistent
physical interpretation. The primary series is selected before outcome modeling:
first a shaft or mine-water level directly connected to the site, otherwise the
nearest physically relevant groundwater series, and within a tier the series with the
greatest overlap with eligible IoT days. Other eligible series are sensitivity tests.

## Time alignment, gaps, and eligible coverage

All source timestamps are converted to UTC before joining. Ambiguous local times are
resolved at ingestion rather than during modeling. Hourly aggregation uses observed
measurements only. Long gaps are never interpolated, and a row is not considered
scored merely because it appears on the complete hourly grid. Contiguous blocks are
defined from required observed inputs; optional covariates may be admitted only when
they preserve at least 90% of required rows overall and within every material block.

Daily direct-state analysis requires at least 18 observed IoT hours. Daily CO2
residuals, water level, and controls are calculated only from those eligible hours.
No interpolation bridges a missing water-state interval. The frozen record must
contain at least 60 paired days distributed across at least two blocks of 15 or more
days before a confirmatory direct-state conclusion is attempted. Failure of that gate
is an evidence result, not a reason to relax it.

The preferred freeze is 8 September 2026. It requires at least 60 post-restoration
days with at least 90% CO2 coverage, at least 90% KNMI coverage over that block,
normalized direct-state data, sufficient paired daily blocks, and a passing software
reliability suite. If a coverage or groundwater gate fails, the only extension is to
6 October 2026. The available record is frozen then even if it supports only a
data-limited or null/boundary chapter.

# Analytical Design

## Pressure decomposition

The first stage estimates a pressure-only baseline for hourly CO2. Pressure level and
prespecified pressure-tendency features represent barometric forcing; the fitted
component is subtracted from observed CO2 to create the pressure-separated residual.
The residual is not described as hydrological. It is simply the portion not assigned
to the locked pressure model. Model coefficients, fit coverage, residual diagnostics,
and the explained-variance summary are retained so that later detector behavior can
be traced to this decomposition.

## Procedural replication

The Eryilmaz replication fits the two inherited logistic-regression configurations:
an indoor-sensor model and a public-weather model. Preprocessing, outcome construction,
and random-fold scoring follow the implemented replication contract. Its purpose is
to establish procedural continuity and reveal how the current record behaves under
the earlier design. Because the folds are not time-separated, their AUROC values are
reported as replication metrics and are excluded from the chapter's principal
out-of-sample claim.

## Detector specifications

Three complementary detector families operate on the pressure-separated record.
SARIMAX represents serial dependence and, when supported after a converged base fit,
daily seasonality [@BoxJenkins2015]. A jointly estimated local-level state-space model
produces one-step innovations while allowing the latent level to evolve
[@Kalman1960]. Isolation Forest supplies a multivariate, nonparametric anomaly score
for the eligible feature frame [@LiuTingZhou2008]. These choices cover parametric
serial structure, adaptive latent state, and distributional isolation rather than
assuming that a single anomaly definition is definitive [@Chandola2009;
@Blazquez2021].

A versioned detector contract is shared by full-record fitting, synthetic injection,
and rolling-origin evaluation. Every fitted model records the requested and actual
family, input features, optimizer diagnostics, convergence, and one of four statuses:
`ok`, `non_converged`, `failed`, or `insufficient_data`. A warning-only or
non-converged fit cannot be labeled `ok`. If an approved fallback is needed, the
artifact names that actual family rather than presenting it as SARIMAX or a Kalman
model.

Each detector writes a native scored indicator. Ensemble agreement is calculated
only where the relevant detectors were all scored. Union-grid rows are labeled
`unscored`, `partial`, or `common`, which prevents an absent score from being treated
as a normal observation. Pairwise and three-way agreement use their explicitly
reported common denominators.

## Validation and time-aware evaluation

Synthetic Gaussian bursts and CutAddPaste-style perturbations test whether each saved
detector family responds to known injected departures. This is an engineering and
sensitivity exercise, not evidence that the injected shapes reproduce a hydrological
event. Synthetic tests are useful precisely because unlabeled anomaly benchmarks can
produce misleading rankings [@WuKeogh2023].

The official rolling-origin design uses 30 days for training followed by seven days
for evaluation. Windows preserve temporal order, enforce coverage rules, and refit the
same saved families. Outputs include the run identifier, data cutoff, fit status,
scored hours, and evaluation summaries. If evaluation is skipped or cannot run, the
pipeline removes or explicitly invalidates prior rolling artifacts. No stale result
may survive as if it belonged to the current snapshot.

## Direct-state confirmatory analysis

The primary direct-state model aggregates the pressure-separated CO2 residual and
water level to eligible UTC days and estimates

$$
r_d = \beta_0 + \beta_1 z(W_d) + \boldsymbol{\gamma}^{\mathsf T}\mathbf{x}_d
      + \alpha_{b(d)} + \epsilon_d,
$$

where $r_d$ is daily residual CO2, $z(W_d)$ is standardized hydrological level,
$\mathbf{x}_d$ contains KNMI temperature, relative humidity, and pressure, and
$\alpha_{b(d)}$ represents contiguous-block fixed effects. Inference for $\beta_1$
uses heteroskedasticity- and autocorrelation-consistent standard errors with maximum
lag 14 and a 28-day moving-block bootstrap.

Support requires all four locked conditions: a two-sided HAC $p$ value below 0.05;
a bootstrap interval excluding zero; the same coefficient sign in at least two usable
blocks; and a seven-day future-water placebo with $|t| < 2$. Lags of 1, 3, 7, and 14
days, changes in water level, and alternative wells form one secondary family with
Benjamini-Hochberg false-discovery-rate control. Those analyses can qualify or bound
the primary interpretation but cannot replace a failed same-day test.

## Proxy, event, and transfer analyses

The precipitation/discharge distributed-lag analysis is a locked boundary test. It
uses antecedent precipitation windows, discharge context, HAC uncertainty,
moving-block uncertainty, block consistency, and a future-rain placebo. The latest
engineering rehearsal returned `NOT SUPPORTED`. That provisional outcome is retained
to prevent selective forgetting, but the reportable result will be rerun under the
unchanged rule on the frozen snapshot.

Event-window summaries distinguish descriptive alignment from confirmatory evidence.
Cross-site transfer is a final, secondary dry run using only genuinely shared
features. Inadequate transfer coverage does not delay the chapter and weak transfer
does not negate a supported site-level direct-state association. Conversely, transfer
performance cannot compensate for missing or failed direct-state evidence.

## Reproducibility and uncertainty

The frozen pipeline records code state, data cutoff, environment versions, executed
commands, input hashes and coverage, output hashes, model family, convergence, and a
single scientific-output hash. Frozen mode rejects dirty or unknown Git state,
changed inputs, mixed snapshot identifiers, failed commands, stale outputs, and
models marked valid without explicit convergence. Two runs on the same immutable
snapshot must reproduce matching hashes and summaries.

Uncertainty is interpreted at several levels: sampling uncertainty in coefficients,
temporal dependence in residuals, block-to-block stability, sensitivity to series and
lag choice, model convergence, and the amount of time actually scored. These checks
do not eliminate structural uncertainty or equifinality in an observational
hydrological system [@Beven2006]. They make the boundary between the data and the
claim visible.

# Results

## Frozen record and pressure decomposition

The frozen Kerkrade grid extends from `{{FROZEN:coverage.start_utc}}` to
`{{FROZEN:coverage.end_utc}}`. CO2 was observed in
`{{FROZEN:coverage.co2_observed_hours}}` of
`{{FROZEN:coverage.grid_hours}}` hourly positions
(`{{FROZEN:coverage.co2_observed_share}}`), with
`{{FROZEN:coverage.material_blocks}}` material blocks. The post-restoration block
contributed `{{FROZEN:coverage.post_restoration_days}}` eligible days, and KNMI 06380
covered `{{FROZEN:coverage.knmi_overlap_share}}` of that block.

The pressure baseline explained `{{FROZEN:pressure.r_squared}}` of observed CO2
variation on `{{FROZEN:pressure.n_hours}}` eligible hours. Its frozen residual
diagnostics were `{{FROZEN:pressure.diagnostic_summary}}`. Figure
`{{FROZEN:figure.pressure_decomposition}}` shows the fitted pressure component and
the residual without connecting outages.

## Predecessor replication and detector behavior

The indoor and public-weather Eryilmaz configurations produced random-fold AUROC
values of `{{FROZEN:replication.indoor_auroc}}` and
`{{FROZEN:replication.weather_auroc}}`, respectively. These values describe the
procedural replication only. Their uncertainty and fold construction are reported in
Table `{{FROZEN:table.replication}}`.

The selected SARIMAX family was `{{FROZEN:sarimax.family}}` with fit status
`{{FROZEN:sarimax.fit_status}}`; the selected local-level family was
`{{FROZEN:kalman.family}}` with fit status `{{FROZEN:kalman.fit_status}}`.
Isolation Forest used `{{FROZEN:iforest.selected_feature_count}}` admitted features.
The three detectors scored `{{FROZEN:sarimax.scored_hours}}`,
`{{FROZEN:kalman.scored_hours}}`, and `{{FROZEN:iforest.scored_hours}}` hours,
respectively. Common coverage was `{{FROZEN:ensemble.common_hours}}` hours, on which
the distribution of zero-, one-, two-, and three-detector agreement was
`{{FROZEN:ensemble.agreement_summary}}`.

Synthetic-injection recovery was `{{FROZEN:synthetic.summary}}`. Across
`{{FROZEN:rolling.usable_windows}}` usable rolling-origin windows, fit-status and
out-of-sample summaries were `{{FROZEN:rolling.summary}}`. Hours outside detector
coverage are shown as unscored rather than normal in Figure
`{{FROZEN:figure.detector_timeline}}`.

## Direct hydrological state

The locked hierarchy selected `{{FROZEN:direct.primary_series_id}}` from
`{{FROZEN:direct.provider}}`, a tier `{{FROZEN:direct.tier}}` series measured in
`{{FROZEN:direct.unit}}` relative to `{{FROZEN:direct.datum}}`. After daily coverage
filtering, the primary model contained `{{FROZEN:direct.paired_days}}` paired days in
`{{FROZEN:direct.usable_blocks}}` usable blocks.

The standardized same-day level coefficient was `{{FROZEN:direct.beta}}`, with HAC
standard error `{{FROZEN:direct.hac_se}}`, $p = {{FROZEN:direct.hac_p}}$, and 28-day
moving-block interval `{{FROZEN:direct.bootstrap_interval}}`. Block signs were
`{{FROZEN:direct.block_signs}}`; the future-water placebo gave
$t = {{FROZEN:direct.placebo_t}}$. The prespecified primary outcome was
`{{FROZEN:direct.outcome}}`. FDR-controlled sensitivities are reported separately in
Table `{{FROZEN:table.direct_sensitivities}}`.

## Boundary and secondary evidence

Under the unchanged five-part rule, the frozen distributed-lag result was
`{{FROZEN:distributed_lag.outcome}}`, with the primary and placebo summaries shown in
Table `{{FROZEN:table.distributed_lag}}`. The current pre-freeze rehearsal is `NOT
SUPPORTED`; it is not substituted for this frozen field.

The transfer lane was `{{FROZEN:transfer.status}}`. If run, it supplied
`{{FROZEN:transfer.shared_coverage}}` shared-feature coverage and the secondary
summary `{{FROZEN:transfer.summary}}`. If omitted for insufficient coverage, that
omission is reported without changing the core chapter outcome.

# Discussion

The final interpretation is selected from the four paragraphs below only after the
frozen direct-state checks have run. The retained paragraph must agree with the
machine-readable primary outcome; the other three branches are deleted. Detector
agreement, precipitation/discharge alignment, and transfer can refine the scope of
the interpretation, but they do not choose the primary branch.

<!-- CLAIM_BRANCH:supported_site_level -->
### Supported site-level hydrological signal

The direct-state association passed the locked HAC, moving-block, block-sign, and
future-water placebo criteria. The result therefore supports a reproducible
site-level hydrological signal in pressure-separated Kerkrade CO2 over the observed
period. It does not establish a unique subsurface pathway, generalize the relationship
to other sites, or turn the sensor into a flood-warning instrument.

<!-- CLAIM_BRANCH:site_specific -->
### Site-specific direct-state signal with weak proxy or transfer evidence

The direct-state analysis supported an association at Kerkrade, while proxy,
replication, or transfer evidence was weak or inconsistent. The appropriate claim is
site-specific: the local residual carried information about the measured state, but
the present evidence does not establish portability or justify substitution of
rainfall, discharge, or an external-site model for the direct measurement.

<!-- CLAIM_BRANCH:coverage_inconclusive -->
### Inconclusive because of coverage

The available record did not satisfy the paired-day, block-replication, or scoring
coverage needed for the locked direct-state decision. The chapter therefore cannot
distinguish a small or intermittent association from no association. Pressure
separation and the reproducible workflow remain established outputs, while mechanism
confirmation is deferred rather than inferred from proxies.

<!-- CLAIM_BRANCH:null_boundary -->
### Null or boundary result

The frozen direct-state result failed one or more prespecified association,
replication, uncertainty, or placebo criteria despite adequate coverage. The analysis
therefore does not support an antecedent hydrological signal in the pressure-separated
CO2 record under this specification. This boundary result narrows the interpretation
of earlier event-specific and proxy findings and documents how barometric structure
can create apparently meaningful lag patterns.

Across all branches, the distinction between detection and explanation remains
central. An anomaly is a departure relative to a fitted reference, not a labeled
hydrological event. Agreement among model families is more credible when computed on
common coverage, but correlated detectors are not independent replications.
Similarly, a stable regression association is evidence about the measured site and
period, not proof of the physical route by which water state and indoor gas are
connected.

# Limitations

The principal limitation is the fragmented single-site record. Long outages reduce
both statistical power and the variety of hydrometeorological states available for
evaluation. The block rules protect against joining unrelated fragments, but they
cannot recreate missing seasons or events. The post-restoration record may also
differ from earlier periods because of sensor, building, or operational changes.

CO2 is measured indoors and can respond to ventilation, occupancy, sensor drift,
temperature, and processes not represented in the available covariates. Pressure
decomposition reduces a major known confounder without guaranteeing that its
functional form is complete. KNMI station 06380 is an external reference rather than
an on-site measurement, and daily aggregation trades temporal detail for sufficient
paired direct-state coverage.

The direct water series may not observe the precise hydraulic compartment connected
to the building. The locked selection hierarchy and alternative-series sensitivity
make that uncertainty explicit, but spatial relevance still depends on provider
metadata and hydrogeological interpretation. Block fixed effects control stable
level differences; they do not absorb all time-varying operational changes.

Anomaly evaluation is constrained by the absence of independently adjudicated event
labels. Synthetic injections test software behavior against controlled disturbances,
not environmental realism. Random-fold predecessor scores are vulnerable to temporal
leakage, while rolling-origin estimates may be imprecise when few windows qualify.
The transfer lane uses different instruments and contexts and is therefore a stress
test rather than external validation.

Finally, the study is observational. HAC errors, moving-block bootstrap intervals,
placebos, and FDR control address specific inferential risks but do not identify a
causal mechanism. The results should guide better monitoring and hypothesis design,
not operational flood decisions without independent prospective validation.

# Conclusion

This chapter provides a gap-honest, snapshot-verifiable test of whether low-cost CO2
observations contain information about directly measured hydrological state after
barometric effects are separated. The final frozen record comprised
`{{FROZEN:conclusion.coverage_summary}}`; the direct-state decision was
`{{FROZEN:direct.outcome}}`. Accordingly, the retained discussion branch supports the
following bounded conclusion: `{{FROZEN:conclusion.claim}}`.

Whatever the outcome, the analysis establishes a reusable distinction between raw
sensor correlation, pressure-separated anomaly detection, time-aware recurrence, and
direct-state confirmation. That distinction is necessary for a credible result from
a sparse environmental IoT record and makes a null or coverage-limited finding as
traceable as a supported site-level association.
