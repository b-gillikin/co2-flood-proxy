# Decisions Log

> Historical audit log. Entries before the 2026-08-07 held-out-watercourse
> reset describe designs and claims that may now be superseded, including the
> project-chosen 0.05 margin. Current decisions live in `scope-decisions.md` and
> the locked analysis protocol.

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

## 2026-08-06 — Groundwater obtained from public BRO service

Decision: Source groundwater from the Dutch Basisregistratie Ondergrond (BRO)
public REST service rather than waiting on a provider delivery. Retain three
Gemeente Heerlen wells (GMW000000013210, GMW000000013172, GMW000000013161),
6-hourly, 2021-01-01 to 2025-08-27, at 2.85-3.60 km from the site.

Alternatives considered: Continue waiting on a provider response before any
groundwater work; use only the closest wells regardless of whether they publish
level series.

Reasoning: The data required no registration or certificate and was available
throughout the period the repository recorded it as `waiting on data`. A 5 km
well search returned 26 wells; only these three carry usable series. The full
2021-2025 record was retained rather than the overlap slices, because the long
record is what makes barometric efficiency estimable and what quantifies how
unrepresentative the IoT overlap windows are.

Consequence: These are shallow phreatic wells, not mine water. Closer
provincial wells and the mijnwatermeetnet have been requested separately.

Source: `scripts/05a_fetch_bro_groundwater.py`; `data/raw/groundwater/`;
`docs/groundwater-data-contract.md`.

## 2026-08-06 — Barometric correction of the exposure is mandatory

Decision: Barometrically correct water level before using it as an exposure,
using per-well efficiency estimated from 6-hourly first differences over the
full record.

Reasoning: Estimated barometric efficiency is 0.20-0.34, so raw water level
carries a substantial pressure component. Within the Feb 2025 IoT window, water
level and barometric pressure correlate at -0.74 to -0.75; an association with
a pressure-separated CO2 residual there would have been largely artifact.
Correction removes this in the Jun-Aug 2025 window entirely and in Feb 2025 for
one well only. Including pressure as a linear control on the outcome, as the
previous design did, is not equivalent and is weaker.

Source: `scripts/05b_barometric_efficiency.py`;
`results/groundwater/barometric_efficiency.txt`.

## 2026-08-06 — Chapter redirected to the July 2021 reanalysis

Decision: Reframe the chapter around whether the CO2 excursion Viefhues (2022)
attributed to the July 2021 flood was hydrological or barometric. Withdraw the
previous antecedent-hydrological-state framing, the four-branch claim
machinery, the 60-paired-day gate, the two-block sign criterion, the seven-day
future-water placebo, and the ensemble anomaly-detection programme.

Alternatives considered: Continue the 2025-2026 confirmatory design; reframe
around barometric physics without the predecessor reanalysis; wait for
additional IoT accumulation.

Reasoning: The previous question required a flood, and the current IoT record
begins 2025-01-31 with no flood in it. The single clean overlap block provides
62 days across 0.20 m of water-level variation, 7-12% of the range those wells
span. Separately, the withdrawn criteria were scaffolding artifacts rather than
author decisions, and two were defective: the placebo omitted the
contemporaneous term and would have rejected a true association, and the block
criterion could not be satisfied by an unbroken record. The prior rule
excluding the predecessor period also ruled out the analysis the chapter now
intends; it is withdrawn, since testing whether a predecessor inference
survives a control the predecessor did not apply is not circular.

Blocking dependency: the Viefhues IoT record, 2020-08-25 to 2021-09-01, is not
held. Groundwater already in the repository would overlap it by roughly 243
days including the flood.

Source: `docs/chapter-direction.md`; `docs/predecessor-notes.md`;
`docs/data-requests.md`.

## 2026-08-06 — KNMI precipitation unit factor corrected

Decision: Remove the 0.1 unit factor applied to the KNMI `R1H` column. In the
10-minute in-situ product ingested here R1H is already in mm.

Reasoning: Station 06380 reported 111 mm for 2024 against a true 1110 mm.
Verified against the independent Visual Crossing series (Maastricht 1054 mm,
Kerkrade 1153 mm) and by summing only the top-of-hour R1H records (1110.1 mm).

Rejected alternative: summing rather than averaging when resampling. R1H is a
running one-hour accumulation reported every ten minutes, so the six records in
an hour are overlapping totals for the same quantity; averaging recovers the
hourly total and summing sextuples it to 6659 mm. The existing `mean` is
correct and is now documented as deliberate.

