# Decisions Log

## 2026-06-06 — Initial chapter framing

Decision: Set up this repository around the working claim that the Kerkrade low-cost IoT stream carries a decomposable antecedent-hydrological-state signal once barometric effects are explicitly characterized and separated.

Alternatives considered: Treat the chapter as a direct flood-prediction chapter; treat it as a purely barometric mine-gas dynamics chapter; delay repository setup until after data ingestion.

Reasoning: The June 2026 pre-work plan makes the first month a foundation and decomposition sprint. The chapter should survive either outcome of the first kill check: if pressure explains only part of CO2 variance, the hydrological-signal framing proceeds; if pressure explains nearly all variance, the chapter can redirect toward a barometric-decomposition methods contribution without losing the work already done.

Source: `chapter-prework/June 2026 - How-To.docx`; `chapter-prework/Lit-scaffold - chapter draft.docx`.

## 2026-06-06 — Repository structure

Decision: Use numbered runnable scripts in `scripts/` and reusable package code in `src/`, with no notebooks as core analytical artifacts.

Alternatives considered: Notebook-first exploratory workflow.

Reasoning: The chapter needs reproducible, defensible analysis steps. Numbered scripts make the run order explicit; `src/` keeps readers, feature builders, models, and evaluation code stable across scripts.

Source: `chapter-prework/June 2026 - How-To.docx`; `chapter-prework/skill-dissertation-chapter-scaffold/reference/repo_layout.md`.

## 2026-06-06 — Data-window policy

Decision: Treat January 2025 to present as the first synchronized modelling window only, not as a limit on data acquisition.

Alternatives considered: Pull only January 2025 to present for every source; postpone older data acquisition until after the first models run.

Reasoning: The IoT stream appears to constrain the primary aligned analysis window, but hydrological and meteorological context benefits from longer records. Longer discharge and weather histories are especially useful for percentile thresholds, event catalogues, seasonality checks, and deciding whether 2025-present events are ordinary, high-flow, or genuinely extreme. Pulling longer histories now is low-cost and reduces the chance of rebuilding loaders later.

Working rule: For each source, acquire the longest practical history available. Use the full history for context and thresholds; subset to the common IoT/weather/discharge overlap for the first synchronized models.

## 2026-06-06 — Task 1.3 discharge sources

Decision: Use WVER Wurm Rimburg NL discharge, Waterschap Limburg Geul Hommerich discharge, and Waterschap Limburg Geul Meerssen discharge as the first discharge set for the June soft-label/event-catalogue work.

Alternatives considered: Use WVER Herzogenrath water level only; wait for a separate official data request before implementing discharge ingestion.

Reasoning: The June How-To names Worm/Wurm plus Geul discharge as the unblock-everything task. WVER exposes Wurm Rimburg NL `Abfluss` JSON directly, while Herzogenrath's public WVER page exposes water level rather than discharge. Waterstand Limburg exposes public OData-style `Afvoer` measurements for the named Geul Hommerich and Meerssen gauges. These three sources provide a usable first-pass discharge frame now, while leaving room to replace or supplement them with official historical/gauge-validated files later.

Source: `docs/discharge-sources.md`; public WVER and Waterstand Limburg station endpoints inspected on 2026-06-06.

## 2026-06-06 — Routine data refresh entry point

Decision: Use `python scripts/update_data.py` as the routine command for bringing available chapter data sources up to date.

Alternatives considered: Re-run each task-specific script manually; wait to create a refresh command until IoT/weather ingestion is implemented.

Reasoning: Several chapter inputs update daily or hourly. A single refresh entry point keeps the workflow simple when data needs to be current before analysis, while still letting each source family keep source-specific ingestion details in its own script. For discharge, Waterstand Limburg sources are appended from the latest local timestamp and WVER's compact public JSON is replaced.

Source: `scripts/update_data.py`; `scripts/01_ingest_discharge.py`.

## 2026-06-06 — Task 1.1 IoT source

Decision: Ingest the Kerkrade IoT stream from the existing Azure storage blobs in `stkerkradeprod01bg` / `air-quality-device-data-1`, rather than re-querying Blynk for historical rows.

Alternatives considered: Re-run the Blynk polling code locally; wait for a separate export; copy the source CSVs manually from Azure Storage Explorer.

Reasoning: The Azure Function already polls Blynk every minute and writes daily CSV blobs with UTC timestamps. Using those blobs makes the chapter update path simple, repeatable, and consistent with the production capture path, while avoiding credential storage in the repository. The local script uses the current Azure CLI login and refreshes only missing or size-changed daily blobs by default.

