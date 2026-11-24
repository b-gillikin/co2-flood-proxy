# TESSERA data access pilot

18 November 2026. Step 2 of the Limburg representation extension. The pilot
verified streaming and aggregation from the public **v1.1-dclimate** Icechunk
snapshot `VTS86NCZ0NT7DK59V390`. The planned 2017 product has substantial
coverage gaps in three of the four pilot catchments. The same release's
2018 product has near-complete coverage in these four catchments.

## Coverage

The four complete reference polygons were selected to exercise two local
catchments, one regional donor, one reserved external catchment, and the UTM
31/32 boundary. The percentages are shares of polygon area intersecting pixels
with a valid provider scale.

| Catchment | Role | Reference area (km²) | 2017 | 2018 diagnostic |
| --- | --- | ---: | ---: | ---: |
| Brommelen | Local | 36.45 | 87.21% | 100.00% |
| Cottessen | Local, UTM 31 and 32 | 121.38 | 50.88% | 99.97% |
| Herbram | Regional donor | 24.17 | 7.66% | 100.00% |
| Nespen | Reserved external | 26.39 | 11.53% | 99.99% |

Cottessen's 2017 coverage was 90.23% in zone 31 and 19.14% in zone 32.
Herbram and Nespen also have low coverage away from the seam. All excluded
area in the pilot had NaN scales. The provider characterizes them as
unembedded pixels, with the physical reason unresolved at each pixel.

The same release's Source Cooperative mirror returned exactly the same 2017
scale arrays, including NaNs, in five aligned 128 × 128 windows. The windows
included one in each catchment and one on either side of Cottessen's zone
boundary. The same windows had full finite-scale coverage in 2018–2020.
The complete-polygon 2018 check above provides stronger evidence than the
small windows. Coverage across the other 390 catchments remains open.

## Resource measurements

| Run | Wall time | Peak process RSS | Public response body transfer |
| --- | ---: | ---: | ---: |
| 2017, direct Icechunk S3 | 79.9 s | 763 MiB | No reliable direct byte count |
| 2017, metered HTTP | 59.6 s | 785 MiB | 398 MiB in 173 GETs |
| 2018, metered HTTP | 99.7 s | 853 MiB | 979 MiB in 235 GETs |

Both access paths read the pinned snapshot and produced identical 2017
per-catchment statistics and all 128 mean coordinates. The meter counted
actual public response bodies through a local read-only relay. Connection
overhead is outside those counts. The initial macOS process counter decreased
when connections closed, so it was replaced with direct body measurement.
Each run streamed 32 windows of at most 512 × 512 pixels. The isolated
environment occupies 857 MiB and the three receipts together occupy about
0.26 MiB. No raster files were retained.

The full geometry inventory implies **2,088 distinct windows**, of which
1,405 touch multiple catchments. At the pilot's observed rates, a simple
window-count extrapolation gives roughly 1–2 hours of uninterrupted reading
and aggregation and tens of GiB of transfer. The pilot retained only
compact receipts on disk. This extrapolation does not capture
regional differences in pixel density, network rates, or processing time per
overlapping polygon.

## Methods and evidence

Pixel weights are exact fractional intersections in the published 10 m zone
grids. The pilot split Cottessen at 6° E, checked each part's area accounting,
and verified that total zone areas agree to within 0.1% of the equal-area
reference. It dequantized native int8 codes using each pixel's own valid scale
before summing weighted values and squared values. It saved included and
unembedded areas, pixel counts, weighted sums, second moments, and means.
All mean vectors are finite and have 128 coordinates. Group completion and
source run IDs were read from the pinned snapshot.

Replay with the isolated Python 3.13 environment. The machine-readable
[pilot record](reviews/limburg-tessera-pilot-2026-11-18.json) preserves library
versions, request counts, coverage by zone, mirror checks, and file hashes.

```sh
OPENBLAS_NUM_THREADS=2 VECLIB_MAXIMUM_THREADS=2 \
  .venv-tessera/bin/python scripts/282_pilot_tessera.py \
  --snapshot VTS86NCZ0NT7DK59V390 --year 2017 --meter-http
```

