# Student Next Actions

Updated 2026-09-18 (afternoon) for protocol draft 0.9. First written
2026-08-19. All eight design decisions (D1–D8) are recorded in `decisions.md`
and built into the pipeline (68 tests passing). Every core regional input
except the discharge series is built: gauge metadata, rating eras, catchment
polygons, catchment rainfall (RADOLAN 2010–2025) and public weather are all in
`data/interim/`. The discharge ingest itself is written and tested
(`scripts/45_build_event_study_discharge.py`) but refuses to produce the core
file until Waterschap's semantics are verified — see task 1. **This is now the
only blocker.** Preserve and return other complete replies and deliveries as
they arrive. Do not lock the protocol or inspect any signal contrast before
the discharge series is committed and the blinded feasibility audit
(`scripts/31_event_study_gates.py`) has run against it.

## 1. Send a short, targeted Waterschap follow-up

Design decisions are the author's, recorded and dated in `decisions.md` before
any signal outcome is inspected; that timing, not a supervisor signature, is
what protects the chapter. The supervisor is informed of decisions that change
the chapter's shape; work does not wait on a reply from them, and none of the
three questions below need their input.

Everything that could be resolved without Waterschap is done: the cohort
(D3), the rating eras (D8), and a coordinate cross-check that confirms the
provisional pour points to within 8.8 m using Waterschap's own map pins from
the 2026-09-07 reply (`config/waterschap_gauge_coordinates_crosscheck.csv`).
That reply also already answered sampling semantics, units and July 2021
station status, which earlier drafts of this file listed as still open — they
are not.

**Exactly three questions are still open, all in the same email thread as the
2026-09-07 reply.** Two of them were asked before but not actually answered;
the third is new. Suggested text:

**Send to:** `R.Mols@waterschaplimburg.nl` (same thread as the 2026-09-07 reply)  
**Subject:** Re: data request — three remaining questions

> Dear René,
>
> Thank you again for the rating curves, the July 2021 report and the station
> details. Three specific points from my original list are still open; the
> data are otherwise ready to use.
>
> 1. **Timezone.** The delivery header labels the time axis "GMT+1". Is this a
>    fixed UTC+1 offset all year, or Dutch civil time (CET in winter, CEST in
>    summer, i.e. following daylight saving)? This matters for placing events
>    to the correct hour, especially around the March and October clock
>    changes.
> 2. **Zero values.** My third question asked about the meaning of absent
>    timestamps, missing codes, zeros and sentinel values together; your reply
>    addressed absent timestamps only. Does a delivered value of exactly 0.000
>    always mean zero discharge, or can it also mean an unreliable or
>    non-operational reading, the way a blank cell does?
> 3. **Rating-curve history and the delivered series.** For a station whose
>    rating relation changed over 2010–2025 (for example Azijnfabriek on the
>    Gulp), was each part of the delivered discharge series computed with the
>    rating relation in force at that time, or was some of the history
>    recomputed later using a newer relation? I ask because the 1997–2006
>    Azijnfabriek relation was recomputed once already, in 2007.
>
> Kind regards,
>
> [full name]

Save the sent message and any reply the same way as the original thread.

**Optional, non-blocking, can go in the same email if convenient:** water-level
(stage) records with datum and sensor history, for recovering the timing of a
censored onset where discharge is missing; and current and historical Fase
warning thresholds at the exact crisis-plan leading gauges (current values are
already on the public portal). Neither is needed to ingest discharge or run
the blinded feasibility audit.

The original 2026-08 request text is retained below as a correspondence
record. Do not send it again.

