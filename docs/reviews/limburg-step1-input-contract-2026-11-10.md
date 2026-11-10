# Limburg step 1 — SAR input and reference contract

Internal engineering/scientific audit. No external accuracy or benefit estimate.

## Findings from held files

- The held Flood-S1 source contains four ordered radar channels: earlier VV/VH,
  event VV/VH, on co-registered 224 × 224, 10 m grids. Sample raw values are
  positive float32 linear intensity, often above the model's 0.15 clip. The
  publisher's loader applies that clip to the learned input. The source rasters
  do **not** contain a tag proving sigma0 versus gamma0 or the complete terrain/
  speckle processing chain. Their origin must be described as held processed
  Flood-S1 imagery, not silently equated to a new GRD product.
- The pinned GEOID v1.1 card calls `s1grd` linear sigma0 VV/VH, pre/post, on a
  common 1024 × 1024 10 m grid. GEOID RTC is a different product. Its loader's
  dB normalization is **not** the Copernicus-FM author normalization used for
  Flood-S1. The adapter must accept GEOID linear values and apply the frozen
  Copernicus-FM clip, means and standard deviations; target statistics cannot be
  refitted from held-out labels or target images.
- The earlier physical-control adapter inverted Copernicus model normalization
  after clipping at 0.15. That reconstruction is inadequate for a conventional
  SAR comparator: strong land backscatter is truncated. The new chapter's
  physical input uses un-clipped raw linear values, converts valid positive
  values to dB and leaves zeros/nonfinite pixels unknown. Historical analyses
  are retained as historical; no previous score is silently amended.

## Declared comparison contract

1. P0 is the delivered pre-event image. P1 is the latest *newer* pre-onset image
   with the same platform, relative orbit, direction, processing/calibration,
   resampling/grid procedure and nominal tile coverage. The event image stays
   fixed. Selection reads acquisition metadata only. No label or score informs it.
2. A `processing_contract` identifier must represent the entire image chain,
   not just a name such as `GRD`. For external P1, compare actual tags, source
   product IDs, calibration/correction, pixel scale, nodata and geolocation to
   delivered P0. If the delivered chain cannot be replicated, reproduce *both*
   P0 and P1 through one chain and report that paired subset separately. Do not
   call a mixed-chain contrast an age effect.
3. The learned pipelines use the same source-selected normalization, labels,
   train/validation partition, source-only hyperparameters and three seeds.
   P0/P1 replace only the pre-image and its acquisition-date metadata. The
   physical comparator uses the same raw acquisitions and geometric valid
   footprint but does not inherit the neural clip.
4. Fixed target: three classes (0 background, 1 permanent water, 2 flooded
   water), with 255 and invalid pixels ignored. Keep the CEMS floodmask and
   permanent-water masks separately for label-composition diagnostics. P0 and
   P1 are scored against the *same* target and paired valid support; P0 coverage
   and P1 availability are also reported for the full released cohort.
5. Choose one source-calibrated physical SAR change rule with raw dB VV/VH,
   source-only threshold search and a declared local speckle/noise convention.
   It is a transparent physical comparator, not the operational Global Flood
   Monitoring system. The conventional method's threshold is frozen before
   external labels are opened for scoring.

## Checks completed and remaining

`src/limburg_chapter_sar.py` implements label-blind P1 choice and raw dB
conversion with unit tests. Held source grid and numeric sample were inspected;
the pinned GEOID card and author loader/config were read. This establishes an
explicit *test* for cross-dataset input compatibility, not proof it already
passes. Target GeoTIFF header/tag audit, source/target distribution comparison,
and a same-chain P0/P1 processing check require the step-2 rasters. The physical
spatial noise convention and its source-only calibration are step-4 work.

### Step-1 code/data/chapter cleanup

No historical data were deleted or rewritten. The new raw physical-input path
is separate from previously scored, clipped source features; no old estimates
are rebranded. The active chapter plan and input contract use only the chosen
three pipelines/two reference policies. The first target acquisition will test
the unresolved radiometric claim before full-cohort inference.
