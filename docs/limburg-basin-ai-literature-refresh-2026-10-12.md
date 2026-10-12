# Limburg basin-aware AI literature refresh

**Status:** targeted update, 2026-10-12. This pass tests and tightens the active
design. It is not a systematic review and does not create new model or data
requirements.

## Question used for the pass

What does recent primary research imply for evaluating a system that combines
documents, a flood-basin/provenance graph, checked hydrological tools and
historical event representations?

## Most useful evidence

| source | useful result | consequence here |
| --- | --- | --- |
| [Du et al. (2025), OFPO/KGFPO](https://doi.org/10.1016/j.envsoft.2025.106317) | A flood-observation ontology can formally connect events, observation tasks, data, methods and sensors, improving heterogeneous resource retrieval. | The curated graph is scientifically defensible, but the graph itself is not the contribution. Test whether its explicit station-river-agency-quality relations prevent errors. |
| [Ru et al. (2024), RAGChecker](https://arxiv.org/abs/2408.08067) | RAG errors should be diagnosed separately at retrieval and generation stages using claim-level measures; more context can improve coverage while increasing noise sensitivity. | Report retrieval recall/precision separately from answer correctness and unsupported claims. Keep top-k fixed rather than tuning it against final answers. |
| [Zhang et al. (2024)](https://doi.org/10.18653/v1/2024.inlg-main.35) | Citation support is not adequately represented by a single binary or automated score; full, partial and unsupported citation relations can differ across evaluators. | Human-score every material claim as fully, partly or not supported. Automated faithfulness scores may be secondary diagnostics only. |
| [Thakur et al. (2024), NoMIRACL](https://doi.org/10.18653/v1/2024.findings-emnlp.730) | Robust RAG evaluation requires both relevant-evidence and non-relevant-evidence cases, including multilingual settings. | Preserve genuinely unanswerable cases and add hard negatives where a plausible source has the wrong jurisdiction, station or effective date. Score false answers and unnecessary abstentions separately. |
| [Russo et al. (2025)](https://aclanthology.org/2025.inlg-main.50/) | RAG systems still struggle with heterogeneous reliable knowledge bases, and model size does not uniformly determine faithfulness or context adherence. | Heterogeneity is part of the Limburg test, not noise to remove. Keep one generator fixed and compare information environments. |
| [Dihan et al. (2025), MapEval](https://proceedings.mlr.press/v267/dihan25a.html) | General foundation models need explicit testing on relational map reasoning rather than assumed spatial competence. | Score station-river membership, upstream/downstream and jurisdiction relations directly. Do not ask the LLM to infer verified topology from prose or map images. |

The earlier targeted review remains the basis for TTM-R2 and AlphaEarth. This
pass found no evidence that a second temporal model, another geospatial
foundation model or fine-tuning would answer the research question better.

## Bounded improvements

1. **Separate the failure stages.** Report source retrieval, checked-tool
   correctness, claim correctness, citation support and abstention as distinct
   outcomes. Do not collapse them into one “AI accuracy” score.
2. **Add an oracle-packet diagnostic.** For each case, give the fixed generator
   the gold evidence packet once. This is not another deployable system arm; it
   estimates whether a failure comes from retrieval/evidence assembly or from
   synthesis despite adequate evidence.
3. **Use hard negatives already implied by the case.** Include wrong-country,
   wrong-river, wrong-rating-era and current-versus-historical-threshold
   distractors. This directly tests the claimed value of basin and provenance
   grounding without acquiring more data.
4. **Score support at the claim level.** Use full, partial and no support, plus
   a separate factual-correctness judgment. A true statement without support is
   still a grounding failure.
5. **Keep paired comparisons.** Every arm answers the same cases with fixed
   generation settings. Report paired case-level differences and bootstrap
   intervals; avoid significance fishing across many overlapping metrics.
6. **Double-score a small audit sample.** A second knowledgeable reviewer can
   independently score roughly 20% of cases, selected across task types, to
   expose ambiguous gold answers or rubric wording. This is an annotation QA
   step, not an interview or operator evaluation.

## What not to add

- no second LLM family or model leaderboard;
- no generic GraphRAG framework merely to replace the small verified graph;
- no additional hydrological or geospatial foundation model;
- no fine-tuning before the frozen baselines are evaluated;
- no live warning, dashboard or operator-effectiveness claim; and
- no expansion beyond Limburg/Wurm to make the system look more general.

The main improvement is sharper causal attribution inside the experiment: when
performance changes, the design can say whether the difference came from
retrieval, deterministic basin/provenance structure, historical-event evidence
or the generator's synthesis.
