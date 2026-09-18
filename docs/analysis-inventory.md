# Analysis Inventory — Prospective Case-Crossover Study

Status: 2026-09-18, protocol draft 0.9. There is no chapter result. The
regional chapter is stopped at its core data gate.

## Prospective chapter

| component | purpose | state |
| --- | --- | --- |
| literature notes, evidence matrix and BibTeX | verified source corpus | 44 sources; case-crossover and distributed-lag design references still to be added |
| Viefhues and Eryilmaz source reading | motivation for the regional question | incorporated; no CO2 analysis in draft 0.9 |
| `31_event_study_gates.py` | audits the binding regional inputs | implemented for draft 0.8 floors; **must be updated to draft 0.9** |
| `32_lanuk_feasibility.py` | audits the German route | implemented; relevant only to the conditional distance module |
| `35_audit_waterschap_delivery.py` | raw availability and provider-sourced station QA | implemented; timezone, zero and cohort unresolved |
| `36_design_recovery.py` | design simulations and stage/discharge comparison | implemented 2026-09-17; to be reviewed against draft 0.9 |
| ERA5-Land raw archive | relative humidity and pressure | complete; 300/300 months audited |
| `src/event_study.py` | episodes, storms, censoring, quiet controls, pressure residuals | episode and storm functions reusable; quiet controls and pressure residuals superseded |
| radar rainfall and cross-border catchments | principal exposure | not acquired |
| hourly discharge ingest and rating eras | outcome series | not built; awaits source semantics |
| at-risk hours and strata | case-crossover comparison set | not implemented |
| distributed-lag conditional Poisson models | primary and secondary estimands | not implemented; reference implementation or validated equivalent to be chosen |
| year-month block bootstrap | uncertainty | not implemented |
| July 2021 regional anchor | descriptive trajectory | not run |
| conditional distance module | ordered-pair slope if LANUK passes before lock | inactive |

No prospective figure or outcome table exists. The protocol is unlocked.
LANUK products under `results/feasibility/` are input-QA artifacts, not chapter
findings.

## Supporting data acquisition

- `01_ingest_iot.py` and `src/io_iot.py`: later Kerkrade IoT for the conditional
  case;
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
scientific verification.

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
