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