Consequence: the distributed-lag rerun rescaled every coefficient by ten
(confirmatory 130.6 to 13.1 ppm per mm/day) but left every t statistic, p value
and criterion unchanged, because scaling a regressor is scale-invariant for
inference. The `NOT SUPPORTED` outcome stands and was never a units artifact.
The correction matters for physical interpretability and for any analysis using
absolute rainfall, such as the precursor comparator.

Source: `src/io_knmi.py`; `results/distributed_lag/summary.txt`.

## 2026-08-06 — No precursor skill in indoor CO2

Decision: Record that indoor CO2 shows no usable precursor skill for tributary
high-flow events over the available record.

Evidence: 19 independent episodes, 3,492 scored hours (445 pre-event, 3,047
quiet), hours inside events excluded, 24-hour lead window. AUROC by predictor:
72-hour rainfall 0.835, 24-hour rainfall 0.794, pressure level 0.250 (inverted,
so informative), 24-hour pressure change 0.470, raw CO2 0.523, pressure-
separated CO2 residual 0.409 at 24 h and 0.405 at 72 h. The CO2 residual departs
from 0.5 in the wrong direction, being lower before events, and is far weaker
than rainfall. The three episodes with no pre-onset pressure fall show no
positive residual excursion (z of -0.58, -0.16, -0.13).

Caveat: bootstrap intervals were computed by resampling hours, which are
autocorrelated, so the stated intervals are too narrow. The ranking and the
size of the gap between rainfall and CO2 are robust to this; marginal claims
about whether 0.41 differs from 0.5 are not.

Consequence: the early-warning premise is not supported at this site. The
chapter reports a bounded negative result with a quantified comparator rather
than an inconclusive one.

Source: `scripts/18_precursor_skill.py`;
`results/precursor/precursor_skill.txt`.

## 2026-08-06 — 2026 sensor coverage is one outage, not intermittency

Decision: Correct the characterization of the 2026 Azure device record. Its
30.7% coverage is not flaky sampling.

Evidence: only three gaps exceed one hour across the whole deployment: 2 h, 3 h,
and one outage of 87.7 days from 2026-04-13 02:00 to 2026-07-09 18:00. Observed
hours are flat across the diurnal cycle (38-40 per hour of day). March coverage
was 93.8%; coverage since restoration on 2026-07-09 is 100%.

Consequence: no intermittency to diagnose. This also identifies what
"post-restoration" meant in the superseded readiness plan: the device returning
on 2026-07-09 after that outage. The action is uptime monitoring, not sampling
repair.

Source: `data/interim/iot_hourly.csv`; `data/processed/iot_coverage_gaps.csv`.

## 2026-08-06 — Barometric response is instantaneous; sensor reads the building

Decision: Record what the CO2 sensor is coupled to, from the barometric response
function and a semidiurnal contamination check.

Evidence: regression deconvolution per contiguous block puts the peak response at
lag 0-1 h with 63% complete inside the hour, total -9 to -40 ppm/hPa. A response
concentrated at zero lag indicates a shallow, well-connected air-filled void
rather than diffusion through a thick unsaturated column.

The semidiurnal probe failed and the failure is the useful part. It assumed
little indoor behaviour is semidiurnal, which is false for a residence with
morning and evening occupancy. Observed 12-hour CO2 amplitude is four to eight
times what the response function predicts (55.6, 32.3 and 76.5 ppm against
predictions near 8-10) and survives subtraction of the fitted pressure model
(11.4, 23.2, 8.0 ppm). A barometric signal could not do that.

Consequence: the non-barometric variance of this record is dominated by the
building, not the subsurface. The script is retained for the contamination check,
with its docstring rewritten to lead with the failure.

Source: `scripts/19_barometric_response.py`; `scripts/20_tidal_response.py`;
`results/barometric_response/`.

## 2026-08-06 — Forward bound: the mechanism was below detection throughout

Decision: Bound the water-driven gain change physically rather than only
testing for it statistically.

Model: rising water shrinks the connected void, so d(gain)/gain is approximately
dh/H for vertical extent H. One assumed parameter, reported as a sensitivity.

Evidence: for the 0.20 m rise available, predicted change is 20% at H = 1 m and
1% at H = 21 m. The windowed gain estimates carry an SD of 19.5 ppm/hPa; in
absolute terms the predicted effect is 0.03-8 ppm/hPa against that scatter.
Detection would require a void no deeper than 0.09 m.

