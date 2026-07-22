# Scripts

Run scripts from the repository root. Each script should import public data
loaders from `src.io_data`; source-specific parser implementations live in
`src/io_iot.py`, `src/io_weather.py`, `src/io_discharge.py`, `src/io_knmi.py`,
`src/io_rivm.py`, and `src/io_groundwater.py`.

Routine refresh:

- `update_data.py` — bring available raw/interim data sources up to date, rebuild the event catalogue, and run the Week 1 EDA/QC pass.

June ingestion scripts:

- `01_ingest_iot.py` — Task 1.1, sync Kerkrade IoT CSV blobs, merge local Blynk exports from `iot-device-data/` when present, and build hourly IoT data plus source/gap reports.
- `02_ingest_weather.py` — Task 1.2, sync Visual Crossing weather blobs, catch up current Kerkrade weather directly from Visual Crossing, and build hourly weather data.
- `01_ingest_discharge.py` — Task 1.3, sync public discharge sources and build hourly discharge data.
- `03_build_event_catalogue.py` — Task 1.4, build discharge thresholds, sustained events, and hourly soft labels.
- `01_eda.py` — Week 1 cleanup, build joined hourly analysis data and QC plots.
- `02_barometric_baseline.py` — Week 2, compute pressure-tendency features, fit the pressure-only CO2 baseline, save residuals, and report Kill Check 1.
- `03_eryilmaz_replication.py` — Week 3, reproduce Eryilmaz's two logistic-regression models and report Kill Check 2.
- `04_signal_characterization.py` — Week 4, characterize the barometric residual with lagged correlations, exploratory random forests, and PCA.
- `04_ingest_knmi.py` — Week 4, cache/load KNMI reference meteorology and compare it against Kerkrade Visual Crossing pressure/temp.
- `04_sync_knmi_azure.py` — Week 4/Azure bridge, download Azure-collected KNMI station-slim blobs into local raw storage and rebuild the hourly KNMI table.
- `04_ingest_rivm.py` — Week 4, cache/load starter RIVM/Luchtmeetnet transfer-site measurements. Use `--use-portal` when the live API is unavailable.
- `05_ingest_groundwater.py` — validate delivered direct-state metadata and normalize source readings to observed UTC series-days without interpolation.

Week 4 external data notes:

- Local Blynk exports are treated as raw local data and are ignored by git.
  Use `python scripts/01_ingest_iot.py --skip-download` to rebuild the merged
  hourly IoT frame from Azure raw files plus `iot-device-data/`. Add
  `--skip-exports` for an Azure-only rebuild.
- KNMI live downloads require `KNMI_API_KEY`. Get it from the KNMI Developer Portal API Catalogue, then run `export KNMI_API_KEY="your-key"`.
- For long KNMI historical backfills, deploy the Azure Timer Function from
  `kerkrade_data/azure/deploy_knmi_function.sh`. The Azure collector keeps
  broad variables for the selected Meuse/Maas stations as compact monthly gzip
  CSV blobs and discards full raw NetCDF files by default.
- Pull Azure-collected KNMI blobs back down with
  `python scripts/04_sync_knmi_azure.py`. This writes local raw slim blobs under
  `data/raw/knmi/azure_slim/` and rebuilds both `data/interim/knmi_hourly.csv`
  and `data/interim/knmi_hourly.parquet`.
- `run_knmi_hourly_job.sh` runs a bounded KNMI historical backfill and rebuilds the selected Meuse/Maas station-hour `knmi_hourly.csv`. It is intended for the launchd job in `ops/com.briangillikin.chapter1-co2.knmi.plist`.
- RIVM/Luchtmeetnet is public and does not need a key; use fair-use pacing and cached raw payloads when the service is unavailable.

Data format policy:

- Keep raw/source files in source-native form unless storage is genuinely wasteful.
- Prefer Parquet for larger normalized analysis tables because it preserves dtypes
  and compresses well.
- Keep CSV mirrors for small summaries, human inspection, and compatibility with
  existing scripts.

July provisional modelling scripts:

- `05_sarimax.py` — Week 1, run the first SARIMAX-family residual model, stationarity/transform logging, order search, residuals, and anomaly flags.
- `06_kalman.py` — Week 2, run local-level Kalman innovations on the barometric residual with exogenous regressors.
- `07_isolation_forest.py` — Week 3, fit the official provisional Isolation Forest flag and 0.03/0.05/0.10 contamination sensitivity outputs.
- `08_ensemble_agreement.py` — Week 3, align SARIMAX/Kalman/Isolation Forest anomaly flags and summarize detector agreement.
- `09_synthetic_injection.py` — Week 3, run Gaussian-burst and CutAddPaste synthetic anomaly smoke tests.
- `10_evaluation.py` — Week 4, write the official 30-day/7-day evaluation-window check, provisional smoke-window summaries, event-window tests, and Kerkrade API baseline.
- `11_transfer_stress_test.py` — August v1, train Kerkrade detector-surrogate classifiers, run the cached RIVM/KNMI South Limburg transfer dry run, and write writing/figure scaffolding outputs.
- `12_distributed_lag.py` — locked precipitation/discharge distributed-lag boundary test with HAC inference, moving-block bootstrap, block replication, and future-rain placebo.
- `13_write_run_manifest.py` — inspect or freeze-validate an existing schema-v2 manifest; it refuses legacy manifests that only list intended commands.
- `14_weekly_readiness.py` — compute IoT/KNMI/groundwater/window coverage and optionally append a dated row to the canonical readiness plan without duplicating that date.
- `15_run_analysis_pipeline.py` — execute core modelling, available direct state, and optional transfer offline; invalidate step-owned outputs; record an execution ledger; and write the schema-v2 snapshot manifest.
- `16_direct_state.py` — run the locked groundwater/mine-water primary model, HAC and moving-block uncertainty, block replication, future-water placebo, and FDR sensitivities.

Verified offline run order for July/August modelling:

```bash
python scripts/15_run_analysis_pipeline.py
```

The runner invokes scripts 05, 06, 07, 08, 09, 10, 11, and 12 as separate
Python processes and automatically adds script 16 when both normalized
groundwater files are present. Use `--skip-rolling` only for a development rehearsal. After
the data freeze and a clean code commit, use `--freeze`; the command refuses a
dirty or unknown Git state and validates input snapshot IDs, successful command
records, recreated output hashes, and model convergence. The compatibility
check is `python scripts/13_write_run_manifest.py --freeze`. When shared-feature
coverage is inadequate, add `--skip-transfer`; this omits only secondary script
11 and cannot block the core chapter run.

For a frozen run, missing direct-state data is an error unless
`--direct-state omit` is supplied explicitly for the prespecified data-limited
outcome. Use `--direct-state required` during receipt/analysis checks.

`05_sarimax.py` uses a compact default SARIMAX search for routine reruns. Add
`--full-grid` when you want the full p,q in 0..2 order search.

Standalone August v1 dry run:

```bash
python scripts/11_transfer_stress_test.py
```

The August script is intentionally provisional. It reports feature availability,
label fallbacks, and RIVM dry-run scores, but does not interpret transfer
success or failure.

Transfer is secondary under `docs/chapter-readiness-plan.md` and cannot block
chapter completion. On the frozen snapshot, run the transfer dry run after the
core Kerkrade/direct-state analyses and before the final manifest only when
shared-feature coverage is adequate.

Weekly collection monitoring should not rerun the scientific interpretation:

```bash
python scripts/14_weekly_readiness.py --append-plan
```
