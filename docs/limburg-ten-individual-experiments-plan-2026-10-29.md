# Ten individually designed Limburg encoder experiments

Execution update: [implementation and live-status instructions](limburg-individual-experiments-implementation-2026-10-29.md). The design below preserves the decisions before implementation. Its original preparation labels are historical; actual workers, benchmarks and results are tracked by their receipts.

29 October 2026. Internal research/implementation plan; Brian writes manuscript prose. Audited amendment to commit `655c130`, with [findings and corrections](reviews/limburg-ten-experiment-design-audit-2026-10-29.md). This is exploratory development on previously inspected outcomes, not formal preregistration or an untouched confirmation. No new extraction/scoring is launched by this documentation update.

The [machine-readable plan](../config/limburg_individual_encoder_experiments_v1.json) supplies the live design. [Individual documentation/literature review](reviews/limburg-individual-encoder-use-review-2026-10-29.md); [readiness sweep](reviews/limburg-ten-experiment-readiness-2026-10-29.md). Original designs and results remain in Git and their dated records.

## Shared design

**Rq:** Can satellite AI help assess developing high water when ground-monitoring data are limited?

**Population:** Full held 481-episode, eight-gauge rainfall-landmark census; eligibility is recorded per experiment, never sampled for final scoring.

**Source:** results/limburg_scarcity_v2_2026_10_28

**Issue offsets h:** 0; 6; 12; 24

**Primary scenarios:** rich_basin; local_q_absent; all_q_absent

**Supporting scenarios:** Replay the two existing combined sparse-monitoring profiles after primary checks; retain their exact saved masks. No new severity search.

**Target:** Next 24 hourly discharge values; site-native units and catchment-area-normalized mm/h summaries. No hidden current Q or retrospective p99 anchor.

**Outer split:** Earlier calendar years, query storm wholly excluded and donor outcome/closure complete before issue. Fixed year-boundary learned fits. Also report a fixed-year conventional archive to separate archive-refresh advantage.

**Inner split:** Latest two feasible earlier-year validation folds within each outer training set; shared storms and masks across arms. No final-year selection of cadence, regions, product or hyperparameters. This plan uses previously inspected outcomes and makes no confirmatory-test claim.

**Arms:** C: strongest held conventional analogue mean; frozen baseline recipe; C+R: learned correction from model-specific raw descriptors and common context; C+R+E: same correction with the model-specific encoder features added; C+E: supporting attribution arm, not primary proof of encoder value

**Readout:** Multi-output ridge residual correction. Train-only mean imputation, scaling and variable missingness flags; scale each feature block by sqrt(its dimension) after standardization. Alpha candidates [0.001, 0.01, 0.1, 1, 10]. C+R candidates include zero whole correction; C+R+E contains every raw-only candidate exactly (EO weight zero) plus EO block weights 0.1 and 1. Select using inner-fold corrected-trajectory MAE, not residual training MSE or final outcomes. Ridge fits squared-error loss; disclose that fitting loss differs from MAE selection. Clip final Q at zero identically. This is a small explicit encoder-use choice, not fixed forced fusion; disclose different candidate counts and validate all selection chronologically.

**Residual training:** For each historical assessment build its baseline prediction from only earlier closed donor outcomes, excluding its whole regional storm. Targets are observed trajectory minus that archived causal prediction. Training labels must have closed before the outer/inner training boundary; no fitted-in-sample or leave-random-row residuals. Inner folds refit head/preprocessing using earlier data only; baseline donor refresh is causal and recorded separately from fixed head training. Evaluate fixed-year and rolling donor references with distinct identifiers; never switch prediction policies silently.

**Primary scores:** Site-balanced next-24h trajectory MAE in mm/h under local_q_absent: equal offsets within a storm/site, equal storms within site and equal sites. First average within case-mask replications so extra masks/offsets do not create sample size. Retain per-site native m3/s tables. Report whole rainfall census and evaluation-only high-water stratum together; an all-flow gain alone is not high-water benefit.; Encoder increment: C+R+E versus C+R on identical supported/evaluable rows. Net increment: versus both frozen conventional mean C and its median-trajectory reference, on identical rows; also show fixed-year archive references. E08 uses source-watercourse C_transfer and its median counterpart. Do not choose the easier baseline retrospectively.

