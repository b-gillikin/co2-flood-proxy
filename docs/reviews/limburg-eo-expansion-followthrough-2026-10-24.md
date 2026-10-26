# Supplemental archive: staging, audit and model comparisons

Brian authorized the four follow-through steps on October 24. The remote archive
is complete: 66,913 committed files, 107,154,546,597 bytes including archive
metadata, zero failed transfers. The acquisition VM is deallocated. No VM restart
or new cloud inference is needed.

## Running sequence

1. Script 126 stages every planned TIFF/receipt pair from private `expansion-v1`,
   reusing matching local files. Both downloaded receipts and data are checked
   against immutable remote metadata and SHA-256; conflicting local files are
   preserved and reported. Two transfer workers, 5 GB batches, a 150 decimal GB
   local archive/weights allowance and 60 GiB free-disk reserve protect the laptop.
   These storage settings do not remove observations from the acquisition ledger.
2. Script 127 audits every staged raster: receipt/job identity, hashes, CRS, grid,
   band counts, catalogue dates, observed pixel dates and joint spectral validity.
   The resumable JSONL records zero-valid tiles explicitly. Its identity binds
   the jobs and audit code. Tile validity is not claimed to equal catchment or
   complete-sequence coverage; the existing exact-area aggregator measures those.
3. Script 131 waits for this staging/audit **and the existing corrected extraction,
   aggregation, scoring and review to finish**, then runs the compatible expanded
   sensitivities below. It does not modify or interrupt the current queue.
4. Each alternative gets an engineering check, full context-census extraction,
   exact observed-area aggregation, a separately selected ten-arm merge, the
   established retrospective scoring, and actual-analogue review. No results are
   available merely because the queue was launched.

Controller entry points:

- `scripts/128_run_eo_expansion_followthrough.py`: stage then audit.
- `scripts/131_run_eo_expansion_comparisons.py`: wait, extract, aggregate, score,
  review. Progress is in the corresponding `logs/eo-expansion-*` directories.

## Which acquired data can be used immediately?

| Supplemental data | Maintained model use | Comparison |
| --- | --- | --- |
| S2 harmonized TOA 10/20 m plus QA60 | SatMAE multispectral checkpoint | Separate TOA alternative to held SR input; same publisher normalization and same-UTC-day spectral mask, adding observed same-day QA60 clear support. |
| Same S2 products | Copernicus-FM S2 route | Same separately labelled input-domain sensitivity. Existing asset documentation identifies the TOA-pretrained/SR transfer issue. |
| S1 ascending orbit 15 | CROMA SAR | Ascending VV/VH route, separate orbit; never pooled with orbit 88 or 161. |
| S1 ascending orbit 161 | CROMA SAR | Separate orbit sensitivity with the same fixed publisher transform. |
| Other S1 descending orbits | Retained, audited inventory | No substitution into an ascending-only maintained route without an explicit input-contract review. |
| Landsat 5/7/8/9 surface reflectance | Retained, audited inventory | Not HLS: do not relabel as harmonized Prithvi input. Six spectral bands do not automatically satisfy a ten-band S2 adapter. Future use requires a justified sensor-specific adapter. |
| S2 TOA in other models | Retained, audited inventory | No automatic rerun where maintained input contracts are SR or need additional sensor-specific handling. |

This is not four new models or tuning: two existing encoders are reused in four
explicit source-domain/orbit alternatives. The original seven other model routes
and all event definitions stay fixed. The selected ten-arm comparison replaces
only the relevant arm for each alternative; unchanged arms reuse their verified
corrected outputs. Never compare differing-population headline averages as if
paired: use matched eligible queries, donor policies and storm/year intervals.
Report context availability, country/river support and misleading analogue matches
alongside performance. The existing scoring retains these distinctions.

## Input safeguards

The new input views alias a native product to an existing encoder route only in
their job-index interface. Original paths, receipt identities, assets, dates,
reflectance units and orbit provenance remain intact. No pixels are copied or
changed by those views. New wrapper/source hashes enter extraction manifests.

S2 QA60's masked/unavailable periods remain missing, never clear. Clouds/cirrus,
different QA/reflectance acquisition days, and different 10/20 m spectral days
are excluded from this clear-support alternative. QA60 availability changes can
reduce support; this is reported, not filled with another day. This changes both
reflectance domain and QA support, so it is an **input-route sensitivity**, not a
clean causal estimate of atmospheric correction alone. Same-day checks establish
UTC-day coherence, not exact scene identity. Source publication latency remains
unresolved for prospective use; the evaluation remains retrospective.

CROMA's additional ascending orbits are independently processed. A changed viewing
geometry is a sensitivity, not new measured hydrology. No learned fusion,
synthetic observation, satellite-based flood label or operational claim is added.

## Checks and current limits

