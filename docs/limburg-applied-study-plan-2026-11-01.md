# Applied satellite AI: research, data and storage plan

1 November 2026. Internal implementation plan, not dissertation prose. Planning is complete; this document does not launch training, transfers or local deletion. The [task registry](../config/limburg_applied_tasks_v1.json) and [source review](limburg-applied-task-configurations-2026-10-31.md) supply the exact configurations. Existing discharge results remain evidence; this is a proposed spatial extension with a different target, not a correction to their outcomes.

## Purpose and research questions

**Main question:** Can satellite AI improve assessment of high water and flooding, through better maps or lower data, labeling and computing costs?

1. For observed satellite acquisitions, how well do supported models distinguish water, non-water and, where reference labels allow, newly flooded land compared with appropriate conventional methods?
2. How do accuracy, coverage and resource requirements change across events/locations and with less labeled training data, including the observable NL/DE setting?

The common empirical spine is **quality and cost of spatial flood information**. A source-supported map at acquisition time is useful evidence for flood assessment and response; its delivery delay determines when it could be available. We will not turn it into an earlier forecast, demonstrate operator benefit without evaluating that, or require a new discharge/hydraulic model. Different model tasks may support different parts of this spine without yielding a universal winner.

## Phase 1 — Make room, preserve recovery, finish existing work

### Observed storage and dependencies

Read on 1 November: **61.7 GiB free**, approximately **11.7 GiB above the authorized 50-GiB reserve**. Presto and Galileo are running; all 20 queue-protected source hashes match. Disk guard is monitoring at 50 GiB, with resume at 51 GiB. Sizes below are rounded `du` observations, not promised APFS reclaimable space.

| Local holding | Observed size | Planned treatment |
|---|---:|---|
| `data/raw/limburg_compact_eo` | ~55 GiB | Keep while active workers need it; later stage by task if useful |
| `data/raw/limburg_eo_expansion` | ~100 GiB | First source-offload candidate after local/remote manifest reconciliation and dependency checks; preserve source bytes remotely |
| `data/processed/limburg_eo_coherent_census_v1` | ~296 GiB | Large completed patch-cache candidate; inventory selected runs, consumers, hashes and restore requirements before offloading |
| `data/processed/eo_expansion_sequences` | ~39 GiB | Candidate after preserving selected aggregates and checking later consumers |
| `data/processed/limburg_eo_token_consistent_sequences` | ~20 GiB | Check hard links/shared selected outputs; no automatic removal |
| Current individual experiments under `results/` | ~8.8 GiB, growing | Keep locally through completion/review; back up separately |
| Held model/source collection | ~4.9 GiB | Keep task models; no new backbone download required for the three direct configurations |

The current archive adapter reads compact imagery and `limburg_monitoring_eo` for Presto/Galileo. SatMAE's input view and older comparisons can point into expansion imagery through symlinks. A root directory being absent from the current loader does not establish that every file is unused. Older caches are scientific evidence/recovery candidates, not presumed trash. No other chapter or shared data is an offload target.

### Offload procedure

