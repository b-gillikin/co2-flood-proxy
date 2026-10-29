# Ten individually designed Limburg encoder experiments

29 October 2026. Internal protocol/research aid, not dissertation prose. Brian writes prose and sends emails. This is exploratory development following the completed common-interface benchmark and learned-readout diagnostics. It is not preregistration, an untouched confirmation, or a new chapter prerequisite. No experiment must produce a positive result.

The machine-readable source of truth is [`config/limburg_individual_encoder_experiments_v1.json`](../config/limburg_individual_encoder_experiments_v1.json). This plan supersedes the assumption that ten encoders should receive one interchangeable configuration; it does not overwrite earlier results. Scientific sources and checkpoint qualifications are recorded in the [individual-use review](reviews/limburg-individual-encoder-use-review-2026-10-29.md).

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

**Readout:** Multi-output ridge correction with train-only mean imputation/scaling, variable missingness flags, alphas [0.001, 0.01, 0.1, 1, 10] plus a zero-correction option in every learned arm. Standardize each feature block using training data then divide by sqrt(block dimension); use fixed equal raw/EO block weights rather than another EO-weight search. Clip final discharge predictions at zero consistently. For heterogeneous modalities use separately scaled feature blocks. All arms use identical outcome information and comparable tuning opportunities.

**Residual training:** Build each training residual from an earlier-only out-of-fold conventional prediction, not an in-sample baseline fit. Inner validation refits every preprocessing/readout component without its held year. Exclude or explicitly fallback where no causal baseline residual exists.

**Primary scores:** Next-24h trajectory MAE under local_q_absent, pooling four issue offsets equally within site and sites equally. Report whole rainfall census and evaluation-only high-water stratum together; an overall-flow gain alone is not a high-water benefit.; C+R+E versus C+R, then versus C, strongest original and fixed-year conventional references; E08 uses its declared source-watercourse C_transfer override.

**Secondary scores:** RMSE; +6/+12/+24h error; peak magnitude/timing with undefined timing retained; high-water and documented-flood strata; coverage/fallback and country/site diagnostics

**Uncertainty:** 999 shared whole-year bootstrap draws across methods/models, keeping storms/sites/issues together and mask timelines paired. Report year counts and nonfinite draws. Pointwise intervals are exploratory across ten prespecified primary encoder contrasts; do not make a family-level winner/significance claim. Cross-watercourse E08 has a distinct population and is not pooled as an identical estimand.

**Probability boundary:** These ridge corrections produce point trajectories. Do not score their spread as predictive uncertainty or compare MAE with CRPS. Distributional calibration would be a separate implemented extension.

**Coverage:** Whole census with fallback plus exact paired-supported and common-support views. No complete-case deletion disguised as a census; unsupported/poor-quality cases remain in ledgers.

**Clock:** Freeze EO context at the initial rainfall landmark for all four issue offsets, matching held archive contexts; report increasing age. Only completed source windows strictly available by that landmark under the existing nominal acquisition clock; future pixels, future weather, hidden Q and post-issue product composites prohibited. No as-issued operational replay claim.

**Physical control:** Soil/snow is a supporting shared physical-state control once downloaded and wrangled. ERA5 soil water is not TerraClimate soil water and cannot fill that Galileo channel.

**Spatial pool:** Where regional pooling is used, use whole catchment plus fixed catchment-elevation thirds derived from held DEM before outcomes. These are elevation zones, not validated floodplain or travel-time zones. Area-weight token/pixel support; record missing fraction and spatial receptive field.

**Execution:** No full run launched by this plan. One MPS extraction lane and at most two CPU lanes, respecting model-specific runtime/device support. Start with conformance fixtures and measured full-context benchmarks; extraction and scoring phases need not compete for all three lanes.

**Storage:** Stream area-weighted feature moments and discard transient token tensors after verified output; do not persist dense token cubes. Measure peak temporary disk/memory and project census volume before queueing each experiment. No other-chapter data changes or cloud spend.

**Interpretation:** Positive encoder-versus-raw plus positive versus strong C supports incremental retrospective usefulness under declared conditions. Encoder-versus-raw only supports representation benefit, not net FEWS benefit. Null/adverse findings remain reportable; no experiment has to win.

## Model-specific experiment cards

### E01 — Pixel heterogeneity and antecedent seasonal condition (presto)

