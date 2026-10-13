# Foundation-model literature for the Limburg basin-aware AI chapter

**Status:** targeted literature review and design lock, 2026-10-11. This is a
bounded review for model selection and evaluation, not a systematic review of
all Earth foundation models.

**Scope update, 2026-10-13:** The RAG and three-condition policy experiment
language below is historical. The active analogue design and its direct
hydrograph-similarity literature link are in
`limburg-historical-analogue-active-design-2026-10-13.md` and
`limburg-analogue-literature-bridge-2026-10-13.md`.

## What was reviewed

The search covered four literatures that meet in the proposed experiment:

1. Earth-observation and Earth-system foundation-model reviews;
2. remote-sensing foundation-model benchmarks;
3. hydrometeorological and streamflow foundation-model evaluations; and
4. learned geospatial representations used as catchment descriptors.

The chapter is not asking which foundation model is best in general. It asks
whether a pretrained representation improves retrieval and source-grounded
assessment of historical cross-border high-water events beyond conventional
hydrological descriptors, when basin topology and measurement provenance are
held constant.

## Review and benchmark evidence

| Source | What it establishes | Consequence for this chapter |
| --- | --- | --- |
| Zhu et al. (2026), *On the foundations of Earth foundation models* | The TUM-led perspective proposes 11 properties of an ideal Earth FM, including geolocation, scale and time awareness, multisensor support, uncertainty, physical consistency and links to language models. It also concludes that no current model dominates all criteria. | Treat the paper as an evaluation rubric, not a shopping list. The chapter directly tests location/scale representation, time, uncertainty and physical consistency. It does not attempt to construct an ideal universal model. |
| Xiao et al. (2025), *Foundation Models for Remote Sensing and Earth Observation: A Survey* | Organizes visual, vision-language and language foundation models for remote sensing, and emphasizes sensor, scale, spectral and temporal differences from natural imagery. | Prefer an Earth-observation representation with documented geospatial pretraining. Do not infer suitability from natural-image benchmark performance. |
| Lu et al. (2025), *Vision Foundation Models in Remote Sensing: A Survey* | Reviews pretraining, architectures and downstream use while identifying data quality, compute and generalization as continuing constraints. | Supports a frozen or already-published representation and a bounded downstream evaluation instead of local model development. |
| Xiong et al. (2024), *EarthNets* | Catalogues more than 500 Earth-observation datasets across tasks, including disaster monitoring, weather and climate. | Useful as a data and benchmark index; it does not create a new chapter data requirement. |
| Lacoste et al. (2023), *GEO-Bench* | Provides common classification and segmentation tasks, 20 baselines and an aggregated evaluation procedure. | The transferable lesson is controlled comparison: identical downstream data, splits and adaptation for each representation. Its imagery tasks are not the Limburg outcome benchmark. |
| Simumba et al. (2026), *GEO-Bench-2* | Extends the TUM/IBM/ServiceNow benchmark to 19 datasets, multimodal and multitemporal inputs, and capability-specific comparisons. No model dominates across tasks. | Confirms that model selection must follow the Limburg modality and task. Retain as a current benchmark reference; do not import its model roster as a dissertation experiment. |
| Adorni et al. (2025), capabilities-encoding benchmark review | Finds fragmented and expensive comparison across remote-sensing FM studies and encodes model capabilities to narrow candidate selection. | Select models from task needs first. Do not run a model leaderboard or broad sweep. |
| Ullrich et al. (2025), independent evaluation recommendations | Calls for common diagnostics, physical checks, transparent data/model provenance, open implementations and out-of-sample evaluation. | Predefine retrieval and assessment outcomes, retain conventional baselines, version inputs, expose failures and test held-out events. |

## Direct hydrology and hydrometeorology evidence

| Source | Evidence | Use here |
| --- | --- | --- |
| Zhang et al. (2025) | General foundation models were useful for data processing and event diagnosis in the authors' hydrometeorology trials, but forecasting remained unreliable; hallucination, responsibility, over-reliance and openness remained concerns. | Supports an assistive, source-linked event-assessment role. It also supports the boundary against automated warning or unvalidated forecasting claims. |
| Sun and Sun (2026) | Four time-series foundation models were tested zero-shot on streamflow. The strongest models could be competitive in some univariate settings, while multivariate and peak-flow performance remained difficult. | Justifies one open TSFM challenger and makes superiority an empirical question. High-water behavior must be scored separately from average performance. |
| Liu et al. (2025) | Benchmarks LSTM and 11 attention architectures across hydrological tasks and tests pretrained models in zero-shot settings. LSTM remained strongest for several regression and short-horizon tasks, while relative performance changed with task complexity and horizon. | Reinforces a conventional baseline, task-specific metrics and the rule that architecture novelty is not evidence of value. |
| Brown et al. (2025), AlphaEarth Foundations | Produces annual, 64-dimensional, approximately 10 m global satellite embeddings intended for low-data downstream use. | Feasible geospatial representation product; aggregate within verified catchment units rather than treating pixels as event dynamics. |
| Liu et al. (2026) | Across 531 CAMELS basins and a 3,434-basin global experiment, AlphaEarth and StefaLand embeddings acted as transferable catchment descriptors. AlphaEarth-only temporal performance was close to conventional attributes; combined representations helped more under spatial transfer. | Strongest direct precedent for catchment aggregation and the conventional-versus-learned representation comparison. It does not show that embeddings improve event retrieval in Limburg. |
| Ou and Zheng (2026) | AlphaEarth embeddings improved spatiotemporal hydrological generalization across 455 Australian catchments, with larger gains in human-affected and poorly represented basins. | Supports the representation hypothesis and makes cross-catchment similarity a meaningful target. Different geography, outcome and model prevent direct transfer of effect sizes. |
| Qu et al. (2026, preprint) | Tests AlphaEarth embeddings for hydrological simulation and donor-basin selection. | Relevant to the analogue/donor interpretation, but remains supporting evidence until peer reviewed. |
| Lin et al. (2026, preprint) | Fuses satellite embeddings for streamflow reconstruction across a river network and reports stronger gains for magnitude/bias than timing. The work also highlights the annual embeddings' inability to represent event-scale hydrological state. | Reinforces the division of labor: catchment embeddings describe place; rainfall, antecedent conditions and hydrographs describe the event. |

