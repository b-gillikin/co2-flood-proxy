# Compact EO acquisition on Azure

This moves acquisition of the existing pinned compact imagery manifest to a
dedicated VM. It does not change event coverage, composites, model inputs or
scientific methods. Source scripts 95 and 96 must match the manifest hashes.

## Deployment and current handoff

`deployment.json` records the nonsecret Azure resource IDs and absolute deadline.
The VM is `vm-limburg-eo` in `rg-limburg-eo`, West US 3, zone 1. The private
archive is `https://stkerkradeprod01bg.blob.core.windows.net/limburg-compact-eo`,
prefix `v1`. Storage is in East US. Cross-region transfers add a small charge.

As of 2026-10-15, the acquisition service is **running independently on Azure**.
Brian explicitly approved the private Earth Engine credential transfer. All four
product export checks passed, including SHA-256 readback, and production has
downloaded further files successfully. All 3,341 completed local TIFF/receipt
pairs were uploaded; the worker was restarted after the last upload to refresh
its archive inventory. The local compact worker was retired and its files
retained. The laptop can close. Seeded files have transport MD5 validation and
matching local SHA-256 receipts; production performs full SHA-256 readback when
it reaches those jobs. Upload completion is not a claim that all planned imagery
has been acquired or all seeded files have finished cloud readback.

All twelve deployed source/input hashes were checked. A nonsecret reproducibility
bundle is stored at `v1/_control/acquisition-inputs.tar.gz`; its SHA-256 is in
`deployment.json`. It contains only the explicitly listed scripts/manifests and
input receipt, never credentials or raw gauge files.

No raw gauge files, SSH private keys or Earth Engine credentials enter the Blob
archive or Git. SSH is restricted to the researcher's configured public IP.
The managed identity has Blob Data Contributor only on this new container and
a custom deallocation-only permission on this exact VM; it has no VM Contributor
role. Earth Engine credentials, if approved, belong only in
`/home/eo/.config/earthengine/credentials`, mode 600, directory mode 700.

## Completion sequence

1. Authenticate Earth Engine on the VM using the approved method. The task root
   is `/home/eo/limburg-eo`; the interpreter is `.venv-cloud/bin/python`.
2. Run `infrastructure/compact_eo/cloud_worker.py --smoke` there. It exports one
   job per product and verifies a full SHA-256 readback from private Blob Storage.
3. Pause the local compact worker only after the cloud check succeeds. Finish
   seeding all local TIFF/receipt pairs using `--seed data/raw/limburg_compact_eo`
   from the laptop, with Azure CLI authentication. Rerunning skips identical
   uploads. Do not resume the superseded full-archive worker.
4. Write `data/raw/limburg_compact_eo/seed_pending.json` on the VM as a JSON list
   of all seeded TIFF relative paths. The production service defers these jobs
   until after new acquisitions. It then verifies seeded blobs by SHA-256.
5. Start `sudo systemctl enable --now limburg-eo.service`; inspect its journal
   and `v1/progress.json`. Confirm new exports and archive readbacks before
   ending the local worker. The laptop can close after all seed uploads finish.

## Controls and inspection

On the VM:

```sh
sudo systemctl status limburg-eo.service
sudo journalctl -u limburg-eo.service -n 30 --no-pager
systemctl list-timers limburg-eo-deadline.timer
```

From an Azure-authenticated laptop:

```sh
az vm get-instance-view -g rg-limburg-eo -n vm-limburg-eo --query instanceView.statuses
az vm deallocate -g rg-limburg-eo -n vm-limburg-eo
az vm start -g rg-limburg-eo -n vm-limburg-eo
```

Deallocation stops compute billing; disk, IP and stored blobs still incur charges.
The absolute timer is 2026-10-29 22:53:25 UTC. The worker also requests
deallocation on completion, error, deadline or storage limit. Systemd invokes
deallocation on service failure. Restarting later does not extend that deadline.
The archive ceiling is 70 decimal GB; this is a storage limit, **not a dollar
spending cap**. The planning target is USD 20–40 acquisition plus roughly USD
1.50–4/month retained storage, depending on volume and transactions. Fourteen
days is a maximum compute window, not a promise of completion.

Each immutable TIFF has SHA-256 metadata and a matching receipt. Uploads use
transport MD5 checks; production reads the complete blob back and checks SHA-256
before marking it complete. Only verified, disposable VM cache files are removed.
Local source files are retained. Missing/failed jobs remain explicit; a restart
verifies and resumes. `progress.json` reports completion only when every planned
file is committed. Smoke-test status is separate from production status.

## Validation

Fifteen focused tests pass across cloud publication, compact acquisition and
the source archive helpers. They cover hash corruption, immutable conflicts,
restart behavior, storage limits, temporal/orbit filtering and source provenance.
These checks establish transport and scheduling correctness, not model
compatibility or scientific results. Actual cloud export checks passed for
all four product groups with zero failures.
