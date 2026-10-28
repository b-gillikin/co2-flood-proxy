# Research-design audit: controlled monitoring scarcity

**Subsequent implementation:** Brian authorized the corrections; see the [implementation and verification record](limburg-scarcity-corrections-2026-10-28.md). The assessment below preserves the design as audited before those changes.

28 October 2026. Internal research aid for Brian; not dissertation prose. Audits the executable protocol, config, preparation, runner and tests before the remaining scoring queue. No scenario performance was used to choose recommendations. The completed delay/outage analysis and the new rich-reference benchmark remain preserved.

## Assessment

The question is scientifically defensible: **Can satellite AI help assess developing high water when ground-monitoring data are limited?** Controlled withholding, paired methods, chronological historical analogues and retained verification can answer it for these sites and this assessment task. The literature supports studying observation frequency, network placement and missing-input patterns. It does not guarantee that EO will help.

The implementation is a credible foundation, but the design is not yet a complete test of the broader scarcity story. The principal problems concern which shortages are actually represented, the population being averaged, donor quality and the exact inferential target. Resolve those points in the existing workflow; neither a new chapter direction nor more encoders/data is needed.

## Findings and corrections

### 1. Local feed loss is not regional information scarcity — high priority

Evidence: `scenario_keep` in `src/scarcity.py` thins/masks only the target channel for the density, schedule and missing families. Other tributary gauges, both Maas channels and rainfall remain available. Network subsets are a separate axis with complete retained feeds. The matrix has no combined sparse-network plus sparse-feed situation, although the broader design explicitly proposed a few combined situations.

Interpretation: those local scenarios validly measure loss of a local feed in an otherwise comparatively well-observed network. They cannot establish performance under simultaneous shortages. Each target-specific mask also describes its own hypothetical information view; it is not one realized network-wide outage seen identically by every target.

Correction: retain the single-axis contrasts, then add a small, declared set of combined profiles. Suitable candidates are a reduced network with six-hour reporting, and a reduced network with clustered gaps. Apply each profile to all retained affected feeds on coherent timelines, specify whether Maas remains, and retain every target's verification. Reuse the enumerated networks and shared masks rather than choose favorable stations. Do not form the full Cartesian product. This is completion of the stated design, not another research question.

### 2. The census is rainfall episodes, not exclusively high-water events — high priority

Evidence: the fixed calendar contains 481 regional rainfall episodes, eight targets and four issue offsets. The metadata has no high-water reporting stratum, and the new runner currently scores complete next-24h discharge responses without distinguishing ordinary flow, rising high water or recession. Complete verification exists for 3,746/3,751/3,761/3,778 cases at offsets 0/6/12/24h out of 3,848 opportunities at each offset.

Interpretation: keeping all episodes is a strength. However, average discharge error over all these opportunities does not by itself answer the high-water part of the question. This is also a census of the declared rainfall calendar, not a census of every possible flood mechanism or every high-water episode in the record.

Correction: keep the full eligible census and reuse the existing independently computed high-water and agency-threshold evidence for separate reporting. Show all-episode performance alongside high-water performance and rising/recession distinctions where support permits. Hindsight outcome labels are legitimate evaluation strata; they must not enter retrieval or simulated issue scheduling. Preserve undefined labels. Do not tune a percentile or select a few dramatic floods to obtain EO gains. Do not equate p99 with a flood-warning stage.

### 3. EO coverage changes the meaning of the average — high priority

Evidence: the preparation's weekly/recent `eo_valid` flags cover 1,192–1,600 of 3,848 gauge–storm contexts, depending on the encoder: approximately 31–42%. These counts precede verification and chronological-donor eligibility, so usable EO assessment support can be smaller. Unsupported EO uses conventional fallback. The code correctly retains broad conventional, matched conventional and EO-augmented arms.

Interpretation: the full-archive average answers the value of an EO-plus-fallback strategy over the held record. It combines actual EO use with many situations in which EO cannot contribute. It cannot alone describe the representation's contribution when available. Differences between models may reflect coverage, sensor era and donor counts.

Correction: report both the whole-census strategy effect and the supported-case representation increment on paired cases/donors, with actual EO use, dates, site, season, donor counts and high-water coverage. Use common-support comparisons when ranking encoders, alongside each model's broader coverage result. Do not replace the full census with a convenient common subset. Retain the decomposition into augmentation, donor restriction and total effect.

