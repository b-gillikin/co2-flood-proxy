# Disaster recovery

The chapter's immutable inputs are copied to a dedicated private Azure GZRS
storage account. GitHub remains the recovery source for code and documentation.
The backup is additive: deleting a local file cannot delete its remote copy,
and Azure blob versioning retains overwritten objects.

```bash
make recovery-doctor
make data-inventory
make data-backup
make data-verify
make data-restore  # on a replacement machine; preserves existing local files
```

Run `az login` on a replacement machine. Access uses the signed-in Microsoft
Entra identity and is restricted to the backup account; storage keys and SAS
tokens are not stored in this repository.

The manifest is evidence of the exact bytes backed up. A checksum alone is not
a backup; successful `data-backup` and a periodic clean restore test are the
recovery controls.

## Completed discharge study — verified 24 November 2026

The private discharge backup contains 5,915 files in 24 archives (1.46 GiB).
It covers the prepared analysis inputs, gauge deliveries, final fits, paired
predictions, supporting figures and code. The scope is recovery of the
completed comparison. Intermediate tuning weights and duplicate prepared
tables were omitted.

The [recovery receipt](limburg-discharge-2026-11-24.json) identifies the
separate Azure manifest and restore receipt. Every archive was downloaded
after upload and checked against its archive and member SHA-256 hashes.
A clean-folder restore recovered six representative files. The restored
prediction table opened with 81,857 rows, and the restored XGBoost model
loaded successfully.

For a restore, find the required relative path in the Azure manifest's
`archives[].records` list. Download its `blob` from the configured private
container using Microsoft Entra authentication. Verify the archive hash,
extract only the requested regular files into a clean folder, then verify
each file against its member hash. The general chapter recovery manifest
applies to its own scope and is separate from this package.

## Azure Cold tier for historical EO materials

The earlier original and expansion Sentinel collections, applied EO input
copies and result bundles, external flood-mapping predictions, and the
November 18 derived-cache bundle payloads are kept in Azure Cold storage.
The download paths and checksums in the original recovery records still
apply. The discharge recovery package, EO control files, and derived-cache
catalogue and receipts use Hot storage.

The [24 November inventory receipt](limburg-historical-eo-cold-2026-11-24.json)
records 208,396 objects (276.79 GiB) and the exact prefixes, verified after
tiering by matching blob names, sizes and ETags to the original listing.

Use the recovery catalogue or original archive ledger to select the specific
files needed. Cold supports direct reads at the existing paths. Azure
charges for bytes read, in addition to any transactions or outbound traffic.
Its 90-day minimum applies if the blobs are erased, overwritten, or moved
out of Cold early.

## Historical compact imagery offload (10 November 2026)

The inactive `data/raw/limburg_compact_eo` imagery can be retired locally using
`scripts/230_offload_historical_compact.py --run --target-gib 45` with Azure CLI's
Python. These existing objects are in **stkerkradeprod01bg / limburg-compact-eo /
v1**, separately from the generic recovery account above. No new VM is needed.
Retirement requires local SHA-256, remote byte-readback verification metadata,
matching scientific receipts, a fresh download/restore test, and remotely
read-back intent ledgers before local unlink. Scientific receipts/catalogues,
aggregates, results, weights, applied-task imagery and other chapters stay local.

The append-only recovery mapping is
`results/disk-cleanup-2026-11-10/compact/removed.jsonl`; each row also identifies
its independently preserved remote intent ledger. For one exact file:

```bash
python scripts/182_restore_offloaded_expansion.py \
  --ledger results/disk-cleanup-2026-11-10/compact/removed.jsonl \
  --path data/raw/limburg_compact_eo/images/EXACT_WINDOW/PRODUCT/EXACT_FILE.tif \
  --restore
```

To restage the entire original catalogue, use script 103 with an adequate disk
budget. It verifies existing bytes and downloads missing files. Remove
`data/raw/limburg_compact_eo/OFFLOADED-2026-11-10.json` only after all retired
paths have been restored and hash-verified. Historical extraction entrypoints
fail explicitly while this marker exists; offloading must not become missing
observations or a smaller census. Existing completed results remain valid.

## Historical derived-cache offload (18 November 2026)

Brian authorized the first 40–60 GiB cleanup of inactive Limburg caches. The
current run preserves lossless copies of the spatial tensor arrays and bulky
supplemental per-patch JSON records in **stunumeritphdbackupbg /
dissertation-recovery / chapter1-co2/derived-eo/2026-11-18**. It retains local
run-level index/manifest/status files, supplemental NPZ arrays, aggregate
representations and results. Current DISE/representation inputs, raw source
observations/weather/landscape data, weights and other chapters are untouched.

Monitor `results/disk-cleanup-2026-11-18-derived/progress.json` and `worker.log`.
The offload is **complete**. All 1,047,888 archived files were verified against
remote compressed bundles and member hashes before local retirement; a full
restore pilot passed. The finalizer verified the remaining files and protected
current-study hashes, then backed up the exact SQLite recovery map. The durable
closure receipt is `results/disk-cleanup-2026-11-18-derived/closure.json`, with
the detailed record at `docs/reviews/derived-cache-offload-2026-11-18.json`.
Observed available space increased by 51.75 GiB (78.12 to 129.87 GiB during
closure; later APFS readings can differ).

Resume an interrupted worker (same catalogue, no model rerun):

```bash
/opt/homebrew/Cellar/azure-cli/2.83.0/libexec/bin/python \
  scripts/278_offload_historical_derived.py --run
```

With the local catalogue, restore one exact file using `--restore-path` in
script 278. After closure, restore a whole bundle or all archived files:

```bash
/opt/homebrew/Cellar/azure-cli/2.83.0/libexec/bin/python \
  scripts/280_restore_historical_derived.py --bundle 00000

/opt/homebrew/Cellar/azure-cli/2.83.0/libexec/bin/python \
  scripts/280_restore_historical_derived.py --all
```

The full restorer downloads each bundle once, verifies its compressed hash and
every uncompressed member, refuses to overwrite different local bytes and
clears `OFFLOADED-DERIVED.json` only after the entire census is restored. On a
replacement machine it can recover the SQLite index from the closure receipt.
While markers exist, owning cache readers fail explicitly rather than treat
cold data as unavailable observations. Original executed readers remain in
Git and `provenance/source-snapshots/`; guard-only compatibility is recorded.
