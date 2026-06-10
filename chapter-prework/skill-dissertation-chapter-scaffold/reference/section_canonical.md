# Canonical section structure

Assemble the scaffold by picking sections that apply to this specific chapter. Don't force-fit. Skip sections that don't apply rather than padding them.

## Section types

### 0. Framing and positioning

**Always include.** Two paragraphs:

- Paragraph 1: What the chapter tests / argues. State the claim plainly. If there's predecessor work, name it and say what's inherited from it. State the methodological frame.
- Paragraph 2: Where the chapter sits in the field. Name 2-3 active research conversations it speaks to. State the contribution at intersection-level.

### 1. Context / setting

**Almost always include.** Background framing only — not load-bearing.

Sub-sections vary by chapter type:
- Empirical site-based: basin/study area, immediate site/sub-system, anchor event if any
- Methodological: the methodological field, recent developments, current SOTA
- Theoretical: the conceptual lineage, the live debates
- Mixed: combine as appropriate

Tone: orient the reader to the setting, then move on. Don't dwell.

### 2. Specialized substantive context

For empirical chapters with a particular physical, biological, or geographical setup that's unusual — e.g. post-mining hydrogeology, a specific cell type, a particular archive — include a section that explains it. Examiners will need this background to follow the methods.

For methodological chapters this is often "current understanding of the problem space" — e.g. open questions in TSAD benchmark evaluation.

### 3. Mechanism / theoretical framing

For chapters with a hypothesized causal or theoretical chain, name it explicitly. Cite the supporting literature. Flag the principal confounds. Defend the decomposition strategy if there's a confound that has to be controlled.

This section is where methodological commitments live. Use inline Notes for them.

### 4. The proxy / target / construct (if applicable)

For empirical chapters that use one observable to track another, explain the chain. For methodological chapters, this is the construct under study.

### 5. Methodological foundations

The general literature backing the chapter's approach. Surveys, taxonomies, foundational frameworks. Should be brief — these are background.

### 5.x Evaluation methodology

**Almost always include for empirical chapters.** Often the most load-bearing methods sub-section. State the chapter's position on evaluation explicitly, especially under non-standard conditions (low-N labels, non-stationarity, single case, etc.).

### 6. Specific methods / models / techniques

One sub-section per method the chapter uses. For each: foundational citations, applications in the field, the specific parameterization the chapter adopts. Defend method-selection choices in PhD-level chapters.

### 7. Applied / operational analogues

Closest published work to what the chapter does, in the chapter's domain. The genre conventions the chapter will be read against.

### 8. Compound events / UQ / non-stationarity / robustness

For chapters where the conditions are non-stationary, the labels are sparse, or the inferential machinery has to handle compound factors. State the chapter's UQ position (e.g. GLUE-positioned, ensemble, Bayesian) explicitly. This is examiner territory.

### 8.x Reference databases / standards / benchmarks

If the chapter uses external data for validation (impact databases, reanalyses, gold-standard benchmarks), list and date them.

### 9. Predecessor work (if exists)

**Include only if applicable.** When this chapter directly builds on prior theses, lab papers, or a research group's accumulated work. For each predecessor:

- Full citation
- What they did, in their own words where possible
- Their headline result
- What this chapter inherits from them
- What this chapter does differently

If no predecessor work, skip this section. Don't pretend to have inherited work that doesn't exist.

### 10. Transferability / portability / generalization (if applicable)

**Include only if applicable.** When the chapter tests whether something generalizes across sites, populations, conditions, etc.

The literature backing the test — typically prediction in ungauged basins, transfer learning, domain adaptation, external validation. State the chapter's specific test as a response to current best-practice methodological injunctions.

### 11. Institutional / infrastructure context

Background framing for the institutional context. Useful for the chapter introduction; rarely load-bearing. Often grey literature.

### 12. Gaps and contribution

**Always include.** Reformulates the contribution as journal-paper-publishable claims, organized around the gaps in the literature.

Typically 3-5 gaps, each named explicitly. Then a one-sentence contribution statement (or three claims, structured as methodological / empirical / applied).

### 13. Data plan (if applicable)

For empirical chapters. Sub-sections:
- 13.1 In hand
- 13.2 To acquire
- 13.3 Soft-label / event catalogue construction (if relevant)
- 13.4 Transfer sites / external validation sites / replicate populations (if relevant)
- 13.5 Baselines to beat
- 13.6 Reproducibility / FAIR
- 13.7 Methods-chapter constraints to flag

### 14. Execution plan

Monthly or milestone-based. Pre-work first, then per-period tasks. Include kill-checks at decision points.

### 15. Housekeeping / what to do next

Non-data, non-execution items. Confirmations, verifications, things-to-decide-with-supervisor.

## Section ordering

Use the numbering above as a default. Reorder if a particular chapter has a different center of gravity. Two common variants:

- **Methodologically heavy chapters**: put Methods (Section 5-6) closer to the front; treat Context as a single brief section.
- **Empirically heavy chapters**: put Context and Substantive Context (Section 1-2) prominently; treat Methods as one section.

## Section inclusion checklist

Before generating the scaffold, decide for this chapter:

- [ ] Empirical or theoretical?
- [ ] Has predecessor work?
- [ ] Has data plan dimension?
- [ ] Has transferability / portability dimension?
- [ ] Has labelled events / soft-labels to enumerate?
- [ ] Has institutional/grey-literature backing?
- [ ] Master's or PhD level?

The answers drive which sections appear and how much weight they carry.