Source: `kerkrade_data/air_quality_timer/__init__.py`; `docs/iot-sources.md`; Azure resource group inspection on 2026-06-06.

## 2026-06-06 — Task 1.2 weather source

Decision: Ingest Visual Crossing weather for the June Task 1.2 brief from the existing Azure weather blob containers, not from fresh API calls.

Alternatives considered: Use the Visual Crossing API keys to pull fresh daily/hourly data; defer weather ingestion until a primary meteorological source is chosen; pull only the Kerkrade weather container.

Reasoning: The resource group already contains monthly Visual Crossing weather blobs for Kerkrade and nearby comparison locations. Pulling from Blob Storage now satisfies the immediate June ingestion brief, avoids spending API quota, and gives the chapter a repeatable local source layout. The stored CSV timestamps are local civil time, so the loader localizes them to Europe/Amsterdam time and converts to UTC for alignment with IoT and discharge.

Source: `docs/weather-sources.md`; Azure weather container inspection on 2026-06-06.

## 2026-06-10 — Kill Check 1 barometric baseline

Decision: Proceed with the hydrological-signal framing after the Week 2 pressure-only baseline. After merging the local Blynk IoT exports, the official linear IoT-pressure model R2 is 0.430628, below the June kill-check proceed threshold of 0.85.

Formula: `CO2 ~ pressure + delta_pressure_1h + delta_pressure_3h + delta_pressure_6h + delta_pressure_12h + delta_pressure_24h`.

Analysis window: 2025-02-01 15:00 UTC to 2026-04-13 02:00 UTC after lag/dropna. Rows used: 3719 from the 10491-row joined frame.

Sensitivity: Ridge on the same IoT-pressure features produced R2 = 0.430315. The Kerkrade Visual Crossing pressure sensitivity produced linear R2 = 0.423368 and ridge R2 = 0.423217.

Reasoning: Pressure level and tendency explain a meaningful share of CO2 variance, but far less than the >0.95 redirect threshold. Residual variance remains large enough to support the next June tasks: Eryilmaz replication and residual hydrological-signal characterization.

Source: `scripts/02_barometric_baseline.py`; `results/baseline/r2.txt`; `data/processed/co2-residual-barometric.csv`; `chapter-prework/June 2026 - How-To.docx`.

## 2026-06-10 — Kill Check 2 Eryilmaz replication

Decision: Treat the Eryilmaz public-weather substitution result as replicated on the current Kerkrade IoT window and proceed. Model B, using outdoor Visual Crossing weather features, is within 0.05 AUROC of Model A, using indoor IoT environmental features.

Target: `iot_co2_ppm > 1000`.

Model A features: `iot_temperature_c`, `iot_relative_humidity_pct`, `iot_air_pressure_hpa`, `delta_pressure_6h`.

Model B features: `kerkrade_weather_temp_c`, `kerkrade_weather_relative_humidity_pct`, `kerkrade_weather_pressure_hpa`, `delta_pressure_6h`.

Evaluation: Stratified random 5-fold cross-validation with `random_state=42`, using `StandardScaler` and `LogisticRegression(max_iter=1000, solver="liblinear")`. This random CV setup is used only for faithful Eryilmaz replication; later chapter models should use time-aware evaluation.

Results after merging local Blynk exports: Model A AUROC = 0.961009 and
Model B AUROC = 0.921572 on the same 3776 complete-case hourly rows, with 408
positive CO2 events. AUROC gap = 0.039438.

Reasoning: The outdoor-weather model performs nearly as well as the indoor-IoT environmental model on the same CO2 leak target, consistent with Eryilmaz's same-site feature-substitution finding. Because the current IoT window is short, this should be rerun unchanged after additional IoT data are added.

Source: `scripts/03_eryilmaz_replication.py`; `results/eryilmaz/auroc.txt`; `data/processed/eryilmaz_replication_predictions.csv`; `chapter-prework/June 2026 - How-To.docx`.

## 2026-06-11 — Week 4 exploratory signal characterization

Decision: Treat the Week 4 residual-structure work as exploratory characterization rather than a confirmatory hydrological model.

Scope: Use the Week 2 barometric residual as the response for lagged cross-correlations, random-forest feature-importance scans, and PCA. Use the existing soft-label hydrological columns as proxy targets/features only for early signal triage.

Reasoning: The current IoT/residual window is still short, while the June Week 4 task asks for lags out to 14 days. The outputs are still useful for finding candidate timing, confounding channels, and transfer-site needs, but the chapter should not over-interpret these results until the added IoT data are incorporated.

