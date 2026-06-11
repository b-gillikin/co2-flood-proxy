# Decisions Log

## 2026-06-06 — Initial chapter framing

Decision: Set up this repository around the working claim that the Kerkrade low-cost IoT stream carries a decomposable antecedent-hydrological-state signal once barometric effects are explicitly characterized and separated.

Alternatives considered: Treat the chapter as a direct flood-prediction chapter; treat it as a purely barometric mine-gas dynamics chapter; delay repository setup until after data ingestion.

Reasoning: The June 2026 pre-work plan makes the first month a foundation and decomposition sprint. The chapter should survive either outcome of the first kill check: if pressure explains only part of CO2 variance, the hydrological-signal framing proceeds; if pressure explains nearly all variance, the chapter can redirect toward a barometric-decomposition methods contribution without losing the work already done.

Source: `chapter-prework/June 2026 - How-To.docx`; `chapter-prework/Lit-scaffold - chapter draft.docx`.

## 2026-06-06 — Repository structure

Decision: Use numbered runnable scripts in `scripts/` and reusable package code in `src/`, with no notebooks as core analytical artifacts.

Alternatives considered: Notebook-first exploratory workflow.

Reasoning: The chapter needs reproducible, defensible analysis steps. Numbered scripts make the run order explicit; `src/` keeps readers, feature builders, models, and evaluation code stable across scripts.

Source: `chapter-prework/June 2026 - How-To.docx`; `chapter-prework/skill-dissertation-chapter-scaffold/reference/repo_layout.md`.

## 2026-06-06 — Data-window policy

Decision: Treat January 2025 to present as the first synchronized modelling window only, not as a limit on data acquisition.

Alternatives considered: Pull only January 2025 to present for every source; postpone older data acquisition until after the first models run.

Reasoning: The IoT stream appears to constrain the primary aligned analysis window, but hydrological and meteorological context benefits from longer records. Longer discharge and weather histories are especially useful for percentile thresholds, event catalogues, seasonality checks, and deciding whether 2025-present events are ordinary, high-flow, or genuinely extreme. Pulling longer histories now is low-cost and reduces the chance of rebuilding loaders later.

Working rule: For each source, acquire the longest practical history available. Use the full history for context and thresholds; subset to the common IoT/weather/discharge overlap for the first synchronized models.

## 2026-06-06 — Task 1.3 discharge sources

Decision: Use WVER Wurm Rimburg NL discharge, Waterschap Limburg Geul Hommerich discharge, and Waterschap Limburg Geul Meerssen discharge as the first discharge set for the June soft-label/event-catalogue work.

Alternatives considered: Use WVER Herzogenrath water level only; wait for a separate official data request before implementing discharge ingestion.

Reasoning: The June How-To names Worm/Wurm plus Geul discharge as the unblock-everything task. WVER exposes Wurm Rimburg NL `Abfluss` JSON directly, while Herzogenrath's public WVER page exposes water level rather than discharge. Waterstand Limburg exposes public OData-style `Afvoer` measurements for the named Geul Hommerich and Meerssen gauges. These three sources provide a usable first-pass discharge frame now, while leaving room to replace or supplement them with official historical/gauge-validated files later.

Source: `docs/discharge-sources.md`; public WVER and Waterstand Limburg station endpoints inspected on 2026-06-06.

## 2026-06-06 — Routine data refresh entry point

Decision: Use `python scripts/update_data.py` as the routine command for bringing available chapter data sources up to date.

Alternatives considered: Re-run each task-specific script manually; wait to create a refresh command until IoT/weather ingestion is implemented.

Reasoning: Several chapter inputs update daily or hourly. A single refresh entry point keeps the workflow simple when data needs to be current before analysis, while still letting each source family keep source-specific ingestion details in its own script. For discharge, Waterstand Limburg sources are appended from the latest local timestamp and WVER's compact public JSON is replaced.

Source: `scripts/update_data.py`; `scripts/01_ingest_discharge.py`.

## 2026-06-06 — Task 1.1 IoT source

Decision: Ingest the Kerkrade IoT stream from the existing Azure storage blobs in `stkerkradeprod01bg` / `air-quality-device-data-1`, rather than re-querying Blynk for historical rows.

