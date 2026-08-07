# Analysis Inventory — Prospective Event Study

Status: 2026-08-07. There is no new event-study result. The repository is
stopped at the hard data gate.

## Prospective chapter components

| component | role | current state |
| --- | --- | --- |
| Viefhues/Eryilmaz source reading | establishes event observation -> public explanation -> transfer test | ready; source notes retained |
| `31_event_study_gates.py` | audits the non-negotiable data requirements | implemented; current audit fails |
| `src/event_study.py` | small definitions for storms, censored events, controls, pressure residuals and time blocks | implemented and unit-tested |
| long-record p99 event catalogue | independently defines high-water episodes | not built; discharge gate fails |
| matched event contrasts | sole analysis of recurrence and held-out signal transfer | not run or fully implemented |
| July 2021 Kerkrade anchor | censored trajectory and later-event CO2 recurrence | not run; original IoT gate fails |
| later Kerkrade recurrence sample | distinguishes a null from no usable recurrence data | not evaluable until pair discharge arrives |
| RADOLAN catchment rainfall | principal rainfall exposure | not built; radar/polygon gate fails |
| long public-weather assignment | temperature, humidity and pressure for each watercourse | source/rule not selected; gate fails |

No figure or outcome table from this prospective design exists. The protocol is
not locked.

## Existing analysis retained as predecessor context

| analysis | permitted role |
| --- | --- |
| `03_eryilmaz_replication.py` | short same-site context for Eryilmaz; not spatial transfer |

## Data infrastructure retained

- IoT, Visual Crossing and KNMI ingestion and provenance;
- Waterschap, LANUK and RWS discharge ingestion;
- DWD point-rainfall ingest as a sensitivity source, not the principal
  catchment exposure;
- already-held BRO groundwater as optional Kerkrade mechanism evidence;
- zero-sentinel, timestamp and precipitation-unit corrections;
- source PDFs, source notes and the historical decisions log.

## Stopped

- symmetric all-pairs/Mantel and catchment-signature analyses;
- best-lag search, correlation radii and monitoring-location inference;
- Fase thresholds outside exact crisis-plan leading gauges;
- water-level expansion as a substitute for discharge history;
- anomaly-detector and fun-model comparisons;
- SARIMAX and Kalman filtering, which answer anomaly/dynamics questions rather
  than event recurrence;
- generic model/substitution frameworks and generated prose reports;
- the 2024–2026 hourly transfer classifier and its operational metrics;
- the unreproducible later-record precursor pipeline, whose input-producing
  exploratory script had already been retired;
- the three-gauge soft-label catalogue and full-period CO2 barometric baseline;
- operational alerts, warning recall, false-alarm budgets and FEWS comparison.

Deleted code remains in Git history. More spatial rows, thresholds or model
families do not compensate for missing years or missing catchment rainfall.

## Data-science code standard

New analysis should read as an auditable notebook translated into scripts:

`load -> check -> define events/controls -> estimate -> tidy tables -> figures`

Keep transformations in pandas, keep intermediate tables visible, and comment
scientific choices rather than obvious syntax. Add a shared helper only when a
definition is reused or needs an isolated regression test. Do not build a
pipeline framework, configuration system, report generator or reusable model
product for this chapter.
