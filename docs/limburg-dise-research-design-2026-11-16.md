# DISE adaptation: research-design review

16 November 2026. Proposed internal research aid, not dissertation prose or an
executed protocol. No fitting, bulk acquisition, cloud provisioning or new
encoder extraction was launched in this review. The completed GEOGLOWS v2
experiment and its negative incremental-encoder results remain intact.

## Recommendation and the substantive change

Pursue one landscape-conditioned **daily discharge reconstruction** comparison,
using AlphaEarth and a pooled XGBoost correction of GEOGLOWS. This is a better
documented role for the satellite representation than a new per-gauge correction
of event analogues. It is a defensible candidate, not evidence of a future gain.

This changes the outcome from the previous next-24h trajectory experiment.
Contemporaneous model discharge and same-day weather are legitimate inputs for
reconstruction; they are not legitimate inputs for an earlier-issued forecast.
Do not label this an unchanged rerun, an operational fallback, or a forecast.
Retain the three-stage logic: trusted local observations, the same rivers with
global modelled information, then independently observed other European rivers.

Stage 1 becomes the reference and measurement audit, rather than a model that
uses today's observed discharge to predict that same observed discharge. That
would be target leakage. The earlier observed-input forecasting results remain
a separate completed experiment, not a directly comparable reconstruction arm.

## Research questions and practical contribution

Main question: **Can satellite-derived catchment information make a global
discharge model more accurate during high water, including on other rivers?**

1. At the held NL/DE gauges, how do GEOGLOWS errors vary with flow magnitude,
   season, catchment and model-to-gauge spatial correspondence?
2. Does a shared correction using AlphaEarth improve on the same correction
   using weather, model discharge and conventional catchment descriptors?
3. Does any improvement or identified failure transfer to other European rivers
   without using those rivers' observed discharge to calibrate the correction?

Policy relevance: assess when globally consistent satellite information can
supplement local modelling and monitoring capacity, and when gauge investment
or local calibration still matters. Report prerequisites, cost, severe errors
and transfer limitations. This study does not quantify warning lead time,
operator benefit, inundation, avoided losses or reduced disaster mortality.

## What the source study actually supports

