# Developing EO-assisted high-water assessment under sparse monitoring

2026-10-28. Research concept and internal design advice for Brian. This develops the proposed scarcity direction; no new retrieval/scoring experiment was run and no active RQ was automatically replaced. The accompanying [read-only feasibility record](reviews/limburg-scarcity-feasibility-2026-10-28.json) checks held input support, not performance. Brian retains all dissertation writing.

## Scientific proposition

The useful hypothesis is conditional: satellite representations may contribute little when recent hydrometeorological observations already describe the river, but may reduce the loss of assessment quality when that information is delayed or unavailable. The experiment should estimate that relationship, not assume EO will eventually win if the conventional reference is weakened enough.

Suggested main question: **Do EO foundation-model representations reduce the loss of high-water assessment accuracy when recent river observations become delayed or unavailable?**

Supporting questions:

1. Does EO compensate for missing recent discharge state, missing discharge trends, or unavailable rainfall information, and are those different problems?
2. How does any benefit vary with assessment horizon, age of satellite information and catchment/event context?
3. Does the gain survive realistic archive/coverage constraints and simpler geographic/seasonal explanations?

The completed full-information comparisons can form the reference condition for this main experimental axis. Developing the question after seeing limited full-information gains must be disclosed; it is not an independent confirmation of an untouched hypothesis. The project need not produce a crossover favoring EO to be informative.

## Why this is connected to FEWS/DRR

A concrete use case is an analyst assessing a storm while a local gauge feed is delayed. Historical monitoring and calibration may exist, rainfall estimates may still arrive, and the location/catchment remain known. The question is how much situation-assessment quality can be preserved with other sources.

Potential policy relevance includes monitoring redundancy, contingency arrangements during outages, the limits of satellite substitution and prioritization of observations for restoration. No monetary value, evacuation benefit or reliability of an operational warning system follows automatically. Those are implications for later evaluation, not requirements to undertake this retrospective study.

Existing RADOLAN rainfall is itself radar-based information. The comparison is learned satellite representations versus or alongside conventional hydrometeorological signatures, not a pure division between all remote sensing and ground data.

## Literature that motivates, rather than predetermines, the experiment