Consequence: the chapter reports a bounded negative rather than an
uninterpretable null, and the seasonal-coverage limitation is defused, since more
winters cannot recover a signal an order of magnitude beneath the floor. Run
backwards the bound specifies a capable study: metres of water movement, as in
decadal mine-water recovery, or an exogenous manipulation such as documented
pumping.

Caveat: the script also prints scatter relative to the median gain (232%), which
is inflated because the median sits near zero. Quote the absolute comparison.

Source: `scripts/21_forward_gain_model.py`;
`results/barometric_response/forward_gain_bound.txt`.

## 2026-08-06 — Analysis closed

Decision: Stop adding methods. The analysis is complete for what this data can
support; what remains is figures and writing.

Reasoning: six independent lines converge on the same answer, and the forward
bound explains why additional methods would not change it. Two candidates were
considered and dropped: a Gaussian-process varying-coefficient model and an
interaction distributed-lag model, both of which test whether gain varies with
water level. The forward bound answers that more directly, and the block
bootstrap already provides the honest-uncertainty framing the former was wanted
for.

Open externally: the provincial reply on closer wells, the mine-water network,
and pumping schedules; and the Viefhues 2020-2021 IoT record.

Source: `docs/chapter-direction.md`.

## 2026-08-06 — Correction: the noise floor is not fixed, and more data helps

Decision: Withdraw the claim, recorded earlier the same day, that the
water-driven gain change sat about two orders of magnitude below detection.

Error: the comparison was made against the scatter of two-week windows and
treated that scatter as a fixed property of the site. It is not. Sweeping window
length gives SDs of 21.7 ppm/hPa at two weeks, 5.69 at four, 4.58 at six and 3.84
at eight, falling faster than 1/sqrt(n). That is estimation noise, which more
data reduces, not real variability in the underlying gain.

Corrected position: at eight-week windows the noise is 3.84 ppm/hPa on a gain of
5.35, and the predicted effect reaches 0.28x the noise for the thinnest plausible
void and 0.01x for the deepest. The effect is at or below detection, not a
hundredfold beneath it.

The conclusion survives for three reasons that are properties of the design
rather than of the sample size. The effect scales with how far the water moves,
so more years of 20 cm swings enlarge the data without enlarging the signal.
Longer windows buy precision and cost windows: at eight weeks there are four,
spanning 0.20 m, which is too little variation to correlate against. And the best
case is marginal rather than clean.

Consequence for the chapter: the seasonal-coverage limitation is only partly
defused. It is fair to say more of the same data would not settle the question;
it is not fair to say the effect was invisible by two orders of magnitude. What
would settle it is metres of water movement, or direct occupancy measurement to
cut the floor structurally.

Source: `scripts/21_forward_gain_model.py`, rewritten to sweep window length;
`results/barometric_response/forward_gain_bound.txt`.

## 2026-08-06 — Reframed as donor-catchment regionalisation

Decision: Reframe the chapter around donor-catchment transfer. Characterise one
tributary deeply, transfer to others, and measure how transfer skill decays with
similarity.

Alternatives considered: a symmetric transfer matrix fitting and testing at every
gauge; continuing the early-warning framing; continuing with the Kerkrade site
alone.

Reasoning: the early-warning framing could not compete with the Dutch operational
system and was too broad. The site-alone framing produced a defensible negative
that was too thin to carry a chapter, because it rested on one house and 19
summer episodes. The donor framing keeps the supervisor's Viefhues to Eryilmaz
progression as a genuine arc -- each step widens the scope of substitution, from
data source to space -- and makes the deep Kerkrade instrumentation load-bearing
as donor characterisation rather than an aside.

The symmetric matrix was rejected because it treats every catchment as equally
known, wasting the Kerkrade instrumentation, and because it makes shared regional
forcing a confound rather than an explanatory variable. Retained as the natural
robustness check if the result proves sensitive to donor choice.

Donor selection evidence: 17 candidate gauges pulled, all 91-100% coverage over
2024-08-06 to 2026-08-06, so coverage does not discriminate. Worm at Rimburg
selected on centrality (0.203, second of 17), mid-range response characteristics,
a downstream partner at Randerath, and holding the CO2 sensor and BRO wells. Geul
selected as validation catchment for its three-gauge chain; routing Hommerich to
Meerssen measured at +4 h.

Source: `docs/chapter-direction.md`; `scripts/22_ingest_waterschap_gauges.py`;
`data/interim/waterschap_discharge_hourly.csv`.

