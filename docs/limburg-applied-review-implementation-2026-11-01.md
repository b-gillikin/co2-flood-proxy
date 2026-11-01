# Applied review recommendations: implemented without reducing the study

1 November 2026. Internal execution specification; Brian writes dissertation
prose. Implements the [design/literature review](reviews/limburg-applied-design-and-literature-review-2026-11-01.md)
under Brian's instruction to retain the study's breadth and prioritize sound
results over economy. This is a methods/preparation update, not a mapping result.

## Scope retained

- All ten earlier encoder/discharge experiments remain in the chapter record;
  the pending Presto/Galileo extractions continue unchanged.
- All four spatial pipelines remain: TerraMind, Galileo, Prithvi and Copernicus-FM.
- The entire eligible benchmark census remains:446 water chips/11 events and
  5,000 radar-change records/20 activations. No test-event subsampling.
- All100/20/5% nominal **training-label** settings and seeds42/1729/31415 remain.
  Nested subsets preserve the training events, so actual chip fractions can
  exceed the nominal percentage. Both actual training and total selection-label
  fractions are now recorded.
- All local acquired scenes/references remain. Unobservable/unknown pixels stay
  visible in coverage accounting instead of being converted to dry ground.
- Full-label-first is an execution order, not permission to omit lower-label
  comparisons. The50-GiB reserve protects execution; it is not an analysis cap.

## Changes actually implemented

### Physical and stronger learned controls

[Physical runner197](../scripts/197_run_applied_physical_controls.py) uses the
same named-task tensors, source masks, held events and target semantics.

| Task | Added physical comparator |
|---|---|
| TerraMind paired inputs | NDWI/MNDWI on available optical bands, using the paired-input valid support. This control uses a declared subset of the available modalities. |
| Prithvi optical adaptation | NDWI/MNDWI using actual green, B8A NIR and SWIR inputs after the declared224px preparation; continuous indices are projected to the target grid before thresholding. |
| Galileo radar | VV or VH low-backscatter threshold, after inverting its native normalization to dB. |
| Copernicus radar change | Same pre/event VV/VH intensities, retaining author clipping; calibrated low-backscatter and change thresholds distinguish persistent dark water from new dark water. |

Optical selection considers33 thresholds from−0.8 to0.8 for each index; radar
water selection considers52 polarization/threshold combinations; change
selection considers60 polarization/threshold/drop combinations. These cheap
calibration candidates are fully recorded, not mislabeled as three neural
training trials. Threshold/index choice uses validation only. Each selected
control is tested once on the entire held event. Optical threshold0 controls
are also declared in advance and reported separately on test; no test-based
selection among those fixed controls is permitted.

These are transparent physical baselines, not reproductions of the complete
operational Copernicus GFM. SAR vegetation/urban/topographic ambiguities remain.
Single-date water classification does not establish new inundation.

[StandardUNet](../src/applied_unet.py) adds a conventional four-downsampling
32/64/128/256/512-channel encoder–decoder, with GroupNorm and bilinear upsampling,
to the existing compact U-Net and linear controls. All named pipelines and all
previous controls are retained. Scratch learners receive their own learning-rate
grid; the named pipeline is not allowed to dictate a tiny pretrained rate to
every comparator. Results remain pipeline comparisons, not causal attribution
to pretraining. No additional encoder, fusion or distillation experiment added.

### Complete batches, labels and tuning diagnostics

[Runner192](../scripts/192_tune_applied_water.py) now uses
[complete batches](../src/applied_evaluation.py). The last singleton is merged
with the preceding batch, which may be one larger than requested. No selected
example disappears. This preserves pooled batch-normalization compatibility.
All learners within a task use the same policy. Evaluation never drops records.

The manifest records training/validation/test chips, actual training fraction,
training-plus-validation fraction, source-grid labeled pixels and training
examples. Test labels are evaluation-only; chip counts are not annotation hours.

Each epoch records training loss, example count, no-valid-target examples,
optimizer updates, learning rate, validation metrics and train/validation wall
time. Trials record initialization/setup cost, parameter counts, failures,
selected epoch and checkpoint hash. Boundary-rate winners and ceiling-epoch
winners are flagged for convergence review. No test score can extend the grid
or choose a checkpoint. A failure remains in the ledger.

Cached Galileo feature preparation is carried into the manifest as a separate
one-time cost. It is neither omitted nor repeatedly charged per probe fit.
Process RSS is explicitly a cumulative high-water mark with platform units.
Test-scoring time includes data/scoring/export work, not model-only latency.
Busy-worker engineering timings must not become claims of isolated comparative
speed. Clean, same-device profiles and recorded device differences remain
necessary when interpreting efficiency; no speedup is claimed in this update.

### Event synthesis and local coverage

