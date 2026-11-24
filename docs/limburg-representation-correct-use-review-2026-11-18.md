# Representation fit and correct-use review

18 November 2026. Research aid, not dissertation prose. Follow-up to the
[inclusion audit](limburg-representation-extension-audit-2026-11-18.md).
No model was executed and no empirical result changed in this review.

## Judgment

Keep all four representations in the agreed daily reconstruction study.
AlphaEarth has direct supporting hydrological applications; TESSERA is a
plausible independent landscape descriptor; StefaLand has the closest native
land-surface/streamflow purpose; Basin2Vec has the closest native basin-shaped
representation purpose but requires the largest geographic/input adaptation.
Their practical readiness differs. Agreement to include them does not establish
that the available releases can already generate valid European descriptors.

The common XGBoost head is a defensible test of frozen descriptor utility in
GEOGLOWS correction, following the DISE adaptation. It does not reproduce every
paper's LSTM/residual adapter, or measure the maximum attainable skill of each
foundation model. A negative outcome will concern the specified descriptor,
temporal support and correction task. No new LSTM, fine-tuning campaign or
forecasting question is added as a condition of this study.

## What was reread

- AlphaEarth's primary paper and Google's current Satellite Embedding V1
  catalog, plus the existing DISE adaptation and Qu et al. v3's hydrological
  question/results. The held local/regional extraction code was checked too.
- TESSERA v7 methods, inference and downstream application appendices; current
  model repository and pinned GeoTessera registry/Zarr/Icechunk code.
- StefaLand v3 methods, streamflow experiments, architecture and source tables;
  the newer author repository's embedding guide, generator, frozen-encoder
  helper, normalization helper and model forward method, pinned to a commit.
- Basin2Vec v1 methods and appendices, especially equations 6/14, extraction,
  patch alignment, metadata and downstream tasks; pinned encoder/dataset code
  and its AlphaEarth/TESSERA extraction scripts.
- Corley et al.'s pooling preprint, including its task, probes and model-width
  descriptions. This is supporting evidence about aggregation, not a
  hydrological performance result.

The Liu et al. publisher page supplied indexed primary abstract/introduction
material, but fresh full-text retrieval timed out/returned 403; the Mendeley
entry has no PDF. Its detailed extraction supplement was not freshly verified.
Earlier chapter notes and its Zenodo README remain available, but are not a
substitute for that missing recipe. Do not claim to have reproduced its
StefaLand extraction from the main paper alone.

## AlphaEarth: retain the completed use

**Fit:** strong as a static landscape descriptor in pooled hydrological
correction. Direct hydrological papers support this use, without guaranteeing
an extreme-flow gain.

**Correct use:** retain all 64 axes of the annual 2017 field and the audited
catchment means. Google's catalog explicitly permits linear spatial
composition, and the completed local/regional preparation uses the common
10-m EPSG:3035 extraction convention. The older script 67 is historical; it
is not the only provenance for current inputs. The current catalog identifies
the distributed field as model v2.1; the original paper evaluated v2.0. Record
the collection, source images and saved hashes rather than describing every
artifact as identical to the paper's encoder.

Pixel vectors are unit length; their catchment average generally is not.
That is expected. Keep the raw area-composed vector as the XGBoost input;
do not introduce re-normalization solely to make its norm equal to one. The
tree head does not require unit vectors. Any later cosine-based comparison
would need its own normalization convention. Retain all dimensions and do not
interpret an individual axis as a measured physical variable.

**Limits:** this is a prior landscape descriptor, not a contemporaneous storm
or flood-water measurement. Its model was learned using later/global data;
fixed 2017 input support does not make the experiment an as-issued 2017 model.
Nothing in this reread requires rerunning the completed AlphaEarth extraction.

