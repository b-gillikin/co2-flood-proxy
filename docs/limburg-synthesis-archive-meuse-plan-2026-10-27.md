# Plan: synthesize findings, quantify archive trade-offs, test Meuse context

Prepared 2026-10-27 at Brian's request. Implementation plan and research aid; not manuscript prose, a formal preregistration, or a new result. Work is limited to Chapter 1. Existing empirical findings and their exploratory development remain visible. Brian writes dissertation/article text.

## Purpose and questions

Overarching motivation: can AI-selected historical events improve assessment of how high water develops in the Meuse basin beyond conventional hydrological analogues?

This pass answers three concrete questions:

1. What does the completed evidence establish about useful similarity, severity, timing and uncertainty?
2. How much do representation requirements change the available historical evidence, separately from how a representation ranks that evidence?
3. Does contemporaneous Meuse state/trend improve the existing tributary analogue assessment on a declared retrospective task?

FEWS/DRR motivates reliable interpretation of historical precedents and the risk of false reassurance. Deployment, operator interviews, impact/damage modeling and a new warning classifier are not part of this pass. There is no requirement for an AI win or statistically significant result.

## Workstream 1: make one coherent evidence synthesis

### Reuse completed analyses

Read from the final corrected results and their hash manifests:

- `results/limburg_findings_consolidation_2026_10_27/`: conventional/raw/TTM/AlphaEarth and ten EO comparisons, actual feature-complete rainfall benchmark, archive controls and sensitivities.
- Existing October 15 analogue-distribution results: empirical CRPS, coverage/width and directional misses for raw/state, TTM, conventional and AlphaEarth. These results have not been computed for every final EO configuration; mark that distinction.
- October 15 storm-response census: phase/forcing divergence, peer-gauge information and repeat-pulse findings, including the unfavorable and unstable results.
- `results/flood_case_review_2026_10_27/`: source-bounded flood episodes, whole-event measurement review, saved donors and failure diagnoses.
- `results/meuse_context_2026_10_27/`: observational mainstem context and source-quality audit.

### Products

Build an evidence map with one row per scientific claim: question, exact population/donor archive, method and comparator, outcome/estimator, effect and intervals where available, coverage, sensitivity, development status, and source artifact. Distinguish evidence from different populations rather than combining their event counts or making a cross-cohort league table.

Organize the chapter's argument around:

1. Whether historical selection adds information beyond a generic eligible archive.
2. What AI adds beyond conventional hydrological matching.
3. Whether similarity gains translate into severity/timing/distributional gains.
4. Which source, archive, retrieval or aggregation limitations explain particular failures.

Keep the ten encoder results in a comprehensive supporting table. Choose illustrative cases by a declared failure taxonomy and retain already inspected cases; do not replace them with success-only examples. The primary support for performance claims remains the eligible event census, including events that do not escalate after assessment.

Produce an internal synthesis memo and figure/table reading order. Update the living one-pager and active-design reading map to point to the final evidence. Do not draft Brian's dissertation prose or retrospectively describe exploratory choices as prospective.

## Workstream 2: separate information gain from archive restrictions

### Coverage accounting

Start with the full 1,062-row held inventory, retaining explicit reasons for unusable histories/outcomes, insufficient prior archive, unavailable rainfall predictors, unavailable imagery, and missing Meuse context. Carry NL/DE, watercourse, year and storm counts. Use each arm's actual feature requirements; do not reinstate the old 512-hour rainfall completeness restriction for 168-hour predictors.

For all ten EO models, report their own available population alongside the shared all-ten intersection for the three existing readouts. Reuse existing model/input routes and their provenance; supplemental imagery routes remain sensitivity context rather than additional models.

For each query/pool record distinct eligible donor storms, earliest/latest precedent, age distribution and source-quality support. Where labels exist, record retained/lost prior H3-reaching precedents and known documentary floods. German or incomplete outcomes without equivalent labels remain unknown, not negative. Losing a labelled severe precedent does not automatically mean losing the best predictive analogue.

