# Deferred plan: recoverable offloading of completed Limburg EO outputs

4 November 2026. Brian requested a plan, with no rush to execute. **Planning
only: do not launch transfers, alter the queue, or remove payloads now.**
This is storage engineering, not a change to research scope or sample selection.

## Objective and activation

Free local space when useful while preserving the exact completed scientific
outputs and their provenance. Restoring an offloaded run must require download,
not encoder extraction or model fitting. A recipe for regeneration is not an
acceptable substitute for an archive of the actual retained outputs.

Activation is manual on a later instruction to implement/run the offloader.
A free-space warning may prompt review but must not automatically launch it.
At planning time approximately 89 GiB is free. The existing 50-GiB reserve and
current queue behaviour remain unchanged. Prefer a small pilot before reclaiming
large caches; no reason to offload the whole workspace at once.

## Scope: keep the work, move its bulky storage

| Material | Treatment |
| --- | --- |
| Completed older per-patch NPZ/array payloads and their per-patch receipts/missingness records | Candidates for exact, recoverable cold storage after dependency checks |
| Aggregated catchment embeddings, selections, scores, uncertainty outputs, actual analogue/event reviews, figures | Keep locally; include a compact provenance/results copy in the archived run bundle |
| Configurations, run manifests/status, environment locks, code revisions and executed-source snapshots | Keep locally and archive with the run; preserve all versions |
| Current spatial feature/tensor caches, raw imagery, weights, live results/checkpoints and required runtimes | Protect; not targets for this first offloader |
| Other chapters, field originals, provider deliveries, human labels and human drafts | Outside scope |

The historical ten-encoder study is not discarded. Selected, corrected and
superseded runs retain their distinct identities and interpretation. Cold storage
changes access latency, not scientific status or the findings.

## Initial inventory and target order

Use an explicit, versioned allowlist of exact run paths. No recursive purge of
`data/processed`, no wildcard deletion, no inference that an old date means
unused. First assess:

1. `data/processed/limburg_applied_galileo_spatial_v1`: bounded pilot candidate,
   approximately 896 MiB. The November 2 receipt reports 446 features identical
   to v2. Recheck present bytes, future-job references and link allocation. Keep
   v1's distinct index/receipts and restoration record. v2 remains protected.
2. Completed older patch extraction runs selected in
   `config/limburg_eo_coherent_selected_runs.json`, including its referenced
   Prithvi and OlmoEarth runs. These can be valuable retained outputs, not junk.
   Inspect one exact run at a time; do not offload parent directories containing
   mixed smoke, repaired, selected and engineering runs indiscriminately.
3. Inactive unselected engineering/superseded runs, only after identifying
   whether they still contain unique error evidence or shared payloads.
4. Historical `eo_retrieval_cache` (~1.3 GiB) and
   `eo_followup_route_retrieval_cache` (~57 MiB), lower priority.

For each run report file count, logical/allocated bytes, shared-link bytes,
estimated exclusive reclaimable space, scientific role, aggregate/provenance
locations and dependency findings. Do not promise that directory size equals
freed APFS space. Shared hard links and copy-on-write storage can reduce gains.

Read the **current** queue pointer, all pending job commands/configuration,
cache/tensor indexes, local-application inputs and runtime links. At present,
protected cache roots include `limburg_terramind_encoder_v1`,
`limburg_applied_galileo_spatial_v2`, `limburg_copernicus_spatial_v1` and
`limburg_tensor_cache_v1`. This list supplements dependency discovery; it is not
an exhaustive permanent protection list. Future configuration changes invalidate
an earlier eligibility decision.

## Proposed implementation

A separate CLI, provisionally `scripts/offload_completed_eo.py`, with explicit
phases: `plan`, `archive`, `verify`, `retire`, `restore`, `status`. Default to
read-only planning. Each mutation consumes a saved manifest; no delete-on-upload
mode and no implicit target discovery during retirement. No scheduled task,
new VM, background daemon or integration into training is needed.

Use a streaming JSONL inventory plus an on-disk SQLite index if sorting/lookup
requires it. Millions of patch files must not become one in-memory file list,
receipt dictionary or tar-member list. Verification also streams. Reuse the
existing SHA-256/remote-readback approach from script 207, **not its unbounded
in-memory inventory and whole-run double-archive storage layout**.

