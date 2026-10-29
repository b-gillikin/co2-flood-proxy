# Information-rich reference and controlled monitoring scarcity

28 October 2026, after completion of the 42-job delay/outage analysis. Brian clarifies the organizing direction: keep the same monitored NL–DE river system, historical situations and verification evidence, then reduce the information available to assess each situation. This is an internal design amendment, not dissertation prose or a report of unrun scenarios.

**Later implementation update:** the [corrected executable protocol](limburg-scarcity-executable-protocol-2026-10-28.md) and scripts 159–163 now implement the responsive comparator, separate axes, two combined profiles, donor-support checks, outcome/EO coverage and explicit uncertainty. Results are versioned under `results/limburg_scarcity_v2_2026_10_28/`; prior v1 benchmark sources are snapshotted. Earlier planned descriptions below record the design sequence, not new empirical findings.

**29 October results update:** the corrected 180-job matrix, audit and automated review are complete. [First findings](limburg-scarcity-results-2026-10-29.md) report no primary average EO advantage under the tested scarcity conditions. The design history below remains intact.

## Working question and motivation

**Can satellite AI help assess developing high water when ground-monitoring data are limited?**

The preceding wording—“when a gauge's data are late or stop arriving”—remains the question for the completed information-age component. Scarcity also concerns how much information exists, where it is observed and how complete it is. Do not narrow the overarching direction back to latency alone.

Use the relatively information-rich held NL–DE records as a controlled reference. Compare each method's deterioration and any EO contribution as access to those records is reduced. The practical question is whether EO preserves useful assessment capability when conventional monitoring is limited, and which information it can or cannot supplement. The FEWS/DRR application is monitoring contingency and prioritization of observations, without claiming operational deployment or warning benefit.

The quality and institutional context make a useful test bed, not an established explanation for limited EO gains. Different methods need not have equal reference performance. Do not relabel a negative EO increment as equivalence, or assume that poorer ground information will make EO win. The held reference has natural gaps, source uncertainty and retrospective revisions; “information-rich” does not mean perfect ground truth.