### Paired decomposition

For an unchanged query set and an unchanged baseline B, distinguish:

- **Full baseline:** B on the broad archive compatible with B's predictors.
- **Restricted baseline:** B recomputed on the exact archive compatible with representation M.
- **Augmented representation:** M on that same restricted archive.

Recompute any candidate-dependent distance scaling on the actual respective prior pool. Reuse hash-verified cached results when they already meet this exact contract. Where a paired reference is missing, compute only the necessary baseline/control retrieval and response scores; no new EO extraction is involved.

For lower-is-better loss L on the same paired queries:

    archive restriction difference = L(B, restricted) - L(B, full)
    representation increment       = L(M, restricted) - L(B, restricted)
    total difference               = L(M, restricted) - L(B, full)

Check the arithmetic identity per query. These are empirical comparisons under specified archive policies, not a causal attribution to missing imagery or a physical mechanism. Query exclusion is a separate applicability result; do not hide it inside this decomposition.

Use conventional matching as the substantive reference on actual rainfall-complete cases and TTM/state as the incremental EO reference. Preserve the broad Q-history result for cases without rainfall. Primary presentation uses existing pooled/all-river, five-donor settings, with the existing ten-donor and other-river views shown separately. Reuse existing outcome definitions and storm/year resampling for any new paired control contrasts. Retain every encoder and undefined/short-archive result, not only attractive comparisons.

### Products

Create a population/donor-support ledger, paired decomposition table and two figures: information increment versus archive restriction; coverage by representation/year/watercourse. Link severe-case timelines to their exact lost/retained precedents. Consolidate numerical evidence rather than claiming that different unpaired cohort scores isolate a coverage effect.

## Workstream 3: one focused Meuse-context experiment

### Hypothesis and assessment

Hypothesis: tributary events with similar local histories can have different wider-basin states; adding the observed Meuse state/trend may improve the distribution of subsequent tributary discharge represented by historical analogues.

Assessment remains the existing retrospective p99-onset catalogue. Modern frozen representations, finalized records and full-era tributary normalization retain their declared limitations. This is not a historical as-issued forecast replay. Query context is restricted to temporal support ending by assessment, and donor response windows must be complete before that assessment.

### Inputs and population

Use held ordinary controlled code-00 Sint Pieter/Venlo discharge and the source-audited hourly support from script 145. Keep interpolated/broader-code curves for documentary display rather than filling primary features with them. Missing Meuse input does not remove an event from the original catalogue.

Primary Meuse block has four fixed features:

- Sint Pieter discharge rank relative to available ordinary controlled data from earlier calendar years.
- Sint Pieter net 24-hour discharge change.
- Venlo equivalent prior-year rank.
- Venlo net 24-hour discharge change.

Use the existing feature values at cutoff. Net 24-hour change needs both endpoint observations; do not demand unused complete 72-hour context merely to calculate it. Retain reference observation/year counts, quality flags and past-window coverage as diagnostics. They are not features selected in response to a favorable result.

A single declared coverage sensitivity uses Sint Pieter's two features alone because Venlo's earlier archive is sparse. Label it separately; do not select between the two views after seeing scores. No inference of confluence backwater or tributary-to-mainstem causation follows from these features.

### Arms and donor controls

Four primary arms on the same actual rainfall-feature-complete, Meuse-complete query/donor population:

1. Conventional rainfall/discharge matching.
2. The same conventional matching plus the Meuse block.
3. Frozen TTM plus existing river state.
4. The same TTM/state matching plus the Meuse block.

Retain a storm-balanced generic eligible-archive distribution as context. The main scientific contrasts are 2 versus 1 and 4 versus 3; comparisons across different populations are not substitutes.

Baseline methods must be recomputed on the restricted archive, with their existing formula unchanged. For augmented methods, robust-scale Meuse feature columns using eligible prior candidates only, then use the existing prior-candidate RMS block normalization. Preserve the baseline's internal distance weights by treating its existing combined distance as one block. Combine baseline and Meuse blocks with equal squared-distance weight (50:50); do not search weights. Record both distance contributions and all scales.

