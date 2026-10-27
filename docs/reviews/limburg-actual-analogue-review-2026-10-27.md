# Actual analogue selections — 27 October 2026

Internal interpretation aid for Brian. These are **post-hoc illustrations**, not
a validation sample, a model ranking, or evidence of how often a pattern occurs.
The complete-census estimates and uncertainty remain in the comparison outputs.
The corrected-rainfall and whole-archive follow-up was still running when these
examples were examined; no conclusion about those unfinished comparisons follows.

## What was inspected

Script `139_review_actual_analogue_cases.py` reads the corrected main-run case
index and renders six query/TTM-versus-EO pairs, including the individual donor
curves and their mean. All use main/pooled/other-river retrieval, requested k=5,
with actual donor counts checked equal within each pair. Each pair uses its own
model-available cohort; **different rows do not share a common population**.
All four displayed errors were independently recomputed from the stored donor
IDs and held response curves for all 12 rows and matched stored scores.

Outputs: `results/eo_actual_case_review_2026_10_27/`, containing the contact sheet,
case scores, complete donor identities/provider flags and a hashed manifest.
The contact sheet was visually inspected. It shows the full 72-hour response,
not just peak-normalized shapes. The horizontal p99 line denotes a statistical
discharge reference, not flood stage. Ratios are not comparable absolute flows.

## What these cases show

| Query and representation | Actual donors | What the curves and scores show |
|---|---:|---|
| Herzogenrath 1, 23 Sep 2018; CROMA monthly | 5 | A rapidly receding response. Adding EO changes two of five donor IDs and follows the recession more closely: curve RMSE 0.230 → 0.089 and duration error 4.0 → 1.4 h. A useful individual match; not a general CROMA advantage. |
| Randerath, 14 Mar 2019; TerraMind monthly | 5 | The query has a later, larger rise, with its maximum around hour 45. Both donor sets mostly recede and miss that rise. EO replaces all five donors but worsens curve RMSE 0.836 → 1.072; peak-timing error remains 43.2 h. A changed selection is not necessarily new useful information. |
| Gulp, 30 Sep 2017; AnySat recent | 2 | Both methods return exactly the same two donors and identical errors. A visually good match supplies no incremental evidence for AnySat here. The future response is already below p99; the onset crossing need not persist into the subsequent scoring window. |
| Voer, 17 May 2024; Prithvi monthly | 5 | The recorded response is much larger and more prolonged than either donor set. Peak-normalized shape error improves 0.327 → 0.287 while curve RMSE worsens 1.672 → 1.933 and duration error worsens 50.2 → 60.6 h. Shape similarity must not be described as accurate severity/duration estimation. Provider status is `pending_range_check`; the binary measurement-concern flag is false. |
| Geul, 3 Jan 2015; OlmoEarth snapshot | 2 | Shape error improves 0.053 → 0.039 but curve RMSE worsens 0.096 → 0.170. The changed donor overshoots the query's early peak. Sparse support and the provider-status label (`exclude_out_of_range`) must stay visible; that label is not synonymous with the response-specific binary concern flag. |
| Eyserbeek, 29 Oct 2017; OlmoEarth monthly | 5 | EO's donor mean follows a short recession more closely: curve RMSE 0.159 → 0.059. This query has a recorded measurement concern. It is illustrative of the retained main analysis, not a clean-data validation success; the existing quality sensitivity is the proper comparison. |

## Implications for the pending interpretation

- Check whether an apparent improvement changes the donor set, or simply leaves
  the same small archive in place. Requested k is not actual k.
- Keep individual shape agreement separate from scale, duration and aggregate
  trajectory errors. Neither metric can stand in for the other.
- Inspect delayed/multiple rises and unusually prolonged responses as failures,
  as well as attractive short-recession matches. These examples do not establish
  their cause or how prevalent the failure is.
- Preserve source-specific provider status alongside the response-specific
  measurement flag. Neither a favourable-looking curve nor a false binary flag
  resolves every provider qualification.
- Use the queued common-archive and generic-reference results, with paired
  storm/year uncertainty, before concluding that targeted retrieval adds value.
  The examples explain mechanisms of matching/failure; they do not establish
  operational forecasting skill or a calibrated rule for withholding an answer.

No fitting, reranking, encoder extraction, changed eligibility rule, new data
requirement or dissertation prose was introduced by this review.