## Literature locked for the chapter

### Core design and evaluation set

These sources should appear in the chapter's method or design rationale:

- Zhu et al. (2026): Earth-FM selection and evaluation criteria;
- Xiao et al. (2025): remote-sensing FM taxonomy and domain constraints;
- Lacoste et al. (2023): controlled downstream comparison;
- Ullrich et al. (2025): independent, physically informed evaluation;
- Zhang et al. (2025): defensible assistive role in hydrometeorology;
- Sun and Sun (2026): direct zero-shot streamflow TSFM benchmark;
- Liu et al. (2025): hydrological architecture and zero-shot benchmark;
- Brown et al. (2025): AlphaEarth product and intended representation;
- Liu et al. (2026): catchment aggregation and transferable descriptors; and
- Ou and Zheng (2026): hydrological generalization as a representation problem.

### Basin, provenance and policy set

Retain the already identified flood knowledge-graph/RAG work, ontology-based
flood-platform work, Busker et al.'s cross-border FEWS comparison, provider
documentation and the chapter's historical-event literature. These establish
the basin graph, institutional rules, source provenance and policy experiment.

### Supporting or parking-lot set

Lu et al., EarthNets, GEO-Bench-2, Adorni et al., Qu et al., Lin et al. and individual
weather/EO foundation-model papers are supporting literature. They should not
each create a model arm. HydroGEM, graph neural networks, weather foundation
models, fine-tuning and multimodal vision-language models remain parked unless
a core experiment exposes a specific failure that one of them can test.

## Gap this chapter can test

The reviewed Earth-observation benchmarks mostly evaluate mapping,
classification or segmentation. The newer hydrology papers evaluate runoff
prediction, reconstruction or transfer to other catchments. The flood
knowledge-graph and RAG work integrates heterogeneous evidence, but does not
isolate whether conventional versus pretrained hydrological representations
improve historical-event retrieval and source-grounded assessments under real
measurement limitations and cross-border institutional rules.

That intersection is the chapter's tractable gap: **a controlled downstream
evaluation of conventional and pretrained event/catchment representations
inside a basin- and provenance-grounded cross-border high-water assessment
system.** This is an inference from the targeted review, not a claim that no
related study exists anywhere.

## Design consequences

1. **Keep three representation levels.** Text retrieval is the baseline;
   conventional hydrological signatures add event dynamics; foundation-model
   representations are challengers.
2. **Give each model the same test.** Use the same historical events, temporal
   splits, catchment units, evidence packet and scoring rules. Do not compare
   published headline metrics from incompatible benchmarks.
3. **Separate place from event.** AlphaEarth can represent relatively stable
   catchment surface characteristics. It cannot replace hourly rainfall,
   antecedent wetness, discharge/stage or provider quality flags.
4. **Make extremes and abstention explicit outcomes.** Report high-water
   retrieval quality, unsupported-claim rate, provenance handling and
   calibrated abstention, not only average error.
5. **Use one TSFM and one geospatial product.** Candidate choice requires open
   weights or reproducible access, documented preprocessing, compatibility with
   held data, manageable compute and a named baseline comparison.
6. **Retain hydrological constraints outside the LLM.** Verified river
   topology, time, units, rating periods and numerical calculations remain
   deterministic inputs or checked tools.
7. **Treat policy as an information-governance experiment.** Compare fragmented,
   harmonized and provenance-complete evidence environments. Do not infer live
   operational benefit from a retrospective accuracy result.

## TUM criteria mapped to the bounded experiment

| TUM criterion | Bounded implementation |
| --- | --- |
| Geolocation and scale awareness | Verified catchment/station graph and catchment-level aggregation |
| Balanced geographic representation | Test Dutch and German records separately and together; report coverage imbalance |
| Time variable | Assessment-time cutoffs and event histories; annual embeddings never stand in for hourly state |
| Multisensor evidence | Rain, flow/stage, weather and satellite-derived catchment descriptors remain distinguishable |
| Uncertainty quantification | Retrieval uncertainty, missing-data flags and abstention outcomes |
| Physical consistency | Basin topology, temporal order and checked numerical tools |
| LLM integration | Fixed generator synthesizes supplied evidence and citations only after retrieval is evaluated |
| Carbon minimization | Reuse frozen embeddings and one challenger; no local pretraining or model sweep |

The remaining ideal-model properties are background considerations, not gates
for this dissertation experiment.
