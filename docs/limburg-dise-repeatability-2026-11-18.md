# DISE Step 3 — repeatability and largest-flow review

18 November 2026. Completed internal research aid for Brian's writing. Step 3
of the [saved plan](limburg-dise-four-step-plan-2026-11-17.md). The
[completed Step 4 evidence pack](limburg-dise-alphaearth-consolidation-2026-11-18.md)
brings these results together for writing. The primary incremental contrast is **H+A+E versus H+A**: the same
correction learner, adding AlphaEarth beyond model/weather history and
conventional catchment information. Positive percentage reductions below mean
lower river-balanced MAE. No fitting, model selection or new acquisition was
performed in this step.

## What repeats, and what does not

The all-day improvement when withholding a local river repeats across the five
test years. **A reliable added high-water benefit does not emerge.** These are
different outcomes; the all-day result does not replace the high-water research
question after seeing its results.

| Evaluation | Conventional MAE → with AlphaEarth (mm/day) | All-day error reduction | High-water error reduction |
| --- | --- | ---: | ---: |
| Later years at local rivers with historical target labels permitted | 0.2439 → 0.2474 | −1.44% | −2.15% |
| Local river withheld from correction fitting and tuning | 0.3839 → 0.3307 | **13.86%** | −1.06% |
| Reserved Ahr/Erft/Sieg transfer, no external correction labels | 0.5023 → 0.4789 | **4.67%** | −0.72% |

Temporal and spatial local tests each contain the same 12,362 observed/model
gauge-days in distinct fitting regimes. Each has 226 p99 high-water gauge-days
on 87 dates, and 172 strict-clean high-water gauge-days. External transfer has
57,133 gauge-days, including 1,055 high-water gauge-days on 122 dates. There are
49 contributing external gauges; the original 50-record inclusion ledger and
unavailable gauge-years remain in Step 2 coverage. None of these row or gauge
counts is a count of independent floods or catchments.

### Years and rivers

Local withheld-river all-day reductions are **12.47%, 11.75%, 11.48%, 14.32%
and 19.57%** in 2021–2025. The pooled improvement survives removal of any one
test year (12.69–14.38%) and any one local river (11.87–17.62%). Four of five
river groups improve: Geleenbeek 15.93%, Geul 13.27%, Gulp 23.09%, Wurm 18.71%.
**Voer worsens by 8.31%.** Pooling must not conceal that harm.

Local temporal all-day gains vary around zero and are worse overall. External
all-day point estimates improve in each of the four years, but year-specific
populations vary with observation availability (48/45/45/41 gauges). At fixed
river-system level, Ahr improves 1.74%, Erft 20.00%, and Sieg worsens 0.75%.
Removing Erft reduces the external pooled all-day gain to **0.18%**. This is
primarily an Erft transfer improvement, not uniform success across Germany.

Local withheld-river high-water MAE worsens in 2021–2023 and improves slightly
in 2024–2025. The pooled high-water loss remains after omitting any local test
year or river. Gulp improves 17.00%, while the other four river groups worsen.
External high-water annual changes vary from **9.75% worse to 20.00% better**;
the pooled point estimate slightly worsens. Its sign reverses when 2023 is
removed, illustrating dependence on the events actually observed.

## Paired uncertainty and what it covers

Configuration: `config/limburg_dise_repeatability_v1.json`. The seed is 20261118;
999 shared draws are saved for every scheme. Model predictions are fixed.

- **Joint whole-year resampling:** sample the five local or four external
  calendar years together across all gauges and models. Each replicate
  recalculates within-gauge means, then within-river gauge means, then the mean
  across rivers. Fixed gauge populations cannot silently shrink.
