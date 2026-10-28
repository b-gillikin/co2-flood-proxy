# Limburg: high-water assessment when gauge information becomes unavailable

2026-10-28. Active internal research design, adopted following Brian's request to develop the delayed-feed/outage idea and check its literature. This updates the RQs and simulation specification; **no scarcity performance analysis has been run**. Brian writes dissertation and article prose. The [literature refresh](reviews/limburg-monitoring-literature-2026-10-28.md), [scenario specification](../config/limburg_monitoring_scenarios.json) and [held-data feasibility check](reviews/limburg-scarcity-feasibility-2026-10-28.json) accompany this document.

## Research questions and purpose

**Can satellite AI help assess developing high water when a gauge's data are late or stop arriving?**

1. How does assessment accuracy change as the last available discharge observation gets older?
2. Do frozen EO representations reduce that loss beyond the same available rainfall/discharge information and simple fallbacks?
3. Does any benefit persist after accounting for EO age, season and historical-archive coverage, and is it consistent between the Dutch and German study gauges?

The target is the distribution of discharge over the next 24 hours, including its magnitude and timing. A sequence of retrospective assessments tests monitoring resilience, with a potential FEWS/DRR application in contingency assessment and monitoring redundancy. It does not establish operational warning skill, actual telemetry-failure probabilities, avoided damages or whether operators make better decisions.

The question was developed after inspecting limited full-information EO gains. Retain that exploratory history and all completed results. This is not an independently confirmed hypothesis or a claim that EO must win under sufficiently poor monitoring. No formal preregistration is assumed.

## Situations and simulation clock

Retain the verified UTC hour-end axis and provider timezone conversions. An issue at t can use an hourly value ending at t; the first future verification value ends at t + 1h. Use an hourly rainfall-defined landmark, `t0`, then reassess at `t = t0 + u`, with **u = 0, 6, 12, 24 hours**. A station feed includes any valid backup reading delivered for that station. A primary sensor failing while its backup continues supplying observations is not a station-feed outage.

| Situation | Local discharge information available at issue time t | What the test means |
| --- | --- | --- |
| Complete reference | Readings through t | Counterfactual full-information reference; no requirement that historical records were delivered instantaneously. |
| Fixed delivery delay | Readings through t − D; D = 1, 3, 6, 12, 24h | New readings keep arriving, each D hours late. D = 0 is the complete reference. |
| Persistent stopped feed | Readings through t0, then no new readings | Last known state remains fixed; its age grows from 0 to 24h over the assessment sequence. |
| Earlier stopped feed, sensitivity | Readings through t0 − 6h | Outage precedes the rainfall landmark; age grows from 6 to 30h. |

At one issue time, delay and outage with the same last-available timestamp have identical information. Deduplicate their numerical calculation and retain both scenario labels. Their difference is the **sequence of information arriving**, not an invented one-time accuracy difference. Do not count repeated issue times or overlapping masks as independent storms.

For each scenario preserve original measurement timestamps and assign synthetic release times. Delay releases observation s at s + D; outage never releases observations after its stop time during the assessed sequence. Do not interpolate across hidden observations, relabel stale readings as current, or turn genuine zero discharge into missingness. Apply the scenario deterministically to every eligible gauge–storm opportunity; no random gauge/event sample is needed.

Rainfall remains available through each issue time under the same declared nominal availability assumption in all arms. Other station feeds remain intact. The primary comparison uses the local gauge and catchment rainfall; a peer-gauge rescue model is not silently claimed to have been evaluated. Regional network loss, rainfall loss and recovery after reconnection are separate possible extensions.

**Separate missingness from bad measurements.** Spikes, drift, saturated sensors, incorrect rating conversions and stuck readings with current timestamps require fault detection or quality assessment. This pass assumes the information unavailability is known; it does not add a fault classifier. Verification discharge still receives the existing provider/measurement review.

## Assessment opportunities: census rather than sampled floods

Use the held rainfall-episode preparation for all eight response gauges: six NL gauges and two DE gauges. The existing 468 storms produce 3,744 gauge opportunities, including nonresponses; 3,491 have the previous numeric outcome eligibility. These are preparation counts, not final supported or independent sample sizes.

