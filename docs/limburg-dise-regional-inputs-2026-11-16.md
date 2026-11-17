# Matched regional input acquisition

16 November 2026. Internal research aid. Requested by Brian; acquisition is
completed and hash-verified, not a completed regional analysis. No dissertation prose or new
model family is introduced.

## Scope and correspondence

Acquire all 386 mapped nonlocal records: 336 provisional regional donors and
50 reserved external records in Ahr/Erft/Sieg. They correspond to **371 distinct
GEOGLOWS reaches**; shared reaches are downloaded once and linked explicitly.
The existing mapping ledger, source roles, topology groups, reference areas and
geometry/coverage flags remain unchanged. Flagged spatial pairs and twelve
records without 2018–2024 observational overlap are retained in acquisition;
this does not approve their later analytical correspondence or quality.

All catchment means use the **reference gauge catchment**, matching the observed
Q verification footprint. Modelled Q comes from its documented selected global
reach. Preserve both areas and overlap diagnostics. No selection uses Q errors,
reserved external labels or a favourable AlphaEarth result.

## Inputs and conventions

| Input | Acquisition |
| --- | --- |
| GEOGLOWS V2 | Hourly retrospective Q, 2017–2025. Group requested reaches by source storage chunk to avoid repeated decompression. Shift UTC hour-start means +1 h, then require exactly 24 valid hourly means per UTC day, as in local preparation. Retain m³/s and convert with the same reference area for matched specific discharge. |
| ERA5-Land | 2017–2025 daily precipitation, temperature, dewpoint, pressure, wind components and short/longwave radiation. Same eight bands and native-grid pixel-area/fraction weighting as local preparation. Annual stacks avoid hundreds of simultaneous spatial reductions; batches retain every requested gauge/date and source dates. Missing values remain missing; negative accumulated values are counted and retained in raw input snapshots for the existing feature-level missing-value policy. |
| AlphaEarth | Fixed 2017, all 64 axes, EPSG:3035 at 10 m. Same mean/count reduction as the metric-grid local table. Retain per-axis common support, valid pixel counts, geometry hashes and unnormalised catchment means. No new imagery/encoder extraction. |
| Conventional controls | The same SRTM elevation/slope, 2017 Copernicus tree/crop/urban fractions and OpenLandMap surface field-capacity proxy used locally; 100-m EPSG:3035, common valid support. Reference area/location remain in the ledger. This prevents an unfair comparator gap and is not a new research branch. Regulation coverage remains incomplete. |

The daily GEOGLOWS derivative was checked against one held local 2021 hourly
aggregation (365 complete days, maximum absolute difference 0.0005001 m³/s).
Rather than silently interchange derivatives, this acquisition retains the
**same hourly source/aggregation** as the local study. The difference is not a
new hydrological finding or evidence of a source error.

Source observations end in 2024. Downloading 2025 predictors does not create
external verification for 2025: retain that absence explicitly. Local 2025
verification remains available. Incomplete terminal observation days are not
filled from model outputs.

## Execution, storage and recovery

Configuration: `config/limburg_dise_regional_inputs_v1.json`.
Command (existing isolated acquisition runtime):

```sh
.venv-geoglows/bin/python -u scripts/267_acquire_dise_regional_inputs.py all
```

One GEOGLOWS worker and two Earth Engine workers ran concurrently and have finished. No GPU,
Azure compute, full global archive or image export is required. Compact local
raw tables and combined tables are expected to remain well below 1 GiB; source
network traffic and decompressed working memory can be larger because global
storage chunks contain unrequested dates/rivers. Preserve the 50-GiB reserve.
Actual coverage, size and runtime are reported from receipts, not inferred from
successful requests. No fixed completion estimate is claimed before representative
batches complete.

Raw per-reach/per-batch tables and checksummed receipts:
`data/raw/limburg_dise_v2/regional_inputs/`.
Progress, executed source snapshots, runtime/run manifest, and eventual combined
matched tables: `results/limburg_dise_v2/regional_inputs/`.

The first shell-background launch stopped early without a recorded traceback;
its completed inputs were checksum-verified and reused. The resumed acquisition
completed successfully in managed execution session 38318. Do not start a duplicate process: a
single-run file lock protects the acquisition. Completed requests are reused
only when source identity and checksums agree. Failed requests receive three
attempts; unresolved failures are recorded, not replaced with fabricated data.

After acquisition: verify calendar/population support and all file receipts,
review mapping flags independently of outcomes, assemble compatible features,
and benchmark actual regional training size before full regional fitting.

## Source documentation

- [GEOGLOWS retrospective data](https://training.geoglows.org/rfs/datasets/retrospective/): hourly means are labelled at interval start in UTC; this is retrospective reanalysis, not an as-issued forecast.
- [ERA5-Land daily catalogue](https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_LAND_DAILY_AGGR): `_sum` bands represent daily accumulated flows; other selected bands are daily means. Known accumulated-value artefacts require explicit handling.
- [AlphaEarth catalogue](https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_SATELLITE_EMBEDDING_V1_ANNUAL): all 64 axes jointly represent annual surface information and support spatial aggregation; do not treat axes as individually physical variables or annual vectors as storm observations.

The acquisition helpers pass four meaningful support/identity regression tests;
together with the existing DISE and GEOGLOWS tests, **41 tests pass**. No new
package was installed or fitted-model runtime changed.


## Completed acquisition and verification

All 371 distinct model reaches, 117 weather batches, 49 AlphaEarth batches and
13 conventional-attribute batches completed successfully. All **550 raw tables**
and four combined tables passed independent SHA-256 re-verification. Model and
weather tables each contain **1,268,782 gauge-days**, covering all 386 gauges
over 2017–2025 with no missing model/weather cells. AlphaEarth and conventional
controls each contain 386 rows, all with valid spatial support. This establishes
input coverage, not measurement quality or final spatial correspondence.

Combined files occupy approximately 94 MiB; about 79 GiB remains free. The
completion audit is `results/limburg_dise_v2/regional_inputs/completion_audit.json`.
No workers remain active, and no full regional model fit has started. Remaining
work is mapping-flag treatment, compatible feature assembly and a regional-size
benchmark; external observation coverage still ends in 2024.