Alternatives considered: Re-run the Blynk polling code locally; wait for a separate export; copy the source CSVs manually from Azure Storage Explorer.

Reasoning: The Azure Function already polls Blynk every minute and writes daily CSV blobs with UTC timestamps. Using those blobs makes the chapter update path simple, repeatable, and consistent with the production capture path, while avoiding credential storage in the repository. The local script uses the current Azure CLI login and refreshes only missing or size-changed daily blobs by default.

Source: `kerkrade_data/air_quality_timer/__init__.py`; `docs/iot-sources.md`; Azure resource group inspection on 2026-06-06.

## 2026-06-06 — Task 1.2 weather source

Decision: Ingest Visual Crossing weather for the June Task 1.2 brief from the existing Azure weather blob containers, not from fresh API calls.

Alternatives considered: Use the Visual Crossing API keys to pull fresh daily/hourly data; defer weather ingestion until a primary meteorological source is chosen; pull only the Kerkrade weather container.

Reasoning: The resource group already contains monthly Visual Crossing weather blobs for Kerkrade and nearby comparison locations. Pulling from Blob Storage now satisfies the immediate June ingestion brief, avoids spending API quota, and gives the chapter a repeatable local source layout. The stored CSV timestamps are local civil time, so the loader localizes them to Europe/Amsterdam time and converts to UTC for alignment with IoT and discharge.

Source: `docs/weather-sources.md`; Azure weather container inspection on 2026-06-06.

## 2026-06-10 — Kill Check 1 barometric baseline

Decision: Proceed with the hydrological-signal framing after the Week 2 pressure-only baseline. The official linear IoT-pressure model R2 is 0.593641, below the June kill-check proceed threshold of 0.85.

Formula: `CO2 ~ pressure + delta_pressure_1h + delta_pressure_3h + delta_pressure_6h + delta_pressure_12h + delta_pressure_24h`.

Analysis window: 2026-03-17 22:00 UTC to 2026-04-13 02:00 UTC after lag/dropna. Rows used: 622 from the 654-row Week 1 joined frame.

Sensitivity: Ridge on the same IoT-pressure features produced R2 = 0.593321. The Kerkrade Visual Crossing pressure sensitivity produced linear R2 = 0.574862 and ridge R2 = 0.574719.

Reasoning: Pressure level and tendency explain a meaningful share of CO2 variance, but far less than the >0.95 redirect threshold. Residual variance remains large enough to support the next June tasks: Eryilmaz replication and residual hydrological-signal characterization.

Source: `scripts/02_barometric_baseline.py`; `results/baseline/r2.txt`; `data/processed/co2-residual-barometric.csv`; `chapter-prework/June 2026 - How-To.docx`.

## 2026-06-10 — Kill Check 2 Eryilmaz replication

Decision: Treat the Eryilmaz public-weather substitution result as replicated on the current Kerkrade IoT window and proceed. Model B, using outdoor Visual Crossing weather features, is within 0.05 AUROC of Model A, using indoor IoT environmental features.

Target: `iot_co2_ppm > 1000`.

Model A features: `iot_temperature_c`, `iot_relative_humidity_pct`, `iot_air_pressure_hpa`, `delta_pressure_6h`.

Model B features: `kerkrade_weather_temp_c`, `kerkrade_weather_relative_humidity_pct`, `kerkrade_weather_pressure_hpa`, `delta_pressure_6h`.

Evaluation: Stratified random 5-fold cross-validation with `random_state=42`, using `StandardScaler` and `LogisticRegression(max_iter=1000, solver="liblinear")`. This random CV setup is used only for faithful Eryilmaz replication; later chapter models should use time-aware evaluation.

Results: Model A AUROC = 0.986009 and Model B AUROC = 0.975709 on the same 643 complete-case hourly rows, with 62 positive CO2 events. AUROC gap = 0.010299.

Reasoning: The outdoor-weather model performs nearly as well as the indoor-IoT environmental model on the same CO2 leak target, consistent with Eryilmaz's same-site feature-substitution finding. Because the current IoT window is short, this should be rerun unchanged after additional IoT data are added.

Source: `scripts/03_eryilmaz_replication.py`; `results/eryilmaz/auroc.txt`; `data/processed/eryilmaz_replication_predictions.csv`; `chapter-prework/June 2026 - How-To.docx`.
