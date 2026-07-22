# Chapter Readiness Plan

Status date: 2026-07-22

Preferred data freeze: 2026-09-08

Single contingency freeze: 2026-10-06

Status vocabulary: `done`, `in progress`, `waiting on data`, `ready after freeze`,
`secondary`, `blocked`

This is the canonical record for moving the Kerkrade CO2 analysis from a
working research pipeline to a dissertation-ready chapter. The earlier
`docs/august-readiness.md` is retained as a historical planning snapshot but is
superseded by this document.

## Research Question and Claim Boundaries

Neutral research question:

> After atmospheric-pressure effects are separated, do low-cost CO2
> observations at the Kerkrade post-mining site contain reproducible information
> about directly measured antecedent hydrological state?

The final chapter may take one of three evidence-led forms:

1. **Supported site-level signal**: the direct groundwater/mine-water analysis
   passes the locked inference, block-replication, and placebo criteria.
2. **Site-specific or data-limited signal**: direct-state evidence is useful but
   proxy, transfer, or replication evidence is weak or coverage-limited.
3. **Null/boundary result**: pressure separation is reproducible, but the frozen
   record does not establish an antecedent hydrological signal.

Cross-site transfer is a secondary analysis. It may strengthen the chapter but
cannot block completion. The current 10-day precipitation result remains `NOT
SUPPORTED` unless the frozen rerun changes it under the unchanged decision rule.
No causal groundwater or mine-water language is permitted until the direct-state
analysis passes its locked criteria.

## Can Do Now

### Final-analysis machinery: July 13-24

- [x] `done` Make skipped rolling evaluation invalidate stale rolling
  outputs.
- [x] `done` Record `ok`, `non_converged`, `failed`, and
  `insufficient_data` model statuses; a warning-only non-converged fit is not
  `ok`.
- [x] `done` Add per-detector scored indicators and compute agreement on
  common scored coverage.
- [x] `done` Exclude local `.python_packages` from the Linux Function App
  deployment package.
- [x] `done` Add `scripts/12_distributed_lag.py` to the documented frozen
  run order and make the tracked Python tree pass Ruff.
- [x] `done` Add a fixture-driven offline integration check for scripts
  05-12.
- [x] `done` Generate `results/run_manifest.json` with run ID, data
  cutoff, git commit, environment versions, commands, input hashes/coverage, and
  output hashes.

### Stable chapter writing: July 13-August 15

- [ ] `in progress` Draft the introduction around the neutral research question.
- [ ] `in progress` Finalize site and predecessor context, distinguishing prior
  2021 evidence from the current analysis period.
- [ ] `in progress` Finalize source provenance, UTC normalization, gap handling,
  and coverage rules.
- [ ] `in progress` Draft pressure decomposition and the Eryilmaz procedural
  replication, including the random-CV limitation.
- [ ] `in progress` Draft detector specifications and the time-aware evaluation
  protocol.
- [ ] `in progress` Draft uncertainty and claim-boundary language.
- [ ] `in progress` Add results-section placeholders and caption drafts without
  treating provisional numbers as final.
- [x] `done` Preserve the distributed-lag null result as an explicit boundary
  result.

### Weekly monitoring only

Run one refresh per week while data accumulate:

1. Sync IoT and KNMI source caches.
2. Rebuild normalized data and coverage reports.
3. Record the latest timestamp, observed-hour share, longest contiguous block,
   post-restoration block length, and usable 30-day/7-day windows.
4. Run fast QC, unit tests, and the offline integration check.
5. Append one row to the weekly log below.

Do not rerun or reinterpret the primary scientific analyses during weekly
monitoring.

## Incoming Data

| Source | Status | Readiness gate | First action on receipt |
| --- | --- | --- | --- |
| Post-restoration Kerkrade IoT | `waiting on data` | At least 60 days from 2026-07-09 with at least 90% hourly CO2 coverage | Sync raw blobs, rebuild hourly data, and update the gap report |
| KNMI station 06380 | `in progress` | At least 90% coverage across the post-restoration IoT block | Forward Azure collection reached its three-hour publication edge on 2026-07-22; sync slim blobs and rebuild hourly CSV/Parquet |
| Groundwater/mine-water | `waiting on data` | At least 60 paired daily observations across at least two blocks of 15 or more days | Preserve source files, write provenance, normalize without long-gap interpolation |
| Discharge/weather context | `in progress` | Covers the frozen IoT period and event catalogue | Refresh cached sources and rebuild labels/QC |
| Transfer sites | `secondary` | Shared-feature coverage sufficient for an honest dry run | Refresh only after core Kerkrade analysis is ready |

### Groundwater/mine-water source selection

Select the primary state series before modelling, using this locked hierarchy:

1. shaft or mine-water level directly connected to the Kerkrade site;
2. the nearest physically relevant groundwater series;
3. within a tier, the series with the greatest IoT overlap.

Record provider, units, datum, spatial relationship, measurement meaning,
quality flags, sensor or operational changes, duplicates, gaps, and discontinuities.
Other eligible series are sensitivity analyses.