### Archive format and small local index

- One model/run per archive set; split into independently verifiable shards.
  Initial target about **1 GiB**, maximum **2 GiB** per shard, with a member-count
  ceiling (initially 50,000). Benchmark the pilot and adjust operational defaults
  transparently; do not change the scientific file census to fit a shard.
- Preserve every allowlisted scientific payload and receipt. Record relative
  path, bytes, SHA-256, original mtime/mode and link information. Store regular
  members; reject path traversal and unsupported symlinks/devices. Large files
  that exceed the configured shard limit require an explicitly budgeted plan,
  not silent exclusion.
- Use a standard lossless tar format, with low-level gzip if useful. NPZ is
  already compressed; compression gains are not assumed. Record format/version
  so restoration does not depend on the live encoder environment.
- Keep a small local `OFFLOADED.json` and chapter-level catalogue mapping exact
  run/path ranges to remote shard keys, digests and inventory files. Preserve a
  remote copy of the complete run index and required metadata. Never embed
  temporary credentials or signed URLs.
- Keep aggregate/result files locally as well as in the compact run provenance
  bundle. Do not remove all evidence from an old directory after offloading.

### Remote location and discoverability

Use the existing dedicated recovery destination named in `recovery/config.json`
(`stunumeritphdbackupbg` / `dissertation-recovery`), with a separate derived-output
prefix such as `chapter1-co2/derived-eo/v1/<run-id>/<sha256>.tar.gz`.
Validate the subscription, account, permissions, storage policy and charges at
activation; no new resource provisioning or tier/lifecycle changes are planned.

The ordinary backup configuration covers raw paths, **not these processed
caches**. A generic backup success is therefore not evidence of their recovery.
Record the separate archive catalogue/restore command in `recovery/README.md`;
do not claim the existing whole-chapter restore tool knows this new prefix
unless it has actually been integrated and tested. Keep compact receipts/index
hashes in Git; large inventories remain local and remote with their own hashes.

### Durable per-shard sequence

`inventoried → packed → local_verified → uploaded → remote_verified → retire_ready → local_retired`

1. Confirm the exact run is complete/quiescent and outside protected dependencies.
   Capture input/config hashes and file identity/stat records. Do not stop a
   training job to make an input eligible.
2. Stream a shard, hashing its source bytes as read. Detect mutation during
   packing; preserve the originals and invalidate that shard on a mismatch.
3. Read the completed local archive and verify its member census, sizes and
   individual hashes against its inventory. Atomically mark it locally verified.
4. Upload additively under its content hash, using Entra credentials. Never
   overwrite a different object. A remote same-name object is reusable only
   after verification, not merely because it exists or has a checksum metadata tag.
5. Download the full remote shard, verify its SHA-256, and stream-check every
   member against the inventory. Check the complete remote run metadata too.
   An ETag, listing, upload receipt or sampled member is insufficient.
6. For the pilot, restore the **entire small candidate bundle** to an isolated
   scratch directory and verify every file/path. For later shards, full member
   verification is compulsory; perform a representative actual extraction test
   for every archive format/code revision. Use safe extraction and no overwrite
   of existing chapter files.
7. Before retirement, recheck the current queue/dependencies and exact local
   source identity/digest. Retire only files covered by durable remote-verification
   receipts. If anything changed, leave it and mark it unresolved. Preserve
   manifests/status, aggregates, decisions, source snapshots and the offload map.
8. Verify the expected local remainder and protected-file hashes, record observed
   free-space change, then delete only disposable local packing/readback copies.
   Keep remote archives and inventories; never propagate local deletions remotely.

The catalogue must distinguish `uploaded`, `verified`, `local_retired` and
`restore_failed`; do not collapse them into a single backed-up flag. Failed or
interrupted packing/upload/verification **never authorizes source removal**.
An interrupted retirement resumes from an append-only per-file ledger; it must
not lose the mapping of already removed files.

## Avoid a silent scientific change after offloading

