# Paper-guided methodological recovery and chapter focus

10 November 2026. Brian authorized the revised recommendation and explicit use of published papers as experimental templates. Internal research plan, not dissertation prose. Earlier results remain intact; there is no positive-result requirement or automatic chapter stop.

## Scientific direction

Prioritize **spatial flood mapping and transfer to unfamiliar river landscapes** as the primary development direction. This fits the models' intended tasks and has direct relevance to public agencies reusing models and reference data developed elsewhere. Retain the completed discharge/analogue studies as distinct supporting evidence; do not rerun them automatically or claim mapping gains imply discharge forecasting gains.

Working question: **How well do pretrained satellite models map water and flood extent in an unfamiliar river landscape, and what observations and local labels do they require?**

This is provisional until the controlled adapter comparisons define an executable final experiment. It is deliberately narrower than "Can satellite AI improve flood assessment?" It does not commit to new institutional fieldwork, interviews, a hydraulic model, or a new large download.

Keep three separately measurable capabilities:

1. Identify observable surface water at acquisition time (binary-water tasks).
2. Distinguish newly inundated land from pre-existing water (paired-image change task with compatible reference semantics).
3. Transfer/adapt each capability to a held-out landscape, measuring source-label, target-label and validation-label use separately.

Do not score binary water as if it necessarily represented new inundation. Do not merge different sensors/targets into a model ranking. A reduction of source training chips is not a demonstration of reduced target adaptation labels. Whether current local references can support adaptation/accuracy rather than descriptive agreement remains an empirical data issue, not a prohibition on research.

## Published templates and what we borrow

