# Session Handoff

Updated 2026-09-14. Session state only; use the synthesis and protocol for
chapter claims.

Read in this order:

1. `chapter-synthesis.md` — canonical question, contribution, design and state.
2. `chapter-scope-and-preregistration.md` — draft 0.7 protocol.
3. `supervisor-decision-memo.md` — the 2026-08 supervisor response and the rationale for the provisional floors (historical record).
4. `student-next-actions.md` — current student tasks and sent requests.
5. `data-requests.md` — delivery contracts and blockers.
6. `analysis-inventory.md` — prospective, supporting and retired work.
7. `literature-source-notes.md`, `literature-evidence-matrix.csv` and
   `chapter-references.bib` — source corpus for the student-authored review.
8. `dissertation-research-and-code-guidelines.md` — reusable standard for
   scoping, evidence, coding and review across the remaining chapters.

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
of 10 complete event/control contrasts per ordered pair. The author freezes
these values after the blind availability audit, recording each decision in
`decisions.md` before outcomes are inspected.

The Waterschap discharge and Provincie Limburg mine-water deliveries were added
on 2026-08-19 under the ignored external-deliveries tree and hashed. The
regional gate still **fails**. Do not inspect prospective signal contrasts or
lower the gate.

Waterschap supplied one exact quarter-hour grid for 2010--2025 with 15 series
columns, 14 station IDs and eight named watercourse labels. The CSV and XLSX
are cell-for-cell value-equivalent. `35_audit_waterschap_delivery.py` found nine
series across those eight labels that pass the provisional 80% overall/70%
every-year availability rule, but this is an upper bound rather than a cohort.
The 2026-09-07 provider follow-up confirms trailing 15-minute means, unavailable
blank cells, no validation flags and no relocations; it also supplies rating
curves and station-specific July 2021 failure/range evidence. Raw availability
is now kept separate from analytical usability in
`35_audit_waterschap_delivery.py`. Timezone/DST, zero semantics, numerical
coordinates and natural/managed cohort status remain unresolved.
Millen/Vloedgraaf and Partij/Molentak are split systems, Munstergeleen is
threshold-labelled, Oud-Roosteren is duplicated and Meerssen has gravel-bar
interference. No p99 threshold or event has been calculated.

The Viefhues K4 source is reproducible and has all 744 July 2021 hours. Device
identity/calibration, complete ABC lineage, a defensible hydrological pair,
independent onset bounds and later complete events remain unresolved. The CO2
case is therefore unavailable, but the regional chapter is not blocked by it.

Provincie Limburg confirms that GMW000000091726 (Willem) and
GMW000000091599 are mine-water-network points. The delivered `WILLEM OUD`
series contains 31 daily July 2021 observations; its adjacent replacement
starts in December 2023. The untouched files and receipt are in
`data/raw/external_deliveries/provincie_limburg/2026-08-19/`. Timezone,
validation status, value/sentinel semantics, identifier mapping, continuity and
reuse terms must be resolved before use. This is secondary mechanism evidence,
not a regional-gate input and not enough to make the Kerkrade case available.

## ERA5-Land acquisition

The ERA5-Land backfill completed all 300 months from 2001-01 through 2025-12 in
`stkerkradeprod01bg` / `era5-land`. The final 2026-08-14 audit downloaded and
reopened all files, revalidated timestamps, variables, units and missing cells,
and recomputed sizes and SHA-256 hashes. Its manifest was byte-for-byte
identical to the cloud manifest: 300 unique periods, blobs and hashes, zero
missing/extra months and 310,537,386 total bytes.

The Function App remains available and HTTPS-only but is **Stopped**, which
definitively disables its five-minute timer. The defense-in-depth settings also
remain `ERA5_ENABLED=false` and
`AzureWebJobs.era5_backfill_timer.Disabled=true`. The running Python host did
not honor the trigger-specific setting alone, so stopping this backfill-only app
is the operative control. Azure reported no invocation at the first subsequent
five-minute boundary (13:35 UTC). SCM basic publishing remains closed. The
local fetch script is a fallback only.

The same 300 source files are available in the ignored local working cache at
`data/raw/era5_land/`. `data/raw/era5_land/manifest.csv` is identical to the
versioned `data/processed/era5_land_manifest.csv`; the raw NetCDF files remain
outside Git.

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
LANUK acquisition/feasibility code remains to reproduce the failed German
route. LANUK's 2026-09-11 reply confirms inflection-point change series but says
constant values and gaps cannot be distinguished and gives no hold-forward
rule; the conservative no-fill audit therefore stands. Azure collection code
is operational infrastructure, not chapter analysis.

The event helper now requires timestamps as well as rows to be exactly one hour
apart, preventing a false p99 crossing across an omitted timestamp. A focused
regression test protects that scientific rule.

## Agent work after deliveries

1. Inventory and hash native replies; resolve sampling, timezone, units,
   sentinels, rating curves, natural/managed status and July 2021 QA.
2. Complete the blind Waterschap availability audit; decide and record
   the watercourse floor, then fix the admissible cohort after metadata arrives.
3. Write the direct hourly discharge ingest only after source semantics and the
   cohort are fixed.
4. Build verified catchment polygons, assign the completed ERA5-Land grid by
   nearest catchment centroid and calculate RADOLAN area averages.
5. Complete the blinded threshold/coverage table and record the remaining
   floor decisions.
6. Rerun the strict gate and lock the protocol before outcomes if it passes.
7. Implement one direct pandas analysis producing tidy contrasts, pair medians,
   distance estimates, influence rows and four figures. Add only claim-
   protecting checks.
8. Add the Kerkrade section only if its separate evidence contract passes.

## Verification

Interpreter:
`/Users/briangillikin/miniforge3/envs/chapter1-co2/bin/python`

- literature crosswalk: 44 notes, 44 BibTeX keys, 98 matrix rows and 37 unique
  DOIs; all keys resolve;
- default scientific suite: **26 passed**;
- operational infrastructure suite: **5 passed**;
- Ruff lint and format: passed across **47 files**;
- ERA5 raw archive: **300/300 months complete**; all NetCDF checks passed;
  recomputed and cloud manifests byte-identical; 300 unique hashes;
  backfill-only Function App stopped;
- regional gate report: expected **FAIL**, with all six contracted inputs
  absent;
- Waterschap delivery: 561,024 requested-period quarter-hours on an exact grid;
  15 series, 14 station IDs, eight named watercourse labels; XLSX/CSV values
  equivalent; no outcomes inspected;
- Viefhues real-file QC: 169,594 source rows, 2,829 hourly rows and 744/744 July
  hours.