### 4. Finalized historical archives are a substantive assumption — high priority

Evidence: `159_prepare_scarcity.py` retains rich earlier donor histories; `partial_history_distances` projects those histories onto the query's retained coordinates. Network removal masks current observing inputs, but same-gauge historical donor response labels remain. The 3/6/9-year archive caps are separate.

Interpretation: this is valid for an historically monitored site suffering reduced current information. It does not simulate an ungauged basin or a country that never collected the historical gauge data. The all-Q-absent endpoint removes the current 72h input windows, not all historical discharge knowledge. Similarly, rainfall removal retains the reference rainfall-based assessment clock.

Correction: retain this coherent primary estimand and state it directly in the main results. Identify contemporary information loss, archive shortening and operational trigger availability separately. A persistent historical-poverty or ungauged experiment is not required to answer the current question. Do not quietly claim it from these simulations.

### 5. Missing donor inputs can influence retrieval — high priority

Evidence: historical Q gaps are forward-held within the 72h donor window, then filled with earlier-coordinate means. Missing rain descriptors are mean-filled too. There is no donor-specific overlap or imputation penalty in the distance. At issue zero, the raw 72h input-window finite fractions are approximately 91% for Sint Pieter and 59% for Venlo, versus 97–100% for the tributary channels. These are window-coordinate fractions, not percentages of clean events.

Interpretation: causal filling avoids future leakage, but does not guarantee a faithful hydrograph. A donor with missing values can look artificially close to an ordinary query because it is filled near the calibration mean; long forward holds can obscure its dynamics. Source-quality flags describe query inputs and outcomes but do not alone establish the quality of selected donor histories.

Correction: add selected-donor measured/held/mean-filled support to the retrieval audit, including duration and channel. Add one shared-support or overlap-aware donor-treatment sensitivity, defined before examining scarcity gains, if imputed support materially drives selection. Use the same eligibility/treatment in matched conventional and EO arms. Preserve uncertain cases in the declared main analysis and show the existing measurement-quality sensitivities; no blanket exclusion of all imperfect events is warranted.

### 6. The new reference changes several components together — medium priority

Evidence: this version uses an ordered 72h signature, peer and Maas groups, different conventional scaling and a new unit-vector EO distance. The completed age/outage analysis used a different signature and metric. Rich-local and Maas controls identify some network contributions, but do not individually isolate every change.

Interpretation: the new version can fairly compare its own rich/scarce conditions. A difference from earlier results cannot be attributed solely to scarcity or to better EO use.

Correction: keep versions separate and retain a compact bridge showing the new local reference versus the prior local method on matched cases. Attribute new within-version contrasts to their declared intervention. No large tuning search is needed. The fixed 50/50 fusion is a transparent method choice; a null result concerns this fusion/retrieval design, not every possible use of satellite AI. Do not select a winning fusion weight on these same scored outcomes.

### 7. Uncertainty and weights are not yet executable — high priority before interpretation

Evidence: the protocol names “999 joint mask × whole-storm/year bootstrap draws” and fixed gauge/issue weights. The reporting/bootstrap implementation has not been written, and the documents do not yet give an exact weighting or resampling algorithm. The scorer stores paired replication-level primary CRPS effects, providing a useful basis.

Correction: write down the target average first. A defensible primary summary is an equal-site, equal-issue average of paired case differences, with the eligible-case denominator and coverage visible; retain native-unit site results and the declared area-normalized summary. Fix the choice before inspecting gains. Estimate the scarcity interaction directly: `(EO − conventional)_scarce − (EO − conventional)_rich`, on paired support; separate significance labels are not an interaction test.

For uncertainty about mean performance over simulated random masks, resample whole mask-realization IDs coherently across methods, sites and issue times, then average their scores; do not treat a single random-mask draw as uncertainty about that mean. Preserve all gauges and issue offsets for each sampled storm. Specify whether year blocks are sampled alone or years then storms within years; do not implement two unrelated independent resamplings under an ambiguous label. Exact reporting phases and enumerated station subsets are design averages, not Monte Carlo mask samples; summarize their spread separately. Keep finite-year limitations visible. A full event census does not remove uncertainty about other storms, measurement quality or the masking mechanism.

### 8. Many contrasts need a reporting hierarchy — medium priority

Evidence: 39 scenario groups × four offsets, ten encoders, two readouts, K5/K10 and multiple scores create many correlated comparisons. The protocol prioritizes K5 CRPS and recent EO, which helps, but does not yet specify how model/scenario-wide claims will be made.