> Dear Waterschap Limburg water-information or hydrology team,
>
> I am a PhD researcher at UNU-MERIT studying which public
> hydrometeorological signals recur before high-water episodes across Limburg
> tributaries, and how the spatial footprint of those signals changes with
> distance. The public Waterstanden Limburg endpoint available to me is a
> rolling record beginning in August 2024, which is too short for an event
> recurrence study.
>
> Could you provide the full available historical discharge series, preferably
> at its native resolution and in its existing native format, for natural
> tributary gauges including:
>
> - Geul: Cottessen, Hommerich and Meerssen;
> - Worm: Rimburg;
> - Geleenbeek: Brommelen, Munstergeleen, Millen and Oud-Roosteren;
> - Eyserbeek, Gulp, Selzerbeek and Voer; and
> - enough additional natural tributary watercourses to assess at least ten
>   watercourses over a common period of ten or more years that includes July
>   2021.
>
> Please provide 1 January 2010 through 31 December 2025. I do not need the
> pre-2010 archive. Native 15-minute data are preferable; I will aggregate to
> hourly values only after checking continuity and source conventions.
>
> For each gauge, could you also provide or identify:
>
> 1. station identifier, coordinates, watercourse and any relocation history;
> 2. units, timezone and daylight-saving convention;
> 3. native sampling and any aggregation convention;
> 4. the meaning of absent timestamps, missing codes, zeros and sentinel
>    values;
> 5. validation flags and the dates of applicable rating curves or revisions;
> 6. known damage, failure, censoring or unreliable-data intervals during July
>    2021, including any evidence that bounds high-water onset; and
> 7. licence, citation and redistribution conditions.
>
> If available, I would also appreciate current and historical crisis-plan
> Fase thresholds for their exact designated leading gauges. These would be
> used only as a sensitivity analysis, not imposed on other gauges.
>
> This is a non-commercial academic information request and does not involve
> personal data. I will preserve the native files, document all transformations
> and quality flags, and leave missing values missing unless the source
> convention explicitly supports another treatment. If another team handles
> historical hydrometric data, please forward this message or tell me whom to
> contact.
>
> Kind regards,
>
> [full name]  
> PhD researcher, UNU-MERIT  
> [UNU-MERIT email]  
> [optional telephone]

Save the sent message as `.eml` or PDF. When a reply arrives, preserve every
attachment in its native format; do not open and resave CSV or spreadsheet
files before returning them.

## 2. Ask LANUK to define its verified-discharge timestamps and gaps

**Send to:** `poststelle@lanuk.nrw.de`  
**Ask them to route it to:** Fachgebiet 51.4, Pegelwesen Süd  
**Official contact/organisation source:**
<https://www.lanuk.nrw.de/fileadmin/lanuv/service/GVP/GVP_Aktuell.pdf>  
**Data product:**
<https://www.opengeodata.nrw.de/produkte/umwelt_klima/wasser/oberflaechengewaesser/hydro/q/>  
**Subject:** Academic question about timestamps and gaps in verified discharge
data

Use the following English text, replacing only the signature details.

> Dear LANUK NRW team,
>
> Please route this question to Fachgebiet 51.4, Pegelwesen Süd, if
> appropriate.
>
> I am a PhD researcher at UNU-MERIT studying the spatial extent of
> hydrometeorological signals before high-water events in the cross-border
> Rur-Wurm region. I am assessing the verified discharge CSV archives published
> through OpenGeodata NRW. I am not yet using signal outcomes; I first need to
> interpret the source time axis correctly.
>
> In the downloaded verified-discharge files, timestamps are irregular and
> sometimes fall outside a regular 15-minute grid. Could you clarify the
> following?
>
> 1. Does each CSV row represent an individual observation, or are these
>    compressed step/change series?
> 2. Does an omitted timestamp mean that discharge is missing, or is the last
>    published value valid until the next timestamp? If it is valid, what is
>    the maximum permitted hold-forward duration?
> 3. At what stage are the published discharge values verified, and how can a
>    user identify the applicable rating curve and later revisions?
> 4. What codes or rules define missing, zero, invalid and estimated values?
> 5. Are there documented closure, failure, damage or unreliable-data periods
>    around July 2021 for the following stations?
>
>    - 2828300000200 — Herzogenrath 1 (Wurm)
>    - 2828400000200 — Herzogenrath 2 (Broicher Bach)
>    - 2828890000200 — Honsdorf (Beeckflies)
>    - 2828900000200 — Randerath (Wurm)
>
> 6. For Herzogenrath 1 and Randerath, are validated July 2021 discharge or
>    water-level observations available from another archive even though they
>    are absent from the verified-discharge files I downloaded?
>
> I need to avoid both treating a compressed series as gauge downtime and
> carrying a value through hours that were not observed. A data dictionary,
> quality-code document, rating-curve history or contact with the responsible
> hydrologist would therefore be very helpful. I will cite the source and
> retain its published missing-data convention.
>
> Kind regards,
>
> [full name]  
> PhD researcher, UNU-MERIT  
> [UNU-MERIT email]  
> [optional telephone]