Reference data policy: Add KNMI reference meteorology and RIVM/Luchtmeetnet transfer-site ingestion as cached, reproducible starter lanes. KNMI live downloads require a KNMI Open Data API key via `KNMI_API_KEY`; RIVM/Luchtmeetnet is public and uses a fair-use policy. If the RIVM live API is unavailable, use official data-portal CSVs with `python scripts/04_ingest_rivm.py --use-portal`.

Source: `scripts/04_signal_characterization.py`; `scripts/04_ingest_knmi.py`; `scripts/04_ingest_rivm.py`; `chapter-prework/June 2026 - How-To.docx`.

## 2026-06-17 — July provisional modelling protocol

Decision: Proceed with July as a pipeline-first modelling month, but treat model interpretation as provisional on the current gappy 3719-row barometric-residual window.

Reasoning: The merged Kerkrade IoT/residual overlap is now long enough to run the official 30-day train / 7-day evaluation machinery, smoke-test anomaly agreement, and preregister transfer evaluation. It is still not a continuous annual IoT record, so final chapter claims should wait for more IoT continuity and KNMI backfill. The scripts should be rerun unchanged after more IoT and KNMI data arrive.

Reference meteorology policy: Include `data/interim/knmi_hourly.csv` as optional exogenous reference meteorology when present. When KNMI is absent, use Visual Crossing plus IoT pressure level/tendency features and record that omission in model summaries.

Source: `chapter-prework/July 2026 - How-To.docx`; `scripts/05_sarimax.py`; `scripts/06_kalman.py`; `scripts/07_isolation_forest.py`; `scripts/08_ensemble_agreement.py`; `scripts/09_synthetic_injection.py`; `scripts/10_evaluation.py`.

## 2026-06-17 — July model implementation choices

Decision: Save July detector outputs using reproducible script-first artifacts, using the planned `statsmodels` state-space paths when the `chapter1-co2` environment is active and documented fallbacks only when those packages are unavailable.

SARIMAX first pass: Use the planned residual target, stationarity/transform decision logging, and compact default order-search output. With the active `chapter1-co2` environment, `scripts/05_sarimax.py` fits the `statsmodels` SARIMAX path and selects `(1,0,2)` with daily seasonality. The full p,q in 0..2 grid remains available with `--full-grid`; routine checks use the compact grid to avoid slow state-space refits.

Kalman innovations: Use the planned residual target and exogenous-regressor structure. With the active `chapter1-co2` environment, `scripts/06_kalman.py` uses the `statsmodels` local-level state-space path with exogenous regressors; the simpler fallback remains available if state-space packages are missing.

Isolation Forest and ensemble: Use `IsolationForest(n_estimators=200, max_features=0.8, contamination=0.05, random_state=42)` as the official provisional flag, with 0.03/0.05/0.10 sensitivity outputs. Align SARIMAX, Kalman, and Isolation Forest flags by hourly UTC timestamp and summarize detector counts, all-three agreement, Jaccard, and Cohen kappa.

Evaluation: Preregister transfer evaluation before transfer-site modelling outputs. The official 30-day train / 7-day evaluation is now runnable on the merged IoT frame, while the shorter 14-day train / 3-day smoke scheme remains only for validating the pipeline when needed. Kerkrade API is computed from Visual Crossing precipitation with `d=0.85` and `N=14 days`.

Source: `docs/transfer-experiment-preregistration.md`; `scripts/10_evaluation.py`; `chapter-prework/July 2026 - How-To.docx`.

## 2026-06-21 — KNMI reference station and backfill policy

Decision: Use KNMI station `06380` Maastricht Airport as the primary reference meteorology station for the Kerkrade chapter, with `06377` Ell and `06392` Horst reserved as possible sensitivity stations.

Reasoning: The KNMI 10-minute in-situ product is delivered as timestamp-level NetCDF files containing many stations. Downloading only the Meuse/South Limburg station is not supported by the current file endpoint, but processing can and should narrow the normalized frame.

Operational policy: This initial local launchd policy is superseded by the later Azure Timer Function policy below. The local wrapper remains as a fallback, but Azure now performs the long-running backfill and stores compact station-slim monthly blobs instead of retaining the raw all-station NetCDF corpus.

Source: `scripts/04_ingest_knmi.py`; `src/io_data.py`; `docs/knmi-sources.md`.

## 2026-06-23 — KNMI Meuse/Maas station-set policy

Decision: Keep normalized hourly KNMI data for a curated Dutch Meuse/Maas station set rather than only Maastricht Airport or the full KNMI station corpus.

