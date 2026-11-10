# Compute design for the audited spatial study

10 November 2026. Internal execution specification. Review of the audited W/F/T/R
plan, existing fast loaders/caches, tuning reuse, completion/checkpoint code and
recorded production profiles. No new training queue, installation or cloud VM.
This replaces naive per-question/per-fold repeated execution, not the scientific
comparisons or eligible test population. No shortening of convergence budgets,
lossy feature compression, test sampling or dropped annotation/optimization draws.

## 1. What is already known

Hardware: M3 Pro, 36 GiB unified memory, 12 CPU cores, 18 GPU cores. About
122 GiB disk free after verified historical-image offload; 50 GiB reserve.
The old implementation already has memory-mapped FP32 inputs, deterministic
worker-independent augmentation, frozen-feature caches, batched scoring,
on-device adaptive-pooling replacements and compact frozen-encoder checkpoints.
These are useful foundations, not new speed gains to count a second time.

Earlier TerraMind profiling found approximately 3–4x training throughput for its
frozen cached route, with a bounded output/gradient parity check. This cannot be
applied to full adaptation, PEFT, corrected inputs or every new dataset as an
assumed speedup. Existing v5 full-label median candidate fits were about 5.2 min
for Galileo native, 41.6 min Prithvi native, 4.6 min frozen TerraMind native and
82.8 min Copernicus native. They include historical setup/contention and omit
other stages; new spatial support/source populations make them planning evidence,
not exact future durations.

Two specific legacy limitations must not migrate unnoticed:

- `applied_tuning_reuse.fixed_learning_rate` requires exactly three candidates
  and the old shared-label-mask partitions. Galileo's 16-rate reference search
  and independently redrawn annotation pools need a versioned reuse contract;
  disabling those checks is not a valid implementation.
- The old selected checkpoint contains model weights/buffers, not complete
  optimizer/scheduler/data-order/RNG state. It supports inference and a restarted
  fit, not exact epoch continuation after interruption.

## 2. Share preparation and predictions, preserve independent learning

Represent execution as a dependency graph, not a Cartesian product of RQ tags:

`immutable physical rasters → model-specific transforms → compatible frozen features`

`source policy/state → independent target fit/state → complete probabilities`

`probabilities + references → W/F metrics, calibration, geometry and resource tables`

RQ names, reports and reference masks do not by themselves justify new fits.
Changes to training/selection populations, weights, label pools, seeds, schedules
or trainable components do. A different test set alone needs new inference/scoring
and an eligibility check, not an identical source refit. A single verified state may support several reports
with its cost charged once to research and allocated transparently for reuse.

### Reuse by pipeline

| Work | Reuse safely | Must remain separate |
| --- | --- | --- |
| W water mapping | One selected model's whole-area probabilities feed geometry, boundaries, reliability and modular flood calculations | Different folds, actual input products, trained weights or corrected spatial support |
| Modular F0–F4 | Same W probabilities with alternative references/terrain rules; CPU recombination | A reference-trained model or a changed neural input requires its own declared fit |
| Copernicus F1–F3 | Each identical, independently encoded date/crop cached once, including both pre-images; reuse across frozen heads, seeds and annotation draws | F1/F2/F3 necks/decoders learn separately. Joint temporal encoders cannot be decomposed this way without proof |
| Galileo | Frozen tokens once per patch size/product/mask/normalization; all LR heads/seeds use them | Patch4 versus patch8 caches and readouts; feature normalization fitted on different allowed source populations |
| Frozen TerraMind | Native early-fusion features once for the exact multimodal/time configuration and each required input augmentation | Pre-optical/event-radar versus event-optical/event-radar; changes to available modalities, merge or weights |
| Prithvi/full TerraMind/PEFT/encoder-updating TTDA | Raw decoding, aligned rasters, masks, deterministic windows and augmentation indices | Live encoder forward/backward. Frozen features do not implement fine-tuning or PEFT within the encoder |
| AlphaEarth | One dense vector export per unique AOI/year/product; aligned block reuse | Independent decoder states/pools and genuinely different years |

