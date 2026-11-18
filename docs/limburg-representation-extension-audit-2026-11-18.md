# Chapter audit: TESSERA, StefaLand and Basin2Vec inclusion

18 November 2026. Internal research aid; Brian writes dissertation prose.
Brian approved inclusion of all three representations and requested this design,
data and disk assessment. Configuration:
`config/limburg_representation_extension_v1.json`. Completed AlphaEarth models,
inputs, predictions and results are preserved. No new extraction or fitting
queue has launched. Small source snapshots and one candidate checkpoint were
acquired to investigate the actual release, rather than assuming readiness.

Follow-up: the [model-specific correct-use review](limburg-representation-correct-use-review-2026-11-18.md)
checks native extraction, normalization and pooling and corrects the TESSERA
Icechunk coverage interpretation below. Its refinements govern preparation.

## Assessment of the chapter with all three included

**The inclusion is scientifically coherent and remains one comparative chapter.**
The task stays daily retrospective reconstruction of global modelled discharge,
with the existing seven NL/DE gauges, regional donors, external river systems,
chronology and high-water evaluation. The additional question is whether the
observed benefit and limitations depend on the catchment representation.

The four representations have distinct reasons for inclusion:

| Representation | Role in this study | Intended use |
| --- | --- | --- |
| AlphaEarth | Completed anchor: a satellite-based landscape descriptor | Existing fixed-2017 64-dimensional catchment means |
| TESSERA | Independent satellite representation | Fixed-2017 native 128-dimensional descriptors, dequantized before area-weighted catchment averaging |
| StefaLand | Physical/meteorological land-surface representation | A verified frozen encoder or documented precomputed annual descriptor, initially retaining native 256 dimensions |
| Basin2Vec | Catchment-centred representation with spatial, seasonal and basin-geometry structure | Frozen 64-dimensional basin descriptor from the existing European reference polygons and documented pre-evaluation inputs |

StefaLand and Basin2Vec are not interchangeable satellite-image encoders. They
can legitimately be compared as **catchment representation products** in a
common downstream task. Different pretraining inputs, objectives and geographic
coverage prevent a claim of isolating encoder architecture alone.

Their inclusion strengthens a robustness/transferability study; it does not
automatically create novel methods or guarantee a positive flood result. The
main p99 question, whole-record secondary outcomes and documented failures all
remain. Four representations and one learner are not four new dissertations.

## Findings that need resolving in preparation

### 1. The additional input information needs a fair control

The old H+A control does not contain every physical input that StefaLand and
Basin2Vec may receive. In particular, temperature extrema, snow, PET, richer
soil/geology, vegetation and patch geometry may introduce new information.
An advantage could therefore come from those inputs as well as their encoding.

Keep the completed H+A comparison as **C0**. For the extension, prepare **C1**:
the same H+A information plus declared compact raw summaries/metadata of the
new physical input families. Fit the following controlled family:

`C1; C1+AlphaEarth; C1+TESSERA; C1+StefaLand; C1+Basin2Vec`.

This makes the extra physical information available to the conventional
comparator too. The summaries do not reproduce every spatial relationship in
a learned representation; that is part of the representation comparison. The
study must disclose these differences rather than claim identical upstream
processing. Choose the raw summaries from the verified native variable schema
before seeing new test scores. Predictor features cannot include observed-flow
signatures, held Q or full-record climatologies that use later test information.

**AlphaEarth needs a new fit against C1.** C1 is a richer baseline, so its new
increment cannot be inferred from the existing 13.86% H+A result. The original
result remains valid for its original design and is not overwritten.

### 2. A public StefaLand candidate is not established as the intended Q-free encoder

The original paper's anonymous release API returns `repository_expired` (410).
Further source investigation found a public candidate checkpoint:

- `jaxonson25-hash/StefaLandRelease`, pinned commit
  `1cec7ce402373f283d2329f6a0d48178755f0565`;
- `modelFiles/StefaLandA.pt`: **46,914,220 bytes**, SHA-256
  `b00c94d7499ee190b2c52a444a5b781632d5b3c16b3dfaa4bab8ba8e67aeb6b3`;
- archive/pickle opcodes were inspected **without executing pickle code or
  loading the neural model**;
- its input-projection keys include **P, Tmax, Tmin, PET and Runoff**, with
  22 named static projections. That does not match the simple assumption of
  the six-forcing, runoff-free pretraining route described in the paper/Liu
  application. Its author provenance, training stage, normalization and native
  missing-channel use are not established by the filename.