Station set: `06380` Maastricht Airport, `06377` Ell, `06392` Horst, `06370` Eindhoven Airport, `06375` Volkel Airport, `06350` Gilze-Rijen Airport, and `06356` Herwijnen.

Reasoning: KNMI 10-minute NetCDF files contain all stations for each timestamp, so raw downloads remain file-level during acquisition. The normalized hourly output can still be narrowed to the stations most useful for Meuse/Maas catchment and corridor analysis. This preserves future basin-scale weather context with far less processed storage than retaining every KNMI station, while keeping `06380` as the primary Kerkrade comparison and transfer meteorology station.

Operational policy: `scripts/04_ingest_knmi.py` defaults to `--station-set meuse` and writes `results/knmi/knmi_station_set.csv`. The Azure KNMI function uses the same station set through `KNMI_STATIONS`. Use `--station-set maastricht` only when the old single-station extraction is needed.

Source: `scripts/04_ingest_knmi.py`; `src/io_data.py`; `docs/knmi-sources.md`.

## 2026-06-23 — Azure KNMI collector policy

Decision: Move the long-running KNMI historical backfill from local launchd to
an Azure Timer Function.

Reasoning: The local collector is blocked by macOS unattended-script
permissions and is tied to laptop wake state. The KNMI task is a resumable
server-side ingestion problem: pull bounded batches of 10-minute NetCDF files,
store raw files in blob storage, and track progress with a cursor blob.

Operational policy: Deploy `kerkrade_data/knmi_backfill_timer` with
`kerkrade_data/azure/deploy_knmi_function.sh`. The Azure function downloads
each raw all-station NetCDF file as temporary input, extracts broad variables
for the selected Meuse/Maas stations, appends/deduplicates monthly gzip CSV
blobs under `knmi-data/slim/10-minute-in-situ/`, and writes progress to
`knmi-data/state/knmi_backfill_state.json`. Full raw NetCDF persistence is off
by default; use `KNMI_KEEP_RAW=true` only for short debugging windows.

Source: `kerkrade_data/knmi_backfill.py`;
`kerkrade_data/knmi_backfill_timer`; `docs/knmi-sources.md`.

## 2026-06-24 — KNMI cloud-to-local and file-format policy

Decision: Treat Azure Blob Storage as the long-running KNMI collection cache,
then sync the compact station-slim monthly blobs into local `data/raw/knmi/`
for reproducible modelling runs.

Reasoning: The Azure function is the right place for slow unattended API
collection, but the chapter analysis should remain runnable from the repository
workspace. Keeping local copies of the station-slim blobs avoids repeated API
calls and makes model reruns independent of Azure availability.

Data-format policy: Use source-native or compact CSV.GZ files for raw/source
caches, prefer Parquet for larger normalized analytical tables because it
preserves dtypes and compresses well, and keep CSV mirrors for small summaries,
human inspection, and existing script compatibility.

Operational policy: `scripts/04_sync_knmi_azure.py` downloads Azure slim blobs
to `data/raw/knmi/azure_slim/`, stores local copies of the Azure state JSON,
and rebuilds `data/interim/knmi_hourly.csv` plus
`data/interim/knmi_hourly.parquet`.

Source: `scripts/04_sync_knmi_azure.py`; `scripts/04_ingest_knmi.py`;
`src/io_data.py`; `src/io_knmi.py`; `docs/knmi-sources.md`.

## 2026-06-24 — Source-family loader split

Decision: Split the large shared data-loader file into source-family modules
while keeping `src/io_data.py` as the stable import facade for scripts.

Reasoning: The repo now has distinct IoT, weather, discharge, KNMI, and
RIVM/Luchtmeetnet ingestion lanes. Keeping each parser in its own module makes
the code easier to review and extend without forcing every script import to
change at once.

Operational policy: Source-specific logic lives in `src/io_iot.py`,
`src/io_weather.py`, `src/io_discharge.py`, `src/io_knmi.py`, and
`src/io_rivm.py`. Scripts should continue importing public loaders from
`src.io_data` unless they have a source-specific reason to use the lower-level
module directly.

Source: `src/io_data.py`; `src/io_iot.py`; `src/io_weather.py`;
`src/io_discharge.py`; `src/io_knmi.py`; `src/io_rivm.py`.

## 2026-06-23 — Local Blynk IoT export merge policy

Decision: Merge local Blynk device exports from `iot-device-data/` into the
canonical hourly IoT frame, while keeping source/device coverage reports as
first-class QC artifacts.