## Weekly Coverage Log

Append rows; do not rewrite earlier entries. `Usable windows` means official
30-day training plus 7-day evaluation windows meeting the configured coverage
threshold.

| Refresh date | IoT latest UTC | CO2 observed share | Longest block hours | Post-restoration block days | KNMI 06380 overlap | Groundwater paired days | Usable windows | Notes |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 2026-07-12 | 2026-04-13 02:00 | 36.2% of the current full grid | 2495 | 0 locally synced | Pending refresh | 0 | 11 defined as usable on the current grid | Baseline before weekly post-restoration syncs |
| 2026-07-21 | 2026-07-21T20:00:00+00:00 | 31.7% | 2495 | 12.1 | 0.0% | 0 | 11 | Full refresh and provisional pipeline rerun; forward KNMI collection restored after this coverage calculation |
<!-- weekly-log-rows -->

## Current Implementation Checkpoint

The 2026-07-21 current-data rehearsal is an engineering check, not the chapter
freeze. Ruff, format checking, all 46 unit/integration tests, and the deployment
shell syntax check pass. `results/run_manifest.json` records run
`20260721T200000Z-0480f3f`, the 2026-07-21 data cutoff, six hashed inputs, 75
hashed outputs, runtime versions, and `git_dirty: true` so this rehearsal cannot
be mistaken for an immutable snapshot.

The live Azure configuration was reconciled on 2026-07-22. The primary Function
App contains the minute-level IoT, hourly weather, hourly historical-weather,
and once-daily summary-email timers. The email timer runs at 21:05 UTC; no
storage-account Event Grid subscriptions remain for per-blob email. The KNMI
app runs forward every 15 minutes from the 2026-06-24 handoff, uses
`state/knmi_forward_state.json`, and stays 180 minutes behind the publication
edge. The 02:30 UTC run reached that edge with its next cursor at 2026-07-21
23:40 UTC after 3,958 successful downloads and zero failures. Live collection
is current under the publication-lag rule; the subsequent local slim-blob sync
remains part of the next data refresh.

The convergence gate materially changes the provisional model readout. Across
11 usable official rolling windows, Isolation Forest has 1,848 scored hours;
SARIMAX and Kalman are `non_converged` in all windows and have zero valid scored
hours. The in-sample ensemble has 758 hours of common three-detector coverage.
Synthetic-injection output ranks Isolation Forest only; the two non-converged
detectors remain visible but unranked. The distributed-lag rerun remains `NOT
SUPPORTED` under the unchanged five-part decision rule.

The remaining work is data- and manuscript-gated: weekly IoT/KNMI refreshes,
groundwater/mine-water receipt and normalization, the freeze-gate decision, the
locked direct-state analysis, two clean-snapshot reproducibility runs, full
results/discussion/conclusion prose, publication formatting, and final Word
tracked-edit and page-render review.

## Data-Freeze Gate

Attempt the final freeze on 2026-09-08 when all conditions are true:

- the post-2026-07-09 IoT block contains at least 60 days with at least 90% CO2
  coverage;
- KNMI station 06380 covers at least 90% of that block;
- groundwater/mine-water data are normalized and documented;
- at least 60 paired daily observations exist across at least two blocks of 15
  or more days;
- all reliability changes and validation checks pass.

If a groundwater or coverage gate fails, extend once to 2026-10-06. If the gate
still fails, freeze the available record and complete a data-limited/null
boundary chapter without direct mechanism confirmation. After the freeze, new
observations belong to a later sensitivity update and do not change the main
chapter snapshot.

## Locked Direct-State Analysis

Primary daily frame:

- response: daily mean pressure-separated CO2 residual;
- exposure: standardized primary groundwater/mine-water level on the same UTC
  day;
- daily inclusion rule: at least 18 observed IoT hours;
- controls: KNMI temperature, relative humidity, and pressure;
- structure: block fixed effects;
- inference: HAC standard errors with 14-day maximum lag plus a 28-day
  moving-block bootstrap.

Primary model:

`daily residual ~ standardized water level + KNMI temperature + KNMI relative humidity + KNMI pressure + block fixed effects`

The site-level signal is supported only if all criteria pass:

1. primary water-level coefficient has `p < 0.05`;
2. the 95% moving-block bootstrap interval excludes zero;
3. the coefficient has the same sign in at least two usable blocks;
4. the future-water placebo is null at `|t| < 2`.

Secondary analyses use water-level lags of 1, 3, 7, and 14 days, water-level
change, and alternative wells. Report false-discovery-rate-adjusted p-values and
label these analyses as sensitivity/exploratory rather than confirmatory.

## Frozen Run Order

Run every stage against one immutable input snapshot:

1. coverage and QC;
2. pressure decomposition;
3. Eryilmaz procedural replication;
4. exploratory signal characterization;
5. SARIMAX, Kalman, and Isolation Forest;
6. common-coverage ensemble agreement;
7. synthetic-injection validation;
8. rolling-origin out-of-sample evaluation;
9. direct groundwater/mine-water analysis;
10. precipitation/discharge distributed-lag test;
11. event-window analysis;
12. prespecified sensitivities;
13. transfer dry run only when shared-feature coverage is adequate;
14. run-manifest generation and artifact hash verification.

