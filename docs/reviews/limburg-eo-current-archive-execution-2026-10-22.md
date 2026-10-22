# Ten-model current-archive comparison — 22 October 2026

Internal execution and interpretation aid; Brian writes the dissertation text.
This pass implements the authorized verification, comparison and actual-analogue
review. It adds no model, event definition, acquisition requirement or tuning.

## Verified inputs

All ten selected extraction/aggregation pairs passed script 117 and were merged
to `results/eo_catchment_representations/selected/census/`. Presto extraction
finished with 399,584 embeddings and zero errors; its aggregation completed at
04:25 UTC on 22 October. Its three output checksums verified. The merge selects
the token-consistent Galileo and OlmoEarth recovery runs explicitly, not the
old controller's default paths. All ten run statuses, source-code compatibility,
output hashes, context counts/ledger and shared catchment geometry were checked.
Legacy extraction receipts without input-ledger hashes retain that limitation;
validation does not retroactively create provenance they never recorded.

The inputs are the held archive, version `held_archive_v1_with_token_repairs`.
Seven Sentinel-2 routes still use their documented independent-band composites.
The mixed-day audit quantified that exposure; no full same-day corrected
embedding census is implied here. Additional Azure observations are separate
and do not change these input hashes or silently enter this comparison.

| Encoder | Monthly snapshot | Twelve months | Four weeks |
| --- | ---: | ---: | ---: |
| Prithvi | 637 | 438 | 211 |
| CROMA | 576 | 437 | 243 |
| TerraMind | 485 | 380 | 281 |
| DOFA | 485 | 380 | 281 |
| Copernicus-FM | 485 | 380 | 281 |
| SatMAE | 485 | 380 | 269 |
| AnySat | 485 | 380 | 270 |
| OlmoEarth | 576 | 437 | 243 |
| Galileo | 485 | 379 | 202 |
| Presto | 485 | 380 | 270 |

These are eligible event-vector counts before chronological donor availability,
country/river restrictions and quality sensitivity. They are coverage findings,
not model-performance results. The 1,062-event inventory is retained; the inherited
Q-only scoring census contains 851 events, rain-matched 770 and preceding-year
AlphaEarth-matched 373 before EO availability. Each model retains its available
population, with additional all-ten matched comparisons. No random sample is used.

## Execution and completion evidence

Script 102 was launched with `--run`. It reuses conventional rainfall/discharge,
raw hydrograph/state and TTM/state controls, EO-only and EO-plus-TTM/state arms,
area/identity controls, matched AlphaEarth subsets, both river scenarios,
pooled/domestic/foreign donor policies, quality sensitivity and five/ten donors.
Donor responses must finish at least 72 hours before the query; the query storm
is excluded. Existing paired storm/year bootstrap intervals use 9,999 draws,
fixed seed 20261013. Actual donor counts are matched; one-cluster cases keep
the difference but no manufactured interval. Retrieval caches are bound to
input contents, index/order, blocks, options and source code.

This note records the launch, not a completed empirical result. Check
`logs/eo-current-archive-workflow-2026-10-22.json` for current step status.
`logs/eo-comparison-2026-10-22.log` holds the comparison log. Published results
exist only after the fresh output directory receives its completed manifest.
Earlier scientific outputs remain separate and are not relabelled.

Script 121 waits on the running comparison's publication lock, rejects an old,
failed or partial result, then runs script 120. It does not launch duplicate
scoring or retry failures silently. On completion, the results are:

- `results/eo_analogue_comparison/`: full assessment/donor tables, retrieval and
  event coverage, paired storm/year intervals, execution plan and hash manifest.
- `results/eo_analogue_review/`: configuration/country/river summaries, full
  equal-count paired event differences against TTM, raw and conventional controls,
  independent donor audit and actual-donor case browser.

The browser includes every scored main/pooled/five-donor case in the available
model and rain-matched cohorts, across both river scenarios and all readouts.
Other donor policies, counts, quality sensitivity and the all-ten intersection
remain in the full tables. Browser selection is not the scientific population.
It plots withheld query/donor responses and reports provider concerns; it does
not rerank donors using those responses. Error-extreme illustrations are labelled
post-outcome selections and cannot establish how commonly a method helps.

## Interpretation to complete after execution

Inspect both average paired differences and event-level changes. Ask whether a
different donor set improves response shape, peak, timing, duration or recession;
one need not imply another. Check actual donor overlap, measurement concerns,
source coverage, short archives and whether apparent gains survive the same
query/donor population. NL–DE contrasts remain entangled with river identity and
archive/measurement differences. No country-causal effect is identified.

These are retrospective Q/own-era-p99 comparisons. Full-era normalization and
pretrained exposure do not establish an as-issued forecast evaluation. A p99
crossing or analogue's subsequent rise does not prove inundation. The study can
show where past events provide useful evidence and where they mislead; operator
benefit and calibrated warning probabilities require separate evaluation.

## Checks

The existing pairing, input and integrity tests passed (46 tests). Eight new
review tests check independent rejection of chronological/storm/country/river
leakage, quality violations and inadmissible responses, and prevent unequal
actual counts or different cohorts being presented as matched model gains.
The complete review writer also passes an isolated engineering fixture covering
all output tables, exact donor joins, the browser payload and manifest hashes.
Full empirical audit/browser checks follow the comparison automatically; do not
substitute these unit tests for the eventual completed run manifest.
