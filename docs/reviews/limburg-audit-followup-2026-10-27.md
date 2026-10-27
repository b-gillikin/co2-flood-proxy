# Audit follow-up — 27 October 2026

Brian authorized the recommended next pass. This is a versioned downstream
analysis using held inputs, not a new RQ, provider request or encoder extraction.
Original scoring, reviews, source files and manifests remain unchanged.

## Implemented work

1. **Correct review provenance.** Script 135 regenerates the main and four
   supplemental reviews under `results/eo_review_provenance_v2/`. Notes derive
   from each selected input contract rather than claiming Azure data are absent
   or three models were reused. The controller checks that all non-HTML numerical
   review artifacts are byte-identical or exactly equivalent parquet values.
2. **Use actual rainfall-predictor requirements.** Script 136 replays only the
   rainfall-matched comparisons, retaining all other method/settings and Q/target
   eligibility. The predictor maximum is 168 h, not an inherited 512 h rainfall
   history. Planning confirmed **836** eligible cases versus the original **770**
   among 851 Q-eligible events. Outputs are separate in
   `results/eo_analogue_comparison_rain168_v1/`. These are feature-eligible counts,
   not claims that all 836 have an EO representation or a valid prior archive.
3. **Direct supplemental-route contrasts.** Script 137 forms the intersection
   of eligible main/supplemental event representations for each route/readout,
   then uses this same population as both the query universe and candidate archive.
   Both representations, raw/TTM/state controls and the corrected conventional
   benchmark are retrieved on the shared archive. Same query IDs, candidate rules,
   actual donor counts, river/country/quality restrictions and complete prior
   responses are checked. This goes beyond pairing cases with different archives.
4. **Restore the generic historical reference.** Each original main/supplemental
   EO population and corrected rainfall population receives the unranked eligible
   archive reference. Storms receive equal mass; events within a storm share its
   mass. Candidate-event/storm counts must equal those recorded by retrieval.
   Individual shape/timing similarity and aggregate peak/curve/duration/recovery
   estimates remain distinct. No withheld response selects the archive or ranks.

## Evaluation and computational scope

All eligible cases are retained, with the existing three temporal readouts,
all/other-river scenarios, pooled/domestic/foreign archives, main/quality
sensitivity and k=5/10. Empty common-support cases are explicit, not manufactured
estimates. The generic archive is not constrained to k events; its role is the
whole eligible historical reference, not another equal-k retrieval method.

Paired query-storm and query-year intervals retain 9,999 draws and seed 20261013.
A chunked multi-metric implementation shares the established random draws; a
regression check verifies equivalence with the existing scalar estimator. This
reduces repeated work without changing the estimator or resampling unit. Small
cluster cases keep point estimates with undefined intervals. No multiplicity-
selected winner or operational probability calibration is claimed.

The review correction and rainfall replay run on two CPU workers. They finish
before the common-route/archive analysis starts, avoiding concurrent scoring-cache
writers. No GPU is needed. The controller records progress under
`logs/eo-followup-2026-10-27/progress.json` and checks the 60 GiB working reserve
before new phases. Authorized cleanup remains Limburg-only. All source/encoder
files used by the completed runs stay frozen. New entry points explicitly record
their own identities and the numerical dependency chain.

## Outputs

- Corrected review pages: `results/eo_review_provenance_v2/{main,variant}/`.
- Rainfall benchmark: `results/eo_analogue_comparison_rain168_v1/`, with its own
  input/output manifest and an updated review.
- `results/eo_followup_2026_10_27/common_route_assessments.parquet`, paired
  differences, storm/year intervals and explicit support table.
- Same directory: generic-reference case tables, summary and interval artifacts.
- `results-memo.md`: a fixed-view internal readout linking full support and
  uncertainty artifacts. Numerical means are not automatically human relevance
  findings or independent validation.

Original completed outputs remain the baseline; new populations and source-route
contrasts must be labelled separately. The follow-up does not by itself isolate
pretraining's value from raw EO information, prove wetness anomalies, establish
country causality or supply a calibrated abstention rule. Those limitations in
the audit remain explicit. Brian writes dissertation/article prose.

## Checks at launch

- Full suite: **326 passed**, including seven follow-up tests covering the
  multi-metric/scalar bootstrap equivalence and review-page regeneration.
  Verification log: `logs/eo-followup-tests-2026-10-27.log`.
- Real-input engineering check: orbit-15 snapshot intersection contained 16
  eligible events and 14 queries with donors; main/supplemental retrieval shared
  query IDs, and generic candidate universes matched recorded counts exactly.
- Rainfall planning verified 851 Q-eligible / 770 original rain / 836 actual-
  predictor-complete cases. No empirical follow-up improvement is claimed at launch.
