# Limburg chapter re-audit — 27 October 2026

Internal research/code review for Brian, not dissertation prose. This pass
rechecked the current RQ/method/evidence map, completed runs, new downstream
calculations, actual-case interpretation and job recovery. It builds on the
[earlier full chapter/model/literature audit](limburg-completed-chapter-audit-2026-10-27.md);
it does not claim to have reread every paper or rerun every encoder again.

## Assessment

The retrospective analogue question remains coherent and supported by the
declared design. No new defect requiring another embedding extraction or data
collection was found. The important new findings concern workflow recovery,
the meaning of an inherited quality label, donor-trace packaging and clear
denominators. These are specific corrections, not reasons to stop the chapter
or introduce a new research direction.

## Findings and actions

### 1. The queue had stopped at a resource check; completed calculations were sound

The rainfall replay and its review completed, but script 138 stopped before
the final reference/combination phase when free disk space fell to 57.9 GiB,
below its 60 GiB working reserve. This was not a scientific exclusion, model
failure or incomplete rainfall result. Disk space subsequently recovered to
about 75 GiB without any chapter data being deleted in this audit.

**Action:** added script 140 to verify completed rainfall input/output hashes,
resume only the unfinished phase and preserve the original failure in
`resume_history`. It uses the existing controller lock. The final phase reuses
the verified independent results and computes only the new rainfall references.
Neither encoder extraction nor completed scoring was restarted. Recovery tests
reject incomplete or altered completed results. The reserve is a resource
precaution, not a gate on research conclusions.

### 2. Dutch `provider_status` is a July 2021 gauge note, not a verdict on every event

Tracing script 46's `build_review` shows that it reads
`source_qa.july_2021_discharge_status` once per gauge and writes that same string
to every episode at that gauge. Script 64 carries it into the event library.
The Dutch labels span events from 2010 to 2025. Thus a January 2015 Geul event
labelled `exclude_out_of_range` was not thereby excluded by its provider, and
`pending_range_check` does not mean the May 2024 Voer event awaits a reply.
German status originates in different rating-period logic.

The scientific filtering uses event-level measurement flags and exact-response
admissibility, not that inherited Dutch string. Inspection did not show those
flags being overridden by the misleading label. The existing uncertainty review
already explains the distinction, but the recent case notes were insufficiently
explicit and could mislead a reader.

**Action:** corrected the [actual-case review](limburg-actual-analogue-review-2026-10-27.md)
with the traced scope and corrected both examples. Completed numerical artifacts
and their manifests remain frozen. When preparing a publication-facing browser,
label Dutch status as historical July 2021 gauge context; do not silently relabel
it as a present event-specific quality assessment. This requires presentation
work, not rescoring or excluding unrelated events.

### 3. Common-route donor identities exist in cache but are not directly packaged with the final case table

Script 137 saves matched-route scores, paired differences and intervals; its
actual retrieval donor IDs and distances remain in the isolated content-addressed
cache. Those receipts are enough to trace the calculations locally, but a final
score table alone is not a portable donor-review bundle.

**Action:** the new read-only audit indexes and verifies **1,116 retrieval cache
entries / 3,348 files**, including their donor tables and prediction receipts.
The index is `results/chapter_reaudit_2026_10_27/route-cache-hashes.json`.
This is explicitly an audit-time preservation record, not invented contemporaneous
proof. Preserve these files until the small reproducibility bundle is assembled.
Copying/indexing these derived artifacts requires no new retrieval, training,
imagery download or raw provider-file redistribution.

### 4. The corrected rainfall denominator is larger, but not every EO analysis gains 66 cases

There are 851 common Q-eligible events; actual conventional predictors are
complete for 836 versus 770 under the old 512-hour rainfall requirement.
The corrected review has **646 distinct scored rainfall-matched queries**, versus
**603** in the original review's rainfall cohorts: 43 additional query identities
across the union, not 66 new cases for every model.

For the fixed main/pooled/all-river conventional arm in the all-ten intersection:

| Readout | Old eligible / scored | New eligible / scored |
|---|---:|---:|
| Monthly snapshot | 472 / 471 | 475 / 474 |
| Twelve completed months | 352 / 346 | 355 / 349 |
| Four completed weeks | 102 / 101 | 103 / 102 |

