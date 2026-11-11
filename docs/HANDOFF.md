# Limburg handoff — 11 November 2026

## Active scope

Brian accepted the [chapter-sized mapping study](limburg-chapter-sized-study-2026-11-10.md).
The [current-study pointer](../config/limburg_current_study.json) selects it.
RQ: How do satellite AI and conventional methods compare in mapping new flood
events, and how does the choice of pre-flood reference affect their performance?
Compare frozen Copernicus-FM paired-SAR encoder/trained head, same-input U-Net,
and one source-calibrated physical rule. No target fitting or new model branch.
Brian writes dissertation prose and sends all emails.

## Completed

- Six final source fits (two learned methods × three seeds), hash verified.
- All 1,301 delivered external tiles and 913 harmonized P0/P1/post triplets
  acquired/audited. Paired effects use one processing chain; delivered P0 is
  separate. Two candidate assets unavailable in the chosen Earth Engine chain.
- Full external mapping: each learned method 2,214 jobs / 3,127 reference-tile
  evaluations × three seeds. All 18,762 learned maps are in 46 readback-verified
  Azure archives (83.1 GiB). Physical mapping completed 3,127 maps.
- Independent support/overlap census complete. Cross-UTM overlap is handled by
  prediction-blind native pixel-center ownership, retaining valid-support holes.
- Conventional scoring complete. Sixteen targeted checks pass. All 74 frozen
  encoder/vendor assets checked match the source feature-cache hashes.

## Running and automatic continuation

`245_continue_chapter_evaluation.py` runs two bounded archive restoration/scoring
workers, then `244` paired event summaries and `246` a systematic map atlas.
State: `results/limburg_chapter_sized_v1/evaluation/queue_status.json`.
Progress: `evaluation/archive_scoring_status.json`; logs in
`results/limburg_chapter_sized_v1/engineering/{archive_scoring,paired_summary,map_review}.log`.
Do not interpret partial-archive results as a completed comparison.

`247_prepare_chapter_local.py` is acquiring small same-chain local triplets over
all 167 held event-scene/grid records. P0 is the held same-orbit/pass baseline;
P1 is latest newer same-platform/orbit/pass covering the relevant footprint,
before a conservative 13 July 2021 cutoff. Otherwise P1=P0. This local policy is
not the external GEOID delivered P0 policy. The first actual radiometry check
matches held dB-to-linear values (median ratio 1.0 in both polarizations).
`249_continue_chapter_local.py` waits for checked acquisition, then runs `248`
for all three pipelines. One MPS worker; no local target adaptation. July 2021
remains one dependent flood; mapped non-flood is not independently verified dry.

## Evaluation and next review

[Scoring conventions](../config/limburg_chapter_evaluation_v1.json) were recorded
before external scores. Primary contrasts use identical support and fixed labels.
Aggregate confusion counts before activation IoU; average training seeds; weight
conservative episode blocks equally. Two Iberian activations share one dependence
block, without asserting one meteorological storm. Report all activations,
training-seed variation, 9,999 block-bootstrap draws, leave-one-block-out,
source-mask/validity/boundary sensitivities and timing/source-footprint strata.
Eight blocks limit precision. Labels and timing qualify claims as map agreement.

After completion: read the event/seed tables and atlas, inspect actual error
locations against imagery/timing, compare local cases, record actual resource
costs, and update the one-pager/findings. Do not turn a weak result into a new
model search. The earlier discharge/TTM/AlphaEarth work is historical/supporting.

## Recovery, disk and cleanup

Scoring restores at most two bounded archives, verifies full SHA256/membership,
retains compact class maps and score receipts, then removes temporary restored
TARs. Original probabilities remain verified in Azure. Maintain 50 GiB free;
no data in other chapters is an offload/cleanup target. Reuse completed archive
scores and local map receipts on restart. Sleep suspends and wake resumes local
processes; reboot/FileVault may require Brian's login and controller restart.
Email production alerts remain disabled until Brian requests the later window.

The audit is [Step 6 scoring](reviews/limburg-step6-scoring-2026-11-11.md).
Do not format/edit active worker files during execution; final style-only cleanup
can follow completion, preserving recorded runner/source versions in Git.