**Secondary scores:** RMSE; +6/+12/+24h error; peak magnitude/timing with undefined timing retained; high-water and documented-flood strata; coverage/fallback and country/site diagnostics

**Uncertainty:** 999 identical whole-year bootstrap draws of saved predictions across methods; assign each whole storm and all its sites/issues/masks to its initial-landmark year, including year-spanning windows. Aggregate each declared mask design before/within the existing shared-replication resampling rule. Report contributing years and nonfinite draws. Intervals are conditional on fitted/frozen selection procedures and this held network, not full training/pretraining uncertainty or a random sample of countries/basins. Pointwise exploratory intervals; no family-level winner claim. E08 reports watercourse-specific effects separately and does not infer basin-population uncertainty from year resampling.

**Probability boundary:** These ridge corrections produce point trajectories. Do not score their spread as predictive uncertainty or compare MAE with CRPS. Distributional calibration would be a separate implemented extension.

**Coverage:** Maintain one census ledger of all site/storm/issue/mask rows with source, raw-feature, encoder, training-fold, prediction and verification status. For primary attribution compare arms on the exact same query support; no-query-label selection or easy-case omission. If EO alone is unavailable, C+R+E returns C+R where raw correction is supported; if neither correction is supported return C. Missing verification remains unscored, never zero error. Report whole-census pipeline-with-fallback and paired-supported effects separately. Use common support for configuration ablations; no arbitrary numerical support gate is introduced.

**Clock:** Freeze EO context at the initial rainfall landmark for all four issue offsets, matching held archive contexts; report increasing age. Only completed source windows strictly available by that landmark under the existing nominal acquisition clock; future pixels, future weather, hidden Q and post-issue product composites prohibited. No as-issued operational replay claim.

**Physical control:** Soil/snow is a supporting shared physical-state control once downloaded and wrangled. ERA5 soil water is not TerraClimate soil water and cannot fill that Galileo channel.

**Spatial pool:** Where regional pooling is used, use whole catchment plus fixed catchment-elevation thirds derived from held DEM before outcomes. These are elevation zones, not validated floodplain or travel-time zones. Area-weight token/pixel support; record missing fraction and spatial receptive field.

**Execution:** No full run launched by this plan. One MPS extraction lane and at most two CPU lanes, respecting model-specific runtime/device support. Start with conformance fixtures and measured full-context benchmarks; extraction and scoring phases need not compete for all three lanes.

**Storage:** Persist compact catchment/context feature tables and area-weighted moment accumulators, NOT another per-patch million-file cache. Stream tokens/pixels and discard transient tensors after their verified contribution. Resume at atomic tile/context contribution boundaries with source/run hashes and a compact coverage ledger; combining resumptions must not double-count weights. Benchmark peak temporary disk/memory and project full-census volume before queueing. Keep held imagery/checkpoints/selected old results; no other-chapter data changes or cloud spend.

**Conditioning interactions:** A surface-state modifier should be allowed to depend on the developing storm, rather than only add a constant correction. In the SAME ridge head include main raw/EO blocks plus each block multiplied by two train-standardized causal scalars: observed preceding-24h rain and C_mean predicted next-24h mean discharge in mm/h (C_transfer for E08). Build the same interaction recipe for raw descriptors and encoder features, normalize resulting blocks separately, and keep the exact raw-only/zero-EO candidates. Forecast conditioners for training come from the causal out-of-fold baseline ledger, never observed future Q or rain. No new encoder/model family or hyperparameter sweep is added. This tests a physically motivated moderation hypothesis, not identification of a physical causal effect.

**Interpretation:** Positive encoder-versus-raw plus positive versus strong C supports incremental retrospective usefulness under declared conditions. Encoder-versus-raw only supports representation benefit, not net FEWS benefit. Null/adverse findings remain reportable; no experiment has to win.

