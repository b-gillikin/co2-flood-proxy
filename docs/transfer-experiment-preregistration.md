# Transfer Experiment Preregistration

Date: 2026-06-17

## Purpose

This note preregisters the first transfer experiment before applying Kerkrade anomaly models to transfer-site data.

The chapter question is whether anomaly structure learned from the Kerkrade low-cost CO2 site has a reproducible relationship to antecedent hydrological state, and whether related air-quality or meteorological transfer sites show comparable event timing. Transfer results are exploratory until more Kerkrade IoT and KNMI reference data are available.

## Training Site

Primary site: Kerkrade post-mining calibration site.

Training inputs:

- Barometric CO2 residuals from `data/processed/co2-residual-barometric.csv`.
- July model-ready signal frame from `data/processed/signal_characterization_frame.csv`.
- Optional KNMI reference meteorology from `data/interim/knmi_hourly.csv` when available.
- Visual Crossing and IoT pressure features remain the fallback exogenous set when KNMI is absent.

Targets and detectors:

- SARIMAX-family residual anomalies from `scripts/05_sarimax.py`.
- Kalman innovation anomalies from `scripts/06_kalman.py`.
- Isolation Forest anomalies from `scripts/07_isolation_forest.py`.
- Ensemble agreement from `scripts/08_ensemble_agreement.py`.

## Transfer Sites

First transfer lane: RIVM/Luchtmeetnet Limburg candidate stations from `scripts/04_ingest_rivm.py`.

Initial candidate stations are selected for proximity to Maastricht, Roermond, Heerlen, and the South Limburg/Meuse corridor, using station metadata cached under `data/raw/transfer/rivm/` and normalized hourly measurements in `data/interim/rivm_hourly.csv`.

Later discovery lanes:

- IRCEL-CELINE Belgium stations near the Meuse corridor.
- LANUV NRW stations near the German side of the border region.

Those later lanes should be discovery-first and should use official public APIs or documentation at implementation time.

## Locked Evaluation Ideas

Transfer-site outputs should be summarized without changing the Kerkrade detector protocol after seeing transfer results.

Primary summaries:

- Hourly anomaly score and flag availability by transfer site.
- Event-window anomaly rate around shared hydrological soft-label/event windows.
- Pairwise timing agreement among Kerkrade detectors and transfer-site candidate signals.
- Sensitivity to detector threshold only where already specified in the July scripts.

Hydrological comparison windows:

- Main event window: 72 hours before event start.
- Control window: the preceding 72 hours.
- Statistical comparison: paired sign-flip or permutation test where at least two event/control pairs overlap the transfer-site record.

## Success Criteria

Proceeding evidence:

- Transfer-site anomaly rates increase in antecedent event windows relative to matched controls.
- Timing is broadly consistent with the Kerkrade residual anomaly windows.
- Results remain directionally stable after rerunning with longer IoT and KNMI data.

Weak or redirect evidence:

- Transfer outputs are dominated by missingness, station-specific artifacts, or unrelated local emissions.
- Anomaly timing has no event-window enrichment after additional Kerkrade data are incorporated.
- Detector agreement exists only under hand-tuned thresholds not declared in the scripts.

## Current Limits

The current Kerkrade residual window is about 3719 hourly rows after merging
local Blynk exports. July model outputs remain provisional because the record is
gappy, but the official 30-day train / 7-day evaluation scheme is now runnable
for pipeline evaluation.

No transfer model results should be interpreted as chapter evidence until this preregistration is committed with the July pipeline code.
