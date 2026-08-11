# Session Handoff

Written 2026-08-10. Session state only; use the synthesis and protocol for
chapter claims.

Read in this order:

1. `chapter-synthesis.md` — canonical question, contribution, design and state.
2. `chapter-scope-and-preregistration.md` — draft 0.6 estimator protocol.
3. `supervisor-decision-memo.md` — choices requiring supervisor approval.
4. `student-next-actions.md` — the student's detailed five-task handoff.
5. `data-requests.md` — delivery contracts and blockers.
6. `lanuk-feasibility.md` — reproducible decision on the held German route.
7. `literature-source-notes.md` — source-level notes, not a literature review.
8. `literature-evidence-matrix.csv` — 23 evidence questions mapped to sources.
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

## Supervisor response

Approved: the contribution, transferability as all-donor spatial extent,
natural Limburg tributaries as the primary population, ERA5-Land as primary
weather, July 2021 as a censored regional anchor and the conditional status of
the Kerkrade CO2 case. Three held-out receiver events is provisionally
acceptable.

Still open: the numerical cohort floor, the coverage/donor-availability floors
and the clarified requirement that every retained test event have at least one
complete donor in each distance third. These are design judgements, not field
standards. Use the proposed blinded availability audit before outcomes, then
freeze a supervisor decision. The protocol remains unlocked.

## Weather acquisition

- `scripts/34_fetch_era5_land.py` downloads monthly files for 2001–2025
  temperature, dew point and surface-pressure grids over 50.5–52.0° N and
  5.0–6.7° E and hash them. `cdsapi` is installed in the named environment.
- The CDS credential and ERA5-Land licence are verified. Full-day annual
  requests exceed the 12,000-field limit. A five-hour annual-block benchmark
  passed but was slower per field than the monthly requests, so acquisition is
  proceeding in restart-safe monthly files. Six validated monthly files were
  recovered before the full sequential run began; newly completed months are
  added atomically. The 2001 annual-block benchmark is not part of the final
  source manifest.
- `scripts/35_ingest_knmi_validated.py` downloaded and hashed nine official
  decade ZIPs and wrote a 655,221-row 2001–2025 Maastricht/Ell/Arcen table.
  Temperature/humidity are effectively complete; validated pressure exists
  only at Maastricht and Arcen currently ends 30 September 2025. This is
  sensitivity evidence, not a core input.

## Literature reset completed

- `literature-source-notes.md` contains 43 independent source entries across
  the predecessors, local mine context, July 2021, flood processes, spatial
  dependence, event sampling, radar rainfall and discharge uncertainty.
- `literature-evidence-matrix.csv` contains 97 question/source relationships
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
**FAIL** because all six analysis-ready network inputs are absent. Do
not lower the ten-year cohort rule, substitute the rolling two-year record or
inspect prospective signal contrasts.

The student's immediate actions are:

1. obtain the supervisor's remaining floor/occupancy decisions after the
   explanations in `supervisor-decision-memo.md`;
2. wait for the already-sent Waterschap, LANUK and Viefhues replies; and
3. return correspondence and native attachments unchanged.

## Agent work after the student returns

1. Inventory and hash native deliveries; resolve sampling, timezone, units,
   missingness, rating curves, natural/managed status and July 2021 QA.
2. Fix the admissible watercourse cohort and write direct, tidy ingests only
   after the delivered formats are known.
3. Complete and QA the ERA5-Land pull; build and visually verify catchment
   polygons, centroid weather assignment and RADOLAN area averages.
4. Rerun the strict regional gate. If it passes, record hashes and approvals
   and lock the protocol before outcome inspection.
5. Implement matched contrasts, one prespecified spatial gradient per signal,
   tidy outputs and four figures. Add only claim-protecting estimator checks.
6. Add the Kerkrade section only if its separate evidence contract passes;
   missing case evidence is not a null CO2 result.

## Verification

Named interpreter:
`/Users/briangillikin/miniforge3/envs/chapter1-co2/bin/python`

- literature integrity: **43** source notes, **97** question/source rows,
  **43** matching BibTeX entries and **36** unique bare DOIs; all 23 questions
  and all retained keys resolve;
- default scientific suite: **32 passed**;
- optional legacy infrastructure suite: **18 passed**;
- `ruff check .`: passed;
- `ruff format --check .`: passed (59 files);
- regional gate report regenerated: **FAIL**, as expected, with all six
  contracted inputs absent.
