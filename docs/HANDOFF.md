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
**No acquisition or fitting workers remain active.** Acquisition progress is
`results/limburg_dise_v2/regional_acquisition_progress.json`. Data location:
`data/raw/limburg_dise_v2/camels_timeseries/`, daily records under
`results/limburg_dise_v2/regional_observations/`. Disk reserve remains 50 GiB;
74.8 GiB was free at verification; no other-chapter data were changed or Azure
job started. See the [verification receipt](reviews/limburg-dise-corrections-verification-2026-11-16.json).

## Next work

Resolve or explicitly stratify mapping-identity flags and obtain the matched regional model Q, common weather/landscape/AlphaEarth inputs.
Then benchmark the actual regional training size before the full comparison.
A favourable local result is not a gate. Preserve adverse calibration cases
and the separate clean/unknown-quality strata.

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
