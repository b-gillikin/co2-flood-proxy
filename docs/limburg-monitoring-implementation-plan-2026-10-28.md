# Implementation plan: high-water assessment with late or unavailable gauge data

2026-10-28. Brian requested a plan for the **whole new direction**, not only TTM/AlphaEarth. Planning and read-only input checks are complete; simulations, new model inference and new downloads have not started. Brian retains dissertation/article prose. This plan refines the [active design](limburg-monitoring-resilience-design-2026-10-28.md) without changing its RQ. Its primary event-clock refinement supersedes the earlier 126-storm restriction; the original design discussion remains dated history.

**RQ: Can satellite AI help assess developing high water when a gauge's data are late or stop arriving?**

The study estimates how assessment accuracy degrades with observation age and whether EO reduces that loss, relative to ordinary available information. Its practical application is evidence for monitoring redundancy and contingency assessment within FEWS. It does not assume an AI advantage or establish operational warning performance.

## 1. Prepare the complete assessment calendar and availability ledger

Use the continuous held hourly discharge and rainfall, preserving UTC hour-end semantics, source quality and genuine zeros. Retain every eligible gauge–storm opportunity, including nonresponses and unsupported predictions, with explicit reasons. There is no random event/gauge sample.

**Improve the clock:** start at the first hourly timestamp at which a core catchment has accumulated the inherited 10mm rainfall criterion within the observed episode. Use only the observed prefix, not eventual rain totals or hidden target Q. A read-only check finds this timestamp in **all 468 held episodes**, rather than only the 126 qualifying in their first six hours. The old six-hour clock can remain a supporting comparison; it does not limit the main census. The threshold is a study-calendar definition, not a flood-warning threshold.

Retain the existing 12-observed-dry-hour grouping and uncertain-boundary flags. Seven held episode boundaries are uncertain; review them without making all uncertain outcomes disappear. Audit whether German-only rainfall episodes are absent from the Dutch-defined calendar using the already-held German rain series. If that audit identifies additional compatible episodes, extend the shared calendar before scoring, preserving the original 468 as a traceable subset. Do not claim an exhaustive independent German census from a six-Dutch-catchment trigger.

Reassess at 0/6/12/24h after each landmark. Implement full observations, fixed 1/3/6/12/24h delivery delay, a stopped feed, and the already-specified early-outage sensitivity. The station feed includes its valid redundant sensors. The interruption affects delivered local Q; observed rain and other feeds remain intact. Assign release times separately from measurement timestamps. Deduplicate instantaneous information states shared by different scenario labels.

**Deliverable:** one row per gauge, storm, issue and information state, including last available Q time, input/source age, retained values, verification availability and quality flags. Version the calendar and identify additions or shifted landmarks.

## 2. Complete the data inventory and acquire useful additions

Audit actual source acquisitions, clear/valid catchment pixels, consistent spectral dates, orbit/input route, model compatibility and product-release evidence. Distinguish missing transfers, unqueried source scenes, clouds/no-valid-pixel periods, pre-mission dates and unavailable products. More data is worthwhile where it fills a real support gap; absent observations cannot be recovered by duplicating downloads.

| Data | At hand | Planned action and role |
| --- | --- | --- |
| Hourly Q and catchment rain | Eight-gauge continuous axis, 2010-01-01 01:00 UTC through 2026-01-01 00:00 UTC; natural gaps remain | Required, held. Rebuild histories and future windows for every new issue time. Recover valid observations from held native deliveries where possible; retain real gaps and measurement-domain uncertainty. |
| Catchments, areas, gauge identities and source QA | Held, including German aliases and provider replies | Required, held. Reuse reviewed geometry, quality flags and unit/time conversions. Do not request already-unavailable historical thresholds or datums as a prerequisite. |
| Ten corrected EO representations and source imagery | Held corrected aggregates plus completed supplemental archive (66,913 committed files, about 99.8GiB including metadata) | Required for their supported arms. Reuse exact compatible contexts. Join to the new landmarks by actual cutoff; never attach an old vector containing imagery after a newly earlier cutoff. |
| EO contexts needed at changed/new landmarks | Some can be reused; final join not rebuilt | Inventory all required dates/catchments and all compatible source scenes. Fetch genuinely missing compatible scenes/metadata, including relevant dates outside the original requests; then extract only changed or absent contexts. Cover the eligible census rather than a convenient example subset. No blanket rerun of all ten is assumed. |
| Soil moisture and snow context | Held ERA5-Land fetch requests temperature, dew point and surface pressure, **not soil moisture or snow** | Recommended addition: full-period catchment/covering-grid ERA5-Land soil water layers 1 and 2 plus snow depth water equivalent. Reuse temperature. This supplies one transparent antecedent-state control and event-interpretation aid, not another hazard/model project. |
| TTM weights/source and legal 512h Q histories | Pinned model/source held; shifted-history support exists | Supporting arm. Rebuild histories ending at last available Q, not issue time. No new model download required. |
| Annual AlphaEarth catchment summaries | 2017–2024, all nine exported catchments, including the eight response sites; original and metric-grid versions held | Supporting landscape/cross-river control. Use the preceding completed year, document nominal availability and preserve version/geometry identity. Current inventory covers study-event years through 2025; no newer annual layer is required for those events. |
| Historical delivery timestamps and station-wide interruption logs | Not established by finalized provider records | Valuable optional request to existing Dutch/German contacts: any retained observation-versus-receipt timestamps, known feed interruptions, real-time quality flags, and whether backups were delivered at the time. Enables realism checks; absence does not stop the counterfactual study. Do not resend already-answered source-semantics questions. |
| Flood labels, inundation maps, forecast archives | Partial supporting flood evidence; not a complete operational archive | Not required to estimate observation-loss effects on discharge assessment. Preserve held high-water/flood cases for interpretation. No new flood-mapping, forecast-replay or damage-model data requirement is introduced. |

