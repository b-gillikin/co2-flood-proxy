# Scripts

Numbered, runnable analysis steps. Each writes to `data/` or `results/` and can
be run on its own; the numbering is dependency order, not a schedule.

Retired scripts moved to `archive/scripts/` on 2026-08-05. See `archive/README.md`
for what each did and `docs/chapter-direction.md` for the reframing.

## Data collection

Run these first, or run `update_data.py` which chains them.

| Script | Purpose |
| --- | --- |
| `update_data.py` | Refresh all sources, rebuild the event catalogue, and run the coverage QC pass |
| `01_ingest_iot.py` | Sync Kerkrade IoT blobs, merge local Blynk exports from `iot-device-data/`, build hourly IoT data plus source and gap reports |
| `02_ingest_weather.py` | Sync Visual Crossing weather blobs and catch up the current month |
| `01_ingest_discharge.py` | Sync Wurm and Geul tributary gauges into hourly discharge |
| `04_ingest_knmi.py` | Normalize KNMI reference meteorology and compare against Visual Crossing |
| `04_sync_knmi_azure.py` | Pull Azure-collected KNMI station-slim blobs into local raw storage |
| `05a_fetch_bro_groundwater.py` | Fetch groundwater dossiers from the public BRO service; no credentials needed |
| `05_ingest_groundwater.py` | Normalize delivered groundwater to observed series-days without interpolation |

`04_ingest_knmi.py` defaults to `data/raw/knmi`, which holds NetCDF requiring
xarray. Pass `--raw-dir data/raw/knmi/azure_slim` to rebuild from the slim CSVs
alone.

## Frame assembly

| Script | Purpose |
| --- | --- |
| `01_eda.py` | Join sources into `data/interim/analysis_hourly.csv` and write coverage QC plots |
| `03_build_event_catalogue.py` | Discharge thresholds, sustained high-flow events, hourly soft labels |
| `02_barometric_baseline.py` | Fit the pressure-only CO2 baseline and write the barometric residual |
| `04_signal_characterization.py` | Assemble the signal frame; exploratory residual structure |

`02_barometric_baseline.py` produces the chapter's central instrument. Everything
downstream consumes `co2_residual_barometric_ppm`.

## Analysis

| Script | Purpose |
| --- | --- |
| `18_precursor_skill.py` | **Main result.** AUROC of CO2, pressure and rainfall predictors for high-flow onset, with block-bootstrap intervals and false-alarm rates |
| `05b_barometric_efficiency.py` | Well barometric efficiency and the shared-pressure confound |
| `05c_groundwater_event_lag.py` | Whether groundwater leads or lags tributary events |
| `12_distributed_lag.py` | Antecedent-wetness distributed-lag boundary test |
| `03_eryilmaz_replication.py` | Inherited logistic-regression comparison, reported as replication only |
| `05_sarimax.py` | SARIMAX residual-structure diagnostic |
| `06_kalman.py` | Local-level state-space baseline for the drifting indoor level |

`05_sarimax.py` and `06_kalman.py` are retained as diagnostics, not detectors.
SARIMAX establishes that the residual is serially correlated, which is what
justifies autocorrelation-robust standard errors elsewhere.

## Monitoring

| Script | Purpose |
| --- | --- |
| `14_weekly_readiness.py` | Append a coverage row: latest timestamps, observed shares, longest contiguous block |

## Conventions

- Hourly UTC throughout. Local times are resolved at ingestion, never later.
- Coverage gaps are never interpolated, and a row on the hourly grid is not an
  observation. Anything counting coverage must count observed values.
- Contiguous blocks break at any gap over one hour, so a "block" is a run with
  no missing hours, not merely a date range.
