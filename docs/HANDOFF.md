# Limburg handoff — DISE-inspired reconstruction

Updated 17 November 2026. Brian writes dissertation prose and sends all emails.

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
All acquisition workers have finished; the first regional-fold benchmark is complete. Input-acquisition progress is
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
is complete; no full multi-year comparison has launched.

[Regional preparation and benchmark](limburg-dise-regional-benchmark-2026-11-16.md):
1,151,268 feature rows, actual local-recipe parity audited, 51 tests passing.
The Wurm/external 2021 fold completed 152 fits; no worker is active.
Progress: `results/limburg_dise_regional_benchmark_v1/benchmark_wurm_external_2021/progress.json`.
The completed run is frozen; preserve its inputs/code identity and outputs.
The first-fold review and capacity check are now complete; see the authorized
continuation below. A favourable result is not a gate for the saved next steps.

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


Completion update — 17 November 2026: the first regional-fold benchmark finished
all **152 fits**, calibration and scoring in **39.3 minutes**. Input/output hashes
reverify; 303 metric records and the prediction/calibration tables are available.
No workers remain active. This is one 2021 fold; the results and capacity review
is now complete, with a fair capacity extension recommended before full scaling.


## Reviewed first-fold results — 17 November 2026

[Results, spatial strata and tree limits](limburg-dise-regional-results-review-2026-11-17.md).
All-day Wurm E gain is substantial (23.1%); external mean is small (2.9%) and
Erft-driven. High-water gains are small and selection/measurement-sensitive;
corrections worsen some severe errors relative to raw GEOGLOWS. 26/128 tuning
fits are capped, including selected H+E/article-faithful cases and a close
primary H+A+E runner-up. Recommended one fair 3,000-tree capacity check, then a
locked multi-year comparison. Review artifacts are
under `results/limburg_dise_regional_benchmark_v1/review_2026_11_17/`.

## Authorized continuation — 17 November 2026

The [four-step plan](limburg-dise-four-step-plan-2026-11-17.md) is saved in
`config/limburg_dise_four_step_plan_v1.json`. **Step 1 is complete; Step 2 is
running; Steps 3–4 remain pending.**
The capacity run uses `scripts/275_run_dise_capacity_check.py` and
`config/limburg_dise_capacity_v1.json`, with results/progress under
`results/limburg_dise_capacity_v1/`. The fixed 3,000-tree reuse control matches
the original stopping point and validation predictions exactly. All 26 previously
capped jobs were refit from scratch; 101 verified early stops were reused. Four
selected specifications changed, requiring 12 new final fits; 12 were reused.
The original benchmark is preserved. The run finished in 22.1 minutes with one
CPU fitting worker/two threads. No workers were active at that completion. No GPU, download
or cloud task was used. Fifty-four relevant tests and Ruff pass.

The same test populations and raw/FDC controls reverify. No selected candidate/fold
fit remains capped; three unselected sensitivity fits do. Primary AlphaEarth
all-day MAE gains are now 21.3% Wurm/2.3% external; high-water MAE changes are
−2.5%/+1.7% improvement, respectively. [Results and verification](limburg-dise-capacity-check-2026-11-17.md)
explain the distinct RMSE results and continuing measurement/one-year limitations.
Rerunning the capacity command verifies completed outputs without refitting.
The machine-readable plan/current-study status was updated. No further cap
increase was launched. The separately authorized Step 2 follows below.

## Active Step 2 queue — 17 November 2026

[Multiyear design/run record](limburg-dise-multiyear-run-2026-11-17.md).
`scripts/276_run_dise_multiyear.py` uses `config/limburg_dise_multiyear_v1.json`.
Two CPU workers/two threads each; no GPU or new download. The queue has 30 outer
jobs/4,560 fit slots, including 152 verified slots reused from the 2021 Wurm
capacity result. Sixty-three relevant tests and complete reuse verification pass.
Fresh jobs retain the same four arms, policies, candidates, seeds and 3,000-tree
budget. Do not change pinned code/config while they run.

All 81,857 verification rows are retained across the separate regimes. External
gauges have no fitting-label access and are evaluated once per 2021–2024 year
using the temporal model; spatial jobs evaluate only the held local river.
Coverage ledgers retain missing-verification gauge/years. Donor FDC explicitly
excludes the target river in temporal jobs, preventing self-donor label leakage.

Progress: `results/limburg_dise_multiyear_v1/progress.json`; individual jobs under
`jobs/`, worker logs under `logs/`. Each fit checkpoints; job manifests preserve
inputs/code/output hashes. The same `run` command resumes completed work after
interruption. The coordinator aggregates point estimates and marks Step 2
complete on success. It does not launch Step 3 or send emails. Keep the existing
50-GiB disk reserve; estimated new output is 2–6 GiB, with about 81 GiB free at
launch. No cleanup/offload or other-chapter changes were needed.
