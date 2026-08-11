# Scripts

Numbered scripts are data ingests or transparent analyses. New work should
follow `load -> check -> define -> estimate -> tidy tables -> figures`; this
repository does not need an analysis framework.

## Prospective event study

| script/module | purpose | state |
| --- | --- | --- |
| `31_event_study_gates.py` | audit the binding regional core and all-donor spatial support | implemented; regional inputs fail |
| `32_lanuk_feasibility.py` | audit held German gauges without inspecting signal outcomes | implemented; German route does not pass |
| `33_ingest_viefhues_iot.py` | normalise source-native K4 CO2/pressure and write compact coverage/provenance QC | implemented; complete July 2021 hourly coverage |
| `src/event_study.py` | small tested definitions for storms, controls, censoring, pressure residuals and time blocks | implemented |
| event-contrast script | local recurrence, all-donor distance gradients, held-out validation and four figures | deliberately not run or completed before gates/lock |

Audit without pretending the known failure is a result:

```bash
python scripts/31_event_study_gates.py --report-only
python scripts/32_lanuk_feasibility.py
python scripts/33_ingest_viefhues_iot.py
```

## Predecessor context

| script | permitted role |
| --- | --- |
| `03_eryilmaz_replication.py` | same-site context for Eryilmaz |

Its input is the compact IoT/weather frame written by `01_eda.py`. Run
`update_data.py --skip-download` to rebuild that frame from cached source files.

## Relevant data collection

| script | purpose |
| --- | --- |
| `update_data.py` | refresh later-era Kerkrade IoT/weather and rebuild context QC |
| `01_ingest_iot.py` | currently held 2025–2026 Kerkrade IoT |
| `02_ingest_weather.py` | Kerkrade public weather |
| `01_eda.py` | join those two sources and write the Eryilmaz/QC frame |
| `04_ingest_knmi.py` / `04_sync_knmi_azure.py` | KNMI normalisation/cache |
| `22_ingest_waterschap_gauges.py` | rolling two-year Waterschap network; not the long-record gate input |
| `25_ingest_lanuk_nrw.py` | German long-record gauges |
| `26_ingest_rws_maas.py` | RWS main-stem source validation |
| `27_ingest_dwd_precipitation.py` | point-rainfall sensitivity source |
| `34_fetch_era5_land.py` | fixed 2001–2025 primary-weather grid over Limburg and its cross-border margin |
| `35_ingest_knmi_validated.py` | 2001–2025 validated Maastricht/Ell/Arcen weather for observational sensitivity |

RADOLAN catchment averaging and long Waterschap ingestion remain to be written
after the data are obtained and their formats inspected. ERA5-Land is the
approved primary public-weather source. Fetch its source grid with:

```bash
python scripts/34_fetch_era5_land.py
```

This requires a Copernicus CDS account, accepted ERA5-Land licence and the two
credential lines in `~/.cdsapirc`. The script retrieves annual NetCDF files for
2001–2025 and writes a checksum manifest. Catchment-centroid assignment and
relative-humidity derivation wait for the verified cohort; no outcome is read.

The BRO groundwater fetch/normalisation code is archived because groundwater is
now optional mechanism evidence, not a live analytical lane. The already-held
BRO observations can still be used descriptively if the Kerkrade case warrants
it.

## Retired directions

The live tree no longer uses all-pairs prediction matrices/Mantel,
Fase-everywhere, best-lag,
catchment-signature, detector-ensemble, hourly transfer classification or
generic substitution machinery. The history remains in the decisions log.
The retained all-donor table answers one fixed spatial-extent question. More
models and more pair rows are not substitutes for missing years and rainfall
exposure.

## Verification boundary

`pytest -q` runs the small scientific suite for event definitions, leakage
guards and source semantics. Older IoT/daily-summary application checks live in
`infrastructure_tests/` and run only when that legacy machinery changes:

```bash
pytest infrastructure_tests -q
```

The Viefhues ingest is checked against the actual delivered source and its QC
table. It does not add another fixture-based test layer.
