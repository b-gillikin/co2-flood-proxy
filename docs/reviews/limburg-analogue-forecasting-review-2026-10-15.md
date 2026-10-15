# Review of the proposed analogue-forecasting extension

Date: 2026-10-15. Internal scientific review for Brian, not dissertation prose.
Reviewed repository state: `1b35c09`. This note recommends options; it does
not authorize or implement a new analysis, change the active design, or claim
independent human validation. No new model results were generated.

## Assessment

The nearest-neighbour analogue ensemble is scientifically defensible, and
AlphaEarth has a plausible role in cross-catchment selection. However, much
of the proposed forecasting exercise already exists as retrospective outcome
evaluation. Renaming the current donor means as forecasts adds little.

The smallest worthwhile addition is a probabilistic assessment of the existing
analogue sets: do their distributions of future outcomes improve on the
eligible historical archive, and do their uncertainty ranges cover outcomes
as advertised? This would strengthen the present research question without
another model family or data request. It would remain a retrospective
distributional evaluation under the current full-era normalization.

A chronological forecasting extension is also feasible with held data, but
requires rebuilding event eligibility and normalization from past observations.
It should be a separately dated extension. Neither extension is necessary to
make the existing evidence scientifically reportable, and neither has to show
an AI win for the chapter to be worthwhile.

## 1. What would be new?

The current implementation already produces donor-mean peaks, mean response
curves, duration and late-flow estimates. `78_cross_river_analogue_checks.py`
computes ensemble-mean curve RMSE; script 82 compares it with a group-balanced
unranked archive; script 86 evaluates H1-started H2/H3 donor shares against
binary outcomes using squared error (the Brier-score arithmetic for those
shares). This is substantially more than visual similarity inspection.

The current strongest shape endpoint is the average mismatch between the
query and individual donor responses, each divided by its own response peak.
It evaluates shape relevance. It is not a proper score for a predictive
distribution, and it deliberately removes peak magnitude. Using the observed
query peak for this verification-only endpoint is legitimate; using that
unknown peak to construct a prediction would not be.

The information review gives a concrete reason to investigate distributions:
on 845 pooled queries, five-donor TTM mean-curve RMSE is 0.3504 versus 0.3387
for the generic archive, while individual shape mismatch is 0.1961 versus
0.2287. Finding closer individual precedents has not translated into a clear
advantage for their mean trajectory. Different donor peak times can smear a
mean curve. That motivates evaluating the ensemble, but does not establish
that its distribution is better.

New questions that the existing scores do not settle are:

- Does the complete distribution of donor outcomes improve on the archive's
  distribution, beyond any improvement in its mean or individual shapes?
- Are narrow donor ranges empirically reliable, or overconfident?
- How does this vary with lead time, river, archive support and geographic
  selection, under the same specified comparisons?

These can yield a useful negative result: closer examples may remain useful
for historical comparison while failing as a probability forecast.

## 2. Model and cross-gauge transfer

Use an equal-weight nearest-neighbour empirical ensemble as the transparent
starting point. TTM and AlphaEarth define retrieval features; the retrieved
completed responses define the ensemble. Keep entire donor trajectories so
their temporal dependence is preserved. Independently selecting a different
set of donors at every future hour would change the model.

Five and ten donors are already implemented. Their distributions are coarse,
and short archives are coarser still; report actual member counts. A finite
analogue ensemble cannot provide evidence for an unprecedented tail merely
because none of its donors exceeded a threshold. It has no general ability to
invent a missing storm mechanism or extrapolate new extreme shapes.

Our current transfer is effectively

    target Q(h) = target p99 * donor Q(h) / donor p99.

This expresses relative high-flow magnitude, not physical equivalence between
basins. Equal Q/p99 does not imply equal runoff depth, channel capacity,
flooding, or H1/H2/H3 category. It also does not force each transferred curve
to start at the target's observed current discharge.

For the minimal distributional review, retain this mapping so the review
answers a new scoring question about the existing model. Do not quietly
change the mapping while attributing the difference to a probabilistic score.

For a separate prediction model, make the initial-condition choice explicit.
A simple candidate for high-water cases with positive onset discharge is

    target Q(h) = target Q(0) * donor Q(h) / donor Q(0).

This transfers relative subsequent change, preserves nonnegative flows and
starts every member at the observed target state. It is a proposed modeling
assumption, not a literature-established universal correction. It can amplify
measurement errors, assumes transferable relative dynamics and may perform
poorly across contrasting river responses. Compare it with the existing
past-only p99 mapping as one stated transfer sensitivity if forecasting is
pursued; do not search many transformations for the best score. Specific
discharge (Q/area) alone would not resolve differences in runoff generation,
storage, regulation or travel time.

Direct TTM forecasting is a separate optional comparator, not necessary to
assess the analogue ensemble. Learned weights, fine-tuning and a new
hydrological model are also unnecessary for this extension.

## 3. AlphaEarth: plausible mechanism and current evidence

