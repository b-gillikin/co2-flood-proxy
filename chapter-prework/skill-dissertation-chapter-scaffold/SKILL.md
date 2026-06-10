---
name: dissertation-chapter-scaffold
description: Use this skill when the user wants to scaffold a single chapter of a PhD dissertation. Trigger phrases include "build a chapter scaffold," "scaffold this chapter," "literature scaffold for [topic]," "draft chapter [N]," "PhD chapter [topic]," "help me structure this dissertation chapter," "build a chapter lit review," or whenever a user provides research documents and signals they're working toward a PhD chapter-level deliverable. The skill runs an 8-stage workflow that elicits the chapter's thesis claim and shape, sets up a project repository, produces a sectioned literature scaffold .docx with DOI-tagged references, exports a BibTeX file ready for Mendeley/Zotero/EndNote, and generates monthly How-To execution docs. Outputs adapt to chapter type — supports chapters with or without predecessor work, with or without a transfer/portability dimension, across methodological families (anomaly detection, statistical modelling, qualitative analysis, mixed methods, simulation, theoretical). Do NOT use this skill for: master's theses or chapters, undergraduate work, entire dissertations (one chapter at a time only), non-academic writing, short conference papers, journal papers unconnected to a PhD chapter, or pre-thesis brainstorming without a defined claim.
license: User asset. Original workflow from Brian Gillikin's Maas/Meuse flood chapter (May 2026).
---

# PhD dissertation chapter scaffolding workflow

This skill runs an 8-stage workflow that takes a user from "I have research material and a thesis claim for one PhD chapter" to "I have a project repository, a literature scaffold, a bibliography for my reference manager, and a monthly execution plan." Each stage produces a concrete artifact; the user reviews and redirects between stages.

The skill operates on **one chapter at a time**. It is not a tool for planning a whole dissertation, sequencing chapters, or comparing chapters across the work. Run it once per chapter.

## When to use this skill

Trigger it whenever a user signals PhD chapter-level scope. The user typically arrives with:

- Research documents (papers, predecessor theses or papers, grey literature, notes)
- A rough thesis claim or research question
- Some sense of methodology, even if undeveloped
- An intent to write the chapter over a multi-month horizon

Do NOT trigger for:
- Master's theses or chapters (the rigor and section structure are calibrated to PhD examination depth)
- Undergraduate honors theses
- Entire dissertations (run this skill once per chapter, not for the whole work)
- One-off literature reviews not tied to a specific PhD chapter
- Short conference papers (workshop, 4-8 pages)
- Pre-thesis brainstorming where there's no defined claim yet
- Editing existing chapter prose

## Skill contents

```
dissertation-chapter-scaffold/
├── SKILL.md                              # this file
├── reference/
│   ├── elicitation_questions.md          # Stage 2 question bank
│   ├── section_canonical.md              # canonical section structure with applicability notes
│   ├── kill_check_pattern.md             # risk-checkpoint and pre-registration pattern
│   └── repo_layout.md                    # PhD chapter project repo structure
├── templates/
│   ├── scaffold_build.js                 # docx generator (sections customizable)
│   ├── howto_build.js                    # monthly How-To generator
│   └── bibtex_export.py                  # BibTeX with section-tagged keywords
└── examples/
    └── maas-flood-chapter.md             # worked example from this skill's first use
```

## Workflow — 8 stages

The stages are conversational, not script-driven. Don't try to run all eight without the user's input — pause between stages for review and redirection.

### Stage 1: Corpus orientation