No rotation of a frozen ViT feature map is assumed equivalent to encoding a
rotated image. Cache actual required finite input transformations, or recompute
dynamic ones; do not remove augmentations for caching convenience. A frozen
backbone must use the declared eval-mode behavior, with no hidden BN updates.

Cache identity includes physical input/validity hashes, modality/product/units,
acquisition/date/location metadata, source-fitted transform identity, crop/affine/
resolution, input augmentation, model/checkpoint/code, layer/readout and numerical
precision/runtime policy. Labels enter the identity if they influenced any
preprocessing; label-dependent transformations must obey the split. Cache only
the frozen side of the boundary, before trainable necks/decoders. Changed keys
invalidate reuse instead of silently loading an older, convenient cache.

Keep FP32 scientific arrays and lossless compression for cold storage. Expensive
features are cached only when measured encoding savings exceed extra local I/O,
transfer and storage. Use rotating dataset/model shards, not every source/target/
backbone cache on disk at once. Reordering jobs is permitted; changing their data
census is not. Co-locate compatible heads/pools before evicting a feature shard.

## 3. Tuning and target-fit workload

The approved source full-label policy is one complete source-validation search
at seed42, plus two freshly initialized/independently optimized repeat-seed fits
using the selected rate. The seed42 winner counts as its final state only if the final training and
selection contract is identical; do not train that identical state twice merely
because reporting directories differ. Expanding the source training pool or
changing its stopping policy requires a new final refit for every seed. Every repeat selects its checkpoint on legitimate validation
evidence. Count failed/undefined candidates. Do not inherit target event labels
or a different input contract to make a reuse match.

For r candidates and three final seeds **with unchanged final population/selection**:

- Independent per-seed search: `3r` candidate fits.
- Approved shared source selection: `r + 2` fits.
- r=3: **9 → 5**, 44.4% fewer fits; r=16: **48 → 18**, 62.5% fewer fits.

If the final population/selection changes, one shared-search block plus three
source refits costs **r+3**, with all source-CV/meta-validation work charged
separately. A new evaluation subset alone is not such a training change.

These are arithmetic fit-count savings against repeating tuning per seed, not
measured wall-time gains and not necessarily additional to a previously optimized
grid. Author-reference reproduction keeps its prescribed repeated-search protocol
if required; shared tuning describes the applied comparison, not a silent change
to a numerical reproduction. Any expanded grid is chosen from source validation,
with comparable competent control tuning and explicit extra search costs.

Target adaptation uses the declared source-pseudo-target policy across all
target pools/seeds. There is no LR search per target by default; target labels
must not select the policy. No sharing across new label draws through the legacy
helper; the new source-fixed policy is recorded as such. Identical rounded
budgets/full pools are computed once **only when the complete training identity
is identical**, with aliases preserving every requested report.

The three seeds denote paired source→target end-to-end training chains; their
variation does not isolate source and target optimization separately.

Three low-label budgets × three pool draws × three seed chains plus
three full-pool fits = **30 primary adaptation states per compatible system/domain**.
The previous one-pool formula gave 12; stronger variation accounting adds work.
Eight compatible systems across 89 domains would therefore mean **21,360 states**,
before adaptation extensions; this is a workload illustration, not the eligible
queue. Blindly multiplying external applications by five source cross-validation
folds would make 106,800 states. The design specifies three source-refit seeds,
not a five-fold external ensemble: avoid that unnecessary fivefold multiplier.
Source cross-fitting itself remains intact.

Each target state starts from its designated source initialization, not another
target event or a lower-budget fit. Do not warm-start increasing label fractions,
reuse one seed's learned head for another, omit independent pool draws, use ridge
instead of the declared optimizer, or prune candidates by interim test accuracy.
Such changes would alter the experiment, not merely save computation.

### Possible additional optimization: grouped linear probes

