# Current data needs — four catchment representations

Updated 23 November 2026. The AlphaEarth and TESSERA comparisons are complete.
StefaLand and Basin2Vec are pending compatible artifacts. [Design audit](limburg-representation-extension-audit-2026-11-18.md),
configuration: `config/limburg_representation_extension_v1.json`.
[Native-use review](limburg-representation-correct-use-review-2026-11-18.md)
specifies each encoder's input/output conventions. For TESSERA's selected
Icechunk store, NaN scales are source nodata, not verified water. StefaLand
also needs a verified normalization, sequence and missing-channel recipe;
Basin2Vec needs its final projected/L2-normalized output, not an auxiliary state.

| Required input | Held / outstanding | Acquisition route and purpose |
| --- | --- | --- |
| Observed Q, qualifications, GEOGLOWS, core weather, existing conventional attributes and 2017 AlphaEarth | Held for the existing local/regional populations | Reuse audited inputs. No further René/Jens request needed for this design |
| Common reference polygons | Held; 394 processing polygons inventoried | Seven local, 337 donor and 50 reserved external; preserve existing mapping strata. Three self-touching geometries repaired only in a new processing copy, topologically equal to their originals |
| 2020 AlphaEarth and TESSERA descriptors | Validated for all 394 gauge records; 64 and 128 dimensions respectively | Reuse matched 2020 inputs. TESSERA minimum area coverage is 99.67%. The 2018 TESSERA table is an alternate. |
| Intended StefaLand encoder/descriptor recipe | Compatible export or checkpoint outstanding | Exact 256-dimensional runoff-free variant and Dutch/German catchment coverage remain to verify. A matching 2020 catchment export would suffice |
| Basin2Vec trained encoder and exact schema | Compatible checkpoint outstanding | The tagged source archives contain an evaluation variant's channel list. The deployed U.S. atlas yields a verified reference vector. Verify the trained encoder, exact preprocessing and a prepared input for that reference case |
| StefaLand physical/weather inputs | Partial: existing core weather/attributes; exact additions depend on verified schema | Likely extrema/PET and richer vegetation/soil/geology. Paper and candidate schemas differ; verify units, sources and history before downloading guessed inputs |
| Basin2Vec monthly/static gridded patches and geometry metadata | Partial source families held; native patches not assembled | Candidate sources include E-OBS or ERA5-Land and a CORINE-to-NLCD crosswalk. Treat subsurface agricultural drainage as a separate sensitivity if the checkpoint supports a documented substitution or missingness treatment. Use existing 394 polygons and document real source resolution |
| Matched enriched conventional controls | C1 and C2 complete for AlphaEarth and TESSERA | For these two pending encoders, inventory the extra raw input families and add their conventional summaries to the shared control once the native recipes are known |