AlphaEarth can encode landscape properties associated with how rainfall and
antecedent conditions translate into runoff and recession. Its plausible
role here is selecting transferable catchments, not observing current storm
wetness or forecasting future rainfall.

The held literature already includes Liu et al. (2026), *Geospatial Foundation
Embeddings as Transferable Catchment Descriptors*. Its large-sample experiments
support geospatial embeddings as hydrological descriptors, with stronger
advantages in spatial transfer than within previously observed basins. It also
reports that annual embeddings did not outperform multi-year static averages.
Those results motivate our controls; they do not validate our hourly analogue
distance or prove that annual changes in Limburg add information.

The detailed Dutch review already shows an identity effect: annual AlphaEarth
increases the same-gauge donor share from 30.9% to 77.9% in the strengthened
five-donor comparison. Identity alone gives 94.7%; fixed-2017 context gives
85.3%. These are cohort-specific figures, not all pooled NL/DE results.

The necessary controls already exist: temporal/state alone, area, gauge
identity, fixed context and annual context; matched queries; and other-river
retrieval. In the other-river setting the identity penalty is constant, so a
gain there cannot be explained simply by preferring the target gauge. Area
and fixed-context comparisons then distinguish size and annual variation.

These comparisons can establish an empirical increment beyond those controls.
They cannot identify which landscape process caused it. Only a few distinct,
partly overlapping catchments support the geographic inference; thousands of
event rows do not become thousands of independent landscape examples. German
stations share the Wurm and do not constitute a national sample.

The latest sensitivity results reinforce conditionality: annual context's
timing effects change with event population and country. Preserve that result.
AlphaEarth belongs in a bounded extension as an incremental comparison on its
matched subset, with the full temporal cohort retained separately.

## 4. Evaluation audit

| Item | What the implementation does | Consequence for an extension |
| --- | --- | --- |
| Donor chronology | Script 65 requires a donor onset earlier than the query, its 72h response complete by the query, a different regional group and at most one selected event per group. | Sound protection against direct use of future donor responses. Preserve it; claiming all temporal leakage is thereby removed would be incorrect. |
| Distance scaling | Robust state scaling and RMS distance-block scaling use eligible prior candidates; raw-history standardization uses each history only. | These parts are already aligned with a sequential information boundary. |
| Event labels and state scale | `src/event_study.py::era_thresholds` uses the full rating-era series; p99 also enters history-state features and response transfer. | Valid for the declared retrospective catalogue. For forecasting, rebuild thresholds, onsets and scales from a past-only reference period. Changing just the final score denominator is insufficient. |
| Query completeness | Script 65 begins with `complete_scoring_sample` and a known 72h outcome; downstream comparison cohorts also require usable future responses. | A retrospective evaluation can score complete outcomes. A forecasting runner should first issue predictions for all input-eligible queries, then attach outcome availability. A missing hour at +50 need not exclude a +6h score. |
| Measurement flags | Some flags are established from later provider information or response-window problems. | Use these to qualify verification. Do not represent them as information an operator necessarily possessed at issue time or retrospectively suppress an issued prediction. |
| AlphaEarth timing | Script 84 uses the preceding year's embedding; fixed-2017 controls are explicit. | Avoids using the event year's annual image summary. It does not recreate historical release dates or an encoder trained only on data available then. Describe a retrospective test with a modern pretrained model, not an as-issued replay. |
| Storm dependence | Donors are distinct onset groups; intervals resample query groups and years. Groups use 72h onset linkage rather than independently established meteorological storms. | Keep group/year uncertainty and per-river results. Adjacent/overlapping windows and reused donors limit independence; existing intervals are conditional on the archive. No automatic 512h purge is justified just because input histories overlap. |
| Assessment population | Evaluations begin at selected high-water onsets or current-threshold H1 entries. | They address continuation conditional on observed high water, not detection of all floods among ordinary hours or an all-year false-alarm rate. |
| Prior development | Outcomes have informed multiple documented exploratory refinements. | A newly fixed sequential evaluation is useful but does not turn previously inspected years into an untouched confirmatory test. Disclose development history; no new data is required merely to report it. |

The 72h future window is not automatically a defensible warning lead time.
For a forecast extension, a fixed 24h main window with 6h and 12h readouts
would keep the question local and interpretable. These horizons are a proposed
design choice, not a claim that predictability lasts that long. Reporting
performance at each lead can distinguish near-onset persistence from later
continuation. Future observed rainfall must remain out of forecast inputs;
existing past rainfall is usable under a stated finalized-data assumption.
Archived weather forecasts are not needed for an observation-only test.

### Probability scores and calibration

Use CRPS on discharge distributions at specified leads, with a predeclared
aggregation over the horizon. Evaluate the actual finite weighted forecast
distribution, keeping the generic archive group-balanced. A median point
forecast corresponds to absolute-error scoring; a mean corresponds to squared
error. Do not compare a mean to a median under MAE and treat the difference as
solely a representation effect.