Retain earlier-completed response eligibility, a different storm group, one selected donor per storm, five donors as the main setting and ten as sensitivity. Short archives remain explicit. Existing other-river and measurement-quality sensitivities are retained; country/watercourse results are descriptive transfer checks, not policy effects.

Also show the unchanged baseline on the broad eligible archive. Apply the workstream-2 decomposition to distinguish the cost of requiring Meuse data from the benefit of using it. For full-census applicability, report one simple fallback policy: augmented retrieval where its query context and prior context-supported donors exist, original broad baseline otherwise. Evaluate this separately from the clean paired increment; do not use it to conceal missing-context cases.

### Outcomes and uncertainty

Primary endpoint: exact empirical-distribution CRPS averaged over subsequent hours 1–24, reusing the existing implementation and whole donor trajectories. Lower is better. This tests whether selected precedents provide a better distribution of subsequent discharge, not just a closer normalized shape.

Secondary diagnostics reuse defined estimators: 6/12/24-hour distribution scores, coverage/width and above/below-range misses; the original 72-hour peak-magnitude, mean-trajectory, individual peak-time mismatch and high-water-duration measures. Keep shape similarity as an explanatory endpoint rather than the success definition. Do not silently change mean to median, normalize by an unknown query peak in retrieval, or label a pointwise range a simultaneous trajectory interval.

Pair the same queries for each contrast. Use the existing 9,999 joint storm-block draws and year-block sensitivity, shared across arms, with the established seed. Report effect sizes, intervals, event/storm/year denominators and undefined results. Existing storm dependence, reused donors and explored outcomes limit interpretation; intervals are not multiplicity-adjusted confirmation or gates.

Review all eligible queries numerically. For detailed visual inspection, retain the existing severe cases plus a deterministically selected set spanning improvements, degradations, unchanged selections and absent support. Record how examples were selected. No future-outcome-only sample replaces the main census.

### Validation

- Check the F103 centred-time support and UTC labels against hand-checked source rows.
- Poison post-cutoff values and same-/future-year reference data to prove input/rank invariance.
- Confirm missing/interpolated values never become ordinary controlled observations or zeros.
- Verify exact query/donor pairing, chronological response completion, storm separation and short-archive accounting.
- Confirm adding/removing the Meuse block changes no baseline formula, and reproduction on the same restricted pool agrees with the reference runner.
- Reconstruct selected-donor outcomes independently, check empirical CRPS against the existing implementation, and retain actual member counts.
- Hash inputs, code and outputs; preserve the original score bundles and report numerical failures rather than silently dropping rows.

### Products

A compact executable comparison specification; a single retrieval/scoring runner with checkpointed stages; support and donor ledgers; paired scores/intervals; updated analogue browser; and an internal results memo answering the question whether Meuse context helped, hurt or made no discernible difference under this configuration.

## Order, compute and completion

1. Build the evidence map and agreed reporting task.
2. Construct archive/query support ledgers and inventory missing exact paired references.
3. Write the Meuse comparison specification and execute the paired controls/retrieval.
4. Score, resample, inspect cases and independently audit numerical consistency.
5. Combine all three workstreams in one internal readout; update the one-pager and reading map; commit/push reviewable code and documentation.

No encoder rerun, GPU or new data acquisition is needed. Work is downstream CPU/table processing. Benchmark a representative retrieval/scoring batch and project runtime before launching the full computation; use caches and checkpointing. Exact elapsed time depends mainly on missing control comparisons and resampling, so do not promise a duration before that benchmark. Reuse source inputs in place and write versioned output directories; do not copy large EO caches or clean data from other chapters.

Completion means all declared comparisons and support accounting are produced and validated, including unfavorable or undefined results. Further model/weight searches, a new confidence classifier, a separate Meuse donor population, and impact modeling would be separate proposals. They are not automatic follow-ons if the result is weak.