Current merged source windows: Mantingh Basement 1 (`455022`) covers
2025-01-31 00:00 to 2025-02-27 16:09 UTC, Mantingh Basement 2 (`455025`) covers
2025-06-26 15:00 to 2025-10-08 13:00 UTC, and the Azure device stream covers
2026-03-16 21:58 to 2026-04-13 02:36 UTC in the current local cache.

Reasoning: The exports substantially extend the analysis-ready IoT window and
can be aligned to the existing UTC hourly convention. They also introduce
multiple device windows and two long no-data intervals, so downstream models
should use the merged frame for pipeline completeness but interpret
source-window effects cautiously.

Operational policy: `scripts/01_ingest_iot.py --skip-download` merges Azure raw
files plus `iot-device-data/` by default, writes `data/interim/iot_hourly.csv`,
and writes `data/processed/iot_source_summary.csv` plus
`data/processed/iot_coverage_gaps.csv`. Use `--skip-exports` only when an
Azure-only rebuild is needed.

Source: `scripts/01_ingest_iot.py`; `src/io_data.py`; `docs/iot-sources.md`.

## 2026-06-21 — August readiness boundary

Decision: Begin August scaffolding work now, but do not interpret transfer results until the current preregistration, June/July pipeline, and KNMI scheduler state are committed and at least the selected transfer scope is explicit.

Can start now: methods-section outline, figure inventory, transfer-evaluation script design, transfer-site acquisition planning, and KNMI backfill monitoring.

Should wait: official transfer-stress-test interpretation, transfer baseline comparison claims, groundwater integration, and final discussion framing.

Reasoning: The August plan depends on July detector outputs and transfer preregistration, both of which exist. The official July evaluation windows are now runnable on the merged IoT frame, but interpretation remains provisional because the IoT record is gappy, the KNMI backfill is still in progress, and transfer-site coverage is not yet at the planned three-site threshold.

Source: `chapter-prework/August 2026 - How-To.docx`; `docs/august-readiness.md`; `docs/figure-inventory.md`.

## 2026-06-21 — August v1 transfer dry-run scope

Decision: Implement `scripts/11_transfer_stress_test.py` as a RIVM-only dry run and writing scaffold, not as official transfer interpretation.

Scope: Train one balanced logistic-regression surrogate per July detector label from Kerkrade features. Apply those surrogates only to the currently cached South Limburg RIVM/Luchtmeetnet lane, joined with KNMI station `06380` Maastricht Airport where cached hours exist. Use no random k-fold CV. Report row counts, feature availability, label sources, and score outputs only.

Current dry-run details: The deployable shared features are temperature, relative humidity, pressure, precipitation, PM10, NO2, and pressure deltas through 12 hours. PM2.5, O3, and the 24-hour pressure delta are recorded in feature availability but are not currently deployable across both RIVM sites. After the corrected merged-IoT rerun, SARIMAX and Isolation Forest use official detector flags; Kalman has too few official positives and therefore uses the preregistered top-5-percent fallback label from extreme innovation scores.

Interpretation boundary: Do not read August v1 transfer probabilities as transfer success or failure. Official transfer interpretation waits until at least three transfer-site lanes are available or the dissertation scope is deliberately narrowed and documented.

Source: `scripts/11_transfer_stress_test.py`; `results/transfer/transfer_training_summary.csv`; `results/transfer/feature_availability.csv`; `docs/transfer-experiment-preregistration.md`.

## 2026-07-03 — IoT/weather capture outage root cause

Decision: Record the production capture outage as a deployment defect, not a device failure, and leave the redeploy decision to the project owner.

Finding: `air_quality_timer`, `hourly_pull_timer`, and `monthly_pull_timer` in `func-kerkrade-monthly-pull-bg` have failed on every invocation since the IoT record stops at 2026-04-13 02:36 UTC. Application Insights shows `ImportError: cryptography/_rust.abi3.so: invalid ELF header` — the deployed `.python_packages` contains macOS-built native wheels running on the Linux Functions host. The last captured rows show a healthy sensor (CO2 ~405 ppm, all status flags 1), so the basement device was fine at cutoff.

Fix path (not executed): redeploy `func-kerkrade-monthly-pull-bg` with a remote build (`func azure functionapp publish func-kerkrade-monthly-pull-bg --build remote`) or Linux-built wheels. This app is separate from `func-kerkrade-knmi-backfill-bg`, which is healthy and must not be touched.

Source: Application Insights traces (rg-kerkrade-prod); `data/raw/iot/air_quality_2026-04-13.csv`; blob listing of `air-quality-device-data-1`.

## 2026-07-03 — Gap-honest features and per-block detector fits

