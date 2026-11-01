# Limburg: applied research-design and literature review

1 November 2026. Internal research aid for Brian; not dissertation prose.
Review and recommendations only: no new fits, worker changes, revised RQ or
automatic expansion of the analysis. Read with the [current plan](../limburg-applied-study-plan-2026-11-01.md)
and [runtime/evaluation preparation](../limburg-applied-preparation-2026-11-01.md).

## Assessment

The move toward spatial flood information is scientifically defensible and
closer to the intended use of these encoders. Keep the applied question about
accuracy, coverage, transfer and resource requirements. However, engineering
readiness is ahead of comparison readiness: the simple physical baselines,
label-cost accounting and event-level synthesis need finishing before treating
the new comparisons as evidence of practical added value.

This is an extension with a different target from the discharge experiments,
not simply a corrected rerun of them. Keep the earlier negative/conditional
discharge findings visible. Neither branch establishes the performance of the
complete Dutch or German operational forecasting service.

The strongest potential contribution is a **qualified account of when particular
mapping pipelines provide useful flood information and at what cost**, including
local acquisition timing and blind spots. Merely applying several encoders,
testing fewer labels or measuring laptop speed is not by itself a new gap.
There is very close new prior work on Prithvi Tiny; see below. This calls for
clearer positioning, not more models or a blanket stop.

## What is already sound

- Four task-specific uses replace a universal encoder ranking. Frozen probes,
  spatial decoders and full fine-tuning answer different practical questions.
- Separate whole-event training, validation and test sets are stronger evidence
  of transfer than random nearby-patch splits. Keep every eligible test record.
- Candidate selection uses validation scores; test scores do not select the
  learning rate. Preserve this separation in downstream review and tuning.
- Unknown pixels stay unknown. Permanent water, visible water, new inundation
  and evidence of earlier inundation are explicitly different targets.
- Native CPU runtime checks establish executable architecture and gradients;
  they do not claim accuracy, convergence or production throughput.
- The existing plan counts preprocessing/tuning costs and limits local claims
  to a case application. No additional model family is needed.

## Findings and recommended corrections

### 1. Finish the comparators promised in the plan

The tuning runner currently offers a pixel-linear classifier and a small
16/32-channel, single-downsampling U-Net alongside the named model. Those are
useful controls, but do not exhaust the practical alternatives. A 1x1 linear
classifier is not equivalent to a normalized-difference water index, and a
small learned network is not a physical pre/post radar-change detector.

Add a validation-tuned optical index/threshold control using the bands actually
available to the corresponding task, and a simple radar threshold/change
control for the paired-radar task. Preserve identical held events and valid
support. Separate fixed published thresholds from validation-selected ones.
Do not tune them on local reference outcomes. Document which target each
control can represent; a single optical image cannot independently establish
new inundation without an appropriate baseline.

Report the compact U-Net architecture honestly. If it is poorly converged or
clearly capacity-limited, a win over it is insufficient evidence of superiority
over conventional segmentation. Inspect training/validation curves before
expanding anything. An architecture-matched random initialization is needed
only if attributing a benefit specifically to pretraining; practical pipeline
comparison does not require that causal attribution.

Evidence: `scripts/192_tune_applied_water.py` constructs `nn.Conv2d(...,1)` and
`CompactUNet`; `src/applied_spatial_models.py` defines the compact network.
Relevant precedents: PANGAEA, WorldFloods, Farajpoor and Narimani.

### 2. Correct the meaning of the label budget

The 100/20/5% settings reduce labeled training chips within each training event;
the entire validation event remains labeled. Say **training-label fraction**,
and also report unique training-plus-validation labels used for selection.
Do not call this a 95% reduction in all labeling work.

A metadata-only audit of the prepared folds finds:

| Dataset | Training chips at 5% | Fully labeled validation chips | Training + validation as fraction of all available training + validation chips |
|---|---:|---:|---:|
| Sen1Floods11 | 21–25 | 15–69 | approximately 10–23% |
| Paired radar | 93–258 | 9–2,425 | approximately 5–61% |