Official context: [Rijkswaterstaat's river observations and forecasts](https://www.rijkswaterstaat.nl/water/waterdata/waterstanden-en-afvoeren-rivieren) describes continuous monitoring and model-supported forecasts, including separate validated/unvalidated products. [NRW's parliamentary report on monitoring and forecasting](https://www.landtag.nrw.de/portal/WWW/dokumentenarchiv/Dokument/MMV18-2121.pdf) describes redundancy in sensors, recording, transmission, power and communications at warning gauges. These support the institutional motivation. They do not validate our algorithms or establish a national performance ranking. Held provider replies remain the direct evidence about these particular records.

## Reference and scarcity families

**Literature-based levels, subsequent review:** [Primary-source scenario precedents](reviews/limburg-scarcity-scenario-precedents-2026-10-28.md) supplies a concrete starting matrix: 0/25/50/75/100% missing inputs; separate scattered and clustered gaps; 1/3/6/12/24h observation frequency; eight/six/four/two/zero retained tributary gauges; and 3/6/9-year historical caps as supporting comparisons. It separates exact published choices from our hourly/network adaptations. Rakovec et al. (2012) provides a particularly close Upper Ourthe/Meuse precedent for observation frequency and network placement. These are recommended specifications, not implemented masks or new findings.

| Family | Information deliberately reduced | What stays available for verification | Status |
| --- | --- | --- | --- |
| Rich held-data reference | None beyond natural held-data limitations | Original held outcomes and quality evidence | Existing full-information evidence; must identify the actual inputs used by each reference |
| Age and interruption | Delivery delay or a feed ceasing to update | Original future Q | Completed 42-job component; interpretations remain specific to its inputs/readouts |
| Temporal density | Fewer observations within an otherwise continuing feed | Original dense Q | Planned; isolate density from latest-observation age, then distinguish real reporting schedules |
| Intermittent completeness | Missing individual readings or short blocks, while monitoring continues | Original dense Q | Planned; scattered and contiguous loss are distinct patterns |
| Spatial monitoring coverage | Fewer contemporaneously observed gauges or catchment observations | All target-gauge outcomes remain held privately for evaluation | Planned; requires an actual peer-gauge/context baseline before station removal can affect it |
| Historical information | Less earlier local calibration/donor history | Same query outcomes; only earlier records can become donors | Planned supporting scarcity dimension; distinguish from removing recent observations |
| Ground-input availability | Loss/coarsening of ground rainfall or selected physical-context inputs | Original Q outcomes | Planned candidate dimension, with the rainfall scheduling issue below made explicit |

Candidate degrees should cover mild, moderate, severe and absent input where interpretable. Specify the actual intervals, retention fractions, block lengths and historical windows in the executable plan, independently of which levels favor EO. Start with separate axes to explain effects, then a small number of interpretable combined monitoring situations. Do not automatically run the full Cartesian product of every input, degree, encoder and mask pattern.

## Keep the physical situations fixed

Retain the same catchments, tributaries and held Maas/Meuse context. Keep target sites and the full eligible assessment census fixed where verification exists. Removing a gauge from the observing network must not quietly remove its difficult events from evaluation. Observation eligibility and verification availability are separate.

The completed 42-job component uses local Q, local catchment rain and season. It does **not** use all neighboring gauges, all available weather variables or the Maas as matching inputs. Merely deleting unused stations or variables cannot test spatial or environmental scarcity. Build the declared richer contextual comparator from held, cutoff-safe information before degrading it; preserve a local-only reference so added context has a measurable contribution. Existing Meuse work provides source-reviewed context, not an already validated rescue mechanism. Tributaries and mainstem are not interchangeable gauges, and river connectivity does not establish a downstream-to-upstream causal effect.

Keep earlier same-gauge donors as the primary historically monitored-site comparison where local history is retained. Sparse contemporaneous monitoring does not automatically imply an ungauged basin. A shorter calibration archive is an explicit separate condition. Cross-river transfer and annual AlphaEarth can be examined with that distinction visible rather than silently changing the question.

## Make masks affect the information used

The current local discharge signature contains only Q(s), Q(s−6h), Q(s−24h), changes and observation age. Thinning an hourly record to three- or six-hour spacing can preserve all those values. Such a run could be numerically identical and would not demonstrate that dense hydrograph information is unnecessary. Confirm the feature-level effect of each proposed mask before interpreting model performance.

Use a reference representation of the observed history that can respond to changes in density/completeness, recomputed identically in every arm using only retained observations and their actual times. The choice of descriptors or permitted-history representation belongs in the next implementation plan; do not silently replace the old baseline and present results as if the methods were unchanged. Interpolation, holding the last value or another causal reconstruction is a declared baseline treatment, not recovered truth. Hidden samples and post-issue observations cannot be read during reconstruction. Genuine zeros remain observations.

For a controlled density contrast, keep latest-observation age equal across methods/conditions. For real fixed reporting schedules, vary/report schedule phase and actual age: lower frequency can also make the latest observation older. These are related but distinguishable effects.

For intermittent masks, retain the census and use reproducible repeated mask patterns shared across methods, with nested severity where feasible. Repeating masks does not create new independent storms. Retain a limited, labelled high-water-dependent missingness stress test if included; a uniform random mask alone does not represent every real failure mechanism. Groundwater, soil, weather or other optional fields are not mandatory additions simply because they exist.

Rainfall loss raises a scheduling issue: the current landmark uses observed-prefix regional rain. Either retain a declared common scheduling channel and limit the claim to scarcity of assessment inputs, or reconstruct when the degraded system could actually recognize the assessment opportunity. Do not use hidden rainfall to claim an operationally available trigger. Historical donors obey the corresponding earlier-data restrictions; verification histories remain hidden from matching.

## Comparisons and interpretation

Within each condition compare a capable conventional method, applicable simple missing-data/persistence/history fallbacks, and the same conventional information plus each frozen EO representation. Keep EO acquisition/release assumptions and coverage explicit. Do not improve EO's apparent advantage by giving its control a needlessly weak treatment of missing data, thinning only its control's archive, or dropping unsupported EO cases.

Report absolute error, deterioration from each method's rich-information reference, EO increment against the same scarce ground inputs, coverage/abstention and actual high-water cases. Retain matched and broader donor-archive comparisons. Loss curves and direct paired changes answer where any benefit appears; a different significance label at two degrees is not proof of interaction. Use the existing 24h discharge assessment task, storm/year uncertainty and no-future-information rules. Keep the natural missingness and provider-quality evidence visible.

TTM can supply a permitted-history temporal comparison if its missing-history treatment is defensible; cached complete-history vectors cannot enter masked conditions. AlphaEarth supplies a landscape/transfer comparison, not instantaneous river state. No new encoder, training project or operational dashboard is implied.

## Evidence and next implementation work

The completed delay/outage outputs remain under `results/limburg_monitoring_2026_10_28/`; audit, paired summaries and actual-case reports completed. Their primary same-gauge four-week EO comparisons do not show average improvement over conventional matching at 12/24h delays. Those findings do not answer the unrun density, intermittent, spatial or calibration-history contrasts. Completed analyses remain evidence, not failed work to erase.

Next: inventory which held inputs are actually usable by the richer reference; specify responsive history/context features and a compact graded scenario matrix; audit masks and scheduling against real event windows; then implement the new retrieval/scoring comparisons on the eligible census. Reuse valid frozen embeddings. Masking held ground data does not itself require new imagery extraction or new data acquisition. New source contexts or representations, if justified later, receive their own provenance. Soil/snow remains a supporting physical-context control and does not force a repeat of all encoder extraction.

Brian sends all emails. Provider requests can help calibrate realistic timing, interruptions, redundancy and available reporting records; they are not a requirement for controlled simulations and do not turn simulated scarcity into a measurement of actual operational failures. No new scoring or download is launched by this amendment.
