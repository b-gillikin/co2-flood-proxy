# Controlled scarcity: first findings for Brian

29 October 2026. Internal interpretation aid, not dissertation prose. All 180 configured scoring jobs, the full matrix audit and automated evidence review completed at 01:07 EDT. This note interprets the primary paired summaries; it does not claim a completed manual examination of every analogue.

## Main result

**Simulated ground-data scarcity did not reveal an average benefit from adding the held EO embeddings to conventional analogue matching.** Across the 45 scenario/control groups, four issue offsets and ten encoders, all 1,800 primary recent/K5 total-increment point estimates are positive: higher CRPS with EO. These are correlated comparisons on the same archive, not 1,800 independent experiments.

The same direction holds in every primary future-p99 high-water comparison and in model-specific EO-supported populations. All 1,800 monthly-snapshot whole-census point estimates are positive too. Requiring better measured donor support does not create an overall EO advantage. Thus ordinary-flow dilution, unsupported-EO fallback and poorly filled donor histories do not individually explain away the primary negative result.

## What the information losses actually did

The following are changes in site-balanced conventional K5 CRPS on paired available case-mask observations, relative to the rich reference, across issue offsets 0/6/12/24h. Percentages are ratios of site-balanced mean errors, not means of case percentage errors. They are descriptive point estimates, not independently established significant effects.

| Scenario | Change in conventional error across the four offsets | EO total increment |
| --- | --- | --- |
| No current 72h local-Q history; peer/Mainstem Q and rainfall remain | +0.75%, +2.83%, +3.28%, +2.58% | Worse on average for every encoder |
| Four tributary gauges, 50% clustered gaps of mean 12h, no Maas feeds | +0.89%, +2.95%, +2.35%, +0.05% | Worse on average for every encoder |
| No current Q inputs at any tributary or Maas gauge; rainfall/season/history remain | +4.39%, +10.73%, +10.40%, +9.67% | Worse on average for every encoder |
| Local Q retained every 24h, anchored at issue; other feeds remain | −1.96%, −3.81%, −5.36%, −4.82% | Worse on average for every encoder |

Scarcity therefore does affect assessment, especially when all current discharge information disappears, but the tested losses do not destroy the rainfall/season/historical analogue reference. This is contemporary scarcity at historically monitored sites, not a never-monitored basin; complete historical response labels remain available. The reference is this algorithm, not the national FEWS.

The thinning result deserves attention. The ordered-history matcher is not guaranteed to improve monotonically with more coordinates. Thinning also changes the relative influence of the retained current/recent values versus the older history. This is an algorithmic property/confound to inspect, not evidence that collecting fewer observations improves flood management. The present outputs do not isolate a unique physical explanation.

## Nuance and exceptions

- EO's disadvantage often narrows as ground information deteriorates. There are 1,151 negative primary whole-census interaction point estimates. A smaller disadvantage is not an absolute advantage: all corresponding total effects remain positive.
- Against the same EO-restricted donor pool, ten primary whole-census representation increments are slightly negative, mainly CROMA/OlmoEarth under missing Q/rain. Their pointwise intervals include zero. The broader archive comparison removes any net gain. This supports retaining the archive/representation decomposition.
- Some diagnostic subsets have negative point estimates: net-rising high water, documented-flood overlap, selected clean donors, and a few country/common-support cells. No intervals were specified for most of those diagnostic strata. These are heterogeneous descriptive results, not demonstrated general or operational benefits. Documented-flood overlap has only 45–46 gauge–storm cases per offset, before model support. Do not promote a favorable cell into the primary conclusion.
- Primary retained donors were approximately 97.6% measured coordinates in the rich reference and 99.2% in the combined clustered-gap profile, averaged over site/method/offset diagnostics. Measured-support sensitivities raise those fractions further and retain the overall negative EO conclusion. These percentages describe selected Q-coordinate support, not perfect measurement validity.

## What this establishes

This is a completed controlled comparison that does not support the proposed EO rescue mechanism for these sites, representations, same-gauge archives and fixed 50/50 fusion. It gives information-loss profiles and identifies retrieval-design sensitivities. It does not demonstrate operational added value from EO augmentation, establish the optimal number of gauges, or show that EO/AI cannot help under other methods or applications. No positive result is promised or required.

## Numerical sources and reproduction

- `results/limburg_scarcity_v2_2026_10_28/review/paired-effects.parquet`: filter `country=all`, `readout=recent`, `effect=total_eo_increment`, and the named population; smaller/negative estimates favor EO. Matched increments and scarcity interactions are separate effects.
- `scores/{scenario}__u{offset}/paired_replicates.npz`, `conventional[..., 0]`: for the table, retain paired finite rich/scarce observations, average case-mask scores within each target site, average the eight site means, and compute `100 × (scarce/rich − 1)`. Archive units are area-normalized CRPS.
- `review/site-method-diagnostics.csv`, `coverage-ledger.parquet`, `network-placement-inventory.csv`, `analogue-traces.parquet`, `prior-method-bridge.csv`: secondary scores, coverage, geography, selected donors and prior-version bridge.
- `audit.json`, `review/manifest.json`, `pipeline.json`: completed audit/provenance. Intervals use shared whole-year blocks and coherent mask-mean resampling, with the interpretation limits in the executable protocol. No new scoring or parameter selection was performed for this note.
