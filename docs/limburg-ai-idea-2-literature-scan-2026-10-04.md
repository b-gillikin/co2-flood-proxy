# Idea 2: targeted literature scan (internal research aid, 2026-10-04)

This note tests the candidate Limburg AI idea against adjacent research. It is not a systematic review, a chapter design decision, or dissertation prose. Searches targeted peer-reviewed/primary research on flood knowledge graphs, flood RAG or agents, cross-border FEWS, and RAG evaluation for time, language, conflict, faithfulness, and abstention. The searches do not establish that no closer work exists.

## Candidate research question

Does grounding AI in river-basin structure and data provenance make its assessments of Limburg high-water events more reliable?

This is an evaluation of basin-grounded AI reasoning. Give a general LLM, document-only RAG, and basin-grounded RAG with a curated river map and checked gauge-data tools the same historical questions. Score source-linked assessments for river relationships, agency rules, measurement quality, and justified limits on what can be concluded. The three arms show the value of the practical system relative to simpler alternatives; because capabilities are added together, the comparison alone cannot assign improvement to one component. Keep that distinction clear when reporting results. A small component check is possible later if needed, not a prerequisite for exploring the idea.

## Closest work and what it means

| Source | Relevant finding/design | Consequence for Idea 2 |
| --- | --- | --- |
| [Karimanzira et al. 2025, *Algorithms*](https://www.mdpi.com/1999-4893/18/11/713) | A flood knowledge graph plus RAG integrates hydro-meteorological, GIS, forecast and other sources in a German case study; it compares with a text-only LLM using expert-scored queries. | Directly relevant precedent, not a reason to abandon the three-arm evaluation. Our potential difference is a document-only RAG middle arm and a focused test of basin relationships, cross-border source rules, measurement provenance, and justified abstention. The final claim must follow the results. |
| [OFPO/KGFPO 2025, *Environmental Modelling & Software*](https://www.sciencedirect.com/science/article/pii/S1364815225000015) | Formal ontology and knowledge graph for flood observation events, tasks, sensors, methods and data. | A graph is an existing technique, not the scientific result. Tables may be enough for our small corridor. |
| [HydroAgent 2026 preprint](https://arxiv.org/abs/2607.23983) | Skill-orchestrated LLM embeds explicit rules in a flood-forecast workflow and evaluates hydrologic judgments. | An agent guided by hydrologic rules is also not new. It targets forecast-model workflow, whereas this idea targets the correctness and limits of cross-border evidence synthesis. Preprint status matters. |
| [Busker et al. 2026, *NHESS*](https://nhess.copernicus.org/articles/26/1457/2026/nhess-26-1457-2026.html) | Comparative interviews and document review of northwestern European FEWS report varying threshold and warning arrangements. Cross-border data exchange is generally well organized; warning exchange/translation still has gaps. | Motivates jurisdiction-aware assessment, but does not prove our system will improve operations. Use primary agency documents for rules valid in a specific year. |

## Evaluation literature that bears directly on design

| Source | Implication |
| --- | --- |
| [MRAG / TempRAGEval 2025](https://aclanthology.org/2025.findings-emnlp.167/) | Time-sensitive questions can defeat ordinary retrieval. Include rule effective dates, rating eras, and explicit unanswerable historical-threshold cases. |
| [Ragability 2026](https://aclanthology.org/2026.lrec-1.182/) | Detecting conflicting passages is easier than answering correctly from them. Score the final source-grounded answer, not only conflict detection. |
| [XRAG 2025](https://aclanthology.org/2025.findings-emnlp.849/) | Cross-lingual retrieval and answer generation can fail separately. Check German/Dutch source selection for English-language questions. |
| [Madhusudhan et al. 2025, COLING](https://aclanthology.org/2025.coling-main.627/) | LLM abstention is imperfect. Mix answerable and genuinely unsupported questions; report both false assertions and unnecessary refusals. |
| [Tamber et al. 2025, EMNLP Industry](https://aclanthology.org/2025.emnlp-industry.54/) | RAG still produces unsupported or contradictory claims. Human source-linked adjudication remains important, especially for high-consequence facts. |

## Feasible claim and boundaries

The plausible contribution is an **evaluation of basin-grounded AI reasoning**: whether the full architecture produces more reliable source-linked assessments than a general LLM and document-only RAG, and where it still fails. Existing flood RAG work gives a precedent and comparator. A different task, three-arm design, selected Dutch–German basin setting, and attention to river topology, measurement provenance and abstention can make a meaningful contribution without claiming to invent RAG or flood knowledge graphs. This is an inference from the targeted scan, not a claim of global priority. Keep Dutch-only, German-only, and genuinely cross-border tasks distinguishable. Test tasks that the held evidence can adjudicate and include questions that require saying the record is insufficient.

The held data and correspondence support retrospective observation-based questions. Historical Dutch Fase thresholds are unavailable, and LANUK reconstruction/provisional-curve details remain unresolved. These are suitable tests of source limits, not reasons to infer historical warning decisions. Without as-issued forecasts, archived warnings, and an operational evaluation, this study cannot claim forecast skill, warning lead time, or improved real-world FEWS outcomes. A simple event-selection page may display each assessment and its evidence; the evaluation is the research result.

## Next evidence check before implementation

Inventory exact Dutch and German source documents, gauge-period overlap, verified river order, and metadata rights/permissions. Then draft a small set of source-linked historical questions and independently adjudicated answers to see whether enough nontrivial cross-border tasks exist. This is a feasibility check, not a new data-request requirement or a chapter gate.