**1. Hypothesis.** Pixel-level seasonal condition and within-catchment variability improve response assessment beyond spectral/index histories.

**2. Inputs.** Held S2 ten-band monthly sequences for the preceding twelve completed months; valid pixels, pixel dates/locations, catchment and DEM. Missing Presto modalities remain masked.

**3. Model use.** Frozen default Presto; native twelve-month encoding. Stream area-weighted per-pixel mean and SD for whole catchment and elevation thirds. Do not substitute SD of patch means for pixel SD. Recent four-week route is supporting existing evidence, not a winner-selected replacement.

**4. Matched comparator.** Same pixels/months/areas: band and NDVI, NDMI, MNDWI mean/SD histories and known season/location/coverage; same common antecedent weather/physical descriptors in both learned arms.

**5. High-water contribution.** Test whether antecedent heterogeneity adds to C+raw when local Q is absent; rich/all-Q-absent assess dependence on information availability.

**6. Interpretation.** An increment does not identify soil saturation or show a benefit from more months alone: raw control has the same months. Failure concerns this readout/checkpoint, not all Presto uses.

**Raw descriptor specification:** Monthly band/index mean, SD, first-last change, observed fraction and acquisition age; indices from observed reflectance with invalid denominators masked.

**Preparation before execution:** Implement pixel-moment extraction and weighted area/variance aggregation; Build twelve-month raw descriptors and case/context joins; Check missing months, pixel months, boundary weights and moment-combination identity.

**Encoding:** Fresh model-specific extraction of held imagery is needed.

### E02 — Spatially differentiated optical state (anysat)

**1. Hypothesis.** Local spatial features preserve response-relevant variation lost by tile/catchment means.

**2. Inputs.** Held coherent ten-band S2 four completed weeks, exact dates, catchment and DEM; S2-only primary, no new SAR requirement.

**3. Model use.** Frozen base; supported patch/dense output at documented physical patch size, native temporal input; pool whole catchment/elevation thirds. Verify actual output grid and scale rather than assume dense means 10m.

**4. Matched comparator.** Same S2 pixels/weeks/zones with band/index mean, SD and temporal change; simple terrain descriptors and identical coverage metadata.

**5. High-water contribution.** Compare C+R+E with C+R, and a supporting matched global-output ablation on identical support.

**6. Interpretation.** A local-versus-global improvement is not automatically encoder benefit; raw spatial controls must also receive zones. Elevation thirds are not a hydraulic floodplain.

**Raw descriptor specification:** Weekly zone-level bands/NDVI/NDMI/MNDWI moments, changes, terrain, valid fractions and acquisition ages.

**Preparation before execution:** Implement patch/dense readout and exact output-footprint weights; Use same spatial masks for raw and encoded arms; Conformance test metres versus pixels, output coordinates and one-based dates.

**Encoding:** Fresh model-specific extraction of held imagery is needed.

### E03 — Supported climate and terrain enrichment (galileo)

**1. Hypothesis.** A combined monthly optical/climate/terrain encoding adds beyond the same physical variables represented directly.

**2. Inputs.** Held S2 twelve completed months; exact ERA5-Land monthly temperature_2m and total_precipitation_sum conventions; SRTM elevation/slope. Missing TerraClimate/VIIRS/land-cover groups stay masked. GLO30 is not silently relabelled SRTM.

**3. Model use.** Frozen Nano; official modality helper/normalizer with S2, ERA5 and SRTM groups populated, missing groups masked. Primary monthly cadence matches the climate groups. S2-only matched ablation isolates enrichment.

**4. Matched comparator.** Identical monthly S2 summaries, ERA5 temperature/precipitation and SRTM terrain supplied directly, plus common context. Compare enriched encoding with enriched raw, not enriched encoding with S2-only baseline.

**5. High-water contribution.** Test antecedent physical context under local/all-Q absence, while retaining rich reference.

**6. Interpretation.** Enriched versus S2-only alone is a data-addition result. Nano results do not establish performance of Tiny/larger Galileo. Any unmatched climate product must remain masked and documented.

**Raw descriptor specification:** Monthly optical moments, temperature, precipitation, terrain elevation/slope moments, location/season and support.

**Preparation before execution:** Verify held hourly ERA5 aggregation equals specified monthly product/accumulation convention or pull exact small monthly product; Acquire/verify SRTM and slope for existing tile extent; Implement multimodal Nano tensor/mask contracts and equal-input raw control.