**Soil/snow acquisition:** use [ERA5-Land hourly](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land) through CDS for the full analysis period plus available antecedent history, over all study catchments and covering cells. Preserve the download manifest, grid-cell footprints, units and aggregation weights, and compare anomalies using earlier data only. This is modeled land-state information at much coarser resolution than the tributaries, not measured catchment wetness. [Wanders et al. (2014)](https://hess.copernicus.org/articles/18/2343/2014/hess-18-2343-2014.html) supports the relevance of soil-state information to flood forecasting, but its satellite assimilation results do not validate ERA5-Land or our analogue method. Retrospective reanalysis availability is not proof of live delivery. Use it as a declared supporting physical-context comparison, never as verification truth or an undeclared real-time input. If useful cells are already held, reuse them.

**No stinginess rule:** acquire all compatible observations necessary for the defined catchments, period and model inputs. Report expected bytes and gained coverage before a large transfer; do not choose a small event sample merely to save storage. The laptop has about 76GiB free at this check. Reuse verified files, stage large additions in existing cloud storage if needed, retain compact local aggregates, and avoid duplicating the approximately 100GiB archive. Do not provision a GPU VM, change a cloud budget, or clean another chapter's data. Storage is an engineering consideration, not a scientific sample-size rule.

**Deliverable:** held/missing/recoverable/not-observable inventory, acquisition manifest with purpose and byte estimate, and updated coverage by gauge/date/model. Core preparation can proceed while recommended additions are obtained. No agency reply is required to begin.

## 3. Build comparable conventional and learned inputs

Create complete and restricted Q/rain signatures with identical season information. Fit scaling only on eligible earlier donors. Native m³/s trajectories and same-gauge donors are primary; do not use hidden current Q or full-record p99 to anchor a trajectory. Construct paired broad-archive and EO-supported conventional references. Keep prior completed donor storms, exclude the whole query storm, and apply the same issue offset/mask to donor matching inputs.

Use all ten frozen EO encoders, four completed weekly frames primarily and completed-month snapshots for the broader-coverage comparison. Fix pre-landmark EO context through the first 24h assessment sequence, reporting its increasing age. Reuse or regenerate context based on source identity, not model performance. Preserve original versus supplemental input routes; do not pool radar orbits or mix changed reflectance/masking routes without a labelled comparison.

For TTM, shift the entire 512-observation window back to the last available Q timestamp. Standardize from that permitted history alone and recompute the established ordered-patch representation, with permitted discharge-state information alongside it. Use an identically shifted raw-history comparator to distinguish TTM from ordinary hydrograph similarity. No zero padding, hidden-tail reconstruction or unvalidated missing-value mask is needed. An interior natural gap makes that specific representation unavailable; the shorter conventional signature can still be usable. This does not turn the chapter into a TTM training or direct forecast-head study.

AlphaEarth supplies a separately labelled annual landscape comparator, particularly in cross-river tests, with ordinary area/season/geographic controls. Its previous-year coverage starts with 2018 events. Do not infer current river state from an annual embedding, require its coverage for the other models, or cross all ten EO models with TTM and AlphaEarth in an automatic fusion grid.

The optional soil/snow control uses a single declared physical-context block, with season-aware conventional matching as its reference. It can test whether an EO increment requires a learned representation rather than readily interpretable antecedent-state information. It does not replace the primary rain/Q baseline.

**Deliverable:** content-hashed signature/embedding tables and an input audit showing that every predictor was legally available under its scenario. Cache by actual last-Q timestamp/context identity rather than recompute scenario aliases.

## 4. Implement and verify one reusable simulation runner

Implement the specified release-time masks, donor reconstruction, retrieval and outcome scoring in one runner, with an independent audit. A small hand-checked case verifies plumbing; it is not a sampled scientific result or a test of whether AI deserves the full run.

Check UTC/hour-end boundaries, zero-versus-missing semantics, first-rainfall-qualification timing, equivalent delay/outage states, donor chronology, whole-storm exclusion, permitted-only normalization, source/EO dates and native-unit transfers. Verify that adding later hidden observations cannot change inputs or selections at an earlier issue. Record unsupported cases rather than silently drop them.

Rebuild outcomes from the continuous hourly Q table: the shifted rainfall landmarks can lie up to **54h later** than the old six-hour landmarks, so the old 72h response arrays are not sufficient for every new next-24h target. Likewise rebuild rain histories at every issue. This is held-data preparation, not a reason to request new years automatically.

**Deliverable:** executable runner/audit, regression checks for meaningful failure modes, and a manifest recording code/input hashes, scenario/calendar versions and seed. Internal reproducibility documentation is sufficient; no formal preregistration is assumed.

## 5. Run the eligible census and the declared supporting comparisons

Run all eligible opportunities and preserve the no-prediction ledger. Compare complete and restricted conventional, persistence/generic archive, and each EO-augmented arm. Run the TTM/raw-history and AlphaEarth controls as distinct supporting comparisons. Evaluate the optional soil/snow block once acquired; label its coverage and retrospective availability assumption. Use five distinct donor storms primarily and ten as the existing sensitivity; expose smaller available ensembles and matched-member comparisons.

Score next-24h empirical CRPS and +6/+12/+24h readouts, with magnitude, peak timing, interval coverage and width. Report per-gauge native units and area-normalized pooling. Separate: degradation from losing Q, representation increment on the same archive, and net performance including archive restriction and fallback coverage. Test EO-increment change with observation age directly.

Include NL/DE, same-gauge/cross-river and EO-age/support contrasts without claiming that all gauges or masks are independent. Use 999 reproducible paired storm/year resamples and report block counts. Compare common populations alongside larger model-supported populations. No winner-selected weights or freshness cutoffs, new architecture search, or repeated extraction until a positive result appears.

**Deliverable:** census scores, uncertainty tables, degradation/benefit-by-age figures, donor traces and coverage decomposition. Benchmark a batch before estimating total runtime; CPU retrieval/TTM and possible targeted EO extraction have different compute costs. Do not extrapolate a new multi-day extraction requirement from the previous full runs.

## 6. Review the actual situations and consolidate the evidence

For every eligible high-water case, show the observed hydrograph, what each assessment could see, the selected precedents and next-24h distribution as the feed ages. Retain nonresponses and misleading matches in the population evaluation. Inspect positive, null and harmful EO changes rather than selecting only compelling rescues. Use known severe events as explicit case studies, with existing measurement caveats and flood/H-threshold distinctions.

Answer: how much is lost when monitoring degrades, whether EO offsets it, which information is irreplaceable, what age/coverage limits usefulness, and whether a simpler fallback provides the same value. Results may favor conventional methods. Explain potential government use as contingency evidence and monitoring-restoration priorities; do not claim warning issuance, inundation prediction or reduced damage without testing them.

**Deliverable:** a consolidated research memo, reproducible figures/case browser and updated living one-pager for Brian to write from. Retain the completed full-information results and the exploratory development history.

## Readiness evidence and immediate work

[Read-only readiness receipt](reviews/limburg-monitoring-data-readiness-2026-10-28.json): complete hourly time axis shared by Q/rain, natural missing values preserved; shifted 512h histories are finite for 83,367 of 97,344 potential information states under the **older six-hour calendar**. That is input support, not quality clearance or final analysis N. The new first-observed-10mm schedule must receive its own window audit. Annual AlphaEarth keys support 1,960 old-calendar rainfall opportunities before other eligibility checks. All 468 source storms have an observed-prefix qualification timestamp; four change completed-month bin and twenty completed-week bin.

Start with the full event/release-time ledger and coverage inventory. Then retrieve the recommended land-state fields and genuine EO gaps while building the runner. No new provider delivery is essential for the core counterfactual analysis. No scarcity-performance finding has been produced by these readiness checks.