## 2026-08-06 — Waterschap Limburg as the discharge source

Decision: Use the Waterschap Limburg public OData endpoint as the primary
discharge source, replacing the three-gauge configuration.

Evidence: the endpoint publishes 634 locations with no key -- 390 water level,
185 groundwater, 59 discharge. The previous three-gauge limit was a configuration
choice. Coverage is not confined to the Netherlands: German Lanuv gauges on the
Roer and Worm and Rijkswaterstaat gauges on the Maas are republished through the
same interface, giving cross-border and main-stem comparison for free.

Limit: the archive is a rolling window with earliest record 2024-08-06, so two
years and two winters. Longer history requires a direct request to Waterschap
Limburg, WVER, or GRDC. Groundwater from this source is 11.4 km from the site
against 2.85 km for the BRO wells, so BRO remains the groundwater source.

Source: `scripts/22_ingest_waterschap_gauges.py`;
`data/interim/waterschap_locations.csv`.

## 2026-08-06 — Gauge filter, temporal grain, and EStreams attributes

Decision: exclude managed structures from the gauge set; keep the hourly grain
with event conditioning; acquire EStreams static attributes.

Structures. Canals, dikes, weirs, culverts, inlets, distribution works, ditches
and pumping stations are excluded by name, along with any gauge carrying
sustained negative flow. A weir gauge measures a controlled release rather than a
catchment response. This takes 57 fetched gauges to 41 natural stream gauges
across 30 distinct rivers. Including structures had pushed the baseflow index
negative and flashiness to 0.780, both impossible for a natural catchment, which
is how the problem surfaced.

Temporal grain. Hourly is retained. The apparent case for daily aggregation --
median cross-river correlation of +0.025 on hourly first differences -- was an
artifact of two choices rather than of the grain: averaging over long quiet
periods, and forcing zero lag between catchments with different response times.
Conditioning on hours where both gauges exceed their own 90th percentile, and
allowing lags to plus or minus 12 hours, lifts the median to +0.243 with 773
qualifying hours per pair. Response similarity must therefore be computed on
event-window hours at best lag; the full-series zero-lag figure is the wrong
number.

EStreams. Static catchment attributes for 17,130 European catchments were
obtained without the 10 GB download: Zenodo honours HTTP range requests, so the
script reads the zip central directory from the tail and pulls only the seven
attribute tables. Matching to Waterschap gauges is bimodal -- 18 of 44 natural
gauges match at essentially zero distance, and beyond about 2 km the matches are
spurious nearest-neighbours. A 1 km tolerance is correct; wider tolerances are an
artifact of unbounded nearest-neighbour matching.

Provisional: gauged catchments only, with the ungauged framing set aside because
it is heavily worked by the global LSTM streamflow literature. This makes the
chapter a monitoring-network-design question rather than a prediction-in-ungauged-
basins question. Open with the supervisor.

Source: `docs/scope-decisions.md`; `scripts/22_ingest_waterschap_gauges.py`;
`scripts/24_fetch_estreams_attributes.py`.

## 2026-08-07 — Reset to pre-high-water recurrence and spatial transfer

Decision: replace the short-record hourly donor model as the chapter headline
with a prospective, data-gated event study of which fixed public signals recur
before high-water onset and transfer to an unseen watercourse and period.

Reasoning: the held-out hourly model was a legitimate robustness analysis but
not the chapter that follows most directly from Viefhues and Eryilmaz. Viefhues
observed the July 2021 Kerkrade response; Eryilmaz showed that public weather
explained much same-site CO2 information; the next defensible question is which
regional public components recur across events and places, and whether the CO2
residual itself recurs locally. This design can yield a substantive null without
turning the chapter into model exploration or an operational warning claim.

Locked choices: spatial transfer is primary; event contrasts and an event-window
classifier are co-primary; long-record p99 is the high-water definition; July
2021 is a required interval-censored anchor; groundwater is secondary; the
2024–2026 hourly model is robustness evidence only. Alert, false-alarm, FEWS,
causal and monitoring-placement readings are excluded.

Hard stop: do not finalise or run the prospective outcome analysis unless the
original 2020–2021 IoT package, a qualifying 10-watercourse/10-year discharge
cohort, Worm or a documented Kerkrade pair, catchment-average RADOLAN rainfall
and gauge QA pass the executable audit. The protocol remains unlocked until the
supervisor approves the question. The audit fails on the current repository;
this failure must not be resolved by reverting to the rolling two-year record.