**Encoding:** Fresh model-specific extraction of held imagery is needed.

### E04 — Ordered radar surface change (olmoearth)

**1. Hypothesis.** Spatial/temporal radar features contribute beyond raw backscatter level and change.

**2. Inputs.** Held ascending VV/VH four completed weeks, fixed recorded orbit geometry, masks/dates, catchment/DEM.

**3. Model use.** Frozen v1.2 Tiny; retain per-time features from native encoder, pool observed spatial tokens over catchment/zones, concatenate four ordered summaries and changes. No v1.3-only location-query API.

**4. Matched comparator.** Same VV/VH in documented dB/linear units: weekly means, SD, VV-minus-VH in dB, first differences and zone contrasts, orbit/angle where actually held; geometry unknown remains explicit.

**5. High-water contribution.** Compare ordered encoded radar with ordered raw radar corrections to C, especially local-Q absence.

**6. Interpretation.** Change features may encode acquisition or vegetation rather than wetness. Support/season/raw controls and fixed orbit are necessary for that distinction, but do not prove physical mechanism.

**Raw descriptor specification:** Ordered VV/VH levels, SD, differences, zone contrasts and observation metadata; no mixing units in ratios.

**Preparation before execution:** Expose v1.2 per-time tokens before global pooling; Implement matched raw SAR descriptors and fixed-orbit/geometry ledger; Validate token masks and missing-time pooling without fabrication.

**Encoding:** Fresh model-specific extraction of held imagery is needed.

### E05 — Radar texture beyond absolute backscatter (croma)

**1. Hypothesis.** CROMA pattern features add beyond conventional radar texture/change descriptors and retained absolute levels.

**2. Inputs.** Held primary-orbit ascending VV/VH four completed weeks, dates/masks; orbit-15/161 completed results supporting only.

**3. Model use.** Frozen base SAR branch, corrected publisher normalization. Encode dates separately, retain chronological SAR_GAP and differences instead of only their mean. No claim of native temporal attention.

**4. Matched comparator.** Same inputs: raw VV/VH level/SD/change plus fixed texture descriptors (horizontal/vertical adjacent-pixel contrast and lag-one correlation on valid pixel pairs), zone summaries and observation metadata.

**5. High-water contribution.** Compare C+R+CROMA with C+R under Q loss. Raw absolute amplitudes appear in both learned arms because input contrast stretch removes them from CROMA.

**6. Interpretation.** A positive result supports texture encoding beyond chosen transparent descriptors; a null does not show radar lacks hydrological information. No ad hoc replacement of publisher normalization.

**Raw descriptor specification:** Per-week raw levels, SD, changes, valid-neighbour contrast/correlation for VV and VH; undefined constant-image correlation remains missing.

**Preparation before execution:** Expose per-date SAR_GAP in compact output; Implement raw level and deterministic texture control with masks; Verify constant/no-data fixtures and corrected /255 normalization.

**Encoding:** Fresh model-specific extraction of held imagery is needed.

### E06 — Catchment-local HLS surface condition (prithvi)

**1. Hypothesis.** Pooling spatial features over the actual contributing catchment improves assessment beyond HLS descriptors and whole-tile averaging.

**2. Inputs.** Held six-band HLS 30m four completed weeks, dates/coordinates, catchment and DEM.

**3. Model use.** Frozen EO2 Tiny TL four-frame route; retain spatial/time tokens and pool observed catchment/elevation support. Document 6.72km tile receptive context and token footprint; no claim that masking removes all outside context.

**4. Matched comparator.** Same HLS pixels/times/areas: bands and NDVI/NDMI/MNDWI moments, changes, terrain and metadata. Matched global pooled Prithvi ablation supports pooling attribution.

**5. High-water contribution.** Test C+R+E under local-Q absence; separately report high-water/flood-case errors and effective represented area.

**6. Interpretation.** Global-to-local changes may reflect spatial support rather than architecture; control raw support and compare paired cases. Tiny is not the 300M/600M model.

**Raw descriptor specification:** HLS six-band/index weekly zone moments and changes; product/coverage/date descriptors.

**Preparation before execution:** Expose non-CLS spatiotemporal tokens and map token footprint to HLS grid; Implement area-weighted local pooling and no-data tests; Match four-frame TL metadata/order and raw-support comparator.

