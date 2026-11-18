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
comparison. The completed 2017 AlphaEarth study remains the reference for
its original experiment. The pilot itself measures data availability.
