# Limburg analogue chapter alignment audit

**Date:** 2026-10-13. Internal review of live code, literature and planning
documents; no dissertation prose was written.

**Subsequent implementation, 2026-10-13:** Steps 1--2 have since been executed
in scripts 68 and 69. The remaining-work discussion below describes the audit
state before that implementation; the current handoff records completed R1
and AlphaEarth joins and the pending R2/R3 comparisons.

## Result

The chapter now has one active empirical spine: retrieve prior high-water
events using conventional signatures, raw discharge, frozen TTM-R2 and a
bounded AlphaEarth catchment increment; then assess whether the matches are
hydrologically useful and sufficiently supported by station and measurement
evidence. The four-arm RAG and previous CO2, case-crossover and pressure
branches remain dated history, not parallel chapter requirements.

## Corrections made

| Area | Mismatch found | Correction |
| --- | --- | --- |
| Analogue code | Top-five donors often included multiple gauges from the same regional storm: 322 of 534 query lists had repeated donor-storm IDs. | Select at most one event per prior storm and require the donor's full 72-hour response to be complete by the query cutoff. Retain the established 20-event minimum rather than imposing a new 20-storm floor. |
| Baseline report | The earlier 0.658 versus 0.642 MAE comparison belonged to the multi-gauge-donor selection. | Rerun the baseline. On 534 queries the revised top-five and expanding-median peak-ratio MAEs are 0.6423 and 0.6424: effectively tied. Preserve the old numbers only as dated diagnostics. |
| Measurement evidence | The baseline carried provider and review concern flags but did not show their effect. | Add a paired sensitivity excluding flagged queries and donors. It retains 497 queries; analogue MAE is 0.5555 versus 0.5816 for the main donor set on those same queries. The flags do not automatically invalidate a known onset. |
| Current documents | The chapter handoff and feasibility note still contained the old baseline interpretation or RAG next steps. | Update the active design, handoff, inventory and historical-note status labels. |
| Dissertation assembly | The architecture, synthesis matrix and recovery command still described or ran the retired case-crossover design. | Update planning references and point the recovery command to the current analogue baseline. The manuscript chapter placeholder itself remains Brian's writing. |
| Weekly digest brief | Its Limburg section still described the CO2/lag/distance design and a failed data gate. | Replace that section with the current analogue question and status. The file is a prompt template; an already scheduled job is not updated merely by editing it. |
| GitHub quality workflow | It ran the full data-dependent test suite on a clean runner, though almost all data and results are intentionally untracked. | Remove the push-triggered workflow that could not reproduce the local run and had generated repeated failure notifications; retain local checks. |

## Literature fit

The active literature bridge covers flood-event process heterogeneity,
hydrograph similarity, streamflow foundation-model uncertainty, annual
geospatial catchment descriptors and cross-border FEWS context. The earlier
foundation-model review still contains RAG-specific rationale; its header now
marks that portion historical. The full bibliography and source notes retain
older work for provenance, while the active bridge identifies sources that
support the present question. No extra model or data requirement follows from
this audit.

## Work still necessary to answer the question

The current code implements R0, but not the raw 512-hour R1 control, frozen
TTM-R2 R2 representation, or prior-year AlphaEarth R3 event join and test.
The current event library is Dutch; held German records still need a common
event conversion before the learned-representation result can be called
cross-border. A hydrological review of selected matches and paired,
storm-aware uncertainty also remain to be done. These are the existing core
analysis tasks, not new branches or gates.

The p99 event labels and scaling use the full historical rating eras and are
retrospective. A successful analogue result would therefore establish
historical retrieval value under this archive definition, not as-issued
forecast skill, warning lead time or improved decisions. The baseline's small
MAE difference is not evidence that analogue retrieval already wins.

## Verification

The chapter test suite passes locally in the `chapter1-co2` environment. The
changed Python code passes Ruff lint and formatting. The manuscript recovery
command's `--quick` path passes its representation-contract tests. The
repository-wide Ruff format check still identifies formatting in the
unchanged `tools/disaster_recovery.py`; that recovery utility was left outside
this scientific-scope correction.
