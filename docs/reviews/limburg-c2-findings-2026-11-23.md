# Limburg C2 findings and high-water attribution

Research notes for Brian, 23 November 2026. Daily retrospective reconstruction
of GEOGLOWS discharge against observations. The comparison covers all 30
folds and 81,857 paired verification rows in each completed comparison.
The local temporal tests use historical labels from the target river. The
local spatial tests hold out entire river groups. Ahr, Erft and Sieg are
reserved external rivers. Evaluation years are 2021–2025 locally and
2021–2024 externally. Inputs include fixed landscape snapshots and retrospective
reanalysis, so the results do not measure operational warning performance.

## What the chapter can say

Comparison values are percent reductions in river- and gauge-balanced MAE
relative to the stated reference. Positive values indicate improvement.
The table uses the primary tuning policy. C0 holds the original conventional
predictors, C1 adds previous-year weather summaries and shape, and C2 adds
WorldCover, elevation relief, soil texture and prior-day soil moisture/snow.

| Contrast | Known local rivers all / high water | Held-out local rivers all / high water | External rivers all / high water |
| --- | ---: | ---: | ---: |
| C1 + 2020 AlphaEarth vs C1 | +4.25 / +0.54 | −1.26 / −1.75 | +1.31 / +3.50 |
| C1 + 2020 TESSERA vs C1 | +4.69 / +1.67 | −3.45 / −3.85 | +2.74 / +1.51 |
| C2 vs C1 | +8.25 / +4.34 | −7.89 / +2.10 | +5.60 / +8.02 |
| C2 + 2020 AlphaEarth vs C2 | +0.20 / +0.29 | +10.53 / +2.86 | +0.14 / +1.08 |
| C2 + 2020 TESSERA vs C2 | +1.93 / −0.62 | +5.59 / −4.58 | +3.61 / +1.67 |
| C2 + 2017 AlphaEarth vs C2 | +0.95 / +0.41 | +18.43 / −0.33 | +4.08 / +0.09 |

1. On known rivers, adding physical data reduced error more than adding either
   embedding. After C2, both embeddings' 30-day block MAE ranges include zero
   for all days and for high water.
2. On held-out rivers, C2 alone worsened all-day MAE versus C1. Relative to C1
   alone, C2 with 2020 AlphaEarth reduced all-day MAE about 3.5% and high-water
   MAE about 4.9%. C2 with TESSERA increased both by about 1.9% and 2.4%.
   The pooled C2 high-water directions repeat under article-faithful tuning:
   +1.85% for 2020 AlphaEarth and −4.92% for TESSERA. Local held-out high-water
   RMSE changes in the same directions (+2.36% and −3.92%).
3. For held-out rivers, choosing AlphaEarth imagery year by all-day error
   would favor 2017. It beats 2020 by 8.83% overall (30-day range +6.74
   to +10.78%) and loses by 3.28% on high-water days (−5.73 to −1.13%).
   This demonstrates sensitivity to imagery year. It cannot identify which
   changes in the inputs or embedding explain the difference.
4. Against C2, AlphaEarth 2020's held-out high-water MAE gain has a 30-day
   range of +0.93 to +4.43%. Restricting to 172 locally quality-qualified
   high-water gauge-days narrows the estimate to +1.71% (−0.08 to +3.13%).
   TESSERA's high-water MAE increases by 4.58% (range 3.10 to 6.83% worse)
   and by 5.85% on the qualified subset. This is evidence for selective
   usefulness, with limited support for a transferable high-water gain.
5. The 2020 C0 comparison gave weak gains across all days on held-out rivers
   (+2.58% AlphaEarth, +0.56% TESSERA) and higher high-water MAE for both
   (−2.11%, −6.47%). The C0/C1/C2 sequence shows that the observed value of
   an embedding depends on the conventional comparison. The C2 controls
   enter together, so these comparisons cannot isolate soil water, snow,
   land cover or relief as the cause.

## Which rivers and episodes drive high water

