# Presto runtime migration — 2026-10-18

Brian authorized a fresh full run with the faster CPU runtime after reviewing
the [bounded benchmark](limburg-presto-cpu-investigation-2026-10-18.md).

## Active route

- Python 3.11, **torch 2.9.1, four CPU threads, pixel batch 128**, float32.
- Isolated runtime `.venvs-eo/presto-torch291/`: torch copied from the tested
  isolated probe; inherited dependencies reference the unchanged pinned original
  Presto environment through a `.pth` file. Visible distributions are recorded in
  `environments/eo-screen/presto-torch291-macos-arm64.lock.txt` and the run identity.
  Keep the original environment until this run is complete/reproducibility needs
  are settled; it is not a disposable duplicate during Disk Cleanup.
- `scripts/109_extract_presto_cpu_sequences.py` wraps the original extraction
  logic and records runtime profile, actual torch version, CPU threads, batch,
  executable, wrapper/lock hashes and existing source/weight/input provenance.
- New output root: `data/processed/limburg_eo_presto_torch291_sequences/`.
- Full-census run ID:
  `69e43010176a90d56dd5249b9d298a05ab8560423c9a8011cc9093e2bbd7883e`.
- All 742 contexts remain; no sampling, pixel reduction, changed histories,
  altered masks, precision change or different pooling. Starts from zero and
  resumes only its own verified receipts on future restarts.

The final exact-area aggregation uses only the new root. Existing Presto
aggregates from other runtime profiles cannot satisfy the queue's selected
profile. Other models retain their prior execution paths and completed outputs.

## Validation and handoff

The dedicated wrapper passed a real 12-month held-imagery smoke test: one full
patch sequence written, zero errors and exact repeated output. The controller's
focused tests cover routing/profile separation, rejecting old-runtime aggregate
substitution, unchanged GPU routes, merging integrity and timeout-resume safety.

The original Presto worker was stopped after 151,401 scanned patch sequences and
44,664 written embeddings, with zero errors at the last recorded update. All
outputs remain under original run
`db2e82ca2ae1be5da3d9445bb5183992605807179b8060e0651fd219986cb1f7`;
its status is `interrupted_for_torch291_handoff`. It is retained for provenance
and later Disk Cleanup, not mixed with the new outputs.

The controller was replaced while preserving the existing OlmoEarth GPU process.
The selected new runtime is prioritized to launch before potentially lengthy
receipt checks on already-completed models. Those checks still run before
acceptance/merging. The initially verification-only replacement was retired
before it launched children; no duplicate GPU or Presto inference worker remains.
Galileo's suspended process is explicitly deferred in the plan, so it is not
restarted or counted as completed. AnySat retains its pending GPU slot.

Local process/run records: `logs/eo-census/presto-torch291-handoff.json`;
queue status: `logs/eo-census/progress.json`; model log: `logs/eo-census/presto.log`.
The log includes the old and new run IDs; progress must use the selected new run.

## Interpretation

The benchmark suggested faster encoding and numerical agreement, not a guaranteed
end-to-end speedup or finish date. Measure production progress across comparable
contexts before revising the ETA. This migration creates no scientific result,
new model arm or change to event inclusion.
