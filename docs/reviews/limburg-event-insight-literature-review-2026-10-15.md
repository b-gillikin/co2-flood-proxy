# Limburg: paths from analogue scores to event insight

2026-10-15. Targeted literature review and internal research aid for Brian,
not dissertation prose, a new protocol, or an empirical result. Recommendations
below are proposals; the active RQ, analysis and reported unfavorable results
are unchanged.

## Assessment

There is a credible path to richer insight. The strongest next question is
not whether another representation improves the average nearest-neighbour
score. It is whether we can explain **when apparently similar events diverge,
and when another tributary becomes a useful comparison**. This connects
individual events, inter-river relationships and escalation within one study.

The existing analysis supplies useful baselines and measured limitations.
It does not settle this question: its principal unit is a gauge's high-water
episode and its outcome is retrieval/response agreement. A regional storm's
spatial forcing, nonresponding gauges and changes in relationships through
that storm are not equivalent to another event-level similarity score.

The literature already establishes that rainfall, antecedent state and
catchment characteristics interact. A contribution must establish something
more specific about the timing, transferability or failure of comparisons
in this river system. No search here establishes that the proposed study is
globally unique, and a hydrological breakthrough cannot be promised.

## Search and evidence scope

Reviewed the chapter bibliography, literature bridge and foundation-model
reviews; checked selected Mendeley records; searched fresh primary research
on rainfall-runoff event identification, event-generating processes,
dynamic hydrological similarity, spatial rainfall organization, river-network
synchrony, confluence timing and storm/state counterfactuals. Publisher HTML,
abstracts and the Durham author repository were used. Depth varies: this is
a targeted synthesis, not a systematic review or a full-text audit of every
related publication. Sources below were selected for a design implication,
not simply for mentioning AI or floods. Retrieval date: 2026-10-15.

## Selected literature and implications