Coverage, complete sequences and prior-donor availability still determine which
of the feature-complete events enter each comparison. Report the actual cohort;
do not call 2,246,580 assessment rows independent events or imply that broadening
the denominator establishes improved model performance. The 512-hour **discharge**
requirement remains the shared TTM/history comparison population; this rainfall
correction does not imply it is an unused requirement for every representation.

### 5. Uncertainty implementation is consistent; inference remains exploratory

The independent-stage interval tables have 12,672 common-route rows and
1,752,816 generic-reference rows. Their point estimates are finite; interval
bounds, draw counts and cluster-count contracts passed. There are **10,584**
generic-reference rows with undefined bounds because fewer than two resampling
clusters are available. They are retained as undefined, not replaced by zero
width or silently omitted. No inventoried storm crosses a calendar-year boundary
in the held event inventory.

These are many dependent configurations and conditional bootstrap intervals,
not millions of independent tests or repeated confirmations. Query-storm/year
resampling does not propagate all shared-donor, rating or pretraining uncertainty.
The main remaining presentation task is a compact hierarchy by hydrological
question with support and both resampling sensitivities. A favourable cell or
post-hoc illustration must not become an advertised universal winner.

### 6. Current navigation was lagging behind the executed design

The active-design page and evidence index still led with earlier execution
states. Dated material was valuable history but easy to read as today's plan.

**Action:** added a current reading map at the top of both, preserving their
historical sections. The one-pager and handoff track live completion separately.
No old RAG, CO2, case-crossover or forecast programme was reactivated.

### 7. Held supporting data should not become blanket requirements

The one-pager grouped rainfall/weather together as required data, although the
current EO comparison does not use the held weather variables as predictors.
Current warning thresholds belong to the separate progression analysis. Q-only,
rainfall-matched and model-available EO cohorts have deliberately different input
requirements.

**Action:** clarified the one-pager's data roles. Held weather and thresholds are
supporting products, not prerequisites for the core analogue comparison. Nothing
was deleted or excluded, and no new acquisition requirement was created.

## Verification

- Replayed script 134 into a separate output directory: all five original
  comparison/review pairs and selected model contracts checked; **149 unique
  files, zero hash failures**. Its embedded historical test-count text is not
  the result of this new test run.
- Script 141 checked new rainfall scores, all six corrected review manifests,
  independent/final results, source dependencies and cached donor traces: **3,520
  unique files checked in that pass, zero issues**. These counts overlap with
  other audit passes and must not be summed as distinct files.
- Streamed **2,246,580 rainfall assessment rows** and **279,040 common-route
  rows**: no nonfinite/negative checked errors or invalid donor-count contracts.
- Checked **1,765,488 independent-stage interval rows** and **1,903,296 final
  generic-reference interval rows**: no contract violations. The final table
  includes the independent-stage rows, so these counts are not distinct tests.
- Full test suite: **331 passed in 40.26 s**, using the existing PROJ database.
  Three added recovery checks cover successful verification, incomplete results
  and changed completed output. Ruff and diff whitespace checks passed.
- Reproducible evidence: `results/chapter_reaudit_2026_10_27/`; current test log:
  `logs/eo-followup-2026-10-27/reaudit-tests.log`.

The final rainfall-reference merge completed during this audit. All **18**
archive-reference batches and `results-memo.md` are published under
`results/eo_followup_2026_10_27/`. The final manifest and its recorded outputs
passed the fresh hash check; the controller now records `completed`. No numerical
jobs remain in this follow-up. Scientific interpretation is not inferred merely
from successful completion. A compact committed verification receipt accompanies
this report under `reaudit-2026-10-27/verification.json`.

## Scientific scope remains unchanged

The chapter tests useful historical precedents and failure modes across this
Dutch/German archive. It does not establish routed upstream/downstream causality,
national policy effects, as-issued forecasting skill, verified inundation or a
calibrated operator abstention rule. Statistical p99 discharge and the following
72-hour response remain distinct from flood stage and whole-flood duration.

The held methods/literature spine supports that retrospective task, not a claim
that a particular embedding dimension measures wetness or that pretraining caused
a gain. A same-support raw-EO control is needed only for that stronger attribution;
it is not a new mandatory condition for reporting pipeline utility. Missing-sequence
sensitivities and additional model capabilities remain optional. No new data
requests, models, interviews or blanket scientific stops are recommended here.
