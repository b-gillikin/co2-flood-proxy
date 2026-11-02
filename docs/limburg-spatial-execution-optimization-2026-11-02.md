# Spatial execution optimization — 2 November 2026

Internal execution/research record. No dissertation prose. The previous serial
queue's projected runtime is impractical. Version 4 preserves all four tasks,
all 53 task/event folds, all 1,908 final fold/budget/seed fits,
the three seeds, 100/20/5% label budgets, and the existing
50/100-epoch ceilings. No event subsampling or scientific early stopping added.

## Execution changes

- Memory-mapped exact float32 normalized inputs and original unknown-label masks
  cover all 446 hand-labelled chips (each applicable task) and 5,000 radar-change
  records. Prithvi keeps the original 512px source until augmentation, then
  interpolates to 224px. Preprocessing and metadata match the original loader.
- TerraMind's frozen encoder is cached for all eight existing rotation/flip
  combinations, before its trainable neck/decoder. 446 files retain four selected
  1,024-token, 192-channel layers for each augmentation, about 11.2 GiB. The cache
  does not replace training the decoder. Existing Galileo and Copernicus frozen
  spatial caches are retained. **Prithvi's fine-tuned backbone is not cached.**
- Two CPU lanes handle pixel-linear fits and Galileo's small frozen-token probe;
  each has two Torch threads. One exclusive MPS lane handles the heavier neural
  fits, with two persistent input workers and prefetch. These input workers are
  not additional model fits. Local applications use the selected fit's device.
- Validation/test are batched without dropping records. Training retains the
  original deterministic augmentation draw order and complete epoch census.
  GPU loss readback is deferred to the epoch boundary; nonfinite losses and
  optimizer update counts remain explicit.
- Non-divisible adaptive averaging uses the same floor/ceil bins via separable
  on-device matrix products, avoiding CPU transfer. Tests check values,
  gradients, parameters and unchanged checkpoint keys.
- Cached frozen encoders are omitted from task checkpoints, while their exact
  held backbone hashes remain in manifests. Every trainable parameter and buffer
  remains in task states; reloading permits only missing `encoder.*` keys.
- All lanes share one compression/upload/readback lock. Only checkpoints covered
  by a verified remote recovery receipt can be retired. The 50 GiB reserve and
  5 GiB launch headroom remain. No other chapter data is changed.

## Explicit optimizer changes, not lossless speed claims

Training batch size is common to all learners within a task: TerraMind 8,
Prithvi 2, Galileo 256, Copernicus 16. Galileo previously used 64 and Copernicus 2.
These two changes alter the optimizer trajectory and BatchNorm statistics;
therefore v4 is a distinct comparison version, with its own fits for every
learner. Do not pool earlier fitted scores into v4. Effective epochs, learning
rate grid for seed42 and reduced-label fits, validation selection, label masks and independent final seeds remain.

All production fits stay float32. Short profiling covered mixed precision,
channels-last and foreach. Larger batches hurt Prithvi; channels-last slowed
other paths or failed. Neither is applied blindly. Some older runtime builds
lack `torch.amp.GradScaler`; FP32 now has a compatible unscaled path. Mixed
precision is not adopted from five-step timing tests alone.

## Verification and timing evidence

`tests/test_applied_fast_data.py` checks held raw inputs/masks/coordinates,
legacy augmentation order, complete batching, event-confusion equivalence under
batched scoring, and preservation of the full research grid. Pooling tests check
forward and gradient equivalence. The actual model runtime's two persistent
spawned workers passed two epochs with the complete ordered census. The older
conda test environment exposes an OpenMP conflict for spawned Torch workers;
production prefetch was verified in the separate maintained spatial runtime,
without the unsafe duplicate-library workaround.

An independent TerraMind check produced identical output and all 34 trainable
parameter gradients with and without the encoder cache on a held training
record. This is bounded parity evidence, not a proof that every future GPU
arithmetic result is bit-identical. Prithvi's CPU-resampled loss masks retain
nearest-neighbour semantics. Actual one-epoch, three-candidate CPU smoke runs
for Galileo and Copernicus completed selected-test and full-census verification.
They are marked engineering runs and excluded from final scientific tables.

Short steady-state timings, excluding setup/validation/local application:

