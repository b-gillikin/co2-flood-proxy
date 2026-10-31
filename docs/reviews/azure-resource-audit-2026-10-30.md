# Azure research subscription audit — 30 October 2026

Read-only audit of Azure for Students. Workplace subscriptions were excluded. No services were stopped, resources deleted, tiers changed, or scientific data removed.

## Authorized retirement completed after the audit

Brian subsequently authorized inspecting and retiring `vm-limburg-eo`, its 64-GiB OS disk and static public IP. The VM's expired persistent deadline timer caused immediate deallocation on initial inspection attempts. Its VM-scoped self-deallocation role assignment was removed, the VM briefly started, and the obsolete acquisition services/timer disabled for preservation.

Both guest acquisition directories were archived, excluding credentials, `.config`, `.ssh`, `.azure`, `.env`, virtual environments and Python caches. Service definitions and a file inventory were also preserved. Six files were uploaded and read back with SHA-256 verification, then independently downloaded and verified locally. The tar archive contains 8,912 entries and is 23,115,999 bytes; excluded credential paths were checked against the archive listing.

- Private Azure prefix: `stkerkradeprod01bg/limburg-compact-eo/retirement/vm-limburg-eo/2026-10-30/`.
- Local copy: `results/azure_resource_audit_2026_10_30/vm-retirement/`, including `manifest.json` with sizes and hashes.
- Guest archive SHA-256: `d82d64397a8bc7a4a8accc02f3e960772af3da368f23b08187ea4d3433dd1c06`.
- VM, disk and public IP deletion commands completed successfully. IP detached from the NIC before deletion. Remaining NIC/NSG/VNet were not part of the explicit deletion request.
- Source EO archives, other Azure services and all other chapters' data were preserved. Temporary inspection compute may incur a small final usage charge.

## Initial audit recommendations (before authorized retirement)

| Resource | Observed state | Recommendation |
| --- | --- | --- |
| `vm-limburg-eo` | Deallocated; Standard_B2s_v2; acquisition complete | Retire the acquisition VM after preserving any useful guest-only control files/logs. Current model workers are local. |
| VM OS disk | 64 GiB StandardSSD_LRS, still attached/reserved | Delete with the retired VM after that check. Base public retail E6 LRS rate is $4.80/month in westus3, excluding applicable mount/operation charges. |
| `vm-limburg-eoPublicIP` | Standard static IPv4, still allocated | Delete with retired VM networking. Public retail rate $0.005/hour, approximately $3.65 per 730-hour month. Disk plus IP base savings approximately $8.45/month. |
| `func-kerkrade-monthly-pull-bg` | Running; enabled `air_quality_timer` every minute; other timers disabled | This is the retained Blynk device collector despite its name. Keep while the continuing record is wanted. Stopping ends future observations; current Limburg EO analysis does not need its live stream. Function compute reports $0 month-to-date. |
| KNMI and ERA5 backfill Function Apps | Both stopped | Can retire old deployments for tidiness. Already stopped, so no significant current compute saving. Preserve weather datasets and shared function storage dependencies. |
| Legacy communication/email and `testkerkrade*` resources | Retained email infrastructure, Key Vault, monitoring and Azure ML-style storage | Candidates for a later dependency-checked retirement. Present costs are negligible. Names alone do not establish safe deletion. |
| Shared consumption plan and monitoring | Functions share Y1 plan; Log Analytics reported $0 month-to-date | Keep dependencies of retained collector. No evidence of a large monitoring cost. |

Deallocation stops VM compute billing but does not remove disk/IP charges: https://learn.microsoft.com/en-us/azure/virtual-machines/states-billing . Retail rates verified through https://prices.azure.com/api/retail/prices using westus3, E6 LRS and Standard IPv4 Static Public IP meters. These are approximate future retail savings, not a bill guarantee.

## Storage to retain

- `stkerkradeprod01bg/limburg-compact-eo`: 206,452 current blobs, **154.740 GiB**. Original image prefix 54.932 GiB; expansion image prefix 99.788 GiB; remaining space is control/provenance. Both progress manifests report complete, zero failures: 36,304 original and 66,913 expansion acquisitions. These are scientific source archives and receipts, not obsolete inference caches.
- `stunumeritphdbackupbg/dissertation-recovery`: 2,545 current blobs, **5.066 GiB**, GZRS Hot. Keep this recovery snapshot.
- Other legacy weather, function-host and test containers could be listed, but blob listings returned **403 AuthorizationPermissionMismatch**. Their contents/sizes were not verified and must not be described as empty or redundant. No account keys were retrieved and permissions were not expanded.
- Inspected EO Blob service settings did not establish enabled soft-delete/versioning accumulation. The inventory counts live blobs; it is not proof about every possible retained storage class.

Do not delete either scientific archive or other chapters' data. Consider targeted Cool storage only after access needs settle: retrieval, transactions and minimum retention can offset the small saving. https://learn.microsoft.com/en-us/azure/storage/blobs/access-tiers-overview

## Cost evidence

Azure Cost Management ActualCost query for 1–30 October, as reported on audit day (USD; billing may lag): approximately **$27.61** total. Major charges: storage-account bandwidth $9.196; historical VM compute $7.498; shared production storage $3.579; historical VM bandwidth $3.131; VM disk $2.262; public IP $1.716; dissertation backup $0.224. All three Function Apps report zero compute cost. Historical compute/transfer charges are not evidence the VM is still running.

## Backup maintenance finding

The inspected recovery objects are dated **31 August 2026**, under chapter0-intro, chapter1-co2, chapter2-bukidnon and chapter3-peja. This is an old recovery snapshot, not demonstrated current coverage. Root `tools/dissertation_backup.py` still names `chapter0-intro` and omits `chapter4-jordan`; update and validate that backup workflow separately. Do not delete this old snapshot before a current replacement is verified.

## Evidence and limitations

Audit used explicit research subscription selection, ARM resource/function state, readable Blob metadata/manifests, Cost Management and public retail prices. Detailed temporary evidence: `/private/tmp/azure-audit-20261030/storage-inventory.json`, `extra-checks.json`, `e6-prices.json`. The initial read-only audit did not inspect the guest filesystem; the subsequent authorized inspection, preservation and retirement are recorded above. No active local extraction source/configuration was changed.