Do not combine tables, figures, or summaries from different snapshots.

## Claim Decision Table

| Frozen evidence | Final chapter framing |
| --- | --- |
| Direct state passes all primary criteria; result is stable by block | Supported site-level hydrological signal |
| Direct state is supported but proxy or transfer evidence is weak | Site-specific/direct-state signal with limited portability |
| Direction is plausible but coverage, block replication, or power is inadequate | Inconclusive because of coverage; provisional/data-limited chapter |
| Direct state is null or fails placebo/replication | Null/boundary result focused on pressure separation and false lag structure |

## Chapter Section Tracker

| Section | Status | Current evidence | Remaining blocker | Completion criterion |
| --- | --- | --- | --- | --- |
| Introduction and research question | `in progress` | Literature scaffold and neutral question | Claim wording still needs synchronization | Full prose uses the neutral question and permits all four decision-table outcomes |
| Site and predecessor context | `in progress` | Viefhues/Eryilmaz notes and source corpus | Separate prior-event evidence from current-period evidence | Site mechanism and inherited evidence are cited without treating them as current confirmation |
| Data and provenance | `in progress` | IoT, weather, discharge, KNMI, and RIVM source notes | Groundwater metadata and final coverage | Every reported source has provider, units, time basis, coverage, and QC |
| Pressure decomposition | `ready after freeze` | Reproducible baseline and current R2 | Frozen-data rerun | Specification, uncertainty, and final frozen result reported |
| Eryilmaz replication | `ready after freeze` | Procedural replication pipeline | Frozen-data rerun | Random-CV limitation and frozen AUROC results reported |
| Detector methods | `in progress` | Three detector scripts and provisional outputs | Convergence/coverage hardening | Specifications and failure states are explicit |
| Direct-state analysis | `waiting on data` | Locked method in this document | Groundwater/mine-water receipt and overlap | Primary criteria evaluated without post-hoc changes |
| Distributed-lag boundary result | `ready after freeze` | Current outcome `NOT SUPPORTED` | Frozen-data rerun | Unchanged decision rule and placebo result reported |
| Transfer | `secondary` | Two-site provisional dry run | Shared-feature coverage | Included only as appendix/secondary evidence and never blocks completion |
| Results | `waiting on data` | Outline and provisional artifacts | Frozen run | Every number and figure traces to one run manifest |
| Discussion and limitations | `waiting on data` | Claim boundaries recorded | Final claim selection | Addresses null and site-specific alternatives without causal overreach |
| Conclusion | `waiting on data` | Decision table | Final claim selection | Restates only evidence that passed the frozen analysis |

## Required Main-Text Artifacts

Figures:

1. study area and site/sensor schematic;
2. full data-coverage timeline with outages;
3. representative synchronized data window;
4. pressure decomposition and residual;
5. Eryilmaz replication ROC;
6. direct groundwater/mine-water result;
7. rolling-origin detector performance or anomaly timeline;
8. primary lag/placebo result;
9. common-coverage ensemble agreement;
10. transfer result only if interpretable.

Tables:

1. source provenance and frozen coverage;
2. detector and direct-state model specifications;
3. contiguous-block and evaluation-window counts;
4. primary coefficients, uncertainty, and placebo tests;
5. detector scored coverage and out-of-sample summaries;
6. prespecified sensitivity results and final claim decision.

Exploratory random-forest/PCA figures, order-search tables, extended lag scans,
and provisional transfer diagnostics belong in an appendix.

## Final Reproducibility Checklist

- [ ] `ready after freeze` Ruff check and format check pass.
- [ ] `ready after freeze` Unit and offline integration tests pass under the
  Python 3.11 chapter environment.
- [ ] `ready after freeze` Skipped rolling runs cannot leave valid-looking stale
  outputs.
- [ ] `ready after freeze` Every model reports convergence and scored coverage.
- [ ] `ready after freeze` Two frozen-snapshot runs produce matching scientific
  artifact hashes and summaries.
- [ ] `ready after freeze` `results/run_manifest.json` identifies every reported
  artifact.
- [ ] `ready after freeze` Exploratory, confirmatory, sensitivity, and transfer
  outputs are separated in the manuscript.
- [ ] `ready after freeze` All figures and tables are publication-formatted and
  captioned with sources and time basis.
- [ ] `ready after freeze` No stale `short window`, pre-restoration, or positive
  10-day-signal language remains.
- [ ] `ready after freeze` The final Word manuscript has reconciled tracked
  edits and passes page-by-page render review.

## Definition of Chapter Ready

The chapter is ready when one immutable snapshot reproduces every reported
number; the direct-state evidence determines the final claim; every model has
explicit convergence and coverage status; methods, results, discussion,
limitations, and conclusion are full prose; and no result depends on an
unrecorded local artifact or a different data snapshot.