| Path | Earlier timing | Optimized timing | Interpretation |
| --- | --- | --- | --- |
| TerraMind native MPS | ~12.4 images/s, uncached encoder | ~42.5–47.1 images/s, cached, FP32 | Around 3–4x for this training path |
| Copernicus pixel-linear | Old full epoch ~32–49 s for 4,857 records | Cached CPU smoke later candidates ~8 s including training and validation | Different batch; engineering check only |
| Galileo pixel-linear CPU | — | Cached smoke later candidates ~4 s including training and validation | Extra CPU capacity rather than occupying MPS |
| Larger U-Nets / Prithvi fine-tuning | Still computation-heavy | No comparable blanket speed-up established | Need full-fit measurements |

Profiling receipts, including failed settings and earlier startup/skipped-update
limitations, live in `results/applied_optimization_2026_11_02`. Five-step timing
results are **not** a reliable whole-grid ETA. The remaining grid may still be
lengthy; report actual full-fit throughput before promising completion in days.
The inherited Copernicus classifier completed its original fit and local/physical
application without restarting its training. Its remote bundle passed full readback verification.

## Durable entry points

Prepare: `scripts/222_prepare_optimized_spatial_queue.py`.
Run/resume: `scripts/223_run_optimized_spatial_queue.py --run`.
Master manifest: `results/applied_study_v4/execution-plan.json`.
Per-lane controllers: existing script214, with independently locked state and
one global MPS ownership lock. Current shared progress: `results/applied_study_v4/full-label-tuning-reuse-v1/progress.json`.
The existing `results/applied_study_v3/current-queue.json` pointer identifies the
current version. Intermediate readouts use the master plan, not a single lane.

## Approved full-label tuning reuse and runtime reconciliation

Brian approved learning-rate reuse for full-label seed repeats. Each task,
learner and held fold tunes the original three-rate grid on seed42 validation;
seeds1729/31415 each train a fresh model with its own RNG/augmentation using that
selected rate. Each repeat still chooses its checkpoint on its own validation
trajectory. The 20%/5% label masks retain independent tuning at every seed.
No held-test score is read to select a rate. The helper requires a verified
source fit, identical task/fold/architecture/batch/precision/input membership,
the complete three-candidate source ledger and its validation winner. Retiring
an already-backed-up source checkpoint does not prevent reading its provenance.

This removes848 candidate fits: **5724→4876**, keeping1908 final fits. It is a
protocol refinement, not evidence of a uniform848/5724 reduction in wall time.
The current manifest is
`results/applied_study_v4/full-label-tuning-reuse-v1/execution-plan.json`.
The current pointer remains the canonical discovery mechanism.

The first Galileo MPS compact-U-Net attempt failed all three candidates before
an optimizer update: its older Torch build lacks the optional foreach multiply
operator. The failed ledger is retained. Foreach is disabled only for Galileo
MPS; its explicit replacement output is under `tuning/foreach-recovery-v1`.
Other runtimes retain the tested option. CPU fits and the next Prithvi GPU fit
continued unchanged while controllers were versioned and reattached; no fitted
state or successful epoch was discarded. Pre-reconciliation progress snapshots
and original source snapshots are retained. Tests now check this exception.

67 targeted tests pass. The completed generator scripts218/220 are retained
verbatim so their recorded extraction hashes still identify the executed code;
218 retains one harmless unused-import lint finding. The remaining modified/new
runtime and test files pass Ruff. Detailed timing outputs remain evidence of
particular paths, not a whole-grid completion guarantee.


## Remaining compute problem

Script225 extrapolates actual matching-batch training timings over the full
4876-candidate workload and all selected training records. It gives roughly
**60 GPU-days of training alone**, before validation, test, local application or
interruptions. Copernicus native contributes about28.5days and its standard
U-Net about11.9days. This is an optimistic workload extrapolation from short
profiles, not a calendar forecast. Two CPU lanes overlap other fits; they do not
remove these exclusive-GPU calculations. Caching/batching materially improve
execution but do not solve the full grid's practicality. Further substantial
savings require an explicitly considered repeated-fit design change or faster
compute, not a promise that the current unchanged workload finishes in hours.
The current fits continue; no new scientific stopping gate was imposed.