This is not proof that the file is unusable or that leakage has occurred. It
means a naive default input construction would be scientifically unsafe.
Neither contemporary nor historical held-target observed Q may be supplied
to generate pseudo-ungauged descriptors. Replacing Runoff by modelled Q or
masking it would require an explicit, supported recipe; neither is assumed.
The practical options are the authors' Q-free encoder/descriptors, or a verified
native missing-Runoff route with a clear account of any Q used in pretraining.

A newer repository under `nrkraabel/PaperReleaseStefalandParameterization`
documents a generic embedding generator, but does not distribute its encoder
checkpoint. Its guide also warns that name/shape-only weight copying can
silently leave unmatched parameters random. Our adapter must verify complete
intended encoder coverage and actual variable lists; a successful Python
process is not sufficient. A condensed 64-dimensional adapter is not required
for the initial frozen-descriptor comparison.

### 3. Basin2Vec needs a European inference route, not US embedding lookup

The public repository advertises US-only precomputed embeddings. On this
audit, its release API returned no releases, the advertised v1.0.0 archive
returned **404**, and the captured git tree contained no `.pt/.pth/.ckpt` or
`.safetensors` encoder file. Those are specific asset-access findings; they
are not a conclusion that the model cannot be applied here.

Its 64x64 basin-patch preprocessing is not fully released. Native inputs also
include US-specific Daymet, NLCD and agricultural-drainage information. Existing
European weather means cannot reconstruct missing within-basin spatial grids.
ERA5-Land, global terrain/soils and European/global land-cover alternatives can
support a documented adaptation, but require source/unit/class checks.
Unobserved drainage is not zero drainage; upsampling 9-km weather does not
create 1-km meteorological information.

There is also a schema discrepancy to resolve from the actual checkpoint:
the paper's monthly inputs list temperature minima/maxima, while repository
inventory/normalization examples include `tmean` and `wind`. The grouped loader
reads channel lists and slices from the prepared store/checkpoint. Thus neither
the generic YAML nor the paper alone establishes the precise runnable input
tensor. Source preprocessing, categorical crosswalks, physical units and frozen
pretraining normalizers must follow the selected trained artifact.

Obtaining that artifact and its schema is the next useful action. Downloading
the entire US training collection would not resolve the European extraction
problem by itself.

### 4. Temporal support must be comparable

Use 2017 as the first matched descriptor reference, maintaining the completed
AlphaEarth convention. Annual or sequence inputs must not absorb the test
year's flood or later years through whole-record averages. If the native
physical encoder requires longer climatology, document a pre-evaluation cutoff,
share corresponding raw information with C1 and label the support explicitly.
Do not import the Basin2Vec package's all-years average as a 2017 descriptor.

This remains retrospective information-content evaluation. Later pretrained
model releases are not evidence that these assets were historically available
to a warning service. Frozen encoding does not establish geographically unseen
pretraining; the claim concerns held correction labels and held river groups.

### 5. Geometry and missingness require explicit handling

Prepared the full **394-reference-polygon inventory**: seven local, 337 regional
donor and 50 external records. The existing no-verification cases remain in the
inventory; all available verification remains in evaluation. Canonical gauge
IDs are linked explicitly to local geometry aliases such as `herzogenrath_1`.

Three donor polygons had self-touching rings. The new processing copy uses
`make_valid`; all three repairs are topologically equal to the originals, with
absolute area changes below 0.000001 m². Original source files, source hashes
and completed AlphaEarth means are unchanged. All 394 processing geometries
are valid. Receipts: `geometry_repairs.json`; inventory and processing GPKG are
under `results/limburg_representation_extension_v1/`.

For the selected TESSERA Icechunk store, `NaN` scales mean unembedded/source
nodata; they are not sufficient evidence of water. The earlier generic
NaN-as-water statement was corrected after inspecting the native Icechunk
adapter and reader. Retain source completion/missingness, check scale quality
and use independently justified masks if separating water. Dequantize **each
pixel before averaging**; averaging integer codes and an average scale is not
equivalent. Save weighted sums, weights, second moments and coverage, with
mean pooling retained as primary. Aggregate native-grid pixels over the same
reference polygons, including correct treatment of the UTM 31/32 boundary and
overlapping catchments. Record masking/support differences from AlphaEarth.

The full eligible census is retained. Report paired supported comparisons and
coverage; do not silently replace it with the intersection of convenient model
coverage. Define and disclose any conventional fallback before scoring. An
absent embedding is not a dry condition or a zero vector.

### 6. Preserve the evidence and avoid another uncontrolled search

The new extension is exploratory: AlphaEarth's test outcomes are known. Keep
the existing chronological and river-group assignments, three final seeds,
four tuning candidates, two selection policies and 3,000-tree budget. Retain
native descriptor widths initially; equal dimensions do not imply equivalent
information. Use the same date/year draws across all heads and report every
declared representation, including harms and undefined results. No new formal
preregistration requirement is introduced.