These are inventory counts, not model results. The denominator excludes the
outer test event. Report both counts and label provenance; chips are not equal
annotation hours. Test-reference creation is a separate evaluation cost.
The [metadata receipt](limburg-applied-design-metadata-2026-11-01.json) records
fold-level counts for seed42, input hashes and radar acquisition-gap summaries.

The runner also drops every final short training batch. At small budgets and
large batches, that can remove a substantial share of selected chips in an
epoch. Preserve all selected training examples with an appropriate batching
policy (for example, merge a singleton into the preceding batch where batch
normalization requires it), or explicitly report effective per-epoch use.
Evaluation already retains all records. Do not silently change the published
budget interpretation to match what happened to fit in complete batches.

### 3. Bounded tuning is fairer, but is not proof of adequate optimization

Three task-centered learning rates per learner are a reasonable finite search.
Different native heads, losses and frozen/full fine-tuning policies mean this
tests named pipelines, not the encoder in isolation. Equal epochs do not mean
equal optimizer updates, convergence or computing cost, particularly across
label budgets. Retain curves, selected epoch, failed trials and endpoint winners.

One validation event per fold limits selection stability. Report its identity
and size. Do not choose a better validation event after inspecting test scores.
Bootstrap matched event differences, not pixels; distinguish training-seed
variability from variation across events. With 11 or 20 events, interval precision
is limited and many model/budget comparisons remain exploratory. Do not turn
each favorable subset into a separate confirmatory discovery.

The full Cartesian plan implies **4,293 candidate fits**: 2,673 for three
binary tasks and 1,620 for radar change, before any additional controls. This
is an execution-size calculation, not a proposal to run them immediately.
Finish measured profiles and the full-label comparisons first, preserving the
whole outer-event census. Retain the lower-label comparisons as planned stages;
do not reduce the event census simply to make a very large tuning grid fit.
No new arbitrary scientific gate or fixed accuracy cutoff is warranted.

### 4. Treat local references as reference agreement, with explicit support

The 43 prepared grids are not 43 independent floods. Venlo, Eschweiler and
Wassenberg are July 2021 AOIs with shared storm/source dependence. The two German
AOIs do not automatically correspond to the Wurm gauge catchment. These cases
cannot establish country-wide NL–DE performance differences.

Pool confusion counts within an AOI/acquisition before deriving its IoU, then
show AOI-level outcomes. Do not average tile IoUs as though tiles were independent
events. Retain model-specific observable coverage as well as comparisons on
common valid support: otherwise clouds or SAR-insensitive areas disappear from
the apparent performance cost. Unknown area is not a true negative.

Existing local target conventions exclude hydrography and historical flood
traces where they do not establish contemporaneous flooded area. Outside a
mapped flood polygon within assessed coverage means *mapped non-flood*, not
independently observed dry ground. Reference/source dependence and time offset
remain qualifications even after geometric alignment. Local scoring195 provides
per-grid metrics; the case-level synthesis and uncertainty are still to finish.

### 5. Make acquisition timing part of practical interpretation

Roth et al. (2026) provide a directly relevant operational precedent: satellite
flood-map evaluation can use hydrological observations to assess temporal
coverage. Apply that idea using held records, only where a gauge represents
the mapped reach: place each acquisition on the rise, near the peak or during
recession. State the time difference between imagery and reference observations.
Do not invent a gauge–AOI link, infer flood pixels from p99, or equate satellite
acquisition with product delivery. If delivery timestamps are unavailable,
report that limitation rather than estimating warning lead time.

This is an interpretation aid using existing data, not a new hydrological or
forecast model. It helps distinguish a spatial detection error from a satellite
observing a different phase of the flood. It also connects mapping to FEWS/DRR
assessment without asserting operator benefits that have not been evaluated.

### 6. Audit the physical meaning of pre/post change

The radar inventory's 5,000 records have SL1-to-event gaps with median12days,
75th percentile48days, 95th percentile228days and range6–528days. There are
1,162 records with gaps above90days and15 above365days. These are source
metadata counts, not evidence of model failure; chip counts are event-weighted.