**Fit population:** E01-E07/E09-E10 fit separate same-gauge, same-scenario heads at fixed outer year boundaries; pool all four training issue offsets with each storm given equal total fitting weight. Apply the declared scarcity masks to training/validation query features, not only test queries; final historical donor archives follow the existing availability policy. Future responses remain verification/training labels only after their closure. E08 overrides this with source-watercourse transfer.

**Common context:** Every learned raw/EO arm receives the same causally available ordered 72h Q channels, rain/season descriptors and observation age/missingness summaries used by the declared conventional source, under that scenario mask. Do not give a head hidden Q, future rainfall, outcome-derived thresholds/strata, or retrospectively diagnosed quality labels as predictors. Soil/snow remains an explicitly labelled later equal-input control. Fixed common context prevents attributing an extra ground-input advantage to EO.

**Reference estimands:** C_mean remains the frozen baseline and residual-training source. Compute C_median from the same admissible donor trajectories (coordinate-wise median) because MAE can favor a median over a mean. Both are declared references; a gain versus mean alone does not establish superiority to all conventional point assessments. Point MAE is compared with point MAE, never CRPS.

**Information support:** Raw comparators receive the same observed dates, bands, masks and input-tile footprints that influence encoded features, including surrounding tile context outside the target polygon. Keep target-zone summaries plus tile/context summaries so global receptive fields are not a concealed extra data source. Native masking/fill contracts may still differ; disclose those differences rather than claim architecture-isolated comparison. No future pixels may enter composite construction.

**Physical interpretation:** No independent wetness/saturation/flood-extent labels are introduced: the experiment tests whether a physically motivated representation helps predict gauge response, not whether latent coordinates measure that physical state. High water uses the existing evaluation-only p99 definition; documented floods are separate records, not synonyms. The 24h horizon describes subsequent discharge within that window, not eventual flood progression, warning skill or useful operational lead time.

**Pretraining boundary:** Checkpoint pretraining can overlap European locations and later historical years. Chronological head/donor separation does not prove pretraining independence or availability of that checkpoint at the historical issue date. These are current-model retrospective stress tests, not strict unseen-basin/zero-shot/as-issued forecasts.

**Ablation policy:** Use at most the one declared mechanism ablation per experiment, on exact paired support and with the same fitted-head selection protocol. Reuse old cached pooled vectors only if their inputs, spatial support and date context match; otherwise call it a configuration comparison or recompute the required matched output during the same pass. Do not bolt on a second full scenario sweep.

## E01 — Pixel heterogeneity and antecedent seasonal condition (presto)

**1. Hypothesis.** Pixel-level seasonal condition and within-catchment variability improve response assessment beyond spectral/index histories.

**2. Inputs.** Held S2 ten-band monthly sequences for the preceding twelve completed months; valid pixels, pixel dates/locations, catchment and DEM. Missing Presto modalities remain masked.

**3. Model use.** Frozen default Presto; native twelve-month encoding. Stream area-weighted per-pixel mean and SD for whole catchment and elevation thirds. Do not substitute SD of patch means for pixel SD. Recent four-week route is supporting existing evidence, not a winner-selected replacement. Mean-only versus mean+SD is the single mechanism ablation on the SAME twelve-month pixel output/support, not recent versus monthly.

**4. Matched comparator.** Same pixels/months/areas: band and NDVI, NDMI, MNDWI mean/SD histories and known season/location/coverage; same common antecedent weather/physical descriptors in both learned arms.

**5. High-water contribution.** Test whether antecedent heterogeneity adds to C+raw when local Q is absent; rich/all-Q-absent assess dependence on information availability.

**6. Interpretation.** An increment does not identify soil saturation or show a benefit from more months alone: raw control has the same months. Failure concerns this readout/checkpoint, not all Presto uses.

**Raw descriptors:** Monthly band/index mean, SD, first-last change, observed fraction and acquisition age; indices from observed reflectance with invalid denominators masked.

