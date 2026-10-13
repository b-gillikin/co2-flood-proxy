# Limburg second scientific pass

**Date:** 2026-10-13  
**Scope:** then-active basin-aware AI chapter, after the 512-hour and AlphaEarth audit

**Scope update, 2026-10-13:** Brian removed the four-arm RAG and three-condition
policy experiments after this audit. Its RAG-specific repairs below explain
why that simplification is sensible; they are not remaining tasks. The active
plan is `../limburg-historical-analogue-active-design-2026-10-13.md`.

## Judgment

The chapter remains feasible with held data. The controlled comparisons are
worth running. The central claim needs to be earned in two places that the
current pilot does not yet cover: complete event-level assessments and German
event evidence. Neither requires a new data request or another model.

## Findings and narrow repairs

| Finding | Consequence | Repair before interpreting results |
| --- | --- | --- |
| The 30-case bank is mainly factual questions about stations, thresholds, and data quality. It contains no complete event situation-assessment task. | It can test evidence handling but cannot alone show that historical analogues improve AI assessments of high-water events. | Retain the 30 cases as a separate evidence benchmark. Add a small, reviewed event-level set using the existing Dutch event library and German records after conversion. Each event case must require an assessment that can actually use retrieved history. |
| Pilot `tool_calls` and arguments come from each benchmark case. | A2/A3 receive correctly routed tools; the pilot cannot establish autonomous tool selection or measure routing errors. | Keep this as a controlled tool-access experiment and log the routing as `benchmark_specified`. If a later system claims automatic routing, evaluate that separately rather than relabelling this result. |
| `retrieval_text` is a concise researcher-written source card for each document or dataset. Several cards already state the answer to benchmark questions. | The document arm measures retrieval and synthesis from curated cards, not retrieval from raw PDFs, emails, and tables. Graph facts also appear in some cards, so A3 tests structured access and packaging rather than wholly new facts. | Name the material accurately, freeze cards before generated answers, and report gold-source retrieval separately. Judge A1--A3 as incremental evidence routes; do not claim a pure graph-format effect unless factual coverage and packet size are matched. |
| Rating-era p99 thresholds use all observations in the era, including years after a query event. | The event label and p99-normalized signature are retrospective. `strictly earlier` analogue candidates do not turn the analysis into an as-issued forecast backtest. | Describe p99 as a fixed archive definition. Keep the result within retrospective assessment and avoid historical forecast-skill or prospective-leakage claims. A rolling-threshold redesign is unnecessary for the present question. |
| R1 and R2 receive identical discharge histories but use different transformations and distances. | Their difference tests the frozen TTM representation against raw similarity; it does not isolate pretraining itself as a causal ingredient. | Replace “causal pretraining effect” with “incremental value of the frozen TTM representation.” Retain the same-input comparison. |
| The fragmented/harmonized/provenance-complete conditions have not yet been built as executable packets. | The policy result is a specified experiment, not an existing finding. Missing evidence could be mis-scored as error if all conditions share one answer key. | Hold questions and underlying facts fixed; version the exact fields shown in each condition; score justified abstention as correct when a condition cannot establish the fact. |
| Only Dutch events are in the current 512-hour library. | The source-card questions can be cross-border now, but the historical-representation result is Dutch-only until German event conversion. | Report Dutch and German tasks separately; build the common German event schema before describing a cross-border representation result. |

## Smallest integrated demonstration

The chapter can remain one coherent study if the event-level set uses the same
source, graph, tool and representation components as the existing benchmark.
Choose a small set of reviewed historical events with distinct measurement
conditions, including at least one Wurm case once German conversion is ready.
For each case, fix an assessment cutoff, available evidence, hidden outcome or
source fragment, expected answer, and justified abstentions. Keep all facts
hidden from every arm surface when masking. Score the same assessment with the
conventional and learned analogue packets under one fixed generator.

This adds an evaluation bridge, not a new model or data stream. If the event
set cannot be completed, the defensible chapter claim is narrower: a
source-grounded AI evidence benchmark plus a separate retrospective analogue
representation comparison. It should not say that the analogue layer improved
AI situation assessments until that link is tested.

## Evidence basis

The local findings above come from `scripts/63_build_basin_ai_pilot.py`,
`scripts/46_review_events.py`, `src/event_study.py`, the 30-case benchmark,
source inventory and active design. The [IBM TTM-R2 model card](https://huggingface.co/ibm-granite/granite-timeseries-ttm-r2)
confirms the model's 512-step context requirement. The [official AlphaEarth
catalogue](https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_SATELLITE_EMBEDDING_V1_ANNUAL)
confirms that the embeddings are annual 64-dimensional summaries, supporting
their bounded use as catchment context.