- **Synchronized circular moving blocks:** resample contiguous 30-day calendar
  blocks within each fixed year, with 14/60-day sensitivity. All gauges receive
  the same dates, preserving coincident weather and nested-gauge observations.
  This answers within-year variation conditional on the observed years. Thirty
  days spans the seven-day predictor memory and many multi-day events; it is
  an explicit working block choice, not an estimated universal storm duration.
  Circular wrapping can join year-end/start dates, a conventional boundary
  approximation disclosed here. Block-length sensitivity and whole-year
  estimates are therefore retained together.
- These are **calendar blocks, not recovered meteorological storm IDs**. Shared
  dates and nested gauges are never resampled as independent rows or sites.
  The same multiplicities apply to every compared model. Test years have
  overlapping rolling training histories; resampling fixed predictions does
  not quantify uncertainty from refitting, previously unseen rivers, or
  measurement error.
- Intervals are marginal percentile ranges, exploratory with few years and
  river systems. No multiple-comparison winner or significance claim is made.

Local withheld-river all-day AlphaEarth reduction has a whole-year 95%
percentile range of **11.90–16.64%**, with all 999 draws defined. Conditional
moving-block ranges are **11.29–16.58% (14 days), 10.65–17.17% (30 days), and
10.19–18.14% (60 days)**. Thus this fixed-domain all-day finding is not created
by one arbitrary short block length.

The corresponding local high-water whole-year range is **−5.36% to +1.63%**,
with 993/999 draws defined. The 30-day range is **−3.50% to +1.03%**, with all
999 draws defined. These do not establish an added high-water improvement.

For external all-day results the 30-day range is **2.03–7.00%**, 998/999 draws
defined. Whole-year resampling has **314 undefined draws**, because some
gauges have verification in too few years. Its 2.21–6.99% range is conditional
on the remaining 685 draws and must not be presented as an unconditional
population interval. External high-water has **364 undefined whole-year
draws** and **371 undefined 30-day draws**; the latter conditional range is
−7.23% to +7.38%. All draw arrays and failures remain in the output.

## Measurement, selection and references

Strict-clean high-water sensitivity worsens with AlphaEarth by **4.15% in local
temporal tests and 3.39% in local spatial tests**. Its uncertainty is particularly
fragile: 325/999 whole-year draws lose a required gauge. Clean-only external
analysis remains undefined because row-level provider QA is unknown. A value
outside the inherited strict-clean criteria is not automatically wrong; main
results retain it with its qualification.

The article-faithful selection-policy sensitivity gives all-day reductions of
−0.91%, +11.71%, +4.23% in local temporal/local spatial/external tests. Its
high-water reductions are −0.31%, +0.21%, −0.56%. The main all-day distinction
persists, while the small high-water sign depends on selection policy.
The AlphaEarth-substitution arm H+E improves local spatial all-day MAE 12.37%
and external all-day MAE 2.43% versus H+A. Its small high-water point gains
(1.96% in both) are secondary comparisons, not a new selected primary endpoint.

Total correction benefits and incremental embedding benefits remain distinct.
H+A+E reduces all-day MAE versus raw GEOGLOWS by 53.37%, 37.68%, and 31.50%
in temporal/spatial/external tests. Much of that improvement comes from the
conventional correction. High-water MAE also improves versus raw, but external
high-water **RMSE worsens 11.97%** with H+A+E (7.50% with H+A). A lower average
absolute error can coexist with more severe large misses.

`volume_bias.csv` retains signed and relative volume diagnostics. Relative
volume bias is computed per gauge and then balanced by river; it is not a
physical sum over nested river sections. Source/model mismatches and uncertain
high-flow observations limit causal explanations of these patterns.

## All largest flows and the event ledger

The analysis retains each available gauge-year maximum: **35 local maxima in
each regime and 179 external maxima**. These are maxima of eligible observed
days, not certified annual instantaneous peaks. AlphaEarth reduces absolute
error at 18/35 local spatial maxima and worsens 17; in local temporal tests the
counts are 15/35 and 20. External counts are 106/179 and 73. These correlated
site-year counts are descriptive, not independent success trials.

