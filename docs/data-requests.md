# Data Requests and Delivery Contracts

Status: 2026-09-24 (protocol draft 0.9). The native Waterschap discharge
delivery is preserved and audited. The regional gate still fails because
discharge source semantics remain unresolved. The candidate cohort, cross-border
catchments, ERA5-Land weather table and operational RADOLAN RW catchment series
are built. The Kerkrade CO2 case and the mine-water evidence
were retired from the chapter on 2026-09-18. Their deliveries remain preserved
as provenance, and the sections below that concern them are historical.

**Outreach 2026-09-17 (researcher-reported):** follow-up emails were sent to
LANUK NRW (Jens Hammersen, following his 2026-09-11 reply and its offer of
15-minute-average exports and discharge curves) and to Waterschap Limburg
(René Mols, following the 2026-09-07 metadata reply). The sent-message copies
are not yet archived, so this file does not record their exact requests.

**Outreach 2026-09-21 (researcher-reported):** the three-question follow-up was
sent to René Mols in the 2026-09-07 thread: (1) whether the source's "GMT+1"
is a fixed offset or Dutch civil time; (2) whether a delivered 0.000 can mean
an unreliable reading rather than zero discharge; (3) whether any delivered
discharge history was recomputed with a later rating relation. Fase thresholds
and stage records were included as non-blocking extras. Questions 1 and 2 block
the discharge ingest. Draft text is in `student-next-actions.md`; archive the
sent copy under `data/raw/external_deliveries/waterschap_limburg/` when
convenient.

**LANUK delivery and outreach 2026-09-23–24 (researcher-reported):** Jens
Hammersen supplied four station packages, preserved under
`data/raw/external_deliveries/lanuk_nrw/2026-09-23/`. On 2026-09-24
the researcher replied confirming download and asking for the Honsdorf
continuous 15-minute stage export, row-level reconstruction flags or
affected periods (especially July 2021), and the provisional periods
and date-applicable rating curves for Herzogenrath 1 and Randerath.
The Honsdorf stage file contains 36 dated measurements from 2012–2025,
despite its 15-minute-average filename. Await Jens’s reply; the sent
message itself has not been archived here.

## Current gate state

| component | gate | required delivery | current state |
| --- | --- | --- | --- |
| core | tributary discharge | >=5 natural, hydrologically independent watercourses (6 for the sign test); >=10 common years hourly with 80%/70% density; >=20 joint-period p99 episodes each; >=40 storms and >=15 per season | 2010–2025 native delivery received; six candidate watercourses after the independence rule; metadata and event counts unresolved |
| core | catchment rainfall | hourly radar rainfall averaged over cross-border catchment polygons | built from operational RADOLAN RW 2010–2025 (RADKLIM-RW ruled out on coverage); 0.03–0.21% hours missing per catchment |
| core | catchment polygons | one valid polygon per watercourse from a cross-border DEM | built from Copernicus GLO-30 for all seven candidates; seven area checks within ±4.4%; pour points provisional |
| core | public weather | 10 common years of relative humidity and surface pressure with a fixed assignment per watercourse | built for all seven candidates, 2001–2025, nearest cell to each catchment centroid |
| core | gauge QA | numerical coordinates, rating eras, sampling semantics, timezone, units, zero semantics and July 2021 status | **mostly resolved.** Sampling semantics, units and July 2021 station status were answered in the 2026-09-07 reply and are built into `data/interim/event_study_gauges.csv` (`scripts/44_build_event_study_gauges.py`). Rating eras are transcribed and built (D8). Coordinates were sent as Google Maps pins, not decimals; resolved 2026-09-18, they differ from the public-portal coordinates already in use by 0.1-8.8 m for all six cohort gauges, under one DEM cell — D5 stands without a re-run (`config/waterschap_gauge_coordinates_crosscheck.csv`). **Still open, and blocking the discharge ingest:** (1) whether the source's "GMT+1" label is a fixed offset or Dutch civil time with DST — not asked in either reply; (2) what a delivered zero discharge means, asked on 2026-09-07 but not answered (only blank cells were addressed); (3) **new question (2026-09-18):** was each part of the delivered discharge computed with the rating version in force at the time, or was history recomputed with a later relation? |
| conditional | stage records | Waterschap water level with datum and sensor history, for onset-timing recovery only | requested as a non-blocking extra in the 2026-09-21 follow-up; not received |
| conditional | Fase thresholds | current and historical Fase thresholds at exact crisis-plan leading gauges | requested in August; not received. Current Fase 1–3 values per gauge appear in Waterschap's public-portal location table (snapshot 2026-08-07, `data/interim/waterschap_locations.csv`); historical values and leading-gauge status still needed |
| conditional | LANUK export | 15-minute averages with reconstructed values flagged, for the distance module before lock | four station packages received 2026-09-23; Honsdorf stage export is sparse (36 measurements); reconstruction and rating-curve questions sent to Jens 2026-09-24; re-audit pending |