Retain the author-compatible primary route, but show gap distributions by
activation. Long gaps can include seasonal, vegetation or land-use changes.
An apparent transfer difference may therefore reflect reference-gap mismatch,
not merely an encoder deficiency. The held SL2 alternative can be inspected
before deciding whether a sensitivity is useful; do not automatically add
another extraction or substitute a different pre-image after seeing benefits.
Same-input comparators remain essential.

## Per-model review

| Pipeline | Appropriate question | Interpretation and unresolved limitation |
|---|---|---|
| TerraMind Tiny, frozen paired S1/S2 encoder + decoder | Does a multimodal spatial representation improve water mapping or resource/label trade-offs over matched paired inputs? | Keep native modality preparation and decoder. Radar/optical time differences and optical blind spots matter. This is a multimodal pipeline comparison, not an isolated fusion benefit. |
| Galileo Nano, frozen radar spatial probe | Are the retained spatial tokens useful for a lightweight radar readout? | Native radar normalization and real month metadata are appropriate. A linear spatial probe tests accessible features, not the model's best possible fully fine-tuned performance. |
| Prithvi EO2 Tiny-TL, six optical bands + full fine-tuning | Is this compact optical adaptation competitive at stated label and compute budgets? | HLS pretraining and held Sentinel-2 L1C inputs differ. The224px adaptation and upsampling constrain spatial detail. Do not call this an exact reproduction of larger Prithvi results. Closest new prior work overlaps substantially. |
| Copernicus-FM, pre/event SAR features + native heads | Does this source-compatible paired-radar pipeline distinguish permanent water from event flooding more usefully than matched controls? | Native compiled CPU runtime is now verified. Pre/post timing and asymmetric author normalization must be recorded. CPU smoke success does not establish MPS compatibility or feasible full-grid throughput. |

Keep model-specific target questions under the shared applied question. No
need for four new dissertation RQs. AlphaEarth and TTM remain contextual assets
of the discharge/analogue work; they need not be forced into pixel mapping.
The other six encoders need not acquire new spatial tasks to maintain symmetry.

## Literature review and positioning

This is a targeted methods and positioning review, not a systematic search.
Primary sources, model documentation, held literature and current code were
compared. Publication status is explicit.

