# Current data needs — DISE-inspired reconstruction

Updated 16 November 2026. [Implemented corrections and current inventory](limburg-dise-audit-corrections-2026-11-16.md).

| Input | Current status / remaining work |
| --- | --- |
| Local Q/qualifications | Held; daily observed/model reference and separate clean flags assembled |
| Local AlphaEarth | Held; fixed 2017 means selected, seven target catchments |
| Local weather | Acquired: 2017–2025 catchment-specific ERA5-Land daily summaries |
| Conventional local descriptors | Acquired: common terrain, 2017 land-cover fractions, surface field-capacity proxy; regulation coverage remains incomplete; exact-match no-dam evidence is not proof of no controls |
| Regional donor/external metadata | Acquired; 336 provisional donors, 50 reserved external records, 44 geometry/coverage flags; final mapping treatment still required |
| Regional observations | Acquired and checksum-verified: all 386 mapped nonlocal records, zero failed transfers; 821,400 complete daily observations in 2018–2024; 12 records have no complete daily overlap |
| Regional GEOGLOWS/weather/AlphaEarth | Acquiring locally for all 386 mapped records (371 distinct reaches), including explicit mapping flags; same reference polygons, hourly model source, weather bands and 2017 metric-grid AlphaEarth convention as local inputs |
| CAMELS-DE-1h source clock/quality | Verified primary documentation: UTC, preceding-hour means; mixed provider QA and no exhaustive direct source QA. Unknown quality stays unknown; incomplete days stay missing |
| Additional local provider emails | None required for this preparation |
| Full imagery or new encoder weights | Not required |

Regional source snapshots use 3.66 GiB and daily tables 84 MiB; 74.8 GiB was
free at verification. Matched regional inputs are now acquiring with one GEOGLOWS and two Earth
Engine workers; no model fitting is active. [Acquisition record](limburg-dise-regional-inputs-2026-11-16.md).
The regional verification source ends in 2024; local 2025 verification remains
separate, and 2025 regional predictors do not supply missing labels.

The prior GEOGLOWS next-24h comparison is completed. Its dated inventory below
is historical, not the acquisition list for the current reconstruction study.

---

# Current data needs — corrected GEOGLOWS Stages 1–2

Updated 14 November 2026. [Active design](limburg-geoglows-stages12-protocol-v2-2026-11-14.md).

| Input | Status / role |
| --- | --- |
| Seven NL/DE tributary Q records and provider qualifications | Held; observed inputs, historical training and verification |
| Sint Pieter and Venlo Q | Held and matched to GEOGLOWS reaches; contextual inputs, not targets |
| Common rainfall and regional event clock | Held; unchanged across stages; all 481 regional episodes retained |
| Presto/AnySat raw and encoded context tables | Held, checksums verified; reuse without new imagery extraction |
| GEOGLOWS hourly Q, 2010–2025 | Downloaded, pinned and verified at nine active sites; UTC hour-end aligned |
| Full stream/catchment geometry | Held; topology, area and source identities checked |
| Eys | Excluded as target/predictor in both stages; original data retained. Not an outstanding request |
| New core data request | None needed for this retrospective specification |
| As-issued forecast/reforecast and arrival records | Not acquired; needed for a later operational replay, not assumed available |
| External European rivers / new EO campaigns | Stage 3 not launched; no new acquisition committed |

Corrected preparation has 13,468 opportunities per stage. Earlier mapping-study
inventory below is retained as historical/completed work.

--- | --- |
| NL/DE observed Q and measurement qualifications | Held; reference inputs, historical training labels and independent observed verification |
| Meuse observations | Held; contextual channels at Sint Pieter and Venlo, not new targets |
| Common rainfall and storm clock | Held; unchanged across stages |
| Presto and AnySat context/raw features | Held, selected compact table hashes verified; reuse exact completed contexts |
| GEOGLOWS RFS V2 hourly discharge | Downloaded for 2010–2025 at nine mapped input sites; interval-start labels shifted to hour end |
| RFS V2 stream/catchment geometry | Downloaded and audited against local catchments; nine selected reaches and rejected Eys nearest reach documented |
| Eyserbeek independent model discharge | Not represented in this network; structural coverage limitation, not a pending download. Keep channel missing, retain separate coverage case |
| Additional core data requests | None needed for this retrospective Stages 1–2 specification |
| As-issued forecast/reforecast inputs | Not acquired by this setup; needed for a future operational replay, not assumed present |
| External European gauges / new imagery | Stage 3 not launched; no download committed by current setup |

Earlier mapping-study inventory below is retained as historical/completed work.

---

# Limburg data needs — accepted chapter scope

Updated 11 November 2026. Source of truth:
[agreed study](limburg-chapter-sized-study-2026-11-10.md) and
[active pointer](../config/limburg_current_study.json).