Every inherited p99 exceedance is included in the episode ledger, clustered
within river by a seven-day maximum gap, with three context days either side.
There are **90 local river episodes per regime and 56 external river episodes**;
the same storm can appear on several rivers. The seven-day rule supplies
review windows, not independence for the bootstrap. Complete-window peak-day
and volume results require complete daily verification; available-day errors
and incomplete windows stay visible. No gap is filled. All models, gauge-year
maxima and episodes are saved, including gains and harms.

Examples from the symmetric review index:

- **July 2021 Wurm:** the spatial AlphaEarth model improves on H+A at
  Herzogenrath 1 but worsens Randerath. Both severely attenuate some supplied
  daily surges. Their peak-day observations are outside strict-clean criteria;
  retain the observations and provider qualifications together.
- **December 2023 Sieg / DEA13190:** observed maximum daily specific discharge
  is 34.77 mm/day; raw GEOGLOWS estimates 35.23, H+A 57.93, and H+A+E 91.37
  on that day. Here correction amplifies a close raw estimate into a severe
  overestimate. Row-level QA is unknown; this is an error relative to the
  supplied observations, not a verified explanation of its physical cause.
- **Voer:** the pooled spatial all-day loss persists despite the broader local
  all-day improvement, so a deployable correction would need site/river-specific
  scrutiny. The present analysis does not estimate operator benefit.

The documentary-case table includes every entry in the held documentary
register, including unavailable/out-of-test entries. The year-only 2018 case
cannot identify a particular flood; the May 2024 statement confirms high water
without confirmed inundation. Documentary window boundaries do not supply an
exact flood onset. The inherited p99 definition is not an H1/H2/H3 designation.

## Execution, verification and remaining work

Runner: `scripts/277_assess_dise_repeatability.py`; statistical helpers:
`src/dise_repeatability.py`. The run took about one minute locally and created
small tables/compressed draw arrays. There was no GPU job, download or Azure
cost. Step 2 output hashes verify before analysis; the analysis also checks its
input/code identities afterward. **All 576 nonempty Step 2 metric records**
reproduce independently from sufficient sums (MAE/RMSE/bias); empty verification
strata remain explicitly undefined.

Meaningful checks compare synchronized sufficient sums with explicit weighted
replication, exercise leap years, unsampled nonfinite predictions,
missing-population draws, fixed-population year omissions and year-crossing
episode boundaries. A development check caught a pandas timestamp-unit
assumption in episode grouping; it was corrected before the real analysis.
Removing a year now keeps the original stratum's gauge population fixed; if
that removal eliminates a required gauge, its influence estimate is undefined.
Per-year descriptive summaries disclose their changing observed populations.

Sixteen relevant tests and Ruff pass. Seventy-two real-data resampled score
checks agree with explicit weighting, including undefined draws. All input
and output hashes verify. The durable
[verification record](reviews/limburg-dise-repeatability-verification-2026-11-18.json)
retains the run manifest and checks even though large results remain outside Git.

Reproduce from the chapter directory:

```sh
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 VECLIB_MAXIMUM_THREADS=2 \
  .venv-dise/bin/python scripts/277_assess_dise_repeatability.py
.venv-dise/bin/python -m pytest -q tests/test_dise_repeatability.py tests/test_dise_multiyear.py
```

Outputs: `results/limburg_dise_repeatability_v1/manifest.json`, `paired_effects.csv`,
`paired_intervals.csv`, `annual_effects.csv`, `per_gauge_effects.csv`,
`influence.csv`, `stratum_support.csv`, `volume_bias.csv`, `gauge_year_maxima.csv`,
`episodes.csv`, `episode_contrasts.csv`, `documentary_cases.csv`, and
`symmetric_case_review_index.csv`. The compressed arrays retain every draw,
scope, arm and metric, alongside the common date multiplicities.

**Step 3 is complete.** The linked evidence pack contains the Step 4 tables,
figures, event examples and limitations for Brian's dissertation writing.
