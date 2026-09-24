# Analysis Inventory — Prospective Case-Crossover Study

Status: 2026-09-24, protocol draft 0.10. There is no chapter result. Discharge
source semantics remain unresolved; numerical benchmarks do not stop the study.

## Prospective chapter

| component | purpose | state |
| --- | --- | --- |
| literature notes, evidence matrix and BibTeX | verified source corpus | 44 sources; case-crossover and distributed-lag design references still to be added |
| Viefhues and Eryilmaz source reading | motivation for the regional question | incorporated; no CO2 analysis in draft 0.9 |
| `31_event_study_gates.py` | audits input validity and information | aligned with draft 0.10; numerical benchmarks are nonbinding, rating-era validity remains binding |
| `32_lanuk_feasibility.py` | audits the German route | implemented; relevant only to the conditional distance module |
| `35_audit_waterschap_delivery.py` | raw availability and provider-sourced station QA | implemented; timezone and zero semantics unresolved (cohort decided, D3) |
| ERA5-Land weather table | relative humidity, surface pressure and six-hour change | built for all candidates, 2001–2025 (`40_build_event_study_weather.py`) |
| `src/event_study.py` | eras, thresholds, crossings, censoring, episodes, storms, at-risk hours, strata | implemented and unit-tested |
| radar rainfall | principal exposure | built from RADOLAN RW 2010–2025; timing checked against DWD gauges |
| cross-border catchments | rainfall areas and weather centroids | delineated from GLO-30; seven area checks within ±4.4%; provisional pour points |
| rating eras | per-era p99 and rating domain | built under D8 (`43_build_rating_eras.py`); merge validity checked in the gate audit |
| gauge metadata | cohort, coordinates, QA, July 2021 status | built (`44_build_event_study_gauges.py`) |
| hourly discharge ingest | outcome series | scaffolded and unit-tested (`45_build_event_study_discharge.py`); blocked on verified timezone and zero semantics |
| `src/case_crossover.py` | lag basis, conditional Poisson, block bootstrap, summaries | implemented; reproduces R to within 1e-13 |
| synthetic estimator validation | agreement, recovery and coverage (protocol §12) | run: 800 datasets; coverage 93–93.5% (cumulative difference), 98.5–99.5% (median-lag difference, D7) |
| July 2021 regional anchor | descriptive trajectory | not run |
| conditional distance module | separate ordered-pair slope if LANUK data are comparable | inactive |

No prospective figure or outcome table exists. The protocol is unlocked.
LANUK products under `results/feasibility/` are input-QA artifacts, not chapter
findings.

## Supporting data acquisition

- `25_ingest_lanuk_nrw.py`: held German source needed to reproduce the failed
  route;
- `infrastructure/era5_backfill/`: completed unattended acquisition for the
  sole regional public-weather source; Function App stopped after final audit;
- `34_fetch_era5_land.py`: stopped local fallback for the same fixed requests;
- Waterschap Limburg's native 2010--2025 discharge delivery and the compact
  availability audit produced by `35_audit_waterschap_delivery.py`;
- Provincie Limburg's native Willem/Willem Oud delivery: ignored raw evidence
  for the conditional case, not yet analysis-ready;
- source PDFs, source notes, evidence matrix, bibliography and append-only
  decision log.

The Azure code in `kerkrade_data/` and `infrastructure/era5_backfill/` is
collection infrastructure, not chapter analysis. It is outside routine
scientific verification. The scripts that once normalised the Kerkrade IoT
stream (`01_ingest_iot.py`, `33_ingest_viefhues_iot.py`) moved to `archive/`
on 2026-09-18; see `docs/iot-sources.md`. `src/io_iot.py` stays in `src/`,
still exercised by `infrastructure_tests/test_io_data.py` for the deployed
Azure function.

## Removed from the live analysis

In draft 0.9 (2026-09-18): the log-distance slope over ordered pairs (except as
a conditional module), the conditional Kerkrade CO2 case, the mine-water
evidence, five-nearest-quiet-hour controls with seven-day exclusions,
temperature and pressure level as signals, and donor-flow pairs as signals.

Earlier:

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

Keep transformations visible in pandas. Draft 0.9 uses one distributed-lag
conditional Poisson model per prespecified specification, not an extensible
modelling interface. This is a deliberate, recorded change from the earlier
"one simple equation per signal" standard (`decisions.md`, 2026-09-18). Comment scientific decisions
such as censoring, completeness and aggregation rather than obvious syntax.
Add a helper only when a definition is reused or needs an isolated scientific
check. Do not build a pipeline framework, configuration system, report
generator, model registry or application layer.

The default test suite protects event definitions, leakage-prone source
semantics and gate calculations. It should grow only when a possible error
could alter a reported number or scientific claim. Parsers should first be
checked against real delivered files and tidy QC artifacts, not automatically
given fixture suites.