Save the sent message and all replies. A short answer such as “hold the value
until the next timestamp” is not enough by itself: ask for the maximum valid
duration and the document or quality rule that authorises it.

## 3. Resolve only the remaining Viefhues provenance questions

> **Historical (2026-09-18).** The Kerkrade CO2 case was retired in draft 0.9.
> These questions no longer block anything; pursue them only for the provenance
> record of the motivating observation.

The delivered package is useful but incomplete. The source-native K4 record
already supplies every July 2021 hour at minute resolution, so do **not** ask
for the same July CSV again. Reply through the channel that delivered the
package and ask for these specific unresolved items:

1. The thesis says that two sensors were in the basement, but the delivered K3
   file is named `K3_livingroom`. Which room was K3 actually in, and did either
   sensor move during 2020–2021?
2. Can they supply the pre-15-May-2021 source files named
   `kerkrade3tillJune1.csv` and `kerkrade4tillJune1.csv`, plus `metadata.json`
   and the generated intermediate
   `total_Dataset_with_adjusted_ABC.csv`? These files are referenced by the R
   code but absent from both the extracted folder and ZIP.
3. Confirm that K3 had automatic baseline correction enabled and K4 did not.
   Request the exact dates/rows changed by the ABC repair and the rationale for
   applying the 450-ppm baseline addition.
4. Request sensor manufacturer/model, hardware or channel ID, serial number if
   available, calibration date/method, replacement history and known 5,000-ppm
   ceiling behaviour.
5. Confirm the timestamp convention in the older source files and whether the
   final cleaned `Date` field is Europe/Amsterdam civil time.
6. Ask which sensor contributes to each period of
   `cleaned_data/2021_flood_data.csv`, how duplicate hours were combined and
   why the cleaned analysis table omits many otherwise available July K4 hours.
7. Request the data-use, quotation and redistribution conditions for the raw
   sensor exports and code.

If these files or metadata no longer exist, obtain that statement in writing.
That limits the scope of the case; it does not block the regional chapter.

## 4. Return the decisions and native deliveries without modifying them

Create one folder per source and delivery date under the ignored raw-data tree:

```text
data/raw/external_deliveries/
  waterschap_limburg/YYYY-MM-DD/
  lanuk_nrw/YYYY-MM-DD/
  viefhues_followup/YYYY-MM-DD/
  provincie_limburg/YYYY-MM-DD/
```

For each source, include:

- the original sent message and complete reply as `.eml` or PDF;
- every attachment with its original filename and extension;
- any data dictionary, rating-curve file, licence or terms document;
- a short plain-text note listing the sender, delivery date and anything said
  only in the email body.

Do not rename, edit, convert, concatenate or resave a delivered data file. Do
not unzip over an earlier delivery. If a source sends a link, save the message
containing the link and record the download date. Return the supervisor notes
from task 1 alongside the three delivery folders.

Once Waterschap answers the three questions in task 1, the remaining steps are
mechanical and already scripted: run `scripts/45_build_event_study_discharge.py`
with the verified timezone and zero assumptions and `--commit`, run
`scripts/31_event_study_gates.py` for the blinded feasibility audit (episode
and storm counts, not signal associations), freeze the audit result in
`decisions.md`, then write and run the estimation script against the primary
and secondary specifications in protocol §7. No further design decision is
expected to block that sequence.