The **primary calendar** is the complete subset of **126 storms** with at least 10mm already observed in one of the six core Dutch catchments during the first six hourly observations. Set t0 to the existing six-hour landmark. Qualifying rainfall is thus known at that landmark; the clock does not depend on hidden target-gauge discharge. Ten millimetres is an inherited catalogue criterion, not a warning threshold or a calibrated flood trigger. The calendar is rooted in the six Dutch catchments, so do not describe it as an exhaustive independent German-storm census.

Retain **all 468 rainfall episodes** as the broader retrospective supporting census. Some only satisfy the catalogue's rain-total criterion later; label this future-based inclusion explicitly rather than presenting it as a real-time trigger. Retain the 1,062 p99 high-water events as a separate conditional stress/case-review population. A hidden p99 crossing cannot supply the primary assessment clock.

Report every opportunity and its reason for unavailable inputs, verification, EO or donors. Do not require all ten models to support an event. Report each model's supported population and the shared intersection, and keep nonresponses. The earlier 3491 eligibility flag must be rechecked against each issue time and the new 24h outcome; do not blindly inherit a prior 72h-window exclusion.

## Permitted inputs and trajectories

At each issue, compute the existing rain summaries using only observations up to that issue: 6/24/72/168h totals and the preceding-24h maximum hourly rain. Let s be the last available local Q timestamp. Use Q(s), Q(s−6h), Q(s−24h), their observed changes, and the known observation age t−s. Require the actual retained feature history to be valid, not the entire 512h TTM window. An outage does not erase older local records.

Use **same-gauge historical donors as the primary local-feed comparison**, because this situation concerns a historically monitored site. Transfer their future trajectories directly in m³/s. Do not anchor them to hidden Q(t), rescale them using the target's future peak or borrow full-record p99 as a supposedly known input. Same-gauge evaluation also removes a route for EO gains to arise merely from identifying the river.

Cross-river donors remain a supporting transfer check, retaining the original river/country labels. If executed, transfer specific discharge using documented catchment areas: `q_mm_h = 3.6 * Q_m3_s / area_km2`. This is an area-based assumption to test, not hydrological equivalence. Do not silently substitute the earlier target-p99 transfer. Show within-gauge m³/s results and pooled area-normalized scores so large gauges do not dominate by units alone. Existing p99 and current H1–H3 thresholds may label verification cases; they are not simulated warning decisions.

Use eligible earlier completed storms from the full held 468-storm reservoir for historical donors; the 126-storm primary **query** calendar does not discard otherwise compatible historical precedents. Historical catalogue membership is known by the query issue; it must not supply future information about the query.

Every donor uses the **same relative issue offset and availability restriction** as its query when computing matching features. Its complete response is a historical label, not a ranking input. Donors must be from earlier completed storms, their entire relevant response must end before the query issue, and the query's whole regional storm is excluded at every issue. Scaling, feature normalization and any distance calibration use eligible prior donors only. No later part of the same storm enters through another gauge or issue time.

Compare five distinct donor storms with equal ensemble weights; retain ten as the existing supporting sensitivity. With fewer than five, record the available ensemble and its size rather than hide the case; paired five-member performance uses cases with sufficient common support and separately reports applicability. No new success/failure gate is created.

## Comparisons and EO context

For each legal information state compare:

1. Complete-information conventional matching **with ordinary sine/cosine season information**, rebuilt on the same opportunities and donor policy.
2. Availability-aware conventional matching with the restricted Q signature, current observed rain and **the same season information**.
3. The restricted conventional signature without season as a supporting control, to identify what ordinary seasonal information contributes.
4. The season-aware restricted comparator (2) plus each of the ten held frozen EO representations.
5. Persistence of the last actually available Q, and an unranked storm-balanced eligible historical distribution.

Use the established prior-only robust feature scaling. For EO fusion use equal weights on the squared, prior-pair-distance-normalized conventional and EO distance blocks. Carry the season control identically into the comparator and augmented arm; use robust-scaled sine/cosine features in the conventional block. Constant feature dimensions contribute zero distance. No validation-on-query weight search, new encoder, classifier or model training is added.

**Four completed weekly frames** are the primary antecedent-context readout; the **last completed monthly snapshot** is the declared broader-coverage sensitivity. Choose these roles by temporal interpretation, not whichever has the best old score. Twelve-month representations and AlphaEarth remain existing background/context results; no additional primary factorial is implied. All ten encoders remain eligible; temporal ordering versus mean-frame adapters retain their documented differences.