For Galileo/linear heads using the same frozen features, training/label membership
and batch order, benchmark a shared input pass with independent heads/optimizers/
schedulers/early-stop state. A vectorized head operation may reduce repeated I/O
and dispatch. This does **not** mean fitting one shared head across seeds or
averaging their gradients. Verify per-head loss, gradients, update counts and
selected state against serial FP32 execution, with independent RNG where needed.
Only adopt after parity and complete-development-fit timing; no speedup is yet
measured. Large decoder candidates remain separate unless profiling establishes
memory safety and equivalent training. No speculative multi-model GPU concurrency.

## 4. Local scheduling and numerical choices

- One MPS training owner; up to two CPU fit/scoring lanes. Galileo's small frozen
  probe and shallow/pixel controls are CPU candidates; select CPU versus MPS from
  complete-development-fit timings rather than model name alone.
- Initial CPU fit setting: two Torch threads per fit, one BLAS/OpenMP thread;
  tune jointly with the MPS owner. Start MPS loading with two persistent workers,
  prefetch factor1; benchmark0/1/2 workers and0/1/2 CPU lanes. Loader subprocesses
  count toward the same CPU/memory budget; three model lanes are not three GPUs.
- Mac unified memory means CPU jobs, GPU tensors, mmap/page cache and host apps
  compete. Do not add GPU allocation to process RSS as if it were separate VRAM.
  Measure system pressure, swap-out growth, driver allocation and resident memory
  during the overlap profile. Initial engineering allowance reserves about8 GiB
  for OS/interactive work; adjust admission from real pressure/throughput, not a
  scientific sample cap. Reduce concurrent lanes before changing training data.
- Do not automatically increase training batch size. It changes optimizer/BN
  trajectories and previously slowed Prithvi. Keep the declared effective batch,
  schedule, augmentations and complete window cycles. Change evaluation batching
  separately in eval/inference mode with whole-census parity checks.
- Keep FP32 production initially. Mixed precision, channels-last, compilation or
  a newer runtime is an isolated measured candidate, not a promised free speedup.
  Earlier profiles already found slowdowns/failures for some choices. Do not
  enable MPS fast math or undocumented fallback globally. Record CPU fallback
  transfers and preserve validated on-device pooling where contract-compatible.
- Activation checkpointing trades recomputation for memory and is **not a speed
  optimization**. Use only if needed for a supported trainable model's footprint,
  with RNG/gradient checks. It cannot make a frozen cache valid for fine-tuning.
- Avoid per-minibatch CPU scalar reads/synchronizations when already validated
  epoch accumulation can preserve diagnostics. Validate on the specified schedule;
  do not skip validation or silently change plateau/stopping behavior to go faster.

