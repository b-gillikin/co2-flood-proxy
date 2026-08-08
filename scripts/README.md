# Scripts

Numbered scripts are data ingests or transparent analyses. New work should
follow `load -> check -> define -> estimate -> tidy tables -> figures`; this
repository does not need an analysis framework.

## Prospective event study

| script/module | purpose | state |
| --- | --- | --- |
| `31_event_study_gates.py` | audit the binding regional core, all-donor spatial support and conditional Kerkrade case separately | implemented; core fails, case input not yet normalised |
| `32_lanuk_feasibility.py` | audit held German gauges without inspecting signal outcomes | implemented; German route does not pass |
| `src/event_study.py` | small tested definitions for storms, controls, censoring, pressure residuals and time blocks | implemented |
| event-contrast script | local recurrence, all-donor distance gradients, held-out validation and four figures | deliberately not run or completed before gates/lock |

Audit without pretending the known failure is a result:

```bash
python scripts/31_event_study_gates.py --report-only
python scripts/32_lanuk_feasibility.py
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

RADOLAN catchment averaging and long Waterschap ingestion remain to be written
after the data are obtained and their formats inspected. A long-record public
weather source and assignment rule must also be fixed. Do not create parsers
against imagined files.

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