Use `--year 2018` for the matched diagnostic. Raw receipts are under
`results/limburg_representation_extension_v1/tessera_pilot_v1/`.
[GeoTessera source formats and access](https://github.com/ucam-eo/geotessera).

## Implication for the next run

Start Step 3 with a scale-only coverage inventory for 2017 and 2018 across the
394 reference polygons. A mean based on 8–12% of a catchment may describe a
different landscape from a mean based on almost its full area. Use spatial
coverage and the shared input design to decide on the reference year, before
comparing discharge scores. If 2018 coverage holds across the census, align
AlphaEarth and the year-specific conventional descriptors to 2018 for that
comparison. The pilot itself measures data availability.

## Step 3 coverage run

Launched at 2:12 p.m. Eastern on 18 November. The coverage pass uses a single
local worker, 1,024 × 1,024 scale windows, and the same 10 m source grid and
fractional intersection weights as the pilot. Each year has 637 distinct
windows across the 394 catchments. Overlapping polygons share the reads.
Scale-only coverage measures eligible area without reading the embedding bands.
The completed receipts retain both valid and unembedded areas for every
catchment, plus area accounting by UTM zone.

Progress is in `results/limburg_representation_extension_v1/tessera_coverage_v1/`,
with a worker log and checkpoints for each year and zone. Rerun the same command
after an interruption to resume from the last written checkpoint. Run identity
includes the pinned snapshot, the geometry hash and the runner hash.

```sh
OPENBLAS_NUM_THREADS=2 VECLIB_MAXIMUM_THREADS=2 \
  .venv-tessera/bin/python scripts/282_pilot_tessera.py \
  --snapshot VTS86NCZ0NT7DK59V390 --year 2017 --year 2018 --census-coverage
```

The coverage census passed for 2018. All **394 of 394** polygons have at least
97.4% embedded area. By cohort, mean coverage is 99.89% for the seven local
gauges, 99.95% for the 337 regional donors and 99.98% for the 50 reserved
external records. In 2017 the corresponding means were 52.5%, 44.4% and 42.5%;
17 regional donor polygons had zero embedded area. The initial 2018 choice was
based on input coverage alone, not discharge performance, and it predates all
held evaluation years. A subsequent check of 2019 and 2020 showed that 2018 was
not the latest adequately covered candidate.

## Later pre-evaluation year coverage

The pinned store contains complete annual groups through 2025 in both UTM
zones. Since the first held evaluation year is 2021, 2020 is the latest
strictly pre-evaluation candidate. Full-census scale-only coverage was checked
for 2019 and 2020 before changing the reference-year recommendation.

| Year | Cohort | n | Minimum coverage | Mean coverage | At least 95% |
| --- | --- | ---: | ---: | ---: | ---: |
| 2018 | Local | 7 | 99.74% | 99.89% | 7 |
| 2018 | Regional donor | 337 | 97.43% | 99.95% | 337 |
| 2018 | Reserved external | 50 | 99.46% | 99.98% | 50 |
| 2019 | Local | 7 | 99.94% | 99.98% | 7 |
| 2019 | Regional donor | 337 | 99.44% | 99.99% | 337 |
| 2019 | Reserved external | 50 | 99.69% | 99.99% | 50 |
| 2020 | Local | 7 | 99.92% | 99.97% | 7 |
| 2020 | Regional donor | 337 | 99.67% | 99.99% | 337 |
| 2020 | Reserved external | 50 | 99.84% | 99.99% | 50 |

Recommend **2020** as the extension's fixed pre-evaluation descriptor year:
it is the latest complete year before evaluation and all 394 polygons exceed
99.6% embedded area. The 2018 descriptors are complete and preserved, but are
provisional rather than the extension's primary features. The original
2017 H+A/AlphaEarth analysis remains unchanged. A 2020 descriptor is a fixed
pretest catchment snapshot, not an operational as-of-each-day predictor; this
retrospective design does not establish real-time availability during the
earlier training years.

For the new controlled extension, 2020 is the recommended common annual
descriptor reference. The completed original H+A/AlphaEarth study remains on
its original 2017 basis and is not rewritten. The extension needs 2020
AlphaEarth, TESSERA and year-aligned conventional C1 inputs before fitting any
paired comparison. The full 2020 TESSERA and AlphaEarth extractions completed
on 19 November. Both inputs were used in the held Geul 2021 benchmark with
C0. The completed 2018 extraction is retained as a verified alternate.

The full TESSERA 2018 descriptor census is a resumable run. It streams native
128-band windows, decodes each pixel with its own scale, applies fractional
polygon weights, and checkpoints weighted sums and second moments by UTM zone.
Only compact per-catchment descriptors and the coverage receipt are retained;
no complete mosaics or downloaded raw tile archive are written locally. The
completed run took 3 hours 25 minutes, with a peak RSS of 2.08 GiB. The machine
had 132.36 GiB free before and after; no large raster cache was retained.

```sh
OPENBLAS_NUM_THREADS=2 VECLIB_MAXIMUM_THREADS=2 \
  .venv-tessera/bin/python scripts/283_extract_tessera_census.py \
  --snapshot VTS86NCZ0NT7DK59V390 --year 2018
.venv-tessera/bin/python scripts/284_validate_tessera_descriptors.py
```

Checkpoints and the receipt are under
`results/limburg_representation_extension_v1/tessera_census_v1/`. The run
identity pins the public snapshot, 394-polygon geometry, and extraction/helper
code hashes. Rerunning the same command resumes at the last atomic zone
checkpoint; a changed identity fails closed.