| Source | Status and access | Consequence for this design |
|---|---|---|
| [Farajpoor & Narimani, Accuracy and efficiency of compact foundation models for surface-water mapping during floods](https://arxiv.org/abs/2610.34904) | Preprint,26October2026; abstract and HTML full text inspected | Very close overlap: Prithvi Tiny, the same446 optical chips, label amount, excluded events, strong controls and computational cost. Avoid a first-study claim. Its shared hyperparameter selection across event exclusions also cautions against copying its protocol uncritically; retain our validation-only outer-event separation. |
| [Roth et al., Performance of Dual-polarization Sentinel-1 Flood Monitoring in Austria](https://link.springer.com/article/10.1007/s41064-026-00417-7) | Peer-reviewed open-access article,3September2026; publisher full text inspected | Strong practical precedent for acquisition-phase assessment using hydrology, alongside visibility/terrain limitations. Reuse held observations where geographically valid; do not add another model. |
| [Schindlegger et al., ESA CIN TerraMind/THOR project](https://cin.philab.esa.int/databases/projects/a-systematic-comparison-of-terramind-and-thor-downstream-deployment-architecture-outweighs-model-choice-in-geospatial-foundation-model-performance) | Institutional project report; publication field remains incomplete, not a verified journal article | Decoder/tokenization choices can be consequential within the explored configurations. Interpret our outcomes as pipeline-specific; this does not justify adding THOR or reproducing its large ablation grid. |
| [PANGAEA](https://arxiv.org/html/2412.04204v2) | Primary manuscript and held text checked | Strong supervised controls and explicit preprocessing are central. Foundation-model superiority cannot be presumed. |
| [Corley et al., Resizing and normalization matters](https://openaccess.thecvf.com/content/CVPR2024W/PBVS/papers/Corley_Revisiting_Pre-trained_Remote_Sensing_Model_Benchmarks_Resizing_and_Normalization_Matters_CVPRW_2024_paper.pdf) | CVPR2024 workshop paper; held extracted text inspected | Justifies sensor/band/resolution contracts and explicit adaptation. Preprocessing fidelity is necessary but does not guarantee added value. Held bibliography uses its earlier arXiv identity. |
| [WorldFloods / Mateo-Garcia et al.](https://www.nature.com/articles/s41598-021-86650-z) | Peer-reviewed2021 paper; indexed publisher methods checked; direct publisher opening failed | Prior art for simple spectral/learned baselines and practical processing constraints. Surface-water classification must not be relabeled as complete flood extent. |
| [Kuro Siwo](https://proceedings.neurips.cc/paper_files/paper/2024/hash/43612b0662cb6a4986edf859fd6ebafe-Abstract-Datasets_and_Benchmarks_Track.html) | NeurIPS2024 Datasets and Benchmarks; primary record and held documentation checked | Supports temporally explicit radar benchmarking. Our held20-activation subset is not the entire published dataset. |
| [GEOID-Flood](https://arxiv.org/abs/2608.02315) |2026 preprint; record reports ECCV Terrabytes II workshop acceptance; primary record/HTML checked | Multimodal/pre-post flood transfer is already an active benchmark area. No need to acquire this larger dataset merely to claim novelty. |
| [Schmalstieg et al., Edge flood segmentation distillation](https://arxiv.org/abs/2609.20441) |2026 preprint; primary record checked | Computing cost is an established practical question. Distillation is precedent, not another chapter experiment. |

Additional primary model sources checked against the held implementation notes:
[Galileo](https://proceedings.mlr.press/v267/tseng25a.html),
[Copernicus-FM official repository](https://github.com/zhu-xlab/Copernicus-FM),
[Prithvi EO2 manuscript](https://arxiv.org/abs/2412.02732) and
[Tiny-TL model card](https://huggingface.co/ibm-nasa-geospatial/Prithvi-EO-2.0-tiny-TL).
TerraMind's ICCV2025 paper and held author task configurations are part of the
existing model-use review. No claim that every model publication was reread in full.

Search date:2026-11-01. Query families included compact/foundation-model flood
segmentation, Sen1Floods11 label efficiency, benchmark normalization/resizing,
SAR operational flood-map validation and hydrological timing, TerraMind/THOR
decoder comparisons, and the four named model documentation sources. These
were targeted discovery and verification searches; no exhaustive-review claim,
screening count or new systematic-review component is implied.

New citation records are in
[the dated bibliography](limburg-applied-literature-additions-2026-11-01.bib).
Earlier task citations remain in the
[existing task bibliography](../limburg-applied-task-literature-2026-10-31.bib).
No Mendeley synchronization is claimed by this file.

## Smallest worthwhile next pass

1. Finish physical controls, batching/label accounting and per-event aggregation.
   Keep the current outer-event census and validation-only selection.
2. Use device profiles and curves to schedule the full-label comparison first;
   subsequently execute the declared label-budget stages with actual total cost
   recorded. Keep failed runs visible. No automatic4,293-fit submission.
3. Interpret local maps with their timing, source dependence and observable
   coverage, using held reach-relevant hydrographs where possible.
4. Report the accuracy/coverage/cost trade-off even if gains are absent. A cheaper
   pipeline with comparable accuracy can be useful, but equivalence cannot be
   inferred from an interval crossing zero: report differences and intervals,
   and justify any practical tolerance before using it to declare comparability.

No new external dataset, email request or encoder is essential for this pass.
Existing reference metadata, date/coverage checks and strong controls are more
valuable now than adding another source. Deployment/user evaluation, new flood
forecasting, distillation and a renewed RAG experiment remain outside this pass.
None of these recommendations creates a chapter-stopping rule or an empirical
result. Brian retains all dissertation writing.
