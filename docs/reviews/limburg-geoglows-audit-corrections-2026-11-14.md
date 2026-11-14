# Resolution of the six GEOGLOWS setup audit findings

14 November 2026. Implements Brian's requested corrections. The
[original audit](limburg-geoglows-code-design-audit-2026-11-14.md) and the v1
configuration, acquisition and setup outputs remain preserved. The active study
is [v2](../../config/limburg_geoglows_stages12_v2.json), with a
[corrected protocol](../limburg-geoglows-stages12-protocol-v2-2026-11-14.md).

| Finding | Implemented correction | Evidence |
| --- | --- | --- |
| Eys/network confounding | Drop Eys as target and predictor in both stages. Explicit seven-target indices; mask its legacy query/donor/quality/normalization slots. Nine active feeds, including the two Meuse sites. Active-network coverage excludes the unused padding slot. | Full input audit and perturbation regression: arbitrary original Eys values cannot affect predictors; 13,468 opportunities per stage, 481 regional episodes |
| Different training populations/fallbacks | Hydrology, raw and encoder arms train and validate on identical historical opportunities. Missing features use train-only treatment. Raw may retain the exact causal hydrology policy and returns it when raw EO is unavailable; encoder returns the selected raw policy when unsupported. Zero encoder influence is exact raw, not a separate EO-free retuning search. | Regression verifies equal training-row/validation-year records, exact fallbacks and invariance of earlier predictions to future-label perturbation; scorer also asserts matching at runtime |
| Bootstrap changing sites | New study explicitly requests fixed-population summaries. Define the site population within each verification-eligible stratum before prediction filtering. Missing any site makes a draw undefined; report partial-site and total undefined draws. | Two-site reproduction now counts partially missing draws as undefined; coverage-only checks on the real seven-target census. Legacy summary defaults and existing scientific output files are retained |
| Missing joint/strong-control summaries | Explicit high-water primary summary, full-census and joint mapped/high-water/EO-supported summaries, the existing conventional median reference, and joint-stratum source-by-encoder interactions. | Regression checks exact joint-stratum row support and median contrast |
| Column/receipt identity weakness | Validate the pinned acquisition config, mapping, output hashes, individual reach identities and timestamp shift. Require unique registered labels and reindex by labels, not positions. Validate target identities against original bank slots. | Reordered/duplicate-column and stale-config/mapping regressions; actual pinned acquisition and derived inputs verified |
| Hardcoded execution status | Derive not-started/running/interrupted/failed/completed/reviewed status from job receipts and controller/worker locks. Persist errors and attempt history, close owned workers on failure. | Status lifecycle fixtures, failed-controller resume-history fixture; actual v2 status is `not_started`, zero active jobs |

The correction heads continue to fit the existing multi-output ridge objective,
with earlier-year selection and closed causal residual targets. No new model
family, encoder extraction, data request or Stage 3 was added. The substantive
RQ is unchanged. The new training/fallback arguments and fixed-population option
are opt-in: earlier experiment output files were not recomputed or overwritten.

Inputs/code are hashed before computation and checked again before a completed
receipt, including consumed derived banks and reference predictions. Changes
during computation leave partial artifacts and an error rather than a completed
receipt that misidentifies its inputs.

## Validation and present state

- **57 relevant tests pass**, including a synthetic complete scorer and an
  actual baseline/calibration-loop fixture with seven targets.
- Ruff checks/formatting and the isolated dependency check pass.
- Real preparation: **13,468 opportunities per stage**, seven correct target
  IDs, 481 storms; nine active source channels. All mapped model histories are
  available in the selected period. Verification/rainfall are unchanged.
- Full-census hour-end/history checks pass. Eys is absent as a target and carries
  no Q information in either stage's predictors or normalization.
- About **79 GiB free** remains, above the 50-GiB reserve. No new remote/cloud
  job or alert was started; the acquisition is reused.
- **No real-data model comparison has launched.** Synthetic fits and deterministic
  baseline checks are engineering validation, not new empirical findings.

[Machine-readable readiness and evidence](limburg-geoglows-audit-corrections-readiness-2026-11-14.json)
contains input/code/output hashes and the corrected real-census coverage-only
bootstrap diagnostic. Quantiles on supported draws remain conditional on support,
particularly for sparse documented floods; there is no favourable-draw retry.

Ordinary scientific limitations remain explicit: GEOGLOWS retrospective release
lag, approximate model/gauge spatial correspondence, historical-observation
qualifications, previous inspection of this archive and differing source/EO
coverage. These repairs make the comparisons interpretable; they do not guarantee
an AI advantage or establish live warning performance.