PyTorch's [loader documentation](https://docs.pytorch.org/docs/2.9/data.html)
describes persistent workers, prefetch and multiprocessing/RNG concerns;
[activation checkpointing](https://docs.pytorch.org/docs/2.9/checkpoint.html)
explicitly involves recomputation and RNG handling. Neither implies a universal
Mac speed improvement. The pinned actual runtime, not live latest documentation,
determines supported implementation APIs.

## 5. Inference, storage and restart design

Run whole-census test inference only for selected states. Learning-rate candidates
need source validation, not redundant held-test/local-case predictions. During
fitting retain sufficient training/validation curves, candidate states and source
receipts to audit selection; test information never feeds candidate selection.
Store selected probabilities/valid masks once, with grid and class metadata.
W/F/reference variants, calibration and boundary metrics reuse those outputs.
Calibration transformations are fitted on the correct separate data and applied
as separate versions; hard masks cannot reconstruct probabilities.

Use complete spatial windows and stitched grids; do not shorten inference to
sampled/favorable patches. No FP16 probability archive or dropping low-confidence
pixels as a storage shortcut. A direct-change fit differing in its learned inputs
still requires its own probability map. Supplemental reporting does not refit it.

For interruption safety, keep separate best-model and latest-resume states.
The latter includes trainable weights/buffers, optimizer, scheduler, epoch/update
position, scaler if used, Python/NumPy/Torch CPU/device RNG, sampler/augmentation
state and exact source/data identities. Resume at verified epoch boundaries
initially, preserving data order/update state and declared numerical replay
tolerances. Bit-identical MPS continuation is not assumed when operations are
nondeterministic; failure to show bit equality does not stop other work. Frozen weights may be referenced by verified immutable hashes; their
task neck/decoder/buffers and optimizer states may not be omitted. Trainable
backbones/PEFT modules require complete reconstruction state. Test resumed versus
uninterrupted training on a development fixture before claiming exact continuation.

One bounded CPU archive/network worker offloads completed shards asynchronously,
with the existing upload/full-readback/restore protections. This worker shares
CPU/I/O resources and yields to fitting; it is not a fourth heavy lane. Do not
block the MPS owner on every small upload when local headroom permits overlap.
Separate `fit_complete`, `evaluation_complete`, `recovery_verified` and
`local_retired`; the study is not complete just because a process exited.

Maintain the50GiB reserve and approximately5GiB archive scratch allowance. Before
prefetching a shard, account for source rasters, active features, worst-case new
states/probabilities and compression/readback scratch. Additional offloading is
available, not automatically authorized by this document. Never remove current
dependencies or other chapters. Avoid thousands of small remote reads during
training: restore the next compatible working shard once, verify, then work local.
No new Azure VM/GPU or enlarged cloud spend is assumed.

## 6. Measure research cost and reusable mapping cost separately

The policy-facing resource record separates:

1. One-off research: reference reproduction, model selection, annotation-pool/
   seed repetitions, source fitting and exploration history.
2. Source-model preparation that an agency might reuse: dataset preparation/QA,
   feature generation, training and calibration; charge real annotation separately.
3. New-area use: acquisition/transfer, preprocessing/QA, optional local annotation/
   adaptation, complete map inference/stitching, confidence/reference calculation
   and output delivery. Report warm reuse and cold setup, with assumptions.

Report hardware/runtime/precision, total candidate/selected fits, unique source
encodings, wall time and device time, cache/storage/network bytes, peak system
memory/pressure, km² or valid pixels processed, observable coverage, failures and
restart work. Measured compute time is not electricity/carbon or human labor.
Simulation labels do not supply measured annotation-hours. Acquisition latency
is not just model latency. Cost allocation and reuse counts must be explicit;
an agency producing one map does not run the whole dissertation grid.

## 7. Timing confidence and implementation sequence

The [full audit](reviews/limburg-three-prong-full-audit-2026-11-10.md) reconciles
training/inference/scoring identities, source-refit arithmetic and expanded
event-completion packaging. The old6–16week envelope remains superseded. There is **no defensible single new
ETA yet**. Full-Kuro source expansion, target eligibility, annotation draws and
uncached full-adaptation costs are unresolved. Fit-count savings cannot be
multiplied into all stages as a blanket runtime factor.

Next implementation order, without dropping any scientific branch:

1. Build the actual dependency/job graph and exact fit/cache identities from the
   audited splits/model contracts; show requested reports versus unique compute.
2. Version tuning-policy reuse and exact epoch-resume support; keep old production
   sources/results intact. Verify recovery/manifest compatibility.
3. Implement/model-check the correct spatial routes and feature boundaries;
   benchmark optional grouped linear probes and the data-loader/worker overlap.
4. Profile a complete development cycle per changed architecture, plus a full
   target-adaptation case and a large-AOI inference pass. Include validation,
   input preparation, probabilities and asynchronous recovery, not only five steps.
5. Use measured per-unit rates and actual job counts to publish the critical path,
   total CPU/MPS work, source/cache/egress volume and restart allowance. Independent
   preparation/acquisition can proceed while another model is profiled.

No scientific output has been changed by this review. The machine-readable
policy records optimizations as inherited, specified or pending parity/profile;
none of the new policies is falsely marked implemented in the old queue.
