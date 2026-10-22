# EO error, correction and execution ledger — 22 October 2026

Current consolidated index for the ten-model extraction/comparison work. Dated
audits remain evidence of what was known then; their earlier instructions to
wait, reuse CROMA or finish old scoring are superseded by the
[authorized retirement/restart](limburg-eo-retirement-and-restart-2026-10-22.md).
Implemented fixes are distinguished from completed full-data execution.

| Issue | Correction and evidence | Current disposition |
| --- | --- | --- |
| Mixed-acquisition-day Sentinel-2 bands | Same-UTC-day validity in `src/eo_coherent_inputs.py`; full 8,538 tile/window audit. [Audit fixes](limburg-eo-audit-fixes-2026-10-21.md). | Implemented; seven optical routes are being re-extracted. This establishes day agreement, not exact scene identity. |
| CROMA omitted `/255` | Publisher input capture demonstrated 0–255 instead of 0–1; corrected stretch/quantization/scaling in `src/eo_encoder_corrections.py`. [Documentation review](limburg-ten-model-documentation-review-2026-10-22.md). | Implemented and engineering-checked; CROMA joins the rerun, making eight replacements. Earlier reuse advice is superseded. |
| SatMAE used z-scores instead of publisher transform | Independent transform capture; corrected clipped eight-bit stretch followed by 0–1 scaling. [Pre-correction audit](limburg-pre-correction-full-audit-2026-10-22.md). | Implemented and engineering-checked; full replacement pending. |
| AnySat prose/demo date disagreement | Executable demo and dated loaders use one-based day-of-year; leap-day/year-boundary fixtures recorded. Same correction module. | Implemented; rationale and conflicting README retained. No material performance effect is claimed in advance. |
| Presto assigned one patch-median month to all pixels | Corrected actual acquisition month per pixel/timestep; absent slots masked, unknown observed dates rejected. | Implemented and engineering-checked; full replacement pending. |
| Galileo/OlmoEarth token validity and metadata support | Native-token observation policy applied before patch metadata calculation; readout and mask diagnostics documented in [readout review](limburg-eo-readout-diagnostics-2026-10-21.md) and restart record. | Repaired OlmoEarth is retained; Galileo's repaired token policy is included in its new coherent-S2 replacement. Do not select older interrupted runs. |
| Publisher assets/dependencies incompletely bound | Galileo normalization JSON and correction module now hashed; aggregation source and area-algorithm hashes recorded. | Implemented; protected Prithvi/repaired OlmoEarth hashes verified. No numerical area error was established. |
| Wrapper consumed `--run` as `--runtime-profile` abbreviation | `allow_abbrev=False`; 16 actual-command regression cases. | Fixed before any census writes from the failed launch; failure logs retained. Current controller launched successfully. |
| Finite/repeatable smoke checks missed preprocessing errors | Independent publisher input captures plus real 1/4/12-frame and sparse-mask checks, and storage round trips. | All eight replacements passed engineering checks. Previous restart suite: 307 tests passed; this ledger does not claim full census completion. |
| Repaired runs omitted from final selection | Explicit per-model selection, manifest/coverage/geometry validation and merge. | Corrected controller will create its new selection only after aggregation. Old selection is historical and contains retired references. |
| Stale/incomplete results accepted or left visible | Completion/status/source checks; isolated planning; staged scientific publication; explicit zero-score status, rollback and output manifests. [Second-audit fixes](limburg-eo-second-audit-fixes-2026-10-21.md). | Implemented. Cancelled old scoring published no completed ten-model scientific result. |
| Legacy ledger, absolute paths and partial/full aliases | Comparison-entry ledger checks; portable identities/resolvers; resolved output-path separation. | Implemented with regression checks; no unknown numerical source transition accepted. |
| Extraction fingerprints included downstream-only code | Small population builder and explicit reviewed metadata-only compatibility snapshots. | Implemented; numerical dependencies remain bound. |
| Repeated retrieval work slowed scoring | Content-bound retrieval cache and cold/cached equivalence profile on the eligible TTM/state cohort. | Implemented; old derivable scoring cache retired. No ten-model ETA inferred from the profile. |
| Slow Presto CPU execution | [Runtime investigation](limburg-presto-cpu-investigation-2026-10-18.md) and [handoff](limburg-presto-runtime-handoff-2026-10-18.md): separate validated Torch 2.9.1, four-thread, batch-128 profile. | Profile retained in corrected queue; not an unrecorded dependency upgrade. |
| Disk insufficient for duplicate patch archives | Explicit retirement script/receipt; stopped only owned old scoring/review; preserved original manifests, catchment summaries, raw inputs and protected runs. | 36 superseded full/partial/smoke directories retired; restart began with about 477 GiB free. This is a dated measurement, not current free space. |
| Historical README execution presented as current | README now points to corrected controller/map/output paths and retired-input status. | Fixed; historical audit and handoff entries remain dated. |

## Remaining execution and research limits

Eight corrected extractions, aggregation, ten-model verification/merge, scoring
and actual-analogue review remain the controller's sequence. Prithvi and repaired
OlmoEarth are the two reused routes. Read
`logs/eo-coherent-correction-v1/progress.json` for live status. Neither an
implemented fix nor an engineering smoke is a completed scientific comparison.

The [literature/runtime review](limburg-eo-model-literature-and-runtime-2026-10-22.md)
separates supported configurations from optional Presto mean-plus-spread and
Copernicus-FM metadata adaptations. Neither is an unresolved input defect or an
automatic further run. Different footprints, cadence transfer, frame-mean order
invariance, composite-date approximations, acquisition availability and possible
foundation-pretraining exposure remain interpretation limits. Their existence
does not stop the chapter or establish failure. No new data request, model arm,
scientific result or dissertation prose is created by this ledger.