The attribution uses the inherited p99 labels and seven-day river episodes.
Every high-water row maps to one episode in its evaluation regime. There are
226 local high-water gauge-days and 90 episodes in each local regime, and
1,055 gauge-days and 56 episodes externally. Episodes on different rivers
may share weather. Contributions are percentage points of the pooled MAE
change with the original weights. Exclusions re-score fixed predictions
with the original weights on remaining rows, without refitting. They are
descriptive influence checks. The block ranges above account for temporal
dependence conditional on these evaluated rivers and fitted predictions.

| Held-out local river | Gauge-days | AlphaEarth 2020 contribution | TESSERA 2020 contribution | AlphaEarth 2017 contribution |
| --- | ---: | ---: | ---: | ---: |
| Geleenbeek | 28 | −2.29 | −4.03 | −3.60 |
| Geul | 21 | +2.14 | −1.61 | +0.02 |
| Gulp | 42 | +1.52 | +1.03 | +1.27 |
| Voer | 62 | +0.78 | +0.86 | +0.62 |
| Wurm | 73 | +0.70 | −0.83 | +1.35 |

- **2020 AlphaEarth on held-out rivers.** The Geul and Gulp were the largest
  sources of improvement. The Geul in late December 2023 contributed +0.40
  points. The July 2021 Gulp episode contributed +0.51 points, from four days
  outside the quality-qualified subset. At the same time, July 2021 Geleenbeek
  contributed −0.35 points. At Brommelen on 15 July the observed daily value
  was 18.78 mm/day, C2 estimated 2.67, and adding AlphaEarth lowered that to
  2.02. Across all local rivers the July 2021 episode windows contributed
  +0.31 points overall and −0.39 on the qualified subset. The pooled 2020
  gain remains positive after omitting any single river or episode under either
  tuning policy.
- **TESSERA on held-out rivers.** Geleenbeek produced the largest loss.
  The late-January/early-February 2021, July 2021 and November 2024 episodes
  contributed −0.69, −0.61 and −0.49 points. The pooled loss survives omitting
  any single river or episode under either tuning policy. Gulp and Voer
  contain examples of improvement and remain in the ledger.
- **AlphaEarth imagery years.** Most of 2020's high-water advantage over 2017
  came from the Geul, particularly in December 2023 and February 2024, with a
  smaller contribution from Geleenbeek. No single river or episode changes
  the direction under either tuning policy. High-water gains for 2020 remain
  modest even though it beats 2017 on that metric.
- **Known local rivers.** Under the primary policy, AlphaEarth 2020's small
  +0.29% pooled change depends on Geul gains offsetting Wurm and Geleenbeek
  losses. Removing the March 2023 Geul episode changes the pooled contrast to
  −0.14%. The pooled TESSERA direction changes with tuning policy.
- **External rivers.** The small pooled 2020 AlphaEarth gain (+1.08%) is
  attributable mainly to Ahr (+1.14 points). The Sieg's December 2023–January
  2024 episode alone contributed −5.72 points, partly offset by its January
  2023 contribution of +2.00. At Kaiserau on 25 December 2023 the daily
  observation was 34.77 mm/day, C2 estimated 66.59, and AlphaEarth raised that
  to 121.45. TESSERA's pooled gains come mainly from Sieg (+1.87 points)
  despite a −1.03-point contribution from the late-2023 Sieg episode. Both
  headline high-water MAE ranges cross zero, and high-water RMSE increases
  by 3.79% with AlphaEarth and 0.11% with TESSERA. On the high-overlap,
  location-consistent subset the MAE gains shrink to +0.14% and +0.70%.
  External observation quality is unknown for this clean-only comparison.

## Seasonal pulse and high-water sensitivity

