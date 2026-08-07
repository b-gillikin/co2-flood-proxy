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

The reasons and numerical history are preserved in `docs/decisions.md`. The
live design is `docs/chapter-synthesis.md`; the live file inventory is
`docs/analysis-inventory.md`. Ruff intentionally excludes this directory.