Source: `docs/chapter-synthesis.md`,
`docs/chapter-scope-and-preregistration.md`,
`scripts/31_event_study_gates.py`.

## 2026-08-07 — Drop classification; make signal contrasts the whole chapter

Decision: remove both the planned event-window classifier and the 2024–2026
hourly transfer classifier from the live chapter. The sole analysis is now the
event-minus-quiet contrast for each fixed signal, reported as recurrence across
events/watercourses and then under crossed watercourse/time holdout.

Reasoning: classification introduced a second estimand—predictive
discrimination—and risked turning the chapter back into model comparison. The
substantive question is simpler: which signals recur before high water, and do
their direction and magnitude travel? A held-out contrast directly answers
that question without thresholds, fitted outcome models or operational
interpretation.

Transfer rule fixed before outcome inspection: for each held
watercourse-by-time-block and signal, exclude that watercourse and time block,
take the median contrast within each remaining watercourse, and use the median
of those watercourse medians as the expected direction/magnitude. Compare this
with the held-out median contrast. Report both values, signs, concordance,
magnitude difference and event counts without a success threshold.

Consequence: the hourly classifier code and its classifier-specific tests were
removed from the live tree. Eryilmaz's logistic analysis remains predecessor
context; it is not the method inherited by this chapter.

Source: `docs/chapter-synthesis.md`,
`docs/chapter-scope-and-preregistration.md`, `src/event_study.py`.

## 2026-08-07 — Remove the orphaned short-record precursor lane

Decision: delete the later-record precursor script, three-gauge soft-label
catalogue, full-period CO2 barometric baseline and their generic evaluation and
feature helpers from the live tree. Retain only the compact Eryilmaz
re-evaluation as predecessor context.

Reasoning: the precursor script read
`data/processed/signal_characterization_frame.csv`, but the exploratory script
that created that file had already been retired. The result was therefore not
regenerable from the active code. It also answered hourly discrimination rather
than the chapter's event-minus-quiet recurrence question. The three-gauge
catalogue and full-period baseline existed only to feed that lane and conflicted
with the prospective fold-specific thresholds and quiet-only, sensor-era
pressure adjustment.

Consequence: `update_data.py` now refreshes only later-era Kerkrade IoT/weather
and their QC frame. Waterschap, LANUK, RWS and DWD pulls remain explicit source
reconnaissance commands. Historical results remain in this log and Git history,
not as a robustness arm.

## 2026-08-07 — Complete the feasibility contracts before lock

Decision: add long public weather and its watercourse assignment to the hard
gate; require gauge coordinates, explicit July 2021 onset bounds and
non-overlapping provenance records for both Kerkrade sensor eras.

Reasoning: temperature, humidity and pressure were fixed primary signals but
had no long-record input contract. The held Visual Crossing points sit on an
approximately ten-year boundary and KNMI currently begins in 2020; neither had
been assigned prospectively to the future watercourse cohort. Likewise, a
distance-only donor rule cannot be reproduced without coordinates, the censored
anchor cannot be drawn without interval bounds, and pressure baselines cannot
be separated by era without timestamped era metadata. These were design holes,
not implementation details.

Consequence: the gate now expects nine contracted files, including a tidy
watercourse-weather table and provenance table, and checks ten common years
across discharge, RADOLAN and public weather. The weather source/assignment is a
supervisor decision to make before lock; it may not be chosen from event
performance. It also requires at least three later exact-onset Kerkrade-pair
events with complete primary-window CO2 and pressure. Fewer events cannot be
reported as a null recurrence result.

## 2026-08-08 — Harden comparable-period, density and holdout contracts

Decision: count feasibility episodes and storms only within the joint
discharge/RADOLAN/public-weather period; require that period to contain July
2021; open and validate the catchment GeoPackage; expose every planned
receiver-by-time-block fold; and make the held-block restriction an explicit
control-selection argument.

Draft rules pending supervisor approval: require at least 80% observed hourly
cells overall and 70% within every calendar year for each primary series; mark
a distance-selected donor pair adequate only when at least 80% of receiver
events have its level and complete 13-hour change window; mark
a transfer fold eligible with at least three held-out event contrasts and a
nonempty reference; require three eligible blocks within a receiver for a
receiver-level transfer summary.

