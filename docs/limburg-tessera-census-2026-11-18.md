# TESSERA full-census descriptors

Completed 18 November 2026. Internal research and data-processing record;
Brian writes dissertation prose.

## Result

Extracted the 2018 TESSERA v1.1-dclimate 128-band descriptors for all **394**
reference catchments in the pinned Icechunk snapshot
`VTS86NCZ0NT7DK59V390`. This covers seven local gauges, 337 regional donors
and 50 reserved external records. It is the full intended census, not a sample.

The 394 catchment means are finite. Coverage agrees with the preceding
scale-only census to within `2.3e-16` for every polygon. Minimum coverage is
97.43% among regional donors, 99.46% among reserved external records and
99.74% among local gauges. Mean coverage is 99.95%, 99.98% and 99.89%,
respectively. Each descriptor contains the 128 native coordinates, weighted
sum, weighted second moment, embedded area, coverage and valid-pixel count.

The run processed 2,088 spatial windows across UTM zones 31N and 32N. It took
3 hours 25 minutes, with peak resident memory of 2.08 GiB. The window arrays
read and decoded totaled 72.25 billion bytes; this is processed array volume,
not a retained download or a measure of network transfer. Disk space was
132.36 GiB before and 132.37 GiB after. No raw mosaics were retained.

## Method and validation

For each 10 m pixel, decode its native signed-int8 embedding with that pixel's
scale before aggregation. Weight by exact fractional polygon intersection area.
Sum over the two UTM-zone pieces where needed, while retaining missing/source
nodata as unknown. Do not treat NaN scale as water, replace missing pixels with
zero, or average integer codes before dequantization. The published native
128-dimensional area-weighted mean is the descriptor for the extension.

The run uses bounded 512 × 512 windows and atomic per-zone checkpoints. Its
receipt records the exact snapshot, geometry hash, extraction and helper code
hashes, source run IDs, package versions, window counts, coverage, sums,
second moments and resource use. Run files are in
`results/limburg_representation_extension_v1/tessera_census_v1/`:

- `receipt_2018_direct.json` is the full result and provenance receipt.
- `descriptors_2018.csv` is the model-input table, with gauge, station, role,
  coverage and 128 feature columns.
- `validation_2018.json` records validation hashes and CSV-to-receipt checks.
- `checkpoint_2018_31N.npz` and `checkpoint_2018_32N.npz` retain the resumable
  accumulators.

Quality control found a CSV quoting defect in the first export: one station
name contains a comma. The receipt vectors were unaffected. The CSV was
regenerated from the receipt with standard CSV quoting, and all 394 rows and
128 features match the receipt exactly (`max_abs_delta = 0`). The correction
and repeatable exporter are in `scripts/284_validate_tessera_descriptors.py`.
After rerunning the extraction command, rerun that exporter to validate and
regenerate the CSV.
The executed extraction source is preserved in commit `8d04950` and its hash
is recorded in the receipt.

## Interpretation and next work

The 2018 reference year is justified by near-complete native support across the
entire census and because it predates every held evaluation year. This choice
used coverage only, not discharge results. The original 2017 H+A/AlphaEarth
study remains unchanged. Do not compare its 2017 result with the new 2018
descriptor as though the year were matched.

Before fitting the extension, acquire or extract 2018 AlphaEarth means and
assemble conventional C1 summaries from the same year-aligned information
families. Resolve the StefaLand runoff-free artifact and Basin2Vec trained
weights/input schema. This TESSERA run supplies an input representation; it is
not a model-performance result and says nothing yet about predictive value.