Hold each pre-t0 EO context fixed during the first 24h assessment sequence and increase its age accordingly. Verify that every source acquisition/bin ends by t0. Bin end is not acquisition age, and acquisition time is not proof of product release time. Report actual acquisition ages and quality support where held; mark unavailable release timestamps as unknown. These are acquisition-safe retrospective reconstructions under nominal availability, **not an as-issued replay**. Document checkpoint pretraining periods/possible study overlap as another limit on prospective claims. No new imagery extraction is needed for the held readouts.

Keep the broad conventional donor archive alongside each EO-supported restricted archive. On identical queries use the same season-aware conventional specification on broad and restricted archives, then decompose: archive restriction, EO increment within the restricted archive, and net difference versus broad conventional matching. Full-versus-sparse degradation also keeps season information identical. Fix compatible donor populations across delay levels for the paired degradation curve; report natural-support applicability separately. Where EO is absent, retain the available conventional fallback and count it in end-to-end coverage rather than delete the opportunity.

Complete-history raw-hydrograph/TTM vectors contain the hidden values. Preserve them as earlier full-information references, but **do not reuse them as sparse-input methods**. Recomputing a permitted-input TTM route would be a separate, justified addition; it is not required for this comparison. The older storm-response matcher also contains realized future rainfall and cannot be used unchanged.

## Outcomes, uncertainty and interpretation

Predict/distribute the next **24 hourly Q values after each issue**, with +6/+12/+24h readouts. This stays inside the held 72h response for the proposed issue offsets. Primary loss is mean hourly empirical CRPS over those 24 hours. Report m³/s by gauge and area-normalized pooled loss; show mean-trajectory RMSE, peak-magnitude and peak-time errors as secondary diagnostics. Evaluate interval coverage and width empirically; a five-member range is not automatically a calibrated confidence interval. Do not reinterpret the existing score helper's p99-based `Q >= 1` duration or peak-normalized shape metrics as native-unit flood diagnostics.

Estimate degradation versus the complete conventional reference, paired EO increments versus season-aware restricted conventional matching, and net EO performance versus the broad restricted conventional archive. Test how the EO increment changes with observation age directly. Significance at one delay and nonsignificance at another do not establish an interaction. A recovered-loss fraction is secondary and undefined unless the full-versus-sparse denominator is positive; absolute loss differences remain primary.

Use 999 reproducible paired joint storm/year resamples, retaining all gauge/issue/scenario observations belonging to a storm together; report storm- and year-based intervals and the number of blocks. Aggregate issue offsets and gauges with explicit equal weighting before interpreting pooled summaries. Show country/gauge estimates without treating eight gauges as a large independent catchment sample. Repeated masks/assessment times do not increase independent N. Report all ten encoder estimates; do not declare a winner from whichever uncertainty interval excludes zero.

Inspect actual high-water cases across the sequence, including missed rises, false reassurance, nonresponses and quality concerns. Separate hindsight-defined outcome subgroups from information available at issue time. No reliable transition from high water to inundation is inferred from discharge alone.

## What is ready and what remains

Held rainfall, gauge histories, catchment geometry, quality notes and finite rainfall-linked EO embeddings support preparation without another acquisition. The feasibility receipt shows monthly snapshot support for 2,191–2,682 currently outcome-eligible rainfall opportunities per model; stricter early-rain support is 552–741 before new donor/history checks. Weekly support is smaller. None of these counts is a scarcity result.

Next implementation: build the release-time/issue ledger and native-unit histories; audit clocks, legal inputs, zero/missing semantics, donor completion and EO dates; run a transparent end-to-end case to verify plumbing, then the entire eligible census. Do not tune the design to that case's AI gain. Publish the complete scenario/support ledger, input/code hashes, scores, uncertainty and reviewed cases. Simulation outcomes may favor conventional methods or show that EO cannot replace recent Q.

Design consistency checks and provider-source hashes are recorded in [the check receipt](reviews/limburg-monitoring-design-checks-2026-10-28.json); these do not validate an unimplemented runner or constitute a scientific gate pass.

No new data request, fieldwork, interview, dashboard, routing/hydraulic model, fine-tuning task or operational acceptance threshold is added. The policy contribution is evidence on information substitution and contingency limits in a warning chain; operational adoption remains a separate evaluation.
