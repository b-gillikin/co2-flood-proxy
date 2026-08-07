# Chapter Writing Register

> **Superseded 2026-08-06.** This register tracks `chapter/chapter-draft.md`,
> which is machine-generated scaffolding rather than an author draft, and the
> four-branch claim machinery it describes is withdrawn. See
> `docs/chapter-direction.md`.

Status date: 2026-07-22

Canonical prose draft: `chapter/chapter-draft.md`

Canonical readiness record: `docs/chapter-readiness-plan.md`

This register separates prose that is stable before the data freeze from text that
must be completed from one immutable run. It is a writing handoff, not a second
analysis plan.

## Stable Now

| Section | Stable content now | Remaining editorial work |
| --- | --- | --- |
| Introduction | Motivation, neutral research question, contribution, non-causal scope | Final citation, bibliography-metadata, and house-style review |
| Study context | Regional post-mining setting; separate Viefhues and Eryilmaz periods and purposes | Confirm any site wording that depends on provider documentation |
| Data and provenance | UTC alignment, source-native preservation, gap policy, coverage rules, direct-series hierarchy | Insert frozen source coverage and groundwater metadata |
| Analytical design | Pressure decomposition, procedural replication, detector contract, rolling evaluation, direct-state inference, boundary and transfer roles | Synchronize exact frozen model specification table |
| Uncertainty | HAC, moving-block bootstrap, block replication, placebo, FDR, convergence, and scored coverage | Insert frozen estimates and diagnostics |
| Limitations | Single-site scope, missingness, unmeasured indoor processes, spatial representativeness, labels, observational design | Remove any limitation disproved by final metadata |

## Freeze-Dependent Fields

Every unresolved number or artifact is written as
`{{FROZEN:<machine-readable-key>}}`. These tokens are intentional: provisional
results must not be copied into the manuscript as final values. The frozen-run handoff
must resolve them from `results/run_manifest.json` and its hashed outputs.

| Result family | Required frozen evidence | Primary source |
| --- | --- | --- |
| Record and coverage | Cutoff, hours, shares, material blocks, post-restoration days, KNMI overlap | Coverage outputs and manifest |
| Pressure decomposition | Eligible hours, explained variance, residual diagnostics | Baseline outputs |
| Replication | Both AUROCs and fold uncertainty | Eryilmaz replication outputs |
| Detectors | Actual families, fit statuses, selected features, native and common scored hours | Model summaries and ensemble outputs |
| Validation | Synthetic recovery and rolling-origin summaries | Scripts 09 and 10 outputs |
| Direct state | Selected series and metadata; paired blocks; coefficient; HAC, bootstrap, sign, and placebo tests | Script 16 outputs |
| Boundary evidence | Frozen distributed-lag outcome and placebo | Script 12 outputs |
| Transfer | Run/omit status, shared coverage, bounded secondary summary | Script 11 outputs |

## Claim Selection

The working draft contains all four prespecified discussion branches, each identified
by a `CLAIM_BRANCH` marker. After the frozen run, retain exactly one:

1. `supported_site_level`
2. `site_specific`
3. `coverage_inconclusive`
4. `null_boundary`

The selected branch must match the machine-readable direct-state outcome. Proxy or
transfer evidence may narrow the branch wording but cannot promote the conclusion.

## Finalization Procedure

1. Freeze the eligible data and run the pipeline twice from clean code.
2. Confirm matching scientific hashes and summaries.
3. Resolve every `FROZEN` field from that run only.
4. Retain the one claim branch dictated by direct-state evidence and delete the other
   three.
5. Run `python scripts/17_check_chapter_draft.py --require-final`; a nonzero exit is a
   release blocker.
6. Reconcile tables, figure callouts, captions, citations, and cross-references.
7. Verify provisional bibliography metadata, including the final Eryilmaz venue,
   against the source corpus.
8. Convert to the Word manuscript, reconcile tracked edits, and complete page-by-page
   render review.

## Figure and Caption Writing State

Caption content can be finalized now for the data-coverage timeline, synchronized
window, pressure decomposition, detector timeline, direct-state coefficient plot,
distributed-lag/placebo plot, and common-coverage ensemble view. Each final caption
must state the time basis, analysis population, uncertainty representation, and
snapshot/run identifier. Geographic and sensor schematics still require confirmed
site metadata; transfer graphics remain secondary.
