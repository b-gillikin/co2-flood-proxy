# Limburg: historical analogue assessment — synthesis and Meuse test

Completed 2026-10-27. Internal research readout for Brian, not dissertation prose. Implements the [three-workstream plan](limburg-synthesis-archive-meuse-plan-2026-10-27.md). All declared comparisons are complete; unfavorable and undefined results are retained. Brian writes the chapter/article.

## Main conclusion

The chapter is best supported as a retrospective evaluation of the information supplied by historical high-water analogues. Conventional matching already supplies useful response-shape information. Learned representations have modest or conditional increments, and an apparently strong result can depend on which historical evidence its data requirements remove. The new Meuse test does not establish a distributional advantage from adding mainstem state under the declared configuration.

The empirical question is: **Can AI-selected historical events improve assessments of how high water develops in the Meuse basin, beyond conventional hydrological analogues?** The current answer is conditional and endpoint-specific. It does not establish an operational warning model, a universal encoder winner, or a rule that reliably identifies misleading analogues before the outcome.

## 1. One evidence map, rather than another search for a question

The executed [evidence map](../results/limburg_assessment_2026_10_27/review/evidence_map.json) contains 12 claim records with populations, quantitative anchors where applicable, source documents, limitations and exploratory status. Read it alongside the [complete query/donor browser](../results/limburg_assessment_2026_10_27/review/analogues.html) and [tables/figures](../results/limburg_assessment_2026_10_27/review/index.html).

| Question | Completed evidence | Supported interpretation |
| --- | --- | --- |
| Does historical matching help? | Conventional/raw comparisons against the same eligible generic archive | More similar individual subsequent shapes; aggregate trajectory estimates are less consistently improved. |
| What does AI add? | Broad Q-history TTM result and final ten-encoder comparisons | TTM's individual-shape increment is modest; EO effects depend on archive, population, outcome and transfer setting. |
| Are the implied distributions useful? | Earlier full-census CRPS/coverage study for conventional/raw/TTM/AlphaEarth; new Meuse study | Five-donor TTM has no clear general distributional increment. Ten-donor improvements over a generic archive are also achievable conventionally. The earlier distributional study is not a final all-ten EO distributional comparison. |
| Can storm/state differences explain divergence? | Completed October 15 storm-response census, including nonresponses | Local phase and subsequent rain expose misleading matches. General peer-state and repeat-pulse results are unfavorable or unstable; no new flood-generating mechanism is established. |
| What happens in severe episodes? | Source-bounded register and whole-event review | Missing precedents, retrieval misses, insufficient extreme members, averaging and evaluation-window anchoring are distinct failures. Two scored pre-flood continuous-response queries do not establish their population frequencies. |
| Does Meuse context improve the assessment? | New controlled primary/coverage-sensitivity comparisons | It adds interpretable basin context, but no clear primary distributional benefit to conventional matching; the two-site addition worsens TTM's primary score. |

The development was exploratory. The plan for this pass preceded its new calculations, but the underlying archive and many outcomes had already been inspected. The evidence does not become an untouched confirmatory test through a new label.

## 2. Representation increments and archive restrictions are now separated

For each fixed query, the new comparison holds the target and response estimator constant:

1. A baseline uses its broad compatible prior archive.
2. The same baseline is recomputed on the exact archive supported by the EO representation.
3. EO+TTM retrieval uses that same restricted archive.

The restriction effect and representation increment sum exactly to the total difference. Query exclusion remains a separate applicability result. The analysis includes all ten encoders, three readouts, their own available populations and the all-ten intersection, Q-only and corrected rainfall-complete settings, five/ten donors, other-river and quality checks. It contains **2,210,316 paired metric/component records**, not that many independent events.

### A material qualification to the earlier AnySat result

On the same **111 German snapshot queries**, mean-trajectory RMSE in Q/p99 is approximately:

| Method and donor archive | Error |
| --- | ---: |
| Conventional matching, broad compatible archive | 0.2731 |
| Conventional matching, all-ten EO-supported archive | 0.3009 |
| AnySat+TTM/state, that EO-supported archive | 0.2674 |