[Consolidator198](../scripts/198_summarize_applied_comparisons.py) reads frozen
selected-test receipts. It verifies matching held chips and class/reference
support, preserves missing jobs, reports target IoU/precision/recall/F1 and
counts, and separates training-seed differences from event resampling.

Seed means are formed within events before999 paired event-bootstrap draws.
Leave-one-event-out means expose influential cases. Undefined IoU stays visible.
One event does not acquire an interval because it has three training seeds.
Incomplete contrasts remain pending in the complete workload ledger; no smaller
surviving set is silently declared the final census. Intervals are exploratory,
not a significance gate or evidence of equivalence.

[Local scorer195](../scripts/195_score_local_reference_agreement.py) now reports
both each model's own observable support and the intersection across models.
Confusion counts are pooled across nonoverlapping grids within an AOI/acquisition
**before** IoU is calculated. Eligible area, unobserved/unknown coverage and
projected pixel areas are retained; no tile-level averaging or pixel bootstrap.
Different acquisition/reference offsets cannot be pooled into one case.
July2021 AOIs remain dependent cases, not independent floods or country rankings.

### Acquisition and pre/post timing

[Timing audit200](../scripts/200_audit_applied_timing.py) processed all54 local
AOI/acquisition records and all5,000 radar benchmark records. It retains actual
reference offsets and leaves product delivery times unknown where not established.

Venlo alone is linked to the held Venlo gauge, with measured and display series
kept separate. Twenty-five acquisitions fall in the declared July review window;
the June pre-event acquisition is retained without a July phase label. The held
records do **not** provide a complete verified measured peak window; the display
window is also incomplete. Consequently no verified peak or universal phase
assignment is manufactured. Available local hour-to-hour trends may be reported
with their source qualification. Rur/Inde AOIs are not assigned the Wurm series.
This preserves the useful hydrological-timing idea without inventing information.

Both held SL1 and SL2 dates were inventoried. SL1 gaps have median12days and
range6–528days; SL2 has median24days and range18–540days. SL2 dates exist for
all5,000 records but do not offer a generally newer baseline. Keep SL1 as the
author-compatible primary pairing, show per-activation gaps, and interpret
seasonal/reference-gap differences explicitly. No extra extraction or silent
SL2 substitution was initiated.

## Execution and checks

[Planner199](../scripts/199_prepare_applied_execution.py) creates the full workload:

| Work | Number |
|---|---:|
| Neural tuning jobs, each with three candidates |1,908|
| Neural candidate fits |5,724|
| Deterministic physical calibration/test jobs |53|

Physical jobs are reused across neural label budgets/seeds because they have
no fitted training-label head; those reuses are not independent replications.
The stronger U-Net increases the workload; no existing comparison was removed.

The one-CPU [physical queue201](../scripts/201_queue_applied_physical.py) completed
**53/53 jobs, zero failures**. Each binary task tested every446 chips exactly
once and radar change tested every5,000 records exactly once. All53 source
manifests were reverified;22 optical folds also have fixed-threshold readouts.
These physical reference scores exist; encoder-versus-control conclusions do not.
It preserves source hashes, logs failures, refuses incomplete-directory overwrite,
and waits for storage instead of cropping the test set. Existing extraction and
nine-job device-profile queues are unchanged. Neural fits are prepared, not
launched: the current MPS owner and intended-device/batch profiles remain the
execution dependencies. Copernicus has a validated CPU route; MPS is not assumed.
There is no new accuracy threshold or supervisor-approval requirement.

Local execution records:

- `results/applied_study_v2/execution-plan.json`
- `results/applied_study_v2/physical-queue/progress.json`
- `results/applied_study_v2/timing-checked/audit.json`
- `results/applied_study_v2/pre-run-ledger.json` (dated pre-run snapshot)
- `results/applied_study_v2/physical-complete-ledger.json` (physical outputs complete,
  encoder comparisons explicitly pending)
- `results/applied_study_v2/engineering-tuning/` and `engineering-physical/`

Validation completed:27 targeted tests pass, including complete batch coverage,
source-scale physical controls, real fold census, pooled local metrics,
undefined-event handling, seed/event independence and timing provenance.
Ruff and `git diff --check` pass. A real23-chip training smoke check completed
all three1-epoch linear trials, using23/23 examples in each; a real optical
control check calibrated66 candidates. Neither engineering check scored test.
These checks are not comparative mapping findings. Test commands use
`PYTHONPATH=src .venv-foundation/bin/python -m pytest`.

The [implementation receipt](reviews/limburg-applied-review-implementation-receipt-2026-11-01.json)
records hashes, workload counts and engineering evidence. It is a dated snapshot,
not live queue progress. No other chapter's data or dissertation prose was edited.
