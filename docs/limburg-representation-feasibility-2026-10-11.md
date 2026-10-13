# Limburg representation feasibility: first implementation status

**Status:** internal analysis note, 2026-10-11. These are pipeline diagnostics,
not dissertation results or operational forecast claims.

**Update, 2026-10-13:** The initial baseline numbers below used up to five
events, which could include several gauges from the same regional storm. The
current baseline selects at most one event per prior storm and requires its
72-hour outcome to end by the query onset. On the same 534 queries, the
top-five analogue peak-ratio MAE is **0.6423** and the expanding historical
median MAE is **0.6424**: effectively a tie. The original figures below are
retained as dated diagnostics, not the active result. The masked-observation
and generative steps in the old sequence below were retired with the RAG
experiment. See `limburg-historical-analogue-active-design-2026-10-13.md`.

**Steps 1--2 completed, 2026-10-13:** Script 68 has joined the prior-year
AlphaEarth context, reproducing 304 complete-input and 296 complete-outcome
events. Script 69 has executed raw 512-hour R1 on the same 534 R0 queries;
R1's peak-ratio MAE is 0.7492, versus 0.6423 for R0. The quality-sensitivity
comparison uses 497 identical queries and gives 0.6282 versus 0.5555. TTM,
the AlphaEarth-effect comparison, German conversion and uncertainty remain
the next work in the current handoff.

## Event library

`scripts/64_build_basin_ai_event_library.py` transforms the reviewed Dutch
events into fixed hourly windows. Each event contains 512 hours of history
through its onset and 72 later hours marked as withheld outcomes. The run
contains:

- 724 events and 422,816 event-hour rows after enforcing exactly 512
  assessment observations plus 72 withheld outcome hours;
- 721 events previously marked usable for the primary retrospective analysis;
- 58 events with a retained measurement concern;
- 629 complete discharge histories, 655 complete rainfall histories and 724
  complete weather histories;
- 570 primary-usable events complete across all three histories and 558 of
  those with all 72 withheld discharge hours; and
- SHA-256 hashes for all four input files.

The current event library covers Eyserbeek, Geul, Gulp, Voer, Worm and
Geleenbeek. It does not yet convert the LANUK records into German event
objects. That extension needs an explicit compatible event definition and
verified topology; it should not be achieved by relabelling all four German
packages as Wurm observations.

## Interpretable analogue baseline

`scripts/65_hydrological_analogue_baseline.py` describes each event using only
information available by its onset: trailing rainfall totals and intensity,
discharge relative to the event's rating-era p99 threshold, and six- and
24-hour discharge changes. A candidate analogue must occur strictly earlier
and belong to another storm.

The fixed representation-input frame contains 570 events. Outcome scoring uses
the 558 with complete withheld response windows; 534 have at least 20 prior
candidate events. With five nearest historical events:

- analogue mean absolute error for the subsequent 72-hour peak/p99 ratio:
  **0.658**; and
- expanding historical-median mean absolute error: **0.642**.

The simple analogue representation therefore did not beat the historical
median on this initial diagnostic. This does not establish that analogue
retrieval is useless: the metric is preliminary, the input starts at a known
p99 crossing, and the comparison does not yet use catchment context, topology
or learned representations. It does establish a real baseline that AlphaEarth
or a time-series foundation model must improve upon.

## AlphaEarth feasibility boundary

The official Earth Engine collection is
`GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL`: annual 64-band embeddings from 2017
onward, sampled at 10 m for downstream classification, regression, change and
similarity tasks. The repository already holds seven Dutch catchment polygons,
so a bounded first test can aggregate the 64 dimensions by catchment and year,
then ask whether they improve donor-catchment or event retrieval beyond area
and conventional hydrological signatures.

The authenticated export has completed. The validated local table contains 72
rows: nine catchments by eight annual layers, 64 embedding dimensions, no
missing values and stable geometry hashes. It includes the delivered
Herzogenrath 1 and Randerath Wurm catchments. Event linkage still needs a
deterministic prior-year join before the representation can be evaluated. The
prior-year rule limits the fair AlphaEarth comparison to events from 2018
onward; it is not a 570-event arm. In the corrected Dutch library that subset
contains 304 complete-input events and 296 complete-outcome events across six
watercourses. Those event counts do not turn six watercourses or their
catchment-year embeddings into hundreds of independent catchment observations.

## Next decision sequence

1. **Completed and validated 2026-10-12:** AlphaEarth aggregation for the seven
   Dutch catchments and Herzogenrath 1/Randerath. The delivery contains the
   complete 9-catchment by 8-year grid (72 rows), 64 embedding dimensions, no
   missing values and stable geometry hashes. Event year `Y` uses the prior-year
   embedding.
2. Test whether those embeddings add retrieval signal; do not infer physical
   meaning from individual embedding axes.
3. **Fixed:** TTM-R2 `512-96-r2`, frozen last-layer patch-mean representation,
   tested against conventional signatures and a raw 512-hour hydrograph
   baseline on the same 570 complete events.
4. Define the German event/catchment extension and masked-observation task.
5. Return to generative synthesis only after at least one event-retrieval
   method has a defensible evaluation.

The model justification, 512-hour completeness audit and download commands are
in `docs/limburg-foundation-download-readiness-2026-10-11.md`.
