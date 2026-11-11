# Limburg chapter execution plan — 10 November 2026

Internal research and execution plan. Brian writes dissertation and article text.
The accepted scientific scope is in `config/limburg_chapter_sized_study_v1.json`;
this plan makes it runnable without reopening the archived broad programme.

## Question and contribution

**Question:** How do satellite AI and conventional methods compare in mapping
new flood events, and how does the choice of pre-flood reference affect their
performance?

Compare Copernicus-FM paired SAR change, a same-input U-Net and a competent
physical SAR change/water rule under two pre-event reference policies. The
contribution is an event-level assessment of model choice, reference preparation,
errors, coverage and actual resources. Do not claim improved operational warnings
or general model superiority from map agreement alone. René/Jens gauge records
provide event and measurement context, not pixel labels.

## Work sequence

| Order | Work | Reviewable output |
| --- | --- | --- |
| 1 | Complete the source-to-target input contract: SAR radiometry/processing and geometry, per-date Copernicus statistics and metadata, fixed flood/permanent-water labels, P0/P1 common support, and physical-rule specification. Freeze the source-only selection recipe. | Versioned input contract, source diagnostics and checked examples. |
| 2 | Retrieve the nine pinned GEOID shards (9.068 GiB) with hash verification. Inventory label timing, linked activations and source-footprint overlap. Search and acquire P1 under a label-blind, same-processing policy. If processing parity requires it, retrieve a harmonized P0 through the same chain. | Acquisition manifest, provenance/coverage matrix and paired-support census. |
| 3 | Build native-grid 1024px evaluation with bounded windows, edge masks, crop coordinates, stitch/overlap checks and immutable per-tile products. Hold the event image and flood target fixed when replacing P0 with P1. | Tested full-tile pipeline and score-ready outputs for a small fixture. |
| 4 | Reuse completed source development evidence. Resolve learning-rate boundary diagnostics, choose final hyperparameters and epoch budgets on source data only, then fit six all-source final states (two learned pipelines × three seeds). Calibrate the physical comparator on source data only. | Six recoverable model states, one frozen physical rule and provenance. |
| 5 | Run all eligible external tiles and assessable local cases for P0 and P1. Record inability to obtain P1 as coverage, not invented predictions. Stream and verify inactive chunks to Azure as disk approaches 80 GiB free; maintain 50 GiB free reserve. | Complete census/coverage ledger, per-tile probabilities and verified recovery manifest. |
| 6 | Score flood IoU, permanent-water confusions, false/missed flood area, paired policy differences and method × policy interaction. Give event/linked-episode-balanced results primary weight; show area-weighted totals separately. Trace large errors to timing, imagery, processing, reference choice or labels. | Tidy tables, maps, event cases, uncertainty and sensitivity to label/timing support. |
| 7 | Interpret when the extra model or a newer reference improves, worsens or cannot cover a case; calculate actual acquisition/preparation/compute burden. Update the living one-pager and provide Brian an evidence memo, leaving article/dissertation wording to him. | Supervisor-ready results and limitations, reproducible run manifest. |

## Unattended execution and monitoring

Before the long run, add full-state atomic training checkpoints, verified
tile/window inference resume and a detached queue for one MPS plus up to two CPU
workers. Demonstrate worker kill/restart, sleep/wake, network interruption,
Azure upload/readback, disk-pressure pause and restoration using bounded fixtures.
Keep two checkpoint generations and never delete unverified remote data.

The Azure email action group and two disabled query alerts exist in
`rg-limburg-eo`. The local telemetry sender is
`scripts/224_emit_limburg_monitor_event.py`. Integrate it with the new runner so
`limburg-main-v1` emits running, planned-pause, failed and completed events.
Verify cloud ingestion, alert query results and **actual email receipt** before
enabling the heartbeat/failure rules. A test-notification API call is unavailable
on this Azure for Students subscription. A temporary real-rule email test
(`limb-run-email-test`) fired on 10 November and Brian confirmed email receipt;
the test rule was then removed. The production rules remain disabled until
the actual runner publishes its state and its recovery behavior is tested.
A sleeping Mac cannot send telemetry;
planned pause is a separate state. FileVault login after reboot may still require
Brian. The source-only fitting and harmonized imagery acquisition have begun;
the production email alerts remain disabled at Brian's request until the
long-run monitoring window. A detached continuation controller now waits for
all six hash-verified source fits, then runs the complete U-Net and Copernicus
external mapping censuses sequentially. Its status is recorded in
`results/limburg_chapter_sized_v1/mapping_queue_status.json`.

## Evidence checks

- Pin code, raw-file hashes, processing policy, model weights, random seeds and
  per-event membership. Record source-only decisions before external scoring.
- Compare source and target distributions, coverage and label semantics before
  making performance claims. Keep the full released-cohort accounting visible.
- Report new-event results separately from source-overlapping footprints. Treat
  related activations as dependent and July 2021 local cases as interpretation,
  not an extra pristine validation set.
- Keep P0/P1 results on matched pixels/events for the direct contrast; also report
  how often P1 could actually be obtained. Distinguish a policy effect from a
  pure reference-age effect.
- Report physical-event uncertainty and undefined flood IoU when appropriate.
  Do not imply a statistical confidence interval from a few chosen scenarios.

## Immediate next work

The triplet download and independent audit are complete: 913 verified triplets;
two candidate products were unavailable in Earth Engine. The source-calibrated
physical mapping census is complete (3,127 reference-tile evaluations).
Finish the six source fits and automatic learned mapping; retain telemetry/email
activation for Brian's requested later monitoring window.
The pinned external package and P1 inventory are documented in the
[steps 2–3 audit](reviews/limburg-steps2-3-acquisition-grid-2026-11-10.md).
Acquisition and implementation can overlap where files and compute do not contend.
A positive result is not a
prerequisite for completing the chapter: the empirical answer includes null,
mixed and coverage-limited findings.

## Automatic continuation and recovery

`scripts/240_continue_chapter_mapping.py` waits for all source model/manifest
hashes to verify, then runs `scripts/237_run_chapter_external.py` for U-Net and
Copernicus. Each method covers 1,301 delivered P0 tiles plus 913 harmonized
P0/P1 pairs: 2,214 jobs and 3,127 reference-tile evaluations per method, each
with three seeds. The controller retries failed mapping workers up to three
times. It resumes completed tiles from receipts and verified Azure archive
membership, and rejects receipts from a different final checkpoint.

`scripts/238_archive_chapter_predictions.py` uploads completed prediction groups
and their provenance receipts, downloads each bundle again, verifies its SHA256
and membership, and only then deletes the local predictions. The workers offload
at 100-job intervals or below 80 GiB free; a disk guard and archive workspace
check preserve the 50-GiB reserve. Upload failures retain local data.

Sleep suspends these local processes; they continue on wake. After a terminated
controller or reboot/login, restart the source queue if needed and then run
`python scripts/240_continue_chapter_mapping.py`; the queue lock prevents two
continuation controllers from owning the same queue. This does not configure
automatic restart before login. Local July 2021 receiving cases still need their
separate assessability/coverage check; this external mapping controller does not
claim their completion. Accuracy scoring remains Step 6.
