# Design audit: water, new inundation and transfer

10 November 2026. Internal research specification and critique, not dissertation
prose. Sources: held author configurations/loaders, current production adapters,
the completed-study inventories, fresh author papers/repositories and the pinned
external catalogues. No new accuracy result, training or bulk download.

**Assessment:** a scientifically defensible direction, but the previous plan is
not yet an executable specification for the full run. Its principal weaknesses
are underspecified model/data bridges, conditioned evaluation populations,
reference dependence, annotation accounting and an untested novelty claim.
These are corrections to comparisons, not reasons to abandon the chapter or
require positive AI results. Independent preparation can proceed concurrently.
This audit's specifications supersede ambiguous statements in the original plan.
The subsequent [full audit](limburg-three-prong-full-audit-2026-11-10.md) corrects
its cross-document acquisition, compute/refit, normalization and seed-chain details.

## 1. Questions and the contribution

**Main question:** When satellite AI is taken to a new river landscape, what
observations and local training are needed to map newly flooded land reliably?

1. **W — Water:** How accurately can each task-appropriate pipeline map visible
   surface water, including narrow features and difficult surroundings?
2. **F — Flood change:** How do the age and stability of the pre-flood reference,
   a second pre-flood image and terrain affect mistakes between existing water
   and newly inundated land?
3. **T — Transfer:** In unfamiliar landscapes, how much do unlabeled imagery,
   local annotations and supported adaptation improve those maps, relative to
   competent conventional pipelines using the same information?

Reliability, usable coverage and total resource requirements accompany all three
questions. They are not an additional model contest. W establishes the component
capability; F tests the information needed for the substantive flood map; T tests
what a receiving mapping team must supply. Each has its own empirical output.

The methodology is a comparative remote-sensing study with controlled input
ablations, event/geographic external validation, and simulated local annotation.
Methods are segmentation/change models, reference-map construction, spatially
blocked adaptation, paired error analysis and event-level uncertainty.
Do not conflate a method (U-Net) with a methodology (controlled comparison).

### Novelty audit

| Existing precedent | Already established research activity | Our testable extension |
| --- | --- | --- |
| Galileo, Prithvi/TerraMind evaluations | Water segmentation and pretrained-versus-trained controls | W provides a justified capability/geometry foundation; another ranking is not the main novelty |
| Kuro Siwo; GEOID-Flood | Pre/post SAR, terrain, permanent/flood separation and cross-dataset transfer | F measures reference contribution and error propagation at fixed post-event observations, with reference age/disagreement and independent-reference sensitivities |
| Farajpoor & Narimani (2026) | Tiny Prithvi, random initialization, U-Net, labeling fractions, event-excluded accuracy, reliability and compute | Those endpoints alone are now particularly weak novelty claims; distinguish truly budgeted target adaptation, independent development/test events and the flood-change target |
| CIM-TTDA; rapid adaptation; ALFA | Unlabeled adaptation, lightweight adaptation and informative annotations | T measures their actual additional local-information requirements and failure/coverage trade-offs under the same target pools and source-only model selection |

