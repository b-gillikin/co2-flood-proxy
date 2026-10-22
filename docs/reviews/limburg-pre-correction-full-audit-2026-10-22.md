# Pre-correction pipeline audit — 22 October 2026

**Later same-day documentation review:** the
[ten-model read-through](limburg-ten-model-documentation-review-2026-10-22.md)
found CROMA's omitted input `/255` and AnySat's prose-versus-training date
inconsistency. CROMA also needs re-extraction; the correction list becomes eight
models, reusing only Prithvi and repaired OlmoEarth on current evidence. The
seven-model storage measurements below remain historical measurements, not an
eight-model estimate. The earlier source-consistency/reuse conclusion for CROMA
is superseded; the original audit text and evidence are preserved below.

Internal engineering/scientific audit, not dissertation prose. Scope: the held
imagery and ten encoder routes, extraction/resume, catchment aggregation, event
comparison, actual-case review and the queued seven-model correction.

The pending correction controller was terminated while still waiting, before
any new extraction began. Its progress file records `held_for_requested_audit`.
Current held-archive scoring and its queued case review continue unchanged.
There is no scientific reason to discard the other models' current analyses
because the new correction is held. Findings below distinguish encoding changes
from storage/provenance work and interpretation limits.

## Findings requiring attention before restarting extraction

| Finding | Evidence and consequence | Action / stage affected |
| --- | --- | --- |
| **SatMAE preprocessing does not match the pinned reference.** | Our adapter applies `(DN - mean) / std`. The publisher's Sentinel pipeline uses mean ±2 SD, clips/quantizes to uint8, then `ToTensor` scales by 255. Capturing the actual adapter input gives 0 at the channel mean; the reference gives 127/255 = 0.498039. A three-SD engineering fixture spans −3 to +3 in our adapter versus 0–1 in the reference. Finite/repeatable vectors did not detect this. | Correct this inside the versioned rerun adapter, with independent publisher-conformance checks. SatMAE needs re-extraction; it is already one of the seven scheduled models. Do not interpret the original arm as correctly preprocessed SatMAE performance. Leave the old numerical source intact while its comparison is running. |
| **The current output layout is too large to duplicate locally.** | The seven selected run directories allocate 285.659 GiB; about 70 GiB is free. Galileo alone allocates 165.6 GiB. The vectors' float32 payload is only 2.830 GiB; masks, acquisition-day arrays, repeated receipts, missing-patch records and filesystem allocation account for the remainder. This remainder is not all disposable. The loop also pauses below a hard-coded 60 GiB reserve. | Use compact, indexed/shared metadata and lossless mask storage, and/or verified retirement/archive of superseded intermediates. Preserve all missingness evidence, masks needed for aggregation, source hashes and rebuildability. Verify round trips and equivalent aggregation before the full run. Merely lowering the 60 GiB reserve will not make another 285 GiB fit. This is storage engineering, not a smaller event census or a new data requirement. |
| **Presto repeats the patch's representative month for every pixel.** | The model API accepts a month per pixel/timestep. The adapter repeats the patch-median date's month. A captured two-pixel month-boundary fixture supplies August/August when actual acquisition dates imply August/September. Of 426 held S2 weekly windows, 81 cross a calendar-month boundary; that is potential exposure, not a count of erroneous pixels or events. | Use the held per-pixel acquisition dates for Presto's month tensor during the correction. Monthly bins already have a single calendar month. This is a removable temporal approximation; its effect on retrieval is not yet known. Presto is already in the seven-model rerun. No new imagery is needed. |
| **Galileo's normalization JSON is not directly fingerprinted.** | The selected run binds Python source and checkpoint assets, including the checkpoint config, but not `code/galileo/config/normalization.json`, which its forward adapter reads. The code repository revision is pinned, but a local change to this JSON is not checked by the run's direct source hashes. No change to its current values was found or inferred. | Bind this file explicitly in the corrected run identity, before extraction starts. Also freeze the input contract and actual runtime settings. This is a provenance correction, not evidence that an existing embedding value is wrong. |
| **The correction queue's checks are too narrow for the changes being bundled.** | Script 122 performs a two-frame smoke test, then launches a census. That verifies execution/repeatability, but not all publisher input transforms, one-/four-/twelve-frame readouts, boundary-month dates or storage round trips. The maintained suite passed despite the SatMAE mismatch. | Exercise the corrected adapters against publisher transforms and small real held inputs for the three declared readouts, including sparse masks and boundary/padding cases. Recheck resumability and corrected aggregation. These are small engineering checks to prevent another expensive run, not empirical significance or novelty gates. |