Decision: Never compute a lagged difference, autoregressive lag, or filter innovation across a coverage gap. The signal frame keeps the full hourly grid (left join in `04_signal_characterization.py`, hourly reindex in `src/models/july.py`), and SARIMAX/Kalman fits run per contiguous hourly block of at least 168/72 hours with initial warm-up hours masked.

Alternatives considered: keep row-wise lags on the gappy frame (a "1-hour" delta could span the 160-day outage); interpolate across gaps (invents data); fit one model over concatenated blocks (seasonal and AR lags misalign at every boundary).

Reasoning: The merged IoT record is three usable blocks (626h, 2471h, 606h) plus fragments. Order selection uses the longest block; the selected specification is refit per block. KNMI reference meteorology now joins as single-station `06380` data rather than a multi-station elevation-mixed average.

Source: `src/models/july.py`; `scripts/04_signal_characterization.py`; `scripts/05_sarimax.py`; `scripts/06_kalman.py`.

## 2026-07-03 — One official flag rule and time-aware evaluation

Decision: All three detectors use the same official anomaly flag — |robust z| > 3.5 on the detector's native score (SARIMAX residual, per-timestep standardized Kalman innovation, Isolation Forest score). Contamination levels become score-quantile sensitivity columns. Evaluation windows are defined in calendar time with a minimum 70% observed-hour coverage in both spans, detectors are refit per rolling-origin window and scored out of sample with train-window thresholds, and event-window anomaly-rate tests run per deduplicated physical episode rather than per gauge/quantile catalogue row.

Alternatives considered: keep per-detector flag rules (the Kalman global-3-sigma rule fired on 1 of 3,635 hours and made the ensemble effectively two detectors); keep row-position windows (a "30-day" window could span the 160-day outage); keep per-row event tests (one physical episode entered the sign-flip test up to nine times).

Reasoning: The chapter's Section 5.2 commitment is time-aware splits applied uniformly across all three detectors; the in-sample full-record summaries are retained but labelled `in_sample_full_record` and are diagnostic only. Synthetic injection (`09`) now refits the actual pipeline detectors on injected series and writes a tsadams-style unsupervised selection ranking.

Source: `scripts/07_isolation_forest.py`; `scripts/09_synthetic_injection.py`; `scripts/10_evaluation.py`; `src/eval.py`; `tests/test_eval.py`.

## 2026-07-09 — Capture restored: vendored-package redeploy

Decision: Redeploy `func-kerkrade-monthly-pull-bg` (authorized by the project owner on 2026-07-09) with a source-only whitelist zip plus the repo's verified Linux-built `.python_packages`, excluding `knmi_backfill_timer/` so no second KNMI backfill runner could register in this app.

Sequence: A first source-only deploy relied on remote build, but the app lacks `ENABLE_ORYX_BUILD` and Kudu skipped dependency installation (`ModuleNotFoundError: requests`). The second deploy vendored the repo's `.python_packages` (all 72 native libraries verified ELF x86-64, cp311, covering requirements.txt) and succeeded without any app-settings changes.

Verified after deploy: `air_quality_timer` succeeding every minute with zero exceptions, `air_quality_2026-07-09.csv` being written to `air-quality-device-data-1`, function list unchanged at the original four functions. `func-kerkrade-knmi-backfill-bg` was never modified.

Follow-ups: the IoT gap 2026-04-13 → 2026-07-09 is permanent unless Blynk device exports cover it (place any in `iot-device-data/`); Visual Crossing weather for the gap is recoverable via the monthly/hourly pull backfill. The deploy-script defect that caused the outage (`azure/deploy_function.sh` zips `.python_packages` built on the deploying machine) remains; prefer excluding `.python_packages` and enabling `ENABLE_ORYX_BUILD=true`, or only deploying from a Linux-wheel tree.

Source: `results` of config-zip deploys on 2026-07-09; Application Insights (rg-kerkrade-prod); blob listing of `air-quality-device-data-1`.

## 2026-07-09 — Distributed-lag test of the multi-week antecedent signal

Decision: Before proposing any redesign around the Week 4 lag-scan result (residual–discharge coupling at ~10.6 days), test it with a pre-stated decision rule in `scripts/12_distributed_lag.py`: daily aggregation per block, exponentially weighted antecedent-precipitation timescale scan with same-day met controls and block fixed effects, confirmatory inference at a 10-day half-life (HAC + moving-block bootstrap), per-block sign replication, and a future-precipitation placebo.

