# Results Outline

> **Superseded 2026-08-05.** Organized around the previous claim structure and
> its four discussion branches. The coverage, barometric-baseline and
> replication sections remain broadly reusable; the detector, ensemble,
> synthetic-injection and transfer sections are retired. See
> `docs/chapter-direction.md`.

Date: 2026-06-21

Purpose: organize result paragraphs around current reproducible artifacts.
Transfer sections are placeholders until the transfer scope is complete enough
for interpretation.

Every final number must come from the frozen snapshot identified by
`results/run_manifest.json`. Until then, this file supplies paragraph and
caption slots rather than final numeric prose.

## Data Coverage and QC

Current artifacts:

- `data/interim/analysis_hourly.csv`
- `results/eda/co2_pressure_coverage.png`
- `results/eda/co2_temperature_humidity.png`
- `results/eda/co2_discharge_soft_labels.png`

Draft result paragraph:

- State the synchronized Kerkrade overlap, hourly UTC convention, source
  completeness, and visible CO2/weather/discharge structure.
- Separate source coverage limitations from model results.

## Barometric Baseline

Current artifacts:

- `results/baseline/r2.txt`
- `results/baseline/co2_fit_residual.png`
- `data/processed/co2-residual-barometric.csv`

Draft result paragraph:

- Report the official Week 2 pressure-only R2 and Kill Check 1 decision.
- Explain that pressure explains meaningful CO2 variance but leaves a residual
  large enough for hydrological signal exploration.

## Eryilmaz Replication

Current artifacts:

- `results/eryilmaz/auroc.txt`
- `results/eryilmaz/roc_curves.png`
- `data/processed/eryilmaz_replication_predictions.csv`

Draft result paragraph:

- Report Model A and Model B AUROC, the AUROC gap, and Kill Check 2 status.
- Note that the random 5-fold setup is predecessor replication only.

## Residual Signal Characterization

Current artifacts:

- `results/signal/summary.txt`
- `results/signal/residual_cross_correlation_heatmap.png`
- `results/signal/residual_structure_rf_feature_importance.png`
- `results/signal/hydrology_proxy_rf_feature_importance.png`
- `results/signal/pca_scores.png`

Draft result paragraph:

- Summarize residual timing, feature-importance scans, and PCA structure as
  exploratory evidence.
- Avoid causal language until the longer IoT and KNMI records are rerun.

## July Detector Outputs

Current artifacts:

- `data/processed/sarimax-anomalies.csv`
- `data/processed/kalman-anomalies.csv`
- `data/processed/iforest-anomalies.csv`
- `data/processed/ensemble_anomaly_flags.csv`
- `results/evaluation/evaluation_summary.txt`

Draft result paragraph:

- Report detector availability, anomaly counts, and ensemble overlap as
  provisional pipeline diagnostics.
- State that the official 30-day / 7-day evaluation window is now runnable on
  the merged IoT frame, while interpretation remains provisional because the
  record is not yet continuous across a full annual cycle.
- Report convergence status and scored coverage before anomaly rates.
- Calculate cross-detector agreement only on common scored hours.

## Direct Groundwater/Mine-Water Result

Current status: analysis implementation complete; field result waiting on data.

Current implementation artifacts after a run:

- `results/direct_state/summary.json`
- `results/direct_state/decision.csv`
- `results/direct_state/selection.csv`
- `results/direct_state/per_block.csv`
- `results/direct_state/sensitivities.csv`
- `results/direct_state/aligned_daily_state.png`

Required final paragraph:

- Identify the locked primary state series and justify it from provenance and
  physical relevance rather than observed association.
- Report paired daily observations, contributing blocks, standardized
  coefficient, HAC p-value, bootstrap interval, per-block signs, and the
  future-water placebo.
- State which claim-decision row in `docs/chapter-readiness-plan.md` the result
  supports.

Required figure/table slots:

- aligned daily residual and primary state series with coverage gaps visible;
- coefficient/uncertainty and placebo comparison;
- primary plus FDR-controlled sensitivity table.

## Distributed-Lag Boundary Result

Current artifacts:

- `results/distributed_lag/summary.txt`
- `results/distributed_lag/timescale_scan.csv`
- `results/distributed_lag/timescale_scan.png`

Required result paragraph:

- Retain the current `NOT SUPPORTED` outcome unless the unchanged frozen rerun
  changes it.
- Report the 10-day coefficient, HAC p-value, bootstrap interval, usable blocks,
  and future-precipitation placebo.
- Explain that the earlier 10.6-day cross-correlation is shared low-frequency
  structure on the current record, not established antecedent signal.

## API and External Reference Lanes

Current artifacts:

- `data/processed/api.csv`
- `data/interim/knmi_hourly.csv`
- `results/knmi/knmi_visualcrossing_comparison.csv`
- `data/interim/rivm_hourly.csv`
- `results/rivm/candidate_stations.csv`

Draft result paragraph:

- Describe the API baseline and the status of KNMI/RIVM availability.
- Treat KNMI comparison plots as draft while backfill continues.

## August v1 Transfer Dry Run

Current artifacts:

- `results/transfer/transfer_training_summary.csv`
- `results/transfer/feature_availability.csv`
- `results/transfer/baseline_availability.csv`
- `data/processed/transfer-anomalies/*.csv`
- `data/processed/events-transfer-*.csv`

Draft result paragraph:

- Do not interpret transfer success or failure.
- Report only that the dry-run machinery trains three Kerkrade surrogates,
  writes RIVM site scores where enough aligned rows exist, and records feature
  gaps for later official transfer work.
- Keep transfer secondary/appendix-level unless it becomes interpretable; its
  coverage cannot block chapter completion.

## Figures and Tables

Current artifact:

- `results/figures/figure_manifest.csv`

Draft result paragraph:

- Use the figure manifest and `docs/figure-inventory.md` to decide which draft
  plots become final chapter figures.
