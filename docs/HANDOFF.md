# Session Handoff

Written 2026-08-11. Session state only; use the synthesis and protocol for
chapter claims.

Read in this order:

1. `chapter-synthesis.md` — canonical question, contribution, design and state.
2. `chapter-scope-and-preregistration.md` — draft 0.7 protocol.
3. `supervisor-decision-memo.md` — recorded approvals and open floors.
4. `student-next-actions.md` — current student tasks and sent requests.
5. `data-requests.md` — delivery contracts and blockers.
6. `analysis-inventory.md` — prospective, supporting and retired work.
7. `literature-source-notes.md`, `literature-evidence-matrix.csv` and
   `chapter-references.bib` — source corpus for the student-authored review.

## Current chapter

The chapter is now scoped as one direct matched event study:

1. Viefhues: one Kerkrade event and indoor CO2 response.
2. Eryilmaz: same-site public-weather explanation outside that event.
3. This chapter: recurrence before independently defined high water and spatial
   extent across the observed tributary network.

Transferability means the change in event-minus-quiet contrast with distance.
It does not mean prediction, gauge substitution, propagation, operational
radius or ungauged-basin performance.

Local event-minus-quiet contrasts establish recurrence. Spatial event
contrasts are aggregated to one median per ordered receiver-donor pair, then
one fixed line is fitted per signal:

`pair_median_contrast ~ 1 + log(1 + distance_km)`.

Pairs receive equal weight; complete storms are resampled for uncertainty;
each watercourse is omitted in turn as an influence check. The former crossed
watercourse/time-block validation and random-intercept model are retired.

Signal hierarchy is fixed: RADOLAN catchment rainfall and donor flow are the
principal hydrological signals; ERA5-Land temperature, humidity and pressure
are one compact Eryilmaz-derived atmospheric block; CO2 is conditional.

## Data and approvals

Approved: the contribution, spatial-extent meaning, natural Limburg tributary
population, ERA5-Land source/rule, July 2021 anchor and conditional Kerkrade
case.

Still open: the provisional 10-watercourse/10-year/20-episode/40-storm floor;
80% overall and 70% annual/receiver/distance coverage rules; and the new minimum
of 10 complete event/control contrasts per ordered pair. The student should
show the blind availability audit, freeze these values with the supervisor and
inform the supervisor that the prediction-style holdout has been retired.

The Waterschap, LANUK and Viefhues follow-up messages were sent; replies are
pending. The regional gate still **fails** because all six analysis-ready
network inputs are absent. Do not inspect prospective signal contrasts or
lower the gate.

The Viefhues K4 source is reproducible and has all 744 July 2021 hours. Device
identity/calibration, complete ABC lineage, a defensible hydrological pair,
independent onset bounds and later complete events remain unresolved. The CO2
case is therefore unavailable, but the regional chapter is not blocked by it.

## ERA5-Land acquisition

The ERA5-Land backfill is deployed and enabled in
`func-kerkrade-era5-backfill-bg` in `rg-kerkrade-prod`. It runs every five
minutes, permits one CDS request at a time and persists `_state.json` plus a
checksum manifest in `stkerkradeprod01bg` / `era5-land`. Closing the laptop does
not stop it.

The local process was stopped after completing September 2005. Sixty-two
validated local files were seeded. Azure adopted the already-running October
2005 request, validated and uploaded it at 13:26 UTC, bringing Blob Storage to
63 source files: the contiguous 2001-01--2005-10 sequence plus five later
benchmark months. The scheduled timer independently submitted November 2005
at 13:30 UTC. At handoff its request ID is
`d0f418be-2709-47fe-bef0-98982f6b095e`; there is no error or blocked state.

The app is `Running`, `ERA5_ENABLED=true`, HTTPS-only and registered with one
timer trigger. SCM basic publishing is closed. `deploy.sh` always redeploys it
paused, temporarily opens SCM only for the remote build and explicitly syncs
the trigger. The local fetch script remains a fallback and must not run while
the cloud timer is enabled.

ERA5-Land is the only regional weather source. The user stopped the retired
KNMI Azure Function App; its app and stored blobs were not deleted.

## Code-review result

The live analysis tree was reduced by more than 1,900 net lines. Removed:

- the later-era Eryilmaz re-fit and Visual Crossing join;
- rolling two-year Waterschap and RWS main-stem pipelines;
- DWD point-rain sensitivity;
- holdout/time-block helpers and their tests;
- the obsolete weather-source note and unused environment dependencies.

Eryilmaz remains predecessor evidence in the source corpus. Active later-IoT
ingestion remains only because it may support the conditional Kerkrade case.
LANUK acquisition/feasibility code remains until the pending source reply is
resolved. Azure collection code is operational infrastructure, not chapter
analysis.

The event helper now requires timestamps as well as rows to be exactly one hour
apart, preventing a false p99 crossing across an omitted timestamp. A focused
regression test protects that scientific rule.

## Agent work after deliveries

1. Inventory and hash native replies; resolve sampling, timezone, units,
   sentinels, rating curves, natural/managed status and July 2021 QA.
2. Fix the admissible cohort and write direct ingests after inspecting actual
   formats.
3. Finish/validate ERA5-Land, then build verified catchment polygons, centroid
   assignment and RADOLAN area averages.
4. Run the blinded threshold/coverage table and obtain the remaining supervisor
   decisions.
5. Rerun the strict gate and lock the protocol before outcomes if it passes.
6. Implement one direct pandas analysis producing tidy contrasts, pair medians,
   distance estimates, influence rows and four figures. Add only claim-
   protecting checks.
7. Add the Kerkrade section only if its separate evidence contract passes.

## Verification

Interpreter:
`/Users/briangillikin/miniforge3/envs/chapter1-co2/bin/python`

- literature crosswalk: 42 notes, 42 BibTeX keys, 96 matrix rows and 36 unique
  DOIs; all keys resolve;
- default scientific suite: **26 passed**;
- operational infrastructure suite: **5 passed**;
- Ruff lint and format: passed across **45 files**;
- ERA5 Azure execution: adopted and completed 2005-10; independent timer
  submitted 2005-11; 63 validated source blobs, no blocked/error state;
- regional gate report: expected **FAIL**, with all six contracted inputs
  absent;
- Viefhues real-file QC: 169,594 source rows, 2,829 hourly rows and 744/744 July
  hours.