**Preparation:** Implement pixel-moment extraction and weighted area/variance aggregation; Build twelve-month raw descriptors and case/context joins; Check missing months, pixel months, boundary weights and moment-combination identity.

**Encoding:** Targeted extraction of held imagery needed.

## E02 — Spatially differentiated optical state (anysat)

**1. Hypothesis.** Local spatial features preserve response-relevant variation lost by tile/catchment means.

**2. Inputs.** Held coherent ten-band S2 four completed weeks, exact dates, catchment and DEM; S2-only primary, no new SAR requirement.

**3. Model use.** Frozen base; supported patch output (dense only if the pinned API requires it for an equivalent grid) at documented physical patch size, native temporal input; pool whole catchment/elevation thirds. Verify actual output grid and scale rather than assume dense means 10m.

**4. Matched comparator.** Same S2 pixels/weeks/zones with band/index mean, SD and temporal change; simple terrain descriptors and identical coverage metadata.

**5. High-water contribution.** Compare C+R+E with C+R, and a supporting matched global-output ablation on identical support.

**6. Interpretation.** A local-versus-global improvement is not automatically encoder benefit; raw spatial controls must also receive zones. Elevation thirds are not a hydraulic floodplain.

**Raw descriptors:** Weekly zone-level bands/NDVI/NDMI/MNDWI moments, changes, terrain, valid fractions and acquisition ages.

**Preparation:** Implement patch/dense readout and exact output-footprint weights; Use same spatial masks for raw and encoded arms; Conformance test metres versus pixels, output coordinates and one-based dates.

**Encoding:** Targeted extraction of held imagery needed.

## E03 — Supported climate and terrain enrichment (galileo)

**1. Hypothesis.** A combined monthly optical/climate/terrain encoding adds beyond the same physical variables represented directly.

**2. Inputs.** Held S2 twelve completed months; exact ERA5-Land monthly temperature_2m and total_precipitation_sum conventions; SRTM elevation/slope. Missing TerraClimate/VIIRS/land-cover groups stay masked. GLO30 is not silently relabelled SRTM.

**3. Model use.** Frozen Nano; official modality helper/normalizer with S2, ERA5 and SRTM groups populated, missing groups masked. Primary monthly cadence matches the climate groups. S2-only matched ablation isolates enrichment. Restrict enriched/S2-only attribution to common source/feature support; other modality additions stay optional.

**4. Matched comparator.** Identical monthly S2 summaries, ERA5 temperature/precipitation and SRTM terrain supplied directly, plus common context. Compare enriched encoding with enriched raw, not enriched encoding with S2-only baseline.

**5. High-water contribution.** Test antecedent physical context under local/all-Q absence, while retaining rich reference.

**6. Interpretation.** Enriched versus S2-only alone is a data-addition result. Nano results do not establish performance of Tiny/larger Galileo. Any unmatched climate product must remain masked and documented.

**Raw descriptors:** Monthly optical moments, temperature, precipitation, terrain elevation/slope moments, location/season and support.

**Preparation:** Verify held hourly ERA5 aggregation equals specified monthly product/accumulation convention or pull exact small monthly product; Acquire/verify SRTM and slope for existing tile extent; Implement multimodal Nano tensor/mask contracts and equal-input raw control.

**Encoding:** Targeted extraction of held imagery needed.

## E04 — Ordered radar surface change (olmoearth)

**1. Hypothesis.** Spatial/temporal radar features contribute beyond raw backscatter level and change.

**2. Inputs.** Held ascending VV/VH four completed weeks, fixed recorded orbit geometry, masks/dates, catchment/DEM.

**3. Model use.** Frozen v1.2 Tiny; retain per-time features from native encoder, pool observed spatial tokens over catchment/zones, concatenate four ordered summaries and changes. No v1.3-only location-query API.

**4. Matched comparator.** Same VV/VH in documented dB/linear units: weekly means, SD, VV-minus-VH in dB, first differences and zone contrasts, orbit/angle where actually held; geometry unknown remains explicit.

**5. High-water contribution.** Compare ordered encoded radar with ordered raw radar corrections to C, especially local-Q absence.