The five-head controlled family has **5,700 logical fit slots**:
30 outer jobs × 5 heads × 2 policies × (4 candidates × 4 inner folds + 3 final
seeds). Original completed H/H+A models need not be blindly refitted, but C1 and
its four representation additions do. Do not duplicate the 0.84-GiB historical
daily feature table for every encoder; join small descriptor tables at fit time.

Benchmark actual memory, selected-tree saturation and time on one matched
outer fold before forecasting the full runtime. Two CPU fitting workers with
two threads each remain a sensible starting point after measurement. Encoding
may use a verified CPU or available MPS route; CUDA-only examples do not prove
Mac support. No measured runtime estimate exists for these new adapters yet.

## Further data: required, held and outstanding

| Input | At hand | Further work / acquisition |
| --- | --- | --- |
| Local and regional observed Q, source qualifications, GEOGLOWS, existing daily weather | Yes; completed common data spine | Reuse. No new request to René or Jens is needed for this extension. Keep known high-flow qualifications. |
| All reference catchments, roles, IDs and fixed splits | Yes; new 394-row inventory prepared | Use the processing copy with saved source/repair hashes. No new basin is required. |
| AlphaEarth 2017 means and original conventional descriptors | Yes | Reuse as features; fit against the enriched C1 where required. |
| TESSERA 2017, native 128 bands, per-pixel scales and masks | Provider store and metadata accessible; pixels/means not yet acquired | Stream the existing 394 polygons and save means, valid area/counts and source/version receipts. No raw Sentinel collection or model training is needed if published pixels provide support. |
| StefaLand trained encoder or author-provided European annual descriptors | One candidate weight file held; intended runoff-free route unresolved | Verify/procure the appropriate encoder, complete normalizers and a reference input/output recipe or the authors' descriptor export. Do not assume the candidate is the Liu et al. encoder. |
| StefaLand physical/climate inputs | Some weather/terrain/land-cover and regional soil summaries held | Exact missing columns follow the verified encoder. Likely additions include Tmax/Tmin, PET, NDVI/grass cover, soil texture/depth, porosity/permeability and related native attributes. Published pretraining and candidate schemas differ; this list is not a command to download every dataset used anywhere in the paper. |
| Basin2Vec trained encoder, channel metadata and pretraining normalization | Code and some normalization examples held; trained encoder not located | Request/locate the actual artifact and its native tensor schema, metadata scaling and categorical encoding. US output vectors are not European inputs. |
| Basin2Vec 2017 monthly/static basin grids | Not assembled | Matched grids for precipitation, temperature variables, solar radiation, vapour pressure and SWE; annual PET/land cover; selected soil/terrain/hydrogeology and any required population/drainage layers; masks and native basin geometry metadata. Exact channels/depths follow the checkpoint. |
| Raw C1 controls corresponding to extra inputs | Partially held, not assembled | Use the same acquired input families to create declared compact summaries and geometry descriptors. No separate observational campaign. |

Open/clear acquisition leads: existing ERA5-Land via Earth Engine/CDS for
temperature extrema and snow; native MSWX/MSWEP access for StefaLand where
available; MODIS vegetation and ESA/Copernicus land-cover products; ISRIC
SoilGrids/HWSD, global terrain and GLHYMPS. These require verifying the chosen
artifact's units, source definitions, licence/access and vintage. The held
CAMELS-DE soil table already contains texture, coarse fragments, bulk density
and organic carbon at three depth ranges; those are useful summaries but are
not automatically the native HWSD variables or the required spatial rasters.
Do not use stored full-period climatic/hydrological signatures as if they were
pre-test predictors. Old soil/snow files need polygon/date/source checks before
reuse and cannot fill missing coverage for all 394 catchments by assumption.

Two possible author requests are now concrete: StefaLand's appropriate encoder
or 2017 descriptor export plus its normalization/masking recipe; Basin2Vec's
trained encoder, channel/metadata definitions and new-European-basin extraction
guidance. Brian sends any emails. None was sent by this audit.

No new flood labels, interviews, local surveys, hydraulic data or current/live
gauge feeds are required by this reconstruction comparison.

## Disk assessment and storage design

The audit measured about **77–78 GiB free**. With the retained 50-GiB operating
reserve there is approximately **27–28 GiB of immediate working allowance**.
The chapter uses roughly 546 GiB of allocated directory storage at the census
snapshot; about 484 GiB is under `data/`, with roughly 398 GiB under
`data/processed/`. These `du` values are not promises of exclusive reclaimable
APFS space; hard links and shared extents matter.

