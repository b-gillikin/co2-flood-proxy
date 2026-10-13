# Limburg high-water analogues: active research design

**Decision date:** 2026-10-13. Internal research plan; Brian writes dissertation text.
This supersedes the four-arm RAG and three-condition information-governance
experiments in the 2026-10-11 basin-AI design. Those files remain as dated
research history and evidence-preparation aids, not chapter requirements.

## Question and contribution

> Can basin-aware AI find useful past high-water events across Limburg's Dutch
> and German tributaries, and identify when the available evidence is too
> uncertain to use?

The research test is whether learned event and catchment representations add
useful historical analogues beyond transparent hydrological summaries. The
policy connection is concrete: station identity, river relationships, rating
eras, provisional measurements and source provenance determine whether an
analogue can be trusted for cross-border evidence exchange. This is a
retrospective archive study, not an operational forecast or warning study.

## One core comparison

Use the held 512-hour assessment histories and 72 withheld response hours.
Compare the fixed representation arms in `ai-eval/representation-arms.json`:

| Arm | Role |
| --- | --- |
| R0 conventional discharge and rainfall signatures | Practical hydrological benchmark |
| R1 raw 512-hour discharge shape | Same-input temporal control |
| R2 frozen TTM-R2 discharge representation | Temporal foundation-model challenger |
| R3 prior-year AlphaEarth catchment context | Bounded geospatial increment on the common 2018+ subset |

R1 versus R2 tests the *frozen representation's* incremental value against raw
similarity on identical inputs. It does not isolate pretraining as a causal
mechanism. R0 includes rainfall, so it is the practical comparator, not a
same-input control. R3 must be compared with the same event representation
without AlphaEarth and with a simple catchment-area control. Its independent
support is limited by catchments and years, not by the count of event rows.
R4 fusion remains optional only if R0 and R2 have useful, distinct behavior;
it is not necessary to complete the chapter.

For each query event, eligible analogues come from earlier regional storms
whose 72-hour responses have finished by the query cutoff. Select at most one
event per prior storm so one multi-gauge storm cannot fill the top-k list.
Hold the eligible queries and candidate pool fixed across paired comparisons.
Score retrieved events against the withheld
72-hour response and human-reviewed hydrological relevance. Report sample
counts, watercourse-specific results, paired storm-clustered uncertainty and
leave-one-watercourse-out behavior. On the corrected distinct-storm selection,
the conventional top-five analogue mean and expanding historical median are
effectively tied (peak-ratio MAE 0.6423 versus 0.6424 on 534 queries). That is
an honest baseline rather than a reason to search for new models after results.
Retain the existing measurement-concern flags in the main run and repeat the
paired comparison without flagged queries or donor events as a sensitivity.
An uncertain peak need not erase a known onset, but it may weaken a
response-based score.

The full-rating-era p99 event labels and normalization are retrospective.
They must not be described as values known at each historical onset. No
as-issued forecast skill, warning lead time or agency decision benefit follows
from this design.

## Cross-border and policy interpretation

The current event library is Dutch. Convert the held German Wurm records into
the common event schema before describing the representation result as
cross-border. Preserve the provider's redundant-local-sensor continuity,
rating validity and provisional post-July-2021 high-flow status. Keep the two
Wurm stations nested within one watercourse; do not count them as independent
tributaries. Use only inputs that can be aligned on both sides, or report the
German analysis separately with its narrower input set.

Record cases where a retrieved event looks similar numerically but is
inapplicable because of river identity, rating era, quality, missingness or
provisional discharge. These failures support a bounded recommendation for
minimum cross-border identifiers and provenance fields. A source-linked
example assessment may illustrate a result after the quantitative comparison;
it is not a second RAG experiment or evidence of operator usefulness.

## What is no longer required

- No general-LLM versus RAG versus tools versus graph arm comparison.
- No 30-question generated-answer benchmark, generator selection or LLM
  scoring exercise to complete this chapter.
- No fragmented/harmonized/provenance-complete policy experiment.
- No masked-observation task or extra event-assessment benchmark solely to
  connect a RAG system to the representation comparison.

The 30-case bank, source inventory, verified basin graph, rubric and script 63
remain as optional evidence QA and historical feasibility work. They can help
check factual statements or source links, but their completion is not a gate
for the core analysis. The prior design and audits remain dated records of why
the scope was narrowed.

## Next work

1. Join the validated AlphaEarth catchment-year table by the prior-year rule
   and verify the common 2018+ sample.
2. Run raw-discharge R1 and frozen TTM-R2 R2 on the same Dutch event frame,
   alongside R0 and the historical-median benchmark.
3. Convert the held German records and assess what comparison is valid on
   common inputs, reporting Dutch and German results distinctly.
4. Review retrieved analogues and provenance-related failure cases, then
   interpret positive, null and unstable results within this retrospective
   scope.
