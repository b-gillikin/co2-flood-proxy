# Completed EO representations: coverage and comparison review

Internal research-aid note, not dissertation prose. Scope: audit the eight
completed models and the fairness of their planned comparisons. No model scoring,
new research question, new data request or changed eligibility threshold.

## Audit result

All eight selected aggregates passed: output checksums, extraction-source code
fingerprints, completed census status, absence of recorded extraction/aggregation
errors, finite nonzero vectors, unique context/catchment keys, representation–
coverage agreement, full-catchment coverage bounds and expected calendar slots.
The corrected OlmoEarth aggregate is selected explicitly; its earlier aggregate
is not used. Galileo and Presto remain pending in this dated audit.

All 36,304 source jobs have acquisition times within their declared windows.
Across 163,715 observation/raw-pixel links, no latest observed pixel reaches or
exceeds its assessment cutoff and no window ends after that cutoff. Raw-pixel
latest dates bound the retained encoder pixels conservatively; they are not a
new measurement of model-specific acquisition ages. This establishes input-date
consistency, not prospective publication availability or freedom from pretrained
model exposure to later imagery. Existing retrospective limitations remain.

This pass rechecks aggregate files, run manifests and code fingerprints. The
held extraction, aggregation and full-pixel audit already verified imagery and
patch receipts; this pass does not independently reread millions of those files.
The audit manifest says this explicitly.

## Available events

Counts below are out of the same 851 existing Q-only baseline-eligible high-water
events. All 1,062 candidate high-water events and the separate 3,744 rainfall-
episode gauge rows remain in the coverage ledger. Unavailable is not nonresponse.

| Model | Completed-month snapshot | Twelve monthly frames | Four weekly frames |
| --- | ---: | ---: | ---: |
| Prithvi | 637 | 438 | 211 |
| CROMA | 576 | 437 | 243 |
| TerraMind | 485 | 380 | 281 |
| DOFA | 485 | 380 | 281 |
| Copernicus-FM | 485 | 380 | 281 |
| SatMAE | 485 | 380 | 269 |
| AnySat | 485 | 380 | 270 |
| OlmoEarth, corrected | 576 | 437 | 243 |
| Same events across these eight | 479 | 357 | 115 |

This eight-model intersection is a diagnostic, not the final all-ten cohort.
No model is dropped from the required set merely because it is still running.

Coverage is not binary image availability. Median mean observed catchment area
for available recent high-water contexts is approximately 100% for radar CROMA/
OlmoEarth, 39% for Prithvi, 29% for TerraMind/DOFA/Copernicus-FM, 21% for SatMAE
and 18% for AnySat. These are fractions of the full catchment, without an added
area cutoff. Equal event counts do not imply equal spatial information.

The baseline has 614 NL and 237 DE events. Model/readout availability is uneven
by country, river and period; the machine-readable summary keeps these strata.
Sensor start dates, acquisition and masking differ. Identical availability for
some models reflects shared routes; it does not prove identical vectors.

## Comparison choices

1. Retain each model's entire available population. Compare it with conventional
   and existing AI controls on exactly those queries and the same eligible donor
   archive. Never compare average errors calculated on different populations as
   if they measured model superiority.
2. For a direct model-versus-model claim, use that pair's event intersection and
   the same donor population. Retain the all-ten intersection as a supplementary
   comparison after all ten finish. Do not let it exclude broader valid pairwise
   work. The current script 102 implements per-model and all-ten populations;
   direct pairwise scoring is not implemented merely by this coverage audit.
3. Keep snapshot, monthly and weekly readouts distinct. Their intersections,
   archive size and dates differ. Same-query/readout comparisons are needed for
   a temporal-benefit claim. An earlier calendar image is context, not an hourly
   observation of the storm or river state.
4. Retain current completed 72-hour donor outcomes, different storms, one chosen
   donor per storm, pooled/domestic/foreign archives, all-/other-river analyses,
   measurement-quality sensitivity and five/ten target donors. Compare paired
   scores at equal actual donor counts. Keep short archives visible; five/ten
   storm support counts are diagnostics, not new exclusions.
5. Keep country, physical river, year, observed area and common-across-frame area
   alongside results. Patch footprints/modalities and temporal pooling differ;
   area weighting does not make vectors pure catchment-pixel measurements. A
   common-event win would not isolate architecture from sensor or support effects.
6. Use the existing rainfall-matched population to test whether EO improves on
   the strong conventional comparator, and area/gauge-identity controls to test
   geographic specificity. Script 102 currently computes paired uncertainty only
   against TTM/state. Before claiming improvement over rainfall/discharge, add
   the direct paired conventional-reference contrast in the later analysis pass.
   This review does not implement or execute that scoring change. AlphaEarth
   keeps its separate matched subset; it is not an entry requirement for EO.
7. Treat the many model/readout comparisons as comparative retrospective evidence,
   not independent confirmatory discoveries. Show all results and group/year
   uncertainty, avoid selecting a winner from a favorable slice, and distinguish
   available-population coverage from incremental skill.

## Donor archive implications

Before ranking, the eight-completed common populations have the following pooled,
all-river support (main measurement policy):

| Readout | Eligible queries | No prior eligible storm | At least five prior storms | At least ten |
| --- | ---: | ---: | ---: | ---: |
| Snapshot | 479 | 1 | 465 | 438 |
| Monthly | 357 | 6 | 343 | 335 |
| Weekly | 115 | 1 | 102 | 89 |

Restrictions can reduce support sharply. For example, in the weekly common
population, the domestic other-river archive has no prior eligible storm for
41 of 115 queries; 50 have ten or more. This is not evidence of poor model
performance. It limits what that particular archive comparison can answer.
The audit records all 324 population/readout/river/country/quality configurations.

## Reproduction and outputs

Run from the chapter root:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venvs-eo/terramind/bin/python scripts/112_audit_completed_eo_comparability.py
.venv-foundation/bin/python -m pytest tests/test_eo_coverage_review.py tests/test_eo_token_masks.py tests/test_eo_census_runner.py -q
```

Outputs are local under `results/eo_completed_coverage_review/`: `audit.json`,
115,344 observation/model/readout coverage rows, stratified coverage, event
membership, pairwise intersection sizes, donor-support counts and calendar age
summaries. Hashes identify inputs and outputs. A compact dated receipt is saved
alongside this note. The raw-provider records and large research artifacts remain
outside Git.

The donor-support matrix independently reproduced all counts from an initial
loop implementation, exactly, on the real populations. Four new tests cover
missing-model intersections, retained per-model populations, chronological/
storm/country/river exclusions and partial/impossible coverage. The focused
12-test suite passes; lint and whitespace checks pass. Active extraction source
files and worker settings are unchanged. No performance finding is created.
