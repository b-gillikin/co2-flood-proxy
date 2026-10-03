# Session Handoff

Updated 2026-09-29 after the literature-checked retrospective review. Session state only; use the synthesis and protocol for
chapter claims.

Read in this order:

1. `chapter-synthesis.md` — canonical question, contribution, design and state.
2. `chapter-scope-and-preregistration.md` — draft 0.10 internal case-crossover analysis protocol.
   `draft-0.9-implementation-plan.md` — historical build sequence; its stop
   rules have been superseded.
3. `supervisor-decision-memo.md` — the 2026-08 supervisor response and the rationale for the provisional floors (historical record).
4. `student-next-actions.md` — current student tasks and sent requests.
5. `data-requests.md` — delivery contracts and blockers.
6. `analysis-inventory.md` — prospective, supporting and retired work.
7. `literature-source-notes.md`, `literature-evidence-matrix.csv` and
   `chapter-references.bib` — source corpus for the student-authored review.
8. `dissertation-research-and-code-guidelines.md` — reusable standard for
   scoping, evidence, coding and review across the remaining chapters.
9. `limburg-next-pass-method-note.md` — observed-rainfall diagnostic and the
   literature-checked interpretation decision and bounded simulated-storm
   prospect; the original estimand remains documented.
10. `cross-tributary-pilot-2026-10-03.md` — exploratory return to regional
    high-water footprint and onset timing, including the new LANUK export audit;
    it does not yet replace the live protocol.

## Current chapter

Redesigned on 2026-09-18 (protocol draft 0.9; rationale in `decisions.md`). The
chapter is a **time-stratified case-crossover study** asking how public signals
in the 72 hours before high-water onset are associated with onset, and whether
the timing differs between warm and cold seasons.

- **Outcome:** adjacent-hour crossing of each watercourse's own p99, per rating
  era.
- **Comparison:** at-risk hours in watercourse × year × month × hour-of-day
  strata.
- **Exposures:** hourly catchment rainfall (principal); ERA5-Land relative
  humidity and six-hour pressure change.
- **Model:** conditional quasi-Poisson with distributed-lag cross-bases over lags
  1–72 hours.
- **Primary estimand:** the warm-minus-cold difference in the rainfall
  lag-response.
- **Uncertainty:** calendar year-month block bootstrap.

Dropped: the distance slope, which survives only as a separately labelled
conditional LANUK module; the Kerkrade CO2 case and mine water, now motivation only; the
five-nearest-quiet-hour controls; temperature and pressure level.

## Data state

Audit information benchmarks after source semantics are resolved: five natural,
hydrologically distinct watercourses, ten common years, 40 regional storms,
15 per season, 20 episodes per watercourse and 80% overall/70% annual coverage.
These are not chapter-stopping thresholds. July 2021 is a historical case;
cross-watercourse signs are descriptive, with no independent-sign test. Record
the supported claim scale and any outcome-informed changes in `decisions.md`.

Waterschap supplied one exact quarter-hour grid for 2010--2025 with 15 series
columns, 14 station IDs and eight named watercourse labels. The CSV and XLSX
are cell-for-cell value-equivalent. The 2026-09-07 provider follow-up confirms
trailing 15-minute means, unavailable blank cells, no validation flags and no
relocations. It also supplies rating curves and station-specific July 2021
failure and range evidence.

René's answers relayed on 2026-09-29 confirm fixed GMT+1 without DST, true
zero discharge, and period-applicable rating relations with any retrospective
corrections documented in the data file. The current H1/H2/H3 threshold CSV is
archived; historical thresholds are unavailable. No stage datum or sensor
history was supplied. The six-gauge hourly discharge series has been built,
including a correction to align trailing quarter-hour means to their hour-end
label. The input audit passes all 19 binding contracts. The first real-data
fit is in ignored local `results/event_study/real_data_v1/`; read
`limburg-first-fit-review.md` and `limburg-first-fit-results-guide.md` before
using its numbers. The cumulative fixed-rainfall contrast lies outside observed
72-hour rainfall-history support and is not a realistic storm effect size.
The follow-up diagnostic in `limburg-next-pass-method-note.md` shows a strong
descriptive 1–24 h rainfall contrast at onset, a much weaker 25–72 h contrast,
and an observed maximum 72 h case total about half of the fixed model
contrast. An explicitly exploratory two-window fit, with 999 joint-block
bootstrap draws, is documented there too. Neither replaces the original
estimand or constitutes a forecast exercise.
The subsequent matched-support review finds roughly 74% of onsets above every
control hour for 1–24 h rain, but only 11% for 25–72 h rain. Source sums,
selected hydrographs and joint 192-month descriptive intervals are checked.
Interpret the observed matched contrast first; retain the original null
seasonal median-lag comparison and weather block as qualified model results.
The outcome-informed interpretation decision is recorded in `decisions.md`.