The SatMAE reference is the held revision
[`0b210ace…/util/datasets.py`](https://github.com/sustainlab-group/SatMAE/blob/0b210aceb37a14bbbd897110db5b104b3271d818/util/datasets.py#L345-L492),
especially `SentinelNormalize` and `SentinelIndividualImageDataset.build_transform`.
The independent diagnostic executes that class from the pinned file and captures
the current adapter input without loading learned weights. The resize/crop part
of a downstream dataset's evaluation transform is distinct from our declared
native-grid patch transfer design; it is not automatically another required
spatial transformation.

The Presto reference is the held
[`nasaharvest/presto` revision](https://github.com/nasaharvest/presto/tree/11e207a668a34336ced1d8e492a1bd5849b96c4a),
its input helper and encoder month tensor. The diagnostic establishes the
approximation, not a model-performance effect or the frequency of mixed-month
pixels in real observations.

## Additional reproducibility improvements

- The aggregation receipt binds patch receipts, selected extraction identities,
  geometry and output hashes, but does not directly record the aggregator/helper
  source hashes. Add those to future aggregation receipts. The pixel-area cache
  key currently binds geometry/grid but not the area algorithm version; bind that
  version or verify/rebuild the weights when changing the algorithm. No numerical
  area error was reproduced. These changes require no encoder rerun.
- Preserve the fixed run selection. Old interrupted CPU Galileo still has a
  stale `running` flag despite no corresponding process. It is unselected and
  must not be chosen by folder date or a status flag alone. Cleanup must use
  actual process ownership and the authoritative selection, retain historical
  receipts and account for OlmoEarth hard links.
- Extraction/source files and runtimes should be fixed before starting the
  seven workers. Per-model identities already detect many edits; a queue-wide
  preflight receipt makes it easier to avoid discovering changed dependencies
  after several models finish. There should be exactly two CPU owners and one
  MPS owner, without hidden device fallback or duplicate model jobs.

## What checked out

- **284 maintained tests pass** in 41.11 seconds. This is regression evidence,
  not proof that every scientific input convention is correct.
- All **28 publisher assets across ten models** were rehashed against their
  recorded publisher size/hash contract. No weight mismatch was found.
- The selected ten aggregates had already passed the fixed-selection merge:
  completed extraction status, zero recorded errors, correct recovery runs,
  output hashes, context ledger, shared catchment geometry and mask policy.
  CROMA, Prithvi and token-repaired OlmoEarth need no S2-day correction.
- Source inspection found the other declared normalization/band routes
  consistent with their documented pinned adaptations: harmonized S2 SR DN;
  six-band HLS physical reflectance scaled once for Prithvi; S1 dB routes;
  wavelength/band order for DOFA/Copernicus; native band selection for TerraMind;
  published scaling and explicit absent-modality masks for Galileo/OlmoEarth;
  and the official Presto input helper. This was source/contract inspection;
  it is not a new full inference or numerical-equivalence test for every model.
- Monthly/four-week windows end before their event cutoff. No current partial
  window, future response or event outcome ranks donors. Existing chronology,
  distinct-storm, river/country policy, equal actual donor-count and quality
  checks remain in place. Main cohorts and matched subsets are distinct.
- Pixel-area accounting uses the full catchment denominator and exact polygon
  intersections; padding is masked, duplicate support rejected and missing
  frames explicit. Contextual patch vectors can still include outside-catchment
  information; aggregation does not turn them into pure pixel measurements.

## Interpretation limits that do not demand new extraction

S2 same-day masking means the **same UTC day**, not necessarily one exact scene.
Patch/frame representative dates approximate composites for encoders accepting
one date per patch; original date ranges remain in evidence. Presto can avoid
that approximation for its per-pixel month input.

Presto and other models' weekly transfer is not a claim that they were pretrained
on weekly Limburg flood histories. Single-frame models' sequence summaries are
order-invariant frame means, not temporal attention. Native spatial footprints
and missingness behavior differ. These define the transfer comparison and its
controls; changing them opportunistically after outcomes is not an audit fix.

Current full-era p99 scaling, pretrained exposure and completed composites
support retrospective analogue evaluation, not as-issued forecast skill or
historical flood/warning labels. Countries differ in river, record length and
measurement history. Provisional German high flows and source concerns remain
in case records and quality sensitivity. No new agency request or label scheme
is needed for this correction.

The comparison and browser are scientific/research aids; they do not establish
operator benefit. Original-vs-corrected differences require matched queries
**and donor pools** for clean attribution. Changed coverage is a separate result.

## Storage and restart sequence

1. Keep the current scoring/review running and the correction held.
2. Bundle SatMAE normalization, Presto pixel months and normalization-JSON
   provenance into the versioned adapter.
3. Make storage fit through compact lossless outputs and verified cleanup of
   inactive intermediates. Do not delete imagery, weights, selected aggregates,
   KCA/provider deliveries or another chapter's data to make this run fit.
4. Verify publisher input conventions, readout/mask/date cases, resume and exact
   storage/aggregation equivalence on small held fixtures. Record frozen sources,
   checkpoints, inputs, settings and expected output locations.
5. Resume the authorized two-CPU/one-MPS correction. Preserve old and corrected
   results separately and reuse the three unaffected native-product models.

No full corrected extraction has started. The audit did not silently implement
the numerical/storage changes or delete data. It identifies a concrete set of
fixes to consolidate before restarting, rather than assuming the day-mask change
alone is sufficient or guaranteeing that no future issue could ever be found.

## Reproduction evidence

- `scripts/123_audit_encoder_input_contracts.py --model satmae` in the SatMAE runtime.
- The same script with `--model presto` in the validated Presto runtime.
- `logs/eo-pre-correction-audit/`: captured input diagnostics, publisher weight
  verification, vector payload and Galileo normalizer provenance.
- `logs/eo-selected-storage-audit-2026-10-22.txt`: actual allocated directory
  sizes, measured after the owning extraction jobs finished.
- `logs/eo-pre-correction-audit-tests-2026-10-22.log`: complete regression run.
- The [compact check receipt](limburg-pre-correction-audit-checks-2026-10-22.json)
  preserves the numerical evidence and source hashes in Git.
