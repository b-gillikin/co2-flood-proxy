# DISE adaptation: completed preparation and one-fold benchmark

16 November 2026. Internal research aid; no dissertation prose. Independent
adaptation accepted by Brian. The source authors' unavailable code is not a
dependency. No full regional comparison has launched.

## Completed

- Verified HTTP byte-range access to the **15,149,654,797-byte** CAMELS-DE-1h
  ZIP. Acquired its station/catchment geometry and attribute tables without
  mirroring the archive. The metadata-only pass transferred about 34.3 MiB.
- Assembled a candidate census: **286 donor candidates**, **49 external
  candidates** (Sieg 27, Erft 16, Ahr 6), **52 boundary-overlap review cases**,
  four local-overlap exclusions and 1,220 outside-domain records. These counts
  precede model-reach, quality and independence checks. Nested gauges are not
  independent rivers. Do not call this a frozen training cohort.
- Selected the lexicographically first donor candidate, DE110470, without
  examining outcomes; downloaded and CRC/checksum-verified its individual CSV.
  It contains 210,383 hourly rows and 27 columns, including discharge and
  meteorology. This establishes selective series access, not valid training
  labels. Its primary documented timestamp/interval convention still needs
  verification before external aggregation.
- Built local daily observed/model discharge for all seven gauges, preserving
  strict quality as a separate field. There are 40,908 gauge-days in 2010–2025,
  including **39,808 complete observed/model pairs**. No missing observations
  were reconstructed to create these labels.
- Retrieved catchment-specific ERA5-Land daily weather for **2017–2025**. The
  nine tables total approximately **1.77 MiB**. They cover precipitation,
  temperature/dewpoint, pressure, wind components and downward radiation.
  One annual stacked-band spatial aggregation avoids Earth Engine's concurrent
  aggregation limit encountered with one reducer per day.
- Built a common conventional-attribute table from SRTM terrain, **2017**
  Copernicus Proba-V tree/crop/urban fractional cover and OpenLandMap surface
  field capacity. The first CORINE-2012 preparation is retained but superseded:
  the benchmark uses the 2017 table so an older land-cover vintage is not an
  avoidable advantage for 2017 AlphaEarth. Tree cover is not a forest land-use
  class; surface field capacity is not root-zone storage or permeability.
  Regulation remains unknown and was not coded as absence of dams.
- Joined the verified 2017 AlphaEarth metric-grid means. Geometry source checksum
  agrees with its original geometry receipt. All 64 embedding inputs are finite.
- Prepared **20,454 gauge-days for 2018–2025**, with **19,538 observed/model
  pairs** and no missing current/lagged feature cells. This includes non-high-
  water days; it is not a selected storm sample. Daily support tables preserve
  every missing verification day and the clean-verification distinction.
- Checked polygon intersections: material local overlap is confined to the
  three Wurm catchments, which are held together in the benchmark. ERA5-Land's
  native coarse-grid fractional rasterization yields sampled areas slightly
  different from vector areas; retain this support diagnostic, not an assertion
  of fine-resolution rainfall observations.

## Completed fitting benchmark

An **entire local held-Wurm 2021 outer fold** ran with all four learned feature
sets, four hyperparameter candidates, four inner held-river validation folds
and three final seed refits: **76 fits**. The fit/tuning/refit pipeline completed
in **13.44 seconds**; its median individual fit was **0.133 seconds**.

Training: 2,723 rows from 2018–2019 on Geul, Gulp, Voer and Geleenbeek.
Validation: 1,222 rows from 2020, with the inner validation river absent from
its fitting set. Final selected-model refits use allowed pre-test observations.
Test: **1,068** Wurm gauge-days in 2021, across Rimburg, Herzogenrath 1 and
Randerath. The first seven test days are purged for lag separation; no held
regional storm spans these particular split boundaries. All Wurm gauges are
absent from both fitting and tuning. Held-river historical thresholds are
evaluator-only. No output was nonfinite and no negative reconstructed discharge
needed flooring in this fold.

This is a completed **local** validity/cost benchmark, not a benchmark at the
larger regional training size. It lacks the planned regional donors, full
year/river evaluation, calibration references and uncertainty/measurement
sensitivities. Its saved descriptive scores are not the chapter's conclusions;
do not change the design based on this single fold. It does establish that
cached-descriptor fitting needs no GPU or weeks-long encoder extraction.

Results and complete receipts:
`results/limburg_dise_v1/benchmark_local_wurm_2021/`.

## Audit and recovery

**30 relevant tests pass**, including daily midnight/gap/zero handling, river
weights, held-river exclusion, range-download safety, model serialization and
existing GEOGLOWS tests. Ruff and the isolated dependency check pass. Preparation
source hashes and all completed benchmark input/output hashes were reverified.

The isolated `.venv-dise` pins XGBoost 3.1.2 and scikit-learn 1.7.2. Inherited
scikit-learn 1.9 caused an XGBoost estimator-type serialization error during the
first attempt; that incomplete attempt is retained separately, marked failed. A subsequent
startup import error is also retained separately; neither is the completed run's
current status. Prediction/model bytes were unchanged by this error-record
housekeeping.
Package versions now enter checkpoint identity and model-save/reload has a
regression test. The original research environments were not modified.

Source and code receipts make interrupted fits detectable; per-candidate tuning
records can resume when identities agree. A failure is recorded, not silently
replaced with a successful draw. No email alerts, VMs or cloud jobs were enabled.
Source acquisition is separately resumable by verified file/year.

Measured free disk: **79.34 GiB** at audit, about **29.34 GiB** above reserve.
New raw data: **67.15 MiB**; new results/preparation: **20.99 MiB**, excluding
the small isolated environment. No offload, deletion or other-chapter data change
was needed. Recheck space before acquiring the full eligible regional census.

[Machine-readable audit](reviews/limburg-dise-preparation-audit-2026-11-16.json).

## Next work before the full comparison

1. Match regional candidates to GEOGLOWS reaches using topology, drainage area
   and upstream polygons; resolve boundary-overlap cases. Finalize separate
   donor and reserved external membership without inspecting prediction errors.
2. Verify CAMELS-DE-1h hour/UTC and missing/quality conventions from its primary
   documentation; acquire the eligible series by member, preserving metadata
   and checksums. Obtain matched model discharge, common forcing summaries and
   AlphaEarth summaries. Do not use CAMELS hydrological signatures or benchmark
   predictions as covariates.
3. Resolve regulation metadata and conventional-attribute limitations consistently
   across local and regional polygons. Add the declared calibration references
   and full evaluation/uncertainty outputs to the regional runner. The local
   benchmark is not that complete runner.
4. Benchmark one fold at the actual regional training size, then schedule the
   full chronological and cross-river comparison with two CPU workers. The
   earlier 1–4-day allowance is conservative and unmeasured at that scale; the
   local 13-second result does not justify a precise full-study ETA.

The three-stage design remains: local reference, same-river global-model
correction, then reserved external rivers. No favourable-result gate is added.
