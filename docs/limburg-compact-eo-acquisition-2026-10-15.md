# Compact EO acquisition for the bounded model screen

2026-10-15. Internal research/engineering note, not dissertation prose or an
empirical model comparison. Supersedes the full-archive download. Brian approved
a compact shared input package after raising the local storage constraint.

## What is being acquired

The same eight held analysis catchments (six NL and two DE), buffered by 320 m,
are covered by shared EPSG:32632 tiles. Pixels outside this buffered domain are
masked and losslessly compressed. Pooling/model extraction must distinguish the
actual catchment from its context buffer and tile margins. The held delineations
remain provisional; this acquisition does not validate them.

| Product | Bands / provenance |
| --- | --- |
| Sentinel-2 SR, 10 m | B2, B3, B4, B8; per-pixel acquisition day and validity bits. |
| Sentinel-2 SR, 20 m | B5, B6, B7, B8A, B11, B12 and SCL; acquisition day and validity bits. |
| Sentinel-1, 10 m | VV/VH in dB, ancillary incidence angle, acquisition day and validity bits. One consistent ascending relative orbit, 88. Its 2017 scene footprints cover all held catchments. Actual per-date coverage is still checked through pixel masks. |
| HLS, 30 m | Blue, green, red, narrow NIR, SWIR1/2, Fmask, sensor ID, acquisition day and validity bits. Harmonized S30 and L30 observations feed one layer. Sensor ID 1 = S30, 2 = L30. Physical reflectance remains floating point. |

Monthly and recent-week imagery reuse the same source inventories and files
across events. Ordinary pre-Sentinel Landsat archives, duplicate S2 TOA,
descending SAR, thermal bands and broad atmospheric initialization fields are
deferred. A checkpoint that genuinely needs a different radiometric product or
sensor branch receives an explicit compatibility decision; these are not all
assumed interchangeable.