Reference selection itself is also established: [Clement et al.](https://doi.org/10.1111/jfr3.12303) and the [JRC feasibility assessment](https://doi.org/10.2760/653891) discuss multitemporal change, reference water and mapping limits. The novelty is not discovering that pre-flood conditions matter.

These are **candidate incremental contributions**, not claims that nobody has
studied reference age or total label budgets. The focused search found substantial
overlap; it did not prove an empty gap. The original knowledge would be quantified
answers about which complementary inputs/training alter which errors, in which
landscapes and at what coverage/cost. A null still answers that comparison, but
neither a long run nor a novel combination guarantees a substantive contribution.
Interpretation must follow the measured contrasts rather than a promised ranking.

## 2. Use each model for a supported spatial job

The conceptual leap from pooled EO descriptors to next-day discharge is removed
from this run. The four backbones have segmentation/change precedents. AlphaEarth
is a dense annual landscape prior, not an event detector. Earlier ten-encoder
discharge/TTM results remain retained supporting work, not ten new spatial tasks.

| Model | Assigned role and supported basis | Required bridge/check before its full cell |
| --- | --- | --- |
| Galileo Nano | Frozen single-date VV/VH radar features with a learned dense linear readout; held Sen1Floods11 route | Author dB normalization, band/group masks, zero-based month, output layer norm, 10 m input declaration, patch4 **and matching readout**; compare patch8 separately. Reproduce author filtering/splits/metric separately from dry-inclusive event-held-out application. Do not require Nano to equal a Base-model published score. |
| Prithvi EO2 Tiny TL | Six-band optical segmentation, fully adapted encoder and UPerNet; frozen alternative where the contrast requires it | Correct checkpoint, BLUE/GREEN/RED/B8A/SWIR1/SWIR2 order and reflectance scaling; source-card HLS pretraining versus target S2 product disclosed. Native-resolution windows, complete original-grid inference and masks. TL metadata explicitly enabled with correct crop coordinates/time **or disabled as a declared supported setting**, never fabricated. Tiny is not the larger checkpoint in older positive papers. |
| TerraMind Tiny | Actual multimodal spatial features/decoder; frozen reuse and full adaptation | Held task uses **13-band S2L1C + S1GRD**, its own modality statistics and spatial neck. GEOID supplies **pre-event S2L2A**; this cannot be relabeled L1C or made L1C by adding zero B10. Acquire corresponding L1C, or verify checkpoint-supported L2A embedding/statistics and describe that as a different modality configuration. Event-radar + pre-optical is different from paired event-radar/event-optical. Log modality merge, optional modalities and trainable parameters. |
| Copernicus-FM | Frozen per-date SAR encoder + multiscale post-minus-pre features + UPerNet/auxiliary head | Held author data are linear VV/VH intensity with clipping, not dB. Verify radiometric convention (sigma/gamma, GRD/RTC), order, per-date location/day/token-area metadata and exact normalization from pinned loader. Native reference is **one pre + post**. Second-pre and terrain routes require explicit new decoder-side adapters and controls; a loader flag is not proof the model consumes them. |
| AlphaEarth | Earlier-year **dense 64-band** normal/reference-water decoder | Independent water labels, aligned grid, full vectors, valid masks and year/product version. GEOID permanent-water labels are partly AlphaEarth-derived and cannot independently validate this branch. Earlier calendar-year data avoid event-year inclusion, but a product retrospectively released after the event is still not evidence of historical operational availability. |

Same information does not mean applying identical numerical normalization to
different backbones. Preserve a canonical physical raster plus model-specific
transforms, and log both. Fit any learned statistics on allowed source fitting
data only; fixed published/pretraining statistics are external prior information.
Do not use a target-wide fitted normalization under a no-target-adaptation label.

For each exact model/input variant, the contract records checkpoint and code
hashes, channel/units/product, grid and physical footprint, normalization, date/
location metadata, nodata, mask polarity, token/readout shape, task head, loss,
frozen/trainable parameters, optimizer groups, LR/schedule, augmentation and
prediction stitching. Require a real example with statistics/masks/georeference,
strict load, numerical forward/backward and cached/uncached agreement where used.
Missing author reference scores are documented; they are not invented targets.
Reference reproduction, adapter correctness and external accuracy are three
separate types of evidence. No published-score pass threshold is imposed.

For full adaptation, gradients must reach the intended encoder and cached frozen
features must not substitute for it. Attention/normalization precision and Apple
fallbacks need a small CPU/MPS numerical comparison with disclosed tolerances.
Tiny/Nano selection supports implementable compact pipelines; it does not warrant
family-wide claims about larger checkpoints. No new backbone is required now.

## 3. Data quantity, suitability and independence

Fresh checks of retained inventory tables:

- Sen1Floods11: **446 chips / 11 events**, including **52 no-water chips**.
- Held Copernicus-Bench subset: **5,000 records / 20 events**;
  **1,303 contain no flood-class pixels**, but **zero are entirely water-free**.
  Author paper explicitly describes selecting water-containing records.
- Therefore full-census use of this subset is valuable but remains conditioned
  on water presence. It cannot establish whole-landscape false-alarm rates.
  Eleven/twenty events, not millions of pixels or hundreds of fits, define much
  of the independent hydrological evidence.

Retain every eligible test record within each declared dataset population and
report a flow table by physical event, AOI, acquisition, modality and exclusion.
Do not downsample test data to reduce compute or select visually favorable cases.
Whole-area evaluation must retain dry land and dry tiles within the documented
label/validity footprint; unannotated outside-AOI land is **unknown**, not dry.
These event-activated products still do not represent year-round non-flood days.
Independent monitored non-event time coverage would be needed for that claim;
it is not an added prerequisite for acquisition-time mapping.

### Acquisition amendments

1. Use the corrected v2 event-completion GEOID acquisition (v1 retained as history), and reconcile overlapping
   physical events/AOIs and actual label validity before assigning its groups to
   development, calibration or final test. Preserve every eligible final-test
   tile, including no-water tiles; quantify any filtering imposed by the release.
2. Inventory **full Kuro Siwo GRD/labels/metadata**, not just this 5,000-record
   derivative, and WorldFloods/S1S2-Water source pools. Recover missing independent
   source events/landscapes and suitable dry support through their documented
   releases. Full Kuro is advertised as 43 events; pin/reconcile actual release
   counts, radiometry, annotation source and event overlap before selecting it.
   Do not silently mix SLC/coherence into the GRD experiment. Exact extra bytes
   and enlarged training cost are pending inventory, not zero or already budgeted.
3. Audit all 5,000 held second-pre SAR/DEM records for units, true dates/orbits,
   affine/CRS, pixel-centre alignment and validity. File presence is not that audit.
4. Obtain actual product-compatible optical acquisitions. Reconcile label time
   versus each sensor time, rather than regard co-registration as simultaneity.
   Score exact-date/compatible-reference and offset strata separately; no arbitrary
   universal hour cutoff makes a changing flood map valid. Predefine temporal
   eligibility using acquisition/reference evidence before model differences.
5. Acquire dense AlphaEarth only over the independent-label footprint and
   supported earlier years, plus matched reference-water history and terrain.
   Do not inflate the download with unused global layers or substitute annual
   event-year water for a pre-event reference.

**Enough data** means adequate independent event/environment coverage and usable
reference support, not a GiB threshold. Report distributions and learning curves
over available source-event/annotation pools. A broad unseen-region claim requires
actual new-region groups, not merely another date in the same basin. Source
expansion is justified by uncovered landscapes/errors, not by a search for a win.
Estimate detectable/interval precision from source event variability, before
viewing final tests; report limited precision rather than invent a minimum n gate.

Pin release revisions and construct an overlap graph using activation/storm/date,
source acquisition, footprints and parent tiles across datasets. Physical flood
and spatial overlap are separate links: no event may cross event-excluded folds;
no repeated/overlapping landscape may cross the unfamiliar-landscape endpoint.
Repeated later events at familiar sites belong to a separately named temporal
endpoint. Audit model-pretraining/development overlap where disclosed; unavailable
pretraining coordinates remain an explicit unknown, not certified independence.
Previously inspected Limburg cases are a contextual case series, not untouched
confirmatory tests. New external groups are assigned before their scores are seen.

## 4. Specify contrasts, not just a configuration list

### W: visible water

Primary output: water-class IoU by physical event on valid pixels, paired against
the same-input trained U-Net. Secondary: precision/recall, area bias, fixed-distance
boundary errors, geometry/environment strata and acquisition coverage. Report
native/model pixel size in metres and reference uncertainty. Empty-water events
have a separate false-positive area/rate report; an empty IoU must not be silently
dropped or assigned 1 to improve the mean. Pixel-pooled scores are supplementary.

Use all source pixels through deterministic complete window cycles and all valid
test pixels through overlap-weighted logit stitching. Overlap must not duplicate
supervised pixels disproportionately without recorded weights. Track update count,
unique parent/window coverage and full-cycle stopping; equal epochs alone do not
equal equal learning opportunity. Compare corrected support with the retained
resize route as a method contrast, not an outcome-selected replacement.

### F: new inundation

Hold post-event acquisitions, test labels and support fixed for the matched
reference contrasts. Primary outputs: flood-class event IoU difference and the
two directional permanent/flood confusion rates. Also report false-flood area,
missed-flood area, total area bias and coverage for every declared event.

- F0: event water plus cutoff-safe static reference.
- F1: replace reference with nearest compatible valid pre-event observation.
- F2: add the next older compatible observation; retain disagreement/age.
- F3: add terrain to that temporal evidence.
- F4: replace the static normal-water prior with independent-label, prior-year
  AlphaEarth output on its supported footprint; retain the history-only control.

For modular F0–F4, reuse W probability maps. Set subtraction/probability thresholds,
stable-water/disagreement decisions and any unknown/fallback policy using source
meta-validation, never final event labels. Compare F1−F0, F2−F1, F3−F2 and F4−F0
on their exact common support, alongside each route's full-support output. A mask
intersection alone cannot describe the practical cost of requiring more images.

Retain a competent reference-aware physical SAR change control: matched pre/post evidence, source-selected thresholds, explicit reference-water handling and documented masks. A single weak backscatter threshold cannot establish an advantage over current mapping practice. Use the JRC/Clement workflow logic without claiming to reproduce the entire operational GFM service. Its additional inputs and exclusions must be shared/accounted for just as with the neural pipelines.

For direct Copernicus change, keep per-date SAR encoding: F1 uses post−pre1;
F2 supplies both post−pre1 and post−pre2 to a declared trainable fusion/neck;
F3 adds an independently normalized DEM/derived-slope branch at the decoder.
Verify the fusion shapes and nonzero sensitivity/gradients to each additional
input on training fixtures. Do not send elevation through a SAR band embedding
or assume stacking channels is author-supported. Use raw stacked-date U-Net
controls with identical information and support. These F2/F3 adapters are explicit
extensions, not exact author reproductions. Preserve native DEM resolution.

Use acquired pre-image ages/disagreement as descriptors. Where several compatible
references exist, a fixed, metadata-selected alternate-reference policy can test
sensitivity while keeping the post image constant. With only two pre-images,
report their contrast and support; do not promise a precise continuous age curve.
Age-error relationships across events are observational and can reflect season,
orbit or landscape. Water appearing after a reference is new observed water,
not by itself proof of harmful flooding or attribution to a particular storm.
Use documented event-flood references for that stronger label. Derived permanent
water and flood labels must retain separate source/dependency qualifications.

### T: adaptation and local information

Define each task's source fitting, source pseudo-target tuning, calibration and
external test groups in a single manifest. Select hyperparameters inside the
outer source event split. External application uses **three source-refit seeds**
with a declared source pool and source-fixed policy; it does not silently create
a five-fold ensemble or count five correlated models as independent floods.
Calibration labels are disjoint from fitting. If a source refit absorbs them,
generate new legitimate calibration evidence rather than reuse their in-fit logits.
Exact compatible completed states are reusable only when these contracts match.

T0 = source model without target labels or target-fitted statistics.
T1 = separately named transductive unlabeled-target adaptation: specify whether
the whole current target image is available, reset weights between events, bound
updates from source pseudo-target experiments and preserve unadapted predictions.
Target labels cannot choose adaptation steps, pseudo-label thresholds or failures
to exclude. Scoring on an image used without labels is disclosed transduction,
not independent inductive inference. Pin the actual TTDA implementation before
enumerating its full jobs; coastal CIM-TTDA is a template, not a drop-in adapter.

T2/T3/T4 use geographically separated annotation and evaluation blocks, with
buffers derived from image overlap and receptive/geolocation support. Their
same-event adaptation endpoint is distinct from adaptation on prior local floods
and evaluation on a later flood. All current eligible target domains are retained;
incompatible/missing-label cases get a reason, not invented labels or a deletion.

Label budget units are **fully annotated patches/blocks and physical area**, not
isolated sampled pixels. Nested 1/5/20/100% pools refer only to the declared
adaptation area, exclude test/buffer areas and are accompanied by exact counts.
Round small budgets deterministically and mark duplicate rounded budgets rather
than refit identical states. Do not use reference labels to guarantee positives
in a nominally random pool. Include label-map validation, tuning, stopping and
calibration annotations in total local consumption; source/public annotation
and unpaid simulated-oracle labels are separately disclosed. Test labels measure
research evaluation cost, not information supplied to the operational learner.

Retain three end-to-end source→target seed chains (combined training variation,
not separately identified source/target variance). Add **three independent nested annotation-pool
draws** for label-sensitive target comparisons, shared across methods, crossed
with the optimization seeds. This is extra planned work, not three seeds claiming
both uncertainties separately. Keep the full-pool duplicate once per seed.
Informative acquisition shares an initial pool and candidate area, scores only
unlabeled imagery/model outputs and charges every requested full annotation;
matching final positive-class counts by peeking at labels is not permitted.

The primary T contrast is each adapted pipeline minus its own T0 and minus the
same-information conventional pipeline at the same total local budget. Plot
absolute results and paired differences, not only retained source accuracy.
Parameter-efficient/full adaptation is model-supported and consumes raw imagery,
not a frozen-cache shortcut. The exact module/loss/step implementation remains
an identified preparation task; preserve these branches without pretending they
are already executable.

## 5. Statistical and practical interpretation

Use shared physical-event/region bootstrap draws for paired method contrasts.
Summarize seed and annotation-pool variability separately; resampled pixels/folds
are not additional independent hydrological events. Name the primary endpoints
above, report all prespecified contrasts, and label environment interactions and
unplanned event explanations exploratory. Adjust interval/p-value multiplicity
within a stated family if making simultaneous significance claims; no requirement
to call every descriptive interval a formal discovery test. Failure to reject a
difference is not equivalence. Do not declare noninferiority without a justified
application tolerance defined independently of the test results.

Reference errors matter especially at boundaries. Keep common reference masks,
separate label-provenance strata, a resolution/registration sensitivity supported
by documented uncertainty and independent references where held. Do not turn
arbitrary mask dilation into a more favorable primary score. Any new manual
adjudication is a separately budgeted task for Brian, not automatically filled
by an assistant or silently added as a data dependency.

Reliability evaluation uses probability maps and held-out error, class-conditional
calibration, risk–coverage and the fraction/area of true floods omitted or referred
for review. Unknown/unobservable pixels are reported outside confidence abstention.
A confident failure and coverage loss must both remain visible. Conformal theory
does not guarantee new-region coverage without its assumptions. Compare simple
confidence/quality controls before attributing a benefit to a learned reliability
score. Thresholds are selected on development data; actual agency tolerances are
not invented for this study.

Policy-facing outputs: local-data/annotation/technical capacities required to
reuse the pipeline; missed/falsely mapped flood area; review/unknown workload;
accuracy–coverage–resource frontiers. These inform mapping procurement, training
and map-quality practice. They do not measure operator decisions, adoption,
warning lead time or avoided losses. Gauge observations from René/Jens anchor
local event timing and measurement caveats; they cannot validate inundated pixels
or provide the missing spatial flood reference. No new gauge request is needed
for the stated spatial questions.

## 6. Workload and readiness

The previous 6–16 week figure remains a **superseded planning baseline**, not a
current ETA: source-event expansion, actual optical eligibility, independent
annotation draws, decoder adapters and end-to-end source/target profiles have
not been priced. Do not launch a 61-GPU-day Cartesian product from that formula.
Enumerate real eligible comparison cells and reuse only identical verified work;
do not reduce the test census or omit unfavorable configurations to save time.

All requested branches remain in the programme. Run source-reference and complete
end-to-end training/development fixtures first, then each fully specified branch
as ready. A fixture must cover actual preprocessing, model, fit/validation,
native-grid inference, scoring, receipt/recovery and measured memory/time. This
is implementation validation, not an accuracy gate or an instruction to stop all
research. External metadata/acquisition and independent-model preparation can
proceed while another branch's compatibility is resolved.

Current status:

- Completed: design/literature audit, model role assignment, held source/inventory
  review, training-only initial diagnostics, verified 45 GiB imagery offload.
- Outstanding before each affected full run: exact model/input contracts and
  performance-reference checks; added-input raster QA; overlap/development/test
  manifests; target annotation/fusion/adaptation specifications; probabilities/
  calibration handling; measured exact job/resource ledger and recovery paths.
- Independent bulk evaluation inputs are **planned, not yet acquired**. Existing
  model assets and held source data suffice to begin preparation, not to assert
  that the entire revised study is analysis-ready.
- No new fitting queue, model installation or bulk transfer was started by this
  audit; no new empirical result or scientific stop rule was created.

## Primary sources inspected

- [Galileo paper](https://arxiv.org/html/2502.09356v1),
  [author code](https://github.com/nasaharvest/galileo).
- [Prithvi Tiny model card](https://huggingface.co/ibm-nasa-geospatial/Prithvi-EO-2.0-tiny-TL).
- [TerraMind paper](https://arxiv.org/html/2504.11171v1),
  [author code/configs](https://github.com/IBM/terramind).
- [Copernicus-FM paper](https://arxiv.org/html/2503.11849v1).
- [Kuro Siwo paper](https://arxiv.org/html/2311.12056v3).
- [GEOID paper](https://arxiv.org/html/2608.02315v1),
  [author code](https://github.com/links-ads/geoid-flood),
  [dataset card](https://huggingface.co/datasets/links-ads/geoid-flood).
- [Farajpoor & Narimani preprint](https://arxiv.org/html/2610.34904v1).
- [CIM-TTDA](https://doi.org/10.1029/2025JH001145).
- [Clement et al., multitemporal SAR change](https://doi.org/10.1111/jfr3.12303).
- [JRC global monitoring feasibility/resource assessment](https://doi.org/10.2760/653891).
- [Google annual embedding product documentation](https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_SATELLITE_EMBEDDING_V1_ANNUAL).

See existing capability bibliography for ALFA, rapid adaptation, WorldFloods and
uncertainty precedents. The inaccessible Ratté-Fortin full methods remain a lead,
not a verified method recipe. Held sources are pinned independently of live docs.
