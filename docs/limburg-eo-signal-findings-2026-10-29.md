# Model-specific EO diagnostics: findings for Brian

29 October 2026. Internal evidence/interpretation aid, not dissertation prose. All 20 model/readout jobs, covering three information conditions and the full 481-episode/eight-gauge initial-landmark census, completed. The full source/fold/null-source/score-reproduction audit passed. No old score, imagery or encoder was changed. [Protocol](limburg-eo-signal-diagnostic-2026-10-29.md); [implementation and checks](reviews/limburg-eo-signal-implementation-2026-10-29.md).

## Main interpretation

**The stored representations are not uniformly uninformative. A learned readout extracts small conditional increments against its own matched learned-ground control. However, these heads do not reliably improve the strongest existing conventional method, so this does not establish information missing from that stronger method.** This qualifies the broad interpretation of the negative retrieval findings without invalidating those findings.

These are exploratory comparisons on already inspected historical outcomes. Reported intervals are pointwise year-block intervals, not multiplicity-controlled declarations of model superiority or an untouched confirmatory test.

## 1. Real EO versus seasonal placebo

Under the original retrieval recipe, real EO has lower CRPS than earlier same-quarter placebo EO in all 60 model/readout/information-condition combinations. Relative reductions range from approximately 0.8% to 6.8%; 51 pointwise intervals exclude zero. These comparisons use identical eligible donor pools and paired placebo-supported opportunities. This shows that correctly timed representations matter to that recipe. It does **not** establish extra value over ground information: replacing real EO with a mismatched historical image can simply make an already inferior augmentation worse. Coarse quarter preservation does not remove all season, year, acquisition or physical-state differences.

## 2. Learned use changes the result, differently by model

Raw features are fitted separately for each model with train-only scaling and nested earlier-year selection of regularization and EO influence, including zero. On EO-supported opportunities, real EO improves the learned matched-ground point predictor in 46 of the 60 combinations. Eleven pointwise intervals exclude zero in the favorable direction. Real EO also beats its separately tuned seasonal-shuffle head in 40/60 combinations, with eight favorable pointwise intervals excluding zero.

For the recent representation when current local discharge is removed, results are:

| Encoder | Relative MAE change versus matched learned ground-only | Versus learned seasonal placebo | Interpretation |
| --- | ---: | ---: | --- |
| Presto | −2.60% | −2.21% | Both pointwise intervals below zero |
| AnySat | −2.04% | −2.37% | Both pointwise intervals below zero |
| OlmoEarth | −1.86% | −0.49% | Ground comparison interval narrowly below zero; placebo interval spans zero |
| Galileo | −1.73% | −3.18% | Both intervals span zero |
| TerraMind | −0.87% | −1.53% | Small diagnostic point estimates |
| CROMA | −0.47% | +0.78% | No consistent real-EO increment |
| Prithvi | −0.32% | −0.32% | Small diagnostic point estimates |
| DOFA | −0.24% | −0.87% | Small diagnostic point estimates |
| Copernicus-FM | +0.11% | −0.58% | No matched-ground point improvement |
| SatMAE | +0.55% | +0.02% | No matched-ground point improvement |

Negative percentages favor real EO. Models have different support and their own matched controls; this is not an equal-cohort architecture ranking. The headline table illustrates a declared condition, not a new selected primary endpoint. All conditions/readouts remain in the numerical output.

Readout choice matters: CROMA's monthly snapshot shows roughly 1.1–1.4% gains against its learned ground control across the three conditions, while its recent sequence has no clear consistent gain. Prithvi's monthly snapshot improves its learned ground control by 2.13% when all current Q is absent; its recent representation has much smaller increments. These are evidence against treating encoder/readout combinations as interchangeable, not a causal attribution to one architectural feature.

## 3. A stronger reference still wins

