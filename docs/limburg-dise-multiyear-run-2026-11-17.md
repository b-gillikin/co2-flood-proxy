# DISE multiyear and river-group run — Step 2

17 November 2026. Brian authorized Step 2 of the
[saved plan](limburg-dise-four-step-plan-2026-11-17.md). Internal research aid;
Brian writes dissertation prose. Steps 3–4 remain pending.

## Executable comparison

- **Local test years:** 2021–2025, all seven gauges/five river groups.
- **Temporal regime:** train with permitted local/regional donor history; test
  the local gauges in a later year. This has historical target-label access.
- **Spatial regime:** separately withhold Geleenbeek, Geul, Gulp, Voer and Wurm
  from every fit and validation fold. All three Wurm gauges leave together.
- **External test:** Ahr/Erft/Sieg, 2021–2024, once per year using the temporal
  model. No external observed Q enters any fit, validation, calibration or
  predictor. External results from the earlier Wurm diagnostic are preserved
  but are not counted again as the primary external test.
- Train on 2018 through Y−2; validate on Y−1; test on Y. Earlier evaluation years
  can enter later training as history: this is rolling evaluation, not five
  untouched independent trials. All eligible January dates remain.
- Four feature arms, both existing selection policies, four candidates, four
  topology-preserving inner folds and three final seeds remain. Every job has
  the same 3,000-tree maximum. No threshold or tuning choice uses test outcomes.
  The four inner folds apply uniformly to both outer regimes in this executable
  run, rather than using a separate temporal-only tuning recipe.

There are **30 outer jobs and 4,560 fit slots**. The completed held-Wurm 2021
capacity run supplies 152 verified slots; **4,408 fits are new**. Its local
metadata, all seed predictions, selected specifications, FDC predictions and
33 local metric records reproduce. The original inner-fold map is preserved;
previously withheld Wurm is added deterministically without rebalancing any
existing group. The new map is shared by all arms and years.

## Data and evaluation

The frozen census contains **81,857 verification rows**: 12,362 local gauge-days
in each of the separate temporal/spatial regimes, plus 57,133 external gauge-days.
Repeated local days in the two regimes answer different questions and are never
combined as independent observations. An assertion prohibits repeated gauge-days
within either regime. No external 2025 labels are invented.

All requested gauge/year pairs appear in `coverage.csv`, including those with
no complete observed/model pairs. Their missing verification is not filled or
misclassified as failed prediction. Fixed mapping/quality strata and clean-high-
water sensitivities remain. Per-year evaluator-only p99 uses prior target
history from 2018 through Y−1. Unknown threshold/quality stays unknown.

Raw GEOGLOWS, donor-FDC and local clean-label FDC references remain. In temporal
jobs, donor selection explicitly excludes the target's entire river group:
otherwise it could select the target itself and falsely claim no target-label
access. This preserves the original spatial/external donor recipe, whose fitting
population already excludes the target river. Local FDC is still explicitly
target-calibrated. A regression test changes Wurm labels and confirms the Wurm
donor reference is unchanged.

Per-fold predictions retain mm/day and m³/s, all seed arrays, p99/quality flags,
selected models, tuning receipts, row membership/weights and input/code/package
identities. Save per-year and pooled point estimates. Dependence-aware paired
uncertainty and interpretation across storms/years/rivers remain **Step 3**;
Step 2 does not substitute independent-day confidence intervals. The outcome
remains retrospective daily reconstruction, not an as-issued warning forecast.

## Runtime, storage and recovery

Two local CPU jobs, two XGBoost threads each; no GPU or Azure compute. The Mac
has 36 GiB memory and 12 CPU cores. The benchmark peak was 5.88 GiB per job;
later training populations are larger, so monitor measured worker peaks.

The initial planning allowance is **24–48 awake-machine hours**, to be revised
from completed fresh jobs. Later folds have up to 663,000 training rows versus
235,000 initially. Percentage progress counts fit slots, not equal-duration work.

All inputs are held; no downloads or encoder extraction. Retain tuning records
instead of every disposable tuning model, while keeping all selected final
models/predictions. Plan roughly 2–6 GiB of new output, with substantial headroom
at about 81 GiB free. The existing **50-GiB reserve** remains checked. No current
input/output deletion, other-chapter cleanup or offload is needed.

Each fit has an atomic receipt. Final models/predictions have verified hashes;
completed jobs have manifests. Resuming verifies identical code/data and uses
completed fits, not favourable rerolls. Failed jobs stay recorded; successful
independent jobs continue, and incomplete queues cannot be reported complete.
Sleep/lid closure pauses local computation; checkpoints cover process restart.
No email alerts or emails are sent by this queue.

From the chapter directory:

```sh
.venv-dise/bin/python scripts/276_run_dise_multiyear.py prepare
/usr/bin/caffeinate -i .venv-dise/bin/python -u scripts/276_run_dise_multiyear.py run
```

The same run command resumes after interruption. Do not start a duplicate
coordinator or edit pinned fit code/config while jobs are active. `caffeinate`
prevents idle sleep while open; it does not override lid-closed sleep.

Progress: `results/limburg_dise_multiyear_v1/progress.json`.
Individual job progress, manifests and outputs: `jobs/<job-id>/` below that root.
Logs: `results/limburg_dise_multiyear_v1/logs/`. On success the coordinator joins
the full prediction census and writes `completion.json`, `metrics_by_job.csv`
and `pooled_metrics.csv`, then marks Step 2 complete. It does not launch Step 3.

[Readiness/reuse verification](reviews/limburg-dise-multiyear-readiness-2026-11-17.json):
63 relevant tests and Ruff pass; complete held-Wurm 2021 reuse path verified
before launching fresh fits. Implementation commit: `ff9312c`. The two-worker
queue launched on 17 November 2026; no fresh multiyear findings are claimed yet.
