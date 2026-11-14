# Limburg handoff — corrected GEOGLOWS Stages 1–2

Updated 14 November 2026. Brian writes dissertation prose and sends all emails.

## Active design

[Corrected protocol](limburg-geoglows-stages12-protocol-v2-2026-11-14.md) and
[configuration](../config/limburg_geoglows_stages12_v2.json): paired observed versus
GEOGLOWS discharge on seven tributary targets and nine active Q feeds including
two Meuse context sites. Eys is excluded from targets and predictors in both
stages; the original data remain. Full 481-storm census, 13,468 opportunities
per stage. Presto and AnySat features are reused, not re-extracted.

## Current state

All six [audit findings](reviews/limburg-geoglows-code-design-audit-2026-11-14.md)
are addressed; see [resolution](reviews/limburg-geoglows-audit-corrections-2026-11-14.md).
Seven-target preparation and complete input audit pass. 57 tests, Ruff and the
isolated dependency check pass. Corrected outputs are under
`results/limburg_geoglows_stages12_v2/`; the pinned acquisition remains under
`data/raw/limburg_geoglows_stages12_v1/`. Actual execution status is recorded in
v2 `readiness.json`: **not started**, no active jobs, no full model fits. Roughly
79 GiB free; preserve the 50-GiB reserve. No cloud jobs or alerts were started.

## Next action

Full fitting and review remain explicit subsequent actions. From this repo:

```sh
.venv-geoglows/bin/python scripts/260_setup_geoglows_comparison.py readiness
.venv-geoglows/bin/python scripts/260_setup_geoglows_comparison.py run
.venv-geoglows/bin/python scripts/260_setup_geoglows_comparison.py review
```

Training/validation cohorts are matched; unsupported satellite rows use causal
hydrology/raw fallbacks. High-water, full-census and EO-supported results remain
separate; sparse bootstrap draws cannot silently drop sites. The retrospective
GEOGLOWS replay does not establish as-issued forecasting or live warning value.
No new dataset, encoder family or Stage 3 has been added by these repairs.

## Preserved history

The superseded eight-target configuration/results remain under their original
v1 names. Previous one-pager/handoff snapshots are in
`archive/retired-directions/2026-11-14-geoglows-eight-target-setup/`.
[Earlier research account](limburg-short-research-account-2026-11-14.md) retains
completed analogue, scarcity, model-specific correction and mapping evidence.
Older scientific findings were not recalculated or overwritten.