Read what the user has provided. Produce a short structured summary identifying:
- The central thesis claim (or candidate claims if it's still ambiguous)
- The predecessor works if any
- The methodological frame
- The corpus shape (what areas are well-covered, what's thin)
- Any obvious gaps

Output: a few-paragraph orientation message. Do not produce documents yet — this is a calibration step.

### Stage 2: Framing dialogue

Iterate with the user to pin down:
- The thesis claim (one defensible sentence)
- The contribution space (what's novel, vs. what predecessor or field work has already established)
- The methodological frame
- Whether there's a data plan dimension (is there empirical data to acquire / characterize?)
- Whether there's a transferability / portability / generalization dimension
- Whether there are predecessor works that need positioning against

Use `reference/elicitation_questions.md` for the question bank. Ask 1-2 questions at a time, not all at once. Adapt the questions based on what the user has already said.

Watch for framing slips — the most common pattern is the user describing what predecessor work did and slowly drifting into describing it as what their chapter will do. Reflect the claim back as you hear it. Push back when the claim is overstated. PhD examiners will probe, so the claim has to be defended at examination depth.

Output: a clear, written thesis claim and contribution sentence the user has assented to.

### Stage 3: Project setup

Once the claim is settled, set up the chapter's working repository before producing more documents. This grounds all subsequent outputs in a single directory the user can track in version control.

Follow the structure in `reference/repo_layout.md`. The skill creates the directory tree, initializes git, writes a starter README.md tied to the chapter's claim, and writes the environment specification appropriate to the chapter's methodological family.

Defaults:
- Python repos: `environment.yml` (conda) with libraries chosen for the chapter's methodological family
- R repos: `renv.lock` initialization
- Mixed: both
- Qualitative / theoretical: minimal `environment.yml` plus reference manager pointer

No Jupyter notebooks. Analysis is a series of numbered runnable Python (or R) scripts in `scripts/`, importing from a stable `src/` package. The decisions log (`docs/decisions.md`) is initialized in this stage with the chapter's thesis claim as entry #1.

Output: an initialized chapter repo at a user-chosen path, ready to receive data and analysis scripts.

### Stage 4: Sectioned scaffold .docx

Now generate the scaffold using `templates/scaffold_build.js`. The canonical section structure is in `reference/section_canonical.md` — assemble from it the sections that apply to this chapter. Skip sections that don't apply rather than padding them.

Common section types (apply selectively):
- Framing and positioning (always)
- Context / setting (almost always)
- Predecessor work (only if predecessor work exists)
- Methodological foundations
- Specific methods / models / techniques the chapter uses
- Applied/operational analogues
- Verification, UQ, robustness
- Transferability (only if chapter has portability dimension)
- Institutional context
- Gaps and contribution (always)
- Data plan (only if empirical)
- Execution plan
- What to do next

Each section: a brief framing paragraph, a short list of load-bearing references with DOIs in muted color, inline notes where literature is thin or a methodological position needs to be taken.

Use the docx-js helpers from the template: H1/H2/H3 headings, BulCite for citation bullets, Note for inline methodological commitments, Body for prose, Code for shell or layout snippets.

Output: a single .docx scaffold saved into the chapter repo's `docs/` directory.

### Stage 5: Refinement passes

Most chapters need 2-4 refinement iterations. Common ones:

- **Framing tightening**: reflect the claim back, sharpen the contribution sentence
- **Predecessor-work pass**: when predecessor docs are read after the first scaffold, correct misrepresentations
- **DOI pass**: web-search remaining `[DOI to confirm]` entries; verify with corpus
- **Examination-depth pass**: add positioning vis-à-vis field SOTA, defended methodological choices, treatment of confounds at PhD examination depth
- **Data plan pass**: if the chapter has empirical data, add a Data Plan section
- **Execution-plan pass**: monthly schedule, kill-checks, pre-registration

Each refinement should be a focused pass — don't batch unrelated changes. Always rebuild the .docx and validate after each pass.

### Stage 6: Bibliography export

Once the scaffold's section list is stable, generate a BibTeX file using `templates/bibtex_export.py`. Populate `entries` with each citation as `(citekey, type, fields, section_tag)`.

Each entry's `keywords` field gets the section tag, which becomes a Mendeley/Zotero tag for one-click folder organization on import.

Output: `chapter-references.bib` saved into the chapter repo's `docs/` directory. If the user uses a specific reference manager, also produce a one-page import plan adapted to that tool.

### Stage 7: Execution plan + monthly How-Tos

Generate monthly How-To docs using `templates/howto_build.js`. Each month:
- Goal for the month
- Prerequisites from prior month
- Week-by-week tasks
- Each task: Why, How (with code/commands), Output, Time estimate
- Kill-checks at decision points
- End-of-month review checklist

Month 1 must include a pre-work section covering: environment activation, predecessor-work reading with structured notes, decisions log initialization, first data ingestion.

For chapters without a sprint window, replace monthly How-Tos with a milestone-based execution plan — same structure, different cadence.

Outputs: one .docx per month (or per milestone), saved into the chapter repo's `docs/` directory.

### Stage 8: Hand-off

Summarize what was produced, what's open, and what to do next. Confirm the user can find every artifact in the chapter repo. Offer to run the skill again for the next chapter when the user reaches that point.

## Style notes

- Concise prose. Hedging is expensive in scaffolds — PhD examiners read confident framing.
- DOIs in muted color (`#808080`) so they don't interrupt reading flow but are visible when needed.
- Inline `Note` blocks (italic, left-border) for methodological commitments the chapter takes. These are the bits examiners probe — write them as defended positions.
- `[grey: example.com]` after grey-literature entries.
- `[no DOI — reason]` after pre-DOI or genuinely DOI-less entries.
- `[DOI to confirm]` for entries to verify in a later pass.
- No notebooks. Every analytical step is a reproducible script.

## What to avoid

- Don't generate the scaffold before Stage 2 is settled. Wasted scaffold rewrites cost more than a slow Stage 2.
- Don't skip Stage 3 (project setup). A scaffold without a repo accumulates as loose documents the user can't track.
- Don't lock the chapter into a specific methodological pattern at Stage 1. Stay neutral until the user has said what they're actually doing.
- Don't fabricate DOIs. Use only DOIs confirmed via corpus or web search; flag the rest with `[DOI to confirm]`.
- Don't write a discussion section in the execution plan. The discussion is downstream of seeing the results — drafting it ahead of time produces hollow text.
- Don't treat this as a multi-chapter tool. Run once per chapter.