| Paired difference | Estimate | Storm interval | Year interval |
| --- | ---: | --- | --- |
| Restrict conventional archive | +0.02776 | [+0.01270, +0.04379] | [+0.01653, +0.04192] |
| AnySat+TTM versus restricted conventional | −0.03350 | [−0.05038, −0.01728] | [−0.05602, −0.01026] |
| AnySat+TTM versus broad conventional | **−0.00574** | [−0.02267, +0.01172] | [−0.02074, +0.01354] |

Thus the earlier approximately 11% improvement is valid **against the restricted conventional reference**. Compared with conventional matching allowed its broader archive, the point improvement is about 2.1% and both intervals include zero. The own-model-available AnySat archive gives the same qualitative result: DE total curve difference −0.00454, storm interval [−0.02172, +0.01312]. This does not establish equivalence, but it weakens an unconditional practical-improvement claim.

Restriction effects are not uniformly harmful. For example, pooled own-population snapshot conventional curve differences are −0.00675 for the CROMA/OlmoEarth-supported archives and +0.00666 for several optical-supported archives. These are differences under stated archive policies, not proof of a causal effect of imagery absence or that older events are always useful. The complete effect/interval table retains these distinctions rather than selecting a new model winner.

Observed prior H3-positive and unknown-label donor counts are retained. They use the existing current-threshold, next-72h observation labels; an unknown German label is not a negative, and an episode's later H3 transition need not fall inside that donor response window.

## 3. Focused Meuse test

### Specification and population

The [executable specification](../config/limburg_meuse_comparison.json) declares four features: Sint Pieter and Venlo prior-year discharge ranks and their 24-hour changes. Existing source-centred support is cutoff-safe; ordinary controlled values are used without interpolation or stale-state filling. Feature scales come from eligible prior candidates. Baseline and Meuse blocks receive fixed equal squared-distance weight; no feature or weight search was performed.

Conventional rainfall/discharge and TTM/state are each compared with themselves plus Meuse context on identical queries and prior donor pools. The full held inventory remains **1,062 events**. The broad actual rainfall-feature-complete cohort has **836 eligible events / 830 with prior donors**. Two-site context has **366 eligible / 364 scored**, comprising 284 NL and 80 DE queries. Sint Pieter-only context has **717 eligible / 711 scored**, comprising 513 NL and 198 DE queries. These are overlapping populations; the German gauges are on the Wurm, not a national sample.

Primary outcome is mean exact empirical CRPS over the next 24 hours; lower is better. This scores the specified finite analogue distribution. Current p99 onsets, retrospective normalization, finalized data and inherited complete-72h verification eligibility remain unchanged. The test concerns continuation after observed high water, not all-year flood detection or a false-alarm rate over ordinary hours.

### Main results: five donors, pooled/all-river

| Context and baseline | Queries | Baseline CRPS on restricted pool | With Meuse | Difference | Storm interval | Year interval |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| Both sites; conventional | 364 | 0.25615 | 0.25499 | −0.00116 | [−0.01153, +0.00923] | [−0.01242, +0.00505] |
| Both sites; TTM/state | 364 | 0.25758 | 0.26981 | **+0.01223** | [+0.00156, +0.02286] | [+0.00048, +0.02149] |
| Sint Pieter only; conventional | 711 | — | — | +0.00926 | [−0.00047, +0.01947] | [−0.00056, +0.01606] |
| Sint Pieter only; TTM/state | 711 | — | — | −0.00133 | [−0.01142, +0.00801] | [−0.00976, +0.00713] |

No primary distributional advantage is established for conventional matching, while adding both sites worsens TTM's primary score under both uncertainty views. The larger Sint Pieter-only population does not provide a replacement positive primary result.

There is a secondary conventional trajectory improvement with two-site context: RMSE difference −0.01404, storm interval [−0.02644, −0.00174], year [−0.03527, +0.00230]. Peak, donor timing and duration improvements remain uncertain in the pooled main view. Preserve that endpoint distinction rather than declaring the whole Meuse comparison either successful or useless. All ten-donor, country, other-river and quality results are in the tables.

### Coverage and fallback