When scored as point trajectories, the original conventional analogue ensemble means outperform the learned EO heads in 59/60 supported model/readout/condition comparisons. The one favorable head point estimate is Prithvi/monthly with all current Q absent (approximately −0.14%); its interval spans zero. None has a favorable interval excluding zero against that reference.

For example, Presto/recent improves the matched learned control by 2.60% with local Q absent, yet remains 9.78% worse than the original conventional mean trajectory. AnySat/recent is 2.04% better than its matched learned control but 10.41% worse than the original mean trajectory. These are all MAE-to-MAE comparisons, not a comparison of head MAE with ensemble CRPS.

The benchmark libraries update differently: original retrieval can use earlier completed storms within the assessment year, whereas heads fit at fixed year boundaries. Thus this diagnostic cannot attribute the entire performance gap to model class. It still provides no demonstrated reason to replace the current strongest assessment pipeline with these heads.

## 4. High-water evidence remains weaker

Forty-eight of 60 high-water point estimates improve the learned matched control, but most increments are small/uncertain and the stratum includes unsupported opportunities using fallback. For Presto/recent with local Q absent, the full high-water-stratum improvement is approximately 0.49% and the interval spans zero; its EO-supported overall improvement is 2.60%. Prithvi/monthly shows a 1.43% high-water-stratum improvement with local Q absent, with a favorable pointwise interval against its learned control and seasonal placebo, but still does not beat the original conventional reference. Do not turn overall-flow improvements into a demonstrated flood-warning or high-water rescue benefit.

## 5. The representations have different structure

Five selected routes already use native temporal encoding: AnySat, Galileo, OlmoEarth, Presto and Prithvi. The other five encode dates independently and average their frame vectors. Neither group retains all original spatial information after catchment pooling. Single-month inputs exercise a different amount of temporal capability from four-week sequences; these diagnostics do not establish that every checkpoint has its optimal cadence/readout.

Descriptive variation in unit-normalized, event-linked representations differs substantially:

- Recent CROMA: gauge identity explains about 50%; adding seasonal harmonics raises the total to 76%.
- Recent OlmoEarth: gauge plus season explains about 91%; recent Presto about 81%.
- Recent AnySat: gauge plus season explains about 41%, or about 44% after year and coverage controls.

These are in-sample descriptive variance decompositions, not held-out predictive R-squared or proof that unexplained variation is hydrology. Within-gauge representation-distance associations with local Q, after seasonal/year/coverage/bin-age controls, are generally weak; median partial rank correlations are roughly −0.03 to 0.18 depending on model/readout. Antecedent-rainfall associations are weak and sometimes negative. Pair counts are dependent and no naive pairwise p-values were calculated.

Seasonal/location structure can be meaningful, but assigning half of retrieval distance to it is not the same as learning which components help the discharge task. The learned diagnostic supports that distinction. It does not identify a unique physical mechanism or prove a new extraction bug.

## Implication

The defensible conclusion is **some model-dependent predictive information, an unsuccessful fixed fusion recipe, and no reliable upgrade over the best existing conventional assessment method yet**. Any further work should preserve that strong baseline and test a small, learned correction with the same causal evaluation, rather than replace it with a weaker standalone head or restart extraction. Such a residual experiment is a next option, not run or required by these diagnostics. No new data request, encoder, fine-tuning project or full scarcity rerun is implied.

## Sources and reproducibility

`results/limburg_eo_signal_diagnostic_2026_10_29/review/` contains `paired-effects.csv`, `learned-weight-use.csv`, `model-representation-inventory.csv`, `representation-associations.csv`, `coverage-and-case-scores.parquet`, `audit.json`, `results-memo.md` and the manifest. Each job retains all predictions, tuning choices, outer-fold membership and null source IDs. Scope: same-gauge learned readouts at the initial landmark, not the entire earlier 180-job scarcity matrix or every possible use of these backbones. Frozen-checkpoint pretraining overlap and nominal product availability remain limitations on prospective/operational claims.
