# Ten-model documentation review — 22 October 2026

Internal research/engineering note, not dissertation prose. Read the held model
cards and repository guides, their inference examples, and the implementation
behind the relevant normalization, dates, masks and feature readouts. The
machine-readable companion records the exact files and hashes. This reviews
the ten selected EO checkpoints; TTM and AlphaEarth are separate existing arms.
It is not a new literature search, model sweep or empirical performance result.

## What changes the pending correction

**The planned correction needs eight models, not seven.** CROMA also has an
input-normalization error, independently of the Sentinel-2 date correction.
Prithvi and the already repaired OlmoEarth run remain reusable on this review's
evidence. No new imagery, checkpoint or agency request is needed for these fixes.

| Finding | Evidence | Consequence |
| --- | --- | --- |
| **New: CROMA omits the final division by 255.** | Its full README first stretches/quantizes to uint8, then explicitly supplies `float()/255` to the model. Our adapter supplies the uint8 values as floats. Capturing the adapter on an engineering fixture gives 0–255, versus 0–1 from the executed publisher example. `use_croma.py` does not apply the missing rescaling internally. | Add CROMA to the consolidated extraction correction. Correct the transform before feature extraction; normalizing output vectors cannot repair this input error. Keep the old arm labelled as incorrectly preprocessed. Its numerical effect on retrieval is not established by this diagnostic. |
| **New: AnySat's date documentation conflicts with its executable example.** | README/notebook prose calls January 1 day 0. The notebook function and TreeSAT, FLAIR, PLANTED and S2NAIP dated loaders use one-based day of year. Our adapter follows the prose. A leap-year fixture captures `[0, 59, 365]` versus TreeSAT's `[1, 60, 366]`. PASTIS uses a separate reference-date convention, so this is not a claim that every pretraining dataset had identical dates. | For the fixed S2 inference route, follow the demo and dated loaders' one-based convention in the versioned correction, record why it supersedes the prose, and test leap days/year boundaries. AnySat is already in the seven optical models. Do not claim a known material performance effect from a one-day difference. |
| **Confirmed from earlier audit: SatMAE uses the wrong transform.** | The multispectral dataset's `SentinelNormalize` clips mean ±2 SD to uint8; `ToTensor` then divides by 255. Our current adapter uses a z-score. The captured value at the channel mean is 0 versus the reference's 127/255. | Correct SatMAE's input transform, including the fill value for missing pixels, during its already planned extraction. This is the multispectral checkpoint, not temporal RGB SatMAE. |
| **Confirmed from earlier audit: Presto can use actual pixel months.** | README mentions a starting month; the encoder implementation additionally accepts a full batch-by-time month tensor. Our adapter repeats the patch-median month, although per-pixel acquisition days are held. | Remove this approximation in the corrected Presto adapter. Monthly bins are unaffected; mixed-month weekly composites can differ. Existing dates suffice. |

For CROMA, the example also uses sample SD whereas our NumPy stretch uses
population SD. On the diagnostic, dividing our input by 255 leaves a maximum
difference of one eight-bit step. Match the example's SD convention over observed
support in the corrected adapter as well. The fully observed diagnostic does not
validate a missing-data policy: retain explicit masks, exclude absent pixels from
the stretch, and fill absent pixels at the transformed neutral value. Do not
estimate stretches over a changing inference batch of unrelated patches.