Run `python scripts/31_event_study_gates.py --report-only` for the executable
**regional** audit. Core failure stops the chapter pending a dated rescoping
decision. The rolling record is not a permissible core fallback. The script
encodes the draft 0.9 floors.

## 1. Original Viefhues IoT package — historical (Kerkrade case retired 2026-09-18)

Status: **source package audited; July K4 normalised; follow-up reply reported
but not yet preserved or audited**.

The delivered folder contains the thesis, presentation, analysis code, a
cleaned table spanning 2020-08-25 to 2021-09-24 and raw Kerkrade CSVs. The
source-native extended K4 file contains 169,594 minute observations from
2021-05-15 to 2021-09-24 and covers every July 2021 hour. It is the non-ABC
basement sensor in the supplied R code. `scripts/33_ingest_viefhues_iot.py`
normalises that record to UTC hourly means without filling 335 absent hours
elsewhere in its span.

The longer cleaned analysis table is not source-native. It has 1,333 missing
civil-time hours, a duplicated DST clock-hour and 550/744 July hours. The
pre-May R workflow depends on four absent source/intermediate files. The K3
filename also says `livingroom` while the thesis states that both sensors were
in the basement. Sensor hardware identity, calibration history, row-level ABC
changes and reuse conditions remain undocumented. See `iot-sources.md` for the
audit and `student-next-actions.md` §4 for the precise follow-up.

Request from Jan-Philipp Viefhues, sustainably.io and/or the Maastricht thesis
data holder only for the unresolved material:

- pre-15-May-2021 K3/K4 source-native data and the missing intermediate named
  in the R code, if they still exist;
- indoor CO2 and air pressure are required; temperature and relative humidity
  should be included if present;
- resolution of the K3 `livingroom` versus thesis-basement contradiction;
- device identifier, sensor model, unit and older timestamp/timezone convention;
- calibration and replacement history;
- whether automatic baseline correction (ABC) was enabled and whether the
  supplied values were already processed;
- exact row/date logic for ABC replacement and the 450-ppm correction;
- missing-data, duplicate and aggregation rules used in the cleaned table;
- data-use and redistribution conditions.

Why still important: the source-native July K4 trajectory can now be reproduced,
but it cannot yet be treated as a fully documented sensor era or compared with
later events under the case protocol. The regional recurrence/spatial-extent
analysis can proceed without that case.

Current/remaining products:

- `data/interim/viefhues_iot.csv` with `timestamp_utc`, `sensor_era`,
  `iot_co2_ppm`, `iot_air_pressure_hpa` and source-row count — **written from
  source-native K4**;
- `data/processed/viefhues_iot_qc.csv` — **written**;
- `data/interim/kerkrade_iot_eras.csv`, covering both the 2020–2021 and
  2025–2026 periods with `sensor_era`, `era_start_utc`, `era_end_utc`,
  `device_id`, `calibration_notes`, `abc_processing_notes` and
  `source_resolution`.

Do not assume that the 2021 and 2025–2026 instruments are the same sensor era.
The existing later hourly IoT file remains a conditional-case input. After the
long Kerkrade-pair series arrives, it must overlap at least three exact p99
onsets with all 72 pre-onset CO2 and pressure hours observed. Fewer events
cannot support a recurrence conclusion, but do not block the core chapter.

## 2. Long Limburg tributary discharge — blocking

Status: **native EML, PDF, XLSX and value-equivalent CSV received and audited
2026-08-19; provider metadata follow-up received 2026-09-07 and reviewed
2026-09-14**. The original delivery and follow-up evidence are preserved under
the dated folders in `data/raw/external_deliveries/waterschap_limburg/`.

