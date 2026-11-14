# GEOGLOWS Stages 1–2: code and research-design audit

14 November 2026. Audited commit `9a34d7b`. This is an audit, not an implemented
design revision. No production code, source data, prepared inputs or fitted
research results were changed. No full comparison was launched.

**Brian's steering during this audit:** Eys may be dropped. Adopt removal from
both response targets and predictor inputs in both stages, leaving seven
tributary targets and two Meuse context sites. Preserve the original data.
The current eight-target preparation has not yet been regenerated for this
change; the implementation corrections below remain outstanding.

## Assessment

The paired same-river question is worth pursuing. The data and reusable features
are sufficient for this specification, and the proposed contribution is narrower
and more defensible than a general encoder tournament. However, the setup's
`ready_for_run` statement verified input integrity and executable plumbing; it
did not establish that every scientific contrast was properly controlled.
Two high-priority comparison corrections should be made before the full fits.
This does not require another dataset, encoder or research direction.

Re-ran all 45 relevant tests and Ruff successfully. Inspected preparation,
acquisition, calibration, fitting, inherited analogue/readout/summary functions,
the live protocol and actual held support. Evidence is saved in
[the audit receipt](limburg-geoglows-code-design-audit-evidence-2026-11-14.json).

## Findings, ordered by importance

### 1. P1 — Restricting targets to seven does not equalize predictor coverage

`src/geoglows_experiment.py:95` replaces every Q channel. Stage 1 retains Eys;
Stage 2 has no Eys reach and therefore loses channel 0 for *every* target, not
just Eyserbeek. `scripts/261_run_geoglows_comparison.py:385` supplies all ten
channels to each correction. `:520` then selects mapped *targets* for source
effects, without equalizing the network inputs.

The Eys observed history is 99.65–99.79% finite across the four offsets. Thus a
GEOGLOWS-versus-observed difference for Cottessen, for example, currently mixes
replacement of mapped-source values with removal of a nearly complete peer
gauge. The proposed interpretation as a direct source comparison is too strong.

**Correction, incorporating Brian's steering:** remove Eys as a response target
and as a predictor in both stages, including donor histories, source-dependent
features and normalization. Preserve the original eight-site data and previous
results. The revised population is 481 storms × seven targets × four offsets =
13,468 opportunities per stage. A legacy padded channel may remain internally
only if it is explicitly masked in both stages and cannot enter a predictor.
Regenerate the census/joins with explicit source/target indices; merely deleting
a configuration row is unsafe because several helpers assume eight targets and
ten channels. No separate Eys experiment, new data or model family is needed.

### 2. P1 — Hydrology-versus-satellite contrasts confound training population

At `scripts/261_run_geoglows_comparison.py:401`, the hydrology head receives
`raw_available=True` for every row. At `:410`, the raw/encoder heads receive the
EO-dependent support mask. The inherited
`src/eo_individual_readout.py:387` excludes training rows outside that mask, and
the satellite heads fall back to the conventional baseline rather than the
fitted hydrology correction when raw support is absent.

This is substantial, not hypothetical. Presto has raw support on 9,984/15,392
opportunities; AnySat on 9,416/15,392. For the Cottessen 2017 fold, closed valid
historical eligibility is 802 rows for hydrology versus 147 for Presto and 80
for AnySat, before finite-baseline checks. The years represented also differ.

The raw-versus-encoder contrast shares its training mask, so this finding does
not invalidate that particular contrast. It invalidates interpreting the
raw-versus-hydrology contrast as just the value of adding satellite information,
and can unfairly weaken the satellite pipeline against a strong ground model.

**Correction:** align training/validation opportunities and fallback policies for
representation attribution. Prefer retaining the complete historical hydrology
training record with train-only missing-feature treatment and a hydrology
fallback when EO is unavailable. Alternatively use a matched-training hydrology
control for the conditional representation contrast while retaining the full-data
hydrology model as the practical benchmark. State the chosen approach before
fitting. Do not discard the full event census or manufacture missing imagery.

