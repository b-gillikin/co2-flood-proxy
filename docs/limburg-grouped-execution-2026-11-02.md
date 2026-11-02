# Practical whole-event spatial comparison — 2 November 2026

Internal design/execution aid; Brian writes dissertation prose. This supersedes
the v3/v4 repeated-fit execution design. Previous completed and surviving fits
remain supporting work, with their original manifests and failure records.
The new grouping and stopping choices were made for computational practicality,
not from a preferred held-test accuracy result. The study remains exploratory;
there is no untouched/preregistered evaluation claim.

## What remains

All four spatial tasks and four learned configurations per task remain, with
physical controls, three optimization seeds and 100/20/5% training-label budgets.
All446 hand-labelled chips and5000 radar-change records remain in evaluation.
Every source event and chip is tested exactly once; no test-event sample is drawn.
Labels, unknown masks, input normalization, band order, encoder settings and
catchment/local imagery pairing are unchanged. No new data request or model.
Completed ten-encoder discharge analyses are unaffected.

## What changes

1. **Five whole-event folds per task.** `GroupKFold(5)` assigns complete source
   events to count-balanced groups using only event identity and record count.
   One group is tested, the next whole group is validation, and three groups
   train. Each event is tested once and validated once. No tile from the same
   event crosses roles within a fold. This is720 final fits instead of1908,
   with20 deterministic physical calibrations instead of53.
2. **Fixed nested annotation subsets.** The source-identity hash ordering within
   each training event is fixed at mask seed42. The three optimization seeds
   use the same selected chips at each label budget. 5% is nested in20%, nested
   in full available fold training labels. Small events retain at least one
   labelled chip; actual chips/pixels/validation labels are reported, so these
   percentages are not exact percentages of the whole archive or label costs.
3. **Tune once per fold, architecture and label budget.** Seed42 retains the
   existing three-rate grid. Seeds1729/31415 each fit their own weights using
   the selected rate, and select their own validation checkpoint. Identical
   annotation masks allow reuse at reduced budgets without introducing labels
   from a different seed's subset. Membership and settings must match the
   verified source manifest. No held-test score selects a learning rate.
   This produces1200 candidate fits instead of4876.
4. **Validation-based stopping.** All candidates retain the original50-epoch
   ceiling, or100 for TerraMind. They can stop after10 epochs without an IoU
   improvement exceeding0.0001, once at least15 epochs have run (30 for
   TerraMind). The stopping anchor is monitored from epoch1; the minimum governs
   stop eligibility. The actual best validation checkpoint is retained, including
   smaller improvements. Undefined metrics cannot trigger a stop themselves;
   patience is measured in elapsed epochs and all undefined values remain visible.
   Existing failure handling remains. Same stopping settings within each task
   apply to encoders and conventional controls. Epochs run and termination reason
   are recorded. Schedules keep their original maximum-epoch horizon.

The conventional raw-input learners still receive the same task inputs and labels
as the model-specific encoder pipeline. Frozen TerraMind/Galileo/Copernicus caches
are reused. The fine-tuned Prithvi encoder is not cached. Mixed precision has not
been silently enabled. Two CPU fit lanes plus one MPS fit lane remain; input
prefetch, batched evaluation, exact pooling and verified checkpoint offload remain.

## Scientific interpretation and limitations

