# Limburg Stages 1–2 — corrected seven-target protocol

14 November 2026. Internal research aid; Brian writes dissertation prose.
This implements the [six audit corrections](reviews/limburg-geoglows-code-design-audit-2026-11-14.md)
and Brian's decision to drop Eys. It supersedes the eight-target v1 setup without
overwriting its configuration, downloaded data or prepared outputs. No production
model comparison has launched; tests with synthetic data are engineering checks.

## Research question and practical motivation

**When gauge observations are replaced by global modelled discharge, how well
can we assess developing high water, and can AI improve that assessment?**

The intended contribution is a controlled comparison of actual discharge sources
and the incremental value of hydrological learning, raw satellite context and
frozen satellite representations. This can inform investment in monitoring and
assessment resilience. Historical local observations are available for training:
this is not an ungauged-basin or no-local-label experiment. GEOGLOWS is not
assumed universally worse than observations; evaluate its errors and coverage.

Stage 1 uses observed Q, Stage 2 uses GEOGLOWS RFS V2 retrospective Q. Rainfall,
assessment times, observed verification targets and methods remain fixed. The
retrospective product is released 5–12 days late: this is a hypothetical
hydrological-time information-content study, **not an as-issued/live fallback
demonstration**. An operational replay would need forecast/reforecast vintages
and arrival records. Global model and EO pretraining vintages are not claimed
to predate every historical test event. Only local fitting/tuning is chronological.

## Population, sources and clocks

- All 481 held regional rain episodes × **seven tributary target gauges** ×
  four issue offsets (0, 6, 12, 24 h): **13,468 opportunities per stage**.
- Seven targets: Cottessen, Azijnfabriek, Mesch, Rimburg, Brommelen,
  Herzogenrath 1 and Randerath. These represent five watercourses; both German
  targets are Wurm gauges. Country summaries are descriptive, not national effects.
- Nine active Q inputs: those seven gauges plus Sint Pieter and Venlo on the
  Meuse. The Meuse is context, not an assumed upstream control for every target.
- **Eys is neither a target nor a predictor in either stage.** The unchanged
  historical storage layout retains slot 0, but its query/donor Q and quality
  entries are missing/false and its Q normalization entries zero in both banks.
  No active predictor can use it. Explicit original slot IDs prevent shifting
  gauge identity when selecting the seven targets. Original observations remain.
- Retain the fixed 481-episode regional rainfall calendar, originally assembled
  across the broader eight-catchment region. Do not select a different event set
  after dropping Eys, and do not imply that this is autonomous event detection.
- Histories end at issue; next-24h **observed** Q is verification. GEOGLOWS
  start-labelled hourly means are shifted +1 h to the common UTC hour-end axis.
  No future model discharge is used as a predictor. Completed EO context remains
  frozen at the initial rainfall landmark under the existing nominal clock.
- Reach identities were checked with full stream topology, drainage areas and
  contributing polygons. Model outlets approximate gauge sections; additional
  area, including the substantial Brommelen polygon discrepancy, is part of
  model representativeness error. Do not describe this as measurement noise only.

## Methods and fair attribution

Retain conventional five-donor mean **and median** trajectories, strict latest-hour
persistence, and prior-only monthly empirical flow-duration calibration feeding
both persistence and conventional matching. The local mapper is explicitly our
specified implementation, not an equivalence-tested copy of the GEOGLOWS package:
up to 201 knots, averaged ties, annual fallback below 20 monthly paired hours,
positive multiplicative upper-tail extrapolation, no identity fill when there
is no prior calibration. Save knots, counts and fallback decisions.

Fit the existing small, multi-output ridge residual heads for:

1. **H:** permitted hydrology/rainfall context, correcting conventional C.
2. **R:** the same common context plus matched raw EO descriptors, correcting C.
3. **E:** corresponding frozen encoder features added to R's feature set.

All three arms use **identical closed historical training rows and earlier-year
validation opportunities**, including rows with missing EO. Imputation/scaling
and dropping unobserved/constant features are fitted on training data only;
missing features never become fabricated satellite observations.

R can select the exact causal H policy instead of its own head. Where raw EO is
unavailable, R returns H. E can retain the exact selected R policy as its zero-
encoder option; it has no separate EO-free retuning search. Where encoder input
is unavailable, E returns R. These rules apply during validation as well as at
test time. The scorer asserts equal training-row and validation-year records
and saves actual fallback/selection modes. A selection of C rather than a head
is identified explicitly and is not called encoder information.

Core representations remain **Presto** (twelve completed monthly contexts) and
**AnySat** (four completed weekly contexts), with their already verified raw
controls and feature tables. No new imagery extraction, encoder fine-tuning,
TTM re-encoding, AlphaEarth sweep or other model family is included.