Sources: [catalog](https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_SATELLITE_EMBEDDING_V1_ANNUAL),
[primary paper](https://arxiv.org/abs/2507.22291),
[Qu et al. v3](https://arxiv.org/abs/2601.01558v3),
[DISE](https://doi.org/10.5194/egusphere-2026-1834).

## TESSERA: retain, with corrected coverage semantics

**Fit:** reasonable independent test of whether optical/radar landscape and
phenology information helps the same correction. Its primary tasks concern
land cover, vegetation and related mapping; those results do not establish
streamflow or high-water skill. Native temporal pooling occurs within each
pixel. Spatial catchment averaging is our downstream aggregation decision.

**Correct use:** select one coherent `v1.1-dclimate` source and 2017. Read all
128 distributed feature channels, before the training-only projector. Use
native dequantization per pixel, then fractional-area catchment aggregation.
Retain signed features; do not substitute PCA/RGB previews, average integer
codes with an average scale, truncate arbitrary dimensions, or apply v2's
Matryoshka prefix interpretation to v1.1. Avoid mixing inference variants or
years across subsets of the catchment census. v2 exists, but its availability
and architecture do not make it necessary for this declared v1.1 comparison.

**Correction to the earlier audit:** generic older Zarr comments distinguish
water by NaN scales. The selected Icechunk adapter explicitly sets
`geotessera:mask_source = source_nodata` and says NaN scales are unembedded
pixels, not water. Preserve those as unknown/unembedded; infer water only from
separately justified mask evidence. Do not promote finite scale alone to valid
data: the pinned provider validator also checks positive/plausible scales,
and source completion/coverage must be checked. Use the selected client's
rules, not one generic sentinel interpretation for every store.

Use the published raw dequantized embeddings for the declared mean-based
tree head; no unsupported unit-normalization or feature whitening is added.
During streaming, retain weighted sums, weights, second moments and coverage
receipts. Second moments cost little and preserve an option to examine spatial
heterogeneity without downloading all pixels again. **Mean remains the
declared primary descriptor**; a new pooling model grid is not launched here.
The pooling preprint supports taking aggregation seriously, but uses EuroSAT
classification and describes a 512-dimensional Tessera artifact, unlike our
128-dimensional product. Its numerical gains cannot be transferred to this
hydrological task or treated as validation of our exact release.

Sources: [TESSERA v7](https://arxiv.org/html/2506.20380v7),
[model repository](https://github.com/ucam-eo/tessera),
[GeoTessera](https://github.com/ucam-eo/geotessera),
[pooling study](https://arxiv.org/html/2603.02080v1).

## StefaLand: strong purpose, unresolved exact artifact

**Fit:** strong land-surface/streamflow motivation. It is an attribute/weather
model, not an EO image encoder. The original paper freezes the encoder and
learns lightweight residual/task heads; using frozen features is supported.
A single prior-year descriptor is a narrower adaptation than using evolving
embeddings with a temporal decoder. We must label that distinction.

**Correct use:** obtain the intended Q-free trained encoder and exact variable
schema, or a verified native missing-channel recipe. Do not infer readiness
from the available `StefaLandA.pt` candidate: it has a Runoff projection and
differs from the paper's six-forcing description. The newer helper references
a `StefaLandGlobal20.pt` architecture; its existence does not establish that
the candidate is the same artifact. Require full intended encoder parameter
coverage, not just a count of any parameters successfully copied.

For an artifact compatible with the inspected author helper, the exported
features are the **pre-reconstruction-decoder dynamic hidden state plus the
contextual static hidden state**, not reconstructed input values or predicted
runoff. The generator mean-pools these features by output period. Verify that
recipe against the actual encoder; it is not automatically the precise Liu
et al. supplement recipe.

Three implementation cautions follow from the source code:

1. The helper can generate normalization statistics from the supplied arrays
   when none are present. Prefer the verified checkpoint/inference statistics
   or the authors' prescribed adaptation rule. Do not silently refit them on
   held/test data. If re-standardization is necessary, define its allowed
   source population and evaluate it as an explicit adaptation.
2. Its generic generator defaults to 3,650-day windows with 365-day context;
   the paper reports 365-day pretraining sequences. Do not assume those
   settings are equivalent. Use an artifact-compatible bounded 2020 sequence
   and documented context/pooling, without later-year inputs. Attention can
   use every day within the supplied window; annual labels do not remove
   future information from a longer window.
3. `encode_with_pretrained` supplies all-false input masks and calls
   `is_mask=False`. The inspected forward method's NaN replacement/mask union
   is in the masked branch. Thus passing NaN Runoff to this helper is **not a
   verified missing-channel solution**. Use a proven missingness path and
   ensure invariance to any held-Q placeholder, or obtain Q-free artifacts.

Match physical definitions: Hargreaves PET is not interchangeable with an
ERA5 evaporation variable; relative humidity is not vapor pressure; cumulative
solar energy is not mean irradiance. Native static attributes include specific
soil/geology/vegetation definitions. Document any European/global substitution
and share additional raw information with C1. No pretraining campaign is
needed merely to extract a released frozen encoder.

Sources: [StefaLand v3, methods and appendices](https://arxiv.org/html/2509.17942v3),
[author embedding guide](https://github.com/nrkraabel/PaperReleaseStefalandParameterization/tree/132e2dfb5f4a74a8051a491e94efdc987854c911/docs/embeddings),
[pinned generator](https://github.com/nrkraabel/PaperReleaseStefalandParameterization/blob/132e2dfb5f4a74a8051a491e94efdc987854c911/scripts/generate_embeddings.py).

## Basin2Vec: direct basin representation, substantial European adaptation

**Fit:** strong basin-level purpose. Its native output conditions daily
streamflow models and its pretraining uses no observed streamflow. It is not
a satellite image encoder and its published improvements are not guarantees
for GEOGLOWS correction or European high-water extremes.

**Correct use:** assemble monthly meteorological and quasi-static spatial
stacks for each actual basin, plus the native basin mask and standardized
geometry/effective-resolution metadata. Preserve its learned spatial and
monthly encoding rather than feed it pre-averaged catchment tables. Continuous
versus categorical resampling, padding, alignment and channel ordering matter.
Do not use longitude/latitude as substitutes for scale/shape metadata. The
paper's metadata schema has 18 fields, three constant zero; repository defaults
differ. Follow the actual weights' schema and frozen normalization, including
log transforms. Missing inputs and physical zero cannot be conflated merely
because a helper applies `nan_to_num`.

Use the encoder's **final projected, L2-normalized `z`**, not auxiliary `h`,
`z_multisource`, area prediction, or a branch vector. Run unaugmented inputs
in evaluation/no-gradient mode. Equation 14 normalizes the average of annual
`z` vectors again. For the one-year 2020 comparison this is the
2020 normalized `z`; any longer descriptor must average only the declared
pre-evaluation years, then normalize. Whole-1985–2024 averages would change
temporal support and cannot stand in for our fixed-2020 descriptor.

The original paper's broader multi-year climatological descriptor is not
identical to this controlled one-year adaptation. A result here concerns that
adaptation, not the maximum native Basin2Vec result. A longer native history
can be documented if actually needed; it is not silently substituted or
added as another experiment by this review.

The US source stack, especially Daymet, NLCD and AgTile-US, needs explicit
European equivalents/crosswalks and an account of domain shift. Equal tensor
size is not equal physical resolution. The exact trained encoder and source
schema are still outstanding; the US lookup package alone cannot infer
European embeddings. Its AlphaEarth/TESSERA baseline scripts use coarser
reductions/sampled points; we retain our declared full-support extraction
rather than import those approximations unintentionally.

Sources: [Basin2Vec, sections 3.2/3.4 and appendix A](https://arxiv.org/html/2611.05164v1),
[code and known gaps](https://github.com/Muhammad-Talha-MT/basin2vec).

## Release check — 20 November 2026

**StefaLand.** Liu et al. describe a 256-dimensional representation pretrained
without runoff. The checksum-verified Zenodo v2 archive contains 38 substantive
files (provider MD5 `196c82ef00c3c6ed5a32ea70743235c9`). Its one NetCDF contains
671 CAMELS stations and the 64-dimensional
AlphaEarth variable. It has no StefaLand variables or weights. The prior
Zenodo version contains a short README. The only candidate weights found in
the checked public repositories remain the 46.9-MB `StefaLandA.pt`, with a
Runoff projection and unconfirmed training provenance. Even a valid
masking path for that artifact would test its own masked representation. It
would not establish equivalence to runoff-free pretraining. [GRL paper](https://doi.org/10.1029/2026GL122814),
[reproduction archive](https://zenodo.org/records/22001499),
[first version](https://zenodo.org/records/19157885),
[candidate checkpoint](https://github.com/jaxonson25-hash/StefaLandRelease/tree/1cec7ce402373f283d2329f6a0d48178755f0565/modelFiles).

The separate *StefaLand Global Embeddings* record contains a 218-byte draft
README describing a planned 64-dimensional, 0.1° annual grid. Three of the
seven local catchments and 151 of 394 gauge records have polygon areas smaller
than one 0.1° cell at their latitude. These are area comparisons, independent
of the eventual cell alignment, grid mask or effective support. If released,
the grid would provide a distinct representation at coarser support. The
runoff-free catchment encoder or a catchment-level export remains the more
direct fit. [Draft dataset record](https://zenodo.org/records/21049369),
[author's publication list](https://www.depts.ttu.edu/geosciences/people/atmo/LiuCV.php).

**Basin2Vec.** The checksum-verified PyPI 0.1.0 wheel contains a lookup class and
downloader for precomputed USGS vectors. The `v1.0.0` git tag exists. The
advertised embedding archive returned HTTP 404 and the releases API listed no
releases. The public `main`, `round2-ablations`, `gh-pages` and tagged trees
had no encoder checkpoint. The repository has example normalization files
and the training code. It documents missing preprocessing steps for raw
patches, basin masks, metadata and the sample index. The linked BASINGRID
archive covers U.S. basin inputs and can serve as a native reference if the
encoder becomes available. No model or dataset record was returned by the
exact-name Hugging Face catalog searches for either product.
[PyPI package](https://pypi.org/project/basin2vec/0.1.0/),
[repository and preprocessing gaps](https://github.com/Muhammad-Talha-MT/basin2vec#known-gaps),
[BASINGRID](https://gdex.ucar.edu/datasets/d629000/).

**Basin2Vec European input options.** Candidate sources are E-OBS or ERA5-Land
for meteorology and CORINE as a starting point for the NLCD crosswalk. Handle
AgTile with a separate sensitivity if the checkpoint requires it. That input measures subsurface
agricultural drainage. Generic cropland cover measures a different quantity.
Any sensitivity needs a replacement with comparable meaning or a documented
way to handle the missing channel. The weather data already held are
catchment summaries. Native extraction would use aligned input grids.

A fresh public check found the source tag and evaluator. The tagged release
endpoint and advertised asset returned HTTP 404. The evaluator reads trained
weights, channel lists and basin metadata from its checkpoint. The exact
checkpoint and normalization are needed to prepare new patches.
[Tagged source](https://github.com/Muhammad-Talha-MT/basin2vec/tree/v1.0.0),
[evaluator](https://github.com/Muhammad-Talha-MT/basin2vec/blob/63c8b448170367d915209fb113d2f839e1eb8b52/emb/src/evaluate_embeddings_monthly.py).

**Tagged source archive inspected.** Brian supplied `basin2vec-1.0.0.tar.gz`
(275,678,709 bytes, SHA-256
`9e00b1c49519362d2336b433748b0c2055365025502d5de24e4f2ab5b92cea59`). Its tar
header matches tag `v1.0.0` at `0e1749564242b9efe83724827cb31e778007c167`.
The 1,315 files include code, evaluation tables and arrays, and baseline
embeddings. The archive contains no trained checkpoint, no copy of the
advertised `basin2vec-pretrained-v1.0.0.tar.gz`, and no
`basin_embeddings_full.npz` referenced by its app. The advertised data asset
still returned HTTP 404 on recheck.

Brian also supplied `basin2vec-1.0.0.zip` (276,699,504 bytes, SHA-256
`ac6a8ed402fa2ebd90e7dbf318d4338c1db76003acdcac51370ee84983af0bb7`). Its
embedded commit is the same as the tarball's. All 1,315 regular file paths,
lengths and SHA-256 digests match between archives. GitHub's tagged commit
describes the source snapshot as code without generated embeddings.
[Tagged commit](https://github.com/Muhammad-Talha-MT/basin2vec/commit/0e1749564242b9efe83724827cb31e778007c167).

**Atlas branch and available reference vector.** GitHub reports that
`round2-ablations` is one commit ahead and one behind `main`. The branch-only
commit adds the atlas and a README section. The main-only commit is the
Round-2 merge. Comparing the full trees shows the same model and preprocessing
code. The atlas exports from an existing embedding archive and the branch
ignores `dist/data/`. The deployed `gh-pages` branch, however, serves the U.S.
annual vectors in both representation spaces. I fetched the public 2018
projected vectors and verified the 9,067 × 64 array and unit norms. For USGS
`04101500`, the first five values agree with the package README to a maximum
absolute difference of `2.11e-9`. The complete reference vector and source
hashes are retained in `data/raw/limburg_representation_extension_v1/review_sources/release_resolution_2026_11_20/basin2vec_atlas_us_reference.json`.
The atlas supplies expected outputs for a reproduction case. The remaining
request is for the exact checkpoint and preprocessing recipe, including
prepared inputs for the reference case if available. AgTile still needs
confirmation for the exact checkpoint.
[Branch diff](https://github.com/Muhammad-Talha-MT/basin2vec/compare/main...round2-ablations),
[atlas provenance](https://muhammad-talha-mt.github.io/basin2vec/data/provenance.json).

The main archived `attention_arrays.npz` is byte-identical to the
corresponding file on the checked `main` branch and records an evaluated
variant's channel order. The monthly branch lists `prcp`, `tmax`, `tmin`,
`vp`, `swe`. The nonmonthly branch lists `bdod`, `clay`, `dem`,
`hydraulic_conductivity`, `land_cover`, `permeability`, `pet`, `population`,
`sand`, `slit`, `soc`, `wind`. This differs from the paper's source
description, including shortwave radiation and AgTile. Treat these arrays as
evidence about that evaluated variant. Confirm the channel order, agricultural
drainage requirement and normalization against the delivered checkpoint
before specifying European patches.
[Pinned evaluation outputs](https://github.com/Muhammad-Talha-MT/basin2vec/tree/0e1749564242b9efe83724827cb31e778007c167/emb/src/evaluation_outputs/HCLV4_grouped_monthly_static_meta_areaaux_64d),
[paper appendix](https://arxiv.org/html/2611.05164v1).

**Inference code and design recheck.** The tagged and current encoder source
files match. The evaluator in the tag defaults to the no-temporal ablation.
Current `main` defaults to the main-model run and accepts an explicit
checkpoint. Those defaults do not establish which weights generated the
released vectors. The current evaluator logs the expected and supplied channel
lists, then checks only their dimensions. The grouped-data builder consumes
preprocessed spatial patches, and the example normalization file describes a
different variable list from the archived evaluation. Verify the ordered
channel slices, units, mask, and normalized metadata against the actual
artifact. A prepared U.S. basin-year input and expected final 64-dimensional
vector can check inference independently of the European input substitutions.
[Tagged evaluator](https://github.com/Muhammad-Talha-MT/basin2vec/blob/0e1749564242b9efe83724827cb31e778007c167/emb/src/evaluate_embddings_monthly.py),
[current evaluator](https://github.com/Muhammad-Talha-MT/basin2vec/blob/63c8b448170367d915209fb113d2f839e1eb8b52/emb/src/evaluate_embeddings_monthly.py),
[preprocessing gaps](https://github.com/Muhammad-Talha-MT/basin2vec#known-gaps).

**Full main-branch archive recheck.** The supplied `basin2vec-main.zip`
contains commit `63c8b448170367d915209fb113d2f839e1eb8b52`. All 3,078
files match the Git tree by path and blob hash. The ZIP contains the encoder,
training and export code and published evaluation outputs. It contains
neither the trained checkpoint nor the final Basin2Vec vectors. The main
trainer's checkpoint format records channel names, slices and metadata columns,
but leaves raster scaling and metadata preparation in the upstream inputs.
The shipped `norm_stats.json` nests its entries under `stats`, while the
loader looks up variables at the top level and skips statistical scaling
on a lookup miss. An isolated check using the archived lookup found no
matches for the five monthly variables. Unwrapping `stats` recovered only
`vp` and `swe`. These findings describe the supplied defaults and do not
establish which transformations were used in the original run. Ask for
the checkpoint's actual scaling and metadata recipe, plus the prepared
rasters, mask and metadata for USGS `04101500` in 2018 if available.
[Pinned source tree](https://github.com/Muhammad-Talha-MT/basin2vec/tree/63c8b448170367d915209fb113d2f839e1eb8b52),
[normalization lookup](https://github.com/Muhammad-Talha-MT/basin2vec/blob/63c8b448170367d915209fb113d2f839e1eb8b52/emb/src/basin2vec_dataset_monthly.py#L396-L452).

For Limburg, one fixed 2020 `z` per basin is supported by the per-year
encoder path. Validate the native U.S. reference first, then pilot the
European inputs and log any substitutions and coverage. Compare C1 and
C1+Basin2Vec on the same rows and folds, with conventional summaries of the
verified raw inputs in both arms. The resulting estimate concerns added
descriptor value in the retrospective GEOGLOWS correction. Any longer
pre-evaluation pooling would be a separate sensitivity with a corresponding
control window. The existing study design is sufficient for the annual test.

**Artifact verification.** Check encoder pretraining dates separately from
the 2020 feature cutoff.
Basin2Vec's published pretraining covers U.S. data through 2024, so a 2020
input to those weights would be a retrospective comparison. Confirm the
corresponding StefaLand dates and footprint from the artifact provider.
On receipt, reproduce one reference vector and extract a 2020 European
example before building the census. Use the documented input families to
finish C1 and log any European source substitutions. No production fitting
or new empirical result arose from the release check.

## What changes now

Keep the same RQ, geography, learner, outcomes and agreed four representations.
Correct TESSERA's missingness specification. Make StefaLand's feature tap,
normalization, missing-channel and sequence conventions explicit; use the
correct Basin2Vec projected/normalized output. Preserve provider-native
dimensions and the enriched C1 control. Store compact extraction receipts and
TESSERA second moments so a bookkeeping omission does not require another
pixel download. These are correctness refinements, not additional chapters.

Before production, compare each adapter to a native reference on a small real
input; verify all intended weight tensors, input units/order, ID/date support,
deterministic evaluation and the stated pooling formula. Test missingness and
streamed-versus-direct aggregation on a small window. These checks prevent
incorrect use; they do not require a favourable preliminary score.

The completed AlphaEarth results remain valid for their declared design.
No new findings or high-water benefit are established by this documentation
review. Fresh primary sources and pinned code are saved under
`data/raw/limburg_representation_extension_v1/review_sources/model_use_review_v1/`;
the durable receipt is
`docs/reviews/limburg-representation-correct-use-review-2026-11-18.json`.