Reasoning: endpoint span and events accumulated outside the comparable period
could previously pass the data gate despite long gaps. Empty transfer folds
were omitted rather than reported, and the most leakage-prone control rule was
left to an unavailable caller. The density values are availability rules, not
outcome thresholds, and remain changeable before lock only through an explicit
supervisor decision made without signal outcomes.

Fold-specific input contract: each contrast row must identify the held
watercourse and held block under which its thresholds, event set, controls and
quiet scaling were estimated. A single globally prepared contrast table is
rejected by the transfer summariser.

Episode rule clarified: the 72-hour merge is unbounded single-linkage. Save the
last crossing, crossing count and total chain span so an episode extending well
beyond 72 hours is visible rather than implicit.

Source: `scripts/31_event_study_gates.py`, `src/event_study.py`,
`docs/chapter-scope-and-preregistration.md`, fourth-pass review.

## 2026-08-08 — Held LANUK archive does not establish the German cohort

Decision: retain LANUK as source reconnaissance and a possible future
transboundary route, not as a qualifying primary cohort. Do not reframe the
chapter around NRW from the currently held files.

Evidence: `scripts/32_lanuk_feasibility.py` evaluates four complete ten-year
windows containing July 2021 plus the 2005–2024 RADOLAN-era window, using no
weather, rainfall, CO2 or signal contrasts. Under the draft 80% overall/70%
annual density rule and the fixed 20-episode requirement, the strongest window
contains three passing gauges representing only two verified watercourses.
Official station/HYGON metadata match 32 of 42 held gauges to 18 named
watercourses, but natural/managed status remains unverified.

Correction: official metadata assign `herzogenrath_2` to Broicher Bach and
`honsdorf` to Beeckflies. The matched Wurm gauges are `herzogenrath_1` and
`randerath`; neither has held observations during the July 2021 event window.
Their archive terminations do not themselves provide onset-censoring bounds,
and neither overlaps the later IoT era. The later complete-window events in the
held LANUK files occur on Broicher Bach or Beeckflies and cannot be relabelled
as Wurm recurrence.

Unresolved source issue: verified-discharge files use irregular timestamps,
while the available HYGON data-model note documents quarter-hour raw water
level rather than the verified discharge omission convention. Until LANUK
clarifies whether timestamps are observations, compressed changes or valid
hold-forward steps, unreported hours remain missing in the audit.

Source: `scripts/32_lanuk_feasibility.py`, `docs/lanuk-feasibility.md`, official
OpenGeodata NRW hydrological station and HYGON metadata.

## 2026-08-08 — Keep the Eryilmaz re-evaluation descriptive and calendar-honest

Decision: retain the later-record indoor-versus-public comparison only as
predecessor context. Define its expanding test folds on the full hourly
calendar before complete-case filtering, report every fold's planned dates,
coverage, positive count and longest outage, and do not report a mean AUROC gap.
Remove the randomly shuffled hourly comparison.

Reasoning: row-position folds had made a disconnected test set spanning a
159-day sensor outage look contiguous, while randomly shuffled hours placed
autocorrelated neighbours across train and test. Neither defect changes the
prospective chapter estimand, but leaving them in the sole retained contextual
analysis would invite an avoidable methodological objection.

Source: `scripts/03_eryilmaz_replication.py`, `tests/test_eryilmaz.py`, fifth-pass
review.

## 2026-08-08 — Separate the regional core from the Kerkrade CO2 case

Decision: make the six-file regional network audit the only binding data gate
for the core chapter. Treat recovery of the Viefhues IoT export, both sensor-era
records, a defensible Kerkrade hydrological pair, independently supported July
2021 local-onset bounds and three later complete CO2/pressure event windows as
a separate case-study gate.

Consequence: missing or inadequate Kerkrade inputs produce `case not available`,
not core chapter failure and not a null CO2 finding. The regional study period
must still contain July 2021, and its core figure may show observed regional
rainfall, weather and discharge. Viefhues's published observation remains the
intellectual starting point even if it cannot be reanalysed.

Reasoning: availability of a five-year-old personal sensor export should not
decide whether an otherwise qualifying ten-year regional recurrence and
transfer study exists. The split preserves the sequence without weakening the
core historical-data gate or laundering missing local evidence into a result.

Source: `scripts/31_event_study_gates.py`, draft 0.4 of
`docs/chapter-scope-and-preregistration.md`, user decision.

## 2026-08-08 — Define transferability as spatial extent

