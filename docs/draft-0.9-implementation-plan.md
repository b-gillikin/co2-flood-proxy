# Draft 0.9 implementation plan

Status: 2026-09-18. This plan builds the case-crossover protocol
(`chapter-scope-and-preregistration.md`, draft 0.9) from its current state to
protocol lock and then to results. No outcome may be computed before lock.
Everything up to lock uses only timestamps, counts, geometry, exposure data and
synthetic data.

## Critical path

```text
Waterschap semantics (external) ─► discharge ingest ─► blinded feasibility ─► lock ─► analysis
                                        ▲                     ▲              ▲
code alignment ──────────────────────────┘                     │              │
radar rainfall + catchments ───────────────────────────────────┘              │
estimator validation on synthetic data ────────────────────────────────────────┘
```

Only one step waits on anyone else: Waterschap's answers on timezone, zero
semantics and coordinates, followed up on 2026-09-17. Everything else can start
now, in parallel.

## Phase 0 — Author decisions (before code that depends on them)

| # | decision | recommendation | blocks |
| --- | --- | --- | --- |
| D1 | Estimation toolchain | **R reference implementations** (`dlnm`, `gnm`, `mixmeta`), called from one script, with package versions pinned. Hand-building distributed-lag cross-bases in Python is exactly the kind of reimplementation where a silent error changes a reported number. The rest of the pipeline stays Python. Alternative: `statsmodels` `ConditionalPoisson` plus a hand-built cross-basis, validated against R on synthetic data (§7 of the protocol requires that validation either way). | Phase 5 |
| D2 | Rainfall product | RADKLIM-RW if its released period covers the joint window, otherwise operational RADOLAN RW throughout. Decide after the coverage check in Phase 2.1. | Phase 2 |
| D3 | Cohort classification | Record natural/managed status and hydrological independence for each candidate. Decide Geleenbeek (Brommelen) against Vloedgraaf (Nieuwstadt) once coordinates show whether Brommelen is upstream of the Millen split. | Phase 3 |
| D4 | Season boundaries | May–October warm, November–April cold, as drafted. Confirm, or change before any event is built. | Phase 4 |
| D5 | Provisional coordinates | Waterschap sent Google Maps short links. Expanding them yields provider-sourced coordinates that could start catchment delineation before the numerical coordinates arrive, then be replaced. Allow, or wait. | Phase 2.2 |

Each decision is recorded, dated, in `decisions.md`.

## Phase 1 — Code alignment (start now, no data needed)

1. **Gate script.** Update `scripts/31_event_study_gates.py` and
   `tests/test_event_study_gates.py` to draft 0.9:
   - cohort of at least 5 natural, hydrologically independent watercourses,
     with the sign-test flag at 6;
   - at least 40 storms, and 15 per season, with the fallback recorded rather
     than failing the gate;
   - weather contract changed to relative humidity and surface pressure;
   - catchment contract requires valid cross-border polygons;
   - remove the donor-availability and pair-complete-event checks;
   - rating-era columns in the gauge contract.
2. **Event helpers.** In `src/event_study.py`:
   - keep `episode_table`, `episode_onsets` and `cluster_regional_storms`;
   - replace the censoring logic with the onset-only rule;
   - add rating-era p99 thresholds, `at_risk_hours()` and stratum construction;
   - remove `quiet_control_times` and the pressure-residual functions, which
     stay in Git history.

   Tests should protect only what could change a reported number:
   - at-risk hours are the exact complement of the merge rule;
   - onset-only censoring;
   - era-specific thresholds;
   - lag alignment, so that lag 1 is the hour before onset.
3. **Design simulations.** Review `scripts/36_design_recovery.py` (added
   2026-09-17) against draft 0.9. Reuse what fits the blinded feasibility audit
   and retire the rest.

## Phase 2 — Open-data acquisition (start now, no institution)

1. **Radar rainfall.**
   - Confirm RADKLIM-RW's released period and grid extent, and inspect coverage
     quality over South Limburg. The nearest radars are Essen and
     Neuheilenbach. Then make decision D2.
   - Download hourly composites for the joint period.
   - Crop to a Limburg-plus-headwaters bounding box immediately, to keep
     storage small.
   - Keep missing codes as missing and write a checksum manifest.
2. **Catchments.** Delineate each gauge's upstream catchment from a
   cross-border DEM: MERIT Hydro flow directions, or Copernicus GLO-30 with a
   delineation tool. The Geul, Gulp and Voer rise in Belgium and the Worm
   drains Aachen. Check each delineated area against any catchment area stated
   in Waterschap's rating-curve documents. Write
   `data/interim/event_study_catchments.gpkg`.
3. **Catchment rainfall.** Area-average the hourly radar grid over each
   polygon. Write `data/interim/radolan_catchment_hourly.csv`.
4. **Weather.** From the audited ERA5-Land archive, derive hourly relative
   humidity with one documented formula and the six-hour pressure change.
   Assign the cell nearest each catchment centroid and record shared cells.
   Write the weather table and the weather-sources table.

