# Idea 2: targeted literature scan (internal research aid, 2026-10-04)

This note tests the candidate Limburg AI idea against adjacent research. It is not a systematic review, a chapter design decision, or dissertation prose. Searches targeted peer-reviewed/primary research on flood knowledge graphs, flood RAG or agents, cross-border FEWS, and RAG evaluation for time, language, conflict, faithfulness, and abstention. The searches do not establish that no closer work exists.

## Candidate research question

Does grounding AI in river-basin structure and data provenance make its assessments of Limburg high-water events more reliable?

This is an evaluation of basin-grounded AI reasoning. Give a general LLM, document-only RAG, RAG plus checked gauge-data tools, and RAG plus those tools and a curated river/agency map the same historical questions. Score source-linked assessments for river relationships, agency rules, measurement quality, and justified limits on what can be concluded. The added third arm helps separate the effect of checked observations from the effect of basin structure. The general LLM is a useful reference but cannot be expected to cite documents it has not received.

## Closest work and what it means

| Source | Relevant finding/design | Consequence for Idea 2 |
| --- | --- | --- |
| [Karimanzira et al. 2025, *Algorithms*](https://www.mdpi.com/1999-4893/18/11/713) | A flood knowledge graph plus RAG integrates hydro-meteorological, GIS, forecast and other sources in a German case study; it compares with a text-only LLM using expert-scored queries. | Directly relevant precedent, not a reason to abandon the evaluation. Our potential difference is the intermediate RAG arms and a focused test of basin relationships, cross-border source rules, measurement provenance, and justified abstention. The final claim must follow the results. |
| [OFPO/KGFPO 2025, *Environmental Modelling & Software*](https://www.sciencedirect.com/science/article/pii/S1364815225000015) | Formal ontology and knowledge graph for flood observation events, tasks, sensors, methods and data. | A graph is an existing technique, not the scientific result. Tables may be enough for our small corridor. |
| [HydroAgent 2026 preprint](https://arxiv.org/html/2607.23983) | Separates LLM interpretation, deterministic hydrological computation, explicit task instructions, structured output, and human review in a flood-forecast workflow. It reports judgment and forecast tests, including cases where a wrong early judgment degraded the later forecast. | Borrow the separation of roles, inspectable output contracts, and error-propagation analysis. Do not import its hydrological model, analog-based peak/volume prediction, or warning-publication pipeline into this retrospective assessment question. Preprint status matters; the paper says its full live code/environment is not publicly released. |
| [Busker et al. 2026, *NHESS*](https://nhess.copernicus.org/articles/26/1457/2026/nhess-26-1457-2026.html) | Comparative interviews and document review of northwestern European FEWS report varying threshold and warning arrangements. Cross-border data exchange is generally well organized; warning exchange/translation still has gaps. | Motivates jurisdiction-aware assessment, but does not prove our system will improve operations. Use primary agency documents for rules valid in a specific year. |

## Evaluation literature that bears directly on design

| Source | Implication |
| --- | --- |
| [MRAG / TempRAGEval 2025](https://aclanthology.org/2025.findings-emnlp.167/) | Time-sensitive questions can defeat ordinary retrieval. Include rule effective dates, rating eras, and explicit unanswerable historical-threshold cases. |
| [Ragability 2026](https://aclanthology.org/2026.lrec-1.182/) | Detecting conflicting passages is easier than answering correctly from them. Score the final source-grounded answer, not only conflict detection. |
| [XRAG 2025](https://aclanthology.org/2025.findings-emnlp.849/) | Cross-lingual retrieval and answer generation can fail separately. Check German/Dutch source selection for English-language questions. |
| [Madhusudhan et al. 2025, COLING](https://aclanthology.org/2025.coling-main.627/) | LLM abstention is imperfect. Mix answerable and genuinely unsupported questions; report both false assertions and unnecessary refusals. |
| [Tamber et al. 2025, EMNLP Industry](https://aclanthology.org/2025.emnlp-industry.54/) | RAG still produces unsupported or contradictory claims. Human source-linked adjudication remains important, especially for high-consequence facts. |
| [Nishida et al. 2026, TACL](https://aclanthology.org/2026.tacl-1.29/) | Graph structure quality can bottleneck downstream answers; simple template reports performed well in their evaluated setting. Check river-map accuracy and consider a rules-and-template comparator only after the core arms. |
| [Zhou et al. 2026, EACL](https://aclanthology.org/2026.eacl-long.114/) | Knowledge-graph QA benchmarks may reward direct lookup rather than reasoning under incomplete knowledge. Include questions requiring several sources or warranted uncertainty, not only facts copied from the map. |
| [Over-searching study 2026, EACL](https://aclanthology.org/2026.eacl-long.361/) | Retrieval may degrade abstention on unanswerable questions when evidence is noisy. Measure false assertions and unnecessary refusals separately. |

## Model and retrieval options checked on 2026-10-05

The word *foundation model* covers different input/output tasks. [Prithvi-EO-2.0](https://doi.org/10.1109/TGRS.2025.3642610) learns from Earth-observation imagery, [TerraMind](https://openaccess.thecvf.com/content/ICCV2025/papers/Jakubik_TerraMind_Large-Scale_Generative_Multimodality_for_Earth_Observation_ICCV_2025_paper.pdf) from multimodal EO data, and the [GraphRiverCast preprint](https://arxiv.org/abs/2602.22293) models river-system dynamics using topology and forcing. These are relevant to remote-sensing or forecasting questions, but are not substitutes for a language model that reads agency sources and explains gauge provenance. A [2026 catchment-embedding study](https://doi.org/10.1029/2026GL122814) likewise tests descriptors for rainfall-runoff modeling, not source-grounded situation assessment.

[HydroLLM](https://doi.org/10.2166/hydro.2025.100) is a domain-adapted language-model direction. Its published benchmark is hydrology knowledge QA drawn from textbooks and research literature, rather than local Dutch/German agency rules and station-quality records. It is worth a later matched-access model check, not replacing the general model in the core architecture comparison. [HydroEmbed](https://doi.org/10.2166/wst.2025.156) is a hydrology-specific *retriever/embedding model*, not a response generator; its reported tests are also QA-oriented. Evaluate it against the actual multilingual local corpus before adopting it.

The RAG design has substantive choices: exact and semantic retrieval, agency/date metadata, cross-lingual document retrieval, geographic applicability, and the curated river map. [GeoGraphRAG (2025)](https://doi.org/10.1016/j.jag.2025.104712) shows graph guidance for geospatial modeling, a different task. The [GeoRisk-RAG preprint (2026)](https://arxiv.org/abs/2608.22634) suggests explicitly checking geographic validity and abstaining when a location-specific source does not apply. The [temporal RAG benchmark](https://aclanthology.org/2025.findings-emnlp.167/) and [XRAG](https://aclanthology.org/2025.findings-emnlp.849/) support separate checks for time-valid and cross-lingual source selection. Start with a competent hybrid document retriever, use the same retriever in comparable arms, and log relevant-source retrieval separately from answer correctness. Change retrieval design in a targeted follow-up if error analysis shows a bottleneck; do not launch a grid of model-by-RAG variants by default.

## Feasible claim and boundaries

The plausible contribution is an **evaluation of basin-grounded AI reasoning**: whether the full architecture produces more reliable source-linked assessments than simpler alternatives, which additions help, and where it still fails. Existing flood RAG work gives a precedent and comparator. A different task, four-arm design, selected Dutch–German basin setting, and attention to river topology, measurement provenance and abstention can make a meaningful contribution without claiming to invent RAG or flood knowledge graphs. This is an inference from the targeted scan, not a claim of global priority. Keep Dutch-only, German-only, and genuinely cross-border tasks distinguishable. Test tasks that the held evidence can adjudicate and include questions that require saying the record is insufficient.

The held data and correspondence support retrospective observation-based questions. Historical Dutch Fase thresholds are unavailable, and LANUK reconstruction/provisional-curve details remain unresolved. These are suitable tests of source limits, not reasons to infer historical warning decisions. Without as-issued forecasts, archived warnings, and an operational evaluation, this study cannot claim forecast skill, warning lead time, or improved real-world FEWS outcomes. A simple event-selection page may display each assessment and its evidence; the evaluation is the research result.

## Next evidence check before implementation

Inventory exact Dutch and German source documents, gauge-period overlap, verified river order, and metadata rights/permissions. Then draft a small set of source-linked historical questions and independently adjudicated answers to see whether enough nontrivial cross-border tasks exist. This is a feasibility check, not a new data-request requirement or a chapter gate.