For an empirical ensemble, CRPS equals the weighted mean absolute error of its
members minus half their weighted pairwise absolute separation. This assesses
the distribution, unlike the current mean individual shape mismatch. It does
not by itself verify temporal coherence or accurate peak timing; retain the
existing trajectory and peak diagnostics for that purpose.

Report interval coverage together with width and directional misses. A
pointwise 80% interval is not an 80% simultaneous trajectory band. A donor
minimum/maximum range has no automatic nominal coverage. Brier scores apply
to a defined binary endpoint, but H3's seven observed cases in four regional
episodes are too sparse for a persuasive finely binned reliability analysis.
Keep the threshold findings as sparse supporting evidence, not the primary
calibration target.

Ferro's fair ensemble scores address a particular random-ensemble sampling
target. Our nearest neighbours are selected and storm-constrained; do not
automatically apply an iid ensemble-size correction and call the result fair.
Exact CRPS of the stated empirical distribution is a defensible primary
target, with member-count sensitivity reported. Any later calibration model
would need earlier-only fitting and separate evaluation; fitting one is not
required just to diagnose calibration.

## 5. Smallest worthwhile next step

Recommend a single distributional validation of saved analogue sets:

1. Preserve the current catalogue, models, weights, trajectory mapping and
   donor sets. Use every eligible case, keeping short/no-archive cases visible.
2. Score the existing empirical discharge distributions over a specified 24h
   window, with 6h/12h readouts, and compare with the group-balanced archive.
   Preserve conventional rainfall/Q and matched raw/state comparisons; TTM
   alone versus TTM plus AlphaEarth cannot establish practical AI value.
3. Assess coverage and width on matched cohorts, with existing river,
   group/year, measurement and five/ten-donor checks. Keep continuous Q as the
   main target; avoid another sparse H3 model.
4. Report whether closer retrieved examples also provide better distributions
   and honest uncertainty. State the remaining full-era and finalized-record
   limitations plainly. This does not earn a forecast claim by relabeling.

This adds a missing answer with existing data and model outputs. No RAG,
learned reranker, new foundation model or fine-tuning is needed. A separate
past-only reconstruction can support a stronger prediction question if Brian
chooses it, irrespective of whether the distributional result is positive.
It is additional work for that claim, not a gate on the present chapter.

The existing analysis is sufficient to report a retrospective representation
and transfer study with modest, conditional learned-model increments and
important failure cases. This review cannot guarantee committee acceptance
or operator benefit. The policy connection can remain concrete: transferable
historical evidence, its provenance, and the risk of treating a small,
confident-looking analogue set as reliable guidance.

## Sources and inspected implementation

- [Current evidence index](../limburg-analogue-evidence-index-2026-10-14.md),
  [information review](../limburg-analogue-information-review-2026-10-14.md),
  [AlphaEarth review](../limburg-alphaearth-detailed-review-2026-10-14.md),
  [definition results](../limburg-event-definition-results-2026-10-14.md), and
  [threshold results](../limburg-warning-threshold-results-2026-10-14.md).
- `scripts/65_hydrological_analogue_baseline.py`: candidate eligibility,
  chronological selection, scaling and donor aggregation.
- `scripts/74_review_analogue_census.py`, `78_cross_river_analogue_checks.py`,
  `81_run_expanded_event_analogues.py`, `82_review_analogue_information.py`,
  `84_complete_cross_border_analogues.py`, `86_analyse_warning_threshold_progression.py`,
  and `src/event_study.py`: inspected relevant scoring, context, threshold,
  episode and data-boundary functions. This was not a new full numerical audit.
- [Liu et al. (2026), Geospatial Foundation Embeddings as Transferable
  Catchment Descriptors](https://doi.org/10.1029/2026GL122814): already held;
  rechecked the original methods/results. Supports geographic representation,
  not our exact retrieval or forecast claim.
- [El Ouahabi et al. (2026), Multi-site learning for hydrological uncertainty
  prediction](https://doi.org/10.5194/hess-30-3549-2026): regional uncertainty
  modeling with hydrological outputs and catchment descriptors. Supporting
  context, not a requirement to introduce quantile random forests.
- [Hemri and Klein (2017), Analog-Based Postprocessing of Navigation-Related
  Hydrological Ensemble Forecasts](https://doi.org/10.1002/2017WR020684):
  hydrological analogue postprocessing precedent; differs from our direct
  transfer of observed event responses.
- [Ferro (2014), Fair scores for ensemble forecasts](https://doi.org/10.1002/qj.2270),
  [author manuscript](https://empslocal.ex.ac.uk/people/staff/ferro/Publications/ferro2013.pdf):
  ensemble-size and sampling assumptions in probability-score comparisons.
- [Hapuarachchi et al. (2022), Development of a national 7-day ensemble
  streamflow forecasting service for Australia](https://doi.org/10.5194/hess-26-4801-2022):
  forecasting verification, calibration and operational distinction. Its
  forecast-forcing and service requirements are not new data requirements here.

Review outcome: no changes to empirical code, data, existing results or
dissertation text. Recommendations remain advisory and separately dated.