Real held files from all 13 product routes passed initial checksum/date/grid checks;
some checked optical tiles had zero valid pixels. The full archive audit is pending
local staging. Focused tests verify valid windows, corrupt data rejection,
out-of-window observed dates, missing pixels, and QA missing/cloud/day rules.
The active ten-model extraction source files and environments remain unchanged.

No new scores, recovered-event counts or model improvement are claimed yet.

## Write-up checklist for Brian

Keep these counts distinct:

- **Ten model representations** remain in each selected comparison.
- **Three distinct models** receive supplemental extraction: SatMAE,
  Copernicus-FM and CROMA.
- **Four supplemental configurations** are evaluated: one TOA/QA60 route for
  SatMAE, one for Copernicus-FM, and two separate ascending-orbit routes for CROMA.
- In each configuration-specific comparison, **one model arm is replaced and
  nine are reused**. Across this extension, seven distinct models receive no new
  extraction; their verified corrected representations remain in the comparisons.

Report the original corrected archive analysis separately from these supplemental
input-route sensitivities. A ten-model comparison does not mean ten models were
re-extracted using the supplemental archive. The acquisition ledger covers all
13 products; acquisition, pixel validity, model compatibility, complete temporal
support and inclusion in scoring are different counts.

For each reported result, identify checkpoint, input product/reflectance level or
radar orbit, masking/date policy, extraction run, observed catchment/sequence
coverage, eligible query and donor populations, and which representations were
reused. Distinguish pooled, cross-river and NL–DE results. Explain that TOA/QA60
changes reflectance domain and observed support together; do not attribute a
performance difference solely to TOA versus SR. Additional radar orbits remain
separate sensitivities rather than a fused radar representation.

Label completed results, queued work and incompatible/unimplemented routes
accurately. Retain the current archive as a valid analysis of its stated inputs;
these supplemental comparisons are not evidence that all earlier results were
wrong. Brian writes the manuscript prose; this checklist is an internal methods
aid, not dissertation text.

## Disk headroom

Brian authorized cleanup and, if needed, verified Azure offloading of inactive
data on October 24. See [Disk Cleanup authorization](disk-cleanup-authorization-2026-10-24.md).
Check free space before supplemental work and during long phases; preserve active
and queued dependencies, local manifests and verified results. This authorization
does not itself remove data or change any model population.

## Execution update — October 26

The corrected main scoring and automated review completed at 12:15 UTC. The
supplemental controller initially failed before extraction because it had been
launched in Azure CLI Python, which lacks NumPy required by the local analysis
imports. No main result was changed. The failure receipt is retained in
`logs/eo-expansion-comparisons/environment-failure-2026-10-26.json`. The controller
was restarted with the existing `.venvs-eo/terramind/bin/python`; SatMAE TOA/QA60
engineering checks began. No packages, model inputs or frozen numerical sources
were changed. Future controller launches must use that existing analysis runtime.

## Parallel scheduling — October 26

Brian requested the previous two-CPU-plus-GPU pattern. Script 132 now supersedes
script 131 as the active controller; script 131's fixed variant/view definitions
are reused. Only the old controller PID 84488 was terminated. SatMAE PID 84558
was adopted unchanged, preserving its extraction and frozen numerical code.

- MPS lane: existing SatMAE, then CROMA orbit 15, then CROMA orbit 161.
- CPU extraction lane: Copernicus-FM, after its successful real engineering check.
- CPU postprocessing lane: completed configurations enter one serialized
  aggregation/merge/scoring/review queue. This permits overlap with extraction
  without concurrent retrieval-cache writers or multiple large scoring jobs.

The postprocessing lane remains idle until an extraction completes. Scheduling
changes no inputs, events, encoders, normalization or scores. New phases wait if
free space falls below 60 GiB; resolve that through the separately authorized
Limburg-only Disk Cleanup rather than changing scientific populations. Logs and
per-lane progress remain in `logs/eo-expansion-comparisons`. Source identities for
the already-running extractor are unchanged. Seven focused tests pass, covering
route assignment and the existing supplemental input safeguards; lint passes.

## Orbit-specific engineering-window repair — October 26

Both supplemental optical extractions completed with zero errors. Copernicus-FM
aggregation/merge completed and its scorer started. CROMA orbit 15's default
August/September 2018 engineering fixture had no overlapping acquired imagery,
so it produced no embeddings and correctly returned a nonzero status. This was
not a missing delivery or failed neural inference. The complete orbit-15 archive
was already staged/audited.

Script 132 now selects an engineering-only single snapshot from held windows
with audited observed pixels, without reading event responses. It requires a
finite, nonempty successful output before full extraction. The engineering
single-context output is separately located and cannot certify the full census.
The orbit-15 check passed. Neither archive dates nor census eligibility changed.
Completed optical extraction is reused on resume. The in-progress Copernicus-FM
scorer PID 84158 was preserved and adopted; the controller waits for its verified
completed manifest before any other scoring job. Eight focused tests pass,
including the unavailable-fixed-month/available-observed-window case.
