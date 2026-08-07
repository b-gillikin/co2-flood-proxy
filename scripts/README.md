# Scripts

Numbered, runnable analysis steps. Each writes to `data/` or `results/` and can
be run on its own; the numbering is dependency order, not a schedule.

Retired scripts moved to `archive/scripts/` on 2026-08-05 and again on
2026-08-06. See `archive/README.md` for what each did and
`docs/chapter-direction.md` for the reframing.

## Data collection

Run these first, or run `update_data.py` which chains them.

| Script | Purpose |
| --- | --- |
| `update_data.py` | Refresh all sources, rebuild the event catalogue, and run the coverage QC pass |
| `01_ingest_iot.py` | Sync Kerkrade IoT blobs, merge local Blynk exports from `iot-device-data/`, build hourly IoT data plus source and gap reports |
| `02_ingest_weather.py` | Sync Visual Crossing weather blobs and catch up the current month |
| `22_ingest_waterschap_gauges.py` | Waterschap Limburg inventory (634 locations) and discharge series. **Rolling ~2-year window**, earliest record 2024-08-06. Also writes `discharge_hourly.csv`, the three-column projection the CO2 lane reads |
| `25_ingest_lanuk_nrw.py` | LANUK NRW verified discharge archive, Rur and Niers/Schwalm catchments. **42 gauges, 15-min native, 1950-2026**, open licence. Includes July 2021 |
| `26_ingest_rws_maas.py` | Rijkswaterstaat Maas main stem. **10-min native, ~2000-present**, validated, CC0. Includes July 2021 |
| `27_ingest_dwd_precipitation.py` | DWD hourly station precipitation, 34 stations, 1995-2026, open licence |
| `04_ingest_knmi.py` | Normalize KNMI reference meteorology and compare against Visual Crossing |
| `04_sync_knmi_azure.py` | Pull Azure-collected KNMI station-slim blobs into local raw storage |
| `05a_fetch_bro_groundwater.py` | Fetch groundwater dossiers from the public BRO service; no credentials needed |
| `05_ingest_groundwater.py` | Normalize delivered groundwater to observed series-days without interpolation |

`04_ingest_knmi.py` defaults to `data/raw/knmi`, which holds NetCDF requiring
xarray. Pass `--raw-dir data/raw/knmi/azure_slim` to rebuild from the slim CSVs
alone.

**On discharge sources.** Three now, and they are not interchangeable. The
Waterschap endpoint is the only one covering the Dutch tributaries the chapter
is about, and it is a rolling two-year window containing no event near July
2021. LANUK NRW and RWS both reach back decades and both contain the 2021 flood,
but cover the German tributaries and the Maas main stem respectively. Long
records for the *Dutch* tributaries need the request tracked in
`docs/data-requests.md`. Do not silently substitute one source for another; the
gauge sets barely overlap.

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

### Regionalisation — the current chapter

| Script | Purpose |
| --- | --- |
| `23_catchment_similarity.py` | Gauge signatures, the pairwise similarity space, and its inference: structure filter, id-joined coordinates, event-conditioned lag-aligned response, Mantel permutation test, time-shifted null |
| `24_fetch_estreams_attributes.py` | EStreams static catchment attributes by ranged read of the 10 GB Zenodo zip |

`23_catchment_similarity.py` writes the two tidy tables the rest of the analysis
reads — one row per gauge, one row per pair. Three things in it are corrections
to numbers that had already been written down, and its docstring says which.

**Inference rule for anything built on the pair table:** 42 gauges give 861
pairs, and each gauge appears in 41 of them. Pairs are not independent
observations. Use permutation over gauge labels, never a Pearson p-value on the
pair list.

### The substitution ladder — Kerkrade rungs

`src/substitution.py` is the shared harness: two score sets, one binary target,
AUROC each, a paired block bootstrap on the gap, and Eryilmaz's 0.05 threshold.
Every rung uses it, which is what makes the progression structural rather than
asserted. See `docs/chapter-synthesis.md`.

| Script | Purpose |
| --- | --- |
| `18_precursor_skill.py` | **Rung 2.** CO2 sensor vs rainfall for high-flow onset, with block-bootstrap intervals and false-alarm rates |
| `05b_barometric_efficiency.py` | Well barometric efficiency and the shared-pressure confound |
| `05c_groundwater_event_lag.py` | Whether groundwater leads or lags tributary events |
| `03_eryilmaz_replication.py` | **Rung 1 of the substitution ladder.** Indoor sensing vs public weather. Reports the inherited random-fold procedure *and* the same scores under chapter inference |
| `19_barometric_response.py` | Barometric deconvolution. **Response SHAPE withdrawn** (rings under OLS); the response SUM is sound and is what `21_` consumes |
| `20_tidal_response.py` | Semidiurnal probe. Failed informatively: the 12 h band is occupancy, not tide |
| `21_forward_gain_model.py` | Forward bound on water-driven gain change |

## Conventions

- Hourly UTC throughout. Local times are resolved at ingestion, never later.
- Coverage gaps are never interpolated, and a row on the hourly grid is not an
  observation. Anything counting coverage must count observed values.
- Contiguous blocks break at any gap over one hour, so a "block" is a run with
  no missing hours, not merely a date range.
