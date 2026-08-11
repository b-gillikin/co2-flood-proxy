# Analysis Inventory — Prospective Event Study

Status: 2026-08-10. There is no new event-study result. The regional chapter is
stopped at its core data gate. The source-native July 2021 K4 IoT record is now
normalised, but that alone does not make the separate Kerkrade recurrence case
available.

## Prospective chapter components

| component | role | current state |
| --- | --- | --- |
| literature source notes, evidence matrix and bibliography | verified source-level corpus for the student-authored literature review | ready; 43 sources and 97 question/source relationships; no aggregate synthesis |
| Viefhues/Eryilmaz source reading | establishes event observation -> public explanation -> spatial-extent test | incorporated in the canonical literature corpus; original PDFs retained |
| `31_event_study_gates.py` | audits the binding regional core and all-donor spatial support | implemented; core fails |
| `32_lanuk_feasibility.py` | audits German gauge metadata, density, gaps, episodes and watercourse identity without signal outcomes | implemented; German cohort does not pass |
| `33_ingest_viefhues_iot.py` | normalises the source-native non-ABC K4 record and records coverage/ceiling QC | implemented; all 744 July hours present |
| `34_fetch_era5_land.py` | downloads the approved 2001–2025 primary-weather grid and hashes annual NetCDF files | implemented; blocked before submission by missing local CDS credentials |
| `35_ingest_knmi_validated.py` | downloads and normalises validated Maastricht/Ell/Arcen hourly weather for observational sensitivity | implemented; 655,221 station-hours held |
| `src/event_study.py` | small definitions for storms, censored events, controls, pressure residuals and time blocks | implemented and unit-tested |
| long-record p99 event catalogue | independently defines high-water episodes | not built; discharge gate fails |
| matched local contrasts | establishes which fixed signals recur before receiver high water | not run or fully implemented |
| all-donor spatial contrasts | estimates how each signal's event contrast changes with receiver-donor distance | gate support partly implemented; outcome estimator not implemented or run |
| July 2021 regional anchor | observed regional trajectory inside the common study period | not run; core inputs fail |
| conditional Kerkrade case | Viefhues trajectory and later pressure-adjusted CO2 recurrence | July K4 is reproducible; era metadata, pair, bounds and later-event support remain incomplete |
| RADOLAN catchment rainfall | principal rainfall exposure | not built; radar/polygon gate fails |
| long public-weather assignment | temperature, humidity and pressure for each watercourse | source/rule not selected; gate fails |

No figure or outcome table from this prospective design exists. The protocol is
not locked.

The LANUK feasibility products under `results/feasibility/` are input-QA
artifacts, not chapter findings. The tracked interpretation is
`lanuk-feasibility.md`.

## Existing analysis retained as predecessor context

| analysis | permitted role |
| --- | --- |
| `03_eryilmaz_replication.py` | short same-site context for Eryilmaz; calendar-defined forward folds report coverage and outages separately, with no pooled/mean headline; not spatial transfer |

## Data infrastructure retained

- IoT, Visual Crossing and KNMI ingestion and provenance;
- Waterschap, LANUK and RWS discharge ingestion;
- DWD point-rainfall ingest as a sensitivity source, not the principal
  catchment exposure;
- already-held BRO groundwater as optional Kerkrade mechanism evidence;
- zero-sentinel, timestamp and precipitation-unit corrections;
- source PDFs, the canonical source notes/evidence matrix/BibTeX and the
  historical decisions log.

## Stopped

- symmetric all-pairs prediction matrices, Mantel tests and
  catchment-signature analyses; the retained all-donor table serves one fixed
  spatial-gradient estimand instead;
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

The default scientific suite contains 32 focused checks. Eighteen older
application/ingestion checks have been moved to `infrastructure_tests/` and are
not part of routine chapter verification. New source deliveries should first
be checked against their real files and tidy QC artifacts; do not add fixture
tests merely because a parser exists.