Correction: present primary loss curves and paired effects with uncertainty, then supported high-water and actual-analogue reviews. Treat monthly, K10 and archive caps as supporting diagnostics. If declaring a model/scenario a statistically established winner, handle multiplicity across that declared family or label the finding exploratory. Do not search the matrix for one favorable cell and make it the chapter's central claim. This remains exploratory work; formal preregistration is not required.

### 9. Density, network placement and country labels need exact interpretation — medium priority

Evidence: density masks anchor a reading at issue, but a natural source gap can still change effective last-reading age between conditions. Scheduled thinning intentionally mixes density with age. Three target sites are on the Wurm/Worm; both German targets are on that river. Network counts therefore do not represent interchangeable or independent basins. Maas is a predictor/context component, not an additional forecast target.

Correction: report actual ages and measured coordinate counts for every severity, including how often the controlled-density contrast truly holds age fixed. Keep the full census; use equal-age paired diagnostics where needed. Show target retained/removed, Wurm redundancy, country and mainstem availability alongside network size. NL–DE results are site comparisons, not a causal national-systems comparison. Do not describe the experiment as predicting the Maas itself.

### 10. Retrospective availability and the EO mechanism remain limited — interpretation

Evidence: EO uses completed pre-landmark weekly/monthly contexts held fixed through the issue sequence. Final gauge/rain series can include retrospective revisions. Acquisition-safe source windows do not establish actual historical product release times or remove checkpoint-pretraining overlap. The broader design already acknowledges these points; the executable protocol should carry them forward explicitly.

Correction: describe this as a retrospective controlled availability study with nominal product availability. The hypothesized EO contribution is antecedent surface/catchment context, not an image observing the current flood. Inspect retrieved seasons, dates, sensor support and quality so a gain is not automatically labelled discovery of hydrological state. Demonstrating predictive increment does not by itself establish its physical mechanism. Operational use would require an as-issued validation, but that is not a prerequisite for this dissertation analysis.

## What is already sound

- The same eligible event census and hidden verification are retained across scarcity conditions; no event sampling is needed.
- Missingness is generated independently of source values on continuous timelines, shared across methods and issue times. Genuine zeros remain values. Scattered and clustered gaps are distinct.
- Donors precede the query; their responses and storm closure are complete. Query-storm donors are excluded. Calibration uses earlier inputs, not the query's future response.
- Density and age have separate controlled/scheduled comparisons, with the natural-gap qualification above.
- Broader and EO-restricted donor pools are separated, unsupported EO has a declared fallback, and prediction intervals are not assumed calibrated.
- Enumerating the 128 network subsets avoids handpicking a favorable network. These are not 128 independent river systems.
- TTM vectors containing withheld observations are not reused. AlphaEarth is not presented as instantaneous water-state information. No new model or encoder extraction is needed to address the audit findings.

## Literature check

[Rakovec et al. (2012)](https://hess.copernicus.org/articles/16/3435/2012/) directly studies updating frequency and observation-network configurations in the Upper Ourthe within the Meuse basin. It supports examining placement and frequency separately, rather than treating gauge count as the entire network design.

[Nearing et al. (2022), Appendix A](https://hess.copernicus.org/articles/26/5493/2022/) supplies the two-state continuous-gap mechanism and fraction/run-length relationship used here. Its daily sequence lengths do not validate our hourly outage durations or make our simulated masks measured telemetry failure rates. The held [scenario-precedent review](limburg-scarcity-scenario-precedents-2026-10-28.md) documents the other sources and their transfer limits.

## Verification and next work

Re-ran the twelve scarcity unit/integration tests: **12 passed**. Reviewed the existing independent benchmark audit: rich-basin issue-zero only, 3,746 verified cases, scalar scoring fixtures and donor chronology checked. The preparation audit and benchmark audit are implementation checks, not proof that every scientific estimand is settled. No remaining scenario queue was launched during this audit, and the reporting/bootstrap stage remains unimplemented.

Next work is to amend the compact executable specification for the points above, implement the few combined profiles and reporting/quality ledgers, and define the paired weighting/bootstrap procedure. Preserve the prior completed results and benchmark provenance when versioning revised artifacts. Then run the complete declared census and report positive, null and adverse EO effects alike. There is no data-acquisition prerequisite for these corrections and no basis for killing the idea on the evidence reviewed here.