| Input | Status | Role / remaining work |
| --- | --- | --- |
| Paired-SAR source images, labels and identities | Held: all 5,000 Kuro/Copernicus records across 20 events | Source training/selection; retain water-containing selection and check event separation, class/ignore semantics and selected fit compatibility |
| Selected Copernicus-FM weights, code and normalizers | Held; native full-tile inference smoke passed | Frozen paired-date encoder and head; final all-source refits use the held source-selected protocol |
| Existing source-trained states and fit manifests | All six final all-source states complete and hash-verified; source development retained | Source-only recipe fixed from five held folds; no additional fit needed |
| External SAR, label, validity, flood and permanent-water masks | All nine pinned shards downloaded and hash-verified; 1,301 grids audited | Nine heldout activations; delivered P0 plus targets are available; **9.068 GiB** in the [core manifest](../config/limburg_chapter_sized_geoid_acquisition_v1.json) |
| Updated pre-cutoff SAR (P1) | Metadata inventory and harmonized P0/P1/post acquisition complete for the primary paired subset | 1,118 label-blind metadata candidates; 915 single-product triplets, of which 913 were downloaded and independently verified. Of the 913 paired tiles, 447 match post-image geometry and 466 do not. Report the intended compatible population separately from the full catalogue; all dates share the harmonized processing chain. |
| Existing local SAR acquisitions and mapped references | Complete mapping/scoring: 167 scene/grid records and 14 radar acquisition cases | All pass geometry; 35 records have a reference update. One July 2021 episode; timing and source-dependent labels qualify interpretation |
| René/Jens gauge records and provider notes | Held | Local event timing and measurement context only. They do not define flooded pixels or require a new discharge model |
| Recovery manifests and existing source backups | Retained | Verify any new transfer/cache before cleanup. Historical large imagery may require documented Azure restoration only if actually needed |

## Response-mapping continuation — 12 November 2026

**Later assessment:** [the plan audit](reviews/limburg-response-mapping-plan-audit-2026-11-12.md) revises the recommendation to keep the entire matrix unchanged. Acquired files and accessible papers do not establish that a full experiment is worthwhile. No training is launched; the audit recommends a finite comparator/target revision first.

The previous table describes the completed reference-policy study. Brian has now chosen the [local-adaptation response-mapping plan](limburg-response-mapping-plan-2026-11-12.md); historical exclusions of target adaptation below do not apply to this continuation. No training has started.

Required source/model inputs and the three July 2021 receiving cases are held. [New acquisitions and full-text review](reviews/limburg-response-mapping-literature-and-data-2026-11-12.md) add 15 paired SAR tiles for February 2021 EMSR497, 19 public regional vector packages, eight EMSR497 map PDFs, and 4TU flood-extent/ordinance context. Total new material including literature is approximately 1.01 GiB. The Rhine candidate requires reference/support preparation; Belgian discoveries are contextual, not an expansion of the primary geography. No new default agency request or model weights are needed.

Before fitting, finish unique-ground annotation/test separation, reference rasterization and validity, source pseudo-target lineage and counted annotation/validation budgets. These are preparation tasks, not missing external datasets. Independently observed truth and actual operator annotation time are not established by the downloads. All 12 core literature papers and required supplementary methods are accessible.

## Completed acquisition and validity resolution

All six final source states, external and local mapping/scoring and the geometry/target audit are complete. The [consolidation](limburg-study-consolidation-2026-11-11.md) records 447 geometry-compatible paired external tiles and all 167 compatible local records. No further data pull is required for the bounded interpretation.

## Preserved preparation requirements

Assign source versus external roles after actual event/geographic overlap and
label/reference checks. Preserve delivered-reference metadata, target ignore
classes, validity and permanent-versus-event-water meaning. Catalogue P1 by
metadata without target scores. More recent does not automatically mean better:
reference water may already be elevated. Record failed updates and unknown
coverage rather than converting them to dry pixels or removing events silently.

## Outside current completion requirements

No additional optical archive, dense AlphaEarth inputs, global benchmark expansion,
urban-coherence or beneath-canopy dataset is required. No target-label campaign,
label-budget/adaptation grid, new gauge/weather/soil/snow pull or delivery-log
request is introduced. Existing data and useful literature remain available;
[broader ideas](../archive/future-ideas/2026-11-10-broad-spatial-programme/README.md)
can be deliberately revisited later.

## Storage and compute

The 9.068-GiB package is the exact transfer size of uncompressed tar containers
holding compressed GeoTIFFs, not a total disk/runtime estimate. The native-grid
triplet acquisition adds roughly 23 MB per currently obtainable tile; actual
bytes and coverage come from per-tile receipts. Preserve the 50-GiB local
free-space reserve; use one MPS and up to two CPU workers where profiling
supports it. No other chapter's files were touched. The
[scoped compute policy](../config/limburg_chapter_sized_compute_v1.json)
replaces the broad programme's compute requirements.

## Accepted-scope audit — 10 November 2026

[Full audit and reproducible receipts](reviews/limburg-chapter-scope-audit-2026-11-10.md).
The full metadata/header census found26external tiles overlapping source footprints
and251with post-SAR/label-reference offsets exceeding24h. These are reporting and
provenance issues, not automatic exclusions. Keep evaluation labels fixed across
P0/P1 and match processing as well as geometry; a different service's P1 cannot
silently change calibration/resampling. Open catalogue/product metadata and
possibly harmonized same-footprint retrieval are needed; no new agency request.

Preserve native1024px target support. Whole-cohort float32 date features would
occupy about219GiB and all per-seed learned probabilities about183GiB before
compression, so use bounded tile/event streaming and verified remote preservation.
These are array-shape estimates, not extra downloads already started. About122GiB
was free at audit; the50GiB reserve remains. The prior9.068GiB package size must
not be mistaken for the complete execution footprint.
