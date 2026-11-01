# Applied-study preparation while the extraction workers finish

Internal research aid, 1 November 2026. No dissertation prose. Implements the
four preparation tasks without reducing the study or interrupting extraction.
Machine-readable [receipt](reviews/limburg-waiting-preparation-receipt-2026-11-01.json).

## 1. Complete the engineering profiles

Added `202_profile_applied_supplements.py` and the source-fingerprinted,
resumable controller `203_queue_applied_supplements.py`. All four Copernicus CPU
profiles passed: native, compact U-Net, standard U-Net and pixel-linear.
Three additional standard-U-Net MPS profiles are queued behind Galileo and
completion of the original nine profiles. These are queued engineering checks,
not completed comparative fits. Together the original nine and supplemental
seven cover all four learners in all four spatial tasks.

Profiles use three real training batches, finite-gradient checks and explicit
state/parameter storage measurements. They never select on test scores. Their
short, contended batch timings do not establish end-to-end throughput or
comparative efficiency. Copernicus native state tensors occupy 688.84 MiB;
three candidate states require about 2.02 GiB before predictions/serialization.
No packages or active extraction sources were changed.

The tuning runner now also checks the supplemental queue before taking MPS.
An already-running model is not preempted. Keep one MPS owner.

## 2. Independently audit the physical baselines

`204_audit_applied_physical.py` reconstructs original labels and valid masks,
checks every saved prediction's grid and unknown mask, and recomputes confusion
counts. All **6,338 predictions across 53 held-event outputs** reproduce their
stored scores and masks. The count includes 446 water chips for each of three
different task pipelines plus 5,000 radar-change records; it is not 6,338
independent events.

[Complete error-sheet gallery](../results/applied_study_v2/physical-audit-verified/index.html).
Each event has a sheet showing its highest false-positive, highest
false-negative and median-IoU diagnostic examples (deduplicated). Every chip,
not only those illustrated, contributes to the audit. Visual spot checks of
Pakistan optical, Somalia radar and activation1111002 radar change show broad
land/water confusion and missed mapped flooding. These observations describe
reference agreement, not independently verified causes of errors. All sheets
are available for Brian; no exhaustive human pixel adjudication is claimed.

The audit's first attempt exposed an unsigned-mask conversion difference
between NumPy versions in the **new independent audit**, not the production
predictions. Casting labels to signed integers before inserting -1 fixed it;
a small real-raster regression test protects this. The incomplete
`physical-audit/` directory is superseded by `physical-audit-verified/` and
retained as an engineering record.

Thirteen of twenty radar-change calibrations select at least one numeric grid
endpoint; eight only select zero dB change, a legitimate physical boundary.
This is recorded for interpretation, not used to retune after looking at test
errors. Optical and single-radar selections do not select numeric endpoints.
Do not rank the encoder tasks from their physical scores: inputs and, for
Copernicus, the target itself differ (new flood versus surface water).

## 3. Build the local evidence atlas

`205_build_applied_local_atlas.py` creates the
[local atlas](../results/applied_study_v2/local-atlas-final/index.html): all
**54 AOI/sensor/scene cases, covering 530 held source tiles**, for Venlo,
Eschweiler and Wassenberg. Cases include overlapping granules and repeated
dates; they are not 54 independent floods. All case pages show imagery,
qualified CEMS reference masks and observable/reference support. Counts use
native 10m grids; nearest-neighbour 40m mosaics are viewing aids only.

Unknown QA is separate from absent spectral observations. QA60 flags do not
prove complete cloud detection or water visibility. Several July14/16 optical
cases have all eligible source pixels cloud-flagged; later scenes offer more
support but larger reference-time offsets. Do not treat later clear imagery as
a contemporaneous peak-flood observation.

The timeline shows acquisition times, CEMS reference acquisition times and
Venlo's strict versus display discharge. Venlo's July peak window is not
verified by the strict measured series. Display/interpolated discharge is
context only. German AOIs lie on the Inde/Rur; Wurm gauges are not imposed as
local timing truth. Shared radar lineage is explicit, with exact acquisition
identity unresolved where source descriptors lack full product IDs.

The final atlas is `local-atlas-final/`; the earlier `local-atlas/` and
`local-atlas-verified/` previews are superseded. The atlas is evidence
organization, not model validation. Local neural predictions remain pending.

## 4. Check execution, storage and recovery

`206_audit_applied_execution.py` confirms unique job IDs/output directories,
all four tasks/learners, all held folds, all three training-label budgets and
all three seeds. The grid retains **1,908 tuning jobs / 5,724 candidate fits**,
plus 53 physical calibrations. It rechecks partition hashes and all32 protected
source entries across the extraction and two profile controllers. Full neural
comparisons have not launched.

The four measured Copernicus profiles alone imply a **379.11-GiB lower bound**
for candidate state tensors across their full grid. This excludes other task
states and output overhead. With about90.6 GiB free, keeping every checkpoint
locally is not feasible. The working set of an individual measured Copernicus
job fits; unmeasured devices/activation memory still need their profiles.
There is no defensible whole-grid ETA yet.

Use one completed tuning directory as the recovery/offload unit:

1. Confirm all candidate outcomes are recorded, selection uses validation only,
   the selected checkpoint hash agrees, and the selected test prediction
   census equals `manifest.json`'s test partition.
2. Preserve source/configuration/runtime records, all candidate logs and
   checkpoints, selection and every prediction together. Existing original
   weights/source-data backup remains separately required.
3. Run `207_preserve_applied_results.py --include RELATIVE_DIRECTORY --output
   NEW_BUNDLE_PATH` using Azure CLI's Python. Include any source versions not
   already preserved. This writes an embedded file/hash inventory, uploads
   additively to a content-addressed private blob, downloads the archive again
   and checks every member's byte count and SHA256.
4. Only after verification may a later Disk Cleanup remove the inactive local
   copy. This preparation deleted nothing. Keep50 GiB free; never offload an
   active job or another chapter's data.

Completed preparation artifacts were actually tested through this workflow:
**6,705 files, 38,967,274 archive bytes**, uploaded to
`stkerkradeprod01bg/limburg-compact-eo`, then downloaded and every member
verified. The receipt records the content-addressed blob and SHA256. No Azure
VM or GPU was provisioned. Source benchmarks and inference weights are not
all re-bundled in this small result archive.

Inference checkpoint restoration is supported; **epoch-level resume is not**:
these states omit optimizer/RNG progress. Keep a failed run intact and restart
into a versioned directory. Failed candidates must remain visible in synthesis.
Do not silently treat a partially completed grid as the planned comparison.

## Verification and what remains

All32 targeted tests passed across preparation, masks, task logic, selection,
coverage, execution census and recovery; Ruff passed. Original32 protected
source entries still match. No new empirical encoder comparison or local
validation result was created. All events, budgets, seeds and the ten prior
discharge experiments remain in scope. Other chapters were untouched.

Remaining sequence: finish Presto/Galileo; finish original and supplemental MPS
profiles; use their measured feasibility/cost to schedule the full neural grid;
verify/offload completed jobs; then matched synthesis and local application.
Preparation does not require rerunning the existing extraction workers.