Publisher evidence:
[CROMA inference example](https://github.com/antofuller/CROMA/blob/59505a6bcadbf36ba20767270154bf9f3067c5e7/README.md),
[CROMA forward implementation](https://github.com/antofuller/CROMA/blob/59505a6bcadbf36ba20767270154bf9f3067c5e7/use_croma.py),
[AnySat demo](https://github.com/gastruc/AnySat/blob/5f6f475e1a22ce5e3a56a5b18f4ed6d24eca2a4a/demo.ipynb),
[AnySat TreeSAT dates](https://github.com/gastruc/AnySat/blob/5f6f475e1a22ce5e3a56a5b18f4ed6d24eca2a4a/src/data/TreeSAT.py),
[SatMAE transforms](https://github.com/sustainlab-group/SatMAE/blob/0b210aceb37a14bbbd897110db5b104b3271d818/util/datasets.py),
[Presto encoder/month handling](https://github.com/nasaharvest/presto/blob/11e207a668a34336ced1d8e492a1bd5849b96c4a/presto/presto.py).

## Findings for each selected model

| Model/checkpoint and held route | What the documentation clarified | Assessment/action |
| --- | --- | --- |
| **OlmoEarth v1.2 Tiny; ascending VV/VH SAR** | The computed normalizer maps mean ±2 SD to 0–1 without clipping. Dates are day 1–31, month 0–11, full year. Missing is mask value 3; observed is 0. Missing modalities are supported. The quickstart supports 64-pixel inputs and patch size 4; pooling must count encoded tokens. | The held constants, timestamp order and repaired token masks/masked mean pooling agree with this route. Reuse the repaired run. Optional additional modalities or smaller patches are not missing requirements. Do not apply v1 checkpoint instructions indiscriminately to v1.2. |
| **Galileo Nano; ten S2 bands** | Its helper uses `Normalizer(..., std=True)`, matching the mean ±2 SD scaling already used. Zero means an observed group and one means an ignored group. Months are zero-based. The official feature extractor averages unmasked tokens. | Retain the repaired, token-consistent mask route and patch size 8. Add the directly consumed normalization JSON to future provenance, as identified in the earlier audit. Its static/climate inputs are optional; absent groups remain masked. Rerun for coherent S2 dates. |
| **AnySat base; ten S2 bands** | The notebook supplies the exact normalization constants in our adapter. `patch_size` is metres, not pixels; 20 m on a 64×64 grid at 10 m gives 1,024 patches, within its recommendation. `tile` is a supported embedding output. Its date prose/function conflict is real. | Keep the normalized S2-only tile route, output type and spatial support. Correct day-of-year to the executable demo/dated-loader convention while correcting S2 coherence. No FlashAttention installation, aerial imagery or extra SAR channel is required. |
| **Prithvi EO 2.0 Tiny TL; six HLS bands** | The model is trained on six ordered HLS bands at 30 m. Checkpoint means/stds are in scaled-reflectance units. Location is latitude then longitude in `LocationEncoder`; time is year then one-based day of year. The checkpoint config has four frames; inference/position-grid code permits a changed frame count and cautions that results may vary. | Our one-time conversion of held physical reflectance to scaled units, band order, coordinate order and final non-CLS token mean are consistent. Reuse the existing run. Twelve monthly frames are a supported transfer setting, not the original four-frame training regime. No forced reduction to four frames or new HLS collection is justified by this read. |
| **CROMA base SAR; ascending VV/VH** | SAR-only inference is supported. Default image size is 120 pixels, with 8-pixel internal patches. `SAR_GAP` is the radar branch's pooled/FFN representation. The final input `/255` is essential. | The sensor branch, size and readout are appropriate; the normalization is not. Correct and re-extract CROMA. Optical B01/B09 are not needed for a SAR-only model. |
| **DOFA v1 ViT-base e100; six non-TCI S2 bands** | The documentation advertises newer weights, but also warns that their dynamic layer differs. Its demonstrated v1 route uses Satlas-format inputs, wavelength conditioning in micrometres, and supports band subsets. Demo RGB is TCI imagery, not simply DN-scaled physical RGB. | Retain the matched v1 source/weight pair and the declared six non-TCI bands, their DN-to-eight-bit conversion and corresponding published stats. Do not silently upgrade to v2 or fabricate TCI RGB. No additional defect identified; coherent S2 dates still require re-extraction. |
| **Copernicus-FM base; ten S2 bands** | Missing metadata is explicitly supported, but the demo also shows real longitude/latitude, days since 1970-01-01 and **internal patch-token area in km²**. Wavelengths/bandwidths are nanometres. The official benchmark's patch mean plus output LayerNorm is a documented alternative to the README's CLS example. | Current spectral normalization and fixed benchmark readout remain justified. All-NaN metadata is a valid but deliberately reduced use of the model. The existing held coordinates, representative date and resolution could support one fixed metadata-enabled route without new data. This is an optional design improvement, not a normalization bug or requirement; see below. Rerun for S2 coherence. |
| **TerraMind 1.0 Tiny; ten S2L2A bands** | The model card explicitly supports single modalities and band subsets. Raw backbone normalization is external; the generation API's `standardize=True` should not be mistaken for backbone behavior. TiM and any-to-any generation are separate variants. Its multitemporal wrapper does not turn the single-frame backbone into temporal attention. | The selected S2L2A band subset and v1 statistics match the pinned registration source. Keep the encoder-only route and transparent equal-frame mean. No tokenizers, generated land-cover layer, diffusion model or extra training is required. Rerun for S2 coherence. |
| **Presto default; per-pixel S2 sequences** | One to 24 time steps are supported. The supplied helper normalizes the available bands, constructs derived inputs and masks unavailable ones. Dynamic World class 9 means unavailable. Latitude/longitude and zero-based months are genuine inputs; a full month tensor is accepted. The demo itself demonstrates transfer to single images. | Keep the official helper, absent-input masks and current batched implementation. Use per-pixel months in the correction. Twelve monthly steps are closer to its pretraining cadence; four weekly steps are an explicit cadence transfer, not invalid just because monthly pretraining was used. No new Dynamic World, ERA5 or SRTM pull is required. |
| **SatMAE multispectral ViT-base e199; ten S2 bands** | The README separates multispectral and temporal RGB checkpoints. The selected multispectral pretraining uses 96-pixel images, 8-pixel patches and drops B01/B09/B10. Its dataset transform provides the normalization missing from a casual reading of the README. | Band/order/size and the selected multispectral variant are appropriate. Correct the stretch/quantization/scaling. The publisher's random training crops and downstream resize/crop are distinct from our declared fixed native-grid transfer; copying training augmentation into deterministic extraction is not required. Frame means remain order-invariant. |

## Useful improvements without expanding the study

**Copernicus-FM's existing metadata is the clearest underused capability.** At a
10 m grid and internal kernel size 16, its token area is `(16*10/1000)^2 = 0.0256`
km². This is neither the full 224-pixel image area nor the catchment area. Its
time input is elapsed days since 1970-01-01, not month, day of year or Unix seconds.
If adopted in the consolidated correction, use held patch centres and the declared
representative acquisition date, and record the date range of each composite.
Keep the existing no-metadata outputs as historical evidence; do not introduce
a metadata grid search or pick the version by final event scores.

Latitude/longitude can encode catchment identity, while dates encode season.
Metadata-enabled performance therefore needs the existing cross-river, matched
donor and seasonal comparisons; it would not by itself prove that wetness or
storm evolution was learned. A separate claim that metadata *caused* improvement
would need a controlled ablation. That claim/extra full extraction is not required
for using one explicitly chosen, documented inference configuration. Galileo also
supports location, but adding that modality is a further design change, not a fix
the present review requires.

**Use each representation for what it can observe.** CROMA's local contrast
stretch removes absolute patch brightness/scale; DOFA's eight-bit conversion
clips/quantizes information. These are documented input choices, not evidence
that the models directly measure antecedent wetness. Optical imagery describes
surface/landscape conditions and can be absent during storms. None of these ten
encoders directly consumes the held rainfall/discharge trajectory in this setup.
The comparison with conventional hydrology and TTM remains necessary to establish
whether EO context adds anything about subsequent river response.

**Do not overstate temporal or spatial comparability.** Five selected routes
(OlmoEarth, Galileo, AnySat, Prithvi and Presto) combine observations within a
native temporal model. The other five use an order-invariant mean of independently
encoded frames. Their native windows also span different physical footprints:
Prithvi's 224×30 m is 6.72 km across, compared with Galileo's 32×10 m = 0.32 km.
Even exact catchment area weights do not remove the surrounding context inside a
patch. Results compare declared representation routes, not architectures isolated
from sensor, footprint, normalization and support differences. This calls for
clear interpretation, not a new spatial-size sweep.

**Pretraining is not a hydrological validation dataset.** AnySat's GeoPlex contains
TreeSatAI-TS, PASTIS-HD and FLAIR, among others; these are land-surface learning
datasets, not independent Limburg high-water labels. Broad/global pretraining
can include European imagery. The review does not establish geographic or
calendar independence of pretrained samples. Later chronological donor rules
do not erase that limitation. Do not claim unseen-basin or as-issued forecast
validation merely from frozen weights and earlier donor dates.

## Execution implications and limits

The original controller remains held. Its code still lists seven models and
would incorrectly reuse CROMA if simply restarted unchanged. Before the
authorized rerun, update the versioned adapter/controller to consolidate:

1. Coherent S2 dates for the same seven optical routes.
2. SatMAE and CROMA publisher-compatible normalization; AnySat's documented date
   convention; Presto's held per-pixel months.
3. Direct normalization/adapter/runtime/source binding and the earlier audit's
   compact lossless storage/aggregation work.
4. Small publisher-conformance and one-/four-/twelve-frame checks, including
   missing support, leap/year/month boundaries and resume/aggregation round trips.

Retain the authorized two CPU workers and one MPS worker, with CROMA added to a
serial model lane. Reuse Prithvi and repaired OlmoEarth, subject to their unchanged
recorded identities. The previous **285.659 GiB / 2.830 GiB** allocation/vector
figures describe the seven original directories only; they are not estimates for
the expanded eight-model correction. Storage design must account for CROMA too.

This review changed diagnostic/review files only. No production numerical adapter,
source imagery, selected run, weight, active score or empirical result was changed;
no corrected extraction was launched. The independent CROMA and AnySat diagnostics
load no weights. They establish input differences, not improvements in scientific
performance. The earlier audit's statement that CROMA needed no S2-day correction
is still true; its implied reuse without other corrections is superseded here.

Reproduce input captures with `scripts/123_audit_encoder_input_contracts.py
--model croma` and `--model anysat` in the modern runtime, `--model satmae` in the
SatMAE runtime, and `--model presto` in the validated Presto runtime. All four
captures record their source hashes and explicitly report nonconformance or the
temporal approximation. A successful diagnostic exit means the capture completed,
not that the current adapter conforms. The companion JSON preserves the captures
and source inventory in Git.
