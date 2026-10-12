# Limburg representation feasibility: first implementation status

**Status:** internal analysis note, 2026-10-11. These are pipeline diagnostics,
not dissertation results or operational forecast claims.

## Event library

`scripts/64_build_basin_ai_event_library.py` transforms the reviewed Dutch
events into fixed hourly windows. Each event contains 168 hours of history
through its onset and 72 later hours marked as withheld outcomes. The run
contains:

- 724 events and 174,484 event-hour rows;
- 721 events previously marked usable for the primary retrospective analysis;
- 58 events with a retained measurement concern;
- 694 complete discharge histories, 711 complete rainfall histories and 724
  complete weather histories; and
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

Of 724 events, 708 have complete signatures and 687 have at least 20 prior
candidate events. With five nearest historical events:

- analogue mean absolute error for the subsequent 72-hour peak/p99 ratio:
  **0.701**; and
- expanding historical-median mean absolute error: **0.697**.

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

The Earth Engine Python package is not installed in the current project
environment and no authenticated project was detected in this pass. No data
download has been started. German catchment polygons will be needed before an
AlphaEarth comparison can itself be called cross-border.

## Next decision sequence

1. **Prepared:** authenticated AlphaEarth aggregation for the Dutch catchments
   and Herzogenrath 1/Randerath; event year `Y` uses the prior-year embedding.
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
