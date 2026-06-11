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

Planned analysis scripts:

- `04_signal_characterization.py`
