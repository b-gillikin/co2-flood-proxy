# Making fuller use of the held foundation representations

Internal execution and interpretation aid, 2026-10-13. Brian writes
dissertation prose. Explicitly exploratory after the earlier outcomes.
Runners: `scripts/75_strengthen_foundation_representations.py`,
`76_check_alphaearth_metric_grid.py`, `77_plot_representation_checks.py`.
Outputs: `results/basin_ai_representation_checks/` and
`results/basin_ai_alphaearth_projection/`.

## What changed and why

The census showed a shape-versus-timing tradeoff in TTM, and a strong locality
preference in AlphaEarth. Brian approved testing these specific issues rather
than treating the first readout as the model's final capability. The existing
results remain intact. This pass adds no trained model, forecasting task,
architecture search or new provider request.

TTM's original readout averages eight 192-dimensional patch states. The
alternative concatenates them in their original order to 1,536 dimensions,
then L2-normalizes as before. This preserves patch-specific distinctions;
the backbone already mixes across patches, so the test does not assume that
mean pooling erased every temporal relationship. Both use the same frozen
512-96-r2 checkpoint and identical standardized histories. Architectural
patch sizes, weights and internal scaler remain unchanged.

A separate discharge-state block contains onset Q/p99, assessment-history
mean/p99 and standard deviation/p99. It preserves observed state information
that the standardized shape representation largely discards. The block is
added identically to raw histories, mean TTM and ordered TTM. Each state
column is scaled using the prior candidates' median/IQR, with unit fallback
for a constant column, then the same prior-only RMS block scaling is applied.
Temporal and state blocks receive equal weight. Query values and outcomes
never set these scales. The physical fields use only hours -511 through 0;
their p99 reference remains retrospective, as in the original design.

AlphaEarth retains its original mean-TTM backbone in this pass. On its same
276 main / 257 quality queries and the same eligible prior-event pools, the
comparison now includes conventional rainfall/Q, raw histories, catchment
area, one-hot gauge identity, fixed 2017 embeddings and prior-year embeddings.
Identity supplies a simple location-preference control with the same block
scaling; it is not another foundation model. Static 2017 context is available
before every evaluated event. No future-year average is introduced.

## TTM findings

Main mean-of-five peak MAE / mean individual peak-scaled shape RMSE /
mean individual peak-time mismatch:

| Cohort and representation | Peak MAE | Shape RMSE | Timing mismatch, hours |
| --- | ---: | ---: | ---: |
| Dutch: original mean TTM | 0.7489 | 0.2188 | 10.19 |
| Dutch: ordered TTM | 0.7770 | 0.2149 | 9.40 |
| Dutch: raw + state | 0.6481 | 0.2072 | 10.00 |
| Dutch: mean TTM + state | 0.6399 | 0.2039 | 10.51 |
| Dutch: ordered TTM + state | 0.6389 | 0.2008 | 9.85 |
| Dutch: conventional rain/Q | 0.6423 | 0.1997 | 10.61 |
| Pooled NL/DE: original mean TTM | 0.6969 | 0.2129 | 9.99 |
| Pooled NL/DE: ordered TTM | 0.6984 | 0.2103 | 9.42 |
| Pooled NL/DE: raw + state | 0.5913 | 0.2038 | 9.89 |
| Pooled NL/DE: mean TTM + state | 0.5970 | 0.2000 | 10.34 |
| Pooled NL/DE: ordered TTM + state | 0.5937 | 0.1982 | 9.80 |

The Dutch comparison has 534 queries/186 storms; pooled has 774/236.
Quality sensitivities retain 497/182 and 734/232 respectively. Every arm
within a cohort/sensitivity has exactly the same queries and candidate pool.

Preserving patch order improves timing versus mean pooling by 0.79 hours
Dutch and 0.57 hours pooled. Their conditional storm-resampling intervals
are [-1.34, -0.26] and [-1.11, -0.05]; year-block directions agree. Shape
point estimates also improve, but the main storm intervals include zero.
Peak MAE does not improve from changing pooling alone.

With the identical state block present in both readouts, ordered-versus-mean
timing differences are -0.66 hours Dutch [-1.23, -0.11] and -0.54 pooled
[-1.06, -0.03]. Shape point differences are favorable but their storm
intervals include zero. This direct contrast separates pooling from adding
state information, rather than conflating their contributions.

Retaining state makes a larger difference to magnitude: Dutch mean TTM MAE
falls from 0.7489 to 0.6399; pooled from 0.6969 to 0.5970. Raw-history retrieval
also improves considerably when given the same state block. Thus most of this
magnitude improvement cannot be uniquely credited to pretrained features.

Ordered TTM + state still adds shape value against the matched raw + state
control: Dutch difference -0.0064, 95% storm interval [-0.0101, -0.0027];
pooled -0.0057, [-0.0091, -0.0025]. Year-block intervals agree, and the
measurement-concern sensitivity retains the same direction. Its peak and
timing differences against that matched control remain uncertain.

Dutch shape improves on every river against raw + state. In the pooled
comparison Geul reverses slightly (+0.0027), while the other named river
strata improve. Wurm and Worm still constitute one physical river group;
two German gauges are not two additional independent basins.

