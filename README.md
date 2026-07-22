# Chapter 1 CO2

Working repository for the dissertation chapter testing antecedent-state signal in low-cost IoT data at the Kerkrade post-mining calibration site.

**Research question**: After atmospheric-pressure effects are separated, do low-cost CO2 observations at the Kerkrade post-mining site contain reproducible information about directly measured antecedent hydrological state?

The current evidence supports a pressure-separable residual and a reproducible analysis pipeline, but it does not yet establish the hydrological mechanism. The chapter permits a supported, site-specific/data-limited, or null/boundary outcome depending on the frozen direct-state analysis.

**Methodological frame**: Ensemble time-series anomaly detection and signal decomposition, using pressure-tendency regression, SARIMAX residuals, Kalman innovations, Isolation Forest scores, and transfer-site stress tests.

**Empirical window**: Primary synchronized analysis uses the Kerkrade IoT/weather/discharge overlap, currently expected to begin in January 2025. Where longer discharge, groundwater, weather, or transfer-site records are available, pull the longer history for context, event thresholds, seasonality checks, and baseline characterization.

**Predecessor work**: Viefhues 2022 and Eryilmaz 2025, as summarized in `chapter-prework/Lit-scaffold - chapter draft.docx` and operationalized in `chapter-prework/June 2026 - How-To.docx`.

**Readiness plan**: `docs/chapter-readiness-plan.md` is the canonical record for work that can proceed now, incoming-data gates, the September/October freeze decision, final analysis, and remaining chapter sections. Cross-site transfer is secondary and cannot block chapter completion.

## How to Reproduce

1. Create the environment:

   ```bash
   conda env create -f environment.yml
   conda activate chapter1-co2
   export MPLCONFIGDIR="$PWD/.matplotlib"
   ```

   If the environment already exists, update it after pulling dependency
   changes:

   ```bash
   conda env update -f environment.yml --prune
   ```

2. Bring available source data up to date:

   ```bash
   python scripts/update_data.py
   ```

   The IoT and weather refreshes use your Azure CLI login to read the Kerkrade
   production storage containers. Weather also performs a direct Kerkrade
   Visual Crossing catch-up for the current month when downloads are enabled.
   To rebuild cleaned outputs from already downloaded raw files, run:

   ```bash
   python scripts/update_data.py --skip-download
   ```

   Local Blynk device exports placed in `iot-device-data/` are merged into the
   hourly IoT frame by default. That folder is ignored by git because it holds
   raw exports; the normalized source and gap reports are written to
   `data/processed/iot_source_summary.csv` and
   `data/processed/iot_coverage_gaps.csv`.