The all-season observed daily p99 remains the primary high-water definition.
The seasonality review uses the same 12,362 local gauge-days in each of the
spatial and temporal regimes, covering seven gauges, five river groups and
2021–2025. Apply the Geul study's November–April and May–October split. For
each test-year, gauge and half-year, compute an observed seasonal median,
empirical percentile rank (midrank for ties), and seasonal p99 from the same
prior observations as the all-season p99, restricted to that half-year. The
reference starts in 2018 and ends before the test year, including in the
held-river evaluation. Model inputs and fits remain as archived. The seasonal
reference uses 412–552 daily records per gauge and half-year in the earliest
fold. These counts include serially dependent observations.
[Tsiokanos et al. (2024), §2.3](https://hess.copernicus.org/articles/28/3327/2024/) ·
[Anderson et al. (2025)](https://hess.copernicus.org/articles/29/6069/2025/) ·
[Guimarães et al. (2026), §2.1](https://hess.copernicus.org/articles/30/4245/2026/)

| Evaluated half-year | Gauge-days | All-season p99 | Meets both | Seasonal p99 only | Existing episodes by first p99 day |
| --- | ---: | ---: | ---: | ---: | ---: |
| November–April | 6,228 | 134 | 103 | 5 | 58 |
| May–October | 6,134 | 92 | 92 | 138 | 32 |

The original and seasonal filters overlap on 195 days. Another 31 days met
only the all-season threshold, all in the cool half-year. The seasonal-only
group is dominated by May–July (123 of 143 days) and by 2024 (104 days).
These figures describe the held verification period against earlier records.
The 90 episode counts retain the original seven-day grouping by river and
count each river episode once. They can include a shared weather event across
several rivers. The seasonal-only counts are gauge-days.

On held-out local rivers, the main all-season p99 comparison reproduces the
saved C2 tables. The table below uses the primary
tuning policy. Positive reductions mean lower river- and gauge-balanced MAE
relative to conventional C2.

| Days selected | Gauge-days | 2020 AlphaEarth MAE reduction | TESSERA MAE reduction |
| --- | ---: | ---: | ---: |
| All-season p99 | 226 | +2.86% | −4.58% |
| Both definitions | 195 | +3.02% | −4.42% |
| Seasonal p99 | 338 | +1.41% | −5.96% |
| Seasonal p99 only | 143 | −4.50% | −16.37% |

On the 276 clean seasonal-p99 days, the 2020 AlphaEarth difference was about
zero and TESSERA increased error by 6.61%. The seasonal-only TESSERA loss
persists under either tuning policy on both verification populations. It
also persists when each represented year is omitted in turn with the original
weights. AlphaEarth's sign changes when 2025 is omitted. Treat its seasonal-only
result as sensitive to composition. The clean seasonal-only subset covers
five gauges, compared with seven in the eligible subset.

The cool-half-year all-season-p99 cases show a C2 MAE reduction of 20.27%
versus raw GEOGLOWS. The corresponding warm-half-year estimate is −3.79%,
with a wide 30-day block range. Screening to clean days changes the warm
estimate to +15.36%, also with a range spanning zero and one gauge absent.
This comparison offers limited evidence about differences in C2 performance
by season. The clearer result is that conventional C2 reduced error on
seasonal-only days by 23.86% in the eligible held-river subset, and adding
TESSERA increased error relative to that C2 baseline.

The block ranges in `model_scores.csv` use 999 synchronized 30-day draws at
fixed years and record how many draws support all represented gauges. The
clean sensitivity screens the verification observations. It retains the
same historical reference so that the comparison isolates screening. This
is an exploratory second view of the saved daily errors conditional on the
evaluated years, rivers and models. Seasonally unusual flow is a hydrological
descriptor with a different meaning from an agency warning or flood impact.

Reproduce with `.venv-dise/bin/python scripts/300_review_dise_seasonality.py`.
The [runner](../../scripts/300_review_dise_seasonality.py) writes reference
thresholds, monthly and annual coverage, episode peak ranks, model scores,
year-omission results and `seasonal_pulse.png` under
`results/limburg_dise_seasonality_v1/`. All 24 local primary p99 contrasts
reproduced against their C2 and vintage completion receipts.

## Reproduction and interpretation

Run `.venv-dise/bin/python scripts/296_attribute_c2_high_water.py`. The
script checks the paired archive hash, event membership and agreement with
saved pooled primary and alternate-policy MAEs. It writes the complete river,
episode and gauge-day tables under
`results/limburg_representation_extension_v1/c2_alphaearth_2017_v1/high_water_attribution/`.
The observations in the selected examples are supplied daily values.
Retain their qualification flags when citing them.

The current evidence supports a chapter about when learned catchment context
adds value to retrospective discharge correction. The flood-resilience
implication is specific: report the high-water and cross-river checks before
selecting a representation for a data-poor river. StefaLand and Basin2Vec can
be compared on the same folds if compatible artifacts arrive.

## Whole-chapter audit

### Literature and contribution

The 23 November search used the method and product names DISE, GEOGLOWS,
AlphaEarth, TESSERA, StefaLand and Basin2Vec, and combinations of residual
correction, high flows, nested donors and ungauged transfer. It checked the
chapter's two evidence bibliographies against original papers, product
documentation and the DISE discussion. This was a targeted refresh for this
chapter.

| Source | Implication for this chapter |
| --- | --- |
| [Lin et al., DISE](https://doi.org/10.5194/egusphere-2026-1834) | Closest design. The public record reviewed is still the preprint. The study fits a related pooled residual correction against GRADES-hydroDL in the Yangtze, with 2017 spatial evaluation. The local contribution is independent multiyear transfer testing with a different base product, several conventional information sets and flow-specific checks. The public author/referee discussion also makes clear that annual embeddings represent catchment context; they do not supply event-day wetness. |
| [Liu et al.](https://doi.org/10.1029/2026GL122814), [Ou and Zheng](https://doi.org/10.1029/2025GL121604), [Qu et al. v3](https://arxiv.org/abs/2601.01558v3), [Basin2Vec](https://arxiv.org/abs/2611.05164) | The field already compares learned and conventional descriptors and examines spatial transfer, donor dependence and hydrological extremes. Basin2Vec already places AlphaEarth and TESSERA in one U.S. rainfall–runoff benchmark. Liu's exact runoff-free StefaLand experiment is CAMELS temporal validation. The global spatial result in that paper uses AlphaEarth. |
| [Hales et al.](https://doi.org/10.1016/j.jhydrol.2023.130279), [Chancay et al.](https://doi.org/10.3390/hydrology13050128) | Keep these additions as close GEOGLOWS precedents. Donor-based discharge correction is established. Chancay changes runoff before routing and reports regional differences including limited European aggregate gains. It motivates keeping raw GEOGLOWS in the results without adding a pre-routing experiment. |
| [Neri et al.](https://doi.org/10.5194/hess-24-5149-2020) | Keep. Their Austrian results show why overlap and nesting between donor and target drainage areas merit an independent check even when gauge IDs differ. |
| [Frame et al.](https://doi.org/10.5194/hess-26-3377-2022), [Dolich et al.](https://doi.org/10.5194/egusphere-2026-6036) | Keep Frame and the previously recorded Dolich preprint. Rare-event or instantaneous annual peak performance is a different endpoint from rolling daily p99 performance. Dolich's July 2021 cases help motivate case-level diagnostics. Their LSTM-specific saturation mechanism is not evidence about this XGBoost correction. |

An adjacent November publication applies embeddings to SWOT-based discharge
estimation. The publisher full text was inaccessible in this check; the
publisher index and DOI establish its scope at title level only. It is not
needed to interpret the matched GEOGLOWS results.
[Gan et al.](https://doi.org/10.1080/15481603.2026.2759390)

The contribution is a bounded empirical test of how representation, conventional
input richness and transfer setting interact in one reconstruction method.
Useful claims include the reversal between all-day and high-water ranking for
the two AlphaEarth vintages, the limited added benefit at known rivers after C2
and the loss of external large-error performance despite lower MAE. A claim of
algorithmic novelty, a mechanism specific to any C2 variable, or a causal
benefit of higher-quality data would exceed this design. The useful
UNU-MERIT link is the evidence that a receiving agency would need before
reusing a correction on a river with limited calibration data. The earlier
forecast, analogue and inundation-mapping studies have their own endpoints and
do not serve as additional arms of this chapter.

### Design, data and result checks

- **Matching and leakage.** Rebuilt all 30 fold selections from the C2
  feature table and matched every test key to the prediction archive. Fitting
  and validation end before the test year. Reserved observations and the
  whole held local river group are excluded as specified. Predictor lags use
  modeled Q and weather, never observed Q. Gauge-specific p99 cutoffs use
  2018 through the preceding year and enter evaluation only. This requires
  historical observations to define the evaluation subset. They are daily
  high-water indicators, with neither official alert-threshold meaning nor
  a flood return period. Some July 2021 observations remain qualified.
- **Physical separation.** In the pinned reference polygons, there are no
  cross-group local overlaps above 1 m². Two regional-donor/local boundary
  slivers cover at most 0.058% of a target local polygon. No GEOGLOWS reach
  ID is shared across source roles. One substantive external conflict does
  remain. Weckhoven (Gillbach, reserved Erft gauge `DEA10430`) and Kaarst
  (Nordkanal, donor `DEA10450`) are assigned virtually identical reference
  polygons despite different GEOGLOWS reaches, and Kaarst already has zero
  model-polygon coverage in the ledger. Their 1,460 daily observations on
  common dates are not identical (correlation 0.37), so this is a spatial
  support conflict rather than evidence of duplicate outcome labels.
  Dropping the 978 Weckhoven verification rows (18 high-water rows) from
  the existing predictions preserves the external conclusions. For example,
  the 2020 AlphaEarth/TESSERA high-water MAE reductions change from
  +1.08%/+1.67% to +1.10%/+1.65% versus C2; raw GEOGLOWS still has the
  lowest high-water RMSE. This is a fixed-fit check. Describe the external
  evaluation as target-label holdout with mapped overlap, rather than a
  physically disjoint validation.
- **Inputs and timing.** Verified the daily conversion from m³/s to mm/day
  on all finite feature rows. The hourly-mean GEOGLOWS retrospective is
  independently documented as a deterministic reanalysis simulation.
  The correction uses same-day GEOGLOWS and weather. It therefore tests
  reconstruction after those inputs exist. A fixed 2020 descriptor is
  assigned retrospectively even to pre-2020 fitting rows. Verify no
  same-year imagery for the evaluation period, and distinguish the imagery
  year from model pretraining and product availability. For C2, all 394
  catchments have finite clay summaries, but valid clay area is about
  36–100% across the census and 50–99% locally. Three of seven local
  polygons have less than 80% valid area. The clay features summarize the
  valid portions. No threshold-based exclusion was added. ERA5-Land soil
  and snow are broad antecedent conditions at native grid resolution.
  [GEOGLOWS retrospective documentation](https://training.geoglows.org/rfs/datasets/retrospective/)
- **Absolute errors and the conventional comparison.** The useful contrast
  is a bank of matched baselines, since C2 is richer and can still lose to
  a simpler control. On known rivers, C2 lowers all-day MAE 8.25% versus
  C1 and 5.49% versus C0. During high water, C2 improves on C1 by 4.34%
  and has 1.07% higher MAE than C0. On held-out local high water, raw
  GEOGLOWS, C0, C1, C2 and C2 + 2020 AlphaEarth have MAE of 3.135,
  2.802, 2.884, 2.823 and 2.743 mm/day, respectively. Also retain the
  donor-FDC and extra-information local calibration references in the
  comparison. On external high water, the evaluated C2-family versions
  reduce MAE versus raw GEOGLOWS, but raw RMSE is 9.440 against C2 at
  9.710 and the embedding arms at 9.720–10.078 mm/day. This is why an
  improved typical error is insufficient evidence for handling high flows.
- **Units and uncertainty.** As a diagnostic, scoring those same fixed
  predictions in m³/s also favors 2020 AlphaEarth (+1.72%) and penalizes
  TESSERA (−5.01%) during held-out local high water. For all days in that
  same regime, TESSERA's +5.59% in mm/day becomes −7.26% in m³/s, which
  gives errors on larger basins more influence. State the primary unit and
  river/gauge weighting. On clean local spatial high water, 2020 AlphaEarth's
  30-day range crosses zero and only 751 of 999 draws contain the complete
  contributing gauge set. This limits the inference even though the main
  local spatial direction persists with 14-, 30-, 60-day and whole-year
  blocks. The ranges condition on fitted predictions and the available
  rivers; they are not simultaneous intervals or representative of Europe.

### Reproduction, recovery and handoff

The four paired archives match their recorded SHA-256 hashes and have identical
keys, observed/model Q, cutoffs and quality flags after harmonizing nullable
Boolean serialization. There are 81,857 rows, including 1,507 high-water
rows across the evaluation regimes. Fifty-six gauges contribute verification,
distinct from the 394-gauge input census. Verified 13,098 recorded job output
hashes plus 322 from the two reused pilot jobs. In the held Geul 2021 C2 fold,
loaded all nine saved final models for the three primary-policy arms and
reproduced every one of the 267 saved test predictions and their seed averages
exactly. The focused DISE suite passed 47 tests, the active scripts passed
Ruff, and the analysis environment passed `pip check`. Checked the held results
and inference path without initiating new model fits.

The live README, study pointer and integration manifest now refer to the
completed C2 evidence. The manuscript chapter remains a writing placeholder.
The isolated runtime and source snapshots exist locally. The available
verified Azure restore records cover the older EO work. I found no
equivalent readback receipt for the current discharge evidence. Preserve a
private recovery copy of essential inputs and completed outputs before any
local retirement. Git tracks the scripts and docs, while data and fit outputs
are ignored. Follow the provider correspondence when preparing public
reproducibility materials, including keeping raw LANUK records private.

The chapter is ready to write. Its main results and limitations can be reported
while the StefaLand release link and Basin2Vec checkpoint are outstanding.
The two additions need compatible artifacts, and neither requires another
data request for the completed C0/C1/C2 comparisons.

## Other RQs

Parked on 23 November 2026. Revisit after receiving and checking the requested
StefaLand and Basin2Vec artifacts and completing the planned matched runs.

1. **Local calibration.** How much does limited local gauge history improve
   high-water discharge estimates on a receiving river? How much and what
   kind of local evidence would an agency need to rely on the correction?
2. **Added value of embeddings at equal data budgets.** With the same
   transferred correction and held-out evaluation events, does a frozen
   embedding reduce the amount of earlier local calibration data needed?
   How does adding the embedding compare with collecting a little more
   local data? Measure both record length and the number of distinct
   high-water episodes in each calibration budget.
3. **High-water error mechanisms.** When gains during high water are smaller,
   how much is explained by the larger baseline error, unusually large
   residual corrections, and insufficient event-scale information? Treat
   rainfall timing, antecedent wetness, routing and measurement quality as
   hypotheses to distinguish using event evidence.
4. **Confirmed floods and warning use.** Does performance on daily p99
   episodes carry over to independently documented floods? With forecasts
   as issued, historical warning thresholds and monitored flood/non-flood
   periods, would a correction change missed crossings, false alarms, or
   warning lead time relative to the operational reference?

The earlier [scarcity tests](../limburg-scarcity-results-2026-10-29.md)
mostly reduced during-event inputs at monitored sites and found no
consistent encoder advantage. The earlier
[GEOGLOWS next-day comparison](../limburg-geoglows-first-results-2026-11-14.md)
found about a 3.6% gain from simple local calibration on matched cases,
with no reliable encoder increment and no graded calibration budget.
The current C2 spatial tests supply the zero-local-fitting-data case.
The temporal fits allow historical target-river observations and provide
a separate reference. A future graded comparison would keep the donor
pool, test events and information cutoff fixed and vary only the permitted
earlier target-river records. Operational reliance would also require an
agency-defined performance standard and a forecast evaluation.