| Source | Evidence relevant here | Implication and transfer limit |
| --- | --- | --- |
| [Tsiokanos et al. (2024), Flood drivers and trends: Geul](https://hess.copernicus.org/articles/28/3327/2024/) | Locally relevant event analysis links flooding to prolonged/extreme precipitation and wet initial conditions. | Merely showing that wetness matters in the Geul would repeat existing knowledge. Focus on subdaily trajectories, differences between events and transfer across rivers. |
| [Tarasova et al. (2020), A Process-Based Framework to Characterize and Classify Runoff Events](https://doi.org/10.1029/2019WR026951) | Uses precipitation and catchment-state indicators to classify events across German basins, with distinct response characteristics. | Define explanatory groups from forcing and initial state before comparing outcomes. Do not cluster on future peak and then claim the resulting peak difference is a discovery. Their complete variable set is not a data requirement here. |
| [Giani et al. (2022), An Objective Time-Series-Analysis Method for Rainfall-Runoff Event Identification](https://doi.org/10.1029/2021WR031283) | Joint rainfall/runoff event identification addresses sensitivity to segmentation and temporal resolution. | A storm-response catalogue differs from p99 episodes. Segmentation needs an explicit rationale; this paper is an implementation candidate, not a mandatory additional algorithm. |
| [Loritz et al. (2018), On the dynamic nature of hydrological similarity](https://hess.copernicus.org/articles/22/3663/2018/) | A modeled hillslope ensemble exhibits time-varying functional similarity despite fixed landscape properties. | Motivates testing state-dependent analogue usefulness. It does not demonstrate that observed Limburg tributaries behave this way or validate TTM embeddings as physical states. |
| [Zoccatelli et al. (2011), Spatial moments of catchment rainfall](https://hess.copernicus.org/articles/15/3767/2011/) and [2012 corrigendum](https://hess.copernicus.org/articles/16/1237/2012/) | Relates rainfall concentration and dispersion along drainage distance to response timing, using European flash-flood cases and modeling. | Held radar fields may reveal forcing differences hidden by catchment averages. Read and apply the corrigendum before implementing formulas. Hourly radar limits claims about rapid storm motion. |
| [Tarasova, Basso and Merz (2020), Transformation of Generation Processes From Small Runoff Events to Large Floods](https://doi.org/10.1029/2020GL090547) | Examines how event-generating processes change from ordinary runoff events to large floods. | An extreme need not be a scaled-up ordinary event. Include ordinary storm responses when investigating why analogues fail; do not infer a process transition from hydrograph shape alone. |
| [Mushtaq et al. (2023), Prediction of Extraordinarily High Floods Emerging From Heterogeneous Flow Generation Processes](https://doi.org/10.1029/2023GL105429) | Process mixtures help explain unusually large flood quantiles in selected German catchments. | Supports considering different response pathways. Its flood-frequency method is not an hourly escalation model and is not proposed as another chapter component. |
| [Geertsema et al. (2018), Anatomy of simultaneous flood peaks at a lowland confluence](https://hess.copernicus.org/articles/22/5599/2018/) | At a Meuse–Dommel/Aa confluence, long wave duration and backwater matter more than precise coincidence of peaks. | Study duration of overlap as well as peak order. This is a different, lowland location; neither its backwater magnitude nor mechanism can simply be assigned to Limburg tributaries. |
| [Guse et al. (2020), The role of flood wave superposition in the severity of large floods](https://hess.copernicus.org/articles/24/1633/2020/) | Multi-confluence analysis shows site-dependent relationships; the largest floods are not generally those with perfectly synchronized peaks. | A simultaneous rise is not automatically amplification. A confluence claim needs actual upstream/tributary/downstream geometry and suitable records. |
| [Voutsa et al. (2026), Large Scale Connectivity of River Networks During Rainfall Events](https://durham-repository.worktribe.com/output/5601632/large-scale-connectivity-of-river-networks-during-rainfall-events) | Distinguishes structural connections from synchronous and sequential runoff relationships in ephemeral Walnut Gulch. | Useful inspiration for separating shared storm response from propagation. Arizona's intermittent regime and reported connectivity thresholds do not transfer directly to perennial Limburg streams. |
| [Han et al. (2025), Recombining past event precipitation and antecedent catchment states generates unprecedented floods](https://www.nature.com/articles/s43247-025-02691-6) | Recombines historical precipitation and model states to construct plausible severe floods using mHM. | A later conditional scenario study is scientifically possible. Their daily national modeling is not ready-made hourly Limburg simulation, and observed analogue futures are not counterfactual target-river simulations. |

Existing [Wendi et al. (2019)](https://doi.org/10.1029/2018WR024111)
supports whole-hydrograph comparison; the chapter's earlier literature bridge
documents it. It remains useful, but another shape metric alone does not
answer the explanatory question above.

## Recommended synthesis: storm-centered comparative event diagnosis

Working question, for discussion rather than automatic adoption:

**Why do similar storms develop differently across Limburg's tributaries,
and when can another river's response help us understand escalation?**

Use the existing high-water inventory as an anchor, then construct a catalogue
of qualifying regional rainfall episodes across the held record. Retain all
eligible episodes under a stated rainfall/coverage definition, including
episodes without a p99 crossing and gauges that did not rise strongly.
This is a census of defined, observed storms, not a census of every physically
possible event. Use coverage-specific denominators rather than discarding
every storm unless every gauge is complete. Show major cases through the
population, not in place of it.

Three linked questions can then be answered without three new model families:

1. **An individual event: where did the comparison stop working?** Match
   earlier storms by forcing and initial flow, then locate differences in
   response timing, rise, volume and persistence. Check whether differences
   coincide with another rain pulse, a different rainfall footprint, incomplete
   recovery from the previous storm or documented measurement problems.
   Compare both similar storms on the same river and the same storm across
   rivers. These contrasts separate different explanations more effectively
   than simply listing nearest neighbours. They support conditional evidence,
   not causal attribution by matching alone.
2. **Tributary relationships: do useful neighbours change with conditions?**
   Test whether a river informative during one type of storm becomes a poor
   comparison during another, after accounting for rainfall and starting flow.
   The key quantity is conditional usefulness, not unconditional correlation.
   Geographically separate tributaries can share forcing without exchanging
   water; verified serial gauges can also observe propagation. Analyze these
   relationships separately. This is the most promising connection to the
   original analogue idea and the dynamic-similarity literature.
3. **Escalation: what distinguishes a continuing rise from recovery?**
   Follow storm responses before and after high-water entry, retaining repeated
   rainfall pulses and prolonged rises. Test whether a second pulse arriving
   before recovery distinguishes continued escalation from otherwise similar
   responses. Do not select explanatory features using the future outcome.
   Continuous severity and duration use more evidence than an H3-only target;
   official threshold crossings remain interpretable supporting outcomes.

An illustrative possible finding would be that two rivers are informative
comparators under broad, prolonged rainfall but not under localized storms,
or that divergence occurs when another rain pulse arrives before recession.
These are hypotheses, not findings. If conditional contrasts fail to reproduce
across held-out storms, report that failure rather than renaming clusters
until they appear meaningful.

## Data and practical feasibility

| Component | Held basis | Actual remaining work or limitation |
| --- | --- | --- |
| Storm forcing and response | Hourly catchment rainfall, discharge, RADOLAN raw crop arrays, reviewed provider problems and rating eras | Build storm-to-gauge alignment; check radar coverage, missing cells and cross-border consistency. Nonresponding does not mean unobserved. |
| Initial state and recovery | Antecedent rainfall and discharge histories | Proxy initial wetness/storage; no direct soil-saturation or storage-exhaustion claim. `34_fetch_era5_land.py` requests temperature, dew point and pressure, not soil moisture. |
| Spatial storm structure | Held 1 km/hour RADOLAN fields and catchment polygons | Derive concentration/coverage before considering more elaborate motion metrics. Routing-distance moments additionally need a checked drainage-distance surface/network. This is geospatial processing, not a reason to request a new satellite product. |
| Landscape interpretation | Held catchment geometries, EStreams attributes, AlphaEarth embeddings | Select interpretable terrain/geology/soil descriptors with metadata checks. Many events do not create many independent catchments; do not fit 64 spatial features as if each event were a new basin. |
| Connected-reach timing | German Wurm observations and Dutch Worm records | Verify station order, intervening inflows and comparable periods. The curated graph explicitly does not assert exact station order. Serial-gauge lags alone cannot identify a clean mass balance or channel travel time. |
| Escalation | Native Dutch thresholds and completed crossing census | Current thresholds are not historical agency decisions or independent inundation observations. Seven recorded H3 cases span four regional episodes; continuous response analysis has a broader evidence base. |
| Maas interaction | Held RWS raw files and archived pilot | Separate optional spatial question. The old mixed-code hourly file is unsuitable; much July 2021 Venlo Q is interpolated. A specific backwater claim could need stage evidence, but that does not block the tributary study. |

No new acquisition is needed to begin the core storm-response contrasts.
Quality and timing checks determine what each contrast can say, rather than
whether the chapter is allowed to exist.

## Purposeful AI role

Reuse frozen TTM alongside transparent rainfall/flow signatures to ask whether
its representation distinguishes the initial response states that make an
analogue transferable. Relate representation differences to measured rise,
recession and rainfall history; do not label an embedding dimension as soil
storage. A learned state or transferability rule could subsequently be tested
with whole storms held out, including all gauges from that storm together.
Compare it with conventional signatures on the same events. No benefit from
TTM is an admissible result; a process relationship need not depend on an AI win.

AlphaEarth can describe static context, but cannot observe hourly wetting or
prove a mechanism. Interpret its current weak incremental performance rather
than restoring it through an expanding parameter search. RAG, generative
explanations, another foundation model and a large graph neural network are
not needed to answer the proposed question.

For an explanatory reconstruction, realized storm rainfall after onset can be
used and labeled as such. For any claim of early identification, only data
available at the stated assessment time may enter matching or features;
future rainfall and retrospective normalization must not quietly become
forecast inputs. Existing exploratory development does not become an untouched
test set through a new split. Use storm/year blocking, transparent exploratory
status and response-matching controls to distinguish conditional relationships
from shared season, gauge identity and measurement artifacts.

## Larger option: conditional storm/state scenarios

If observed contrasts reveal a coherent question, a small rainfall-runoff
model on one well-observed catchment could test the same storm under different
antecedent states, following Han et al. Conceptual-model simulation is an
additional modeling component, requiring calibration, independent event
validation, state initialization and uncertainty checks. It need not imply
new field measurements, but its local adequacy has not been established.
This is a worthwhile later option, not the next automatic model to add.

## What not to repeat

The archived [Maas pilot](../../archive/retired-directions/2026-retrospective-high-water/docs/limburg-maas-tributary-pilot-2026-10-04.md)
already tested coarse tributary summaries added to an upstream-Maas/rainfall
baseline and found no increment. That does not rule out a physical confluence
study, but repeating the same predictor addition is not a new direction.

Avoid a generic wetness-effect replication, unrestricted correlation network,
causal claims from attribution plots, or a stage/discharge hysteresis discovery
where discharge is itself calculated from stage using a rating curve.
Maintain the existing analogue and warning results as baselines, including
failures. The proposed synthesis adds an explanatory target; it does not make
unfavorable earlier results disappear.

## Smallest useful next action

Audit and build the regional storm-response table from held data, preserving
ordinary/nonresponse cases, and produce aligned rainfall–flow views for all
eligible storms. Use those to test the three linked conditional contrasts
above, with a few transparent, hypothesis-driven quantities before considering
any newly trained model. The expected FEWS/DRR contribution is evidence about
when neighbouring-river experience is informative or misleading during
escalation. Operator benefit and as-issued warning skill would still require
their own evaluation; neither is necessary for an informative retrospective
chapter.
