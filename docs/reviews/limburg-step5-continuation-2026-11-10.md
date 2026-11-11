# Step 5 continuation audit — 10 November 2026

Internal execution record; no dissertation prose or external accuracy result.

Brian authorized continuing automatically when source training finishes.
The detached mapping controller waits for all six completed model and manifest
hashes. It then runs the full external U-Net census followed by Copernicus,
using one MPS worker. The source training queue remains in control until its
six fits finish. Production email alerts remain disabled.

Checks before starting the continuation controller:

- Eleven targeted input/grid/scoring/checkpoint/prediction-recovery tests pass.
  The test environment requires its explicit PROJ data directory; the production
  Copernicus environment resolved the real tile coordinates in the smoke test.
- A real 224px external patch, with 49,362 valid pixels, gives exactly the same
  probabilities through the shared-feature/multi-seed mapping path and the
  single-model path for both U-Net and Copernicus (maximum difference zero).
  This checks execution equivalence, without scoring external labels.
- Unknown pixels retain unknown probabilities and class 255. Class decisions
  are calculated before float16 probability serialization.
- Resume requires each prediction locally with its hash or in an archive with
  successful remote readback. Model/checkpoint identity is checked on resume.
- An actual Azure upload/download/hash test passed with prediction and receipt
  recovery. Its temporary test blob and local files were removed.
- The conventional physical mapping census finished all 3,127 evaluations.
  Learned mapping and the local receiving-case census are still pending.

The archive script retains compact local receipts/ledgers and removes only its
verified prediction products. It does not clean or offload other chapters.
No source model, imagery or target label is deleted. Final source models and
their manifests remain local. The trained-model mapping stage does not read
target labels; downstream Step 6 will use those labels for evaluation.

Status and logs:

- `results/limburg_chapter_sized_v1/mapping_queue_status.json`
- `results/limburg_chapter_sized_v1/engineering/mapping-queue.log`
- `results/limburg_chapter_sized_v1/engineering/external-unet.log`
- `results/limburg_chapter_sized_v1/engineering/external-native.log`

Sleep/wake retains running processes. Reboot or process termination requires
restarting the controller after login; durable per-tile receipts avoid repeating
verified completed tiles. Worker retries are bounded to expose persistent faults.