## Phase 3 — Discharge ingest (waits on Waterschap semantics)

1. Write the hourly ingest:
   - the four-quarter-hour rule;
   - the verified timezone conversion;
   - zero handling as confirmed;
   - documented failure intervals from the July 2021 status report set to
     missing.
2. Transcribe the rating-curve validity periods from the 14 PDFs into a small
   versioned table of rating eras. Record the transcription in `decisions.md`.
3. Build `data/interim/event_study_gauges.csv` with the cohort classification
   (D3), coordinates, rating eras and July 2021 status.
4. **Conditional:** if stage records arrive, add the onset-timing recovery rule
   from protocol §3.

## Phase 4 — Blinded feasibility audit and floor freeze

Using timestamps, counts and geometry only:

- watercourses passing coverage;
- episodes per watercourse;
- regional storms, in total and per season;
- censored onsets;
- at-risk hours per stratum;
- whether the seasonal fallback applies.

Then freeze the floors, the cohort and the D1 and D2 choices in `decisions.md`.
If a core gate fails, stop and record a dated rescoping decision.

## Phase 5 — Estimator validation (start now, synthetic data only)

1. Simulate hourly series with a known rainfall lag-response, a known seasonal
   difference in median association lag, a null, and storm-clustered
   dependence.
2. Show that:
   - the chosen implementation recovers the known lag-response and seasonal
     difference;
   - the null yields intervals covering zero;
   - the year-month block bootstrap has close to nominal coverage.
3. If D1 chooses Python, reproduce the R reference estimates on the same
   synthetic data to numerical tolerance.

This is the synthetic check required by protocol §12. It is the only
estimator test suite the chapter needs.

## Phase 6 — Lock

Record in protocol §13:

- the floor and cohort entry;
- the D1 and D2 choices;
- the distance-module decision;
- the gate-audit path and hash;
- input hashes;
- the commit;
- the lock timestamp.

**Distance-module cutoff.** The LANUK export must have arrived, passed the
gates and flagged reconstructed values by this point, or the module is out.

## Phase 7 — Analysis

Fit, in this order:

1. the primary model;
2. S1–S4;
3. the exposure-response shape (§9.1);
4. the Fase comparison, if thresholds arrived (§9.2);
5. temporal stability (§9.3);
6. July 2021 (§9.4);
7. the two-stage pooling sensitivity (§9.6).

Then:

- run the 999-replicate year-month block bootstrap;
- write the tidy tables and five figures listed in protocol §12;
- regenerate every manuscript number from those tables.

## Phase 8 — Writing and literature

1. Add the six design references (Maclure 1991; Janes, Sheppard and Lumley
   2005; Gasparrini, Armstrong and Kenward 2010; Gasparrini and Armstrong 2013;
   Armstrong, Gasparrini and Tobias 2014; Cameron, Gelbach and Miller 2008) to
   `chapter-references.bib`, `literature-source-notes.md` and the evidence
   matrix. All six were verified against Crossref on 2026-09-18.
2. Add the RADKLIM or RADOLAN product citation and the DEM citation.
3. Verify the post-2021 Dutch regional-warning reviews before citing them.
4. Draft the chapter to `manuscript-outline.md`. Draft the policy discussion as
   feasibility claims only.

## Outreach still needed for this chapter

When René Mols replies, ask in the same thread for anything still open:

- timezone/DST and zero semantics;
- numerical coordinates;
- stage records with datum history;
- Fase thresholds.

Stage records and Fase thresholds serve conditional analyses only. The chapter
runs without them.

## Risks

| risk | consequence | mitigation already in the protocol |
| --- | --- | --- |
| A second candidate watercourse fails QC | Core falls to 5; S3 becomes descriptive | Five-watercourse core floor |
| Two candidates fail | Core gate fails | Stop and record a dated rescoping decision |
| A season has fewer than 15 storms | Seasonal contrast becomes descriptive | Fixed fallback to the pooled estimand |
| Radar coverage poor over South Limburg | Principal exposure degraded | Coverage checked before D2; never splice products |
| Waterschap does not answer | Discharge ingest cannot start | Only this path waits on anyone; everything else proceeds |
| R toolchain friction | Delay | Python route permitted if validated against R |

## Dissertation-level follow-through (outside this repository)

These arose in the same review and need author decisions:

1. **Peja fallback.** The Peja memo's "replace the case" branch still does not
   say what replaces it. The proposal is the systematic review as the fourth
   chapter. Decide before the Peja requests close on 2026-09-25.
2. **GPT's Tagoloan–Peja swap exploration.**
   `dissertation-manuscript/docs/tagoloan-peja-swap-feasibility-plan.md` is
   uncommitted. It proposes a different resolution for the same chapters, so
   reconcile it with the Peja memo before either is acted on.
3. **Push.** Commits in `chapter1-co2`, `chapter2-bukidnon`, `chapter3-peja`,
   `chapter4-innovation` and `dissertation-manuscript` are local only.
