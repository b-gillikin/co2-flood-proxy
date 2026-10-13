# Session handoff

Updated 2026-10-12 after the Limburg code and directory review.

## Active chapter

> **Can basin-aware AI produce reliable cross-border high-water assessments
> from fragmented Dutch and German data?**

The controlled comparison has two linked parts:

1. **Evidence-access ablation:** general LLM, document RAG, RAG plus checked
   numerical tools, and RAG plus tools plus the curated basin/provenance graph.
2. **Historical-representation comparison:** conventional hydrological
   signatures versus a raw 512-hour hydrograph control and frozen TTM-R2 event
   representations; AlphaEarth is tested only as catchment context.

The same generator, prompts and decoding settings remain fixed across the
evidence-access arms. Retrieval and answer generation are scored separately.
The policy experiment repeats tasks under fragmented, harmonized and
provenance-complete information conditions.

## Current state

- Six Dutch tributary series, provider semantics, rating eras, catchments,
  RADOLAN rainfall and ERA5-Land weather are held and audited.
- Four German LANUK station packages are held. LANUK has confirmed that
  priority-sensor gaps were closed from redundant local sensors rather than
  neighbouring-gauge reconstruction. Post-July-2021 discharge remains
  provisional, especially above warning levels 2 and 3 at Randerath and
  Herzogenrath. The records still require conversion into event objects
  equivalent to the Dutch library before the central result can be described
  as cross-border.
- The event-review source contains 724 Dutch onsets. With the fixed 512-hour
  history, 570 events are complete across discharge, rainfall and weather; 558
  also have a complete 72-hour withheld discharge response for scoring.
- The conventional top-five analogue mean did not beat an expanding historical
  median. This is a baseline result, not a reason to add models.
- TTM-R2 assets and documents are downloaded and verified. The AlphaEarth
  catchment-year export is downloaded and validated: 72 rows, nine catchments,
  eight years and 64 embedding dimensions.
- No LLM answers have yet been generated or scored.

## Immediate work

1. Add a deterministic importer for the validated AlphaEarth table and join it
   by the prior-year rule already fixed in the protocol. Evaluate it on the
   common event subset from 2018 onward rather than the full temporal frame.
2. Implement the raw 512-hour nearest-neighbour control and frozen TTM-R2
   representation on the same 570-event frame.
3. Convert the held German Wurm records into the common event schema. Preserve
   redundant-sensor continuity, curve-validity eras and post-July-2021
   provisional high-flow status; do not label the series as neighbour-gauge
   reconstruction.
4. Complete human review of gold answers, claim-level evidence and genuinely
   unanswerable cases before running the fixed LLM.
5. Run the evidence-access arms, then the three information-governance
   conditions. Keep retrieval, citation support, factual correctness and
   abstention as separate outcomes.

Before any generated answers are inspected, pin the single generator and
decoding contract, blind arm labels for scoring and freeze the reviewed case
bank. Representation comparisons use paired queries with storm-clustered
uncertainty; AlphaEarth uses its smaller 2018+ common subset and is interpreted
at catchment/catchment-year support rather than event-row sample size. The full
scientific audit is in
`reviews/limburg-scientific-readiness-audit-2026-10-13.md`.

Do not add another foundation model, fine-tuning programme, forecast target,
dashboard, operator study or data source merely because it is available. A new
component must resolve a named failure in the fixed comparison.

Completed alternatives are indexed at
`archive/retired-directions/2026-retrospective-high-water/README.md`.
