# DISE-inspired direction: research-design audit

16 November 2026. Audited commit `7a8352e`, design, preparation, benchmark code,
source support and primary literature. This audit changes no model, scientific
configuration, source data or completed result. No fitting launched. Brian
retains all dissertation prose writing.

## Judgment

**Keep the direction.** One pooled landscape-conditioned correction has direct
hydrological precedent and a testable role for AlphaEarth. The four feature
sets, conventional/global references and temporal/spatial tests can answer a
bounded question. This is considerably better aligned to the encoder's role
than treating annual catchment vectors as hourly storm observations.

The principal weaknesses are target/selection alignment, an unnecessary calendar
exclusion and an incompletely specified scoring population. These are correctable
within the same study. Several regional acquisition/evaluation components are
explicitly unfinished; their absence from a local timing benchmark is not a
failed research test. Thirty software tests do not establish scientific validity.

## Findings, ordered by research consequence

### 1. High-water emphasis and model selection are not aligned — high priority

The stated primary question concerns high water. Fitting minimizes squared
log1p residual, early stopping defaults to RMSE on that transformed residual,
and candidate selection averages **all-day** native specific-discharge MAE.
These are three different objectives. Log-space fitting gives proportionally
more attention to low/moderate-flow discrepancies than untransformed fitting;
ordinary days dominate the validation sample. A model can be the correct
selection under that rule and still fail the high-water question.

Evidence: `src/dise.py:95` and
`scripts/263_benchmark_dise_fold.py:129`. This is not proof that the model is
incorrectly optimized in general, nor that it caused a particular result.
Evaluating extremes of an all-flow-trained model is legitimate if that is the
explicit research question. It is a poor unexamined default for a high-water-
centered capability test.

Recommendation: decide the intended estimand now. For the accepted high-water
question, use one declared high-water-aware validation/early-stopping criterion,
with thresholds derived only from the relevant training/validation source
rivers and no held outer-river labels. Retain the article-faithful log-residual
form as a documented reference; use one targeted loss/selection sensitivity
rather than a new loss-function tournament. Keep all ordinary-flow results to
show the trade-off. Do not select the criterion by which gives AlphaEarth a win.

