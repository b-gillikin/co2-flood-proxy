# Limburg basin-grounded AI: bounded feasibility pilot

**Status:** internal research aid, 2026-10-11. This does not replace the live
Limburg chapter protocol or supply dissertation prose.

## Question and boundary

The candidate study asks whether explicit river-basin structure and data
provenance improve AI assessments of historical Limburg high-water evidence.
The output is a cited retrospective situation assessment. It is not a flood
forecast, an issued warning, or evidence of operational benefit.

The first pass deliberately stops before model generation. It tests whether a
small, auditable evidence base, benchmark and set of comparison arms can be
built without adding new data requests or a user interface.

## 1. Evidence inventory

`docs/ai-eval/source-inventory.json` contains 14 versioned source records:

- Waterschap Limburg provider correspondence, the July 2021 technical report,
  current thresholds, rating eras, gauge identities and checked event records;
- four LANUK station packages plus the replacement Honsdorf stage delivery and
  its audit;
- the RWS Maas quality audit and official quality-code guide; and
- the northwestern-European FEWS comparison and International Meuse plan for
  institutional context.

Each record identifies its jurisdiction, agency, validity dates where known,
local path or URL, availability and a compact retrieval passage. Provider and
official records remain primary evidence; researcher audits make file
semantics and known limits retrievable but do not create agency rules.

The inventory is adequate for a pilot about station identity, time semantics,
rating and datum limits, current-versus-historical rules, interpolation and
justified abstention. It is not adequate for a comprehensive comparison of
Dutch and German warning decisions because dated operational-warning archives
and a complete German rule corpus are not held.

## 2. Source-backed question bank

`docs/ai-eval/benchmark-draft.json` contains 30 draft cases. Every case records
a reference answer, required and forbidden claims, gold sources, applicable
scoring dimensions, expected abstention and any deterministic tool calls.

Eight cases form the initial pilot. The remaining 22 are a development bank,
not a hidden test set. They should be reviewed and frozen before any model is
run. The bank covers questions that can expose consequential errors rather than
generic hydrology knowledge: applying a current threshold to 2021, treating an
interpolated Maas series as direct measurement, confusing Honsdorf with the
Wurm, inventing station order, treating matching timestamps as validation, and
claiming a warning decision from a researcher-defined event table.

The cases are not statistically representative of all FEWS work. Any eventual
claim is limited to this deliberately constructed set of Limburg evidence
tasks.

## 3. Four fixed evidence-access arms

`docs/ai-eval/system-arms.json` defines one architecture comparison using the
same frozen language model:

1. **General LLM:** question only.
2. **Document RAG:** question plus retrieved corpus passages.
3. **RAG + checked tools:** the same passages plus narrow read-only lookups over
   audited gauge, threshold, rating, event and RWS-quality tables.
4. **Basin-grounded:** the same RAG and tools plus a curated, source-linked map
   of watercourses, stations, agencies and jurisdictions.

The third arm is essential: it separates the value of deterministic data
access from the incremental value of basin structure. The pilot code enforces
that ordinary tool-RAG does not receive graph facts. No fine-tuning, model
sweep, autonomous warning action or UI is part of this experiment.

## 4. Scoring

`docs/ai-eval/scoring-rubric.json` defines seven case-level dimensions scored
0, 1 or 2: factual correctness, source entailment, temporal/jurisdictional
applicability, basin/station identity, measurement provenance, calibrated
abstention and answer completeness. Only dimensions marked for a case are
scored.

Unsupported assertions and needless refusal are different errors. A correct
answer may need to say that historical thresholds, exact peak discharge,
datum stability or station order cannot be established. Citation presence
alone is insufficient; a cited source must entail the claim.

Model outputs should be anonymised by arm and scored against the frozen case
records. Retrieval must also be evaluated separately so synthesis failures are
not confused with missing evidence.

## 5. Evidence-path pilot

`scripts/63_build_basin_ai_pilot.py` validates the four design files, runs a
hybrid word/character TF-IDF retriever, executes only predeclared read-only
tools, and writes 32 prompt packets (8 cases x 4 arms). It does not call a
language model or score generated answers.

With three retrieved source records per question, every pilot question found
at least one gold source, but only 3 of 8 retrieved all gold sources. Raising
the allowance to five records improved complete retrieval only to 4 of 8.
This is a useful feasibility result: the evidence is accessible, but naive
similarity retrieval is not yet a fair basis for comparing final answers on
multi-source questions. The next retrieval pass should use source metadata and
case-relevant exact identifiers, then freeze the retriever. It should not add a
larger corpus merely to improve a metric.

The pilot therefore establishes that the proposed comparison is implementable
with held evidence and that arm separation can be enforced. It does not show
that basin grounding improves AI answers, because no model outputs have been
generated or scored.

## Smallest credible next experiment

1. Brian reviews the 30 reference answers, especially what each case requires
   and when abstention is expected.
2. Improve and freeze retrieval on the eight pilot cases, then freeze a
   separate scored subset before inspecting model outputs.
3. Choose one model/version, one structured output contract and deterministic
   decoding settings for all four arms.
4. Generate and log every prompt, retrieved source, tool result, graph fact and
   response; blind the arm labels for scoring.
5. Compare paired case-level errors and report counts and uncertainty. Treat
   any UI as a later way to inspect evidence, not part of the scientific test.

Expansion to dated warning archives or German operational rules is justified
only if the eventual research question explicitly tests warning-rule
applicability. The held corpus already supports the narrower and more original
measurement-provenance and basin-identity experiment.
