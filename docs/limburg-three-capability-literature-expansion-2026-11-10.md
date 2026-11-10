# Expanding the three spatial capabilities: literature and held-data review

10 November 2026. Internal research aid, not dissertation prose. Targeted primary-source update to the paper-guided recovery plan. Existing chapter bibliography, model-use/design reviews, held PANGAEA/model documentation, author papers/code, new papers and data release pages were reviewed. This is not an exhaustive systematic search or a new model/data-acquisition run.

## Main assessment

The useful expansion is from average mapping performance to **what information enables a model to identify new inundation, where transfer fails, and what adaptation or verification is required**. The three capabilities can form one connected chapter. Their separation is already present in the literature; it is not itself a novelty claim. Our additional contribution must be a measured result about information, transfer, adaptation effort or reliability.

### 1. Identifying observable water

Move beyond one mean IoU to narrower observational questions:

- Which water geometries are preserved or lost: broad water, thin channels, small isolated patches and boundaries? Calculate reference-mask width/size descriptors at native resolution; do not call them independently surveyed physical channel width. Keep a common valid reference support when comparing models.
- Which surroundings cause confusion: shadows, dark soil, urban surfaces, vegetation and terrain? Initially score what reference/imagery evidence supports. A land-cover mechanism requires aligned independent land-cover labels or a documented review; do not infer it from an error map alone.
- Does spatially faithful cropping improve narrow-water delineation relative to whole-image shrinking? This directly follows the Prithvi diagnostic. Score boundary and area errors alongside IoU, rather than optimizing a single edge metric after seeing results.
- Can the model identify uncertain or unobservable areas? Report coverage, omissions and false positives together. Labeling everything unknown cannot count as successful flood detection. Sensor invisibility and model uncertainty are different outputs.