**6. Interpretation.** Change features may encode acquisition or vegetation rather than wetness. Support/season/raw controls and fixed orbit are necessary for that distinction, but do not prove physical mechanism.

**Raw descriptors:** Ordered VV/VH levels, SD, differences, zone contrasts and observation metadata; no mixing units in ratios.

**Preparation:** Expose v1.2 per-time tokens before global pooling; Implement matched raw SAR descriptors and fixed-orbit/geometry ledger; Validate token masks and missing-time pooling without fabrication.

**Encoding:** Targeted extraction of held imagery needed.

## E05 — Radar texture beyond absolute backscatter (croma)

**1. Hypothesis.** CROMA pattern features add beyond conventional radar texture/change descriptors and retained absolute levels.

**2. Inputs.** Held primary-orbit ascending VV/VH four completed weeks, dates/masks; orbit-15/161 completed results supporting only.

**3. Model use.** Frozen base SAR branch, corrected publisher normalization. Encode dates separately, retain chronological SAR_GAP and differences instead of only their mean. No claim of native temporal attention.

**4. Matched comparator.** Same inputs: raw VV/VH level/SD/change plus fixed texture descriptors (horizontal/vertical adjacent-pixel contrast and lag-one correlation on valid pixel pairs), zone summaries and observation metadata.

**5. High-water contribution.** Compare C+R+CROMA with C+R under Q loss. Raw absolute amplitudes appear in both learned arms because input contrast stretch removes them from CROMA.

**6. Interpretation.** A positive result supports texture encoding beyond chosen transparent descriptors; a null does not show radar lacks hydrological information. No ad hoc replacement of publisher normalization.

**Raw descriptors:** Per-week raw levels, SD, changes, valid-neighbour contrast/correlation for VV and VH; undefined constant-image correlation remains missing.

**Preparation:** Expose per-date SAR_GAP in compact output; Implement raw level and deterministic texture control with masks; Verify constant/no-data fixtures and corrected /255 normalization.

**Encoding:** Targeted extraction of held imagery needed.

## E06 — Catchment-local HLS surface condition (prithvi)

**1. Hypothesis.** Pooling spatial features over the actual contributing catchment improves assessment beyond HLS descriptors and whole-tile averaging.

**2. Inputs.** Held six-band HLS 30m four completed weeks, dates/coordinates, catchment and DEM.

**3. Model use.** Frozen EO2 Tiny TL four-frame route; retain spatial/time tokens and pool observed catchment/elevation support. Document 6.72km tile receptive context and token footprint; no claim that masking removes all outside context. Compute the matched whole-tile pooled output from the same forward pass for its single pooling ablation.

**4. Matched comparator.** Same HLS pixels/times/areas: bands and NDVI/NDMI/MNDWI moments, changes, terrain and metadata. Matched global pooled Prithvi ablation supports pooling attribution.

**5. High-water contribution.** Test C+R+E under local-Q absence; separately report high-water/flood-case errors and effective represented area.

**6. Interpretation.** Global-to-local changes may reflect spatial support rather than architecture; control raw support and compare paired cases. Tiny is not the 300M/600M model.

**Raw descriptors:** HLS six-band/index weekly zone moments and changes; product/coverage/date descriptors.

**Preparation:** Expose non-CLS spatiotemporal tokens and map token footprint to HLS grid; Implement area-weighted local pooling and no-data tests; Match four-frame TL metadata/order and raw-support comparator.

**Encoding:** Targeted extraction of held imagery needed.

## E07 — Metadata-aware optical representation (copernicus_fm)

**1. Hypothesis.** Surface representations using correct location/date/scale add beyond raw spectra and identical metadata.

**2. Inputs.** Held primary coherent ten-band S2 four completed weeks, real patch coordinates/dates/scale. Existing TOA/QA60 route retained as product-domain sensitivity, not selected by final scores.

**3. Model use.** Frozen base; same published patch-mean/LayerNorm readout, metadata populated with lon/lat, days since epoch and internal token area. Independent frame features retained in time order. No-metadata matched ablation with the SAME ordered-frame output; old frame-mean caches alone cannot identify a metadata effect.