**Encoding:** Fresh model-specific extraction of held imagery is needed.

### E07 — Metadata-aware optical representation (copernicus_fm)

**1. Hypothesis.** Surface representations using correct location/date/scale add beyond raw spectra and identical metadata.

**2. Inputs.** Held primary coherent ten-band S2 four completed weeks, real patch coordinates/dates/scale. Existing TOA/QA60 route retained as product-domain sensitivity, not selected by final scores.

**3. Model use.** Frozen base; same published patch-mean/LayerNorm readout, metadata populated with lon/lat, days since epoch and internal token area. Independent frame features retained in time order. No-metadata matched ablation.

**4. Matched comparator.** Same bands/indices, dates, coordinates, token scale, season and coverage; train-only simple metadata and spectral model with same residual-head budget.

**5. High-water contribution.** Assess metadata-enabled features against equal-input raw descriptors and C; verify gain persists beyond coordinates/date alone.

**6. Interpretation.** Metadata-only benefit is not learned hydrological state. Product-domain/support changes cannot be credited solely to metadata.

**Raw descriptor specification:** Weekly band/index moments/changes plus explicit location/day/scale/coverage; metadata-only supporting arm.

**Preparation before execution:** Implement known-metadata route and chronological frame outputs; Test 0.0256km2 token area, date units and coordinate order; Replay no-metadata/product-domain evidence on exact paired cases.

**Encoding:** Fresh model-specific extraction of held imagery is needed.

### E08 — Cross-watercourse landscape transfer (dofa)

**1. Hypothesis.** Wavelength-conditioned landscape context improves transfer to another held watercourse beyond physical/geographic/raw spectral descriptors.

**2. Inputs.** Held v1 six non-TCI S2 bands, preceding twelve completed months, coordinates, catchment areas/DEM and river-group mapping. No new sensor or v2 upgrade.

**3. Model use.** Use held frozen v1 monthly vectors as antecedent landscape context, with train-only transformations. Leave one entire watercourse out across all years, then evaluate each year using only earlier years from other watercourses; group all Wurm sites together. No same-watercourse target outcomes used to fit/readout or select tuning.

**4. Matched comparator.** Same raw optical summaries/indices and terrain/area/coordinates/season; simple transfer correction and cross-watercourse conventional reference using area-normalized mm/h trajectories.

**5. High-water contribution.** Primary contrast under local-Q absence. Remove contemporaneous same-watercourse peer-Q proxies too. Report a separate transfer reference and target adaptation with known historical C only as explicitly labelled deployment variant, not ungauged proof.

**6. Interpretation.** Few independent watercourses limit generalization. This is held-network watercourse transfer, not a country experiment or unmonitored-basin validation. Do not rank its magnitude directly against same-gauge experiments.

**Raw descriptor specification:** Twelve-month six-band means, red-edge/NIR and NIR/SWIR contrasts, seasonal variability and zone terrain/area descriptors; use only genuinely held non-TCI inputs.

**Preparation before execution:** Implement watercourse-grouped chronological folds and source-only tuning; Build mm/h transfer baseline and raw landscape descriptors; Poison every target-watercourse Q source to verify exclusion; retain unavailable-fold ledger.

**Encoding:** Reuse the specified held encoder vectors; raw-descriptor and downstream work still needed.

### E09 — Ordered optical surface context (terramind)

**1. Hypothesis.** A small supervised temporal readout on TerraMind features adds beyond the same ordered optical descriptors.

**2. Inputs.** Held ten-band S2L2A four completed weeks, masks/dates, catchment and DEM. No generation, TiM, extra labels or modality expansion.

**3. Model use.** Frozen 1.0 Tiny; supported single-frame backbone used through a verified ordered-frame readout (wrapper if API-equivalent), catchment pooled per frame, concatenate levels/changes. No claim of pretrained temporal attention.

**4. Matched comparator.** Identical ordered S2 bands/indices and changes, season/terrain/coverage, with same residual-head capacity/tuning approach.

**5. High-water contribution.** Test temporal surface context against C+raw under local/all-Q absence; supporting unordered-frame-mean ablation on paired support.

**6. Interpretation.** A benefit from order belongs to the downstream temporal readout, not proof the backbone learned river dynamics. Flood mapping/generation remain different tasks.