### 3. P2 — Sparse-subset bootstrap silently changes the site population

`src/eo_individual_review.py:64` averages over whichever sites remain finite in
a year-resampling draw. A draw with no rows for one site therefore changes the
site population rather than becoming explicitly undefined. Only draws missing
*all* sites contribute to `bootstrap_nonfinite`.

A two-site/two-year synthetic reproduction gives finite intervals with
`bootstrap_nonfinite=0` even when every resample drops one of the two sites.
In the real documented-flood coverage subset, 440/999 shared draws omit some
sites and another 5 omit all sites, before fitted prediction availability is
applied. Whole-census and mapped-high-water coverage did not have partial-site
draws in this diagnostic. These counts are coverage checks, not performance
results.

**Correction:** maintain the declared site population in each reported estimand;
retain/count unsupported draws as undefined for that fixed-population statistic,
or explicitly specify and justify a different sparse-case uncertainty method.
For the few documented floods, event-level reporting may be more informative
than a nominal pooled interval. Preserve those cases rather than inventing
independent observations. Do not rewrite earlier studies' results silently.

### 4. P2 — Main high-water attribution lacks the joint support summary

`src/geoglows_experiment.py:186` provides separate high-water, mapped-target and
encoder-supported masks. Their intersection is not reported. The stage-level
source summary has mapped high-water rows, but the encoder-increment interaction
at `scripts/261_run_geoglows_comparison.py:544` does not.

Consequently an encoder's reported high-water effect can include the unmapped
Eys case and unsupported-EO fallback rows, while its mapped-target result can be
dominated by ordinary flows. The conventional median is saved but omitted from
the explicit encoder-versus-reference contrast table despite being an important
existing control for analogue averaging.

**Correction:** identify the primary high-water estimand explicitly; report
mapped-target high-water and its EO-supported conditional counterpart, together
with full-census pipeline coverage/fallback results. Include the existing median
reference in net-value contrasts. This adds reporting rows, not another model or
data requirement. Keep undefined severity and peak timing explicit.

### 5. P2 — Preparation can accept a wrong source-column order or stale receipt

`scripts/261_run_geoglows_comparison.py:131` reads the downloaded hourly frame
and blindly renames columns `0..9`. `src/geoglows_experiment.py:95` then treats
column position as source identity. The preparer records hashes but does not
first enforce the download receipt's config/mapping/output identities. A shuffled
frame or revised mapping could therefore be recorded as a new valid preparation
with wrong rivers in the channels. Current retained files are correctly ordered;
this is an input-validation defect, not evidence that current banks are swapped.

**Correction:** verify acquisition/mapping receipts before preparation, validate
unique channel labels and selected-reach identities, and explicitly reindex by
those labels. Add a reordered-column fixture and a stale-mapping fixture. Hashes
are provenance, not proof of semantic correctness.

### 6. P2 — Readiness always reports that no full analysis has launched

`scripts/260_setup_geoglows_comparison.py:310` hardcodes
`full_analysis_launched=False`. Neither that function nor the run controller
derives status from active/completed job receipts. Repeating readiness after a
full run would still print that statement. The current unlaunched status is
accurate, but the mechanism is not reliable for later handoffs.

**Correction:** derive setup/running/partial/completed/reviewed status from this
experiment's actual job records, recording failures and resume history. Keep
data-integrity readiness distinct from the research-design audit conclusion.

## Research-design conclusions and ordinary limitations

- **The research question survives this audit.** A paired change in actual input
  source is useful, and the testable contribution concerns high-water behaviour
  and incremental representation value beyond strong controls. Simple GEOGLOWS
  bias correction itself is established, not novel.
- **Preserve the information-content interpretation.** GEOGLOWS retrospective
  histories are reanalysis-based and released 5–12 days late. A history ending
  at a hypothetical issue time is not proof that it was available then. The
  current protocol acknowledges this; retain it. No additional live-forecast
  branch is required for this retrospective study. Operational fallback claims
  would require that later evaluation.
