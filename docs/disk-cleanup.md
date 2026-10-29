# Disk Cleanup

## 29 October: original-mask OlmoEarth cache retired

Recovered **13.03 GiB of observed free space**, with roughly **82 GiB free** afterward. Retired the superseded original-mask cache under `data/processed/limburg_eo_mps_sequences/olmoearth/09dbb327a3cb2df14027a67e0f32c7f018eaae065f096287122e93a239c25e95`. Its corrected selected replacement completed with zero errors and retains its own files, including 447,858 hard-linked reused outputs. Removing the old names does not remove those corrected files.

Before deletion, indexed all 1,654,678 files, saved a gzip ledger with SHA-256 hashes and lossless contents of non-NPZ metadata, and verified every metadata payload plus the full gzip stream. Removed 1,653,602 superseded files; top-level manifests/status and error evidence remain in place. The original NPZ payloads are not backed up in this ledger: they are obsolete derived arrays, with held imagery/weights/pinned source available for regeneration, not a promise of exact byte-for-byte numerical reproduction. Metadata can be restored from `content_b64`; selected hard-linked arrays remain at the corrected paths. No scientific source delivery is retired here.

The [receipt and restore inventory](reviews/disk-cleanup-2026-10-29.json) binds the archive and procedure hashes. Corrected selected OlmoEarth manifest/status/aggregate hashes were checked before and after and remain identical. No raw imagery, provider data, weights, active download, completed scientific result or other chapter was changed. APFS sharing and concurrent writes mean allocated bytes are not interchangeable with measured free-space gain.

The new experiment plan avoids another million-file patch cache: stream into compact catchment/context features and resumable tile-level accumulators, with measured peak temporary storage. Runtime/disk estimates still require adapter benchmarks. This is storage management, not an event-exclusion rule or scientific gate.

## 22 October: eight superseded caches retired

Brian authorized discarding these first-run patch outputs. Old scoring/review
were stopped and 36 run directories across the eight replaced models were
retired, including superseded partial/smoke runs. Run-level records and complete
catchment summaries/old combined selection occupy about 0.89 GiB in
`data/processed/limburg_eo_retired_2026-10-22`; retired per-patch files are not
claimed to remain available. Their held source imagery, checkpoints and source
history permit regeneration. Protected Prithvi/OlmoEarth outputs revalidate.

Cleanup measured free space rising from 82.9 to 476.8 GiB; it was roughly 70 GiB
before cancelling scoring. The [restart record](reviews/limburg-eo-retirement-and-restart-2026-10-22.md)
and retirement receipt preserve details. This replaces the need to duplicate
the old eight caches or redesign their storage before restarting. The existing
compressed writer/reserve now fit, and new outputs retain their full working
provenance. No raw imagery, weights, provider delivery or other chapter was a
deletion target.

## 22 October: correction held for storage redesign

The later [ten-model documentation review](reviews/limburg-ten-model-documentation-review-2026-10-22.md)
adds CROMA to the pending correction for its input scaling, increasing the planned
extractions to eight. The following measured sizes cover the original seven
selected directories only. Include CROMA when sizing the compact replacement;
do not silently reuse its incorrectly scaled embeddings to save disk space.

The [pre-correction audit](reviews/limburg-pre-correction-full-audit-2026-10-22.md)
measured **285.659 GiB** allocated by the seven selected extraction directories,
including **165.6 GiB** for Galileo. Their float32 vector payload is **2.830 GiB**;
the remaining files include required masks/date/provenance evidence as well as
repeated metadata, absent-patch records and filesystem overhead. It is not all
disposable and is not an estimate of recoverable APFS physical space.

About **70 GiB** remains free. The correction is held before extraction. Do not
launch another copy of the old layout or assume lowering the hard-coded 60 GiB
reserve makes it fit. Use compact lossless outputs/shared metadata and verified
retirement/archive of superseded intermediates; preserve current aggregate
receipts, source imagery and the evidence needed to reproduce missingness and
area calculations. The current score/review can continue. No deletion occurred
in this audit, and the Azure expansion remains remote.

## 21 October 2026: completed safe cache cleanup

Removed approximately **2.00 GiB of allocated disposable cache**: the inactive
PyTorch benchmark installation under `logs/presto-runtime-probe` and pip HTTP/
wheel download caches. Confirmed the active PyTorch 2.9.1 installation has its
own files and no `.pth` reference to the probe before removing it. No installed
runtime, model weights, scientific input, result or active worker was changed.
The local audit receipt is `logs/disk-cleanup-2026-10-21.json`.

