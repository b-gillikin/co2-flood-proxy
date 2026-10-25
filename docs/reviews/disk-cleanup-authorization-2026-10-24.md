# Disk Cleanup: authorization and execution notes

Brian authorized Disk Cleanup on October 24 when needed to finish the current
Limburg workflow and four supplemental configurations. He also authorized
Azure offloading of data not directly needed by those configurations if necessary.
At the check, approximately 130 GiB was available; this is a dated observation,
not a guarantee of later capacity.

Before supplemental extraction, aggregation and scoring, check actual free space
and projected output size. Preserve a working reserve; do not let the system
exhaust storage. Re-check during long phases. The existing 60 GiB staging reserve
is a practical storage-management reference, not a scientific exclusion rule.

Preferred order:

1. Remove disposable temporary files and verified obsolete/reproducible caches.
2. If needed, offload inactive source products or completed patch outputs to
   private Azure storage. Verify full upload/readback hashes and save a local
   restore inventory before removing any local copy. Confirm no active or queued
   process needs those paths. Keep extraction manifests, receipts, selected
   representations, scientific results, code and provenance locally.
3. Reuse remote data by verified staging when later work needs them. Never drop
   events, truncate the acquisition ledger or change model inputs to fit storage.

Do not remove files currently used by Presto, Galileo, current aggregation/scoring,
or the queued SatMAE/Copernicus-FM TOA and CROMA ascending-orbit configurations.
S2 TOA 10/20 m and QA60, ascending orbits 15/161, and retained baseline aggregates
are required by those supplemental comparisons. Other products are candidates
for offloading only after confirming all current and queued dependencies.

The Azure acquisition VM is deallocated and need not be restarted for Blob
transfers. Offloading is not authorization to restart GPU compute or provision
new compute. Storage/transfer charges remain possible.

No data were removed or offloaded by recording this authorization. The existing
workflows continue unchanged. Subsequent actions must log paths, reason, hashes,
remote destination/restore instructions and reclaimed bytes in this task's ledger.