1. Inventory a finite set of candidate runs/products using existing manifests first. Check active processes, queued follow-ons, symbolic/hard links, selected aggregates and restore paths. Avoid repeatedly walking millions of files during extraction. Do not alter active source/configuration fingerprints or runtimes.
2. Reconcile expansion imagery against existing Azure per-file receipts. The 30 October audit recorded ~154.7 GiB in private `stkerkradeprod01bg/limburg-compact-eo`, including the completed expansion; that is historical evidence, not today's full checksum verification. Container metadata was readable and private on 1 November. Reuse verified identical remote objects rather than uploading another complete source archive.
3. Upload missing/changed source bytes and inactive derived outputs to dated, additive prefixes under that container, proposed `offload/2026-11-01/` and `applied-v1/`. Never use a remote-delete synchronization. Preserve relative paths, byte sizes, SHA-256, source/run IDs, symlink targets and hard-link relationships in a local restore ledger. Do not overwrite earlier receipts.
4. Verify every object proposed for local removal against its local hash and trusted remote verification evidence. For objects lacking sufficient evidence, stream remote bytes through a SHA-256 check. Test restoration of a complete small run/chunk, including member hashes and path handling. A successful upload, matching filename or cloud completion count alone is insufficient.
5. Pack small derived files in bounded, independently restorable shards if needed. Start with at most ~1 GiB local archive scratch while headroom is tight; verify remotely by streaming rather than making a second full disk copy. Do not duplicate a 100-GiB directory to build a tarball. TIFFs already stored as individual verified blobs need not be repacked.
6. Remove only the specifically verified, inactive local copies. Keep run-level manifests, decisions, selected compact representations, finished results, code and restore instructions local. Measure free space before/after; shared APFS blocks/hard links can limit actual reclamation.
7. **Initial operational target: recover 40–60 GiB**, yielding roughly 100–120 GiB free before ongoing writes. This is a planning allowance, not a data limit or guaranteed reclaim. If that is insufficient after profiling, offload another verified batch rather than dropping events or changing inputs.

