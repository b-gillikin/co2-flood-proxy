# Disk Cleanup

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
