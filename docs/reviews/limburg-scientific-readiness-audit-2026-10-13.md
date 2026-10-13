# Limburg scientific readiness audit

**Audit date:** 2026-10-13  
**Scope:** active basin-aware AI design only

## Verdict

The chapter is scientifically credible and ready for implementation. Its
contribution is a controlled case-study evaluation of whether explicit basin
relations, checked numerical evidence, measurement provenance and pretrained
event/catchment representations improve retrospective high-water assessments.
It is not a forecast-skill, warning-effectiveness or agency-performance study.

No additional model family, broad literature search or external dataset is
needed before work begins. The remaining work is implementation, one bounded
human benchmark review and execution of the fixed comparisons.

## Corrections made in this audit

1. **Exact temporal context.** The event builder previously generated relative
   hours -512 through 0, which is 513 observations despite the pinned TTM-R2
   context of 512. It now generates -511 through 0: exactly 512 assessment
   observations plus 72 withheld hours. The rebuilt library has 724 events and
   422,816 rows. Completeness counts and the existing analogue result are
   unchanged.
2. **AlphaEarth support.** Annual embeddings begin in 2017 and use a prior-year
   rule. The fair comparison therefore begins with 2018 events and contains
   304 complete-input and 296 complete-outcome Dutch events, rather than the
   full 570/558 temporal sample. These rows represent six watercourses and a
   limited number of catchment-years; they are not independent catchment
   replicates.
3. **Arm separation.** Evidence access (A0--A3) and historical representation
   (R0--R4) are separate experiments. They no longer form one ambiguous ladder.
4. **Fair temporal contrast.** Raw hydrograph R1 and TTM-R2 R2 receive the
   identical standardized 512-observation discharge history. Their paired
   difference is the isolated test of temporal pretraining. The conventional
   signature baseline also contains rainfall and is therefore a practical
   comparator, not a same-input causal contrast.
5. **Policy language.** Fragmented, harmonized and provenance-complete packets
   are constructed evidence conditions. Their differences show how this system
   responds to information governance within the benchmark; they do not
   estimate effects on real agency decisions or flood outcomes.

## Statistical and evaluation contract to lock before outcomes

### Historical representations

- Use identical eligible queries and candidate pools for paired arm
  comparisons.
- Candidate events must be strictly earlier and from a different regional
  storm. No outcome after the query cutoff enters its representation.
- Primary learned-representation contrast: raw discharge R1 versus TTM-R2 R2.
- Report paired changes in peak-ratio absolute error and retrieval relevance,
  with query counts and watercourse-specific results.
- Treat events from the same regional storm as dependent. Use a paired
  storm-cluster bootstrap for descriptive intervals and a leave-one-watercourse-
  out diagnostic. Avoid nominal event-level significance tests.
- Treat AlphaEarth as a bounded context analysis. Report catchment-year support
  and leave-one-watercourse-out behavior; do not use 304 event rows as the
  independent sample size for a catchment-representation claim.
- The fact that the first conventional analogue loses to the historical median
  is a valid baseline result, not a trigger to change models or outcomes.

### AI evidence-access benchmark

- Use the eight pilot cases only to repair and freeze retrieval. Do not tune on
  generated answers from the scored cases.
- Human-review and freeze the remaining reference answers, gold sources,
  required claims, forbidden claims and expected abstentions before generation.
- Pin one generator model/version, prompt template, structured output schema,
  decoding parameters, seed, runtime and quantization before outputs are seen.
  One generator has not yet been selected; this is an implementation decision,
  not a reason to add a model leaderboard.
- Log every prompt, retrieved passage, tool result, graph fact and response.
- Randomize and blind arm labels during scoring. Score retrieval, checked-tool
  correctness, claim correctness, citation support and abstention separately.
- Have a second reader score a small stratified subset or the eight pilot cases
  to expose ambiguous rubric wording. Report agreement and resolve the rubric
  before scoring the held cases; this is quality control, not an operator study.
- Report paired case-level counts and differences. The curated cases are a
  purposeful benchmark, not a random sample of all FEWS questions, so avoid
  population-wide significance or prevalence claims.
- Retain the gold-evidence oracle packet as a diagnostic ceiling, not another
  deployable system arm.

## Cross-border validity

The Dutch event library alone cannot support the word *cross-border*. Before
the central result is described that way:

- convert Herzogenrath 1 and Randerath using one documented event rule and the
  same assessment/outcome boundary;
- preserve fixed UTC+1 source time, rating-curve validity, redundant local
  sensor continuity and provisional post-July-2021 high-flow status;
- keep the two stations as nested observations on one Wurm watercourse rather
  than independent tributaries;
- keep Herzogenrath 2 on Broicher Bach and Honsdorf on Beeckflies; and
- either supply matched rainfall/weather for a German representation task or
  restrict that task to evidence actually common across countries.

The source-grounded benchmark may already test cross-border identity and
provenance. The event-representation result becomes cross-border only after the
German extension is executed and reported separately from the Dutch sample.

## Claim boundary

A positive result would show that, on this fixed historical case study and
benchmark, a specified representation or evidence architecture improves
retrieval or source-grounded assessment. It would support recommendations for
minimum identifiers, topology and provenance fields in cross-border evidence
exchange.

It would not establish live forecast skill, warning lead time, causal flood
mechanisms, improved official decisions, deployment readiness or general
superiority of foundation models. A null result remains informative and does
not justify adding models after inspection.
