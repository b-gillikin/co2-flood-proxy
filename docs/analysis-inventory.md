# Analysis Inventory — Prospective Event Study

Status: 2026-08-11. There is no new event-study result. The regional chapter is
stopped at its core data gate. The source-native July 2021 K4 record is
normalised, but that alone does not make the conditional Kerkrade case
available.

## Prospective chapter

| component | purpose | state |
| --- | --- | --- |
| literature notes, evidence matrix and BibTeX | verified source-level corpus for the student-authored review | ready; 42 sources, 96 relationships, no aggregate synthesis |
| Viefhues and Eryilmaz source reading | establishes observation -> public explanation -> spatial-extent test | incorporated; original PDFs retained |
| `31_event_study_gates.py` | audits the binding regional inputs and all-donor support | implemented; core fails |
| `32_lanuk_feasibility.py` | audits the German route without signal outcomes | implemented; route fails |
| `33_ingest_viefhues_iot.py` | normalises source-native non-ABC K4 and records QC | implemented; all 744 July hours present |
| ERA5-Land raw archive | fixed 2001–2025 weather grid used after catchment assignment | complete; 300/300 months passed NetCDF, size and SHA-256 audit; Azure timer disabled |
| `src/event_study.py` | defines storms, censored events, quiet controls and conditional pressure residuals | implemented and unit-tested |
| long-record event catalogue | independently defines high-water episodes | not built; discharge gate fails |
| local event-minus-quiet contrasts | identifies recurring public signals | not implemented or run |
| ordered-pair spatial contrasts | measures signal coherence at every other watercourse | support audit implemented; outcomes not implemented or run |
| pair-median distance slopes | relates one median per ordered pair to fixed log distance | specified; not implemented or run |
| July 2021 regional anchor | describes observed regional trajectory without invented onset/peak | not run; core inputs fail |
| conditional Kerkrade recurrence | compares July 2021 with later pressure-adjusted CO2 events | unavailable; provenance, pair, bounds and later-event support incomplete |

No prospective figure or outcome table exists. The protocol is unlocked.
LANUK products under `results/feasibility/` are input-QA artifacts, not chapter
findings.

## Supporting data acquisition

- `01_ingest_iot.py` and `src/io_iot.py`: later Kerkrade IoT for the conditional
  case;
- `25_ingest_lanuk_nrw.py`: held German source needed to reproduce the failed
  route;
- `infrastructure/era5_backfill/`: completed unattended acquisition for the
  sole regional public-weather source; timer disabled after final audit;
- `34_fetch_era5_land.py`: stopped local fallback for the same fixed requests;
- source PDFs, source notes, evidence matrix, bibliography and append-only
  decision log.

The Azure code in `kerkrade_data/` and `infrastructure/era5_backfill/` is
collection infrastructure, not chapter analysis. It is outside routine
scientific verification.

## Removed from the live analysis

- the later-era Eryilmaz model re-fit and its Visual Crossing join;
- rolling two-year Dutch discharge, RWS main-stem and DWD point-rain pipelines;
- all-pairs prediction matrices, Mantel and catchment-signature analyses;
- best-lag search, correlation radii and monitoring-location inference;
- Fase thresholds outside their exact crisis-plan gauges;
- water-level expansion as a substitute for discharge history;
- anomaly detectors, SARIMAX, Kalman filters and fun-model comparisons;
- hourly transfer classifiers, alert metrics and operational interpretations;
- generic model/substitution frameworks and generated prose reports.

The Eryilmaz paper remains predecessor evidence. Removing its later-era re-fit
does not remove that intellectual step; it prevents a second same-site model
from competing with the chapter's actual estimands. Deleted code remains in Git
history.

## Code standard

The planned analysis should read as an auditable data-science script:

`load -> check -> define events/controls -> estimate -> tidy tables -> figures`

Keep transformations visible in pandas. Use one simple equation per fixed
signal, not an extensible modelling interface. Comment scientific decisions
such as censoring, completeness and aggregation rather than obvious syntax.
Add a helper only when a definition is reused or needs an isolated scientific
check. Do not build a pipeline framework, configuration system, report
generator, model registry or application layer.

The default test suite protects event definitions, leakage-prone source
semantics and gate calculations. It should grow only when a possible error
could alter a reported number or scientific claim. Parsers should first be
checked against real delivered files and tidy QC artifacts, not automatically
given fixture suites.