**Raw descriptor specification:** Ordered weekly S2 band/index mean/SD/change and observation metadata.

**Preparation before execution:** Implement ordered-frame frozen-backbone output with compact cache; Validate wrapper equivalence/masks against direct single-frame calls; Keep label-free encoder and catchment residual supervision distinct.

**Encoding:** Fresh model-specific extraction of held imagery is needed.

### E10 — Product-matched multispectral spatial context (satmae)

**1. Hypothesis.** Multispectral features add beyond raw optical descriptors when evaluated on a product closer to the checkpoint domain.

**2. Inputs.** Held TOA/QA60 supplemental ten-band route as declared primary; matched SR route supporting. Restrict raw and encoded arms to identical acquisition/product/mask support.

**3. Model use.** Frozen multispectral base e199. Use held completed-month snapshot outputs initially; no temporal-RGB capability claim. New extraction only if a specific verified pooled-readout defect is found, not to manufacture ten extraction jobs.

**4. Matched comparator.** Same TOA bands/NDVI/NDMI/MNDWI moments, fixed spatial contrasts, date/season/coverage with same learned correction budget; paired SR repeats isolate domain/support effects.

**5. High-water contribution.** Evaluate C+R+E against C+R and C under local-Q absence, then rich/all-Q-absent references.

**6. Interpretation.** TOA chosen for checkpoint-domain rationale after earlier evidence exists; this is exploratory, not an untouched product selection. QA60/SR support differences are not encoder effects; keep paired and coverage views.

**Raw descriptor specification:** Monthly TOA band/index mean/SD and neighbour contrast; same-mask SR descriptors only for paired domain diagnostic.

**Preparation before execution:** Build TOA raw descriptors and exact supplemental context joins; Inspect held checkpoint readout/product contract and record primary choice; Implement same-acquisition/support domain comparison, not unpaired score subtraction.

**Encoding:** Reuse the specified held encoder vectors; raw-descriptor and downstream work still needed.

**E08 transfer override:** {"baseline": "C_transfer: earlier other-watercourse donor trajectories in mm/h; source-only fitting/tuning", "arms": ["C_transfer", "C_transfer+R", "C_transfer+R+E"], "target_watercourse": "Exclude every target-watercourse Q source from training, tuning and local-absence peer inputs, including all Wurm sites together", "inner_split": "Earlier-year folds with one source watercourse held out within training; no target-watercourse outcomes", "supporting_reference": "Target-history conventional C is deployment context only, never a training residual source or evidence of ungauged transfer"}

## Preparation and queue order

1. Implement one shared, chronologically cross-fitted conventional/residual backbone and exact raw/encoded feature-support joins. Test hidden/future-data poisoning and fixed-year versus rolling-reference accounting before interpreting encoder increments.
2. Prepare raw optical/SAR descriptors and DEM elevation zones once with source provenance; their reuse must not force identical model footprints or dates. Build model-specific feature tables, not another all-purpose averaged vector table.
3. First complete cached-vector experiments E08/E10 and the shared readout; independently implement extraction contracts for E01/E02/E04–E07/E09. E03 needs small exact-product reconciliation/acquisition and must not delay unrelated work.
4. Run conformance fixtures for each selected checkpoint, followed by a measured representative **full spatial context** benchmark and missing-support fixture. These are engineering tests, not a sampled final analysis. Predict census time and storage from actual counts and measured throughput; no defensible completion ETA exists yet.
5. Queue validated extraction tasks one MPS plus at most two CPU lanes, with per-model environment and output hashes. MPS support is checked for that particular adapter; do not force CPU-only code onto it. Score only complete audited feature tables; continue unrelated experiments if one needs repair.
6. Audit/read all ten results individually, plus a common summary of incremental information, net high-water value, coverage and costs. No uniform winner ranking across different cohorts/tasks. Freeze configuration changes with dated amendments rather than overwrite the trial that motivated them.

## Readiness and limits

The [readiness sweep](reviews/limburg-ten-experiment-readiness-2026-10-29.md) and its JSON receipt distinguish held assets from implemented experiment components. Existing extraction/scoring scripts implement earlier designs and cannot simply be relabelled as these experiments. A preparation status is an engineering dependency, not a decision to abandon a chapter or await optional data. No blanket stop is imposed on the ten-part project.
