# Limburg steps 2–3 — acquisition and native-grid audit

Internal research and engineering record, 10 November 2026. No external
accuracy result has been calculated; Brian writes all article/dissertation text.

## Step 2: data and scientific checks

- The nine pinned GEOID shards downloaded and passed byte-length and SHA-256
  verification against the locked acquisition manifest. The full 1,301-tile,
  nine-activation released cohort has matching 1024 × 1024, 10 m grids for its
  delivered pre/post VV/VH radar, composed three-class label, original flood
  mask, permanent-water mask and validity raster. All five SAR tar shards can be
  read through GDAL `/vsitar` without extracting another ~9 GiB.
- The label is the scoring target. Its source masks are not interchangeable with
  it: 629 tiles disagree with the original flood mask and 24 with permanent
  water on at least one non-ignored pixel. There are 409 tiles with no class-2
  flood pixels; flood IoU is undefined when neither target nor prediction has
  class 2. These tiles remain in the coverage and false-alarm census.
- The public CDSE catalogue initially yielded 1,189 apparent P1 updates. A
  source-blind check against sensing time in the product IDs removed 71 cases
  that reused the original acquisition under another catalogue/product ID.
  The corrected inventory has 1,118 metadata candidates. Of those, 915 have
  one product each for P0, P1 and post-event radar. This simple, reproducible
  triplet subset is the primary P0/P1 comparison; other tiles remain in the
  complete P0/coverage ledger. The delivered P0 combines differing platform,
  orbit or pass traits on 112 tiles. Two otherwise eligible tiles refer to a
  Sentinel-1C product absent from the tested Earth Engine collection, leaving
  913 triplets obtainable through this chain. All 913 downloaded triplets have
  subsequently passed an independent SHA-256, six-band/native-grid and positive
  finite common-support check: 20,834,777,811 bytes and 612,315,903 jointly
  valid, labeled pixels. Two tiles remain unavailable in the chosen chain.
- A single-tile radiometric check found the Google Earth Engine P0 image and
  the delivered GEOID P0 image share sensing identity and 10 m grid but do not
  have equal pixel intensities: GEE/delivered median ratios are ~0.71 for VV and
  VH on that tile. This is **one diagnostic tile**, not a cohort-wide correction.
  Consequently the paired P0/P1 experiment exports P0, P1 **and post-event**
  from the same `COPERNICUS/S1_GRD_FLOAT` chain. The delivered P0 cohort is
  scored separately, with its processing provenance visible. No mixed-chain
  P0/P1 delta will be reported as a reference effect.
- Earth Engine pilot exported all six bands on exactly the native target grid;
  the 913-triplet acquisition and independent verification are complete.
  Metadata candidates and image downloads are distinct statuses. The model still faces transfer from the
  processed Flood-S1 source to a separate external chain; source normalization
  remains frozen and that domain shift belongs in interpretation.

## Step 3: native inference and code/data cleanup

- A 1024px tile is covered by 25 overlapping 224px windows, with crop-specific
  coordinates/date metadata. Probabilities are averaged on overlap only where
  radar is valid; absent pixels remain unknown. The full tile is never resized
  to 224px.
- On one harmonized six-band tile, the held source-CV standard U-Net state ran
  P0 and the held source-CV native Copernicus state ran P1. Both produced native
  3 × 1024 × 1024 probabilities, complete valid support and per-pixel class sums
  within 2e-7 of one. This is an **engineering smoke test**, not final scoring;
  final all-source states are being fit separately.
- A second real tile with 1,283 invalid P0 radar pixels retained exactly 1,283
  unknown output pixels after stitching; every valid pixel retained finite
  probabilities. This checks the masked-edge path beyond the all-valid pilot.
- The pilot recovered exact checkpoint hashes from previously verified Azure
  bundles; no model was silently replaced. Test and compilation checks pass.
  Source label files were not edited. New scripts write separate raw/processed/
  results paths, leaving historical runs and other chapters untouched. The
  temporary 7.2 MB one-band pilot copy and the two newly downloaded Azure
  recovery archives (~521 MB together) were removed after the triplet and
  recovered checkpoint hashes were verified; the checkpoints and Azure blobs
  remain available.

## Remaining work in these steps

The single-product triplets are ready for paired inference. A small
same-chain multi-product mosaic is not asserted equivalent to the released
composite, so the 203 metadata-candidate tiles outside the simple triplet
subset remain an explicit coverage category. Local Dutch/German receiving cases
still need their own fixed image/label ledger. The full-tile inference pilot
establishes mechanics, not external accuracy or operational usefulness.

Sources: [GEOID-Flood dataset card](https://huggingface.co/datasets/links-ads/geoid-flood),
[Earth Engine Sentinel-1 processing](https://developers.google.com/earth-engine/guides/sentinel1),
[Earth Engine small-image export](https://developers.google.com/earth-engine/apidocs/ee-image-getdownloadurl).
