# Session Handoff

Written 2026-08-08. Session state only; use the synthesis and protocol for
chapter claims.

Read in this order:

1. `chapter-synthesis.md` — canonical question, contribution, design and state.
2. `chapter-scope-and-preregistration.md` — draft 0.5 estimator protocol.
3. `supervisor-decision-memo.md` — choices requiring supervisor approval.
4. `student-next-actions.md` — the student's detailed five-task handoff.
5. `data-requests.md` — delivery contracts and blockers.
6. `lanuk-feasibility.md` — reproducible decision on the held German route.
7. `analysis-inventory.md` — live, secondary and stopped work.

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
not a classifier, gauge substitution, physical travel time or an operational
radius.

## Implemented in this pass

- Simplified `scripts/31_event_study_gates.py` to the binding six-file regional
  audit. Optional Kerkrade-source logic no longer turns the gate into a
  product-style status workflow.
- Kept routine chapter verification at 32 scientific checks. Moved 18 older
  daily-summary and generic IoT checks plus fixtures to
  `infrastructure_tests/`; they remain available but are not the default.
- Audited the delivered Viefhues thesis, R code, cleaned table, raw files and
  ZIP inventory. Added `scripts/33_ingest_viefhues_iot.py`, one direct pandas
  ingest with no framework and no new fixture tests.
- Replaced the general request drafts with `student-next-actions.md`: five
  ordered tasks, verified Waterschap/LANUK addresses, English email text and a
  native-delivery return rule.
- Updated the README, synthesis, protocol, inventories, data requests, live
  scope and append-only decisions log to reflect this state.

## Viefhues source finding

K4 is the useful source-native historical record. It is labelled as the
non-ABC basement sensor in the supplied R code and contains 169,594 minute rows
from 2021-05-15 to 2021-09-24. Every July 2021 civil-time hour is present. The
normaliser writes 2,829 observed UTC hourly means and reports 335 missing hours
elsewhere in the May-September span, 83 minute observations at 400 ppm and
5,761 at the 5,000-ppm ceiling. Missing hours and ceiling values are not
silently altered.

The longer `2021_flood_data.csv` is processed thesis output: it has 1,333
missing civil-time hours, a duplicated DST hour and only 550 July hours. Four
pre-May source/intermediate files referenced by the R workflow are absent from
both the folder and ZIP. K3's `livingroom` filename conflicts with the thesis
statement that both sensors were in the basement. Hardware identity,
calibration, exact ABC edits, the 450-ppm baseline adjustment and reuse terms
remain unresolved.

The observed K4 July trajectory is therefore reproducible. The conditional CO2
recurrence case is still unavailable because sensor-era provenance, a valid
hydrological pair, independent onset bounds and three later complete events do
not yet exist. That does not block the regional chapter.

## Current stop

`python scripts/31_event_study_gates.py --report-only` reports **regional
FAIL**: all six contracted long-record network inputs are absent. Do not lower
the ten-year cohort rule, use the rolling two-year record or inspect prospective
signal contrasts.

The student's immediate actions are fully specified in
`student-next-actions.md`:

1. obtain the supervisor's eight design decisions;
2. send the historical-discharge request to Waterschap Limburg;
3. send the timestamp/gap-semantics request to LANUK;
4. request only the seven unresolved Viefhues provenance items; and
5. return decisions, correspondence and native attachments without modifying
   the files.

## Agent work after the student returns

1. Inventory and hash the native deliveries; resolve sampling, timezone,
   units, missingness, rating curves, natural/managed status and July 2021 QA.
2. Fix the admissible watercourse cohort and write an ingest only after the
   delivered formats are known.
3. Build and visually verify catchment polygons, RADOLAN area averages and the
   supervisor-approved long public-weather assignment.
4. Rerun the strict regional gate. If it passes, record hashes and approvals
   and lock the protocol before outcome inspection.
5. Then implement the concise matched contrasts, one prespecified spatial
   gradient per signal, tidy outputs and four figures. Add only the synthetic
   estimator checks that protect those claims.
6. Add the Kerkrade recurrence section only if its separate evidence contract
   passes; missing case evidence is not a null CO2 result.

## Verification

Named interpreter:
`/Users/briangillikin/miniforge3/envs/chapter1-co2/bin/python`

- default scientific suite: **32 passed**;
- optional legacy infrastructure suite: **18 passed**;
- `ruff check .`: passed;
- `ruff format --check .`: passed;
- regional gate report regenerated: **FAIL**, as expected;
- Viefhues K4 normalisation regenerated: **744/744 July hours**;
- the raw Viefhues package and generated data/results remain ignored by Git.
