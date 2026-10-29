# EO signal diagnostics: model-specific representations and learned use

29 October 2026. Authorized diagnostic work, not dissertation prose or an untouched confirmatory test. Existing outcomes and unsuccessful retrieval results have already been inspected. Preserve those results. No new imagery, checkpoint, extraction, fine-tuning or new research question.

## Questions and scope

1. Does real EO identify useful analogues better than a season-preserving, earlier-only placebo under the existing retrieval recipe?
2. Can a small learned hydrological readout extract additional information from each representation, including choosing zero EO influence?
3. Does representation variation reflect gauge identity, season, source support or hydrological differences?

Use the complete 481-episode/eight-gauge assessment census at its initial rainfall landmark. Diagnose rich information, absent current local Q, and absent all current Q, keeping rainfall/season/finalized historical labels. This is a selected set of conditions, not a sample of favorable events or another full scarcity matrix. Record unscored/unsupported opportunities. Use both held recent and monthly-snapshot representations, separately for all ten encoders. The exact cohorts and task remain versioned.

## Respect model differences

Inspect and report each selected checkpoint, modality, dimension, mask/coverage route and temporal handling. AnySat, Galileo, OlmoEarth, Presto and Prithvi already use native temporal paths; DOFA, CROMA, SatMAE, Copernicus-FM and TerraMind average separately encoded frames. Catchment pooling still summarizes spatial information in both groups. Do not imply that all ten had their sequence ordering discarded. Reuse each model's raw stored representation for the trained readout, fitting downstream scaling separately within each fold. Do not average different encoders or pretend that their coordinate systems are interchangeable. The existing retrieval diagnostic retains its original unit-vector distance for attribution.

## Retrieval negative control

Preserve the original conventional distance, same-gauge chronological donor eligibility, K5 empirical distribution and matched EO-supported pool. Replace the query's real EO vector with one drawn from an earlier closed episode at the same gauge and calendar quarter. Exclude its identical context where another seasonal source exists. Twenty reproducible placebo assignments preserve vector coordinates and most seasonal/site context while disrupting event-specific linkage. Sources are strictly earlier; never use later-year vectors. No seasonal source means an undefined placebo, not a hidden favorable fallback. Compare real/placebo/conventional on identical available pairs and retain the full opportunity ledger. Report CRPS here, keeping archive restriction distinct.

## Learned readout

Fit separate same-gauge, multi-output ridge readouts for each model and information condition, predicting the next 24 hourly discharges in area-normalized units. Ground features are the held ordered 72h ten-channel Q histories, rainfall/season, calendar year and satellite coverage/bin-age metadata. Remove the declared Q channels in both training and assessment inputs. Availability metadata enters all matched arms, so EO values do not get credit for metadata alone. Mean-impute and standardize using training rows only; retain variable missingness indicators. Each feature block is scaled by its fitted dimension, not forced to half the distance.

Evaluate ground-only trained on the broader earlier archive, ground-only on the exact EO training support, ground+real EO, and ground+seasonally shuffled EO. An augmented linear kernel is `K_ground + weight * K_EO`; ridge regularization and EO weight use the declared grid, including zero. Every model and each shuffled replication has the same tuning budget. Fit at fixed year boundaries; earlier donor responses and storm closure must be complete before the boundary. Tune on the latest two feasible earlier-year folds. Fit preprocessing anew within every inner/outer fold. When no tuning fold exists, use weight zero/alpha one; insufficient training support uses the lawful broader point predictor or previously saved conventional mean trajectory. Keep those fallback cases, with reasons.

Shuffle complete EO rows within each training quarter, leaving ground predictors and labels in place. Test-placebo vectors are sampled only from that fold's training archive, preferably the same quarter; disclose nearest-quarter relaxation if the quarter is absent. This is a negative control, not a simulated physical training history. Report unchanged permutations when quarter groups are singletons. No test-year data tunes or standardizes a model. All eight gauges share the same outer years; inference retains whole-year storm dependence.

For point readouts, primary score is mean hourly MAE; also report RMSE. Do not compare a deterministic head's MAE directly with the earlier ensemble CRPS as though output types were identical. The original retrieval diagnostic keeps CRPS. Use paired whole-year intervals for real-minus-matched and real-minus-placebo effects, including high-water/model-supported strata; these remain exploratory pointwise summaries. All models, null replicates and unsupported opportunities stay visible. A negative coefficient/weight result does not force EO to be useful.

## Representation diagnostics and interpretation

Describe raw norms, effective rank, duplicate contexts, and unit-vector variability explained sequentially by gauge, season, year and source coverage. Describe within-gauge association between representation distance and antecedent rainfall/current Q differences after seasonal, year, coverage and bin-age controls. Pair counts are not independent storms; these descriptive correlations have no naive pairwise p-values. They do not establish a physical mechanism or actual product-release time.

A real-versus-shuffled increment with lawful earlier-only readout would support usable event-specific information. No increment from either retrieval or learned use would strengthen the negative result for the held representation/task, without proving that no spatial/temporal pooling, fine-tuning or different hydrological model could help. Do not start another extraction automatically. Code, selection, held input hashes, fold membership, tuning choices, null sources and full predictions must be retained.