The source supplies an exact 15-minute grid from 2010-01-01 through
2025-12-31, plus one endpoint at 2026-01-01 00:00. It contains 15 series
columns representing 14 station IDs and eight named watercourse labels. Headers
state `GMT+1`, m3/s and 15-minute means. The CSV and single-sheet XLSX are
cell-for-cell value-equivalent; the CSV is used for the transparent pandas
audit while the XLSX remains the original spreadsheet artifact.

`scripts/35_audit_waterschap_delivery.py` measures blank-cell availability
without calculating thresholds, events or signal outcomes. Nine series across
the eight named watercourses pass the provisional 80% overall/70% every-year
complete-hour rule. This is not a gate pass. There are fewer than 10 named
watercourses, and availability does not resolve whether the stations belong to
the target population or whether their values are valid.

The follow-up resolves that values are means of the preceding 15 minutes,
blanks mean unavailable data, no validation flags exist and no relocations
occurred in the requested period. It supplies rating-curve sheets and a July
2021 station-status report. Material cautions from those sources include:

- almost all gauges exceeded their measurement range in July 2021 and several
  failed from water damage, so a populated cell is not proof of validity;
- continuing gravel bars interfere with Meerssen;
- Millen is one branch of a split and carries at most 1 m3/s; Vloedgraaf
  receives the remaining Geleenbeek flow plus Rode Beek;
- Selzerbeek splits into the main branch and Molentak; 91.6% of observed
  Molentak cells are zero and zero semantics are not yet documented;
- Munstergeleen is labelled as discharge measurement from 2.5 m3/s;
- Oud-Roosteren appears twice under station ID 6.Q.27, with one column marked
  `indicatie`.

Still required before hourly discharge, p99 thresholds or events are built:

- confirmation whether `GMT+1` is fixed UTC+1 or Dutch civil time with DST,
  plus zero/sentinel semantics;
- executable rating-domain/range checks for any candidate gauge;
- numerical coordinates and natural/managed classification;
- interpretation of the special branch, threshold and duplicate columns;
- licence, citation and redistribution terms; and
- either enough additional defensible natural tributaries for the provisional
  10-watercourse floor or a recorded revision made after the blinded
  feasibility audit and before any outcome is inspected.

Primary request to Waterschap Limburg (`info@waterschaplimburg.nl`,
088 88 90 100):

1. Full available discharge history at native resolution for natural tributary
   gauges, including Geul (Cottessen, Hommerich, Meerssen), Worm (Rimburg),
   Geleenbeek (Brommelen, Munstergeleen, Millen, Oud-Roosteren), Eyserbeek,
   Gulp, Selzerbeek and Voer; request enough additional tributaries to support a
   10-watercourse common cohort.
2. Gauge identifiers, coordinates, watercourse names and relocations.
3. Units, timezone/DST convention, missing and zero-sentinel codes.
4. Native sampling convention, including whether absent timestamps are missing
   or imply a valid hold-forward interval.
5. Validation flags and rating-curve periods, especially revisions after 2021.
6. Explicit July 2021 failure/damage status and the interval over which each
   gauge is considered unreliable.
7. Current and historical Fase thresholds at exact crisis-plan leading gauges
   for sensitivity analysis only.

Academic-release precedent: Tsakiris et al. (HESS, 2024) report that Waterschap
Limburg supplied 15-minute Meerssen discharge from 1970 to August 2021. The
archive therefore exists beyond the public endpoint's rolling window.

Alternative routes, in order:

1. the HESS 2024 authors for the cleaned Meerssen series and quality notes;
2. JCAR ATRACE (`info@jcar-atrace.eu`; programme manager Kymo Slager), which is
   assembling transboundary Geul/Roer evidence after the 2021 flood;
3. LANUK NRW replacement 15-minute exports. LANUK confirms that the held
   verified-discharge archive is an inflection-point series in which constant
   values cannot be distinguished from gaps and no hold-forward rule exists;
   it fails the draft density/episode gate under conservative no-fill handling.
   The public
   metadata also show that `herzogenrath_2` and `honsdorf` are on Broicher Bach
   and Beeckflies, not the Wurm; the two held Wurm gauges do not overlap the
   later IoT era. See `lanuk-feasibility.md`;
