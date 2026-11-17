# Limburg handoff — DISE-inspired reconstruction preparation

Updated 16 November 2026. Brian writes dissertation prose and sends all emails.

## Current direction and state

Independent DISE-inspired adaptation accepted; audit corrections implemented in v2. [Design](limburg-dise-research-design-2026-11-16.md),
[configuration](../config/limburg_dise_v2.json), [preparation report](limburg-dise-preparation-2026-11-16.md).
Daily reconstruction is a deliberate outcome change from the completed next-24h
assessment. The source authors' code returned 404; it is not a dependency.

Local daily inputs, seven-gauge weather and common-source descriptors are ready.
The corrected local held-Wurm 2021 benchmark completed **152 fits in 32.19 s**,
including the article-faithful sensitivity. All valid January days are restored;
reconstructed-discharge RMSE (mm/day) drives primary early stopping/selection. Fixed scoring
populations, saved p99 flags/thresholds and local/donor calibration are implemented.
The original benchmark remains under v1. See the
[implementation record](limburg-dise-audit-corrections-2026-11-16.md).

Regional topology screening yields 336 provisional donors, 50 reserved external
records, four local connected-section exclusions and one source-network gap.
44 geometry/coverage flags remain explicit; proximity alone does not approve a
model identity. Source clock is verified from the primary paper: UTC hour-end
means. Provider quality remains qualified, not inferred from finite values.

All **386 mapped nonlocal source records are acquired and checksum-verified**,
with zero failed transfers and 821,400 complete daily observations in 2018–2024.
Twelve records have no complete daily overlap in that period; these are coverage
cases, not transfer failures. Raw snapshots use 3.66 GiB; daily tables use 84 MiB.
The observation-only acquisition is complete. **Matched regional model/weather/
AlphaEarth and conventional-control inputs are complete and hash-verified**.
All acquisition workers have finished; the first regional-fold benchmark is now running. Input-acquisition progress is
`results/limburg_dise_v2/regional_inputs/progress.json`. The observation receipt
remains under `regional_acquisition_progress.json`. Data location:
`data/raw/limburg_dise_v2/camels_timeseries/`, daily records under
`results/limburg_dise_v2/regional_observations/`. Disk reserve remains 50 GiB;
74.8 GiB was free at verification; no other-chapter data were changed or Azure
job started. See the [verification receipt](reviews/limburg-dise-corrections-verification-2026-11-16.json).

## Spatial review completed and next work

[Spatial resolution and strata](limburg-dise-spatial-resolution-2026-11-16.md)
completes the original 44-flag review: 32 directional/partial cases are stratified,
11 remain explicitly uncertain, and the search-boundary case is recovered as a
high-overlap proxy. Eight additional station/reference-location conflicts were
identified. All cases remain represented; uncertainty is not a blanket stop.

The current resolved pool is **387 gauges** (337 provisional donors, 50 external),
with 344 high-overlap and 331 high-overlap/location-consistent sensitivity records.
One added gauge shares an existing model reach; original matched IDs/holdout roles
are unchanged. The resolved input tables are under
`results/limburg_dise_v2/regional_inputs_resolved_v1/`; original 386-record receipts
above remain historical acquisition evidence. The first regional-fold benchmark
is now active; no full multi-year comparison has launched.

[Regional preparation and benchmark](limburg-dise-regional-benchmark-2026-11-16.md):
1,151,268 feature rows, actual local-recipe parity audited, 51 tests passing.
One worker/two CPU threads is running 152 fits for the Wurm/external 2021 fold.
Progress: `results/limburg_dise_regional_benchmark_v1/benchmark_wurm_external_2021/progress.json`.
Do not start a duplicate worker or edit pinned fitting inputs/code during execution.
After completion, inspect capacity/tree caps, runtime, coverage and paired results
before scaling. A favourable result is not a gate.

## Commands

Use `.venv-dise` (XGBoost 3.1.2/scikit-learn 1.7.2); prior environments are
unchanged. `scripts/264_prepare_dise_corrections.py` handles corrected features
and regional physical screening; `scripts/265_benchmark_dise_corrected.py`
verifies/reuses its corrected benchmark; `scripts/266_acquire_dise_observations.py`
handles resumable source acquisition; completed records are verified and reused.
The old scripts 262/263 retain their v1 roles and are not the active continuation.

## Completed earlier work

GEOGLOWS seven-target v2 finished all four fits and review on 14 November 2026;
[qualified results](limburg-geoglows-first-results-2026-11-14.md) and all source
configurations remain. Earlier analogue, scarcity, model-specific correction and
mapping results are retained in their original directories and dated records.
Do not restart those queues or compare their next-24h scores directly with daily
reconstruction. The canonical current-study pointer is
`config/limburg_current_study.json`.