Sources: [S2 SR](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED),
[S1 GRD](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S1_GRD),
[HLS S30](https://developers.google.com/earth-engine/datasets/catalog/NASA_HLS_HLSS30_v002),
[HLS L30](https://developers.google.com/earth-engine/datasets/catalog/NASA_HLS_HLSL30_v002).
HLS supplies the six-band input convention documented by
[Prithvi-EO-2.0](https://huggingface.co/ibm-nasa-geospatial/Prithvi-EO-2.0-300M-TL).
Its current model card also lists Tiny/100M variants: a 300M/600M checkpoint is
not inherently required for the bounded screen.

## Temporal design and event census

All **468** rows of `results/storm_response/storms.csv` remain in the event map.
There is no outcome/peak-based event selection. For each existing assessment
landmark, request up to 12 completed calendar months and the four most recent
completed UTC Monday-to-Monday weeks. Equivalent requests are exported once.
The 12-month history is a proposed shared screening context, not a universal
minimum imposed by the model families.

Every source acquisition is within the requested half-open interval [start,end)
and the interval ends no later than the assessment cutoff. The unfinished
current week/month is excluded. Weekly bins can therefore miss the most recent
few days of wetting; they must not be described as observing the storm itself.
Record acquisition age and evaluate the representation as antecedent context.
A precisely truncated event-time scene pull is a possible later targeted
addition if this limitation is material, not included silently here.

Pixels take the latest usable actual observation in each bin, not a median
invented spectrum. This is a spatial mosaic: pixels can have different dates.
Per-pixel dates and the exact candidate asset timestamps are retained. The S2
stored date is a floored UTC epoch day; SAR/HLS use floating epoch days. Exact
candidate times remain in receipts. These data are not sufficient to assert
historical real-time availability, because processing/publication latency and
modern model training are separate issues.

S2 SCL masks 0/1 (missing/saturated), 3 (shadow), 8/9 (cloud), and 10 (cirrus).
Snow and water remain. HLS masks cloud, adjacent cloud and shadow (Fmask bits
1/2/3); snow/water remain. Missing/fully cloudy pixels stay missing, with zero
fill distinguished by validity bits. S1 orbit 88 is held fixed rather than
mixing viewing geometries. GRD is not assumed equivalent to RTC or a model's
published normalization/preprocessing contract.

Older events and early/sparse Sentinel years are retained in the map, not
promised as eligible for every encoder. Empty windows are recorded; imagery
availability is not inferred from nominal mission start dates. A scene-count
inventory is not a clear-pixel coverage assessment. That assessment and matched
model cohorts follow actual acquisition/compatibility checks.

## Sized manifest and storage controls

The current manifest contains 905 unique requested intervals, 684 with at least
one relevant source scene, and **35,442** export files. The total tiled raster
size before lossless compression is **322.45 GB**. This is not a promise that
the compressed package fits 20–50 GB. Spatial masking/compression will reduce
it; the downloader enforces the budget rather than trusting an extrapolation.

- **70 GB original local imagery-archive ceiling**, including metadata and receipts.
  Brian raised the Azure service ceiling to **200 GB** on 2026-10-15; this is an
  explicit runtime override, preserving the pinned original acquisition manifest.
- **100 GB budget for the new work**, reserving space for weights/processing.
  The downloader counts the retained legacy archive and the designated
  `data/raw/limburg_dynamic_model_weights` folder against this budget; future
  preprocessing must respect the remaining allocation too.
- Reservations cover concurrent uncompressed/packed temporary files. Existing
  files are hash-verified. A 60 GiB free-disk reserve is also retained.
- If the cap is reached, pause and retain the complete pending manifest. Do not
  report the acquired prefix as a completed cohort or automatically exclude its
  missing events. Later streaming/inference can release cache space after
  verified embeddings/provenance are saved; eviction is not implemented yet.
- No automatic deletion of already acquired data. The original full-archive
  worker remains suspended. Script 95 now requires an explicit full-archive
  override, preventing an accidental restart via its former command.

## Execution and handoff

```sh
cd /Users/briangillikin/Desktop/floods/chapter1-co2
# Manifest only; no imagery export:
.venv-foundation/bin/python scripts/96_acquire_limburg_compact_eo.py
# Resume missing files within the stated budgets:
.venv-foundation/bin/python -u scripts/96_acquire_limburg_compact_eo.py --download
```

The compact worker now runs independently on Azure. Four cloud product exports
passed SHA-256 readback checks; all 3,341 completed local files were uploaded,
and the local worker was retired. Production acquisition is continuing; this
does not mean that all 35,442 planned files are complete. The laptop can close.
See the [Azure operating instructions](../infrastructure/compact_eo/README.md).
Do not restart the local worker or start a duplicate cloud worker;
there is also an archive lock. Local paths (all git-ignored):

- `data/raw/limburg_compact_eo/plan.json`: design, hashes, sized manifest summary.
- `event_windows.json`: every event and its requested windows.
- `availability.json`: source-scene counts, including empty product windows.
- `jobs.json`: complete pending/acquired export census with source metadata.
- `images/`: TIFFs and per-file SHA-256 receipts.
- `progress.json`, `worker.json`, `errors/`: current-run status and failures.
- `logs/compact-eo-acquisition.log`: running log.

Actual exports from all four product families passed grid/band/compression
checks. HLS values were checked as physical floating-point reflectance; S2 DN
and SAR dB retain their documented radiometric types. The four export checks
are QA fixtures, not the analysis event sample. Ten focused tests pass for
past-only/deduplicated windows, spatial coverage, source selection/orbits,
HLS merging, float preservation, immutable scientific specifications,
lossless compression and transient/working-budget accounting. Ruff passes.

Next: check the nine EO candidates against the prepared input contracts, choose
one frozen checkpoint/configuration each where feasible, and document exact
normalization, spatial/temporal adapters and any missing modality. No model
has been fitted or ranked, and no dissertation finding has changed.
