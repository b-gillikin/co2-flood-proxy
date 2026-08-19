# Student Next Actions

Updated 2026-08-19. The student reports that replies to all sent emails have
arrived and that the requested core data will take several weeks. The Provincie
Limburg mine-water reply and attachment have been preserved and audited; their
remaining semantic questions are recorded in `data-requests.md`. Preserve and
return the other complete replies and deliveries as they arrive. Do not lock
the protocol or inspect new signal contrasts while the remaining design choices
and regional inputs are unresolved.

## 1. Close the remaining supervisor decisions

Approved: the contribution, spatial-extent meaning, Limburg population,
ERA5-Land source, July 2021 treatment and conditional status of the CO2 case.
Only the following follow-up remains:

- confirm that the 10-watercourse/10-year/20-episode/40-storm values may remain
  prospective design floors after the explanation in
  `supervisor-decision-memo.md` §4;
- confirm the blinded 70/80/90 availability audit and commit to freezing one
  coverage rule before signal outcomes, including the proposed minimum of 10
  complete event/control contrasts per ordered pair; and
- inform the supervisor that held-out receiver-period prediction has been
  removed. The final spatial estimator uses ordered-pair medians, one fixed
  distance slope, storm resampling and leave-one-watercourse-out influence
  checks. Confirm that this directly implements the approved spatial-extent
  meaning.

The original eight-item request is retained below as the response record, not
as a new task.

Send `supervisor-decision-memo.md` before the meeting and ask for a decision,
not a general discussion, on each item below. Take notes in the wording the
supervisor actually uses.

1. **Contribution:** approve or revise the primary question: which signals
   recur before high water, and how does their event-minus-quiet magnitude
   change with distance across the observed tributary network?
2. **Meaning of transferability:** approve spatial extent estimated from all
   receiver-donor pairs. Confirm that the chapter is not intended to estimate
   gauge substitution, physical propagation, an operational radius or
   performance in ungauged basins.
3. **Population:** retain natural Limburg tributaries as the target population,
   with NRW as a possible extension only if clarified records pass the same
   gates, or specify a different population now.
4. **Data floor:** approve or revise at least 10 watercourses, 10 common years,
   20 p99 episodes per watercourse and 40 regional storms.
5. **Coverage floor:** approve or revise 80% observed hourly cells overall and
   70% in every year for discharge, RADOLAN rainfall and public weather; also
   approve 80% overall/70% by receiver and distance third for donor-flow event
   windows.
6. **Public weather:** approve ERA5-Land for 2001–2025, assigning the nearest
   fixed grid cell to each predeclared catchment centroid and deriving relative
   humidity from temperature and dew point.
7. **Spatial estimator:** note that the earlier held-out fold has been retired.
   Confirm ordered-pair medians plus one fixed log-distance slope, storm
   resampling and leave-one-watercourse-out influence checks.
8. **July 2021:** approve its inclusion as a required regional anchor, with no
   invented local onset or peak. Confirm that the new Kerkrade CO2 analysis is
   conditional rather than a gate for the regional chapter.

Immediately after the meeting, record for every item: **approved as written**,
**approved with this replacement wording**, or **not approved**. Include the
meeting date and the supervisor's name. Return those notes before any protocol
lock.

## 2. Request the long discharge archive from Waterschap Limburg

**Send to:** `info@waterschaplimburg.nl`  
**Official contact:** <https://www.waterschaplimburg.nl/contact/>  
**Subject:** Academic data request: historical Limburg tributary discharge and
gauge metadata

Use the following English text, replacing only the signature details.

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

## 3. Ask LANUK to define its verified-discharge timestamps and gaps

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

## 4. Resolve only the remaining Viefhues provenance questions

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

## 5. Return the decisions and native deliveries without modifying them

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

Once those materials are in the repository workspace, the next analysis pass
will inventory and hash them, inspect their native formats and semantics, fix
the admissible cohort, build catchment rainfall and approved public weather,
rerun the regional gate, and lock the protocol only if the gate and supervisor
decisions pass.