| Source and access | What it supports | What it does not establish |
| --- | --- | --- |
| Berthet, Ramos, Perrin, Andréassian and Loumagne (2009), *Can discharge assimilation methods be used to improve flood forecasting when few data are available?* [IAHS primary PDF](https://iahs.info/uploads/dms/14820.16-94-100-333-05-4103_Berthet-corr.pdf). Abstract, methods and delay/lead-time design inspected. | Examines how the value of discharge updates changes with observation delay and forecast lead across 178 French catchments. This directly motivates observation-age degradation curves. | Their rainfall–runoff assimilation system is not our analogue method; their use of realized future rainfall does not authorize it as an input here. Their delay ranges are not mandatory levels. |
| Mbuvha et al. (2023), *A novel workflow for streamflow prediction in the presence of missing gauge observations*. [Publisher](https://www.cambridge.org/core/journals/environmental-data-science/article/novel-workflow-for-streamflow-prediction-in-the-presence-of-missing-gauge-observations/3ACF2CC1DB30EA4DF5B37F109617FC71). Abstract, motivation, data and workflow inspected. | Missing observations are an actual hydrological application problem; the paper combines global-flow-based imputation with daily forecasting at ten Benin stations. | It is not evidence that our EO embeddings can observe hourly flood state or a reason to import their imputation/training chain. |
| Ou and Zheng (2026), *Foundation-Scale Satellite Embeddings Reframe Hydrological Generalization as a Representation Problem*. [Publisher](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2025GL121604). Abstract and plain-language summary inspected. | Supports satellite embeddings as potentially useful catchment representations for temporal/spatial generalization in Australian experiments. | Spatial generalization and landscape information do not demonstrate compensation for a six-hour local telemetry outage. |
| Fisher, Pan and Wood (2020), *Spatiotemporal assimilation–interpolation of discharge records through inverse streamflow routing*. [Article](https://hess.copernicus.org/articles/24/293/2020/). Publisher abstract/summary inspected. | Sparse observations can also be supplemented with river-network information, a reminder to consider ordinary available alternatives. | This is not justification for adding a routing model or claiming that our Meuse features estimate physical propagation. |
| Wendi et al. (2019), Charpentier-Noyer et al. (2023), Lerch et al. (2017), and Busker et al. (2026) | The earlier [literature reassessment](reviews/limburg-analogue-question-literature-reassessment-2026-10-27.md) supports hydrograph evaluation, hydrological timing, non-event-inclusive verification and regional warning interpretation. | A new scarcity analysis does not erase earlier negative results or transform a retrospective evaluation into an as-issued forecast replay. |

The new idea is a focused experiment, not a demonstrated globally empty literature gap. Possible differentiation is the comparison of frozen EO representations for historical-event assessment across controlled monitoring loss, information age and archive support in this river system.

## Corrections to the initial brainstorm

**Trimming the 512-hour discharge history to 168, 72 or 24 hours does not weaken our conventional reference.** Its discharge inputs are Q at cutoff, −6h and −24h and their changes; its longest rainfall signature is 168h. Such trimming mainly changes TTM's inputs. Scarcity should remove or delay information actually used by the baseline.

**The held EO is not same-hour flood observation.** It comprises the last completed month, twelve completed monthly frames or four completed weekly frames. Across held rainfall opportunities the median age of the latest calendar-bin end is about 14.77 days for monthly context and 3.38 days for weekly context; actual acquisitions can be older. Some native temporal encoders use ordered sequences, while other adapters average frame embeddings. Surface/catchment context is plausible; a direct reading of water level during a new outage is not established.

**Landscape and current-state information should be distinguished.** AlphaEarth or simple static attributes can supply landscape controls; more temporally detailed EO might add antecedent-condition information. Neither is presumed to observe the current river. This is an interpretation of possible mechanisms to test, not an established reading of embedding dimensions.

**EO-only retrieval already exists.** Its lack of general full-information advantage is retained. The new question is the change in relative value as hydrometeorological information is lost, including what cannot be replaced.

## Different kinds of scarcity

| Kind | What changes | Interpretation |
| --- | --- | --- |
| Recent gauge delay/outage | Hide Q after cutoff minus N hours | A historically monitored site with an interrupted feed; the most direct first experiment. |
| Sparse recent gauge state | Retain current Q but remove recent trends, or retain no recent Q | Which parts of the recent hydrograph provide the information EO might complement? |
| Missing/coarse rainfall | Hold the gauge condition fixed and remove/coarsen rainfall inputs | A separate observation family; do not conflate it with gauge delay. |
| Short historical local record | Remove earlier local labelled events or local calibration information | Archive/learning scarcity, different from a temporary feed failure. |
| No local gauge history | Withhold local calibration and donor labels entirely | Pseudo-ungauged transfer; current target p99 scaling/event timing cannot quietly remain privileged inputs. |
| Sparse EO acquisitions | Remove frames or vary actual age/coverage | A separate source-support question, potentially requiring re-encoding. It is not implied by the first gauge-loss experiment. |

The first three can be studied using held observations and embeddings. The last three are possible extensions to decide on, not an automatic factorial queue.

## Recommended first experiment: age of local discharge information

Use fixed delay levels such as **0, 6, 12 and 24 hours**, with one separately labelled no-recent-Q endpoint. These are proposed hydrologically interpretable design levels to specify before execution, not levels selected for an AI crossover.

For delay N, remove local discharge after t−N. Conventional Q features can use the last available Q and observed changes ending at that time; for example Q(t−N), Q(t−N−6), Q(t−N−24). Label their age correctly rather than treating stale Q as current. Keep rainfall available up to t in this experiment. Apply the equivalent input restriction at each historical donor's assessment time so comparison does not use a donor's hidden contemporary Q for ranking. Completed historical responses remain labels.

There are four core comparison roles:

1. Full-information conventional matching, to establish reference performance on the same queries.
2. Delay-aware conventional matching using only retained inputs.
3. Exactly that retained information plus each frozen EO representation.
4. A simple fallback, such as persistence of the last actually available Q and a storm-balanced historical distribution, so a sparse comparator is not arbitrarily handicapped.

An EO-only endpoint can be retained as a limit case; no-Q with rainfall still available is rainfall+EO, not EO-only. Calendar, known location, basic catchment size and seasonal information should be available to appropriate simple controls too. Otherwise an apparent EO gain may only recover river identity or time of year. The existing area/identity controls provide a starting point. Within-river comparisons help examine dynamic information separately from geographic donor preference; they are not substitutes for broader transfer checks.

The fixed full-history TTM vectors contain values that a delay scenario hides. They cannot enter that scenario unchanged. A TTM robustness comparison would need permitted history only and documented missing-input handling; it is not needed to establish the main conventional-versus-EO compensation comparison.

## A better assessment calendar is already held

The source preparation covers **1,062 high-water events** and **3,744 storm–gauge opportunities from 468 rainfall episodes**, across the eight response gauges. Of the latter, 3,491 have the existing numeric outcome eligibility. The storm calendar includes nonresponses and does not define its six-hour landmark using a target gauge crossing.

This matters because an experiment that hides Q(t) but uses a p99 crossing at t to decide when to assess would supply privileged gauge information through its clock. The high-water catalogue can still support a conditional stress test, but does not establish detection without a live gauge.

The existing rainfall catalogue provides a larger, gauge-independent assessment calendar. It is retrospective: its qualifying storm-total criterion uses rainfall beyond the initial landmark for some storms. For a stricter available-rainfall-defined subset, **126 of 468 storms** already have at least 10mm in a core catchment within the first six observations. These can supply an available-at-landmark sensitivity without redefining timing from future discharge. This is an option for claim precision, not a new rule closing the broader retrospective study.

The read-only join of finite held embeddings to rainfall observations finds monthly snapshot support for 2,357–2,889 storm–gauge opportunities per encoder, of which 2,191–2,682 retain current numeric outcome eligibility. The early-rainfall subset retains 552–741 outcome-eligible supported opportunities per encoder. These counts precede input histories, past-only scale checks, donor availability and scenario rules. They are not independent catchments or final sample sizes.

Thus this direction can use the rain-defined observations already represented by the completed extraction. No new EO inference or acquisition is implied simply by changing the observation calendar. New signature preparation, legal prior-donor reconstruction and scoring would still be required. Do not reuse the older storm matcher's realized future-rainfall features for a cutoff-information experiment.

## Calibration, verification and practical interpretation

Temporary monitoring loss can assume a calibration scale known before the outage. A permanent ungauged-site claim cannot borrow the target's hidden full-record p99, rating history or current discharge. In particular, current Q cannot secretly anchor transferred trajectories or a persistence prediction when it has been masked.

Retain observed outcomes for verification only and keep input masking separate from naturally missing/uncertain truth. The first experiment can be labelled a retrospective assessment under simulated monitoring loss using declared normalization assumptions. If a stronger deployment-like claim is sought, choose the scale/reference period using past data and specify an available-information trigger. Those choices refine what is claimed; they do not make the existing data worthless.

Keep the donor archive fixed across scarcity levels for the initial information comparison. Preserve the new distinction between broad conventional archives and EO-supported ones: report both sparse conventional on its full compatible archive and its matched-archive control. This prevents an apparent compensation benefit from actually being a donor-availability artifact. Report the own-model population and the common intersection separately, and use baseline fallback where EO is unavailable for full-population applicability.

## Quantities worth learning

- **Degradation:** change in an assessment loss relative to the full-information conventional reference.
- **EO increment at each delay:** paired sparse+EO minus sparse conventional error, with the same observation restriction and verification occasions.
- **Interaction:** whether that increment itself changes as observations become older. A negative interval at one delay and an interval containing zero at another is not, by itself, a test of their difference.
- **Recovered loss:** (sparse loss − sparse+EO loss)/(sparse loss − full-information loss), only when the denominator represents a positive loss. Leave it undefined otherwise; do not clamp negative or above-one values. Absolute paired effects remain more stable than ratios near zero.
- **Availability:** share of the full eligible observation calendar where the approach can issue an assessment; separate missing imagery and missing conventional inputs from verification gaps.

Use the established next-24h empirical CRPS as a candidate main distributional endpoint, with +6/+12/+24h scores and existing peak/timing diagnostics. Plot delay against assessment horizon: an observation that is six hours old and a target 24h later differ from immediate state estimation. EO age is an explanatory dimension available from the provenance, not a reason to scan unbounded freshness thresholds.

All eligible opportunities enter numerical evaluation. Deterministic outages at fixed relative times need no random event sample. If random loss patterns are added, pair identical masks across methods; repeated masks do not create new independent storms. Use joint storm/year uncertainty and report the limited number of watercourses. Keep the selected role of monthly versus weekly context explicit; do not report whichever readout wins as a prospective primary.

## Interpretation and possible contribution

Several outcomes would be informative:

- EO contributes little with complete monitoring but compensates under some delays: evidence for conditional complementarity.
- Simple season/location controls match the benefit: the value may not require a foundation model.
- Gains depend on unusually fresh scenes: timeliness limits the practical application.
- EO cannot compensate even as gauges become stale: these held representations do not replace the missing dynamic state under the declared task.
- EO helps on its supported subset but archive/coverage loss removes the net advantage: useful distinction between representation skill and reliable observation-system support.

The dissertation connection is evidence about the resilience and limitations of AI-assisted high-water assessment when monitoring degrades. It need not promise a complete FEWS. The research should estimate which information is complementary, substitutable or indispensable in this setting, while preserving the earlier full-data results and their development history.

## Next concrete preparation

A compact scenario specification should name the primary assessment calendar, delay masks, legal retained features, calibration treatment, donor archive, simple controls, EO readout roles and outcomes. Then audit the new case/signature joins and run one transparent scenario end-to-end before the full census. This is plumbing/validity verification, not a result-based permission gate. The remaining work is data preparation and CPU retrieval/scoring; the core proposal does not require more imagery, encoders, interviews or field measurements.
