# Shared Limburg satellite acquisition

**Superseded later on 2026-10-15 for storage reasons.** The full-archive worker
is paused. Use the [compact acquisition](limburg-compact-eo-acquisition-2026-10-15.md).
The description below preserves the original launch record, not current
instructions to resume that worker.

2026-10-15. Internal acquisition record, not dissertation prose or a new result.
Brian requested acquiring the shared data first, then assessing model
compatibility. The archive is not restricted to whichever encoder is easiest.

## Scope and sources

Eight analysis catchments: Eys, Cottessen, Azijnfabriek, Mesch, Rimburg,
Brommelen, Herzogenrath 1 and Randerath. The inventory-only Vloedgraaf catchment
is excluded. The held delineations are buffered by 1 km for spatial context;
no claim that these provisional delineations are newly validated is made.

All available acquisitions intersecting that area from 2009 through 2025 are
catalogued. 2009 supplies possible antecedent context for early 2010 events.
All dates are retained, including cloudy scenes and non-event periods. This
supports seasonal references and different temporal windows without selecting
favourable events. Download order interleaves sensor-years; it is not a sample.

| Source | Preserved inputs |
| --- | --- |
| `COPERNICUS/S1_GRD` | IW, 10 m, VV/VH dB and incidence angle; both orbit directions and metadata. Angle is a coarser ancillary field resampled to the radar grid. This product is not assumed equivalent to a model's RTC inputs. |
| `COPERNICUS/S2_SR_HARMONIZED` | Surface-reflectance bands at 10/20/60 m, SCL, AOT, WVP and QA60. |
| `COPERNICUS/S2_HARMONIZED` | TOA bands at 10/20/60 m, including B10, and QA60, keeping the radiometric-level choice open. |
| Landsat 5/7/8/9 Collection 2 Tier 1 Level 2 | 30 m surface-reflectance bands, QA_PIXEL and QA_RADSAT, including the pre-Sentinel record. Thermal products are not included in this shared optical/SAR pull. |

Sources: [Sentinel-1 catalogue](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S1_GRD),
[Sentinel-2 SR](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED),
[Sentinel-2 TOA](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_HARMONIZED),
[Landsat 8 L2](https://developers.google.com/earth-engine/datasets/catalog/LANDSAT_LC08_C02_T1_L2).
The actual dated inventories, rather than nominal mission dates, determine
local availability. Landsat is not automatically interchangeable with Sentinel
in a frozen encoder.

## Storage and validity

The inventory contains **13,549 scene assets** and **318,658 tiled band-group
files** on 19 aligned 9.6 km tiles. The uncompressed raster estimate is
**1,594.9 GiB**; it is not an estimate of final compressed storage or network
traffic. Local free space at setup was about 580 GiB. Downloads use lossless
DEFLATE compression, mask outside the buffered area, and pause when free space
falls below 60 GiB. Completion is therefore not promised within local capacity;
resume on larger storage if the reserve is reached. No dates/sensors are
silently removed to fit the disk. This is a long-running archive acquisition,
not an expectation of completion in this agent turn.

Individual scenes are not temporally composited or cloud-screened. Spectral
band families retain their source pixel spacing but are regridded by nearest
neighbour to EPSG:32632; these are analysis-ready cutouts, not original SAFE
packages or untouched native sensor grids. Raw optical DN and QA values are
retained; apply documented scale/offset later. SAR remains in dB. The final
`valid_bits` band encodes validity of each preceding band (bit 0 for the first,
bit 1 for the second, etc.). Zero-filled missing pixels must not be treated as
observations. QA60 coverage changes are preserved as missingness.

The initial 24 validated smoke-test files retain full tile margins and are
uncompressed; subsequent files use buffered-area masking/compression. Both
cover the intended analysis area. Any model extraction must use the shared
catchment/context geometry, not arbitrary tile margins.

Every file has its source asset, acquisition time, band order, grid, byte count
and SHA-256 receipt. Failed requests are recorded and retried on rerun. No
credentials or ephemeral signed download URLs are saved. A run pauses after
10 consecutive failures rather than repeatedly submitting a broken request.

## Execution and current status

Script: `scripts/95_acquire_limburg_satellite_archive.py`.

```sh
cd /Users/briangillikin/Desktop/floods/chapter1-co2
.venv-foundation/bin/python -u scripts/95_acquire_limburg_satellite_archive.py --download
```

Archive: `data/raw/limburg_satellite_archive/` (git-ignored).
Log: `logs/satellite-acquisition.log` (git-ignored).
`worker.json` records the background PID; `progress.json` records current-run
counts, not a claim of complete coverage. `jobs.json` is the full file census;
`catalogues/` contains yearly source inventories. Reruns verify existing hashes
and fetch missing files. Do not launch a second worker against the same archive.
To move storage, copy the archive and resume with `--destination /path/to/archive`.

At handoff, the 24-file initial download completed without failures and the
full background worker had started downloading across sensor-years. These are
acquired imagery, not tested model embeddings. Compatibility checks follow;
there is no new fitted model, model ranking, event result or scientific gate.

Checks: five focused tests cover tile coverage/alignment, retained bands,
raster validation, lossless compression and complete sensor-year scheduling.
Ruff checks passed. The first actual downloads passed dimension/CRS/band-count
validation. No raw provider gauge files are uploaded as part of this acquisition.