**4. Matched comparator.** Same bands/indices, dates, coordinates, token scale, season and coverage; train-only simple metadata and spectral model with same residual-head budget.

**5. High-water contribution.** Assess metadata-enabled features against equal-input raw descriptors and C; verify gain persists beyond coordinates/date alone.

**6. Interpretation.** Metadata-only benefit is not learned hydrological state. Product-domain/support changes cannot be credited solely to metadata.

**Raw descriptors:** Weekly band/index moments/changes plus explicit location/day/scale/coverage; metadata-only supporting arm.

**Preparation:** Implement known-metadata route and chronological frame outputs; Test 0.0256km2 token area, date units and coordinate order; Replay no-metadata/product-domain evidence on exact paired cases.

**Encoding:** Targeted extraction of held imagery needed.

## E08 — Cross-watercourse landscape transfer (dofa)

**1. Hypothesis.** Wavelength-conditioned landscape context improves transfer to another held watercourse beyond physical/geographic/raw spectral descriptors.

**2. Inputs.** Held v1 six non-TCI S2 bands, preceding twelve completed months, coordinates, catchment areas/DEM and river-group mapping. No new sensor or v2 upgrade.

**3. Model use.** Use held frozen v1 monthly vectors as antecedent landscape context, with train-only transformations. Leave one entire watercourse out across all years, then evaluate each year using only earlier years from other watercourses; group all Wurm sites together. No same-watercourse target outcomes used to fit/readout or select tuning.

**4. Matched comparator.** Same raw optical summaries/indices and terrain/area/coordinates/season; simple transfer correction and cross-watercourse conventional reference using area-normalized mm/h trajectories.

**5. High-water contribution.** Primary contrast under local-Q absence. Remove contemporaneous same-watercourse peer-Q proxies too. Report a separate transfer reference and target adaptation with known historical C only as explicitly labelled deployment variant, not ungauged proof.

**6. Interpretation.** Few independent watercourses limit generalization. This is held-network watercourse transfer, not a country experiment or unmonitored-basin validation. Do not rank its magnitude directly against same-gauge experiments.

**Raw descriptors:** Twelve-month six-band means, red-edge/NIR and NIR/SWIR contrasts, seasonal variability and zone terrain/area descriptors; use only genuinely held non-TCI inputs.

**Preparation:** Implement watercourse-grouped chronological folds and source-only tuning; Build mm/h transfer baseline and raw landscape descriptors; Poison every target-watercourse Q source to verify exclusion; retain unavailable-fold ledger.

**Encoding:** Initially reuse specified held vectors; raw descriptors/readout still need implementation.

**Transfer-specific overrides:**

- **baseline:** C_transfer: earlier other-watercourse donor trajectories in mm/h; source-only fitting/tuning

- **arms:** C_transfer; C_transfer+R; C_transfer+R+E

- **target watercourse:** Exclude every target-watercourse Q source from training, tuning and local-absence peer inputs, including all Wurm sites together

- **inner split:** Earlier-year folds with one source watercourse held out within training; no target-watercourse outcomes

- **supporting reference:** Target-history conventional C is deployment context only, never a training residual source or evidence of ungauged transfer

- **graph exclusion:** Canonicalize physical_river/Wurm/Worm names in an explicit held station graph. Exclude the held watercourse from BOTH the donor response pool and all source training-feature Q channels; do not remove only a target gauge. Related Geul branches remain dependent regional sites, not independent countries/basins.

- **residual crossfit:** For each training source watercourse, obtain baseline residuals as if that source watercourse were also held out of its donor pool/features. Inner folds repeat this source-watercourse holdout using only earlier data; a same-gauge source residual would not match target transfer deployment.

- **weighting:** Within each training/score fold give watercourses equal mass, then sites within watercourse equal mass, then storms and offsets equally. Three Wurm sites are not three independent watercourses.

- **test outcomes:** Target-watercourse Q may be used only as held verification and evaluation strata, not head training, transfer calibration, source normalization or source-only hyperparameter selection.

