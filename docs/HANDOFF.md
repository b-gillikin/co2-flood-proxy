# Limburg handoff — 11 November 2026

## Active scope

Brian accepted the [chapter-sized mapping study](limburg-chapter-sized-study-2026-11-10.md).
The [current-study pointer](../config/limburg_current_study.json) selects it.
RQ: How do satellite AI and conventional methods compare in mapping new flood
events, and how does the choice of pre-flood reference affect their performance?
Compare frozen Copernicus-FM paired-SAR encoder/trained head, same-input U-Net,
and one source-calibrated physical rule. No target fitting or new model branch.
Brian writes dissertation prose and sends all emails.

## Current validated interpretation — 11 November

The [validity resolution and consolidation](limburg-study-consolidation-2026-11-11.md)
supersedes unrestricted headline interpretation below. Full original outputs remain
preserved. Of 913 paired external tiles, 447 match post-image orbit/pass/mode/
polarization/look and 466 do not; all 167 local records match. Geometry-compatible
Copernicus versus U-Net is +.008 IoU [−.023,.037]. Its P1−P0 is −.087
[−.224,.001], and −.022 [−.063,.008] with the existing listed <=24h timing
restriction. These post-result restricted cohorts differ; do not infer a causal
geometry/timing explanation from attenuation alone. Eight/seven/six blocks remain
in full/geometry/geometry+timing estimates. The fixed target is released event-
flood designation, not independent newly inundated area since P1. Water-union
scores are diagnostic. No broad AI advantage or robust universal newer-reference
harm follows. Exact numbers/provenance are in
[the compact receipt](reviews/limburg-validity-consolidation-2026-11-11.json).
No further model/extraction run is queued. Brian writes all manuscript text.

## Next research direction under development

Brian asked to pursue another part of the parked November 10 programme. The
[local adaptation and annotation-allocation proposal](limburg-local-adaptation-direction-2026-11-11.md)
recommends one bounded comparison of which local labels improve maps in separate
target areas. An [initial local-case inventory](reviews/limburg-local-adaptation-evidence-inventory-2026-11-11.json)
is recorded. The [12 November spatial-support census](reviews/limburg-local-adaptation-support-2026-11-12.json) identifies nearest-time receiving cases and extensive partially labelled support; use small annotation regions with larger image context rather than require fully labelled large chips. This is distinct from source-label reduction and reference replacement.
No adaptation protocol, new training queue or extra data download is launched;
the completed study and all validity qualifications remain intact.

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
- All external scoring, paired summaries and both map atlases complete. Twenty-one
  targeted scientific/recovery checks pass. All 74 frozen encoder/vendor assets
  checked match source feature-cache hashes. All workers have exited normally.

## Completed queues and artifacts

The external queue completed all 46 archives / 18,762 learned maps plus 3,127
physical maps. Tidy outputs are in
`results/limburg_chapter_sized_v1/evaluation/summary/`; local outputs in `local/`.
Local acquisition/mapping/scoring is complete for all 167 scene/grid records
and 14 acquisition cases. There are 35 updated references and 132 P1=P0 records.
The native 512px grids are preserved; no target adaptation was performed.

The [event-review memo](reviews/limburg-event-review-2026-11-11.md) and
`results/limburg_chapter_sized_v1/event_review/` contain the full 913-tile
explanation census, per-class transitions, reference dates, nine event-driver
maps, water/flood diagnostic charts and checked official chronology sources.
All original model/data/label choices and primary scores remain unchanged.
The explanatory metrics and case selections are explicitly post-result work.

Main readout: newer references reduce flood-class agreement, often by moving
correct flood detections into permanent-water predictions. Broader water
recognition can be preserved. Copernicus paired episode-balanced flood IoU
falls .396→.274 while water/land IoU rises .519→.541. There is no clear overall
Copernicus advantage over U-Net. Source-context records independently establish
Babahoyo flooding before its catalogue-selected pre-event reference. Low radar
return is a proxy, not independent per-pixel water truth. Colombia and some
German cases show important background-rejection losses, so one mechanism does
not explain every event. March Italy improves principally through precision.

## Evaluation and next review

[Scoring conventions](../config/limburg_chapter_evaluation_v1.json) were recorded
before external scores. Primary contrasts use identical support and fixed labels.
Aggregate confusion counts before activation IoU; average training seeds; weight
conservative episode blocks equally. Two Iberian activations share one dependence
block, without asserting one meteorological storm. Report all activations,
training-seed variation, 9,999 block-bootstrap draws, leave-one-block-out,
source-mask/validity/boundary sensitivities and timing/source-footprint strata.
Eight blocks limit precision. Labels and timing qualify claims as map agreement.

The event/seed tables, atlases, local cases and one-pager have been reviewed
and updated. Remaining useful consolidation is the actual resource-cost account
and supervisor discussion of the information-quality interpretation. Do not turn a weak result into a new
model search. The earlier discharge/TTM/AlphaEarth work is historical/supporting.

## Recovery, disk and cleanup

Scoring restores at most two bounded archives, verifies full SHA256/membership,
retains compact class maps and score receipts, then removes temporary restored
TARs. Original probabilities remain verified in Azure. Maintain 50 GiB free;
no data in other chapters is an offload/cleanup target. Reuse completed archive
scores and local map receipts on restart. Sleep suspends and wake resumes local
processes; reboot/FileVault may require Brian's login and controller restart.
Email production alerts remain disabled until Brian requests the later window.

The scoring audit is [Step 6](reviews/limburg-step6-scoring-2026-11-11.md).
Completed-worker style cleanup was performed after the workers exited; original
execution versions are preserved in Git and their recorded hashes. No research
data were deleted. Temporary PDF-render files created for the event review were
removed after visual inspection; original government PDFs remain preserved.
