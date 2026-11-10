# Limburg: literature and methodological comparison — 10 November 2026

Internal research aid; Brian writes dissertation prose. Targeted comparison of primary papers, author code and this chapter's executed adapters. Not a new systematic review, new fitting run, or a declaration that any configuration change will improve performance. Companion JSON binds inspected local source files by SHA256.

## Assessment

Our strongest limitation is the match between substantive question, observable information and task-specific learning. Reproducibility/integrity is relatively mature. Evidence that each adaptation exercises the published capability, reaches a useful operating regime and answers a consequential flood question is less complete. The prior suggestion to proceed directly to narrative synthesis was premature: a small number of concrete methodological uncertainties should first be separated from genuine unfavorable results.

The work is simultaneously broad across tasks and narrow in independent environmental diversity. Eight gauge series, nested catchments and repeated observations are not eight independent regional hydrological systems; 720 fits reuse the same mapping datasets. Taking the eligible census is sound, but does not create more independent extreme floods. Neither this fact nor an unfavorable interval creates a chapter stopping rule.

## What comparison papers actually did

| Primary study | Method/result relevant here | Difference from our work |
|---|---|---|
| [Kratzert et al., HESS 2019](https://hess.copernicus.org/articles/23/5089/2019/) | Trained rainfall–runoff networks across 531 catchments using meteorological sequences and catchment attributes. | Their transferable representation is learned directly for hydrology across diverse basins. Our EO backbone was generally learned for a different task, then pooled and given a simple discharge readout. |
| [Nearing et al., Nature 2024](https://doi.org/10.1038/s41586-024-07145-1) | Large-scale supervised hydrological learning; historical drivers and meteorological forecast inputs feed the forecasting architecture. | Our next-day assessment without meteorological forecasts asks a different information-limited question. Their claimed forecast improvements cannot be treated as expected results for our EO adaptations. |
| [Li et al., GeoAI 2023](https://arxiv.org/html/2309.14500v2) | U-Net won their ordinary test comparison; Prithvi performed better on the separate Bolivia transfer set. They used a 100M model, class-weighted loss and cropped input. | Our Tiny adaptation and event-held-out design do not recreate that experiment. Importantly, their positive result was specifically transfer, not universal accuracy superiority. |
| [TerraMind, ICCV 2025](https://arxiv.org/html/2504.11171v1) | The paper includes frozen Base/Large backbones with UPerNet and separate full-fine-tuning experiments. | Our Tiny frozen-backbone/UNetDecoder pipeline is a valid configuration but not reproduction of those headline systems. Freezing alone cannot explain everything: some strong published results also freeze encoders. |
| [Galileo, 2025](https://arxiv.org/html/2502.09356v1) and [author evaluation](https://github.com/nasaharvest/galileo) | Spatial probing, input/scaling choices and learning-rate searches are part of downstream evaluation. | Patch size, search breadth, evaluation population and metric differ from our applied run; see confirmed code differences below. |
| [Copernicus-FM, ICCV 2025](https://arxiv.org/html/2503.11849v1) | Its Flood-S1 table does not show a general win over its supervised ViT control; reported task score is multiclass mIoU. | Our target-class event IoU and event-held-out evaluation are different quantities. The original paper does not predict an inevitable flood-task win for us. |
| [WorldFloods, Scientific Reports 2021](https://www.nature.com/articles/s41598-021-86650-z) | Trained spatial water mapping with 119 flood events and tested independent locations plus a constrained hardware/downlink use case. | The practical bottleneck and output are defined together. Our device contention logs do not establish an equivalent end-to-end service improvement. |

The broad [PANGAEA benchmark](https://arxiv.org/html/2412.04204v1) also reports strong supervised baselines, domain-transfer losses and inconsistent fine-tuning benefits. It explicitly examines normalization, resolution, temporal aggregation and convergence. Positive AI results are therefore not a single uniform standard we have somehow failed to reach.

## Confirmed differences that matter

### 1. Galileo spatial granularity and tuning

`src/applied_spatial_models.py` hardcodes `patch_size=8` and the corresponding 8-by-8-pixel readout. Held author `eval.py` defaults to patch size 4, matching the paper's variable-patch evaluation description. The Nano checkpoint supports patch sizes 1–8, so 8 is supported; it is not the default evaluation route. A 4-pixel route requires correspondingly consistent token/readout dimensions, not changing one number in isolation.

Held `src/eval/linear_probe.py` declares 16 learning rates from 1e-4 to .8; our applied tuning uses .0002/.001/.005 for Galileo. All 15 seed-42 selections lie at a boundary; 20 of 45 native selected runs have best epoch at the ceiling, including all 15 at 20% labels. These are reasons to investigate the optimization regime. They do not show that wider search will fix the 5% deterioration.

The author preprocessing retains water-positive 64px subpatches; our applied population retains dry patches. The author evaluation reports mIoU across classes; ours emphasizes target-class IoU and averages by event. Reproducing the original population/metric separately is useful for checking the adapter; the applied evaluation should retain dry land and event separation so false positives and transfer remain visible.

### 2. Prithvi spatial support and model identity

Our Prithvi model is fully trainable, about 12.9M parameters including the task head. It is not an accidentally frozen experiment. `src/applied_fast_data.py` resizes the entire image and nearest-neighbor training target to 224px. The older positive paper used cropped inputs. Shrinking an entire 512px scene can remove narrow wet features; crop-based training preserves their original scale. Both our raw controls and the native model share the resized support, so this is a task-design tradeoff, not an established unfair comparison. Original-grid scoring cannot restore information already removed from the model input.

A supported crop/window or flexible-size route deserves comparison before interpreting this as a general limit of the model family. Source-card support, target alignment and inference tiling must be checked first. The fact that the previous positive paper used a larger, different model does not prove that size explains our result or require downloading all larger models.

### 3. TerraMind adaptation

The encoder is explicitly frozen in our adapter. Full fine-tuning or a supported lightweight adaptation would answer whether task adaptation changes performance; our existing run answers the narrower frozen-Tiny configuration question. A fair follow-up would retain current comparators, support and label accounting, and use validation for configuration choices. An author [issue/example](https://github.com/IBM/terramind/issues/38) recommends backbone fine-tuning for best performance, but that advice is not evidence that it will improve our held-out floods. The original paper's frozen-backbone successes must remain visible as well.

### 4. Performance reproduction before negative family-level conclusions

Our records demonstrate strict weight loading, real forward/backward passes, cached-path equivalence, complete sample handling and final output integrity. I did not find an end-to-end reproduction of a reported author accuracy result under its exact checkpoint/split/metric. Engineering validation and performance reproduction are different checks. A small training-set learnability check, author/adapted path agreement, and one appropriate reference setup would help distinguish adapter behavior from the intended scientific transfer test. An absent published score for an exact Tiny checkpoint limits the available reproduction target; do not invent one.

### 5. Attribution to pretraining

The practical comparison against trained U-Net is legitimate. It does not isolate pretraining from architecture/head/optimization. To claim that pretraining itself helps or fails, compare the same architecture from random initialization under appropriate optimization. That is necessary for that attribution, not an automatic new comparator requirement for every practical pipeline comparison.

## Why the discharge question has been difficult

Weekly/monthly EO and annual landscape context can contain land cover, season and some antecedent wetness information. Next-day flood development also depends on ongoing/future rainfall, routing, storage and water already moving through the system. Catchment pooling discards some localization and connectivity. Some later readouts preserve temporal order/zones, so it would be wrong to say we only averaged everything or never trained a readout.

The original equal-block analogue fusion did not learn which representation components predict hydrological response. Later residual heads did, but within a limited, task-transferred hypothesis class. A null from those methods is not a test of all hydrological neural modeling. Conversely, the real-EO/placebo diagnostics and some model-specific gains already show that the imagery is not universally uninformative.

What remains unestablished is how much error in the strongest baseline is actually recoverable from the available EO at the assessment clock. Independent antecedent-state targets or event-conditioned error analysis could diagnose that mechanism. Soil/snow sources and some preparation are already held; acquisition alone must not be confused with completed aggregation/model use. This is a possible diagnostic use, not another compulsory input collection.

## Rigor, scope and framing

Strengths to retain: whole-event/chronological separation, strong same-input controls, full eligible test censuses, unknown coverage, quality/rating checks, storm/year dependence and unfavorable results. Some literature comparisons answer less demanding within-region questions. This is not a reason to weaken ours.

Remaining limitations: repeated inspection of the same events across evolving questions; few independent extremes; model-specific tuning boundaries; mismatched local reference dates/target semantics; training-only label reduction rather than total labeling cost; cost measurements with unequal cache/device conditions. Transparency about exploratory development is needed. Preregistration is not required by this review. A future independent event/region or otherwise untouched test can strengthen a final settled design, but should not be presented as a magic cure for unclear task fit.

Our working questions have sometimes asked broad family-level questions with configuration-specific evidence. They have also combined discharge continuation, water segmentation, flood change, sparse monitoring, cross-border institutions and resource use. Each is legitimate; their mixture obscures the substantive contribution. The right scale is a clear empirical capability claim supported by the models/data it needs. Neither a fixed model count nor a minimum effect-size gate is proposed.

## Recommended sequence, without launching it

1. Complete a model-by-model literature-to-execution matrix, preserving original results. The confirmed differences above supply the priority issues rather than requiring another generic audit.
2. Resolve the Galileo patch/search/stopping questions and Prithvi spatial-support question with controlled comparisons; distinguish supported methodological changes from suspected bugs. Include TerraMind adaptation if the chosen capability claim concerns attainable task performance. Diagnose these before spending on an entire new census.
3. Separate practical pipeline comparisons from pretraining attribution and total-label/compute claims. Add only the evidence needed for the chosen claim.
4. Decide which substantive target the chapter will answer: useful flood mapping/transfer or discharge assessment under an identified information constraint. Keep the other completed work as supporting evidence if it does not explain that target. This is research prioritization, not deletion or a scientific gate.
5. Freeze the revised design before further outcome-driven adaptation, retain its exploratory history, and use independent evaluation where feasible. Continue to inspect actual events; narrative synthesis supplements but cannot replace methodological diagnosis.

No new extraction, fitting, download, package update, data request or email occurred in this review. No positive-result promise and no automatic decision to retire the chapter follows.
