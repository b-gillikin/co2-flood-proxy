---
license: cc-by-4.0
task_categories:
- image-segmentation
tags:
- geospatial
- earth-observation
- remote-sensing
- flood
- sentinel-1
- sentinel-2
- sar
- dem
size_categories:
- 10K<n<100K
---

# GEOID-Flood

[![arXiv](https://img.shields.io/badge/arXiv-2608.02315-b31b1b.svg)](https://arxiv.org/abs/2608.02315)
[![Code](https://img.shields.io/badge/GitHub-links--ads%2Fgeoid--flood-181717.svg?logo=github)](https://github.com/links-ads/geoid-flood)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)

A large-scale multi-modal benchmark for flood segmentation, built from **219 Copernicus
EMS Rapid Mapping flood activations** across **65 countries** (2016-2026).

**134,596 rasters / 329 GB** across 190 shards. 12,236 tiles: 7,496 train / 1,022 val / 2,417 test, plus 1,301 held-out tiles from activations EMSR857-871 for out-of-distribution evaluation.

Each 1024x1024 tile at 10 m resolution provides co-registered Sentinel-1 GRD and RTC
(pre- and post-event, VV/VH, the same acquisitions in both products), a pre-event Sentinel-2 L2A image, a Copernicus
GLO-30 DEM, and manually checked three-class labels
(0 = background, 1 = permanent water, 2 = flooded water).

> **v1.1** (current) removes unusable, duplicated and wrongly labelled tiles, fixes Sentinel-1 and Sentinel-2 issues
> and adds provenance metadata to every file. See [`CHANGES_v1.1.md`](CHANGES_v1.1.md). The paper describes v1.0,
> which stays available at the `v1.0` tag (`get_data.py --revision v1.0`).

![Representative GEOID-Flood tiles: pre- and post-event Sentinel-1 GRD and RTC, pre-event Sentinel-2 RGB, GLO-30 DEM, and the three-class label, for three events](assets/modality_samples.png)

*Three GEOID-Flood events, all layers of a tile side by side. Flooded water is cyan, permanent
water blue, invalid pixels gray.*

![Global distribution of GEOID-Flood areas of interest, coloured by split assignment, with an inset enlarging Europe](assets/global_aoi_map.png)

*The 219 activations span 65 countries. Splits are assigned per area of interest and touching
AoIs share a split, so no area of interest straddles train, validation and test.*

## Layout

Rasters ship as **uncompressed tar shards of Cloud-Optimized GeoTIFFs**, grouped so you
can download only the modalities and splits you need:

```
{tree}/shards/{split}/{layer}/{split}-{layer}-NNNNN-of-NNNNN.tar
```

Tar members carry the canonical path (`EMSR151-1/s1grd/EMSR151-1-0_s1grd_post_*.tif`), so
extracting **any** shard into a tree root rebuilds the layout the training configs expect:

```bash
tar -xf train-s1grd-00000-of-NNNNN.tar -C data/geoid-flood/
```

## Download

`get_data.py` fetches shards and unpacks them into the expected structure, deleting each
shard as soon as it is unpacked. It checks free space before starting and resumes if
interrupted.
```bash
pip install huggingface_hub tqdm
python get_data.py --dest data                                     # everything
python get_data.py --dest data --layer s1grd label                 # S1-GRD benchmark
python get_data.py --dest data --tree geoid-flood-heldout \
                   --layer s1rtc label                             # held-out eval only
python get_data.py --list --layer s1grd s2l2a dem label            # preview, no download
python get_data.py --dest data --layer s1grd --workers 8           # more shards in flight
```

Download v1.1 into a fresh `--dest`: do not mix v1.0 and v1.1 files.

Shards are fetched over the Xet protocol, several at a time. Peak disk usage is the size of
your selection plus roughly `--workers` x 2 GB for the shards in flight.

Typical selections:

| selection | flags | size |
|---|---|---|
| everything | *(no flags)* | ~329 GB |
| S1-GRD single-image benchmark | `--layer s1grd label` | ~91 GB |
| ...train+val only | `--layer s1grd label --split train val` | ~63 GB |
| early/mid fusion (S1+S2+DEM) | `--layer s1grd s2l2a dem label` | ~241 GB |
| held-out S1-RTC evaluation | `--tree geoid-flood-heldout --layer s1rtc label` | ~10 GB |

### Without `get_data.py`

The shards can also be fetched with the Hugging Face CLI and unpacked with `tar`. Select layers and splits with
`--include` patterns; every shard is on disk before unpacking, so peak usage is about twice your selection:

```bash
pip install -U huggingface_hub
# e.g. the S1-GRD benchmark: metadata + s1grd + label shards of the main tree
hf download links-ads/geoid-flood --repo-type dataset --revision v1.1 --local-dir data \
  --include "geoid-flood/*.csv" --include "geoid-flood/*.parquet" \
  --include "geoid-flood/shards/*/s1grd/*" --include "geoid-flood/shards/*/label/*"
# unpack each shard into its tree, then delete it
cd data && for t in */shards/*/*/*.tar; do tar -xf "$t" -C "${t%%/*}" && rm "$t"; done && rm -r */shards
```

## Modalities

Every tile carries the same nine layers, all co-registered on one 1024x1024 event-UTM grid
at 10 m. Four are imagery, five are derived masks. Every GeoTIFF names its bands; Sentinel-1, Sentinel-2 and cloud-mask
files list the Copernicus products they were made from in the `SOURCE_PRODUCTS` tag (a JSON list).

| layer | bands | passes | size | what it is |
|---|---|---|---|---|
| `s1grd` | 2 x float32 | pre + post | 90.5 GB | Sentinel-1 GRD backscatter as linear sigma0, bands `VV`, `VH`. One acquisition before the event and one after. The loader converts to dB (`10*log10`) on read. Stored rounded to 10 mantissa bits (ZSTD), at most 0.0021 dB from the original after conversion to dB. |
| `s1rtc` | 2 x float32 | pre + post | 88.4 GB | The same two acquisitions, radiometrically terrain-corrected, also linear sigma0, same storage. `NaN` marks pixels outside the valid swath. |
| `s2l2a` | 12 x uint16 | pre | 142.5 GB | Pre-event Sentinel-2 L2A surface reflectance, bands `B01`…`B12` (incl. `B8A`). A per-pixel mosaic: each pixel takes the scene closest to the CEMS pre-event mapping date with valid data. Harmonized to processing baseline 04.00 (no +1000 offset); reflectance = DN x 0.0001, recorded as the band scale. `0` = no data. |
| `dem` | 1 x float32 | static | 7.6 GB | Copernicus GLO-30 elevation in metres, resampled from 30 m onto the 10 m tile grid. |
| `label` | 1 x uint8 | static | 0.1 GB | **The training target.** Manually checked three classes: `0` background, `1` permanent water, `2` flooded water. `255` marks pixels outside the mapped area and is the ignore index. |
| `cloudmask` | 1 x uint8 | pre | 0.1 GB | Cloud and shadow over the S2 image, from OmniCloudMask: `0` clear, `1` thick cloud, `2` thin cloud, `3` shadow. Not folded into `label`, so this is the only per-pixel record of cloud. |
| `floodmask` | 1 x uint8 | static | 0.1 GB | Binary CEMS Rapid Mapping flood delineation used to build `label`. Retains extent the three-class label dropped. |
| `permwater` | 1 x uint8 | static | 0.1 GB | Binary permanent-water extent used to build `label`. No released config reads it. |
| `validity` | 1 x uint8 | static | 0.1 GB | Binary per-pixel validity: `1` where the tile was imaged and mapped. Largely redundant with `label == 255`. |
| | | | **329 GB** | **134,596 rasters** |

`sample/` holds two complete event-AoIs from activation EMSR712 -- `EMSR712-10` (train split) and `EMSR712-3` (test split) -- with all nine layers for all 47 tiles, 8,076 chip rows, so the loader can be exercised end to end without a full download. It extracts to the
same canonical paths, so the only override needed is
`--data.init_args.metadata_filename data_tiles_s256_st128_sample.csv`.

## Normalization statistics

Recomputed on the v1.1 train split, over valid pixels. S1 in dB as the loader reads it (`10*log10` of linear sigma0),
pre and post pooled; S2 in DN (multiply by 0.0001 for reflectance).

| product | band | mean | std |
|---|---|---|---|
| `s1grd` | VV | -10.358 | 4.919 |
| `s1grd` | VH | -17.455 | 6.184 |
| `s1rtc` | VV | -10.586 | 4.651 |
| `s1rtc` | VH | -17.680 | 5.936 |

| S2 band | B01 | B02 | B03 | B04 | B05 | B06 | B07 | B08 | B8A | B09 | B11 | B12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| mean | 555.5 | 668.2 | 954.0 | 1036.1 | 1465.4 | 2315.6 | 2633.1 | 2759.9 | 2857.4 | 2892.9 | 2349.3 | 1640.7 |
| std | 800.9 | 843.6 | 853.7 | 1019.8 | 991.2 | 1049.8 | 1163.4 | 1220.7 | 1205.8 | 1261.6 | 1177.8 | 1101.8 |

## Metadata

| file | role |
|---|---|
| `data_tiles_s256_st128.csv` | **the only metadata the dataloader reads.** Enumerates 256x256 chips at stride 128 (train) / 256 (val, test), with `valid_proportion`, `positive_proportion`, `cloud_cover` and `split` per chip |
| `tile_catalog.parquet` | the 1024x1024 tile inventory, one row per shipped tile: geometry, UTM CRS, event and delineation times, `invalid_pixel_frac` (share of invalid pixels in `validity`), `split`, `countries`, `countries_set`, `macro_areas_set`, and the Copernicus products of each tile (`s1_pre_products`, `s1_post_products`, `s2_pre_products`, the same names as the GeoTIFF tags). Nothing reads it at training time; query it to select events by geography or date |

The tile catalog, the chip CSV and the shipped rasters list the same 12,236 tiles.

## Known limitations

- `label` is not masked under clouds; use `cloudmask` if you need to.
- Some RTC files are smoother than 10 m (lower-resolution processing of the right acquisition).

## Citation

See `CITATION.cff` in the code repository.

## License

The GEOID-Flood compilation, splits and labels: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
Code: MIT, in the code repository. The `dem` layer is licensed separately (below).

Contains modified Copernicus data. Carry these notices forward when redistributing:

- Modified Copernicus Sentinel-1 and Sentinel-2 data (2016-2026).
- Copernicus Emergency Management Service Rapid Mapping products, © European Union.
- The `dem` layer is a resampled Copernicus WorldDEM-30 (instance COP-DEM-GLO-30-F), used under the
  [Copernicus WorldDEM-30 licence](https://docs.sentinel-hub.com/api/latest/static/files/data/dem/resources/license/License-COPDEM-30.pdf).
