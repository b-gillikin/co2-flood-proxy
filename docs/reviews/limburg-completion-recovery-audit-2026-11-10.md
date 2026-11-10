# Limburg completion and recovery audit — 10 November 2026

## Completion

Passed the full planned census: 720 neural jobs (1,200 candidate fits), 20 physical controls, 48 complete contrasts, and 60 matched local summary groups. All 240 full-label local applications and 20 local physical applications reconcile. The five test folds cover each eligible test record exactly once within each task/learner/budget/seed configuration.

Checked 228,168 prediction hashes, 331,228 retained archive members, and the receipt bindings for 1,200 intentionally retired checkpoints. No unexpected missing files or hash mismatches were found. Source, input, cache-index and final benchmark provenance hashes reconcile. This is a completion/integrity audit, not a new assessment of predictive skill or scientific validity.

## Recovery

All 720 content-addressed Azure job bundles currently exist, with receipt-matching lengths and SHA256 metadata (24,828,909,906 bytes combined). Each has a prior full-readback receipt. Current object checks do not constitute a fresh download of every archive.

Fresh full downloads and every-member verification passed for four configuration-selected native bundles: Galileo, TerraMind, Prithvi and Copernicus, each group01, full labels, seed 42. Each selected checkpoint, completion record and selection record was restored into an isolated audit directory and hash-checked. Checkpoints were not deserialized or executed.

Per-job bundles did not cover the consolidated final summaries and separately stored physical controls. An additional closure bundle preserves those, evaluation records, queue/recovery records, pinned source/input files and audit evidence. The closure upload, full remote readback and every-member verification passed; its receipt is recorded in the companion JSON.

Recovery supports restoring retained model/checkpoint artifacts. It does not promise optimizer-state continuation, a complete runtime environment, all raw tensors/imagery, or frozen encoder weights omitted by the documented checkpoint policy. Inference still requires compatible code/runtime and the relevant frozen encoder assets.

## Evidence and restoration

Local evidence: `results/completion-audit-2026-11-10/`: `local-summary.json`, `jobs.json`, `remote-summary.json`, `remote-objects.json`, `fresh-readbacks.json`, the two executable audit scripts, and isolated `restore-tests/`.

Recovery location: account `stkerkradeprod01bg`, container `limburg-compact-eo`; exact blob names and hashes are in receipts. Download the exact receipt-named blob using Azure authenticated access, verify its archive SHA256 and every inventory member with `verify_bundle` in `scripts/207_preserve_applied_results.py`, then restore required members to an isolated directory before any replacement. Preserve existing files and avoid loading untrusted checkpoints.

No scientific runs, model settings, labels, or other chapter data changed. The next substantive step is reviewing the consolidated findings and their uncertainty, not repeating completed jobs solely because of this audit.