4. RWS Waterwebservices for main-stem source validation, not as a substitute
   for the tributary population.

The Waterschap correspondence, discharge delivery and metadata follow-up are
preserved. See `waterschap-source-metadata.md` for the station-level usability
assessment. The regional gate remains closed; the reply does not supply enough
natural watercourses or resolve timezone, zero and cohort semantics.

Routes already ruled out: the Waterstandlimburg OData endpoint before
2024-08-06, the unfinished open.waterschaplimburg.nl portal, GRDC for the small
tributaries, and daily CAMELS-DE (ends 2020 and misses July 2021).

On receipt, inspect the native files before writing an ingest. Then produce:

- `data/interim/event_study_discharge_hourly.csv`, a regular UTC grid with one
  column per candidate gauge and missing hours left missing;
- `data/interim/event_study_gauges.csv` with at least `gauge`, `watercourse`,
  `latitude`, `longitude`, `include_primary`, `natural_tributary`,
  `rating_curve_verified`, `timezone_verified`, `units_verified`,
  `zero_sentinel_verified`, `sampling_semantics_verified`, `july_2021_status`,
  `july_2021_onset_lower_utc` and `july_2021_onset_upper_utc`.

If Worm/Wurm is unavailable, add `kerkrade_pair` and `pairing_rationale`; the
rationale must be hydrological and agreed before outcome inspection.

## 3. Long public weather — raw source archive complete

Status: **ERA5-Land approved; all 300 monthly source files acquired and
audited**.

Temperature, relative humidity and pressure are fixed primary signals.
ERA5-Land was chosen before event contrasts because it supplies one consistent
hourly 0.1° field across Limburg and the cross-border margin. The fixed raw
extract covers 2001–2025 and retains 2 m temperature, 2 m dew-point temperature
and surface pressure. After the cohort and catchment polygons are verified,
assign the nearest grid cell to each catchment centroid, document shared cells
and derive relative humidity from temperature and dew point using one fixed
formula.

The dedicated Function under `infrastructure/era5_backfill/` requested one
month at a time over the fixed bounding box, persisted the CDS request ID,
validated timestamps, variables, units and missing cells, and wrote source
hashes to Blob Storage. Full-year requests exceed the CDS 12,000-field limit,
so the restart-safe monthly partition was retained.

The final audit on 2026-08-14 downloaded and reopened all 300 source NetCDFs.
Every file contained the expected complete hourly UTC month, `t2m`, `d2m` and
`sp` variables in K, K and Pa respectively, with no missing grid cells. The
recomputed manifest was byte-for-byte identical to the cloud manifest: 300
unique periods, 300 unique blob names, 300 unique SHA-256 values, no missing or
extra months and 310,537,386 total source bytes. The backfill-only Function App
was then stopped, which disables its five-minute timer. No outcome inspection
was involved.

No second weather product will be added as a parallel sensitivity. Visual
Crossing remains Eryilmaz predecessor context only.

Deliver:

- `data/interim/event_study_weather_hourly.csv`, a regular tidy UTC grid with
  `timestamp_utc`, `watercourse`, `temperature_c`,
  `relative_humidity_pct` and `pressure_hpa`;
- `data/interim/event_study_weather_sources.csv`, one row per primary
  watercourse with `watercourse`, `source_id`, `source_type`,
  `spatial_assignment`, `timezone_verified` and `units_verified`.

The files must provide 10 years common to the discharge and RADOLAN cohort.
The assignment must support values at every cohort watercourse;
spatial contrasts use all eligible pairs rather than a nearest-site subset.

## 4. RADOLAN catchment rainfall — blocking

Status (2026-09-18): **acquisition running**. RADKLIM-RW was checked first, as
protocol §6 prefers it, but it is masked outside a band around Germany. It
never observes the Voer catchment and misses 45% of the Gulp. Operational
RADOLAN RW observes every candidate catchment and is being downloaded for
2010–2025 (`scripts/37_fetch_radar.py`); `scripts/41_radar_catchment_rainfall.py`
builds the catchment series. Details are in `decisions.md` (2026-09-18).