Measured polygon geometry gives the following payload calculations for one
TESSERA reference year:

| Storage form | Approximate payload |
| --- | ---: |
| 394 catchment areas summed, retaining overlaps | 69,502 km² |
| Unique union area | 38,667 km² |
| All unique 10-m pixels × 128 × float32 | **184.38 GiB** |
| Separate catchment float32 rasters, duplicating overlap | **331.41 GiB** |
| Unique pixels × 128 × int8, before scales/masks/compression | **46.10 GiB** |
| Final 394 × 128 float32 catchment means | **0.19 MiB**, before metadata |

The actual provider store is quantized int8 with per-pixel float32 scales,
compressed indexed shards and 32×32 internal chunks. The metadata and public
object access were verified; actual catchment support and compressed transfer
bytes still need a read benchmark. **184 GiB is a storage arithmetic estimate,
not a measured download size.** Bounding chunks, data masks and repeated range
requests affect transfer. Even quantized full-pixel retention exceeds the
allowance above the current reserve.

Use streaming aggregation rather than retaining full mosaics. A 512×512×128
float32 window is 128 MiB before masks/temporaries. Process overlapping
catchments from shared chunks, save resumable sum/weight/coverage receipts and
compact descriptor outputs, and bound any provider fetch cache. Provider-native
dequantization and source-object identity matter; no arbitrary pixel sampling
is needed to save space. If unique source material must be retained, use the
existing Azure recovery route with verification before local retirement.

StefaLand's tabular annual input and descriptor products should be small once
the recipe is known. As a planning example, 394 basins × 365 days × 6 float32
forcing variables is **3.3 MiB**, before attributes/masks. This does not include
native source retrieval or a longer required climatology. A Basin2Vec example
with six monthly channels and 64 static channels on 64×64 patches is about
**0.82 GiB** for 394 basin-years, before metadata and temporary copies; its
actual checkpoint channel count is still unknown. Neither calculation is a
claim that every required source raster is already held.

A provisional **8–16 GiB local working allocation** for isolated environments,
bounded read cache, physical patch inputs, descriptors and fitted-head outputs
appears compatible with current free space. It is an allocation to verify, not
a new scientific data cap. Expand streaming/offload if actual requirements are
larger. There is no need to retain every downloaded TESSERA pixel on the Mac or
to purchase GPU cloud compute for this audit.

Older mapping/correction/tensor products remain potential offload candidates
after dependency and recovery checks. They were not deleted or offloaded here.
The completed AlphaEarth evidence, inputs and native weight assets are
protected; other chapters are untouched. No cleanup is required merely to
retain the approximately 65 MiB of new audit material and candidate checkpoint.

## Next work in useful order

1. Continue AlphaEarth evidence consolidation while preparing all three model
   routes; no need to suspend the existing chapter for a missing release.
2. Test TESSERA's actual polygon coverage, aggregation and transfer/cache cost
   with source-native decoding; then acquire the full declared catchment census.
3. Resolve exact StefaLand/Basin2Vec artifacts and recipe questions. Their
   inclusion is agreed; do not invent inputs to make an unknown checkpoint run.
4. Assemble the required clipped 2017 physical inputs and C1 summaries. Freeze
   input/unit/normalization/coverage tables and confirm observed-Q exclusion.
5. Perform native-adapter and one-fold resource/parity checks, then schedule the
   common comparison. Report all model results and source/mapping limitations.

## Evidence locations

- Source snapshots, pinned repository trees and HTTP probes:
  `data/raw/limburg_representation_extension_v1/review_sources/`.
- Candidate checkpoint and receipt:
  `data/raw/limburg_representation_extension_v1/candidate_weights/`.
- Census, processing geometries and repair receipts:
  `results/limburg_representation_extension_v1/`.
- Durable audit/measurement record:
  `docs/reviews/limburg-representation-extension-audit-2026-11-18.json`.
- [TESSERA client and source conventions](https://github.com/ucam-eo/geotessera).
- [StefaLand v3 methods and source tables](https://arxiv.org/html/2509.17942v3).
- [Newer StefaLand embedding-generation guidance](https://github.com/nrkraabel/PaperReleaseStefalandParameterization).
- [Basin2Vec code, known preprocessing gaps and input schemas](https://github.com/Muhammad-Talha-MT/basin2vec).
- [Existing completed results](limburg-dise-repeatability-2026-11-18.md) and
  [contribution assessment](reviews/limburg-dise-contribution-assessment-2026-11-18.md).
- [Verified paper citations](limburg-representation-extension-literature-2026-11-18.bib),
  kept separately from the Mendeley-generated bibliography.
