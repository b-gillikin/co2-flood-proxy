# Methods Outline

> **Superseded 2026-08-06.** Written against the previous research question.
> The ensemble anomaly-detection methods outlined here (SARIMAX/Kalman/Isolation
> Forest detectors, cross-detector agreement, synthetic injection,
> rolling-origin detector evaluation) are retired. Pressure decomposition,
> local-level state-space modelling, and gap-honest coverage accounting carry
> forward. See `docs/chapter-direction.md`.

Date: 2026-06-21

Purpose: scaffold the chapter methods section around the reproducible scripts
already in the repository. This is a writing aid, not final prose.

Canonical completion and freeze criteria live in
`docs/chapter-readiness-plan.md`. The chapter asks whether pressure-separated
CO2 observations contain reproducible information about directly measured
antecedent hydrological state; it does not assume that relationship exists.

## Data Provenance and Alignment

- Kerkrade low-cost IoT CO2, temperature, humidity, pressure, and particulate
  measurements are sourced from Azure daily CSV blobs plus local Blynk exports,
  then normalized to hourly UTC in `data/interim/iot_hourly.csv`.
- Visual Crossing meteorology and air-quality fields are sourced from cached
  Azure weather blobs and normalized to hourly UTC in `data/interim/weather_hourly.csv`.
- Wurm and Geul discharge sources produce hourly soft labels and event
  catalogues in `data/processed/hourly_soft_labels.csv` and
  `data/processed/event_catalogue.csv`.
- KNMI reference meteorology uses a curated Dutch Meuse/Maas station set. Azure
  backfills compact station-slim monthly blobs from the present backward toward
  2020, and `scripts/04_sync_knmi_azure.py` brings those blobs into local
  `data/interim/knmi_hourly.csv` and `data/interim/knmi_hourly.parquet`.
- RIVM/Luchtmeetnet stations `NL10136` and `NL10138` are the first transfer
  lane for the August v1 dry run.

## Pressure Decomposition

- Script: `scripts/02_barometric_baseline.py`.
- Target: `iot_co2_ppm`.
- Official formula: `CO2 ~ pressure + delta_pressure_1h + delta_pressure_3h
  + delta_pressure_6h + delta_pressure_12h + delta_pressure_24h`.
- Official Week 2 value after local Blynk export merge: linear IoT-pressure
  R2 = 0.430628.
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
- Current July detector outputs are provisional because the IoT record is gappy,
  but the official 30-day train / 7-day evaluation windows are now runnable on
  the merged frame.

## Evaluation Protocol

- Official scheme: 30-day training window followed by 7-day evaluation window.
- Current implementation writes an insufficiency check when the record is too
  short; after the Blynk export merge, the official scheme is ready.
- Smoke windows validate the pipeline only and should not be written as final
  evaluation evidence.
- Event-window tests compare anomaly rates in 72-hour antecedent windows against
  preceding 72-hour control windows.
- Rolling outputs carry a deterministic run ID, data cutoff, fit status, and
  scored-hour count. Warning-only non-converged fits are not treated as valid
  detector results.
- Ensemble agreement is calculated on common scored coverage. Unscored hours
  remain explicitly unavailable rather than being counted as non-anomalies.

## Direct Groundwater/Mine-Water Test

- Data receipt and normalization follow `docs/groundwater-data-contract.md`.
- Source-native files are immutable. Daily normalization averages only observed,
  usable readings and never interpolates missing dates.
- Source values are retained while an oriented `hydrologic_level` makes larger
  values consistently mean higher water, including depth-below-surface series.
- Select the primary state series before modelling using the hierarchy in the
  readiness plan.
- Aggregate the pressure-separated residual and state series to UTC days with at
  least 18 observed IoT hours.
- Fit the locked daily residual model with KNMI temperature, humidity, pressure,
  and block fixed effects.
- Use HAC standard errors with a 14-day maximum lag and a 28-day moving-block
  bootstrap.
- Require p < 0.05, a bootstrap interval excluding zero, same-sign replication
  in at least two blocks, and a null future-water placebo.
- Treat 1/3/7/14-day lags, water-level changes, and alternative wells as
  FDR-controlled sensitivities.
- The future-water placebo uses a locked seven-day lead. The executable method
  is `scripts/16_direct_state.py`; fixture outcomes validate software only.

## Distributed-Lag Boundary Test

- Script: `scripts/12_distributed_lag.py`.
- The current precipitation-based 10-day result is `NOT SUPPORTED`: the primary
  coefficient is not significant, its bootstrap interval includes zero, block
  replication is unavailable, and the future-rain placebo fails.
- Rerun the unchanged rule on the frozen snapshot. Do not use the exploratory
  Week 4 lag peak as evidence independently of this test.

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

- Groundwater/mine-water collection is in process. Integration waits for source
  provenance and the locked normalization/selection rules.
- SMAP live acquisition remains deferred.
- IRCEL-CELINE and LANUV NRW remain discovery-first transfer lanes.