- **Keep rainfall fixed.** This isolates discharge substitution. It does not
  simulate all aspects of a poorly monitored region or establish an ungauged
  capability; historical local observations still train/calibrate the system.
- **Reach representation is part of the product limitation.** High coverage of
  the local catchment does not imply identical model/gauge sections. At
  Brommelen, only about 79.6% of the assembled model polygon lies inside the
  held local catchment. Describe source differences as model/proxy differences,
  not measurement noise alone; report both area and topology discrepancies.
- **Reference observations remain qualified.** There are 320 high-water
  opportunities marked verification-unclean, versus 2,531 clean high-water
  opportunities. Do not call all finite outcomes exact extreme-flow truth.
  Calibration uses strict/domain-valid hourly pairs whereas learned heads use
  outcome-valid event labels: explain these differing label policies and assess
  consequential measurement sensitivity without a blanket exclusion of events.
- **The local QM is a specified implementation, not yet an equivalence-tested
  copy of the GEOGLOWS package.** Its knots, tie handling, minimum monthly count
  and tail extrapolation are documented. Check that it behaves as a credible
  calibration reference, and name it accordingly; do not claim exact official
  implementation equivalence without checking.
- **Chronological fitting is not a blind new discovery set.** The archive and
  outcomes have informed previous directions. Retain the exploratory status;
  no formal preregistration or favourable-result threshold is needed.
- **Cost claims need the full accounting.** Reusing cached EO features makes
  this run inexpensive but does not make initial EO preparation inexpensive.
  Separate already-incurred extraction cost from marginal inference/fitting
  time using existing receipts. No new compute campaign is required.

## What checked out

- Downloaded hourly values have documented m3/s units and mean aggregation;
  the interval-start to hour-end shift is consistent with provider guidance.
- All ten Stage 2 query/donor channels were checked against the selected model
  series; Eys remains missing rather than zero or observed fallback.
- Rainfall and observed future outcomes are unchanged across the prepared banks.
- Local correction preprocessing/tuning uses earlier closed labels and earlier
  validation years; source-specific donor histories and Q normalization are
  replaced, rather than leaving hidden observed-Q predictors in Stage 2.
- Full census, common source-stage assessment identities, train-only scaling,
  causal residual targets, zero-encoder options, nonnegative discharge and
  missing-outcome handling are appropriate foundations.
- Nine model series are continuous for the selected 2010–2025 period. No new
  core data request or EO extraction is identified by this audit.
- Disk remains approximately 79 GiB free; the two-CPU-worker configuration is
  appropriate. No long GPU run is needed for these repairs or the comparison.

## Literature consulted

1. [Mbuvha et al. (2023)](https://www.cambridge.org/core/journals/environmental-data-science/article/novel-workflow-for-streamflow-prediction-in-the-presence-of-missing-gauge-observations/3ACF2CC1DB30EA4DF5B37F109617FC71):
   direct precedent for GEOGLOWS-based missing-data correction and downstream
   daily forecasting in Benin. Supports the approach, not a claim of first use.
2. [GEOGLOWS retrospective conventions](https://training.geoglows.org/rfs/datasets/retrospective/):
   hourly averaging, left labelling, units and publication delay.
3. [GEOGLOWS correction guidance](https://training.geoglows.org/rfs/bias-correction/bias-correction/):
   local monthly flow-duration correction and the distinction from experimental
   centrally applied SABER. Neither establishes the accuracy of our exact mapper.
4. [Nicolle et al., RAT technical note (2021)](https://hess.copernicus.org/articles/25/5013/2021/):
   temporal/spatial robustness testing and dependence on evaluation conditions.
   Supports the staged validation logic; this audit does not add its full testing
   programme to the chapter.

Recommended order: equalize the predictor network and fitting opportunities;
correct uncertainty/support summaries and acquisition/status validation; rerun
the existing integrity tests plus targeted regression fixtures; then execute the
same two stages. No new model family, research question or external-river stage
is needed to address these findings.