Some legacy readers may skip absent patch files. Before a selected historical
run is eligible, add offload-aware checks at its owning aggregation/analysis
entrypoints: if the required run is cold, stop with the explicit restore command
or offer a separately invoked restore. Missing archived payloads must never
become `no_observation`, dry/zero values, partial coverage or a smaller census.

Preserve the selected-run maps and aggregate hashes. Restore to the original
relative paths and verify hashes before enabling a legacy rerun. Do not redirect
a historical script to a different run merely because it is local. If implementing
these guards would change a currently hashed/running source module, defer that
target or the guard deployment; do not patch the active experiment underneath it.

## Resource and spending controls

- **One offload worker**, no GPU. Low CPU priority, one compressor and one Azure
  connection; do not add two busy compression workers alongside training.
- Coordinate the pack/upload/readback phase with the existing
  `results/applied_study_v3/.archive-owner.lock`. Yield priority to the current
  queue's result preservation; do not hold the lock while idle or waiting for
  operator activation. Do not change the current lock owner or queue code now.
- Default maximum local scratch reservation about **5 GiB**: one up-to-2-GiB
  packed shard, one readback, plus bounded index/extraction overhead. Pilot
  extraction must be separately budgeted; shrink the pilot/shard if needed.
  Preserve the existing **50-GiB free reserve** throughout, including concurrent
  training writes. Recheck free space during packing and transfer; pause this
  offloader before it threatens the fit. A low-space failure leaves originals.
- Resume at durable shard boundaries. Do not create a whole-run archive and a
  whole-run readback on an already pressured disk. Checkpoint stopped work and
  clean only identified incomplete scratch copies before retrying.
- Estimate storage bytes, requests and full readback/download volume from the
  inventory before activation; report Azure charges using current subscription
  terms then. No assumption of free storage/egress or automatic spending expansion.
- No automatic cloud lifecycle expiry or archive-tier transition. Recovery should
  not unexpectedly require rehydration delay or a new model extraction.

## Failure/recovery checks before real payload retirement

Use synthetic small files first; then the bounded real pilot. Test interrupted
upload, corrupt/truncated download, missing member, wrong account/prefix,
path traversal, changed local file, incomplete run, overlapping active input,
shared hard links, low disk space, token expiry and interruption halfway through
retirement. A failed check preserves source files and records the reason.

Confirm that local summaries and historical results remain byte-identical,
current queue input hashes remain unchanged, and a restored bundle is readable
by its appropriate original reader. The first pilot proves the procedure; it
is not a claim that every older run is already safe to retire.

## Deliverables when activated

1. Read-only inventory, dependency/protection report and size/cost estimate.
2. Versioned offload CLI, explicit target manifest and focused failure tests.
3. Small pilot upload, full readback/member verification and full pilot restore.
4. Local/remote catalogue plus documented one-run restoration command.
5. A separately invoked retirement phase and audited before/after space report.
6. Further runs only as needed; current source data and all other chapters remain
   untouched.

**Current status: deferred. No offloader code, upload, new cloud resource,
retirement, queue change or automatic activation was performed by this plan.**

## Activation update — 10 November 2026

Brian authorized the recommended first 40–60 GiB target. The first pass instead
used already recoverable historical compact imagery, so the derived embedding
archive machinery above remains deferred. Script 230 reuses the verified-pair
retirement engine with the exact compact-image root and Azure `v1` prefix.
It retired 28,642 local image copies (45.000 GiB logical), recovering 44.987 GiB
of observed free space: 76.642 → 121.630 GiB. Original local scientific receipts,
catalogues and all completed embeddings/results were preserved. No other chapter
was touched. This does not authorize automatic further retirement.

See `docs/reviews/compact-imagery-offload-2026-11-10.json` and its remote-catalogue
receipt. Each source hash matched existing remote full-readback verification and
linked receipts; a fresh complete-file restore test passed. Remote intent ledgers
were read back before each batch was removed. This was not a fresh download of
the entire 45 GiB. The post-audit verified every retired path is absent and every
local receipt remains hash-identical. Five safety/restore/reader-guard tests pass.
Recovery instructions and the distinct Azure destination are in
`recovery/README.md`. Offload guards preserve historical census semantics; the
original executed loader sources are retained in provenance snapshots with
explicit compatibility records. Numerical processing and scientific findings
have not changed.