Use 2020 as the shared pre-evaluation satellite reference year for the extension.
Record the actual vintage of each conventional control and match annual inputs
to 2020 where the source supports it.
Use a documented pre-evaluation history where a native encoder requires it.
Exclude full-record observed-flow signatures and test-year landscape averages.
The exact snow/soil files already held are not assumed to cover every regional
polygon or satisfy either model's native definition. Retain native descriptor
dimensions; no extra local labels, surveys, flood maps or operational replay
logs are required for this comparison. The [release audit](limburg-representation-correct-use-review-2026-11-18.md#release-check--20-november-2026)
records the inspected artifacts and what needs verifying on receipt.

## Held-input audit for C1 — 20 November 2026

The [audit runner](../scripts/290_audit_c1_held_inputs.py) checked the actual
files against their saved checksums, keys and dates. It covered 394 gauge
records and their reference polygons, including all seven local, 337 donor and
50 reserved external gauges. The output receipt is
`results/limburg_representation_extension_v1/c1_held_input_audit.json`.

| Source | Coverage and units | Use for the next comparison |
| --- | --- | --- |
| ERA5-Land daily catchment weather, 2017–2025 | All 394 gauges and 1,295,078 unique UTC gauge-days. All eight fields finite. Rain in m per day, mean temperature and dew point in K, pressure in Pa, wind components in m/s, accumulated shortwave and longwave energy in J/m² per day. | Reproduced 2020 annual rainfall totals, wet-day counts and means across all gauges. Monthly and seasonal summaries are also available from the daily calendar. Daily mean temperature alone cannot recover daily extrema. [Source bands and units](https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_LAND_DAILY_AGGR) |
| Existing terrain, land cover and field capacity | All 394 gauges have SRTM v4 mean elevation in m and slope in degrees, 2017 Copernicus tree/crop/urban fractions on 0–1, and OpenLandMap v01 surface field capacity in volumetric %. The common 100 m reduction uses 93.98–100.01% of the processing polygon area, with slight excess from gridded area estimation. | Reuse these existing C0 controls with their actual vintages. Field capacity is a static 0 cm proxy. Soil texture, permeability and dynamic soil moisture are different quantities. [SRTM](https://developers.google.com/earth-engine/datasets/catalog/CGIAR_SRTM90_V4), [land cover](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_Landcover_100m_Proba-V-C3_Global), [field capacity](https://developers.google.com/earth-engine/datasets/catalog/OpenLandMap_SOL_SOL_WATERCONTENT-33KPA_USDA-4B1C_M_v01) |
| Reference polygons | All 394 valid in the equal-area processing CRS. Area, perimeter and compactness checks are finite for every gauge. | Can derive common geometry summaries now. Check artifact-specific metadata definitions before using these in a native encoder. |
| Hourly ERA5-Land soil moisture and snow, 2009–2025 | All 204 monthly files verified, with all 8,784 hours in 2020 checked. The 0.1° grid fully covers seven local and three donor polygons, partly covers 15 donors and overlaps no reserved external polygon. Soil moisture is m³/m³ and snow is m water equivalent. | Suitable for local context. Full-cohort physical-state summaries or native snow grids require more consistent coverage if included. |
| Hourly ERA5-Land temperature, dew point and pressure, 2001–2025 | All 300 monthly files verified, with all 8,784 hours in 2020 checked. The 0.1° grid fully covers 33 polygons, partly covers 20 and misses 341. Variables are K, K and Pa respectively. | Can derive daily temperature extrema on covered catchments. A shared full-cohort extrema or PET block requires common inputs and defined aggregation. |
| Held Copernicus GLO-30 tiles | Four tile footprints fully cover 65 polygons and partly cover 34. Coverage is based on file footprints. | Useful for local terrain or a pilot. Keep the common SRTM summaries when comparing the full cohort unless the replacement terrain is harmonized across it. |
| CAMELS-DE-1h supplemental inputs | All 387 nonlocal gauge IDs join directly to the static tables, including CORINE 2018 classes, SoilGrids250m and German hydrogeology. All 387 hourly files have weather columns. Their per-hour completeness was outside this audit. | Useful for regional cross-checks and source comparisons. The local gauge IDs use a different identity system. The hourly meteorology uses German products with different coverage and definitions. The temperature min/max columns are spatial extrema at each hour. Keep full-record observed-flow attributes out of predictor blocks. [CAMELS-DE-1h documentation](https://essd.copernicus.org/preprints/essd-2026-289/) |
| GEOGLOWS, observed discharge, and tested descriptors | The preparation table retains 1,151,268 modelled discharge values in m³/s across 2018–2025. Regional reference observations end in 2024. All 394 AlphaEarth and TESSERA 2020 vectors passed the hash, key and finite-value checks. | Reuse the completed split and verification inputs. Preserve known observation gaps and source qualifications. |

The held daily weather and polygons support a held-data C1 benchmark using
seasonal climate and simple geometry summaries. This enriches the summaries
of existing data. It does not add new raw source families. Record whether the
weather summaries are past-only per fold, as in C0, or use a fixed 2020
reference in the explicitly retrospective comparison. A fixed 2020 weather
block includes information from after some earlier fitting dates.

The full four-product C1 recipe still depends on the verified encoder inputs.
The held summaries do not recover the spatial patches for Basin2Vec. If the
exact artifacts require more data, prioritize harmonized catchment-wide
inputs for the documented channels. No feature table was adopted, no fitting
was started and no new datasets were downloaded in this audit.

To reproduce from the chapter directory:

```sh
PROJ_DATA="$HOME/miniforge3/envs/chapter1-co2/share/proj" \
  .venv-dise/bin/python scripts/290_audit_c1_held_inputs.py
```

The two validated 2020 extraction directories occupy about 14 MiB including
receipts and checkpoints. The Geul benchmark has a roughly 793 MiB materialized
feature table. Keep it with the completed run for replay and join future compact
descriptor tables at fit time to avoid accumulating copies.

## One-fold C1 benchmark — 20 November 2026

The [runner](../scripts/291_prepare_c1_benchmark.py) prepares the existing
held-Wurm 2021 fold with the same eligible rows and assignment. It retains
233,001 2018–2019 training rows, 115,829 2020 validation rows and 1,089
eligible 2021 Wurm gauge-days. The new run identity keeps these fits separate
from the archived C0 estimates. Wurm 2021 was selected for the benchmark
because an existing TESSERA tuning fit on that split reached the tree cap.

The held-data C1 extends C0 with seven transparent predictors. Five come
from the previous complete UTC calendar year, using 2017 weather for 2018
rows through 2020 weather for 2021 rows: wet-day fraction and wet-day mean
intensity at a 1 mm/day threshold, October–March share of annual rainfall,
and mean daily temperatures in the December/January/February and June/July/
August months within that reference year. Catchment perimeter and compactness
come from the audited equal-area polygons. These are summaries of held inputs;
the 2020 EO descriptors are fixed retrospective basin attributes. The C1
columns have their own prefix so the existing donor FDC matching inputs are
preserved.

The sidecar contains 1,576 gauge-year rows. A validation-only probe uses the
same candidate and inner split that capped in the prior TESSERA fit. A single
4,500-round search per arm measures the best score through 3,000 trees and
whether validation RMSE improves beyond that point. The probe sees only
permitted training and validation rows. Its scope is one capacity stress case.
The full outer fold retains both policies, four candidates, four inner folds
and three final seeds per arm, totalling 114 fits. Apply one shared cap and
retain the existing high-water, clean high-water and all-day scoring.

| Capacity probe arm | Best round | Stopped after |
| --- | ---: | ---: |
| C1 | 696 | 746 |
| C1 + 2020 AlphaEarth | 1,679 | 1,729 |
| C1 + 2020 TESSERA | 1,515 | 1,565 |

All three triggered early stopping before 3,000, so use the existing shared
3,000-tree cap for the full held-data benchmark. Check the selected fits for
cap hits after the full tuning grid runs. The launch check reproduces the
1,089 archived test gauge-day keys exactly and verifies 111, 175 and 239
declared predictors in the three arms. Twenty-four existing DISE tests pass.

Preparation and probe receipts are under
`results/limburg_representation_extension_v1/c1_held_benchmark_v1/`.
`prepare` writes the compact conventional sidecar, `probe` runs the capacity
diagnostic and `run` explicitly launches the full held-data fold. The outer
fold completed on 20 November. All 114 fits and 161 saved output hashes were
verified. Two tuning fits reached the shared 3,000-tree cap. Neither was
selected. The completion manifest is `fit/jobs/held_Wurm_2021_c1_held/manifest.json`
beneath the same directory.

### Matched results and chapter implications

The table uses the primary tuning policy and gauge-balanced daily MAE in
mm/day. Every C0 and C1 entry uses the same gauge-days, observations, model
values, threshold flags and clean-verification flags. Scores were independently
recomputed from the predictions. The second tuning policy gives the same
ordering among the three C1 arms in each stratum.

| Model | All days (1,089 gauge-days) | High water (21) | Clean high water (14) |
| --- | ---: | ---: | ---: |
| Raw GEOGLOWS | 0.724 | 6.327 | 5.395 |
| C0 | 0.563 | 6.324 | 3.622 |
| C0 + AlphaEarth 2020 | 0.468 | 6.689 | 4.109 |
| C0 + TESSERA 2020 | 0.651 | 6.932 | 4.309 |
| C1 | 0.615 | 6.687 | 4.111 |
| C1 + AlphaEarth 2020 | 0.538 | 6.902 | 4.356 |
| C1 + TESSERA 2020 | 0.737 | 7.243 | 4.531 |

C1 raised error relative to C0 in all three strata in this fold. Adding
AlphaEarth to C1 improved all-day MAE by 12.38% and worsened high-water MAE
by 3.22%. Adding TESSERA worsened those outcomes by 19.90% and 8.31%.
Raw GEOGLOWS had lower MAE than all C1 arms on the full high-water subset.
All C1 arms had lower MAE than raw GEOGLOWS on the clean subset, with C1
alone leading among them. All four raw/C1 predictions underestimated the
observed value on each of the 21 high-water gauge-days. Those rows span
nine dates on one held river, including six July 14–16 rows outside the clean
subset. The fold supports a matched capacity and robustness check. The
multiyear results carry the chapter-level performance claims.

This Wurm benchmark preceded the completed 30-fold C1 and C2 comparisons.
Use the [consolidated evidence review](reviews/limburg-c2-findings-2026-11-23.md)
for multiyear estimates and current interpretation. The encoder artifacts affect
only the pending additional comparisons.

---

## C2 source pilot — 20 November 2026

C2 extends the conventional information shared by every model. The planned
contrasts are C2 alone, C2 plus 2020 AlphaEarth, and C2 plus 2020 TESSERA, with
the same chronological and river-group splits as C1. Evaluate high-water MAE
first and retain all-day and clean high-water MAE. C2 feature definitions and
coverage rules are chosen from physical meaning and source support before
scoring it.

| Input | Proposed use | Pilot |
| --- | --- | --- |
| ESA WorldCover 2020 v100 | Class-area fractions on reference polygons, emphasizing built-up, cropland, grassland, forest and wetland. Fixed 2020 retrospective landscape snapshot. | Valid native pixels at all three pilot polygons. [Product](https://developers.google.com/earth-engine/datasets/catalog/ESA_WorldCover_v100) |
| SRTM v4 terrain | Add within-basin relief, such as the difference between the 90th and 10th elevation percentiles, alongside the existing means. | Valid native pixels at all three. [Product](https://developers.google.com/earth-engine/datasets/catalog/CGIAR_SRTM90_V4) |
| SoilGrids v2 texture | Add interpretable topsoil texture summaries. Retain the stated depths and convert mapped units before use. | Both selected clay depths have valid pixels at all three. [ISRIC access and variables](https://docs.isric.org/globaldata/soilgrids/access_on_gee.html) |
| ERA5-Land prior-day state | Add volumetric soil water by layer and snow water equivalent. Use only the previous UTC day's state for each evaluated date. | A January 2020 day returned two or three native grid cells per pilot polygon. These coarse data describe broad antecedent conditions. [Product](https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_LAND_DAILY_AGGR) |

The pilot used Limburg gauge `10.Q.29`, donor `DE110470` and reserved gauge
`DEA10040`. These were the first records in each role in the polygon inventory.
Counts show that queries return data. The next audit measures valid weighted
area on all 394 polygons and checks daily coverage, unit conversions and the
lagged join. Preserve missing cells separately from physical zero, including
zero snow. Existing C1 uses audited held inputs. The C2 pilot did not fit a model.

**C2 execution, 21 November 2026.** Use all 11 WorldCover classes as area
fractions of valid mapped area, SRTM elevation P90 minus P10, and the SoilGrids
mean clay percentage at 0–5 and 5–15 cm. Daily ERA5-Land inputs are the four
volumetric soil-water layers and snow water equivalent in millimetres, each
from the previous UTC day. Sample all sources on the pinned reference polygons
at native grids and retain valid area. Missing predictors remain missing in
all arms. The daily join uses the 31 December 2017 through 30 December 2025
source dates. These are retrospective reanalysis inputs. The lag specifies
the dates used for fitting and does not establish real-time availability.
The production preflight verified the terrain area output, the SoilGrids
native Mollweide grid, and all five daily variables over the 2020 leap year
at the three pilot catchments. The first extraction was restarted after
correcting the terrain reducer output name and accepting the SoilGrids CRS
in WKT format. First-attempt batches are retained with their original receipts.
Full extraction then completed for all 394 catchments and 1,151,268
catchment-days. Finalization initially rejected tiny negative snow equivalents
(minimum about −7.35 × 10⁻²² mm). The corrected finalization verified and reused
all 259 batch receipts, mapped only negative residues within 10⁻¹² mm of zero
to zero, and retained the original tables. It recorded 792,301 corrections
and no missing C2 predictor values. No source data were downloaded again.
[ISRIC texture units](https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs_01.html),
[ERA5-Land band definitions](https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_LAND_DAILY_AGGR).

## StefaLand and Basin2Vec pilot preparation — 22 November 2026

The [pilot audit](../results/limburg_representation_extension_v1/encoder_pilot_2020/pilot_audit.json)
records the pinned EPSG:3035 polygon bounds and area intersections with the
native 0.1° ERA5-Land grid. The three largest cells cover 94.9% of Cottessen,
which limits the spatial detail of the proposed weather inputs. The cell
counts include small polygon-edge intersections. The percentages refer to
the archived hourly grid footprint, with daily catchment means available
for all three. [Held weather and geometry audit](../results/limburg_representation_extension_v1/c1_held_input_audit.json)

| Pilot gauge | Role | Polygon area (km²) | Intersecting ERA5-Land cells | Held hourly temperature and snow footprint |
| --- | --- | ---: | ---: | ---: |
| Cottessen `10.Q.29` | Local | 121.38 | 5 | 100% |
| Meckesheim `DE110470` | Donor | 257.79 | 9 | 0% |
| Weidenau `DEA10040` | External | 134.56 | 8 | 0% |

The [Cottessen source sample](../results/limburg_representation_extension_v1/encoder_pilot_2020/cottessen_era5_land_daily_2020.parquet)
contains 1,830 cell-days, covering all 366 UTC days and five native cells.
It includes daily temperature extrema in °C, vapour pressure in Pa, relative
humidity in percent, and snow water equivalent in mm. The
[audit runner](../scripts/296_verify_encoder_pilot_inputs.py) checks all 24
monthly source checksums, native cell coordinates, units and hourly calendars.
Vapour pressure is derived from hourly dewpoint and relative humidity from
hourly vapour pressure and air temperature, then averaged within each UTC day.
Daily snow storage is the mean of the hourly values. Values between
−10⁻¹² mm and zero are handled with the C2 round-off rule. The sample is
source data for evaluating the candidate crosswalk. The released model's
input recipe determines the final preprocessing.

### Basin2Vec crosswalk for Cottessen

The archived evaluator lists five monthly channels. The paper also lists
shortwave radiation among the candidate monthly inputs and agricultural
drainage among the static inputs. Preserve daily inputs through preprocessing
and match each monthly reducer to the delivered checkpoint's recipe.
[Paper input table](https://arxiv.org/html/2611.05164v1#A2.T2) ·
[Daymet definitions](https://daymet.ornl.gov/overview) ·
[ERA5-Land bands](https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_LAND_DAILY_AGGR)

| Channel or input group | European pilot source and handling | Remaining check |
| --- | --- | --- |
| `prcp` | ERA5-Land total precipitation. Convert m/day to mm/day. Keep both daily rate and monthly total until the reducer is confirmed. | Basin means are held. Acquire native pixels when the patch recipe is confirmed. |
| `tmin`, `tmax` | Held hourly ERA5-Land extrema at Cottessen. The daily collection also supplies `temperature_2m_min` and `temperature_2m_max` in K. | Check daily window and monthly averaging against the reference. |
| `vp`, `swe` | Use vapour pressure derived from hourly dewpoint and daily mean snow storage from the Cottessen sample. One mm of water equivalent corresponds to one kg/m². | Confirm the required snow sampling convention and monthly reducers. |
| Shortwave radiation, if used | ERA5-Land downward shortwave daily energy. Daymet's flux averages over daylight hours. Keep daily energy and match the averaging period before converting to W/m². | Verify the checkpoint uses this channel and document the Daymet-to-ERA5-Land difference. |
| Terrain and soil | Use SRTM elevation and SoilGrids bulk density, clay, sand and silt as candidate native grids. Retain source units and depth bands. | Confirm depth aggregation and scaling. The archived evaluator's `slit` label needs confirmation. |
| Land cover | Use CORINE 2018 as the documented pre-2020 land-cover snapshot. Preserve class codes and mask during reprojection. | Confirm the NLCD encoding, crosswalk and treatment of unresolved classes. |
| Other static channels | GLHYMPS 2.0 is a candidate for permeability and hydraulic conductivity. PET, soil organic carbon, wind and population need the checkpoint's version and units. | Verify source, depth, transform and vintage for each enabled channel. Agricultural tile drainage remains unresolved where required. |

The working CORINE-to-NLCD mapping is a semantic starting point. Candidate
labels use the published legends and remain provisional until the model
preprocessing is confirmed. Quantify the area in each retained and unresolved
class on the native raster before testing the mapped patch.
[CORINE legend](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_CORINE_V20_100m) ·
[NLCD legend](https://www.mrlc.gov/data/legends/national-land-cover-database-class-legend-and-description) ·
[SoilGrids units](https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs_01.html) ·
[GLHYMPS 2.0](https://doi.org/10.1002/2017GL075860)

| CORINE codes | Candidate NLCD code | Mapping limit |
| --- | --- | --- |
| 211–213, 221–223 | 82, cultivated crops | Groups arable land and permanent crops under the broader NLCD class. |
| 231 | 81, pasture/hay | Approximate match for managed pasture. |
| 311, 312, 313 | 41, 42, 43, respectively | Broad-leaved and coniferous classes approximate deciduous and evergreen forest. Check leaf habit and mixed-forest thresholds. |
| 321 | 71, grassland/herbaceous | Approximate match for natural grassland. |
| 332, 335 | 31, 12, respectively | Candidate bare ground and perennial ice/snow. |
| 511, 512 | 11, open water | Narrow channels may be omitted by CORINE's mapping rules. |
| 111–142, 241–244, 322–324, wetland and other unlisted codes | Unresolved | Developed intensity depends on impervious cover. Mixed agricultural, shrub and wetland categories need a checkpoint-specific choice or mask. |

For grid alignment, use the pinned basin polygon and keep its EPSG:3035
bounding box, fractional-area cell intersections, and each native raster
transform. Once the author recipe is available, build the common grid and
mask with its exact crop, padding and cell-center convention. Use continuous
resampling suited to the variable and categorical resampling for land cover.
Keep outside-basin and source-missing masks separate from physical zeros.
Record the source resolution and the effective patch-pixel size separately.
BASINGRID's 64 × 64 grid standardizes array size across different basin
extents. Apply the checkpoint's geometry fields, log transforms and training
statistics to the verified polygon metadata. [BASINGRID data and grid design](https://zenodo.org/records/19358585)

### StefaLand forcing inventory

The StefaLand pretraining report lists six daily forcings. The archived
checkpoint's time-series projections are precipitation, temperature extrema,
PET and runoff. The requested 256-dimensional runoff-free artifact determines
which specification applies. [Pretraining forcings](https://arxiv.org/html/2509.17942v3#A3.SS4) ·
[Local checkpoint inspection](../data/raw/limburg_representation_extension_v1/review_sources/stefaland-checkpoint-schema-inspection.json)

| Published forcing | Verified holding or candidate | Remaining preparation |
| --- | --- | --- |
| Precipitation | Daily ERA5-Land catchment means in m/day cover all 394 gauges. | Confirm the required source and convert to the recipe's units. The paper uses MSWX and MSWEP-derived forcings. |
| Downward shortwave radiation | Daily ERA5-Land catchment energy in J/m²/day covers all 394 gauges. | Confirm whether the recipe expects accumulated energy or mean irradiance and its averaging window. |
| Relative humidity | Hourly temperature and dewpoint support the Cottessen pilot calculation. Daily means of temperature and dewpoint are held across the cohort. | Confirm percent versus fraction and whether to derive humidity from hourly values before aggregation. |
| Maximum and minimum air temperature | Verified hourly extrema at Cottessen. The regional daily ERA5-Land extrema bands are available for follow-through. | Check the author time window and derive or acquire matching fields for Meckesheim and Weidenau. |
| Potential evapotranspiration | Cottessen has the needed temperature range and latitude for a Hargreaves pilot. | The final series depends on the artifact's PET equation, radiation convention and units. |

The held geometry, terrain and selected land-cover/soil summaries support
initial static checks. Match depth, source and summary definitions for the
author's static attributes, including vegetation, soil and hydrogeology,
before deriving the final inputs.

### Checks when artifacts arrive

- **Basin2Vec.** Reproduce the final normalized 64-coordinate vector for
  USGS `04101500` in 2018 using the supplied checkpoint and prepared input.
  Compare all coordinates with the [saved atlas output](../data/raw/limburg_representation_extension_v1/review_sources/release_resolution_2026_11_20/basin2vec_atlas_us_reference.json),
  report the maximum absolute difference and check the vector norm.
  Then use Cottessen to check European source substitutions and mask
  alignment, and use the donor and external pilots to check coverage.
- **StefaLand.** Verify the runoff-free variant, pretraining years and
  footprint, forcing definitions and order, native normalization,
  context window, feature layer and annual pooling. Reproduce a supplied
  reference example. For a 2020 export, verify gauge and polygon identity,
  date coverage, provenance, and the finite 256-coordinate schema.
- **Matched evaluation.** Record the new raw input families shared with the
  conventional comparator. Verify one matched fold before expanding to
  all 394 catchments.

---

# Completed AlphaEarth-only acquisition — DISE-inspired reconstruction

Updated 16 November 2026. [Implemented corrections and current inventory](limburg-dise-audit-corrections-2026-11-16.md).

| Input | Current status / remaining work |
| --- | --- |
| Local Q/qualifications | Held; daily observed/model reference and separate clean flags assembled |
| Local AlphaEarth | Held; fixed 2017 means selected, seven target catchments |
| Local weather | Acquired: 2017–2025 catchment-specific ERA5-Land daily summaries |
| Conventional local descriptors | Acquired: common terrain, 2017 land-cover fractions, surface field-capacity proxy; regulation coverage remains incomplete; exact-match no-dam evidence is not proof of no controls |
| Regional donor/external metadata | Acquired; 337 provisional donors and 50 external records after the bounded one-gauge resolution; original 44 flags and eight additional location conflicts have explicit analysis strata |
| Regional observations | Acquired and checksum-verified: original 386 records plus one-gauge supplement; 823,956 complete daily observations in 2018–2024; the original 12 no-overlap coverage cases remain |
| Regional GEOGLOWS/weather/AlphaEarth | Acquired and hash-verified for all 387 resolved mapped records (371 distinct reaches), including explicit mapping flags; same reference polygons, hourly model source, weather bands and 2017 metric-grid AlphaEarth convention as local inputs |
| CAMELS-DE-1h source clock/quality | Verified primary documentation: UTC, preceding-hour means; mixed provider QA and no exhaustive direct source QA. Unknown quality stays unknown; incomplete days stay missing |
| Additional local provider emails | None required for this preparation |
| Full imagery or new encoder weights | Not required for the completed AlphaEarth-only comparison; the current extension needs the inputs above |

Regional source snapshots use 3.66 GiB and daily tables 84 MiB; 74.8 GiB was
free at verification. Matched regional inputs are complete and hash-verified; all workers have
finished. Regional features are assembled and audited; the first regional-fold
benchmark has completed, with no additional input request. [Acquisition record](limburg-dise-regional-inputs-2026-11-16.md).
Current registers and assembled inputs: [completed spatial review](limburg-dise-spatial-resolution-2026-11-16.md).
The regional verification source ends in 2024; local 2025 verification remains
separate, and 2025 regional predictors do not supply missing labels.

The prior GEOGLOWS next-24h comparison is completed. Its dated inventory below
is historical, not the acquisition list for the current reconstruction study.

---

# Current data needs — corrected GEOGLOWS Stages 1–2

Updated 14 November 2026. [Active design](limburg-geoglows-stages12-protocol-v2-2026-11-14.md).

| Input | Status / role |
| --- | --- |
| Seven NL/DE tributary Q records and provider qualifications | Held; observed inputs, historical training and verification |
| Sint Pieter and Venlo Q | Held and matched to GEOGLOWS reaches; contextual inputs, not targets |
| Common rainfall and regional event clock | Held; unchanged across stages; all 481 regional episodes retained |
| Presto/AnySat raw and encoded context tables | Held, checksums verified; reuse without new imagery extraction |
| GEOGLOWS hourly Q, 2010–2025 | Downloaded, pinned and verified at nine active sites; UTC hour-end aligned |
| Full stream/catchment geometry | Held; topology, area and source identities checked |
| Eys | Excluded as target/predictor in both stages; original data retained. Not an outstanding request |
| New core data request | None needed for this retrospective specification |
| As-issued forecast/reforecast and arrival records | Not acquired; needed for a later operational replay, not assumed available |
| External European rivers / new EO campaigns | Stage 3 not launched; no new acquisition committed |

Corrected preparation has 13,468 opportunities per stage. Earlier mapping-study
inventory below is retained as historical/completed work.

--- | --- |
| NL/DE observed Q and measurement qualifications | Held; reference inputs, historical training labels and independent observed verification |
| Meuse observations | Held; contextual channels at Sint Pieter and Venlo, not new targets |
| Common rainfall and storm clock | Held; unchanged across stages |
| Presto and AnySat context/raw features | Held, selected compact table hashes verified; reuse exact completed contexts |
| GEOGLOWS RFS V2 hourly discharge | Downloaded for 2010–2025 at nine mapped input sites; interval-start labels shifted to hour end |
| RFS V2 stream/catchment geometry | Downloaded and audited against local catchments; nine selected reaches and rejected Eys nearest reach documented |
| Eyserbeek independent model discharge | Not represented in this network; structural coverage limitation, not a pending download. Keep channel missing, retain separate coverage case |
| Additional core data requests | None needed for this retrospective Stages 1–2 specification |
| As-issued forecast/reforecast inputs | Not acquired by this setup; needed for a future operational replay, not assumed present |
| External European gauges / new imagery | Stage 3 not launched; no download committed by current setup |

Earlier mapping-study inventory below is retained as historical/completed work.

---

# Limburg data needs — accepted chapter scope

Updated 11 November 2026. Source of truth:
[agreed study](limburg-chapter-sized-study-2026-11-10.md) and
[active pointer](../config/limburg_current_study.json).

| Input | Status | Role / remaining work |
| --- | --- | --- |
| Paired-SAR source images, labels and identities | Held: all 5,000 Kuro/Copernicus records across 20 events | Source training/selection; retain water-containing selection and check event separation, class/ignore semantics and selected fit compatibility |
| Selected Copernicus-FM weights, code and normalizers | Held; native full-tile inference smoke passed | Frozen paired-date encoder and head; final all-source refits use the held source-selected protocol |
| Existing source-trained states and fit manifests | All six final all-source states complete and hash-verified; source development retained | Source-only recipe fixed from five held folds; no additional fit needed |
| External SAR, label, validity, flood and permanent-water masks | All nine pinned shards downloaded and hash-verified; 1,301 grids audited | Nine heldout activations; delivered P0 plus targets are available; **9.068 GiB** in the [core manifest](../config/limburg_chapter_sized_geoid_acquisition_v1.json) |
| Updated pre-cutoff SAR (P1) | Metadata inventory and harmonized P0/P1/post acquisition complete for the primary paired subset | 1,118 label-blind metadata candidates; 915 single-product triplets, of which 913 were downloaded and independently verified. Of the 913 paired tiles, 447 match post-image geometry and 466 do not. Report the intended compatible population separately from the full catalogue; all dates share the harmonized processing chain. |
| Existing local SAR acquisitions and mapped references | Complete mapping/scoring: 167 scene/grid records and 14 radar acquisition cases | All pass geometry; 35 records have a reference update. One July 2021 episode; timing and source-dependent labels qualify interpretation |
| René/Jens gauge records and provider notes | Held | Local event timing and measurement context only. They do not define flooded pixels or require a new discharge model |
| Recovery manifests and existing source backups | Retained | Verify any new transfer/cache before cleanup. Historical large imagery may require documented Azure restoration only if actually needed |

## Response-mapping continuation — 12 November 2026

**Later assessment:** [the plan audit](reviews/limburg-response-mapping-plan-audit-2026-11-12.md) revises the recommendation to keep the entire matrix unchanged. Acquired files and accessible papers do not establish that a full experiment is worthwhile. No training is launched; the audit recommends a finite comparator/target revision first.

The previous table describes the completed reference-policy study. Brian has now chosen the [local-adaptation response-mapping plan](limburg-response-mapping-plan-2026-11-12.md); historical exclusions of target adaptation below do not apply to this continuation. No training has started.

Required source/model inputs and the three July 2021 receiving cases are held. [New acquisitions and full-text review](reviews/limburg-response-mapping-literature-and-data-2026-11-12.md) add 15 paired SAR tiles for February 2021 EMSR497, 19 public regional vector packages, eight EMSR497 map PDFs, and 4TU flood-extent/ordinance context. Total new material including literature is approximately 1.01 GiB. The Rhine candidate requires reference/support preparation; Belgian discoveries are contextual, not an expansion of the primary geography. No new default agency request or model weights are needed.

Before fitting, finish unique-ground annotation/test separation, reference rasterization and validity, source pseudo-target lineage and counted annotation/validation budgets. These are preparation tasks, not missing external datasets. Independently observed truth and actual operator annotation time are not established by the downloads. All 12 core literature papers and required supplementary methods are accessible.

## Completed acquisition and validity resolution

All six final source states, external and local mapping/scoring and the geometry/target audit are complete. The [consolidation](limburg-study-consolidation-2026-11-11.md) records 447 geometry-compatible paired external tiles and all 167 compatible local records. No further data pull is required for the bounded interpretation.

## Preserved preparation requirements

Assign source versus external roles after actual event/geographic overlap and
label/reference checks. Preserve delivered-reference metadata, target ignore
classes, validity and permanent-versus-event-water meaning. Catalogue P1 by
metadata without target scores. More recent does not automatically mean better:
reference water may already be elevated. Record failed updates and unknown
coverage rather than converting them to dry pixels or removing events silently.

## Outside current completion requirements

No additional optical archive, dense AlphaEarth inputs, global benchmark expansion,
urban-coherence or beneath-canopy dataset is required. No target-label campaign,
label-budget/adaptation grid, new gauge/weather/soil/snow pull or delivery-log
request is introduced. Existing data and useful literature remain available;
[broader ideas](../archive/future-ideas/2026-11-10-broad-spatial-programme/README.md)
can be deliberately revisited later.

## Storage and compute

The 9.068-GiB package is the exact transfer size of uncompressed tar containers
holding compressed GeoTIFFs, not a total disk/runtime estimate. The native-grid
triplet acquisition adds roughly 23 MB per currently obtainable tile; actual
bytes and coverage come from per-tile receipts. Preserve the 50-GiB local
free-space reserve; use one MPS and up to two CPU workers where profiling
supports it. No other chapter's files were touched. The
[scoped compute policy](../config/limburg_chapter_sized_compute_v1.json)
replaces the broad programme's compute requirements.

## Accepted-scope audit — 10 November 2026

[Full audit and reproducible receipts](reviews/limburg-chapter-scope-audit-2026-11-10.md).
The full metadata/header census found26external tiles overlapping source footprints
and251with post-SAR/label-reference offsets exceeding24h. These are reporting and
provenance issues, not automatic exclusions. Keep evaluation labels fixed across
P0/P1 and match processing as well as geometry; a different service's P1 cannot
silently change calibration/resampling. Open catalogue/product metadata and
possibly harmonized same-footprint retrieval are needed; no new agency request.

Preserve native1024px target support. Whole-cohort float32 date features would
occupy about219GiB and all per-seed learned probabilities about183GiB before
compression, so use bounded tile/event streaming and verified remote preservation.
These are array-shape estimates, not extra downloads already started. About122GiB
was free at audit; the50GiB reserve remains. The prior9.068GiB package size must
not be mistaken for the complete execution footprint.


Completion update — 17 November 2026: the first regional-fold benchmark finished
all **152 fits**, calibration and scoring in **39.3 minutes**. Input/output hashes
reverify; 303 metric records and the prediction/calibration tables are available.
No workers remain active. This is one 2021 fold; the results and capacity review
is now complete, with a fair capacity extension recommended before full scaling.
