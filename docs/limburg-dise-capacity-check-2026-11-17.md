# DISE capacity check — Step 1 completed

17 November 2026. Internal research aid; Brian writes dissertation prose.
The [four-step plan](limburg-dise-four-step-plan-2026-11-17.md) is saved;
**Step 1 is complete and Steps 2–4 remain pending**.

## What changed

Every arm and selection policy had the same 3,000-tree maximum, replacing the
original 1,500-tree maximum. The four candidates, four inner folds, three final
seeds, predictor definitions, training/validation/test populations, weights,
scoring conventions and raw/FDC references stayed fixed. Selection used only
validation data. This is a capacity sensitivity on the existing 2021 fold,
not an independent replication or another research question.

The fixed early-stopped control reproduced its original stopping iteration,
boosting rounds and validation predictions exactly. All 26 originally capped
tuning jobs were refit from scratch. Including the control, 27 tuning fits were
new; 101 verified early stops were reused. Four ensemble specifications changed,
requiring 12 new final seed fits; the other 12 final models were verified/reused.
The original benchmark and its manifest remain unchanged.

| Policy / feature arm | Selected candidate, old → new | Final trees, old → new |
| --- | ---: | ---: |
| Primary H+A+E | 3 → 2 | 502 → 1,168 |
| Primary H | 2 → 2 | 755 → 755 |
| Primary H+A | 3 → 3 | 475 → 475 |
| Primary H+E | 2 → 2 | 1,312 → 1,498 |
| Article-faithful H+A+E | 2 → 2 | 1,404 → 1,486 |
| Article-faithful H | 2 → 2 | 506 → 506 |
| Article-faithful H+A | 2 → 2 | 1,327 → 1,417 |
| Article-faithful H+E | 2 → 2 | 829 → 829 |

Candidate indices are zero-based. H is model/weather history, A conventional
catchment descriptors, and E AlphaEarth. The primary policy selects reconstructed
specific-discharge RMSE; article-faithful stopping/selection remains a sensitivity.

Cap hits fell from **26/128 to 3/128**. All three remaining hits are unselected
article-faithful candidates. None of the 32 selected candidate/fold fits is capped.
This does not prove an unlimited-cap optimum; the pre-agreed 3,000-tree comparison
is complete, and no further escalation was launched.

## Effect on the existing 2021 results

Primary H+A+E versus H+A, with identical test populations. Positive percentages
mean lower error after adding AlphaEarth. Specific discharge is in mm/day;
metrics average within gauge, then river group, then across groups.

| Population / outcome | MAE reduction, 1,500-tree budget | MAE reduction, 3,000-tree budget |
| --- | ---: | ---: |
| Wurm, all days | 23.15% | 21.33% |
| Wurm, high water | 1.57% | −2.45% |
| Wurm, strict-clean high water | −0.78% | −9.67% |
| External rivers, all days | 2.90% | 2.32% |
| External rivers, high water | 1.71% | 1.66% |

The all-day MAE reduction persists, although it is smaller. The Wurm high-water
MAE comparison changes sign. RMSE gives a distinct view: the expanded primary
model improves Wurm all-day/high-water RMSE versus H+A by 5.92%/2.55%, but worsens
strict-clean high-water RMSE by 3.87%. External all-day RMSE is effectively
unchanged (0.007% worse), while high-water RMSE improves by 0.40%.

Against raw GEOGLOWS, the expanded H+A+E model still worsens full-subset high-water
RMSE by 16.0% on Wurm and 10.0% externally. These statements concern the full
high-water subset; measurement-qualified subsets have different results.
External all-day AlphaEarth gains remain uneven: Erft improves by 18.34%, while
Ahr and Sieg worsen by 3.00% and 1.53%. The pooled external MAE gain is not a
gain on every river.

This supports carrying the all-day reconstruction result into the agreed
multiyear test. It does not establish dependable flood-extreme improvement,
forecast skill or operational warning value. The test remains one 2021 year:
17,637 eligible gauge-days from 51 gauges, with 21 Wurm high-water gauge-days
on nine calendar dates and 274 external high-water gauge-days on 35 dates.
The Wurm strict-clean subset has 14 gauge-days on six dates. These are not
independent flood counts; no between-year confidence interval is available.

## Verification, runtime and records

- Completed in **22.1 minutes**, one fitting worker/two CPU threads; peak process
  memory 5.88 GiB. Free disk was 81.36 GiB at completion. No GPU/cloud job,
  new acquisition, offload or other-chapter cleanup was needed.
- Fifty-four relevant tests and Ruff passed before launch. All original and new
  output hashes, pinned inputs/code, fixed metadata/reference predictions,
  eight validation selections and all eight three-seed ensembles reverify.
- The existing independent reviewer reproduced 85 metric records from the new
  predictions. Reused tuning-model hashes match the original models exactly.
- [Verification receipt](reviews/limburg-dise-capacity-verification-2026-11-17.json).
  Execution code was committed as `5a45dd1`.

Results: `results/limburg_dise_capacity_v1/` contains the manifest, per-fit
receipts/models, tuning/selection tables, predictions, 303 metric records,
`budget_comparison.csv`, `primary_budget_comparison.csv` and `capacity_summary.json`.
Read-only review artifacts are under `results/limburg_dise_capacity_review_v1/`.
Original results remain under
`results/limburg_dise_regional_benchmark_v1/benchmark_wurm_external_2021/`.

From the chapter directory, `.venv-dise/bin/python scripts/275_run_dise_capacity_check.py`
now verifies completed outputs and exits without refitting. The read-only review
uses `scripts/274_review_dise_regional_benchmark.py` with `SOURCE` set to the
capacity-results directory and `OUT` to the capacity-review directory.

Next saved step: the agreed multiyear/river-group tests. **Not launched.**