A targeted follow-up covering these items went to René Mols on 2026-09-21 in
the existing thread. Its sent-message export and the native reply are not archived;
the reply text was pasted by the researcher. The earlier
2026-09-17 follow-up also remains recorded in `docs/data-requests.md`.
Jens Hammersen supplied four LANUK station packages on 2026-09-23; the
researcher confirmed download and asked on 2026-09-24 for the continuous
Honsdorf stage series, reconstruction flags/periods and provisional discharge
curve history. Jens supplied the missing continuous Honsdorf stage export on
2026-10-01 and expects to answer the other questions next week. See
`lanuk-honsdorf-stage-audit-2026-10-01.md`. Await the remaining LANUK answers;
do not resend the request now.

Candidate cohort: Eyserbeek, Geul (Cottessen), Gulp, Voer, Worm (Rimburg), and
Geleenbeek or Vloedgraaf. Those two count once if their high flows are shared
below the Millen split. That is six: one to spare for the core floor, and none
for the former breadth benchmark. Selzerbeek is out.
The review found 724 exact p99 onsets in 240 storms; 721 onsets in 239 storms
have complete 72-hour rainfall histories for the primary fit.

The Viefhues K4 record and the Provincie Limburg mine-water delivery remain
preserved under `data/raw/external_deliveries/` as provenance for the
motivating observation. They are no longer inputs to the chapter.

## ERA5-Land acquisition

The ERA5-Land backfill completed all 300 months from 2001-01 through 2025-12 in
`stkerkradeprod01bg` / `era5-land`. The final 2026-08-14 audit downloaded and
reopened all files, revalidated timestamps, variables, units and missing cells,
and recomputed sizes and SHA-256 hashes. Its manifest was byte-for-byte
identical to the cloud manifest: 300 unique periods, blobs and hashes, zero
missing/extra months and 310,537,386 total bytes.

The Function App remains available and HTTPS-only but is **Stopped**, which
definitively disables its five-minute timer. The defense-in-depth settings also
remain `ERA5_ENABLED=false` and
`AzureWebJobs.era5_backfill_timer.Disabled=true`. The running Python host did
not honor the trigger-specific setting alone, so stopping this backfill-only app
is the operative control. Azure reported no invocation at the first subsequent
five-minute boundary (13:35 UTC). SCM basic publishing remains closed. The
local fetch script is a fallback only.

The same 300 source files are available in the ignored local working cache at
`data/raw/era5_land/`. `data/raw/era5_land/manifest.csv` is identical to the
versioned `data/processed/era5_land_manifest.csv`; the raw NetCDF files remain
outside Git.

ERA5-Land is the only regional weather source. The user stopped the retired
KNMI Azure Function App; its app and stored blobs were not deleted.

## Code-review result

The live analysis tree was reduced by more than 1,900 net lines. Removed:

- the later-era Eryilmaz re-fit and Visual Crossing join;
- rolling two-year Waterschap and RWS main-stem pipelines;
- DWD point-rain sensitivity;
- holdout/time-block helpers and their tests;
- the obsolete weather-source note and unused environment dependencies.

Eryilmaz remains predecessor evidence in the source corpus. The later-IoT and
Viefhues ingests remain as provenance for the motivating observation; the
conditional Kerkrade case was retired in draft 0.9.
LANUK acquisition/feasibility code remains to reproduce the failed German
route. LANUK's 2026-09-11 reply confirms inflection-point change series but says
constant values and gaps cannot be distinguished and gives no hold-forward
rule; the conservative no-fill audit therefore stands. Azure collection code
is operational infrastructure, not chapter analysis.

The event helper now requires timestamps as well as rows to be exactly one hour
apart, preventing a false p99 crossing across an omitted timestamp. A focused
regression test protects that scientific rule.

## Next work

Decisions D1–D8, catchment polygons, RADOLAN RW catchment rainfall, public
weather and the verified hourly discharge ingest are built. Review the input
audit and event/era validity, then proceed to the transparent analysis. Record
any analysis choices or exclusions in `decisions.md`; the protocol is internal
documentation, not formal preregistration.
LANUK's separate follow-up may inform the conditional distance module before
lock but does not replace the core discharge source.

## Verification

Interpreter:
`/Users/briangillikin/miniforge3/envs/chapter1-co2/bin/python`

- literature crosswalk: 44 notes, 44 BibTeX keys, 98 matrix rows and 37 unique
  DOIs; all keys resolve;
- default scientific suite: **68 passed** (2026-09-18);
- operational infrastructure suite: **5 passed**;
- Ruff lint and format: passed across **47 files**;
- ERA5 raw archive: **300/300 months complete**; all NetCDF checks passed;
  recomputed and cloud manifests byte-identical; 300 unique hashes;
  backfill-only Function App stopped;
- input audit: **19/19 binding contracts PASS** (2026-09-29); first 999-draw
  association fit complete, with the limitations in
  `limburg-first-fit-results-guide.md`;
- Waterschap delivery: 561,024 requested-period quarter-hours on an exact grid;
  15 series, 14 station IDs, eight named watercourse labels; XLSX/CSV values
  equivalent; no outcomes inspected;
- Viefhues real-file QC: 169,594 source rows, 2,829 hourly rows and 744/744 July
  hours.