[Frame et al. (2022)](https://doi.org/10.5194/hess-26-3377-2022) supports explicit
extreme-event evaluation with basin-normalized discharge errors. Its LSTM
results do not establish that a particular loss guarantees an encoder benefit.

### 2. The seven-day calendar buffer removes valid research observations — high priority

`src/dise.py:86` starts every validation/test year on January 8 because model/
weather lag histories would otherwise cross the partition. Past predictor
history crossing January 1 is **not itself label leakage**: earlier weather and
modelled discharge are legitimately known historical inputs to reconstruction.
The current target is one day's discharge, not a multi-day future target window
overlapping training labels.

Read-only census check: the five 2021–2025 test years would lose **240 otherwise
valid gauge-days**, including **18 days above their prior-history daily p99**:

| Year | Valid gauge-days excluded | High-water gauge-days excluded |
| --- | --- | --- |
| 2021 | 48 | 0 |
| 2022 | 48 | 2 |
| 2023 | 47 | 0 |
| 2024 | 48 | 7 |
| 2025 | 49 | 9 |

Recommendation: retain valid January 1–7 observations with their causal prior
histories. Purge overlapping **labels** when they actually occur. Distinguish a
normal chronological replay from a deliberately independent-storm test: the
latter can group/remove boundary-spanning storms under a stated rule, but must
not become an automatic blanket removal from the main retrospective census.
Keep regional storm dependence in evaluation/resampling. This removes a
restriction; it requires no new data or model.

### 3. Daily reconstruction is valid, but it is not flood-peak reconstruction — scope clarification

The change from next-24h assessment to daily reconstruction is already disclosed
and accepted. DISE is an appropriate daily reconstruction precedent. However,
the method's daily mean target smooths precisely the fast responses important
in these small tributaries. Improving daily mean discharge must not be described
as recovering peak stage, flood onset or useful warning timing.

Diagnostic using complete observed days in 2021–2025: on each gauge's top 1% of
days by maximum hourly mean, median daily-mean/maximum-hourly-mean ratios range
from **0.36 to 0.63**. This is a timescale description, not a model-performance
finding; neither measure is an instantaneous peak. It shows why the distinction
is consequential rather than just terminology.

Recommendation: keep the daily outcome; describe the primary question as
improving **daily estimates of high river flow** where target-river calibration
is unavailable. Retain hourly/documented-flood hydrographs as context showing
what daily estimates cannot recover. Do not compare predicted daily means to
observed hourly peaks as if that were a valid peak-prediction score. No extra
hourly model is required by this audit.

### 4. Primary population and uncertainty are not yet executable — high priority

`balanced_mae()` averages the groups/gauges present in its input. After
high-water filtering, some sites or years may have no eligible rows. Its current
interface neither receives a declared population nor reports that population
change. A two-group example yields MAE 5.5; removing the worse group's only row
silently yields 1.0. This demonstrates a scorer limitation, **not** an observed
unfair contrast in the completed local benchmark, whose arms share their rows.

The benchmark's 21 high-water gauge-days are repeated observations across three
nested Wurm gauges and a small number of storms, not 21 independent floods.
The design recognizes river/storm/year dependence, but full resampling and
coverage-aware contrast implementation remains pending.

Recommendation: declare the primary estimand and fixed river/site population
over the pooled test period. Save every arm's shared row eligibility and group
weights. Mark genuinely undefined subgroup/draw estimates as undefined with
counts, rather than silently change populations or fill absence with zero.
Show which rivers/years contribute to each conditional high-water estimate.
Use the same resampling blocks across arms and separate local seven-gauge
summaries from the three external river systems. Bootstrap count is not sample
size or proof of independent replication.

Save evaluator thresholds and the high-water flag in the score artifacts: the
benchmark computes them **after** writing `predictions.parquet`, and the numeric
thresholds are not currently saved. The source/code hashes allow reconstruction,
but the production readout should make its exact support directly inspectable.

### 5. Stronger baselines are planned, not yet demonstrated — medium priority

H+A has seven conventional variables: area, elevation, slope, three fractional
cover variables and surface field capacity. This is a reasonable initial
landscape comparator, not a complete conventional hydrological description.
It lacks explicit climate normals and regulation information; surface field
capacity is not root-zone storage. AlphaEarth can encode spatial/climatic
context, so a gain over this arm would not by itself establish a novel physical
mechanism or superiority to every conventional descriptor set.

Recommendation: use low-cost existing data to add coordinates and strictly
past-forcing climatic summaries consistently, and resolve regulation where
documented. Report residual descriptor gaps rather than demand a comprehensive
new field campaign. Implement the already planned local calibration reference
and donor-FDC transfer; do not compare only to raw GEOGLOWS. Local calibration
has extra target labels and must be labelled accordingly.

[SABER](https://doi.org/10.3390/hydrology9070113) already transfers bias correction
to ungauged reaches. The contribution cannot be 'we corrected a global product'
alone. The primary H+A+E versus H+A contrast remains sound; interpret it as the
incremental value of the representation under this specified workflow, not a
causal identification of soil or land-use effects.

### 6. Regional independence and source quality are preparation tasks — high priority before regional inference

286 donors and 49 external candidates are **metadata candidates**, not approved
training/test observations. The code uses polygon overlap, 1% provisional overlap
and exact mainstem names to build the ledger. That is suitable screening, not
a topology proof. Some of the 52 boundary cases can be ordinary delineation
slivers; automatically excluding them would introduce another unjustified rule.

Recommendation: complete the already planned reach/area and upstream-section
checks, source-clock/quality interpretation and duplicate/nested-gauge grouping.
Exclude actual shared contributing areas or directly upstream/downstream gauge
sections across a holdout, rather than every river sharing a distant downstream
outlet. The latter interpretation could unnecessarily collapse much of the
Rhine region into a single group. Verify the full reserved Ahr/Erft/Sieg networks,
not just polygons up to available named gauges. Keep mapping/quality decisions
independent of prediction errors and retain their ledger.

The local benchmark passes outer Wurm withholding. Source qualifications remain
consequential: Herzogenrath 1/Randerath have 365 finite daily values in 2021 but
only 180 days satisfy the inherited strict-clean flag. That does **not** mean
the remaining 185 days are all bad. It means finite daily labels cannot be
silently called fully verified peaks/volumes. An onset-validity decision from
earlier work is not automatically a daily-flow-validity decision. Preserve
provider uncertainty and implement the declared clean-verification sensitivity;
do not discard the German cohort wholesale or require a new provider response.

### 7. Water, weather and encoder use are largely appropriate — retain with qualifications

Positive checks:

- One shared learner can use catchment descriptors to condition discharge
  correction; temporal forcings supply event dynamics. This is directly supported
  by DISE and [Liu et al. (2026)](https://doi.org/10.1029/2026GL122814).
- All 64 AlphaEarth axes, fixed 2017 descriptors, 2017 conventional land cover,
  gauge-specific full-catchment aggregation, common model/observed reference
  area conversion and no target Q covariates are appropriate choices.
- Every outer Wurm gauge stays out of fitting and tuning. Inner validation labels
  legitimately choose hyperparameters/early stopping; that is not outer-test
  leakage.
- Full ordinary-day training, true zero handling, saved source identities, equal
  tuning budgets and seed reuse are appropriate. There is no reason to return
  to ten encoders or fine-tune a foundation model for this question.
- Google documents the daily accumulated precipitation/radiation as totals for
  the represented day and non-flow bands as day means. The current `_sum` usage
  is consistent with that convention; a delayed API source timestamp is not a
  reason to shift the daily precipitation a second time.

Qualifications: ERA5-Land forcing shares model lineage with the global discharge
product and is not an independent rainfall observation. Its ~11-km grid is coarse
for the smallest catchments; interpret forcing error versus landscape error
accordingly. Use the already held RADOLAN comparison as a controlled local
sensitivity if needed. The benchmark currently supplies temperature/dewpoint/
pressure and wind components directly rather than the derived humidity/wind-speed
features described in the plan; lock one common recipe across all future sites.
Unit-length pixel embeddings become non-unit-length catchment means; that is
legitimate aggregation, not an automatic normalization bug. Do not normalize
away their magnitude or add summary statistics without a stated question.

### 8. Policy value and novelty need an evidence chain, not another model — framing

The practical use tested here is retrospective reconstruction at locations
without target calibration, with implications for filling historical knowledge
gaps and evaluating global hydrological information. Same-day reanalysis is
not a feed available during that day's flood. Do not promise direct operational
FEWS improvement, avoided impacts or an optimal monitoring budget from these
experiments.

Recommendation: frame findings around the conditions under which an agency can
trust, correct or reject a globally available daily high-flow estimate: error
magnitude, severe underestimation, required donor/local information, unresolved
regulation and mapping limitations, cost and transfer. Link this to flood-risk
information capacity and DRR. Include event examples and failures. This supplies
a policy-relevant interpretation within the existing analysis; no interviews,
new welfare model or operational dashboard is required.

## Size and execution recommendation

This is one plausible chapter if it remains one learner/representation, four
feature sets, one declared high-water objective and a fixed regional transfer
domain. The seven local gauges are detailed case studies; the regional pool
supplies spatial learning support. Hundreds of nested gauges do not become
hundreds of independent rivers.

Proceed with regional preparation while correcting selection/scoring definitions
and removing the unnecessary calendar buffer. These changes require no new EO
campaign, model family or provider request. Preserve the completed benchmark as
engineering/exploratory evidence. A fresh versioned benchmark after corrections
can precede the full fits; no positive-result gate is introduced.

## Evidence and access

[Machine-readable diagnostics](limburg-dise-research-design-audit-2026-11-16.json)
record code/data hashes, calendar counts, timescale checks and label-quality
counts. Read-only diagnostics do not change fitted results.

Primary sources rechecked: [DISE preprint](https://doi.org/10.5194/egusphere-2026-1834),
[Liu et al.](https://doi.org/10.1029/2026GL122814),
[SABER](https://doi.org/10.3390/hydrology9070113),
[Frame et al.](https://doi.org/10.5194/hess-26-3377-2022),
[AlphaEarth catalog](https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_SATELLITE_EMBEDDING_V1_ANNUAL),
[ERA5-Land daily catalog](https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_LAND_DAILY_AGGR),
[CAMELS-DE-1h preprint](https://doi.org/10.5194/essd-2026-289),
[XGBoost estimator documentation](https://github.com/dmlc/xgboost/blob/master/doc/python/sklearn_estimator.rst).
No exact DISE replication, new systematic literature search or new performance
experiment is claimed.