Use Blob storage, with no VM restart or GPU provisioning. Initially retain readily accessed material in Hot; consider Cool only for genuinely infrequent retrieval after checking transaction/retrieval costs and minimum-retention implications. Existing Azure use is not free capacity; estimate incremental stored bytes, requests and likely readback/egress before a large transfer. Do not reuse the rejected $30 cloud-compute proposal as a new storage budget. [Azure tiers](https://learn.microsoft.com/en-us/azure/storage/blobs/access-tiers-overview), [authenticated Blob uploads](https://learn.microsoft.com/en-us/azure/storage/common/storage-use-azcopy-blobs-upload).

**Deliverable:** dated path-level offload/restore ledger, verified remote coverage, actual free-space gain and a protected-path list. Finish and audit current Presto/Galileo results separately; mapping setup can proceed with light metadata work meanwhile.

## Phase 2 — Acquire source data and establish the local application

| Package | Acquisition and use | Storage policy |
|---|---|---|
| Sen1Floods11 hand data | Acquire all 446 label chips and corresponding S1/S2 images, source splits/event metadata and small JRC reference. Core **1.63 GiB**, JRC ~0.0005 GiB. Verify listed MD5 and local SHA-256; check raster alignment, units, invalid labels, clouds and sensor-date differences | One canonical copy; shared by TerraMind/Galileo and candidate Prithvi. Views/links or channel selection, not three cloned datasets |
| Copernicus-Bench Flood-S1/Kuro Siwo subset | Acquire **5.61-GiB ZIP**, verify recorded LFS SHA-256; inspect central directory for expanded bytes, file count, class definitions and splits before extraction. Do not download the whole benchmark | Store compressed source in Azure. Expand only required task data locally after budgeting it. Stream download/upload or bounded staging if ZIP plus extraction would exceed headroom |
| Local NL/DE reference inventory | Retrieve CEMS EMSR517/520 product lists, footprints, observation/production times, methods/confidence and source sensors; inspect GEOID-Flood metadata for additional relevant events. Resolve ordinary public product routes after the earlier API 403 | Metadata/vector references first; inventory all eligible local mapped events without an arbitrary event sample. Only relevant reference products, not complete global collections |
| Local event/pre-event imagery | Once reference AOIs/times are known, acquire individual Sentinel-1 and model-compatible Sentinel-2 observations, including valid dry terrain within observed AOIs. Preserve orbit, angle, masks and acquisition times | Canonical acquisition store in Azure; task/event working set local. Existing weekly composites are not substitutes. Determine volume from actual AOIs/bands/dates |

No additional discharge/rainfall/soil/snow request is needed. Gauge p99/H3 crossings and the 15-record documentary register supply context, not flood-pixel truth. Keep unobserved terrain unknown. A reference derived from the model's own input acquisition is not automatically independent truth; record the dependence and qualify evaluation. Include local independently documented dry coverage where available, not only known flooded polygons.

If only July 2021 has usable local labels, retain a clearly described local case application plus broader benchmark evidence. If tributaries are unresolved at the reference/sensor scale, use supported Meuse/floodplain AOIs and report that limit. Missing local references narrow the local claim; they do not invalidate another supported task or stop the chapter. Wider flood-event acquisition follows evidence availability, not model performance.

**Deliverable:** acquisition/reference manifest with event/scene identities, sizes, dates, usable AOIs, source provenance, exclusions and explicit unknowns. Local-data footprint remains unmeasured until this inventory exists.

## Phase 3 — Implement supported tasks individually

| Order/model | Task, configuration and inputs | Comparison and unresolved setup |
|---|---|---|
| 1. TerraMind 1.0 Tiny | Author Tiny config; paired S1 VV/VH dB + 13-band S2L1C; frozen backbone, intermediate layers 2/5/8/11, trained UNetDecoder; binary water, ignore -1 | Same-input compact U-Net and transparent calibrated image-feature baseline. Explicitly stage canonical folder names and check modality normalization/masks |
| 2. Galileo Nano | S1-only water segmentation; frozen spatial features and linear segmentation probe; author 64px subpatch route | Same-input radar feature classifier and compact spatial model. Verify Nano wrapper. Preserve dry patches in applied evaluation; keep the author positive-only reproduction population separate |
| 3. Copernicus-FM base | Native frozen-encoder radar change; pre/event VV/VH linear intensity, multiscale differences and UPerHead/auxiliary head; three target classes, ignore3 | Same-pair SAR change baseline and compact supervised change model. Establish class semantics/MNA validity, normalization and missing-target behavior; resolve mmcv/mmseg/SyncBN portability in an isolated environment |
| 4. Prithvi EO2 Tiny TL | Six-band optical water mapping; explicitly loaded held pretrained Tiny weights and compatible spatial head | Same-band optical index/feature model and compact spatial model. Verify Tiny depth/metadata, HLS-to-S2L1C transfer and common output grid; author larger-backbone template is not a ready Tiny config |

All four are in the plan; Prithvi is an adaptation candidate, not a prerequisite for the first three. Attempt a small engineering forward/backward check before its full run and record an unsupported combination as such. Do not silently replace the model. No automatic ten-model sweep, added distillation, generative model or new solver.

Maintain simple data-science scripts: acquire/check, prepare source-specific inputs, fit/evaluate a named task, write tables/maps. Reuse stable helpers where genuinely shared. Keep model-specific transforms visible; do not hide different tasks behind a generic manager. Leave active environments unchanged and pin new isolated task environments.

## Phase 4 — Evaluation and compute protocol

- **Populations:** published split reproduction for comparability; separately construct grouped event/location transfer evaluation from verified identities. Keep all eligible test scenes and valid pixels, including dry scenes/subpatches. No random handful of floods as the scientific evaluation. Tiny engineering samples do not become the final sample.
- **Leakage:** separate parent scene/event/location across transfer folds; keep S1/S2 pairs together. Tune thresholds, transforms, heads and stopping on training/validation only. Audit shared source events, geography and known pretraining/fine-tuning exposure; a famous historical benchmark is not an untouched prospective test.
- **Fair contrasts:** match acquisitions, bands, valid support, folds, label budget and downstream tuning within each task. A fused TerraMind versus radar-only Galileo score measures a system difference, not an isolated encoder effect. Add a shared-modality variant only if supported and needed to answer that distinction. Do not combine binary-water and event-change scores into one model ranking.
- **Accuracy:** primary event-level water/class IoU as appropriate to the target; report precision/recall/F1, false-positive area, missed water, coverage and individual-event maps. Report pooled pixel scores separately. Preserve unknowns; never assign missing labels to dry. Show event-water separately from permanent water when independently supported.
- **Uncertainty:** paired event-level differences, event-cluster resampling where enough independent events exist, and training-seed variability separately. For very few events, show all case results/influence rather than manufacture precise intervals. NL–DE differences require comparable support; otherwise present cases, not a country ranking. No success rule based on significance.
- **Label efficiency:** begin with nested **100%, 20%, 5% training-label budgets**, constructed from a fixed train-only grouped selection and repeated seeds, with the same complete evaluation. Report actual independent groups, annotated area/pixels and spatial distribution; percentages alone are not annotation effort. If a fraction cannot preserve a viable grouped training/validation design, document/revise that comparison before fitting; it is not a chapter stop. Do not add the author's 1% budget automatically.
- **Resources:** same machine/device/precision and explicit comparable tuning effort; record download/preparation, feature extraction, head training and per-scene inference separately, including wall time, peak memory and local storage. Compare amortized reuse as well as cold start. Do not infer efficiency from parameter count or a busy concurrent worker log; do not infer equivalence from a nonsignificant accuracy difference.
- **Execution:** one MPS task at a time. Up to two light CPU preparation/scoring workers only if measured RAM, swap, disk and UI responsiveness permit; this is not permission for two full extra model trainings. Wait for the present device-owning jobs before GPU engineering tests. Profile a forward/backward step, representative epoch and inference batch; then estimate hours/storage for each full run, rather than promising an overnight finish.

**Deliverable:** compact dated analysis specification, fixed splits/label subsets/baselines and measured run budgets before outcome inspection. Internal documentation, not compulsory preregistration. Record justified changes without treating every issue as an approval gate.

## Phase 5 — Rotate the working set, run and interpret

Planning allowances, **not measured model requirements**: ~2 GiB canonical Sen1 inputs, 5–10 GiB of prepared views/bounded feature cache, and 5–10 GiB checkpoints/results/task environment. Reuse existing weights; retain best/last task checkpoints rather than every epoch. Bound logs and temporary extraction. Set the actual allocation after profiling. Copernicus expanded data and local imagery are additional measured line items, not hidden inside those allowances.

Keep the 50-GiB reserve and budget `current free − reserve − expected ongoing-worker writes` before each staging/fitting phase. If the next task will not fit, offload/stage another verified batch; do not silently crop the test population. All eligible events can be evaluated in batches. Azure retains source ZIPs/acquisitions and verified inactive outputs; the Mac holds only the current task's inputs, required weights and bounded outputs. Avoid recreating millions of tiny patch-cache files: use direct raster reads/batches and only persist spatial features when reuse justifies the measured footprint.

Run TerraMind/Galileo comparisons on their shared dataset, then the distinct radar-change task; run compatible Prithvi after its check. Save all eligible evaluation predictions or losslessly sufficient spatial outputs and masks, per-scene/event scores, timing and provenance. Offload finished task outputs after verification before staging the next large package. Compact final tables/maps and restore ledgers stay local.

Interpret four possibilities: improved mapping; comparable accuracy with a measured resource/label advantage; conditional benefits with identifiable failures; or no useful advantage over strong conventional methods. Each can inform choice of flood-information method. Neither mapping success nor no gain proves why prior discharge tests behaved as they did. Linking maps to future river trajectories remains a separate possible extension, not another required stage.

**End product:** one applied comparative readout, event/reference atlas, accuracy–cost/label-efficiency tables, reproducible task configurations and an explicit account of where the information could enter flood assessment. Brian writes the dissertation text. No deployment, warning-skill, causal adaptation or avoided-damage claim follows from mapping scores alone.

## Implementation order

1. Inventory/protect dependencies; verify/offload enough inactive Limburg data; retain current workers and results.
2. Acquire shared hand labels and local reference metadata; profile isolated native task adapters once compute is free.
3. Finalize grouped evaluation, matched controls and measured storage/runtime budgets; acquire local scenes and the separate radar subset against that manifest.
4. Run the task comparisons and local application, rotating data through Azure-backed working sets.
5. Review actual maps/errors, consolidate findings and update the living one-pager.

This pass created the plan and checked existing storage/dependencies only. No data were moved or deleted, no full imagery download or training started, and no running source/configuration hash changed.
