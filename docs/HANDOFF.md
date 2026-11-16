# Limburg handoff — DISE-inspired reconstruction preparation

Updated 16 November 2026. Brian writes dissertation prose and sends all emails.

## Current direction and state

Independent DISE-inspired adaptation accepted. [Design](limburg-dise-research-design-2026-11-16.md),
[configuration](../config/limburg_dise_v1.json), [preparation report](limburg-dise-preparation-2026-11-16.md).
Daily reconstruction is a deliberate outcome change from the completed next-24h
assessment. The source authors' code returned 404; it is not a dependency.

Local daily inputs, seven-gauge weather and common-source descriptors are ready.
One complete local held-Wurm 2021 nested benchmark completed 76 fits/three seeds
in 13.44 seconds. Results/receipts are under
`results/limburg_dise_v1/benchmark_local_wurm_2021/`; progress is **completed**.
No full regional run is queued or active. The failed initial serialization
attempt is preserved separately, not substituted for a completed result.

Regional metadata and selective ZIP access are verified: 286 donor candidates,
49 external candidates (Ahr/Erft/Sieg), 52 overlap-review cases. Neither observed
quality nor model-reach correspondence is certified by these candidate counts.
The new sources total about 67 MiB; approximately 79.3 GiB disk remains free.
Preserve the 50-GiB reserve. No other-chapter data were changed.

## Next work

Regional topology/reach mapping and candidate membership; primary source clock/
quality documentation; selected donor/external observations, matched model Q,
common weather and landscape acquisition. Keep external labels out of training.
Resolve regulation/descriptor limitations; add calibration references and full
paired uncertainty/measurement reporting to the regional runner. Benchmark actual
regional training size before scheduling the complete two-CPU-worker comparison.
A favourable local result is not a gate.

## Commands

Use `.venv-dise` (XGBoost 3.1.2/scikit-learn 1.7.2); the prior environments are
unchanged. Explicit preparation phases are `metadata`, `regional`, `sample`,
`weather`, `attributes`, `daily` in `scripts/262_prepare_dise.py`.
`scripts/263_benchmark_dise_fold.py` verifies/reuses its completed local benchmark
when identities agree; it does **not** launch a regional comparison.

## Completed earlier work

GEOGLOWS seven-target v2 finished all four fits and review on 14 November 2026;
[qualified results](limburg-geoglows-first-results-2026-11-14.md) and all source
configurations remain. Earlier analogue, scarcity, model-specific correction and
mapping results are retained in their original directories and dated records.
Do not restart those queues or compare their next-24h scores directly with daily
reconstruction. The canonical current-study pointer is
`config/limburg_current_study.json`.