- [Galileo paper](https://arxiv.org/html/2502.09356v1) and held release: exact supported input, patch/readout, normalization, reference split/population, LR/schedule and metric for reproduction. Keep the dry-inclusive, event-held-out applied task separate from water-positive reference preprocessing.
- [Li et al.'s Prithvi assessment](https://arxiv.org/html/2309.14500v2): distinguish familiar-region accuracy from geographic transfer; examine crop-preserved detail. Their older100M checkpoint is not our Tiny checkpoint. A Tiny study following that logic is an adaptation, not exact numerical replication.
- [PANGAEA](https://arxiv.org/html/2412.04204v1): task/decoder support, normalization, scale, temporal handling and convergence. Frozen and fully adapted configurations are distinct legitimate experiments.
- [TerraMind paper](https://arxiv.org/html/2504.11171v1): distinguish frozen Base/Large+UPerNet evidence from our frozen Tiny+UNetDecoder and from full fine-tuning. Evaluate an adaptation variant if the final claim concerns attainable task performance rather than frozen reuse.
- [Copernicus-FM](https://arxiv.org/html/2503.11849v1): paired radar change and exact class semantics. Published multiclass mIoU is not our equal-event flooded-class IoU.
- [WorldFloods](https://www.nature.com/articles/s41598-021-86650-z): tie useful output and practical resource constraint together; do not infer service efficiency from busy-worker wall times.

## Work sequence

### A. Source-to-experiment matrix and training-only diagnostics

Record exact checkpoints, products, bands, units, physical pixel scale, temporal inputs, patch size, decoder, frozen/trainable state, loss, optimizer, schedule, stopping, labels, splits and metrics for each template and our implementation. Mark each difference as intentional adaptation, unresolved choice or defect supported by evidence. The [10 November comparison](reviews/limburg-literature-method-comparison-2026-11-10.md) supplies the initial matrix.

Implemented first diagnostics in script229 and `src/applied_reproduction.py`, isolated from completed production sources. Check Galileo patch8 arithmetic parity, supported patch4 outputs, agreement with the author's logit reassembly, and whether a probe can learn two labeled training fixtures. These are plumbing/learnability checks, never test accuracy. Examine Prithvi source-label resampling on matching training fixtures and confirm crop/window coverage without model fitting.

### B. Galileo reference reproduction and applied granularity comparison

1. Bind the exact Nano checkpoint, held author code and reference dataset splits. Reproduce author preprocessing and metrics separately from our applied population. If the exact Nano result isn't reported, compare released and adapted execution paths and state the available reference honestly.
2. Run supported patch4 and patch8 routes with matching readout dimensions. Explicitly report changes in spatial granularity and readout parameter count; this is not necessarily a single-factor architecture comparison.
3. Restore the author LR range/schedule for reproduction. For the applied experiment, document search effort for every trained comparator and inspect boundary/ceiling behavior using validation only. Compare author-style and existing early stopping as a declared protocol comparison, not test-driven selection.
4. Reuse verified patch8 features; write patch4 features to a new versioned cache. All test chips remain held out from tuning. Retain whole-event folds and complete eligible applied evaluation; the initial engineering fixtures do not become the scientific population.
5. Estimate runtime/storage from actual extraction and head fitting before launching the revised full comparison. No fixed unsupported effect threshold or artificial model-count cap.

### C. Prithvi spatial-support comparison

1. Retain the existing fully trainable Tiny/UPerNet adaptation as the historical whole-scene224 reference.
2. Verify supported crop/window input and positional behavior against held source. Build spatially faithful224px windows or a supported flexible-size route. Preserve source georeferencing, masks, metadata and original-grid reconstruction. Crop metadata must represent the crop's location; image-level coordinates cannot be silently reused if spatial position matters.
3. Use paired windows for native and raw-input controls; retain every eligible source scene in evaluation. State whether training samples windows or exhausts them and how overlap affects optimization effort. For inference, specify overlap/logit combination before examining test differences.
4. Diagnose whether useful small-water structures survive preparation. Source-label roundtrip disagreement is a resampling diagnostic, not measured model error and not an attainable IoU bound.
5. Keep class weighting/loss and tuning differences from the older paper explicit. A loss/adaptation change is versioned and applied fairly; do not silently substitute it into completed outputs.

### D. Final scientific comparison

After the methodological comparisons clarify which execution routes support which claims, write one executable design around spatial capability and transfer. Preserve the current competent U-Nets, physical controls and all eligible events. Attribute gains to pretraining only with an appropriate architecture-matched random-initialization contrast; that extra contrast is not required merely to compare practical pipelines.

Separate zero-local-label transfer, limited local adaptation and source-training scarcity. Do not claim the latter establishes the former. Total label accounting includes the annotations used for validation/stopping/model selection. Count source and target labels separately; do not assume equal chips mean equal annotation hours. Local July2021 CEMS labels must remain qualified by acquisition date, trace/permanent-water semantics, coverage and reference dependence. No accuracy claim is forced from noncontemporaneous maps.

Use the already inspected historical data transparently as exploratory/development evidence. Where feasible, reserve an independent event/region for the settled final comparison. This is not a preregistration demand or a reason to withhold valid exploratory results.

### E. Applied interpretation and chapter organization

Connect errors to observed conditions: water width, persistent/new water, urban/vegetated surfaces, sensor availability and time offsets where supported. Distinguish those measurements from unverified physical explanations. Report the complete comparison, not only illustrative successes.

A policy-relevant contribution can concern the capability and complementary observations/labels required when an agency reuses pretrained models. No interviews, adoption claims, monetized benefits or operational deployment are implied. Narrative explanation organizes empirical findings; it does not replace model/task validation.

## Current readiness and limits

Held now: complete benchmark imagery/labels, splits/events, models/source, caches, existing local imagery/reference inventories and recovery records. First engineering checks require no download or package installation. Corrected features/window preparation and controlled reference fitting are next implementation tasks. Wider inference/annotation cost comparisons and independent local accuracy remain uncompleted; they are not declared outcomes.

Existing production adapters/configurations, final benchmark, prior tests and results stay unchanged. A successful fixture does not automatically restart earlier queues. Follow-on stages remain ordinary research work with explicit outputs and transparent choices rather than scientific pass/fail gates.

## First execution evidence

Script229 completed on two explicitly training-only Bolivia fixtures. Patch8 tokens match the historical production path exactly; the cached tensors differ by at most1.19e-6 under the independent CPU calculation. Both4px and8px logit assembly match the author rearrangement exactly. After400 probe updates, training cross-entropy fell from .699 to .034 for8px and .689 to .098 for4px. These are learnability checks on fitted fixtures, not a comparison of generalization or proof that4px is better. Four unit tests passed; changed-code lint passed. No validation/test labels were scored.

The optical-valid Prithvi training-label roundtrip changed2,862 and6,658 water pixels to nonwater on two512px chips, with corresponding additions and unknown-mask changes also retained. This is evidence of boundary changes from resampling, not an estimate of model error or the cause of the completed performance deficit. Nine224px windows cover every source pixel without scene shrinking. Actual crop-based model training/inference and author-score reproduction remain next work.

The first engineering version used radar-valid source labels for a generic resampling check; the currentr3 uses the actual optical-valid Prithvi labels and final source/fixture hashes. All versions remain locally indexed; only currentr3 is the retained readiness receipt: [diagnostics](reviews/limburg-paper-guided-diagnostics-2026-11-10.json).
