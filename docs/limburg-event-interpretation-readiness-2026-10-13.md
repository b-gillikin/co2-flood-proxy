# Tightened preparation for the event-level pass

Internal research aid; Brian writes dissertation prose. Script 80 prepares the
census, frozen representations and reference measures. It does not rerank
expanded analogues, assign interpretation verdicts, train a model or issue a
warning. Original runs remain intact.

## Completed

- Full inventory: 1,062 held episodes, including incomplete or uncertain ones
  with explicit status. No missing response is represented as an observed
  negative result.
- Q-only inputs: 964 complete, known-onset histories; 58 additional Dutch
  histories now have mean and ordered embeddings from the identical frozen
  TTM checkpoint. All original 906 raw/mean/ordered vectors and state blocks
  match exactly on their existing IDs. No weights or operating points changed.
- Scorable Q-only responses: 851, including 56 additional Dutch episodes.
  These are ready for expanded retrieval; their analogue scores have not yet
  been computed. The old rain/Q and AlphaEarth populations remain separate.
- All scorable queries appear in availability tables, including zero and short
  archives. The 20-event/ten-group condition is only a tag for reproducing the
  fixed-k comparison. Quality-flagged queries remain inventoried and explicitly
  marked outside the quality sensitivity, rather than silently disappearing.
- A history-only persistence reference carries cutoff Q/p99 unchanged across
  response hours 1–72. Its inputs are cutoff discharge and the common
  retrospective p99 normalizer; observed responses only score it. No donor
  information or fitting constructs its estimate. The flat reference has no uniquely estimated peak
  time; timing is left undefined rather than assigned hour one by argmax.
- A group-balanced historical median gives equal mass to each onset-linked
  regional group, and equal mass to events within a group. At an exact half-
  mass boundary it uses the adjacent-value midpoint, matching ordinary median
  behavior when every group is a singleton. The original event-weighted median
  remains alongside it.
- Every one of the original 87,987 scored sets is matched to the same candidate
  counts, groups and original median, with the two references and response-phase
  descriptors joined separately. No old donor identity or error is replaced.
- Per-event context separates cutoff information from observed response
  descriptors. It includes Q level/trends and available rainfall summaries;
  source concerns, country and physical-river identity; first/last-hour response
  maxima, persistence of high water and whether the response exceeds onset Q.
  Response descriptors are verification-only and never rank donors.
- The review CSV contains blank fields for history-only assessment, information
  added by analogues, observed verification and misleading/uncertain cases.
  Existing entries survive reruns. No human judgments have been fabricated.

## Reference check, not a new headline finding

On the existing five-donor Dutch main queries, ordered TTM + state peak error
is 0.6389 versus cutoff persistence 0.6386. In the pooled cross-river main run,
it is 0.6457 versus persistence 0.5812. Current level is already a strong
magnitude reference; similarity to a future maximum alone cannot demonstrate
additional understanding.

The full-curve comparison differs: Dutch TTM mean-curve level RMSE is 0.3522
versus persistence 0.7989; pooled cross-river 0.3652 versus 0.8117. Persistence
assumes no recession, so it is deliberately simple and a weak full-curve
reference. Conventional analogues also improve substantially over it. These
point summaries do not establish a foundation-model advantage, a causal AI
contribution, operational skill, or superiority over every possible use of
one's own history. No new significance claim is made from these preparation
summaries. The practical rain/Q and matched raw controls remain essential.

Group-balanced and event-weighted references both remain reported. The balanced
reference answers a different weighting question; it is not selected because
it makes any method look better. Its values use exactly each query's eligible
prior archive, including cross-river and quality exclusions.

## How the event-level pass will use this

1. Start with facts available in the cutoff history and source record: level,
   recent trend, previous pulses, available rainfall and measurement concerns.
2. Describe what actual prior donors add about the following 72h response,
   including recession, persistence, later rises and disagreement. Compare the
   same query against appropriate references and matched conventional/raw arms.
3. Verify those assertions against the observed response. Keep relative metric
   improvement separate from a useful or misleading event assessment.
4. Count patterns across the eligible census; use individual cases to explain
   them. Short archives and unavailable analogues are coverage findings. Country
   labels do not create extra independent rivers or identify jurisdiction effects.
5. Keep empirical donor disagreement and source uncertainty separate. No new
   calibrated probability, fixed refusal rule or independent human-validation
   claim follows from this preparation.

This remains retrospective: full-era p99, finalized provider records and current
foundation assets are not as-issued historical information. Above-p99 duration
is within the 72h segment, not full flood duration or historical warning duration.
No new provider request, hydrological solver, fine-tuning or RAG task is needed.

## Files and reproducibility

Run using the pinned foundation environment:

```sh
MPLCONFIGDIR=/tmp/limburg-mpl \
PROJ_DATA=/Users/briangillikin/miniforge3/envs/chapter1-co2/share/proj \
.venv-foundation/bin/python scripts/80_prepare_event_interpretation.py
```

Ignored output directory: `results/basin_ai_event_interpretation_ready/`.

| File | Purpose |
|---|---|
| `event_inventory.csv` | All held episodes, cutoff facts, source flags, response status and verification descriptors |
| `q_only_signatures.csv` | Broader Q-only eligibility; no rainfall imputation |
| `q_only_standardized_histories.parquet`, `q_only_ttm_mean.parquet`, `q_only_ttm_ordered.parquet`, `q_only_discharge_state.parquet` | Input-ready representations for expanded retrieval |
| `archive_and_reference_inventory.csv` | All scorable queries and availability, persistence and both median references |
| `existing_results_with_explicit_references.csv` | Original scored sets with aligned references and phase descriptors |
| `reference_summary.csv` | Descriptive aligned reference checks; no newly fitted model or significance claim |
| `event_interpretation_review.csv` | Blank, editable research-aid fields; entries preserved |
| `extra_vector_receipt.json`, `manifest.json` | Frozen-checkpoint/runtime information and input/output fingerprints |

The two extraction receipts record evaluation mode, zero trainable parameters
and the same source/checkpoint hashes. Original output fingerprints are carried
forward and verified. Review fields are excluded from immutable output hashes
so Brian can edit them without invalidating the scientific tables.

Validation: 124 tests pass. All twelve new scientific CSV/Parquet artifacts
reproduce exactly in a separate output directory using the verified extraction
cache. All original 906 raw/mean/ordered representations and state blocks
match exactly; all fifteen old result fingerprints remain unchanged. The new
frozen extractions have zero trainable parameters and evaluation mode enabled.
A test-copy review note survives rerunning preparation; real review fields
remain blank. Every scorable response has a positive maximum, so the existing
peak-scaled shape definition is available for the expanded pass. Repository
lint, changed-Python formatting and whitespace checks pass.
