# Supplemental acquisition on Azure

The October 21 supplemental download runs on the existing `vm-limburg-eo`
(Standard_B2s_v2) in `rg-limburg-eo`. Private storage is the existing
`limburg-compact-eo` container, **prefix `expansion-v1`**; the original `v1`
archive is unchanged. No GPU or new VM is provisioned.

The deployed task root is `/home/eo/limburg-eo-expansion`. It reuses the working
`/home/eo/limburg-eo/.venv-cloud/bin/python` environment and the previously
authorized private Earth Engine credential already on the VM. Do not delete
that runtime while this service is running. No credential enters the explicit
acquisition bundle, Blob Storage, Git or logs.

`cloud_worker.py` reuses the original immutable Blob publication and SHA-256
readback implementation. It verifies all code/catalogue/input hashes recorded
in the expansion plan, exports the same jobs, uploads and reads back each TIFF,
checks its SHA-256, commits the receipt, then deletes only its disposable VM
cache. Progress is `expansion-v1/progress.json`; export-test status is separate
at `expansion-v1/_control/smoke.json`. Remote completion requires all 66,913
planned jobs to be committed and verified, not merely exported locally.

The supplemental prefix has a 300 decimal GB storage guardrail, allowing headroom
beyond the provisional ~125 GiB compressed estimate. This is not a dollar budget;
its source ledger is never silently shortened. The original archive ceiling and
archive are unchanged. The existing absolute acquisition shutdown timer remains
October 29, 2026 at 22:53:25 UTC. The worker requests VM deallocation on completion
or error as well. Disk/IP/storage charges continue while compute is deallocated.
No inference cloud plan was resumed.

## Handoff

All 13 cloud product exports passed full SHA-256 Blob readback. Only after that
success was the local script-114 downloader retired. All 3,418 completed local
TIFF/receipt pairs were retained. A local seed transfer initially uploaded 137
pairs; those pairs were finalized without leaving published data without receipts.
Their complete remote data will be SHA-256-verified by the cloud worker before
being counted complete.

To remove laptop dependence immediately, the local upload worker was also retired.
The other 3,281 local-only pairs are preserved locally, while Azure fetches their
jobs directly from Earth Engine. This knowingly duplicates some transfers; it
avoids requiring the laptop to remain online to finish seeding. The cloud worker
refreshes deferred seed entries before verification, so late uploads are visible.
No local data were deleted and no local encoder worker was changed.

`seed_pending.local-all.json` records the original full local inventory;
`seed_pending.json` is the 137-pair verified-upload inventory used by production.
“Uploaded” is distinguished from complete cloud SHA-256 readback. Local
`seed-progress.json` describes the final handoff policy; it is not the live
acquisition counter. Local `progress.json` is marked `retired_to_azure`.

## Inputs and service

Script 115 builds an explicit allow-listed, nonsecret tar bundle from the pinned
plan inputs and cloud source files, authenticating with Azure CLI without writing
tokens. Its bundle SHA-256 and path list are in local `cloud-bundle.json`. The
bundle is private at `expansion-v1/_control/cloud-inputs.tar.gz`; its hash was
verified on the VM before extraction. The service configuration is also uploaded
privately and hash-verified before installation. Azure managed identity accesses
only the existing allowed container and the dedicated VM's deallocation operation.

The completed original acquisition service is disabled. The persistent service
is `limburg-eo-expansion.service`, configured by `configure_service.sh`, with
three workers, single-thread numeric/GDAL settings, no automatic restart and
failure deallocation. The pre-existing deadline timer is retained.

Inspection on the VM:

```sh
systemctl status limburg-eo-expansion.service
journalctl -u limburg-eo-expansion.service -n 30 --no-pager
systemctl list-timers limburg-eo-deadline.timer
```

Local embedding runs still require the Mac to remain awake if they are to
continue. New EO acquisition and storage no longer depend on it. Download only
the supplemental files needed for subsequent coverage/model work; remote immutable
receipts and hashes allow checked staging later. Existing local files need not
be removed until the separately planned disk-cleanup task.

## Validation

Six focused publication/seed-refresh tests pass, including corruption/conflict
handling, readback and idempotent refresh of seeded metadata. Shell syntax and
lint pass. Real cloud smoke verified all 13 product types, with zero failures.
No model performance claim or revised empirical result is produced by this move.

Live status from the Azure-authenticated laptop (the Azure CLI runtime already has
the storage SDK):

```sh
/opt/homebrew/opt/azure-cli/libexec/bin/python scripts/115_handoff_eo_expansion_to_azure.py --status
```

This reads only the private progress object and refreshes local
`data/raw/limburg_eo_expansion/cloud-progress.json`; it does not scan all data
blobs or restart compute. `deployment.json` is a dated handoff receipt, not live
status. Production was observed committing additional files with zero failures.