DWD RADOLAN `RW` is gauge-adjusted 1-km hourly radar rainfall from 2005 onward.
The July 2021 monthly archive was previously verified as downloadable. It is
the principal rainfall exposure because point stations are too coarse for
27–77 km2 tributary catchments.

Required work after the discharge cohort is fixed:

1. obtain the complete hourly RADOLAN period overlapping at least 10 common
   discharge years;
2. obtain or delineate one verified polygon per primary watercourse;
3. preserve the native CRS, transform polygons explicitly and record the
   area-weighting method;
4. convert RADOLAN missing/no-data codes to missing before any sum or spatial
   mean;
5. calculate area-weighted catchment means on each hourly grid;
6. audit boundary cells and coverage, including July 2021.

Deliver:

- `data/interim/event_study_catchments.gpkg`;
- `data/interim/radolan_catchment_hourly.csv` with `timestamp_utc` and one
  column named for each primary watercourse;
- a small provenance table recording RADOLAN product/version, files, CRS,
  missing codes, polygon source and spatial weighting.

EStreams boundaries may be a starting point but must be visually and
hydrologically checked. Point-gauge rainfall is not a substitute for
catchment-average RADOLAN rainfall. ERA5-Land (~9 km) is also not a rainfall
substitute.

## 5. July 2021 gauge evidence — core status, conditional local bounds

The Deltares rapid assessment reports missing/damaged Geul peaks and warns that
surviving flood discharge observations may be unreliable. Independently, some
LANUK gauges stop before the flood. Therefore July 2021 is interval-censored,
not missing at random.

Every core gauge needs a documented July 2021 status. For the conditional
Kerkrade case, request or extract:

- last reliable pre-failure observation;
- first reliable post-failure observation;
- any water-level, discharge, damage or model evidence bounding high-water
  onset;
- rating-curve applicability during the event.

Store the lower and upper onset bounds in the Kerkrade-pair row of
`event_study_gauges.csv`. The analysis will not invent a peak or exact time.

## 6. Groundwater and mine water — secondary

Status: **Provincie Limburg reply and one native CSV received 2026-08-19**.
The untouched EML, mailbox PDF and attachment are preserved under
`data/raw/external_deliveries/provincie_limburg/2026-08-19/` with SHA-256
checksums in `receipt.txt`. The CSV decoded from the EML is byte-identical to
the separately preserved attachment.

The province confirms that GMW000000091726 (Willem) and GMW000000091599 are
mine-water-network points. The delivered file contains the former Willem shaft
record (`WILLEM OUD`, 2000-08-14--2022-10-21) and its adjacent replacement
(`WILLEM`, 2023-12-15--2026-06-07) as two source-native station codes. The old
record contains 31 daily July 2021 observations. The replacement contains no
July 2021 observations. The provider attributes the intervening gap to shaft
remediation/replacement and other gaps to equipment failures.

The file is not analysis-ready. Timezone, validation status, the exact
`Waarde (m -NAP)` convention, repeated `-90`/`-94`/zero values, authoritative
identifier mapping, continuity across the replacement and redistribution terms
remain unresolved. Do not recode or join the two station records until those
points are answered. These data may help interpret the Kerkrade mechanism but
cannot rescue or block the chapter.

Already received: three BRO Gemeente Heerlen wells at 2.85–3.60 km, nominally
six-hourly from 2021-01-01 to 2025-08-27 (16,532 readings). They are shallow
phreatic wells, not mine shafts; screen-depth metadata are incomplete and no
data were published after 2025-08-27 in the earlier retrieval. The province
clarifies that these wells are in Kerkrade and directs current observations to
the provincial Veldoffice portal, with validated series entering the BRO after
a delay. Treat them as secondary contextual evidence.

## Receipt rule

For every delivered dataset, preserve the raw file, licence and request
correspondence; record a checksum; inspect units/timezone/sentinels before
aggregation; and update this file plus the append-only `decisions.md`. Passing
the **core** executable gate still requires the recorded floor decisions before
the protocol is locked. Kerkrade materials may be added only if their separate case
gate passes before that case's outcomes are inspected.

The detailed five-task handoff, verified institutional addresses and message
texts are in `student-next-actions.md`. The student reports that the contact
messages have been sent; preserve the sent messages and replies on receipt.
