# Regional features and first complete regional-fold benchmark

16 November 2026. Internal research/execution record; Brian writes dissertation
prose. Feature assembly and its audit are complete. The first full regional fold
is running; this is not the full multi-year study or a final research finding.

## Completed preparation

The common table has **1,151,268 rows across 394 gauges**: seven local gauges and
387 resolved regional records, for 2018–2025. It contains **168 predictors** under
the existing H/H+A/H+E/H+A+E definitions and occupies approximately **862 MiB**.
Assembly took **23.9 seconds** on this machine, using compact acquired tables.

The new recipe was rebuilt independently from the held local raw inputs and
compared against **every predictor at every day of all seven local gauges**.
The largest absolute difference was 7.82×10⁻¹⁴. The actual-data audit also checks
specific-discharge conversion, complete daily calendars, past-only climate at
every regional gauge/year, grouped folds and target exclusion. All predictor
cells are present; missing verification observations and unknown QA remain
explicit. Earlier-year histories legitimately supply January lags.

Observed Q is used as the outcome/eligibility check, never as a predictor.
Current and lagged modelled Q remain predictors. Weather units, derived humidity/
wind speed, mapping descriptors, conventional controls and fixed 2017 AlphaEarth
means use the same local/regional recipe. The surface field-capacity variable
remains a proxy and missing regulation information remains unknown.

Preparation outputs: `results/limburg_dise_regional_benchmark_v1/preparation/`.
The feature manifest pins source/code hashes; `audit.json` records actual-data
checks; `support.csv` and `test_coverage.csv` record coverage. Fixed row eligibility
and sample weights for outer/inner/final fits are saved separately with a receipt
and the executed reconstruction procedure.

## First outer fold and information boundaries

- Train: **2018–2019**, 233,001 eligible gauge-days across 328 contributing gauges.
- Validate/tune: **2020**, 115,829 gauge-days across 321 contributing gauges.
- Test: **2021**, all eligible Wurm and reserved external records: **17,637
  gauge-days across 51 gauges**. All three Wurm gauges remain withheld together.
- The requested test census is 53 gauges. `DEA10140` and `DEA12200` have no 2021
  verification values; their absence remains in coverage accounting. They are
  not a performance-selected rejection or fabricated as zero-flow observations.
- Every Ahr/Erft/Sieg external record is excluded from all training and tuning.
  Regionally connected sections remain grouped. The 152 potential regional
  donor section groups plus four local groups are deterministically assigned
  to four inner folds without reading discharge magnitudes. Some groups lack
  eligible validation labels; contributing group counts are explicit.

The four inner folds contain respectively 38, 36, 38 and 37 contributing
validation groups. Model selection aggregates fold MSE proportionally to these
counts, preserving equal group weighting rather than treating differently sized
folds as equal observations. Gauge/day weighting within groups is unchanged.

No high-water/event sample is selected. The geometry views are evaluation
populations in this first benchmark: full external support, overlap/location
strata, high-overlap and location-consistent sensitivities. They do not secretly
change training support between feature arms. Local and external results are
reported separately, with per-site support and error records.

## Fits, runtime and resumption

Configuration: `config/limburg_dise_regional_benchmark_v1.json`.
Commands use the pinned `.venv-dise` environment:

```sh
.venv-dise/bin/python scripts/271_prepare_dise_regional_features.py
.venv-dise/bin/python scripts/273_audit_dise_regional_preparation.py
.venv-dise/bin/python scripts/272_benchmark_dise_regional_fold.py run
```

The first complete benchmark has **152 fits**: two declared selection policies,
four feature arms, four candidates across four inner folds, and three final
seeds per arm/policy. Primary early stopping/selection uses reconstructed-flow
RMSE; the article-faithful log-stopping/MAE sensitivity remains separate. All
arms share training rows, weights, candidate budget and seed definitions.

One fitting worker uses **two CPU threads**, without a GPU or cloud compute.
The first real tuning model required **20.7 seconds**. Its post-fit progress
recording failed because the policy field was supplied twice. That model,
records and exact executed runner are preserved in
`benchmark_wurm_external_2021.initial-bookkeeping-failure`; the issue was fixed
before the complete benchmark started. The current benchmark has its own fresh
identity, checkpoints and complete 152-fit count. The old local benchmarks are
untouched. This technical attempt is not evidence for an encoder effect.

Early successful fits in the corrected run take roughly 20–22 seconds each;
other candidates/tree depths may differ. A provisional 1–2-hour planning window
is more useful than the old local 32-second figure, but the progress receipt is
the timing authority. Every fitted model/prediction checkpoint has an input/code/
runtime identity and checksum; matching checkpoints can be reused after a stop.

The early low-learning-rate candidates reach the configured 1,500-tree cap.
Actual fitted rounds and cap status are recorded; they must not be presented as
proof of unconstrained convergence. Review selected configurations and capacity
before scaling to the full study. The cap/grid is not altered during the run to
favour a representation. No positive-result gate is introduced.

## Outputs and interpretation

Directory: `results/limburg_dise_regional_benchmark_v1/benchmark_wurm_external_2021/`.
`progress.json` reports completed fits, active fit, elapsed time, peak memory and
free disk. The managed execution session is recorded in `run_context.json`.
Final assembly/calibration/scoring is automatic after fitting.

Planned output includes all final seed models, predictions in mm/day and m³/s,
raw GEOGLOWS, donor-FDC transfer, and an extra-label historical local FDC
reference for Wurm. Donor-FDC uses the same finite past donor labels allowed to
the learner; unknown provider QA is not silently upgraded to clean. External
local calibration is not introduced. The extra-label local reference is labelled
as a different information budget.

Daily p99 thresholds use the held targets' past observations for evaluation
only. Missing thresholds remain unknown; unknown QA remains unknown. Main
metrics and the known-clean sensitivity use explicitly declared populations.
The one-year benchmark cannot provide a between-year confidence interval:
999 nominal resamples do not create independent years or floods. Undefined
intervals are saved as undefined. Day-level helped/harmed examples are selected
symmetrically and are not counted as independent storms.

**51 tests pass**, including label-independent feature generation, year-boundary
lags, topology withholding, unknown-threshold/QA scoring and external donor
calibration that is invariant to target-observation changes. Ruff passes.

No additional input download, other-chapter change, full multi-year queue or
operational-warning claim is part of this execution. After completion, review
runtime, capacity/coverage, calibration behaviour and provisional paired results
before planning the full chronological comparison.
