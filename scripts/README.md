# Scripts

Run scripts from the repository root. Each script should import reusable logic from `src/`.

Routine refresh:

- `update_data.py` — bring available raw/interim data sources up to date, rebuild the event catalogue, and run the Week 1 EDA/QC pass.

June ingestion scripts:

- `01_ingest_iot.py` — Task 1.1, sync Kerkrade IoT CSV blobs and build hourly IoT data.
- `02_ingest_weather.py` — Task 1.2, sync Visual Crossing weather blobs, catch up current Kerkrade weather directly from Visual Crossing, and build hourly weather data.
- `01_ingest_discharge.py` — Task 1.3, sync public discharge sources and build hourly discharge data.
- `03_build_event_catalogue.py` — Task 1.4, build discharge thresholds, sustained events, and hourly soft labels.
- `01_eda.py` — Week 1 cleanup, build joined hourly analysis data and QC plots.
- `02_barometric_baseline.py` — Week 2, compute pressure-tendency features, fit the pressure-only CO2 baseline, save residuals, and report Kill Check 1.
- `03_eryilmaz_replication.py` — Week 3, reproduce Eryilmaz's two logistic-regression models and report Kill Check 2.
- `04_signal_characterization.py` — Week 4, characterize the barometric residual with lagged correlations, exploratory random forests, and PCA.
- `04_ingest_knmi.py` — Week 4, cache/load KNMI reference meteorology and compare it against Kerkrade Visual Crossing pressure/temp.
- `04_ingest_rivm.py` — Week 4, cache/load starter RIVM/Luchtmeetnet transfer-site measurements. Use `--use-portal` when the live API is unavailable.

Week 4 external data notes:

- KNMI live downloads require `KNMI_API_KEY`. Get it from the KNMI Developer Portal API Catalogue, then run `export KNMI_API_KEY="your-key"`.
- RIVM/Luchtmeetnet is public and does not need a key; use fair-use pacing and cached raw payloads when the service is unavailable.
