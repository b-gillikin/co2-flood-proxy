# Chapter 1 CO2

Working repository for the dissertation chapter on antecedent-state signal in low-cost IoT data at the Kerkrade post-mining calibration site.

**Working claim**: Low-cost IoT air-quality and weather streams at the Kerkrade calibration site carry a decomposable signal about antecedent hydrological state, after atmospheric pressure effects are characterized and separated.

**Methodological frame**: Ensemble time-series anomaly detection and signal decomposition, using pressure-tendency regression, SARIMAX residuals, Kalman innovations, Isolation Forest scores, and transfer-site stress tests.

**Empirical window**: Kerkrade IoT, weather, discharge, and related hydrological data for January 2025 to present, with predecessor work using the July 2021 flood as the motivating event rather than the analyzed event.

**Predecessor work**: Viefhues 2022 and Eryilmaz 2025, as summarized in `chapter-prework/Lit-scaffold - chapter draft.docx` and operationalized in `chapter-prework/June 2026 - How-To.docx`.

## How to Reproduce

1. Create the environment:

   ```bash
   conda env create -f environment.yml
   conda activate chapter1-co2
   ```

2. Run scripts in order from `scripts/`.

3. Write intermediate data to `data/interim/`, processed analysis products to `data/processed/`, and figures/tables/model artifacts to `results/`.

## Structure

- `chapter-prework/`: scaffold documents, monthly how-to docs, bibliography, and source/corpus materials.
- `data/raw/`: immutable raw inputs.
- `data/interim/`: cleaned and time-aligned data.
- `data/processed/`: feature sets, residual series, event catalogues, anomaly scores, and evaluation outputs.
- `scripts/`: numbered runnable analysis scripts.
- `src/`: reusable importable code used by the scripts.
- `results/`: generated figures, tables, and model artifacts.
- `docs/`: decisions log, data-request tracking, predecessor notes, and chapter-facing working notes.

