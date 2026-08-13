# Data Requests and Delivery Contracts

Status: 2026-08-13. The student reports that all email contacts have replied and
that the requested data will take several weeks. No reply files or new native
datasets have yet been added to the repository, so the gates below are
unchanged. Core network deliveries are binding for the regional event study.
Kerkrade IoT and local-onset deliveries govern a conditional case study.

## Current gate state

| component | gate | required delivery | current state |
| --- | --- | --- | --- |
| Kerkrade case | original IoT | July 2021 source CO2/pressure plus device/calibration/ABC metadata | source-native K4 is normalised with complete July hours; broader lineage and device metadata remain incomplete |
| Kerkrade case | sensor-era map | non-overlapping provenance records for the 2020–2021 and 2025–2026 devices | absent; current device history incomplete |
| core | tributary discharge | >=10 natural watercourses, >=10 common years hourly with draft 80%/70% density, >=20 joint-period p99 episodes each, >=40 storms | absent; rolling Waterschap file is only 2024–2026 and held LANUK does not pass |
| Kerkrade case | hydrological pair | Worm/Wurm or documented pair plus independently supported July 2021 bounds | not established in a qualifying common record |
| Kerkrade case | later recurrence | >=3 exact pair events with complete 72-hour CO2/pressure windows | held LANUK Wurm gauges have no later-IoT overlap |
| core | catchment rainfall | hourly 1-km RADOLAN averages over verified polygons | absent; point stations do not qualify |
| core | public weather | 10 common years of temperature, humidity and pressure with a fixed assignment per watercourse | ERA5-Land approved and being acquired |
| core | gauge QA | coordinates for all pair distances, rating curves, sampling semantics, timezone, units, zero sentinels and July 2021 status | incomplete |

Run `python scripts/31_event_study_gates.py --report-only` for the executable
**regional** audit. Core failure returns the chapter to the supervisor. The
conditional Kerkrade case is assessed separately after its pair/onset inputs
exist; failure removes that case only. The rolling record is not a permissible
core fallback.

## 1. Original Viefhues IoT package — conditional Kerkrade case

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

Status: **reply reported; native discharge delivery expected in several weeks**.

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
3. LANUK NRW clarification or replacement exports. The held verified-discharge
   archive contains irregular timestamps and fails the draft density/episode
   gate after deduplication by officially matched watercourse. The public
   metadata also show that `herzogenrath_2` and `honsdorf` are on Broicher Bach
   and Beeckflies, not the Wurm; the two held Wurm gauges do not overlap the
   later IoT era. See `lanuk-feasibility.md`;
4. RWS Waterwebservices for main-stem source validation, not as a substitute
   for the tributary population.

The Waterschap and LANUK messages in `student-next-actions.md` were reported
sent by the student on 2026-08-10. Replies were reported on 2026-08-13, but the
correspondence and any commitments have not yet been preserved in the repo.

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

## 3. Long public weather — approved source, cloud acquisition in progress

Status: **ERA5-Land approved and being acquired unattended in Azure**.

Temperature, relative humidity and pressure are fixed primary signals.
ERA5-Land was chosen before event contrasts because it supplies one consistent
hourly 0.1° field across Limburg and the cross-border margin. The fixed raw
extract covers 2001–2025 and retains 2 m temperature, 2 m dew-point temperature
and surface pressure. After the cohort and catchment polygons are verified,
assign the nearest grid cell to each catchment centroid, document shared cells
and derive relative humidity from temperature and dew point using one fixed
formula.

The dedicated Function under `infrastructure/era5_backfill/` requests one
month at a time over the fixed bounding box, persists the CDS request ID,
validates timestamps, variables, units and missing cells, and writes source
hashes to Blob Storage. Full-year requests exceed the CDS 12,000-field limit.
A valid five-hour annual block was benchmarked but took 16 minutes versus
roughly four minutes for a full-day month, so the restart-safe monthly
partition is retained. The laptop process was stopped after September 2005;
Azure adopted and completed its October 2005 request. At that verification,
the container held the contiguous 2001-01--2005-10 sequence plus five later
benchmark months. No outcome inspection is involved.

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
The assignment must support values at every receiver and donor watercourse;
spatial contrasts use all eligible pairs rather than a nearest-site subset.

## 4. RADOLAN catchment rainfall — blocking

Status: **source verified; not yet built**.

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

Status: provincial/mine-water questions sent 2026-08-06 to
`meetnetbeheer@avallo.nl`, cc `infopuntmijnbouw@prvlimburg.nl`; awaiting reply.

Questions concern closer provincial wells, mine-water monitoring, screen depth,
measurement frequency, pumping schedules and the 2025 publication stop. These
data may help interpret the Kerkrade mechanism but cannot rescue or block the
chapter.

Already received: three BRO Gemeente Heerlen wells at 2.85–3.60 km, nominally
six-hourly from 2021-01-01 to 2025-08-27 (16,532 readings). They are shallow
phreatic wells, not mine shafts; screen-depth metadata are incomplete and no
data were published after 2025-08-27. Treat them as secondary contextual
evidence.

## Receipt rule

For every delivered dataset, preserve the raw file, licence and request
correspondence; record a checksum; inspect units/timezone/sentinels before
aggregation; and update this file plus the append-only `decisions.md`. Passing
the **core** executable gate still requires supervisor approval before the
protocol is locked. Kerkrade materials may be added only if their separate case
gate passes before that case's outcomes are inspected.

The detailed five-task handoff, verified institutional addresses and message
texts are in `student-next-actions.md`. The student reports that the contact
messages have been sent; preserve the sent messages and replies on receipt.