Decision: replace nearest-donor and held-out sign-concordance transfer with an
all-donor spatial-gradient estimand. At every receiver event and its matched
quiet times, evaluate each fixed signal at every other eligible watercourse.
Relate the event-minus-quiet pair contrast to `log(1 + distance_km)` in one
prespecified mixed model per signal, with receiver, donor and regional-storm
intercepts. Report the curve at empirical distance quartiles and validate its
fixed-effect magnitude at crossed held-out receiver-period intersections.

Interpretation boundary: this estimates spatial coherence over the observed
network. It is not a physical travel-time model, gauge-substitution test,
ungauged-basin prediction, maximum-reach estimate or monitoring-radius result.
A negative gradient indicates local decay; a positive contrast with little
decay indicates a broad footprint; a null spatial contrast indicates no
detectable coherence at this grain; unstable gradients indicate storm- or
watercourse-specific extent.

Availability rule, pending supervisor approval: retain all ordered
receiver-donor pairs; require complete -13 to -1 hour donor-flow windows for at
least 80% of all possible pair-event rows overall and 70% within every receiver
and empirical distance third. A draft held-out fold requires at least three
receiver events and coverage in all three distance thirds.

Repository consequence: remove the unused sign-concordance helper and its
synthetic tests, add all-pair distance and availability gates, and archive the
five dated review passes outside live `docs/`. The outcome mixed-model code is
not implemented before the core data gate passes and draft 0.5 is approved.

Source-material update: a 63 MB Viefhues thesis package is now present locally,
including a cleaned hourly August 2020–September 2021 table, raw
May–September 2021 Kerkrade files and ABC-processing code. It remains ignored
as external raw material until normalisation, provenance, calibration and
ABC-processing checks determine whether the conditional case contract passes.

Source: draft 0.5 of `docs/chapter-scope-and-preregistration.md`,
`scripts/31_event_study_gates.py`, user decision.

## 2026-08-08 — Clarify spatial decay and holdout leakage

Decision: interpret decay as a decrease in the fitted contrast's absolute
magnitude over the observed distance range, without a sign reversal. A negative
coefficient alone is not decay for a signal whose local contrast is negative.
If the curve changes sign, report the changing spatial pattern; do not label the
crossing a reach boundary.

For external validation, remove the held watercourse from training both as a
receiver and as a donor. Its out-of-block discharge may define its test p99/p95
and contamination periods, but none of its events, public signals or controls
may estimate the distance curve. Prediction in the held intersection uses fixed
effects only.

Reasoning: the original shorthand imposed rainfall's expected positive
direction on weather signals and allowed the hidden watercourse's donor values
to leak into training. Both would overstate spatial transferability.

Source: draft 0.5 of `docs/chapter-scope-and-preregistration.md`, methods
consistency review.

## 2026-08-08 — Keep routine verification scientific rather than application-wide

Decision: make `tests/` the 32-check scientific suite for event definitions,
data-gate semantics, leakage guards and the one retained predecessor analysis.
Move 18 older daily-summary and generic IoT-ingestion checks, with their
fixtures, to `infrastructure_tests/`; run them only when that legacy machinery
changes. Do not add fixture tests for the Viefhues normaliser: verify it against
the delivered source and its tidy QC output.

Also simplify `scripts/31_event_study_gates.py` to the binding six-file regional
audit. The conditional Kerkrade case remains a scientific admissibility
decision using explicit source, pair, onset and later-event evidence; optional
personal-sensor files no longer generate a parallel product-style status tree
inside the regional CLI.

Reasoning: tests are justified where a silent error would alter an estimand,
event definition or held-out comparison. Routine chapter work did not need a
53-test product surface, speculative missing-file cases or an executable
workflow for inputs that do not yet exist. The split preserves legacy coverage
without presenting application infrastructure as the chapter's analytical
core.

Source: `pyproject.toml`, `tests/`, `infrastructure_tests/`,
`scripts/31_event_study_gates.py`, user instruction.

## 2026-08-08 — Use source-native Viefhues K4 for the July anchor

Decision: normalise the delivered extended K4 CSV directly as the historical
IoT input. Treat it as the non-ABC 2021 sensor era stated by the supplied R
code, convert its labelled Europe/Amsterdam civil timestamps to UTC, average
observed minute rows by hour and never fill absent hours. Preserve 400-ppm and
5,000-ppm values while reporting their counts. Treat the longer
`cleaned_data/2021_flood_data.csv` as processed thesis output, not raw data.

