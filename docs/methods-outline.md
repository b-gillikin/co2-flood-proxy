# Methods Outline

Date: 2026-06-21

Purpose: scaffold the chapter methods section around the reproducible scripts
already in the repository. This is a writing aid, not final prose.

## Data Provenance and Alignment

- Kerkrade low-cost IoT CO2, temperature, humidity, pressure, and particulate
  measurements are sourced from Azure daily CSV blobs and normalized to hourly
  UTC in `data/interim/iot_hourly.csv`.
- Visual Crossing meteorology and air-quality fields are sourced from cached
  Azure weather blobs and normalized to hourly UTC in `data/interim/weather_hourly.csv`.
- Wurm and Geul discharge sources produce hourly soft labels and event
  catalogues in `data/processed/hourly_soft_labels.csv` and
  `data/processed/event_catalogue.csv`.
- KNMI reference meteorology uses a curated Dutch Meuse/Maas station set, with
  station `06380` Maastricht Airport retained as the primary Kerkrade
  comparison station; historical backfill is still running.
- RIVM/Luchtmeetnet stations `NL10136` and `NL10138` are the first transfer
  lane for the August v1 dry run.

## Pressure Decomposition

- Script: `scripts/02_barometric_baseline.py`.
- Target: `iot_co2_ppm`.
- Official formula: `CO2 ~ pressure + delta_pressure_1h + delta_pressure_3h
  + delta_pressure_6h + delta_pressure_12h + delta_pressure_24h`.
- Official Week 2 value: linear IoT-pressure R2 = 0.593641.
- Output residual: `data/processed/co2-residual-barometric.csv`.

## Eryilmaz Replication

- Script: `scripts/03_eryilmaz_replication.py`.
- Target: `iot_co2_ppm > 1000`.
- Model A: indoor IoT temperature, humidity, pressure, and 6-hour pressure
  tendency.
- Model B: outdoor Visual Crossing temperature, humidity, pressure, and 6-hour
  pressure tendency.
- Random stratified 5-fold CV is used only for replication of the predecessor
  design, not for later time-series evaluation.

## Signal Characterization

- Script: `scripts/04_signal_characterization.py`.
- Residual structure is explored with lagged correlations, random-forest
  feature scans, hydrological soft-label association checks, and PCA.
- These outputs are exploratory because the current residual window is short.

## July Detector Models

- SARIMAX-family first pass: `scripts/05_sarimax.py`.
- Kalman innovations: `scripts/06_kalman.py`.
- Isolation Forest: `scripts/07_isolation_forest.py`.
- Ensemble agreement: `scripts/08_ensemble_agreement.py`.
- Synthetic injection smoke tests: `scripts/09_synthetic_injection.py`.
- Evaluation and API baseline: `scripts/10_evaluation.py`.
- Current July detector outputs are provisional until more Kerkrade IoT and KNMI
  data are available.

## Evaluation Protocol

- Official scheme: 30-day training window followed by 7-day evaluation window.
- Current implementation writes an insufficiency check when the record is too
  short.
- Smoke windows validate the pipeline only and should not be written as final
  evaluation evidence.
- Event-window tests compare anomaly rates in 72-hour antecedent windows against
  preceding 72-hour control windows.

## Transfer Preregistration and August v1

- Preregistration: `docs/transfer-experiment-preregistration.md`.
- August v1 script: `scripts/11_transfer_stress_test.py`.
- Training site: Kerkrade.
- Dry-run transfer sites: Heerlen `NL10136` and `NL10138`.
- Transfer surrogates use `StandardScaler + LogisticRegression` with balanced
  class weights and no random k-fold CV.
- August v1 is a RIVM-only dry run plus writing scaffold, not official transfer
  interpretation.

## Deferred Inputs

- Groundwater remains pending until requested data arrive and are documented in
  `docs/data-requests.md`.
- SMAP live acquisition remains deferred.
- IRCEL-CELINE and LANUV NRW remain discovery-first transfer lanes.