## E09 — Ordered optical surface context (terramind)

**1. Hypothesis.** A small supervised temporal readout on TerraMind features adds beyond the same ordered optical descriptors.

**2. Inputs.** Held ten-band S2L2A four completed weeks, masks/dates, catchment and DEM. No generation, TiM, extra labels or modality expansion.

**3. Model use.** Frozen 1.0 Tiny; supported single-frame backbone used through a verified ordered-frame readout (wrapper if API-equivalent), catchment pooled per frame, concatenate levels/changes. No claim of pretrained temporal attention. Compute its unordered mean from those same four per-frame outputs for the single temporal-order ablation.

**4. Matched comparator.** Identical ordered S2 bands/indices and changes, season/terrain/coverage, with same residual-head capacity/tuning approach.

**5. High-water contribution.** Test temporal surface context against C+raw under local/all-Q absence; supporting unordered-frame-mean ablation on paired support.

**6. Interpretation.** A benefit from order belongs to the downstream temporal readout, not proof the backbone learned river dynamics. Flood mapping/generation remain different tasks.

**Raw descriptors:** Ordered weekly S2 band/index mean/SD/change and observation metadata.

**Preparation:** Implement ordered-frame frozen-backbone output with compact cache; Validate wrapper equivalence/masks against direct single-frame calls; Keep label-free encoder and catchment residual supervision distinct.

**Encoding:** Targeted extraction of held imagery needed.

## E10 — Product-matched multispectral spatial context (satmae)

**1. Hypothesis.** Multispectral features add beyond raw optical descriptors when evaluated on a product closer to the checkpoint domain.

**2. Inputs.** Held TOA/QA60 supplemental ten-band route as declared primary; matched SR route supporting. Restrict raw and encoded arms to identical acquisition/product/mask support.

**3. Model use.** Frozen multispectral base e199. Use held completed-month snapshot outputs initially; no temporal-RGB capability claim. New extraction only if a specific verified pooled-readout defect is found, not to manufacture ten extraction jobs.

**4. Matched comparator.** Same TOA bands/NDVI/NDMI/MNDWI moments, fixed spatial contrasts, date/season/coverage with same learned correction budget; paired SR repeats isolate domain/support effects.

**5. High-water contribution.** Evaluate C+R+E against C+R and C under local-Q absence, then rich/all-Q-absent references.

**6. Interpretation.** TOA chosen for checkpoint-domain rationale after earlier evidence exists; this is exploratory, not an untouched product selection. QA60/SR support differences are not encoder effects; keep paired and coverage views. Full SR/TOA scores cannot by themselves isolate radiometric domain from different cloud masks/acquisition support. Compare only matching scene/time inputs where available; otherwise label it a product-and-support sensitivity, not a domain effect.

**Raw descriptors:** Monthly TOA band/index mean/SD and neighbour contrast; same-mask SR descriptors only for paired domain diagnostic.

**Preparation:** Build TOA raw descriptors and exact supplemental context joins; Inspect held checkpoint readout/product contract and record primary choice; Implement same-acquisition/support domain comparison, not unpaired score subtraction.

**Encoding:** Initially reuse specified held vectors; raw descriptors/readout still need implementation.

## Execution order

1. Implement and test the shared causal residual/raw-descriptor foundation; E08 has its own source-watercourse transfer contract.
2. Build cached-vector E08/E10 feature tables while developing the eight targeted extraction adapters. Galileo product reconciliation proceeds independently of other experiments.
3. Run publisher/mask/weighted-pooling conformance fixtures and measure a full spatial context in each intended runtime. Benchmarking checks engineering, not final scientific eligibility or event selection.
4. Queue at most one MPS and two CPU workers according to measured memory/throughput; stream compact moments/features. Preserve old results and all other chapters.
5. Score the full census/coverage ledger, perform paired attribution and high-water review, and retain null/adverse findings. No model must win.

Runtime and temporary storage remain to be measured. The preparation checker inventories assets and support, but cannot certify unimplemented model adapters or launch the run.
