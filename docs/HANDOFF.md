# Session Handoff

Written 2026-08-10. Session state only; use the synthesis and protocol for
chapter claims.

Read in this order:

1. `chapter-synthesis.md` — canonical question, contribution, design and state.
2. `chapter-scope-and-preregistration.md` — draft 0.5 estimator protocol.
3. `supervisor-decision-memo.md` — choices requiring supervisor approval.
4. `student-next-actions.md` — the student's detailed five-task handoff.
5. `data-requests.md` — delivery contracts and blockers.
6. `lanuk-feasibility.md` — reproducible decision on the held German route.
7. `literature-source-notes.md` — source-level notes, not a literature review.
8. `literature-evidence-matrix.csv` — 22 evidence questions mapped to sources.
9. `chapter-references.bib` — verified retained bibliography.
10. `analysis-inventory.md` — live, secondary and stopped work.

## Current chapter

> Across Limburg tributaries, which public hydrometeorological signals recur
> during the 72 hours before independently defined high-water onset, and how
> does their event-minus-quiet signal change with distance from the affected
> watercourse? If the source data support a Kerkrade case, does
> pressure-adjusted CO2 recur there as a local manifestation of that regional
> state?

The sequence is Viefhues's July 2021 observation -> Eryilmaz's same-site public
weather explanation -> this chapter's recurrence and spatial-extent test.
Transferability means the distance relationship in all-donor event contrasts,
not classification, gauge substitution, travel time or an operational radius.

## Literature reset completed

- `literature-source-notes.md` contains 40 independent source entries across
  the predecessors, local mine context, July 2021, flood processes, spatial
  dependence, event sampling, radar rainfall and discharge uncertainty.
- `literature-evidence-matrix.csv` contains 94 question/source relationships
  using only the six declared coverage roles. The 30–40 planning range was not
  treated as a quota; canonical sources were retained where applicable.
- `chapter-references.bib` has one verified entry per retained source, with
  shared keys and no provisional metadata or abbreviated author lists.
- No integrated literature synthesis, literature-gap conclusion, expected
  result or chapter prose was written. The student owns cross-source analysis
  and writing.
- The two supplied predecessor PDFs remain in `chapter-prework/`. Obsolete
  How-To documents, generated source corpora, scaffold skills, reports and the
  legacy bibliography were removed; Git history remains the archive.

## Viefhues source status

K4 remains the useful source-native historical record. It is labelled as the
non-ABC basement sensor in the supplied R code and contains every July 2021
civil-time hour. The observed K4 trajectory is reproducible, but device
identity, calibration, exact ABC edits, the 450-ppm adjustment and reuse terms
remain unresolved. K3's `livingroom` filename still conflicts with the thesis
statement that both sensors were in the basement. These discrepancies are now
recorded in the canonical source notes.

The conditional CO2 recurrence case remains unavailable because sensor-era
provenance, a valid hydrological pair, independent onset bounds and three later
complete events do not yet exist. That does not block the regional chapter.

## Current stop

`python scripts/31_event_study_gates.py --report-only` still reports regional
**FAIL** because all six contracted long-record network inputs are absent. Do
not lower the ten-year cohort rule, substitute the rolling two-year record or
inspect prospective signal contrasts.

The student's immediate actions remain those in `student-next-actions.md`:

1. obtain the supervisor's eight design decisions;
2. send the historical-discharge request to Waterschap Limburg;
3. send the timestamp/gap-semantics request to LANUK;
4. request the seven unresolved Viefhues provenance items; and
5. return decisions, correspondence and native attachments unchanged.

## Agent work after the student returns

1. Inventory and hash native deliveries; resolve sampling, timezone, units,
   missingness, rating curves, natural/managed status and July 2021 QA.
2. Fix the admissible watercourse cohort and write direct, tidy ingests only
   after the delivered formats are known.
3. Build and visually verify catchment polygons, RADOLAN area averages and the
   supervisor-approved long public-weather assignment.
4. Rerun the strict regional gate. If it passes, record hashes and approvals
   and lock the protocol before outcome inspection.
5. Implement matched contrasts, one prespecified spatial gradient per signal,
   tidy outputs and four figures. Add only claim-protecting estimator checks.
6. Add the Kerkrade section only if its separate evidence contract passes;
   missing case evidence is not a null CO2 result.

## Verification

Named interpreter:
`/Users/briangillikin/miniforge3/envs/chapter1-co2/bin/python`

- literature integrity: **40** source notes, **94** question/source rows,
  **40** matching BibTeX entries and **34** unique bare DOIs; all 22 questions
  and all retained keys resolve;
- default scientific suite: **32 passed**;
- optional legacy infrastructure suite: **18 passed**;
- `ruff check .`: passed;
- `ruff format --check .`: passed (57 files);
- regional gate report regenerated: **FAIL**, as expected, with all six
  contracted inputs absent.
