# Archive

This directory is a historical record of analyses retired between 2026-08-05
and 2026-08-07. Nothing here is imported, tested or expected to run against the
current data layout. Archived outputs document what was tried; they are not
chapter findings.

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
they served, and the chapter analyses no CO2 (`docs/chapter-synthesis.md`).
Viefhues and Eryilmaz remain the chapter's motivation in prose; the code that
reproduced their source data as a provenance check is preserved here, not
deleted, because it documents real findings (K4 is the usable sensor; the
pre-15-May-2021 lineage cannot be reconstructed from the delivered package).
`src/io_iot.py` stays in `src/`, not here: `infrastructure_tests/test_io_data.py`
still exercises it to protect the deployed daily-summary Azure function, which
is a maintained asset independent of this chapter. This move does not affect
the Azure collection infrastructure in `kerkrade_data/` and `iot-device-data/`.

The reasons and numerical history are preserved in `docs/decisions.md`. The
live design is `docs/chapter-synthesis.md`; the live file inventory is
`docs/analysis-inventory.md`. Ruff intentionally excludes this directory.

The five dated peer-review passes from 2026-08-06 through 2026-08-08 are under
`archive/docs/reviews/`. They informed the live reset but are not competing
chapter specifications. Their criticisms and resulting decisions remain
traceable in the append-only decisions log.
