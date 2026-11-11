# Limburg data needs — accepted chapter scope

Updated 10 November 2026. Source of truth:
[agreed study](limburg-chapter-sized-study-2026-11-10.md) and
[active pointer](../config/limburg_current_study.json).

| Input | Status | Role / remaining work |
| --- | --- | --- |
| Paired-SAR source images, labels and identities | Held: all 5,000 Kuro/Copernicus records across 20 events | Source training/selection; retain water-containing selection and check event separation, class/ignore semantics and selected fit compatibility |
| Selected Copernicus-FM weights, code and normalizers | Held; native full-tile inference smoke passed | Frozen paired-date encoder and head; final all-source refits use the held source-selected protocol |
| Existing source-trained states and fit manifests | Completed source-CV studies retained; two exact inference states recovered from verified Azure bundles | Source-only final fit recipe fixed from five held folds; six all-source states are being produced |
| External SAR, label, validity, flood and permanent-water masks | All nine pinned shards downloaded and hash-verified; 1,301 grids audited | Nine heldout activations; delivered P0 plus targets are available; **9.068 GiB** in the [core manifest](../config/limburg_chapter_sized_geoid_acquisition_v1.json) |
| Updated compatible pre-event SAR (P1) | Metadata inventory and harmonized P0/P1/post acquisition complete for the primary paired subset | 1,118 label-blind metadata candidates; 915 single-product triplets, of which 913 were downloaded and independently verified. Record remaining tiles as coverage limits. Use the same processing chain for all three images in the paired contrast. |
| Existing local SAR acquisitions and mapped references | Held: mixed radar/optical archive has 54 acquisition/AOI cases and 43 prepared reference grids | Use all assessable radar cases, not all mixed archive entries by default. Verify acquisition timing, support and provenance; no claim of many independent July 2021 events |
| René/Jens gauge records and provider notes | Held | Local event timing and measurement context only. They do not define flooded pixels or require a new discharge model |
| Recovery manifests and existing source backups | Retained | Verify any new transfer/cache before cleanup. Historical large imagery may require documented Azure restoration only if actually needed |

## Data preparation still needed

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
