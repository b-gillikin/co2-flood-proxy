# Limburg foundation representations: scientific and download readiness

**Status:** fixed internal implementation note, 2026-10-11. It prepares one
bounded representation comparison; it does not report a dissertation result.

## Scientific decision

The experiment will use **IBM Granite Tiny Time Mixers R2 (TTM-R2), variant
`512-96-r2`**, as its single time-series foundation-model challenger. The choice
is justified by the research comparison rather than by a vendor leaderboard:

- it is open-weight under Apache 2.0, small enough to reproduce locally, and
  has a pinned public snapshot and safe-tensor weights;
- it supports hourly, multivariate time series and exposes hidden states,
  allowing a fixed event representation rather than an opaque generated text;
- an independent 2026 zero-shot streamflow comparison includes TTM alongside
  Chronos, MOIRAI and Sundial, making it a defensible hydrological challenger;
- its pretraining inventory includes river-flow and weather series, which is
  relevant transfer experience and must be disclosed; and
- it tests the named question: whether a pretrained temporal representation
  retrieves more informative prior events than conventional signatures.

This selection does not imply that TTM is the best general time-series model.
Chronos, MOIRAI and Sundial are documented alternatives, not additional arms.
They enter only if the pinned TTM cannot run as specified, not because its
answer is disappointing.

TTM was trained for forecasting, not specifically for analogue retrieval. The
streamflow benchmark therefore establishes domain relevance and executable
zero-shot transfer, but does not validate hidden-state similarity. Treating a
pooled hidden state as an event representation is the experiment being tested,
not an accepted model property. The raw-sequence control below is what makes
that test interpretable.

## Frozen temporal comparison

The model snapshot is
`b2a0242647492d2652b44135c2529333ac13e007`. TTM-R2's shortest supported hourly
context is 512 hours, and IBM advises against padding shorter histories. A real
data audit rebuilt the 724-event library with 512 history hours and 72 withheld
outcome hours:

| Quantity | Events |
| --- | ---: |
| Complete discharge history | 629 |
| Complete rainfall history | 655 |
| Complete weather history | 724 |
| Complete across all three and primary-usable | **570** |

The original 168-hour library had 683 complete-input events and 721
primary-usable events. The 512-hour common sample therefore retains 83.5% of
the original complete-input set and 79.1% of primary-usable events. That is
enough for the bounded comparison, with exclusions reported by watercourse and
season.

The primary learned representation is frozen in advance:

1. provide the 512 hourly discharge observations ending at event onset;
2. standardize within the available history only;
3. run the pinned model without fine-tuning;
4. extract its last hidden layer, mean-pool across patches and L2-normalize;
5. retrieve only strictly earlier events from a different storm; and
6. score retrieval using the held 72-hour response properties already used by
   the conventional baseline.

All representation arms use the same 570-event complete-case frame. Alongside
the existing hydrological-signature baseline, a standardized raw 512-hour
hydrograph nearest-neighbor baseline is required. It controls for the longer
input and tests whether pretraining adds value beyond hydrograph shape. Layer,
pooling and model selection will not be tuned after comparative results are
opened. Direct 96-hour forecasting is outside the primary experiment.

## Frozen catchment comparison

AlphaEarth is used only as a catchment descriptor. The official annual product
contains 64 embedding bands at 10 m for 2017–2024. The repository exports
catchment-year means and valid-pixel counts rather than imagery.

To prevent same-year future imagery from entering an event assessment, event
year `Y` uses the `Y-1` embedding. Events before 2018 are outside the primary
AlphaEarth comparison; events after 2024 use the latest available 2024 layer.
A 2017–2024 catchment mean may be reported only as a static-similarity
sensitivity analysis, with its retrospective nature stated explicitly.
Individual embedding axes receive no physical interpretation. AlphaEarth is
compared against ordinary catchment attributes and cannot replace observed
rainfall, antecedent conditions or hydrographs.

## Assets and reproducibility

`config/limburg_foundation_assets.json` fixes the model revision, safe file
list, source-code revision, public documents and AlphaEarth export definition.
`scripts/66_download_limburg_foundation_assets.py` downloads public files
atomically and writes a SHA-256 receipt beside each file. It deliberately
excludes the unnecessary pickle-based `training_args.bin` file. Reruns verify
and skip completed assets, retain resumable `.part` files, and continue to the
remaining assets if one host is temporarily unavailable. Hugging Face stores
the weight file through Xet; `environment-foundation.yml` therefore includes
its official `huggingface_hub`/`hf_xet` client for subsequent model use.

`scripts/39_delineate_catchments.py` now also generates a separate nine-feature
cross-border catchment layer: seven held Dutch polygons and the delivered
Herzogenrath 1 and Randerath Wurm stations. The original event-study catchment
output remains unchanged. `scripts/67_export_alphaearth_embeddings.py` starts
the authenticated Earth Engine table export.

Commands:

```bash
python scripts/39_delineate_catchments.py
python scripts/66_download_limburg_foundation_assets.py
python scripts/66_download_limburg_foundation_assets.py --group all --download
python scripts/67_export_alphaearth_embeddings.py --project YOUR_EE_PROJECT
```

The downloader is a dry run unless `--download` is supplied. Earth Engine
authentication and a Cloud project are the only user-specific steps. Raw
AlphaEarth rasters, broad Earth-observation datasets, multiple TSFMs and a new
fine-tuning programme are outside this experiment.

## Interpretation boundary

A retrieval improvement would show that a representation helps find historical
analogues whose withheld responses are more similar. It would not establish
live forecast skill, warning lead time, causal hydrology, better operator
decisions or readiness for deployment. Failure to beat both the conventional
signature and raw-sequence controls is informative evidence against using the
foundation representation in this case; it is not a reason to add more models.