Ordered TTM + state is now close in point magnitude and shape error to the
strong Dutch rain/Q benchmark. This is not a formal equivalence or
noninferiority result, nor demonstrated operational skill. The evidence makes
ordered readout plus explicit state a better-supported candidate for further
interpretation than judging TTM entirely from the original mean-only result.

## AlphaEarth findings

On the identical 276-query context frame:

| Context configuration | Peak MAE | Shape RMSE | Timing mismatch, hours | Same-gauge donor share |
| --- | ---: | ---: | ---: | ---: |
| Conventional rain/Q | 0.6340 | 0.2001 | 10.68 | 28.1% |
| Mean TTM | 0.6955 | 0.2270 | 11.59 | 27.1% |
| TTM + area | 0.6946 | 0.2188 | 11.29 | 71.5% |
| TTM + gauge identity | 0.6826 | 0.2134 | 11.30 | 97.5% |
| TTM + static 2017 AlphaEarth | 0.6749 | 0.2145 | 11.31 | 89.1% |
| TTM + prior-year AlphaEarth | 0.6641 | 0.2124 | 10.76 | 83.6% |

AlphaEarth improves on area, but most of its mean shape increment can be
matched by the simple identity control. AlphaEarth-minus-identity shape
difference is -0.0011, 95% storm interval [-0.0050, 0.0029]. Its residual
peak and timing increments also have intervals including zero. Identity
prefers the same gauge even more strongly; this is not an ablation proving
that the embedding encodes only identity or that the methods are equivalent.

The annual-versus-static shape difference is -0.0021, [-0.0061, 0.0019],
with uncertain peak/timing increments too. The existing evidence does not
establish an advantage from updating catchment context annually. The
conventional rain/Q method still has closer shapes than annual AlphaEarth
on the now-matched frame: AlphaEarth-minus-R0 +0.0123 [0.0056, 0.0194].
The quality sensitivity gives the same overall reading.

These results strengthen the model comparison by identifying what is and
is not distinguishable. They do not make geospatial context a dead end.
The existing held frame repeats six sites, and identity is especially useful
when an on-site archive exists. A purposeful subsequent scenario would remove
same-river donors while retaining query histories, asking whether the embedding
helps find relevant other-river events. That tests absence of a local analogue
archive, not prediction in a wholly ungauged river. It is a suggested next
application, not a gate or an experiment silently added to this run.

## Projection QA resolved

Earth Engine confirmed the annual mosaic's default EPSG:4326 projection;
local source tiles have 10-m UTM grids. A separate 72-row, nine-catchment
table was downloaded using explicit EPSG:3035 at 10 m. The original CSV and
geometry receipt were preserved. New projection/scale/geometry fields and
hashes identify the separate metric-grid delivery.

The minimum cosine similarity between old and metric-grid catchment directions
is 0.999999951; maximum normalized-vector distance is 0.000313. None of the
276 main or 257 quality query donor sets changes, and all seven outcome
contrasts are exactly zero. Thus the projection concern did not materially
affect these retrieval results. The explicit metric grid is preferable for
future aggregation and interpretable pixel counts.

## Evidence status and next work

All 102,645 selected slots and 20,529 query sets were assessed with the same
six census response diagnostics and original peak score. All comparisons,
including unfavorable ones, have paired query-storm and year intervals;
these are unadjusted, exploratory and conditional on the held archive.
Repeated donors, measurement uncertainty, pretraining and unseen locations
are not fully represented by those intervals. Six catchments remain six.

The original controls were replayed successfully in 16 cohort/sensitivity
configurations. Source/model checks and zero trainable parameters remain
enforced; the ordered representation uses the same 906 Dutch/German histories.
The earlier atlas depicts the earlier settings. New selected-pair and query
tables identify the revised donors for subsequent event interpretation.

The next work is to interpret gains and failures using actual event context,
and assess the cross-river application if useful. Weight sweeps, fine-tuning,
rainfall fusion, layer selection and recent-patch weighting remain optional
ideas rather than requirements. No automatic best-score selection was made.

```bash
PROJ_DATA=/Users/briangillikin/miniforge3/envs/chapter1-co2/share/proj \
  .venv-foundation/bin/python scripts/76_check_alphaearth_metric_grid.py --download
MPLCONFIGDIR=/tmp/limburg-mpl \
  .venv-foundation/bin/python scripts/75_strengthen_foundation_representations.py
MPLCONFIGDIR=/tmp/limburg-mpl \
  .venv-foundation/bin/python scripts/77_plot_representation_checks.py
```

Ordered embeddings have a hash-checked cache. A separate output directory
can replay the comparison using the same verified frozen extraction. Source
and result hashes stay in the run manifest. Brian retains prose authorship.

Validation: 112 tests passed, including patch-order preservation, state timing
and prior-only robust scaling. All 51 scientific CSV files reproduced exactly
in a separate directory; all 56 input/code hashes matched. Every selected set
contains five distinct prior storms whose response ends before the query,
and all 588 interval rows contain 9,999 finite draws. Sixteen original control
replays preserve previous predictions. Repository lint, changed-file formatting
and whitespace checks passed; the comparison figure was visually inspected.
The local `reproduction.json` records result hashes and these checks.
