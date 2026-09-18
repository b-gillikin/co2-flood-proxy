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

## Progress (2026-09-18)

| phase | state |
| --- | --- |
| 1 Code alignment | **done** (commit 2221ea0) |
| 2.1 Radar rainfall | coverage check **done**: RADKLIM cannot observe the Voer or half the Gulp. Operational RADOLAN RW 2010–2025 download running (`scripts/37_fetch_radar.py`). |
| 2.2 Catchments | **done, provisional**: GLO-30 delineation, seven area checks within ±4.4%. Pour points are public-portal coordinates. |
| 2.3 Catchment rainfall | script ready (`scripts/41_radar_catchment_rainfall.py`); runs when the download completes |
| 2.4 Weather | **done** (`scripts/40_build_event_study_weather.py`) |
| 3 Discharge ingest | waits on Waterschap semantics |
| 5 Estimator validation | **done**: the Python estimator reproduces R to within 1e-13. Coverage of the primary estimand is 93–97.5%. Results in `results/estimator_validation/`. |

Details and numbers are in `decisions.md` (2026-09-18, "Implement the draft
0.9 workstreams").

## Phase 0 — Author decisions (before code that depends on them)

| # | decision | recommendation and evidence (2026-09-18) | blocks |
| --- | --- | --- | --- |
| D1 | Estimation toolchain | **Python**, with the R script kept as a standing cross-check. The Python estimator reproduces the R reference to within 1e-13 on 8 simulated datasets, which meets the protocol's condition. `gnm`'s `eliminate=` fit diverged on the saturating-stress dataset, so the R reference uses a fixed-effects GLM. | lock |
| D2 | Rainfall product | **Operational RADOLAN RW throughout**, by the protocol's own rule. RADKLIM-RW is masked outside a band around Germany: the Voer is never observed and 45% of the Gulp is not. RADOLAN observed every catchment in the July 2015 probe. Confirm. | Phase 2.3 |
| D3 | Cohort classification | Brommelen lies upstream of the Millen split, so Geleenbeek and Vloedgraaf are one watercourse under protocol §3. Choose the representative gauge on QA grounds. Classify the Worm with its Aachen urban drainage in mind: the provider area at Herzogenrath is below the topographic area in EStreams' record. | Phase 3 |
| D4 | Season boundaries | May–October warm, November–April cold, as drafted. Confirm, or change before any event is built. | Phase 4 |
| D5 | Provisional coordinates | Waterschap's public-portal coordinates were used as provisional pour points. Replace them when Waterschap's numerical coordinates arrive, and re-run `39_delineate_catchments.py`. | none now |
| D6 | Low flows outside the rating domain (new) | Treat an hour as inadmissible only where being outside the domain makes its above-or-below-p99 status uncertain. A value below the domain minimum is still certainly below p99, and censoring those onsets would remove summer onsets from low base flow. Needs an edit to protocol §3. | Phase 3 |
| D7 | Median-lag interval reporting (new) | Report a median-lag interval only when at least 95% of bootstrap draws are estimable in both seasons; otherwise report it as not estimable. | lock |

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