Five folds do not mean five flood events. They reduce how often a model is
trained; event-level scores remain available for every held event. Grouping by
whole events follows dependence-aware evaluation practice, and GroupKFold's test
sets cover each group once. **Five** is a pragmatic compute/design choice, not
a literature-imposed minimum or scientific gate. [GroupKFold documentation](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GroupKFold.html),
[Roberts et al., 2017](https://florianhartig.github.io/publications/roberts2017cross/).

Each fit now trains on roughly60% of source records/events, validates on20%, and
tests on20%, with exact group counts in the manifest. Earlier leave-event-out
fits often trained on a larger fraction. V5 measures held-event generalization
under this explicitly defined training design; do not pool its scores with v4
or attribute score changes solely to runtime engineering. The multi-event
validation group also makes tuning less dependent on a single validation event.

The three seeds quantify **optimization variability conditional on a fixed
label subset**. They no longer quantify variation from drawing different labelled
chips. That trade-off must appear in interpretation. Fold models share training
events, so folds/seeds are not independent extra floods. Existing event-bootstrap
intervals are conditional on fitted predictions; they do not incorporate the
uncertainty of refitting or changing fold assignments. Keep per-event and per-fold
contrasts visible and avoid overprecise general-population claims from five blocks.

Validation-based patience, minimum-change and best-checkpoint stopping are
standard tools; the exact15/30/10/0.0001 choices are declared adaptations, not
universal scientific constants. Stopping may miss a later recovery, and different
architectures can have different learning curves. Retaining the ceilings,
minimum training and complete learning curves makes that limitation inspectable.
[Keras EarlyStopping documentation](https://keras.io/api/callbacks/early_stopping/).
Successive-halving tuning was considered but not added: short-rung model rankings
and optimizer-state continuation would add another design/implementation change.

## Timing evidence

The same measured matching-batch profiles, applied to the new actual subsets and
candidate counts, project **11.13 GPU-days of full-epoch training**, compared with
60.55 before regrouping (about82% less). This excludes validation, tests, local
application, setup, backups and interruptions. It is neither a guaranteed upper
bound on calendar time nor a prediction of how often stopping will trigger.
Actual stopping can reduce training; actual contention can slow it. Do not promise
a shorter calendar ETA until production-fit timings are available.

Native Copernicus (~4.08days) and its standard U-Net (~1.71days), TerraMind's
standard U-Net (~1.66days) and Prithvi adaptation (~1.42days) dominate the full-
epoch projection. All comparators are retained. There is no automatic arbitrary
wall-time cutoff or favorable-result selection.

## Execution and checks

Prepare with script226; the frozen launch plan is
`results/applied_study_v5/ready-v2/execution-plan.json`. Grouped inventories live
in `results/applied_study_v5/evaluation`. Script227 prepares the20 matching physical
controls, starts the exclusive GPU queue and then starts the normal three-lane
supervisor once surviving CPU fits free their slots. The existing current-queue
pointer identifies preparation or active execution. Original v4 workers finish
and are verified/offloaded through dated supporting-drain controllers; no more
old-grid jobs are dispatched. Outputs are never mixed into primary v5 scores.

Real native TerraMind engineering fits at the5% budget passed early stopping,
full held-chip prediction checks, partial-checkpoint reload and same-mask
learning-rate reuse for seed1729. These3-epoch/large-min-delta runs only test the
machinery; they are labelled engineering and absent from the primary grid.
Regression tests cover disjoint event roles, once-only census, row-order/label-
independent grouping, nested identical masks across seeds, stop behavior,
configuration/membership rejection, raw-cache parity, batching and recovery.

## Disk cleanup

30.00 GiB of inactive embedding-extraction inputs were removed locally only after
checking local hashes against their already-held Azure objects and verified
remote receipts. 25,858 files were retired. The remote data remain; no source data
in another chapter were touched. Each removal batch first acquired a remotely
read-back recovery-intent ledger. A complete object was restored and rehashed.
Free space increased from65.33GiB to95.30GiB at completion.

Retained recovery records:
`results/disk-cleanup-2026-11-02/expansion/{removed.jsonl,progress.json,dependency-check.json,restore-test.json}`.
Restore a selected path with Azure CLI's Python and:

```
python scripts/182_restore_offloaded_expansion.py \
  --ledger results/disk-cleanup-2026-11-02/expansion/removed.jsonl \
  --path data/raw/limburg_eo_expansion/images/EXACT_SOURCE_PATH.tif --restore
```

Run without `--restore` to inspect bytes/paths first. Current applied-task rasters,
model weights, tensor caches and frozen encoder caches remain local. The50GiB
reserve plus5GiB launch headroom remains; no extra data download was needed.


At launch, all20 matching physical calibrations completed successfully; the new
three-lane queue started. All previous supporting-drain controllers completed
with verified offloads.75 targeted tests passed. The deletion/restore ledger and
restore helpers were additionally preserved in Azure with full archive/member
readback verification:
`applied-v2/results/f2c9fe9ffdef120a292e3802072cf348f8fb832a010e50741b7b314da8fab0f5.tar.gz`
in `stkerkradeprod01bg/limburg-compact-eo`. The small receipt stays local at
`results/disk-cleanup-2026-11-02/expansion-recovery.tar.recovery.json`.

The first launcher handoff briefly raced a second MPS controller against the
already-live owner. The controller lock prevented any duplicate fit, but global
status misclassified the rejected controller as a queue failure. Script227 now
waits for ownership publication; script223 recognizes and attaches to the actual
owner. A regression test covers the race. Ready-v2 changes only those controller
fingerprints and retains all live fits, original manifests and output paths.