Evidence: K4 contains 169,594 rows from 2021-05-15 12:43 CEST through
2021-09-24 07:28 CEST and all 744 July civil-time hours. The hourly output has
2,829 observed hours, with 335 absent hours elsewhere in its span, 83 minute
values at 400 ppm and 5,761 at the 5,000-ppm ceiling. The cleaned thesis table
has 1,333 absent civil-time hours, a duplicate 2020-10-25 02:00 row and only
550 July hours. After 15 May its CO2/pressure values are almost entirely K4
hourly means. Before May, the supplied R scripts depend on
`kerkrade3tillJune1.csv`, `kerkrade4tillJune1.csv`, `metadata.json` and
`total_Dataset_with_adjusted_ABC.csv`, none of which is present in the folder
or ZIP.

Consequence: the observed July K4 trajectory is reproducible, but the broader
sensor-era provenance is not. K3's `livingroom` filename conflicts with the
thesis statement that both sensors were in the basement; sensor model/serial,
calibration history, exact ABC-repair rows, 450-ppm correction rationale and
reuse terms still require targeted follow-up. These gaps can remove the
conditional CO2 recurrence case but do not block the regional chapter.

Source: `scripts/33_ingest_viefhues_iot.py`, the locally delivered thesis PDF,
raw CSVs and R scripts.

## 2026-08-10 — Replace the literature scaffold with a verified source corpus

Decision: make `docs/literature-source-notes.md`,
`docs/literature-evidence-matrix.csv` and `docs/chapter-references.bib` the only
live literature artifacts. Organize the search with 22 evidence questions and
retain sources because they directly address those questions or are canonical
references for the underlying event, spatial-extremes or measurement method.
The anticipated source count is not a quota. Record each source independently;
do not add an integrated literature argument, aggregate support score, novelty
claim or drafted chapter prose.

Retain the original Viefhues and Eryilmaz PDFs. Remove the superseded
predecessor notes after incorporating their verified facts, along with the old
How-To files, generated source corpus, scaffold bundles, feasibility reports
and legacy bibliography. Git history is the archive.

Reasoning: the prior materials mixed live evidence with obsolete model choices
and AI-generated scaffolding. A question-to-source matrix makes inclusion and
scope inspectable while leaving cross-source analysis and chapter writing to
the student. Canonical references remain necessary where later case studies
apply rather than replace their event-sampling, dependence or measurement
foundations.

Source: `docs/literature-source-notes.md`,
`docs/literature-evidence-matrix.csv`, `docs/chapter-references.bib`, user
instruction.

## 2026-08-10 — Record the supervisor response without overstating approval

Decision: treat the contribution, spatial-extent meaning, natural Limburg
tributary population, July 2021 regional anchor and conditional Kerkrade case
as approved. The supervisor provisionally accepts three held-out receiver
events. The 10-watercourse/10-year/20-episode/40-storm floor, the 80%/70%
coverage rules and the clarified distance-third support rule remain open.

Reasoning: the numerical floors are prospective design judgements, not accepted
hydrological standards and not values learned from signal outcomes. Before
outcome inspection, use a blinded availability audit at 70%, 80% and 90% to
show the consequences of alternative coverage rules; then obtain and freeze a
supervisor decision. Do not use “adjust if needed” as permission for
post-result tuning.

Source: student-reported supervisor responses;
`docs/supervisor-decision-memo.md`; protocol draft 0.6.

## 2026-08-10 — Use ERA5-Land primary weather and long KNMI sensitivity

Decision: acquire ERA5-Land 2 m temperature, 2 m dew-point temperature and
surface pressure for 2001–2025 over 50.5–52.0° N, 5.0–6.7° E. After catchments
are verified, assign the nearest 0.1° cell to each catchment centroid and
derive relative humidity from temperature and dew point. Use validated KNMI
hourly Maastricht, Ell and Arcen observations over the same period as the
observational sensitivity. Keep Visual Crossing only for the Eryilmaz
predecessor comparison.

Reasoning: ERA5-Land gives a fixed hourly cross-border field; KNMI provides an
observed check without pretending that sparse stations are catchment-level
weather. The source choice was approved before prospective event contrasts.
The ERA5 fetch is reproducible but currently cannot submit because the local
CDS token/licence setup is absent. The KNMI source files and normalized table
have been acquired; validated pressure is available only at Maastricht.

Source: student-reported supervisor approval; Copernicus ERA5-Land dataset DOI
`10.24381/cds.e2161bac`; KNMI validated hourly archive;
`scripts/34_fetch_era5_land.py`; `scripts/35_ingest_knmi_validated.py`.
