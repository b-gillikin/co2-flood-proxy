# Worked example — Maas/Meuse flood chapter (May 2026)

The skill's first use. Distilled here as a reference for future runs.

## The chapter

**Title**: Antecedent-state signal in low-cost IoT data: characterization at a Kerkrade post-mining calibration site and transfer to the wider Maas basin

**Level**: PhD dissertation chapter

**Claim**: That the multivariate signal in low-cost IoT air-quality + weather data carries usable information about antecedent hydrological state — specifically, the state of the post-mining aquifer beneath South Limburg as expressed through CO₂ dynamics in a partially flooded disused mineshaft beneath a Kerkrade basement.

## Stage-by-stage trace

### Stage 1: Corpus orientation

User provided 11 .docx files containing prior research material: 7 source compendia from earlier in the project, 1 gaps doc, 1 deck-vs-corpus juxtaposition, 1 consolidated bibliography (~690 references), 1 re-sorted bibliography.

Orientation output: identified the dominant theme as Meuse/Maas flood research with a focus on July 2021; noted the corpus's apparent target as a Maastricht University thesis fusing process-based hydrology with statistical/ML anomaly detection.

### Stage 2: Framing dialogue

Multi-turn conversation. Key pivots:

1. User said: "the central idea at this point is anomaly detection towards understanding some signal that precedes a flood event." Reflected back; user confirmed.

2. User clarified the proxy chain isn't CO₂ as causal precursor but CO₂ as correlate of antecedent conditions. Then further clarified that the CO₂ comes from a partially water-filled disused mineshaft (not soil respiration). Reframed the proxy as a water-table mechanism in the post-mining aquifer, not a soil-saturation one.

3. User said previous work already tried direct CO₂-discharge correlation; project is now in anomaly-detection ensemble mode (SARIMAX + Kalman + Isolation Forest), with the residual signal as the target of characterization.

4. User clarified: it's a PhD dissertation chapter, not a master's thesis. Bar shifts to journal-paper-publishable depth.

5. User said two prior DAD theses exist on the same Kerkrade dataset. Initially framed as "predecessor theses." Later, after reading them, corrected: Viefhues 2022 is a master's thesis (77pp); Eryilmaz 2025 is a paper (11pp). Eryilmaz's actual finding is feature substitution (outdoor weather replaces indoor IoT at the same site predicting the same target), not the "CO₂ ablation" framing I had initially used.

Final agreed claim and contribution: characterize the multivariate antecedent-state signal at the Kerkrade calibration site, decompose barometric vs. hydrological contributions, test transfer to Maas basin sites without mine-gas instrumentation.

### Stage 3: Sectioned scaffold .docx

13 sections plus housekeeping:

- 0 Framing
- 1 Basin and site context (1.1 Meuse, 1.2 Geul/Worm, 1.3 July 2021)
- 2 Post-mining hydrogeology
- 3 Mine-gas dynamics + (3.1) Barometric pumping
- 4 Water table and CO₂
- 5 TSAD foundations + (5.2) Evaluation methodology
- 6 Three candidate models + (6.0) Why these and not deep TSAD
- 7 Environmental sensor TSAD analogues + (7.1) IoT deployment
- 8 Compound events / UQ + (8.1) Flood-impact databases
- 9 Predecessor work (Viefhues, Eryilmaz)
- 10 Transferability
- 11 European mine-water infrastructure
- 12 Gaps and contribution
- 13 Data plan
- 14 Summer execution plan
- 15 What to do next

### Stage 4: Refinement passes

Six iterations:
1. Transferability framing pass (after user clarified the Eryilmaz redundancy finding)
2. DOI pass — corpus sweep, ~35 confirmed
3. Data plan section added
4. PhD-chapter level-of-pitch pass — added positioning, defended methodological choices, examination-depth treatment of confounds
5. Predecessor-work correction pass — after reading Viefhues and Eryilmaz, corrected misrepresentations in Section 9
6. Final DOI pass — web search resolved remaining `[DOI to confirm]` entries; two factual corrections (Frame year/venue, Ba-Alawi venue)

### Stage 5: Bibliography export

`chapter-references.bib` with 80 entries. Each entry tagged with its scaffold section in the `keywords` field for one-click Mendeley folder organization.

Accompanying `Mendeley import plan.docx` covering pre-import sanity check, import workflow, folder structure, post-import cleanup, future workflow.

### Stage 6: Execution plan + monthly How-Tos

Summer 2026 plan: June (foundation, decomposition, Eryilmaz replication, soft labels), July (modeling, ensemble agreement, evaluation protocol, transfer-site acquisition), August (transfer experiment, baseline comparison, initial writing).

Each month: pre-work section (June only), week-by-week task breakdowns, per-task Why/How/Output/Time, kill checks at decision points, end-of-month review checklist.

### Stage 7: Hand-off

User signaled two more chapters coming. Proposed and built this skill.

## What worked

- Iterative framing dialogue. Early scaffold drafts had misframings that came out only when the user reacted to them.
- Reading predecessor works in detail. The Eryilmaz finding I had originally summarized ("signal persists when CO₂ is removed as a feature") was wrong; the actual finding is feature substitution at one site predicting the same target. Reading the paper changed Section 9 substantially.
- Building the kill-checks into the execution plan. Without explicit decision points, the user would have had to construct them ad hoc.

## What to do differently next time

- Stage 2 took longer than expected because framing kept shifting as the user clarified mechanism details. Asking "what is the physical mechanism" earlier — before drafting the proxy chain — would have saved one refinement pass.
- Should have asked about the data window (which dates) before framing the chapter around the July 2021 event. The user's data window starts Jan 2025; July 2021 is outside it. This required a late framing pivot.
- I initially named Eryilmaz 2025 as a thesis when it's actually a paper. Asking for the actual document earlier rather than relying on summarized claims would have caught this.

## Chapter-specific parameters

For future chapters that don't share this chapter's shape:

- This chapter had a calibration-site / cross-site transfer pattern. Most chapters don't. The transferability section is optional.
- This chapter used anomaly detection methods. Other methodological families need different specific-methods sub-sections (Section 6).
- This chapter had predecessor DAD work. Chapters without that have an Empirical Anchor section that establishes the foundation differently.
- This chapter had a Data Plan (empirical chapter). Theoretical or qualitative chapters don't need one.