Outcome (2026-07-09 record): NOT SUPPORTED. Confirmatory coefficient positive but not significant (HAC p=0.31; bootstrap CI spans zero; 72 usable days). Decisive detail: the placebo failed in the damning direction — future precipitation "explains" the residual more strongly (t=-3.64) than past precipitation (t=1.02), the signature of shared low-frequency structure rather than a lagged causal signal. The Week 4 lag-scan correlation should be treated as an artifact of smooth-series cross-correlation until a longer record says otherwise.

Interpretation boundary: this is failure to establish, not proof of absence — at a 10-day half-life only the 2,116-hour block contributes usable days (the shorter blocks cannot supply 30 days of API history by construction), so per-block replication was unachievable on this record and power is low. Rerun the same script unchanged as the restored capture extends the record, and again when Provincie Limburg groundwater data (a direct state predictor, unlike precipitation) is integrated.

Consequence for design: the "retune the evaluation to the 10-day timescale" argument does not currently have evidence behind it. The detector-frame critique stands on its own merits, but no reframing should be proposed to the supervisor as data-driven; the binding constraint is record length.

Source: `scripts/12_distributed_lag.py`; `results/distributed_lag/summary.txt`; `docs/week4-signal-interpretation.md`.

## 2026-07-12 — Chapter-readiness, freeze, and transfer scope

Decision: Use `docs/chapter-readiness-plan.md` as the canonical record for
chapter completion. Target a frozen analysis snapshot on 2026-09-08 after at
least 60 post-restoration IoT days, with 2026-10-06 as the only contingency
freeze. Cross-site transfer is secondary and cannot block the chapter.

Primary claim rule: Ask neutrally whether the pressure-separated CO2 residual
contains information about directly measured groundwater/mine-water state.
Allow supported, site-specific/data-limited, or null/boundary conclusions. Do
not use causal language until the locked direct-state analysis passes its HAC,
bootstrap, block-replication, and future-water-placebo criteria.

Operational rule: Weekly refreshes update coverage/QC only. Final scientific
interpretation occurs once against an immutable snapshot and is recorded in
`results/run_manifest.json` with code, environment, input, command, and output
provenance.

Source: `docs/chapter-readiness-plan.md`; repository end-to-end review on
2026-07-12.

## 2026-07-13 — Replace per-blob alerts with one daily summary

Decision: Keep the minute-level IoT and hourly weather collection schedules,
but remove all weather/IoT blob-created emails. Send one consolidated IoT and
weather status email daily at 21:05 UTC instead.

Implementation: Remove the Event Grid subscription and the
`blob_created_email_alert` function, remove upload-triggered email from the
historical weather timer, and deploy `daily_summary_email_timer`. The production
deployment must use `--build-remote true`; a raw source-package deployment does
not install `requests` or the Azure SDK dependencies on Linux.

Verification: The live Event Grid subscription list is empty; the Function App
contains the daily summary timer at `0 5 21 * * *` and no blob email trigger;
the remote build completed successfully; post-build IoT timer executions and
blob appends succeeded with no new exceptions.

Source: `kerkrade_data/daily_summary_email_timer/`;
`kerkrade_data/azure/deploy_function.sh`; Application Insights and live Azure
Function/Event Grid inventories on 2026-07-13.

## 2026-07-21 — Separate forward KNMI maintenance from historical backfill

Decision: Preserve the completed backward cursor and continue KNMI collection
from the June 24 archive edge with a separate forward state blob. Keep the
forward cursor three hours behind current UTC so KNMI publication latency does
not become a permanent apparent gap.

Implementation: Forward collection uses
`state/knmi_forward_state.json`, while the immutable historical completion
record remains in `state/knmi_backfill_state.json`. Monthly station-slim blobs
are appended and deduplicated by UTC timestamp and station.

Deployment safety: The KNMI deployment script, local settings example, and
deployment documentation default to the production forward handoff, forward
state blob, 180-minute publication lag, and 200-file batch. Historical mode now
requires explicit overrides.

Verification: On 2026-07-22 the live Function App reported direction
`forward`, state `state/knmi_forward_state.json`, a 180-minute lag, a
15-minute schedule, and no failed downloads in the active catch-up.

Source: `kerkrade_data/knmi_backfill.py`;
`kerkrade_data/azure/deploy_knmi_function.sh`; live Azure KNMI state and blob
inventory on 2026-07-22.

## 2026-07-22 — One detector contract and pressure-safe state-space controls

Decision: Full-record fitting, synthetic injection, and rolling-origin
evaluation must use the same versioned detector family and fit/score
implementation. Persist the actual family and reject older family-ambiguous
model artifacts. A non-converged state-space fit may fall back only to an
explicitly named `arx` or `ridge_local_level` family.