[WorldFloods 2023](https://www.nature.com/articles/s41598-023-47595-7) explicitly treats its optical output as water, including permanent water, and handles cloud-related mapping limitations. [UrbanSARFloods](https://arxiv.org/html/2406.04111v1) shows why open and urban flood mapping require different evidence; its SLC/coherence inputs are not recoverable from our GRD intensity arrays. [Roth et al. 2026](https://link.springer.com/article/10.1007/s41064-026-00417-7) provides a held institutional/academic comparison for dual-polarization mapping and vegetation-related failures.

**Held-data fit:** existing source labels, saved hard predictions and original imagery support water/land error decomposition and boundary analysis after alignment checks. Crop-based model comparisons require new inference/fitting, as already planned. Benchmark-wide land-cover strata need an aligned overlay. New urban/under-canopy detection claims need suitable reference classes; stronger claims cannot be obtained merely by adding an urban layer. This is not an automatic commitment to SLC processing.

### 2. Identifying newly inundated land

The most promising expansion concerns **the pre-event reference**. Distinguish observed pre-existing water, long-term permanent water and event-related new inundation. Two pre-event images cannot establish permanence, and ordinary seasonal water change is not automatically damaging flooding.

Controlled comparisons can ask:

1. Event image alone, with a declared static/antecedent reference.
2. Nearest pre-event image plus event image.
3. Two pre-event observations plus event image, using their disagreement to identify unstable reference conditions.
4. The same image evidence with terrain context, compared against a matched non-encoder method.

Score the full background/permanent-water/flooded-water confusion matrix: how often is a true flood classified as permanent water, and how often is existing water classified as new flooding? Report inundated-area over/underestimation and errors near normal-water boundaries. Keep direct three-class learning separate from post-hoc subtraction of binary water masks. Both are legitimate pipelines, with different error propagation.

[Kuro Siwo](https://arxiv.org/html/2311.12056v3) supplies a suitable temporal/three-class precedent. **All5,000 held records already contain SL2 VV/VH and a DEM**, while the current adapter uses SL1 and event imagery. The [inventory](reviews/limburg-capability-extra-input-inventory-2026-11-10.json) verifies presence, not raster quality/alignment or useful terrain information. These are meaningful available inputs, not proof that either will improve results. Begin with metadata, masks, units and source-grid checks.

A further supported candidate is a dense annual landscape embedding as a **normal-water prior**. GEOID-Flood uses AlphaEarth for that role. Our catchment-average CSV cannot serve as a pixel water map; a small, dense embedding acquisition and a compatible supervised decoder/reference would be needed. Event-year annual embeddings may contain observations after the flood, so an issue-time interpretation needs an available earlier-year product. An annual prior is not evidence of current flooding.

**Important reference dependence:** GEOID-Flood derives its permanent-water layer from AlphaEarth. Scoring our AlphaEarth prior against that layer would not independently validate that capability. Its single-date ESW water reference also should not automatically be treated as proof of long-term permanence. Compare against a separately sourced/adjudicated reference or explicitly limit the result to agreement with that product.

The operational [GFM product manual](https://extwiki.eodc.eu/gfm_assets/gfm4.0_pum_2025.pdf) is useful grey literature: observed water, reference water, observed flooding and exclusion/reliability layers are distinct products. A service comparison would need matching acquisitions, archive coverage and compatible masks; GFM is a comparator, not ground truth. No assumption is made that a product exists for every July2021 case.

### 3. Transferring capabilities to unfamiliar landscapes

Transfer should be measured as a set of different information situations:

| Situation | What the receiving agency supplies | What we can learn |
|---|---|---|
| No target adaptation | Compatible target imagery only | How source-trained capability transfers without local labels |
| Unlabeled adaptation | Additional target imagery, no target reference labels | Whether self-supervised/test-time adaptation helps, and when it drifts |
| Limited labeled adaptation | A measured amount of target annotation, including validation | How local supervision changes errors and usable coverage |
| More complete local training | Larger target annotation set | A separate local-data reference, not a required deployment condition |

The prior5%-source-training tests do not answer the target-label question. Keep source/target training, model-selection, stopping and uncertainty-calibration labels separate. Target adaptation/test areas must be disjoint at the claimed level; multiple chips from one flood are not independent events. A same-event spatial adaptation experiment answers a different question from transfer to a new event or catchment.

Useful extensions are:

- Train elsewhere and evaluate held-out regions/events, then compare frozen reuse, supported full fine-tuning and a parameter-efficient adaptation. [Rapid Adaptation](https://arxiv.org/html/2409.09907v1) is a methodological lead, but its reported in-distribution gains coexist with poor external scores; it does not promise that LoRA solves transfer. Exact compatibility with our held backbones must be checked.
- Compare random target-label acquisition with an uncertainty/representativeness strategy. [ALFA, IJCAI2025](https://ijcai.org/proceedings/2025/1057) motivates useful annotation selection. Existing labels allow a simulated-label study, not a claim that Brian/agency annotation time was measured.
- Characterize target/source differences in water geometry, terrain, season, sensor and appearance. Test whether these explain or predict failure on held-out events. Begin with raw descriptors and held representation distances; more embedding models are not a prerequisite. A distance-error association alone does not establish a calibrated warning that a map is unreliable.
- Calibrate confidence/abstention on separate data, then report accuracy versus retained coverage and flood omissions. [Konidakis et al., IGARSS2025](https://doi.org/10.1109/IGARSS55030.2025.11242848) motivates uncertainty evaluation. Spatial dependence and geographic shift mean conformal coverage guarantees cannot simply be assumed for a new river region. Existing hard labels do not contain the probabilities needed: restored selected checkpoints/new inference would be necessary.
- Use [Chen et al.2026](https://doi.org/10.1029/2025JH001145) as a concrete target-adaptation template; its coastal setting and three target events limit direct riverine generalization. Author code has a documented Zenodo route. It is a candidate comparison, not another automatic model family.

## New dataset leads and overlap

| Lead | Role | Acquisition and limitations |
|---|---|---|
| Kuro Siwo full release | More temporal/source-event coverage beyond our Copernicus-Bench subset | [Author release](https://github.com/Orion-AI-Lab/KuroSiwo). First use the second pre-image/DEM already held; audit overlap before adding more events. |
| GEOID-Flood | Closely related experimental template and candidate external transfer/reference source | [Paper](https://arxiv.org/html/2608.02315v1), [code](https://github.com/links-ads/geoid-flood), [dataset](https://huggingface.co/datasets/links-ads/geoid-flood). Public repo lists a complete sample, modality-selective downloads and a held-out package; no bulk download launched. Pin dataset revision: paper/repo tile totals differ. Permanent-water labels require the independence qualification above. |
| S1S2-Water | Additional ordinary-water/terrain/appearance coverage for source training and transfer | [Documented dataset DOI](https://doi.org/10.5281/zenodo.8314175). Water labels are not event-flood labels; check spatial/event overlap. |
| WorldFloods extended | Optical water/cloud and independent-event mapping | [Extended dataset](https://doi.org/10.5281/zenodo.8153513). Source imagery/reference times and permanent-water semantics vary. |
| UrbanSARFloods / DeepFlood | Conditional targeted urban/vegetated evaluation | [UrbanSARFloods](https://github.com/jie666-6/UrbanSARFloods), [DeepFlood](https://doi.org/10.1038/s41597-025-04554-3). Different sensors/resolution/label-generation evidence; useful only for a declared capability test. Not drop-in substitutes for current labels. |

The closely overlapping GEOID-Flood work means "water versus new flooding plus transfer" is an established research structure. Use it as a template, then identify a measurable extension. Promising candidates are the role/age/stability of the antecedent reference, total local adaptation requirements, and reliability under identifiable river-landscape shifts. Their novelty needs a focused check once selected; no claim of an empty literature gap is made.

A newer hydro-climatic representativeness paper, [Ratté-Fortin et al.2026](https://doi.org/10.1016/j.jag.2026.105321), is a particularly relevant lead. Publisher access was blocked; metadata and abstract-level descriptions were available. Full methods should be obtained before treating it as an execution template. It appears to align environmental representativeness, transfer and operational context; this is a lead, not a verified reproduction recipe.

## Recommended incorporation

**Extend the current work directly:** complete the Galileo/Prithvi source-contract comparisons; inspect water geometry/area errors; recover the already-held second pre-event observations and DEM into an audited input contract; evaluate temporal-reference contribution on matched events. These directly improve the three-capability experiment.

**Specify next:** target-label adaptation with full label accounting and uncertainty/coverage reporting. Compare source reuse with ordinary competent local adaptation, retaining physical/U-Net controls and event dependence. Use the new literature to define adaptation rather than adding arbitrary model combinations.

**Conditional additional work:** dense prior-year AlphaEarth normal-water mapping; unlabeled target adaptation; active annotation selection. Each answers a distinct question and needs the stated reference/compute evidence. Record these as candidates, not automatically active obligations.

**Larger independent paths:** urban coherence, inundated vegetation ground truth, depth/damage estimation and new discharge forecasting. The first two require different observational evidence; the latter two are beyond this spatial-capability extension. They can be considered deliberately without becoming requirements now.

No new large dataset, weights, GPU queue, package, data request or dissertation prose was produced in this review. Existing results and production sources are unchanged.
