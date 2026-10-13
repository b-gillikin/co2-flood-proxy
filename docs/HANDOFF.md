# Session handoff

Updated 2026-10-13 after implementing Steps 1--2 of the analogue study.
The canonical plan is
`limburg-historical-analogue-active-design-2026-10-13.md`.

## Active question

> Can basin-aware AI find useful past high-water events across Limburg's Dutch
> and German tributaries, and identify when the evidence is too uncertain to
> use?

The one core experiment compares conventional hydrological signatures, raw
512-hour discharge similarity, frozen TTM-R2 representations and a bounded
AlphaEarth catchment-context increment. River identity and measurement
provenance are used to judge whether retrieved analogues are applicable. The
work is retrospective, with no forecast-skill or operator-benefit claim.

## Current state

- Six Dutch tributary series, provider semantics, rating eras, catchments,
  RADOLAN rainfall and ERA5-Land weather are held and audited.
- Four German LANUK station packages are held. LANUK confirmed that priority
  sensor gaps were closed from redundant local sensors, not neighbouring
  gauges. Post-July-2021 discharge remains provisional, particularly above
  warning levels 2 and 3 at Randerath and Herzogenrath. German records still
  require conversion into event objects equivalent to the Dutch library.
- The event-review source contains 724 Dutch onsets. With a fixed 512-hour
  history, 570 events have complete discharge, rainfall and weather; 558 also
  have a complete 72-hour withheld discharge response.
- After selecting at most one event per prior storm, the conventional top-five
  analogue mean and expanding historical median are effectively tied on 534
  evaluated queries (peak-ratio MAE 0.6423 versus 0.6424). This is a baseline
  result, not evidence that analogue retrieval already adds value.
- The existing measurement-concern flags affect 37 of those queries and 189
  of the 2,670 originally selected donor slots. A sensitivity that removes
  flagged queries and donors retains 497 paired queries; analogue MAE changes
  from 0.5816 on those queries in the main run to 0.5555. This is a
  measurement-decision sensitivity, not proof that the concerns are errors.
- TTM-R2 assets and documents are downloaded and verified. The AlphaEarth
  catchment-year export is validated: 72 rows, nine catchments, eight years
  and 64 embedding dimensions.
- Step 1 is implemented: script 68 validates the delivery and native-geometry
  receipt and joins prior-year context. It reproduces 304 complete-input and
  296 complete-outcome events across six Dutch watercourses. Earlier events
  remain in the inventory with an explicit unsupported-period status.
- Step 2 is executed: script 69 builds 570 standardized raw discharge vectors
  and compares R1 with R0 on 534 identical queries from 186 storms. Raw
  peak-ratio MAE is 0.7492 versus 0.6423 for R0; on the 497-query quality
  sensitivity it is 0.6282 versus 0.5555. These are descriptive results;
  storm-aware uncertainty and relevance review remain for step 6.
- The 30-case source-card benchmark and four-arm prompt builder are retained
  as evidence-QA aids only. No LLM answers have been generated or scored, and
  no generator or RAG-arm evaluation is required for this chapter.

## Immediate work

3. Implement frozen TTM-R2 using the identical standardized histories saved
   by script 69; compare R2 with R1 and R0 on the same query/donor pools.
4. Evaluate the bounded AlphaEarth increment on the common 2018+ subset,
   including the catchment-area control.
5. Convert the held German Wurm records into the common event schema.
   Preserve redundant-sensor continuity, curve-validity eras and provisional
   post-July-2021 high-flow status. Report Dutch and German results distinctly
   where input coverage differs.
6. Review retrieved analogues for hydrological relevance and provenance
   failures, and derive only the cross-border evidence recommendations that
   those cases support.

R1--R3 must use the same query frame and donor eligibility as R0. Repeat the
existing measurement-concern sensitivity for paired representation results;
do not choose an arm or exclusion rule from the direction of its result.

The rating-era p99 event definition and normalization are retrospective. The
raw-versus-TTM result tests the frozen representation against raw similarity,
not the causal effect of pretraining. AlphaEarth uses its smaller common
subset and has catchment/catchment-year support, not event-row independence.
Every arm must use the same prior-storm eligibility rule and select no more
than one event from a given storm among its top five analogues.

The 2026-10-11 RAG-centered design and earlier audit remain dated historical
records. Do not add a new model, fine-tuning programme, forecast target,
dashboard, operator study or data source merely because it is available.
