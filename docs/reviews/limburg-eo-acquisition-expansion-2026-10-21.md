# Expanded EO acquisition

Status: full supplemental download running locally. Brian requested broader
acquisition rather than optimizing primarily for download economy. No new model,
event definition or scientific result is introduced.

## Scope

Script 114 prepares and downloads **66,913 additional files** for all **930
existing calendar windows**, using the existing spatial tile grid and held scene
catalogues. It includes all overlapping catalogued scenes in each selected route;
no flood outcome selects an acquisition. Weekly additional SAR is first, followed
by weekly optical and the requested monthly contexts.

| Additional product | Files |
| --- | ---: |
| S1 ascending orbit 15 | 1,644 |
| S1 ascending orbit 161 | 1,231 |
| S1 descending orbit 37 | 8,317 |
| S1 descending orbit 139 | 8,493 |
| S1 descending orbit 141 | 32 |
| S1 descending orbit 39 | 32 |
| Landsat 5 surface reflectance | 1,106 |
| Landsat 7 surface reflectance | 7,452 |
| Landsat 8 surface reflectance | 7,676 |
| Landsat 9 surface reflectance | 2,499 |
| S2 harmonized TOA, 10 m bands | 9,477 |
| S2 harmonized TOA, 20 m bands | 9,477 |
| S2 QA60, native 60 m | 9,477 |

Ascending orbit 88 is already held and is not downloaded again. Sparse additional
orbits remain in the inventory; they are not excluded for small counts. The
catalogue includes seven SAR direction/orbit combinations across the full period,
including the existing route; the earlier five-combination count described the
2017 catalogue only.

The purpose is to recover observational opportunities lost by a single SAR orbit
or one optical processing route, and retain earlier optical coverage. More files
do not guarantee more complete weeks or model-ready inputs. No 2026 observations
are added to the existing event calendar merely because they are now available.

## Scientific identities retained

- SAR remains separated by direction and relative orbit, retaining VV/VH dB,
  incidence-angle bands and source scene metadata. It is not automatically pooled
  across viewing geometries. [Official S1 dataset description](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S1_GRD).
- Each Landsat sensor remains separate. The six SR bands use the published
  Collection 2 conversion `DN * 0.0000275 - 0.2`, with QA_PIXEL, QA_RADSAT and
  sensor identity in the clear-pixel composites. Fill, dilated cloud, cirrus,
  cloud, shadow and saturated/dropped pixels are excluded; snow and water are
  retained. QA values accompany selected valid composite observations; these
  exports are not a complete unmasked per-scene QA archive. Landsat 7 scan-line
  gaps are not fabricated away. [Official Landsat 7 description and scaling](https://developers.google.com/earth-engine/datasets/catalog/LANDSAT_LE07_C02_T1_L2).
- S2 TOA is a separate reflectance level, retained at native spectral resolutions
  with dates. It does not substitute for SR or establish clear/cloud-free support.
  QA60 is separate because its availability and construction change over time;
  absent QA is not interpreted as clear sky. No automatic TOA-to-SR harmonization
  or reuse of the existing SR encoder normalization is claimed.
  [Official harmonized S2 L1C description](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_HARMONIZED).

The planned optical export is not limited by scene-level cloud-percentage cuts.
All candidate identities/timestamps remain in receipts; composite quality masks
and reflectance level remain explicit. Dates are inside the same completed
calendar windows, with no future scene or nearest-date replacement.

## Storage and execution

Separate destination: `data/raw/limburg_eo_expansion/`. The original compact
archive, active extraction sources, model weights and current results are unchanged.
Original Azure acquisition/inference compute remains deallocated; this worker uses
the existing local Earth Engine credentials. No new VM was started.

The uncompressed payload is approximately **589.6 GB**; the actual files are
losslessly compressed on download, so this is not a forecast of disk consumption.
The compressed total is not yet established. About 238 GiB was free at preparation.
The downloader retains a 60 GiB free-disk reserve to protect the running extraction
and laptop; this is physical storage management, not an event or scientific
coverage gate. The full ledger remains intact if storage requires a pause or
relocation. It does not silently drop the rest of the requested data. No new
arbitrary image-volume cap was added.

Three download workers run with one-thread numeric/GDAL settings. Temporary
exports are validated, losslessly packed and atomically committed with source
metadata, date lists and SHA-256 receipts. Matching verified files resume without
redownloading. Each destination has an exclusive lock. Failed jobs are listed
and remain in the ledger for retry; completion with failures is distinguished
from successful completion.

Live status: `data/raw/limburg_eo_expansion/progress.json`; worker PID/launch details
are in `worker.json`; output log is `logs/eo-expansion-download.log`.

## Validation and follow-through

All 13 product routes passed real Earth Engine exports: 13 downloaded, zero
failures. An independent plan audit checked all 66,913 jobs for date bounds,
source-list agreement, orbit purity, expected radar polarization and unique band
names, with zero issues. Seven acquisition tests pass with the existing PROJ data
directory supplied explicitly. The first test invocation encountered the known
missing PROJ directory; it passed after pointing at the working existing database,
without changing runtimes or active workers. Lint passes. The compact check receipt
beside this note records the plan/runner hashes and smoke status.

After acquisition, verify actual masks and dates, then measure which contexts can
be recovered per pass/sensor and identify compatible encoder use. Preserve the
original run as an analysis of its documented acquisition route. Any expanded
representation must have separate provenance and matched comparison populations.
Do not conclude that different reflectance levels or orbits are interchangeable
because they are now available. This acquisition enables that work; it does not
claim its completion or alter the research question.

Preparation and run commands from chapter root:

```sh
.venvs-eo/terramind/bin/python scripts/114_expand_limburg_eo_acquisition.py
# Earth Engine/network access required; use the existing working PROJ_DATA path.
.venv-foundation/bin/python scripts/114_expand_limburg_eo_acquisition.py --smoke
.venv-foundation/bin/python scripts/114_expand_limburg_eo_acquisition.py --download --workers 3
```