Free space immediately afterward was about 127 GiB. This is a moving figure
because the two extraction jobs continue writing. Allocated cache removed is
not an exact claim about APFS physical blocks reclaimed under concurrent writes.

A broad recursive size scan was stopped because walking millions of patch
receipts competes with the active work; no total for unscanned directories is
claimed.

## Larger cleanup candidates

- **Superseded extraction caches:** old CPU Galileo (404,171 written vectors),
  interrupted old-runtime Presto (44,664), interrupted CPU CROMA (21,477), and
  the original OlmoEarth run with the superseded mask handling. Retain run
  manifests, decisions, error/benchmark evidence and provenance when retiring
  regenerable arrays. Confirm replacement coverage rather than assuming that
  every old patch exists in a newer run. Galileo/Presto replacement censuses
  are still running at this audit.
- **Repeated per-patch metadata:** millions of absent-observation JSON files
  repeat frame/source metadata. These are candidates for lossless indexed
  compression after their owning runs stop writing. Preserve patch IDs, full
  contents and hashes; leave the finite receipts referenced by current aggregate
  manifests accessible. Do not delete missingness evidence merely to save space.
- **Original local imagery:** the roughly 59 GB compact archive has a verified
  Azure copy, but active extraction still reads it. Later it can be staged from
  the immutable remote archive as needed rather than retained in full locally.
- **Supplemental local imagery:** the 3,418 completed local pairs are retained.
  Only 137 were uploaded during handoff; Azure is reacquiring the others. Do not
  treat the cloud transfer as complete backup verification of every local pair.
  Use the remote completion/receipt checks before retiring local copies.

The old Presto environment remains a dependency of the new environment through
`legacy-presto-dependencies.pth`; do not delete it as an apparently unused runtime.
OlmoEarth reused 447,858 outputs by hard link. Unlinking old names will not free
shared data blocks still held by the corrected run; account for that in any
reclamation estimate. Additional Azure imagery should stay remote until needed,
rather than automatically mirroring the full expansion onto the Mac.

This is a storage-management task, not a research eligibility rule or new gate.
No new empirical result or scientific exclusion is created.

## 21 October: weather and cross-chapter follow-up

A targeted source/dependency review found **6.08 GiB of duplicate expanded radar
files**. All 744 files in `radklim/probe/asc`, 744 in `radklim/probe/op` and
342 unpacked supplement binaries were SHA-256-matched byte for byte to their
retained compressed source archives before removal. Archive checksums and counts
are in [the verification receipt](reviews/weather-cleanup-checks-2026-10-21.json).
Only expanded copies were removed. The active RADOLAN crops, RADKLIM comparison
crops, source archives and metadata remain. Current catchment rainfall reads the
crop directories, not these probe expansions. This preserves the earlier product
coverage assessment and the ability to reproduce the old files by extraction.

The older weather inventory is much smaller than the embedding cache: KNMI
Azure-slim files about 1 GiB, ERA5-Land about 299 MiB and four legacy weather
exports about 54 MiB. Source files remain held; no cloud-backup completeness is
assumed from a directory name. The archived pressure/CO2 direction itself has
little raw-data footprint. Removing useful inputs wholesale would reclaim much
less than retiring repeated patch metadata and superseded outputs.

Other chapter **data-directory** totals are approximately 0.93 GiB Bukidnon,
3.7 GiB Peja and 1.1 GiB Jordan; this is not a claim about all files in each repo.

- Bukidnon's ~0.95 GB exploratory-swap folder contains compressed/extracted
  HydroBASINS and a large PH administrative boundary. Its `hybas_au_lev12_v1c`
  HydroBASINS level-12 shapefile is still the source for
  `scripts/build_lipad_request_area.py`; the folder is not entirely obsolete.
- Peja's ~2.3 GiB KCA original ZIP is an important source delivery. Its old
  raster previews are only ~290 MiB; the current open-data archive is ~768 MiB.
  No KCA source delivery or open hydraulic/exposure input was deleted.
- Jordan's retained dust/flood/station material is current project evidence,
  including the conditional flood track, not obsolete merely because modelling
  is paused for review. No Jordan files were deleted.

Other chapter worktrees were inspected without editing, staging or overwriting
their existing changes. No scientific input value, event definition, active
extraction file or empirical result changed. This pass uses exact archive
verification rather than a model test because it removes only duplicated bytes.