Use fixed-year donor archives/normalization and only completed earlier-storm
responses. Residual targets use causal out-of-fold conventional predictions.
Local tuning uses earlier-year overall trajectory MAE; future high-water labels
are evaluation-only, not used to select hyperparameters or normalize predictors.
The archive has been examined before: this remains exploratory research, not a
new blind confirmatory test or formal preregistration.

## Evaluation

The primary substantive summary is seven-target **high-water 24h trajectory MAE**
in mm/h. Also report the complete rain-episode census with all fallbacks and the
joint **high-water × encoder-supported** conditional summary. These answer
different questions; do not interchange them. Keep native m3/s tables per site.

Separate H versus C, R versus H, E versus R, total pipeline value versus C's mean
and median and simple calibrated references, source-stage changes, and the
source-by-encoder interaction. The latter uses four-arm paired support. Include
RMSE, +6/+12/+24h errors, peak magnitude/timing, clean-verification sensitivity,
documented floods, site/country, support and fallback reporting. Incomplete
outcomes remain unscored and flat/undefined peak timing remains undefined. p99
is retrospective high discharge, not a proved inundation or bankfull threshold.

Average offsets within storm/site and then balance sites. Use identical 999
whole-year bootstrap multiplicities, assigning all of a regional storm to its
initial landmark year. For each declared stratum, fix its verification-eligible
site population **before** filtering prediction availability. If any required
site lacks support in a draw, that draw is undefined; retain and count it rather
than silently averaging fewer sites. Report partial-site and total undefined
draw counts. Quantiles from the remaining draws are conditional on their support,
not unconditional confidence intervals; sparse documented floods also need
event-level interpretation. No favourable-draw retries or arbitrary pass threshold.

Observation uncertainty still matters: strict/domain-valid hourly pairs train
the calibration, while the declared event outcome-valid policy trains the heads.
Retain provider qualifications and clean-verification summaries. Do not call
all finite extreme Q exact truth or discard every ambiguous event automatically.

## Execution, recovery and resources

- [Active v2 configuration](../config/limburg_geoglows_stages12_v2.json).
- Original pinned acquisition: `data/raw/limburg_geoglows_stages12_v1/`.
- Corrected outputs: `results/limburg_geoglows_stages12_v2/`.
- Validate acquisition config/mapping/per-reach identities and checksums before
  preparation. Align by unique channel labels, never blind column renaming.
- Two CPU workers with controlled numerical-library threads; no sustained GPU
  extraction is needed. Preserve the 50-GiB free-space reserve. About 79 GiB free
  remains at setup. Increased historical fitting support means older minute-scale
  fits are only indicative; update timing from the first real v2 job.
- Separate already-incurred image acquisition/encoder extraction costs from
  cached-feature fitting and marginal assessment costs, using the existing
  extraction receipts. A fast cached comparison does not establish a cheap
  end-to-end EO service.
- Pin input/code hashes before computation and reject a completed receipt if
  they change during it. Preserve partial outputs and error/resume records.
- Readiness derives actual not-started/running/interrupted/failed/completed/
  reviewed state from controller locks and job receipts. It does not hardcode
  an unlaunched status or confuse data integrity with research findings.
- Old eight-target preparation remains under its original v1 path; intermediate
  never-fitted v2 preparation revisions are retained separately. Historical code
  can be recovered from commit `9a34d7b`. No other chapter's data were changed.

```sh
# Setup/verification; these phases do not launch the full comparison:
.venv-geoglows/bin/python scripts/260_setup_geoglows_comparison.py prepare
.venv-geoglows/bin/python scripts/260_setup_geoglows_comparison.py audit
.venv-geoglows/bin/python scripts/260_setup_geoglows_comparison.py readiness

# Explicit subsequent full-fitting and review commands (not yet launched):
.venv-geoglows/bin/python scripts/260_setup_geoglows_comparison.py run
.venv-geoglows/bin/python scripts/260_setup_geoglows_comparison.py review
```

The same source corrections are applied before both stages' fitting. Stage 3,
if warranted by a specific finding or limitation, remains separate. No additional
core data request, email, cloud service or model is introduced by these repairs.

Literature foundations remain [Mbuvha et al. (2023)](https://doi.org/10.1017/eds.2023.11),
[GEOGLOWS retrospective conventions](https://training.geoglows.org/rfs/datasets/retrospective/),
[local correction guidance](https://training.geoglows.org/rfs/bias-correction/bias-correction/),
[Presto](https://arxiv.org/abs/2304.14065) and
[AnySat](https://openaccess.thecvf.com/content/CVPR2025/html/Astruc_AnySat_One_Earth_Observation_Model_for_Many_Resolutions_Scales_and_CVPR_2025_paper.html).
