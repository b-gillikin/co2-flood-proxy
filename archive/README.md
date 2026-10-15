# Archive

This directory is a historical record of retired analyses. Nothing here is
imported, tested or expected to run against the current data layout. Archived
outputs document what was tried; they are not active chapter findings.

`retired-directions/2026-retrospective-high-water/` indexes the case-crossover,
cross-tributary, prediction, atmospheric, CO2/pressure, Maas and early
basin-AI branches retired when the basin-aware AI design became active.

Retired directions include:

- anomaly detection, SARIMAX, Kalman filtering and detector ensembles;
- RIVM cross-site transfer and generic substitution/model frameworks;
- distributed-lag, groundwater-state and barometric-response analyses;
- monitoring-network similarity, catchment signatures and correlation length;
- operational readiness/report-generation machinery and an obsolete chapter
  draft.

Several later files were deleted rather than copied here because Git history is
the cleaner archive. These include the hourly transfer classifier, Fase and
catchment-similarity code, the three-gauge soft-label event catalogue, the
full-period barometric baseline and the unreproducible later-record precursor
script.

On 2026-08-08, ignored outputs left behind by the retired baseline, precursor,
soft-label and hourly-classifier lanes were moved to
`results/retired_2026_08_08/`. They remain recoverable here but have no live
writer and are not prospective event-study results.

On 2026-09-18, `01_ingest_iot.py` and `33_ingest_viefhues_iot.py` were added.
These normalise the later Kerkrade IoT stream and the Viefhues thesis package.
They are untested at the chapter level and no longer read by the live
pipeline: draft 0.9 (2026-09-18) removed the conditional Kerkrade CO2 case
they served, and the active chapter analyses no CO2 (see the archived
`retired-directions/2026-retrospective-high-water/docs/chapter-synthesis.md`).
Viefhues and Eryilmaz remain the chapter's motivation in prose; the code that
reproduced their source data as a provenance check is preserved here, not
deleted, because it documents real findings (K4 is the usable sensor; the
pre-15-May-2021 lineage cannot be reconstructed from the delivered package).
`src/io_iot.py` stays in `src/`, not here: `infrastructure_tests/test_io_data.py`
still exercises retained IoT ingestion.

On 2026-10-15 the disabled Kerkrade daily email and hourly/monthly weather
collectors, their historical deployment scripts and daily-summary test moved
to `retired-kerkrade-alert-weather/`. The Azure Function App still runs the
IoT timer from `kerkrade_data/`; its storage and raw records remain in place.

The completed four-arm RAG feasibility pilot and its pilot-only contracts
moved to `retired-basin-ai-pilot/`. The basin graph and representation contract
remain live because the analogue analysis reads them.

The reasons and numerical history are preserved in `docs/decisions.md`. The
live design is `docs/limburg-historical-analogue-active-design-2026-10-13.md`; the live
file inventory is `docs/analysis-inventory.md`. Ruff intentionally excludes
this directory.

The five dated peer-review passes from 2026-08-06 through 2026-08-08 are under
`archive/docs/reviews/`. They informed the live reset but are not competing
chapter specifications. Their criticisms and resulting decisions remain
traceable in the append-only decisions log.

## Analogue development archive — 2026-10-14

The [analogue evidence index](../docs/limburg-analogue-evidence-index-2026-10-14.md)
archives earlier analogue stages by status in place. Those scripts and outputs
remain reproduction dependencies, so they are not moved into this retired-code
directory or removed from testing. This differs from the retired directions
above: valid mean-readout ablations remain supporting evidence.