Requiring two-site data restricts conventional CRPS by +0.01121 on the 364 paired queries before the Meuse feature is used. Its total context-strategy difference from broad conventional is +0.01005, with storm/year intervals including zero. The TTM total difference is +0.01684, with both intervals above zero.

The simple fallback policy uses Meuse retrieval where supported and the original broad baseline elsewhere. It retains all **830 scored rainfall-complete queries**. Two-site conventional fallback has CRPS change +0.00441, storm [−0.00167, +0.01060]; TTM fallback +0.00739 [+0.00150, +0.01321]. Fallback prevents silent case loss; it does not rescue the primary result. These are declared retrospective policy comparisons, not calibrated operational decisions.

## 4. Actual matches and source limitations

The browser includes every scored main-view rainfall query, selectable conventional/TTM comparisons, both context definitions and five/ten donors. It shows broad baseline, restricted baseline, Meuse-selected members and observed response. A separate 10-case panel set retains the existing severe/recovery cases and deterministically includes the largest improvements, largest degradations and smallest primary-score changes. This outcome-informed selection illustrates the numerical census; it is not its denominator.

Voer May 2024 remains poorly represented at its extreme peak. Worm July 2014 has no eligible two-site context and retains its broad baseline. Eyserbeek July 2021 is displayed as context with its original eligibility limitations rather than inserted into the scored sample. A small next-24h CRPS change can coexist with very different +60h trajectories; that is a consequence of the declared endpoint, not an improvement established over the whole flood.

There are 73,278 eligibility rows covering the full inventory for each declared baseline/context view. They retain history/outcome/measurement fields, feature applicability, prior donor support, observed-positive/unknown H3 labels and explicit reasons. Missing values are not no-flood observations.

## 5. What this means for the chapter

The strongest synthesis is about the information and limitations of historical analogues. A representation can improve matching on a common archive while contributing little practical increment relative to a conventional method allowed more historical evidence. The AnySat result makes this concrete. The Meuse comparison adds a clear negative/qualified result to a physically motivated hypothesis; it does not supply a reason to search new weights until it wins.

The FEWS/DRR relevance is the quality of evidence used to interpret a developing event: the precedents represented, the severe histories omitted, different local/mainstem conditions, and the danger of treating a small analogue ensemble as an assured range. Damage reduction, evacuation benefit, physical backwater and as-issued warning skill were not evaluated. They are not new requirements for this retrospective chapter.

All three planned workstreams are complete. Further modeling is not required to make this evidence reportable. Brian can now decide how prominently to present the comparative benchmark and its archive-support qualification, with supervisors, while writing the chapter.

## Validation, reproduction and resources

- Full suite: **359 passed**; lint and diff checks clean.
- Independent audit: 22 manifests / 85 output hashes; 194,847 selected donor rows checked; 40,128 independently reconstructed CRPS scores; 63 checks against frozen baseline distances; 2,210,316 decomposition identities; independent reproduction of 9,999 primary bootstrap draws and cutoff-poison checks.
- All 15 figures visually inspected; browser JavaScript syntax checked and local links verified.
- The original bootstrap completed before its planned optimization handoff. Its outputs were preserved and compared with the joint-outcome implementation: all **127,872 interval rows** agree within 1e-12; maximum bound difference 1.43e-14. Optimization changes arithmetic scheduling only. The joint pass took about 38 seconds; completed retrieval/scoring was reused.
- Reproduction: script 146 with `--stage benchmark`, then `--stage baselines`, `--stage archive`, `--stage meuse`; script 149 for the equivalent faster joint intervals; script 147 for reporting; script 148 for independent audit. `--stage all` in 146 also reproduces the same estimands, using its original slower interval path if no completed interval stage exists. Existing local `PROJ_DATA` and a writable `MPLCONFIGDIR` are required as in earlier runs.
- Outputs: `results/limburg_assessment_2026_10_27/`; new result footprint about 100 MiB including the preserved original bootstrap reference. No encoder extraction, model training, new download or other chapter's data change occurred. Compact [completion receipts](reviews/limburg-assessment-2026-10-27/README.md) retain the numerical audit and primary results in the repository.