3. Run analysis scripts in order from `scripts/`.

   Week 2 barometric baseline and Kill Check 1:

   ```bash
   python scripts/02_barometric_baseline.py
   ```

   Week 3 Eryilmaz replication and Kill Check 2:

   ```bash
   python scripts/03_eryilmaz_replication.py
   ```

   Week 4 signal characterization:

   ```bash
   python scripts/04_signal_characterization.py
   ```

   Week 4 reference/transfer data starters:

   ```bash
   python scripts/04_ingest_knmi.py --skip-download
   python scripts/04_ingest_rivm.py --skip-download
   ```

   For live KNMI downloads, request an Open Data API key from the
   [KNMI Developer Portal](https://developer.dataplatform.knmi.nl/): register,
   open the API Catalogue, request an Open Data API key, then run:

   ```bash
   export KNMI_API_KEY="your-key"
   python scripts/04_ingest_knmi.py
   ```

   RIVM/Luchtmeetnet does not require an API key; its public API uses a
   fair-use limit. If the live API is unavailable, use the official data-portal
   fallback:

   ```bash
   python scripts/04_ingest_rivm.py --use-portal
   ```

   See `docs/knmi-sources.md` for the KNMI landing zone,
   `docs/rivm-transfer-sources.md` for the RIVM transfer lane, and
   `docs/week4-signal-interpretation.md` for the current Week 4 readout.

   KNMI historical backfill should run in Azure for long unattended pulls:

   ```bash
   cd kerkrade_data
   export SUBSCRIPTION_ID="<subscription-id>"
   export RESOURCE_GROUP="<resource-group>"
   export LOCATION="eastus"
   export STORAGE_ACCOUNT="<globally-unique-storage-account>"
   export FUNCTION_APP="<globally-unique-function-app>"
   export KNMI_API_KEY="your-key"
   bash azure/deploy_knmi_function.sh
   cd ..
   ```

   The Azure collector keeps broad KNMI variables only for the selected
   Meuse/Maas stations, writing compact monthly gzip CSV blobs. It does not
   persist the full all-station NetCDF archive unless `KNMI_KEEP_RAW=true` is
   explicitly set.

   To bring those Azure-collected slim blobs back into the local analysis
   cache and rebuild KNMI hourly outputs, run:

   ```bash
   python scripts/04_sync_knmi_azure.py
   ```

   The local KNMI ingest writes `data/interim/knmi_hourly.csv` for compatibility
   and `data/interim/knmi_hourly.parquet` as the preferred typed, compressed
   analysis table.

   A local launchd fallback can still run hourly while the laptop is awake:

   ```bash
   scripts/run_knmi_hourly_job.sh
   ```

   The `ops/com.briangillikin.chapter1-co2.knmi.plist` launchd job runs that
   wrapper, but Azure is the preferred collector after the local macOS
   permission failures.

   July provisional anomaly models:

   ```bash
   python scripts/15_run_analysis_pipeline.py
   ```

   This command runs the actual 05-12 entry points in order, including the
   secondary transfer dry run, and writes `results/run_manifest.json`. Before
   every step it removes that step's prior artifacts, so a failed or skipped
   replacement cannot leave a stale output looking current. For the final
   immutable snapshot, commit the code first and add `--freeze`; frozen mode
   refuses dirty code, missing or changed inputs, mixed snapshot IDs,
   unrecorded outputs, failed commands, and non-converged models.
   If shared-feature coverage is inadequate, add `--skip-transfer`; transfer is
   secondary and this omission does not invalidate the core frozen run.

   `05_sarimax.py` uses a compact nonseasonal SARIMAX search, then tests daily
   seasonality only after a base fit converges. Use
   `python scripts/05_sarimax.py --full-grid` for the full p,q in 0..2 search.
   SARIMAX and the local-level model use only standardized IoT temperature and
   relative humidity controls; pressure is not reintroduced after pressure
   separation. If a state-space optimizer does not converge, the saved family
   is named explicitly as `arx` or `ridge_local_level`.

   Full-record fitting, synthetic injection, and rolling-origin evaluation all
   use the versioned specification in `src/detectors.py`. Scripts 09 and 10
   reject legacy model pickles rather than silently substituting a different
   family or feature set.

   Optional features are admitted by accumulated complete-case coverage in
   `src/models/july.py`: they must preserve at least 90% of the required rows
   overall and within every material contiguous block. Each detector writes
   `results/<detector>/feature_coverage.csv` where applicable. Detector anomaly
   files carry native `<detector>_scored` columns; ensemble output distinguishes
   `unscored`, `partial`, and `common` coverage and computes agreement only
   on common scored hours.

   These July outputs are pipeline-first on the current gappy IoT/residual
   record. The official 30-day train / 7-day evaluation windows are now
   runnable, but interpretation remains provisional until IoT continuity and
   KNMI coverage improve. Rerun the same commands unchanged after more data are
   added.

   `12_distributed_lag.py` is the locked precipitation/discharge boundary test.
   Its current 10-day antecedent-wetness outcome is `NOT SUPPORTED`; retain the
   unchanged decision rule for the frozen-data rerun.

   August v1 transfer dry run and writing scaffold:

   ```bash
   python scripts/11_transfer_stress_test.py
   ```

   This trains Kerkrade detector-surrogate models and applies them to the
   cached RIVM/Luchtmeetnet South Limburg lane using KNMI station `06380`
   Maastricht Airport meteorology where available. The broader KNMI cache keeps
   the selected Meuse/Maas station set for future basin analysis. The outputs
   are explicitly provisional and are not official transfer interpretation.

4. Write intermediate data to `data/interim/`, processed analysis products to `data/processed/`, and figures/tables/model artifacts to `results/`. Use Parquet for larger normalized analytical tables when practical, with CSV mirrors retained for small summaries, reviewable outputs, and existing script compatibility.

Week 1 EDA/QC outputs are regenerated by the update command:

- `data/interim/analysis_hourly.csv`
- `data/processed/iot_source_summary.csv`
- `data/processed/iot_coverage_gaps.csv`
- `data/processed/week1_eda_summary.csv`
- `results/eda/*.png`

Week 2 baseline outputs are generated by `scripts/02_barometric_baseline.py`:

- `data/processed/co2-residual-barometric.csv`
- `results/baseline/r2.txt`
- `results/baseline/co2_fit_residual.png`

Week 3 replication outputs are generated by `scripts/03_eryilmaz_replication.py`:

- `data/processed/eryilmaz_replication_predictions.csv`
- `results/eryilmaz/auroc.txt`
- `results/eryilmaz/roc_curves.png`

Week 4 signal outputs are generated by `scripts/04_signal_characterization.py`:

- `data/processed/signal_characterization_frame.csv`
- `results/signal/*.csv`
- `results/signal/*.png`
- `results/signal/summary.txt`

Week 4 reference/transfer starters write:

- `data/interim/knmi_hourly.csv`
- `data/interim/knmi_hourly.parquet`
- `results/knmi/*`
- `data/interim/rivm_hourly.csv`
- `results/rivm/*`

July provisional modelling outputs write:

- `results/models/sarimax.pkl`
- `results/models/sarimax_order_search.csv`
- `data/processed/sarimax-residuals.csv`
- `data/processed/sarimax-anomalies.csv`
- `results/models/kalman.pkl`
- `data/processed/kalman-innovations.csv`
- `data/processed/kalman-anomalies.csv`
- `results/models/iforest.pkl`
- `data/processed/iforest-scores.csv`
- `data/processed/iforest-anomalies.csv`
- `data/processed/ensemble_anomaly_flags.csv`
- `results/ensemble/*`
- `results/synthetic_injection/*`
- `data/processed/api.csv`
- `results/evaluation/*`

August v1 transfer and writing outputs:

- `results/models/*-transfer.pkl`
- `data/processed/transfer-anomalies/*.csv`
- `data/processed/events-transfer-*.csv`
- `results/transfer/*`
- `results/figures/figure_manifest.csv`
- `docs/august-readiness.md`
- `docs/figure-inventory.md`
- `docs/methods-outline.md`
- `docs/results-outline.md`

Frozen-run provenance and boundary-test outputs:

- `results/distributed_lag/summary.txt`
- `results/distributed_lag/timescale_scan.csv`
- `results/run_manifest.json`
- `results/run_logs/*.log`

## Structure

- `chapter-prework/`: scaffold documents, monthly how-to docs, bibliography, and source/corpus materials.
- `data/raw/`: source-format raw downloads, refreshed by ingestion scripts.
- `data/interim/`: cleaned and time-aligned data.
- `data/processed/`: feature sets, residual series, event catalogues, anomaly scores, and evaluation outputs.
- `scripts/`: numbered runnable analysis scripts.
- `ops/`: local operational helpers such as launchd job definitions.
- `src/`: reusable importable code used by the scripts. `src/io_data.py` is the
  stable loader facade; source-family implementations live in `src/io_iot.py`,
  `src/io_weather.py`, `src/io_discharge.py`, `src/io_knmi.py`, and
  `src/io_rivm.py`.
- `results/`: generated figures, tables, and model artifacts.
- `docs/`: decisions log, data-request tracking, predecessor notes, and chapter-facing working notes.