[Lin et al., DISE](https://doi.org/10.5194/egusphere-2026-1834), an EGUsphere
preprint, uses a global discharge product, daily meteorological inputs and
AlphaEarth summaries in a log-residual XGBoost correction. Its leave-one-station-
out experiment uses 41 Yangtze gauges and **2017 only**, including training and
tuning. The manuscript explicitly limits its experiment to spatial transfer.
Its traditional-descriptor control uses selected land-cover fractions, not a
comprehensive set of all relevant hydrological attributes. Do not treat its
reported improvement as proof of temporal robustness or extreme-event skill.

The PDF was inspected in full, including methods, Table 1, Appendix A and code
availability. The listed repository,
`https://github.com/LePapilllon/residual_learning`, returned **404** on this
review; the author's GitHub profile is available but does not expose that
repository. The previous conversational statement that its code was available
was too confident. A methods-based independent adaptation is possible; exact
code replication remains unavailable. No email was sent.

Preserve: one pooled residual learner, frozen satellite representation,
meteorological controls, mean embedding aggregation and held-location evaluation.
Change explicitly: GEOGLOWS instead of GRADES-hydroDL; European small catchments;
multi-year chronological testing; stricter river-group withholding; richer
conventional controls; high-water and observation-quality evaluation.

Do not add GRADES-hydroDL as a second global product simply to resemble DISE.

## Stage 1 — trusted NL/DE reference and source comparison

Population: seven previously mapped tributary gauges. Eys remains excluded from
both predictors and targets because no independent model reach was found. Keep
its original observations. The Meuse sites remain available context records;
they are not new training/target basins here and cannot be treated as upstream
controls for every tributary. This particular reconstruction uses each target's
own GEOGLOWS history, not an all-gauge observed network.

Work:

- Preserve fixed UTC+1 handling for René's files, LANUK source qualifications,
  rating-era and measurement decisions. Retain true zero discharge.
- Build paired daily observations and GEOGLOWS at the checked gauge/reach pairs.
  Use UTC days (00:00 to next 00:00): hourly means indexed at hour end enter a
  day for `day_start < timestamp <= next_day_start`. Require all 24 valid hourly
  means for a daily verification value; do not fill outcome gaps. Save support
  and rejected-day counts. Do not confuse raw instantaneous observations with
  hourly means where providers differ.
- Report daily source errors for 2010–2025 wherever valid; label 2018–2025 as
  the primary AlphaEarth-comparison period. Earlier years support source
  characterization, not additional samples in an unmatched encoder comparison.
- Describe errors versus model/gauge catchment mismatch and provider quality.
  Brommelen's held/model polygon mismatch is a known issue, not a reason for
  outcome-selected exclusion. Retain a predeclared geometry-quality sensitivity.
- Retain hourly records and documented floods for hydrograph interpretation.
  Daily reconstruction cannot establish sub-daily peak recovery.

Deliverables: per-gauge daily support/measurement table, source-error atlas,
time-alignment examples and immutable split/cohort register. Observations are
the verification reference, not error-free physical truth.

## Stage 2 — controlled pooled correction on the same rivers

### Inputs and spatial support

Use the existing area-aggregated **64-dimensional AlphaEarth means**. All nine
held catchments have 2017–2024 rows; seven are relevant here. Verify the selected
metric-grid export's coverage and original geometry receipts before ingestion.
Keep all 64 dimensions initially; no outcome-selected components or encoder
fine-tuning. Fit any imputation or dimensionality handling on training only.

Primary spatial support is the **full upstream gauge catchment**, appropriate
to discharge at that section. DISE's incremental reach subcatchments belong to
its own network model; do not blindly substitute them for our gauge catchments.
Use model/gauge area ratio and overlap in all learned arms as explicit common
mapping descriptors. Document this departure from DISE. A model-polygon versus
gauge-polygon aggregation sensitivity is optional, not a prerequisite.

Primary embedding vintage: fixed **2017 descriptors**, applied to 2018–2025.
This cleanly tests a landscape descriptor without using imagery from the outcome
year. One supporting comparison may use the latest completed prior calendar
year. Neither option recreates the historical release/pretraining date of the
2025 foundation model; this is retrospective information-content research.
Do not use same-year annual embeddings or a 2017–2024 mean to assert causal
availability before earlier test events. No empirical release-latency claim is
made for the prior-year sensitivity.

Weather must be averaged separately over **each gauge's polygon**. The held
watercourse-level RADOLAN/ERA5 tables cannot be assumed to represent all three
different Wurm gauge catchments. Use one common ERA5-Land recipe for the main
local and external comparisons: precipitation, air temperature, dew point,
surface pressure, wind components and downward shortwave/longwave radiation;
derive humidity consistently from temperature/dew point/pressure, and wind
speed consistently from the components. This approximates DISE's forcing
coverage without importing a China-specific product. Same-day summaries and
lags 1–7 days are permitted for reconstruction. Accumulations, units and daily
boundaries require explicit checks. Held RADOLAN is a local rainfall-product
sensitivity, not an extra advantage given only to the embedding arm.

Conventional landscape controls: log drainage area, elevation, slope, forest,
cropland and urban fractions, a soil-storage/permeability descriptor, and a
documented regulation indicator where available. Use common definitions and
sources, not name-matched columns from incompatible datasets. RiverATLAS and
held EStreams attributes are leads; their section correspondence and coverage
remain to be checked, especially at the German gauges. Do not include observed
flow signatures or full-record climate summaries that reveal the held target.
Missing regulation information is unknown, not proof of no regulation.

The completed soil/snow acquisition can support one equal-input physical-state
sensitivity after catchment aggregation. It is not a new mandatory acquisition,
nor evidence that existing derived tables already contain correct gauge-level
states. Do not launch another physical-variable tournament.

### One estimator and four controlled feature sets

Let `q` be specific discharge in mm/day, using the gauge's reference drainage
area for **both** observed and modelled Q. Do not divide the two sources by
different areas and thereby silently remove model/gauge mismatch. Model the
dimensionless residual `log1p(q_obs / q0) - log1p(q_model / q0)`, with
`q0 = 1 mm/day`. Transform back and floor only negative reconstructed discharge
at zero; retain counts. This is an explicit zero-safe adaptation of DISE's
log-space residual, not a claim of exact numerical equivalence to its code.
Native m3/s and per-site results must also be retained.

Log-space fitting and inverse transformation do not automatically yield an
unbiased arithmetic-mean discharge. Describe the point estimator accordingly
and inspect high-flow volume bias explicitly. Any retransformation adjustment
must be estimated on training/validation data identically across arms, never
fitted to test flood magnitudes. Do not repair extreme outputs after seeing a
held flood; retain them as failure cases with the fitted transformation.

| Arm | Predictors | Attribution |
| --- | --- | --- |
| Raw | Unchanged GEOGLOWS | Does any postprocessing help? |
| H | GEOGLOWS current/1–7-day lags, common weather, seasonal terms, common mapping descriptors | Dynamic correction |
| H+A | H plus conventional landscape attributes | Strong conventional spatial comparator |
| H+E | H plus AlphaEarth | Learned descriptors as a substitute |
| H+A+E | H+A plus AlphaEarth | **Primary incremental encoder contrast against H+A** |

Fit one pooled XGBoost head per arm/split, not seven separate heads. Identical
rows, sample weighting, missingness rules, tuning budget and target transform
apply to all learned arms. Weight each training river group equally, then each
gauge within group, then valid days; save weights. Use all eligible days, not
only high water or a sampled storm subset. High-water outcomes do not select
training examples or hyperparameters. Never provide current or lagged local
observed Q as predictors in a supposedly ungauged correction.

Add a training-only monthly flow-duration calibration as a **locally calibrated
reference** in temporal testing. It has local-label access and cannot be called
a fair zero-local-label comparator in spatial/external tests. Include a simple
donor-catchment calibration transfer in those tests, selecting the donor with
conventional descriptors only and fitting transformations from donor training
records. Call this donor-FDC transfer, not a reproduced SABER implementation.
Report raw GEOGLOWS and H+A as the principal zero-local-label comparators.

### Splits, fitting and uncertainty

- **Regional training support is a necessary design addition.** Seven local
  gauges on at most five river groups are too little spatial diversity to make
  strong claims about learning 64-dimensional catchment effects. Longer local
  time series do not solve that problem. Acquire a separate donor training pool
  from CAMELS-DE-1h: all metadata-eligible 25–1,000 km2 catchments with centroids
  in 5.5–9 degrees E, 49–52.5 degrees N, excluding the local targets' connected
  networks and the reserved Ahr/Erft/Sieg external networks. These bounds define
  a western German small/medium-catchment domain before inspecting prediction
  errors. Include regulated catchments with their flags, not only clean-looking
  examples. Apply completeness/measurement and GEOGLOWS mapping criteria to all
  candidates, retain every rejection and freeze the eligible census. The exact
  count is pending metadata inventory; there is no arbitrary minimum-count or
  favourable-performance gate. If actual independent support remains small,
  report that limitation and revise the claim before expensive tuning.
- The main pooled learner uses historical local data permitted by the outer
  split plus these regional donor observations; Stage 2 test outcomes remain
  the same seven NL/DE gauges. Donor labels are training information, not a
  supposedly zero-gauge training system. 'No local labels' refers to the held
  target river. External Stage 3 observations remain wholly outside this pool.
- Temporal test years: **2021–2025**, separately. Train on 2018 through Y−2;
  tune on Y−1; test on Y. This keeps July 2021 in evaluation. Purge 7 days at
  boundaries and any regional storm spanning a split. Later folds may contain
  earlier test years once those years are historical; report them as rolling
  evaluation, not five independent untouched trials.
- Spatial test: the same chronology plus leave-one-**river group**-out. At
  minimum all three Wurm gauges leave together. Build and save a topology/
  polygon-overlap grouping before fitting; merge additional connected/overlapping
  groups when required. Five named watercourses are an upper bound, not five
  certified independent basins. A transboundary Wurm result is not an NL-versus-
  DE causal comparison.
- Spatial tuning: four topology-preserving inner river-group folds within the
  remaining local and regional donor training population, using only the earlier
  validation year. Freeze the fold assignment before fitting; if fewer than four
  independent groups exist, use the actual groups and report that fact. No target group's observations may tune,
  normalize, early-stop, calibrate or choose model configuration. Select by
  river-balanced validation MAE, not the later test high-water subset.
- Withholding applies to this study's correction learner. Audit and report
  global-model calibration and foundation-model pretraining lineage separately;
  do not imply the entire upstream modelling chain is known to have never
  encountered information from a test region.
- Start with four small, regularized hyperparameter candidates, identical across
  feature sets, and a fixed maximum tree count with validation early stopping.
  Document exact candidates in the executable configuration. Tune once per
  arm/outer split, then reuse that configuration across three final seeds.
  Retain all failed fits and the raw/reference predictions; no favourable-run
  rerolls. Use an equal-budget expanded tuning sensitivity only if first-fit
  diagnostics demonstrate underfitting or unresolved search-boundary selection.
- Primary outcome: river-balanced high-water daily MAE, per-site and in mm/day.
  Define high-water days with each target's **training-period observed daily
  p99**, frozen before that test year. In pseudo-ungauged testing that threshold
  is held by the evaluator only, never supplied to the predictor or tuning.
  Report sensitivity to the existing fixed hourly-event definition separately;
  daily p99 and hourly p99 events are not interchangeable.
- Also report all-day MAE/RMSE, NSE/KGE/bias, top-tail flow-volume bias, event
  maximum daily-flow error, errors on rising versus falling limbs, coverage and
  documented floods. Undefined metrics remain undefined. Daily peak-day errors
  are day-scale; do not report them as hourly warning timing skill.
- Make paired comparisons on the same verification rows and retain a full-source
  coverage table. Shared year/storm block resampling preserves all gauges in a
  regional storm. Report river-specific/year-specific paired effects and
  leave-one-river influence. With only five test years and at most five river
  groups, a nominal 999 bootstrap draws do not create strong independent
  replication: intervals are exploratory and depend on these blocks. Do not
  bootstrap daily rows independently or hide undefined draws.
- Review every held documented flood plus the largest helped and harmed storms
  selected by a recorded symmetric rule. Check whether gains concern volume,
  timing or ordinary seasonal bias. Keep negative cases in the reported census.

## Stage 3 — a separate external transfer test

Preferred source: **CAMELS-DE-1h**, hourly 2001–2024, with boundaries and
hydrometry/landscape metadata. Its data paper is under review, but the dataset
has a documented DOI. The older daily CAMELS-DE v1.1 ends in **2020**, so it is
not the preferred route for our 2021 onward test period. Do not download the
wrong version because both products are called CAMELS-DE.

Define the external geography before looking at discharge errors: candidate
gauges in the **Ahr, Erft and Sieg** basins, outside the local study's upstream/
downstream training network. Retain all eligible mapped gauges in that bounded
geography rather than select favourable rivers or an arbitrary performance
sample. Exact count is unknown until the metadata/topology inventory. Preserve
duplicates, nesting and rejected model mappings in an inclusion ledger; group
nested external gauges for summaries rather than count them as independent.

Download observed Q, boundaries and necessary quality/attribute metadata;
retrieve matching GEOGLOWS series and the identical weather/AlphaEarth recipe.
Use 2021–2024 and the appropriate local model trained before each external test
year. External Q is **evaluation-only**: no external-label retraining, tuning,
normalization or calibration in the primary transfer test. Model inputs still
contain external GEOGLOWS/weather/landscape descriptors. Report distance from
the training descriptor support and physical differences; do not remove novel
landscapes just because predictions are poor. Publisher peak-quality cautions
follow the observations into the evaluation.

An alternative acquisition route is **CAMELS-GB v2**, which has daily/hourly
records to September/October 2022, per-file access, quality attributes and an
Open Government Licence. It would support a **2021–2022** external comparison,
not the same 2021–2024/2025 test years. Its published daily/hydrological-day
conventions need alignment; selected hourly records can be aggregated to the
same UTC day. Do not add Germany and Britain simultaneously as two new arms.

Stage 3 can evaluate a limitation or lack of benefit; a positive Stage 2 result
is not a gate. Its scope and source must be fixed before examining external
prediction errors. If the selected external observations have been inspected
for other work, disclose that rather than call them pristine confirmation.

## What must be pulled versus reused

| Item | Held now | Acquisition/preparation remaining |
| --- | --- | --- |
| René/Jens Q and source qualifications | Yes; current seven-target observation/quality ingestion exists | Daily reconstruction QC and exact hourly-window checks; no new provider request |
| Local GEOGLOWS Q and checked regional topology | Yes; 520.75 MiB raw package, nine active reaches 2010–2025 | Reuse seven targets, daily aggregation; do not redownload global archive |
| AlphaEarth means | Yes; 72 catchment-year rows, nine catchments, 2017–2024; metric-grid variant also held | Select seven geometry-checked rows for fixed 2017; no new local embeddings or weights |
| Meteorology | Partial: held ERA5-Land temperature/dewpoint/pressure grids and RADOLAN; existing tables often watercourse-specific | Reaggregate seven gauge polygons; retrieve only missing precipitation/wind/radiation fields for the common recipe, including lag warm-up |
| Conventional landscape controls | Partial: held polygons/EStreams and model topology | Verify per-gauge matches and definitions; subset consistent public attributes or aggregate public terrain/land-cover/soil/regulation sources where absent |
| Soil/snow | Sources held; older preparation records identify aggregation still needed | Optional equal-input sensitivity after current coverage verification, not mandatory new downloads |
| External Q/boundaries/quality metadata | Not yet acquired for this design | Inventory preferred German dataset/version, then subset the fixed external geography; no new email needed if access works |
| Regional donor training observations/boundaries/metadata | Not yet acquired for this design | Same German source, separately frozen western-German donor geography; exclude reserved external and local connected networks |
| External GEOGLOWS, weather, AlphaEarth | Not yet acquired | Selected river series and server-side catchment summaries; not full imagery |
| XGBoost/code | XGBoost absent from checked .venv-geoglows; DISE repository inaccessible | Separate pinned small environment and independent transparent implementation; do not mutate existing fit environment |

GFZ's full hourly German package is reported by a maintained client as about
14 GB compressed; **that size is a secondary-source estimate**, not a verified
primary-file byte count. Primary metadata confirms dataset identity and period,
but this review did not verify HTTP range or individual-file download support.
Inspect the primary file listing and content lengths before retrieval. If only
a monolithic ZIP is exposed, test range support and remote central-directory
selection; otherwise stage it remotely in the already-held Azure storage, or
verify peak local storage before acquiring/extracting. Do not silently fall back
to the old daily dataset or provision a VM. Downloading/storing on Azure carries
storage and possibly transfer costs; existing credit is not assumed free usage.

## Disk and compute design

Measured free space: **79.54 GiB**, leaving **29.54 GiB** above the established
50-GiB reserve. Measurements and local inventory are retained in
[the resource receipt](reviews/limburg-dise-resource-inventory-2026-11-16.json).
No cleanup or offload was needed for this review. No other chapter was touched.

| Phase | Additional peak working allowance | Unbenchmarked machine-time allowance |
| --- | --- | --- |
| Stage 1 daily/QC assembly | 0.5–1 GiB | 30 minutes–2 hours |
| Stage 2 local + regional donor inputs, CPU tuning/fits/review | 4–8 GiB with subset access, including meteorology summaries | Provisionally 1–4 days including full nested tuning; donor count and first-fit timings still unknown |
| Stage 3 selected external series + inference/review | 2–8 GiB when subset access works | Downloads several hours/service dependent; inference minutes to an hour; aggregation/review 1–4 hours |

These are working allowances, not measured ETAs. In the maximal five-group
design: temporal tuning 5 years × 4 arms × 4 candidates = 80 fits; spatial tuning
5 outer groups × 5 years × 4 arms × 4 candidates × 4 inner groups = 1,600 fits;
final refits 30 outer splits × 4 arms × 3 seeds = 360, or **2,040 fits**. The four
inner folds also cover regional donors; they are not one model for every donor.
At an illustrative 15–120 seconds per fit this is 8.5–68 serial fitting hours,
before preparation/review; these timings are assumptions, not measurements.
The two-worker schedule may reduce wall time but does not guarantee a factor of
two. Topology grouping can reduce the fit count. Tree depth, early stopping and
donor data size can move timings beyond this range. Benchmark one complete
outer-fold pipeline and revise the ETA before submitting the full queue.

Use at most **two CPU workers**, each with two XGBoost threads initially;
benchmark throughput and memory before increasing. No GPU extraction or
fine-tuning is required. Cache one daily feature table plus immutable index
splits; cache nested-fold feature views in memory instead of duplicating files.
Write only selected-model predictions, compact tuning metrics and necessary
models/receipts, not every candidate's full prediction archive. Bootstrap from
saved predictions without refitting. Resume by completed arm/fold/seed receipts;
verify sources/config/code before accepting a cached result.

Keep total new local peak staging around **15–20 GiB** with selected-series
access, leaving approximately 59–64 GiB free. A full 14-GB archive **plus**
extracted copies is not included in that allowance and may breach the reserve.
Resolve that storage route before bulk retrieval, not by reducing the scientific
cohort or deleting current results. Offload only checksum-verified recoverable
Limburg source/cache data when needed; preserve observations, compact outputs,
code and manifests. No deletion of other chapters' data is authorized.

## Supporting literature and transfer limits

- [Lin et al., DISE, preprint](https://doi.org/10.5194/egusphere-2026-1834):
  direct pooled reconstruction template; full PDF inspected. One-year spatial
  experiment and limited descriptor control motivate our temporal/strong-control
  checks, not an assumption that their improvements transfer here.
- [Liu et al., GRL 2026](https://doi.org/10.1029/2026GL122814): full primary
  methods/results inspected. Learned catchment descriptors can support spatial
  transfer, with mixed peak-flow results. Its gating weights are model-internal
  diagnostics, not causal attribution. Its multi-year/same-year descriptors do
  not establish historical availability; our primary vintage avoids that issue.
  [Reproduction materials](https://zenodo.org/records/22001499) exist; no 195-MB
  code/data bundle was downloaded just to create this design.
- [Qu et al., arXiv v3, 4 November 2026](https://arxiv.org/abs/2601.01558v3):
  abstract/version inspected; donor catchment representation and donor diversity
  matter. Not evidence that event-neighbour retrieval is the same mechanism.
- [Hales et al., SABER 2022](https://doi.org/10.3390/hydrology9070113): primary
  article inspected. Spatial transfer of discharge bias is established prior
  work, so the novelty cannot be 'correcting a global product at an ungauged
  location' alone. Network-aware donor calibration is a relevant comparator.
- [Hales et al., J. Hydrology 2023](https://doi.org/10.1016/j.jhydrol.2023.130279):
  publisher abstract/highlights inspected; direct GEOGLOWS bias-correction
  context. Do not transfer older-product performance figures to RFS V2.
- [Sanchez Lozano et al., MFDC-QM 2025](https://doi.org/10.1016/j.envsoft.2024.106235):
  publisher abstract/highlights inspected. Local monthly calibration is a
  substantive reference, not a straw-man uncorrected-only comparison.
- [Arsenault et al., HESS 2023](https://doi.org/10.5194/hess-27-139-2023): primary
  methods/results inspected. Gauged calibration and pseudo-ungauged prediction
  have different information budgets; report both honestly, do not equate them.
- [CAMELS-DE-1h, dataset preprint](https://doi.org/10.5194/essd-2026-289) and
  [dataset DOI](https://doi.org/10.5880/fidgeo.2026.045): primary abstract and
  metadata inspected; new source supporting overlapping external years.
- [CAMELS-GB v2, ESSD 2026](https://doi.org/10.5194/essd-18-4345-2026): primary
  time conventions, period and access terms inspected; alternate route only.

Potential contribution: test the **incremental** value and failures of a
satellite-conditioned correction for high water across small European
catchments, under explicit local-label and cross-river transfer conditions,
with documented source/geometry uncertainty and ordinary calibration references.
This is a candidate contribution, not a verified 'first'. A location change or
repeating DISE's average NSE gain would not alone establish novelty.

## Preparation before a new run

1. Build the daily/QC and metadata inventory; verify time windows, catchment
   support and actual external file access. Keep data acquisition and local
   methodological preparation concurrent where independent.
2. Save topology groups, chronological/nested splits, feature definitions,
   high-water evaluator and exact equal-budget tuning configuration. Resolve
   conventional-attribute gaps and common forcing extraction explicitly.
3. Implement the small pooled runner in a separate environment. Check hand-worked
   day boundaries, zero discharge, source area conversion, held-river exclusion,
   train-only transformations and the reconstruction information clock. Compare
   predictions to the raw/no-correction identity before expensive fitting.
4. Benchmark one complete outer fold, record ETA/peak space and review numerical
   behaviour, including the previously problematic Randerath events. This checks
   validity and cost, not whether a favourable EO gain exists.
5. Run Stage 1 and Stage 2, retaining the census and adverse results. Inventory
   Stage 3 in parallel; run external predictions once its fixed source, geography
   and quality rules are recorded. No mandatory favourable-result gate or
   preregistration is introduced.

Current readiness: **scientifically specified candidate; not yet executable**.
The missing work is small-model implementation, daily/spatial data preparation,
attribute harmonization and external access verification, not another weeks-long
encoder-extraction programme.


## Implementation update — 16 November 2026

Independent adaptation is accepted and local preparation plus one fitting fold
are completed; see the [implementation report](limburg-dise-preparation-2026-11-16.md).
The earlier "not yet executable" status above describes the original design
review. The full regional runner remains incomplete, while the local benchmark
is now executable and verified. Common-source conventional land cover uses
2017 Copernicus Proba-V tree/crop/urban fractional cover, matching AlphaEarth's
landscape vintage; a first 2012-CORINE preparation is retained but superseded.
Surface field capacity is explicitly a proxy, not full root-zone storage.
CAMELS byte-range/member access is now verified and its exact ZIP size is
15,149,654,797 bytes; the earlier approximate secondary size/access uncertainty
is superseded. Candidate counts are 286 donors, 49 external and 52 overlap-review
cases; reach and observation checks still determine eligibility. No full
regional fitting or external bulk time-series acquisition has launched.