Feature policy: SARIMAX/AR-X and local-level models use the already
pressure-separated CO2 residual with standardized IoT temperature and relative
humidity controls. They do not reintroduce pressure level, pressure tendency,
or a second weather source. Isolation Forest retains its multivariate feature
contract.

Selection policy: Test a small nonseasonal SARIMAX grid first and consider
daily seasonality only after a base fit converges. Record optimizer convergence,
warnings, iterations, likelihood, information criteria, features, and family
for selection and every block/window fit.

Provisional outcome: On the 2026-07-21 local snapshot, the selected families are
SARIMAX `(1,0,2) x (1,0,1,24)` and jointly estimated local-level state space.
Both are `ok` in all four full-record blocks and all 11 official rolling
windows; each rolling detector scores 1,848 hours. Synthetic injection refits
the same saved families rather than hard-wired approximations.

Source: `src/detectors.py`; `scripts/05_sarimax.py`;
`scripts/06_kalman.py`; `scripts/07_isolation_forest.py`;
`scripts/09_synthetic_injection.py`; `scripts/10_evaluation.py`;
`tests/test_detectors.py`.

## 2026-07-22 — Optional features cannot delete material coverage blocks

Decision: Separate required detector inputs from optional inputs. Consider
optional features in priority order and retain one only when the accumulated
complete-case frame preserves at least 90% of required rows overall and at
least 90% inside every required-data block of 24 hours or longer. Write the
feature, role, decision, reason, overlap, joint coverage, minimum block
coverage, and latest covered timestamp to a feature audit.

Score-coverage policy: Every detector anomaly artifact must carry its native
`<detector>_scored` indicator. Ensemble construction rejects artifacts without
that indicator, masks any anomaly on an unscored row, and labels each union hour
as `unscored`, `partial`, or `common`. A row is normal only when every
detector was scored and none fired; agreement statistics use common or explicit
pairwise coverage.

Provisional outcome: Isolation Forest retains 41 of 69 audited inputs and
scores 3,893 hours, including 244 post-July-9 hours through 2026-07-21 20:00
UTC. The four locally available KNMI candidate columns are rejected because
they have no coverage in the restored material block. The ensemble contains
3,772 common-coverage hours, 213 partial hours, and one wholly unscored hour.

Source: `src/models/july.py`; `src/detectors.py`; `src/eval.py`;
`scripts/07_isolation_forest.py`; `scripts/08_ensemble_agreement.py`;
`tests/test_io_data.py`; `tests/test_eval.py`.

## 2026-07-22 — Direct-state implementation before data receipt

Decision: Implement the locked groundwater/mine-water normalization and model
before provider data arrive, while keeping every fixture outcome explicitly
non-evidentiary.

Normalization policy: Preserve source-native files; require provider,
measurement, unit, datum, tier, site relationship, orientation, and operational
notes; aggregate observed usable values to UTC days without interpolation; and
retain both the native value and a sign-oriented hydrologic level.

Selection policy: Choose tier 1 connected shaft/mine-water series before tier 2
nearby groundwater series, then maximize overlap with eligible IoT days. Do not
select using coefficient size, p-value, or model fit.

Inference policy: Use the prespecified same-day controlled model, HAC lag 14,
28-day moving-block bootstrap, two-block sign replication, and a seven-day
future-water placebo. Treat lags, daily change, and alternative series as one
Benjamini-Hochberg-corrected sensitivity family.

Source: `docs/chapter-readiness-plan.md`; `docs/groundwater-data-contract.md`;
`src/io_groundwater.py`; `src/direct_state.py`; `scripts/16_direct_state.py`.

## 2026-07-22 — Stable prose before frozen numbers

Decision: Maintain one canonical Markdown chapter draft containing all prose that is
stable before the data freeze. Represent every reportable result as an explicit
`FROZEN` field; do not copy provisional rehearsal values into final-result sentences.

Claim policy: Keep all four prespecified discussion branches in the working draft.
After the immutable run, the machine-readable direct-state outcome selects exactly
one branch. Proxy, anomaly, precipitation, or transfer results cannot promote the
primary claim.

Release gate: Check required sections, bibliography keys, overclaim language, frozen
fields, and branch count in code. A working draft must retain all four branches and
expose unresolved fields. A final draft must contain no unresolved fields and exactly
one recognized branch.

Source: `chapter/chapter-draft.md`; `docs/chapter-writing-register.md`;
`src/chapter.py`; `scripts/17_check_chapter_draft.py`; `tests/test_chapter.py`.
