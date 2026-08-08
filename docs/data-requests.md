# Data Requests and Delivery Contracts

Status: 2026-08-08. Core network deliveries are binding for the regional event
study. Kerkrade IoT and local-onset deliveries govern a conditional case study.

## Current gate state

| component | gate | required delivery | current state |
| --- | --- | --- | --- |
| Kerkrade case | original IoT | Aug 2020–Sep 2021 CO2 and pressure plus device/calibration/ABC metadata | package has a cleaned Aug 2020–Sep 2021 table, raw May–Sep 2021 basement files and ABC code; contract not normalised or audited |
| Kerkrade case | sensor-era map | non-overlapping provenance records for the 2020–2021 and 2025–2026 devices | absent; current device history incomplete |
| core | tributary discharge | >=10 natural watercourses, >=10 common years hourly with draft 80%/70% density, >=20 joint-period p99 episodes each, >=40 storms | absent; rolling Waterschap file is only 2024–2026 and held LANUK does not pass |
| Kerkrade case | hydrological pair | Worm/Wurm or documented pair plus independently supported July 2021 bounds | not established in a qualifying common record |
| Kerkrade case | later recurrence | >=3 exact pair events with complete 72-hour CO2/pressure windows | held LANUK Wurm gauges have no later-IoT overlap |
| core | catchment rainfall | hourly 1-km RADOLAN averages over verified polygons | absent; point stations do not qualify |
| core | public weather | 10 common years of temperature, humidity and pressure with a fixed assignment per watercourse | source/assignment not selected |
| core | gauge QA | coordinates for all pair distances, rating curves, sampling semantics, timezone, units, zero sentinels and July 2021 status | incomplete |

Run `python scripts/31_event_study_gates.py --report-only` for the executable
audit. Core failure returns the chapter to the supervisor; Kerkrade-case failure
removes that case only. The rolling record is not a permissible core fallback.

## 1. Original Viefhues IoT package — conditional Kerkrade case

Status: **source package delivered locally; audit and metadata follow-up pending**.

The delivered folder contains the thesis, presentation, analysis code, a
cleaned hourly table spanning 2020-08-25 to 2021-09-24, and raw Kerkrade CSVs
including a basement record dated 2021-05-15 to 2021-09-24. The code identifies
K4 as the non-ABC basement sensor and documents historical ABC adjustments, but
the provenance of the cleaned pre-May record still needs reconstruction. The
folder is kept out of Git because it is a 63 MB external source package
containing raw data and binaries. Presence is not a passed gate: timestamps,
device identity, calibration, ABC processing, aggregation and missingness still
need to be checked against the contract below.

Request from Jan-Philipp Viefhues, sustainably.io and/or the Maastricht thesis
data holder:

- 2020-08-25 through 2021-09-01, preferably source-native minute data;
- documented hourly data are acceptable if the raw export is unrecoverable;
- indoor CO2 and air pressure are required; temperature and relative humidity
  should be included if present;
- device identifier, sensor model, unit, timestamp/timezone convention;
- calibration and replacement history;
- whether automatic baseline correction (ABC) was enabled and whether the
  supplied values were already processed;
- missing-data and aggregation rules used in the thesis.

Why still important: July 2021 is 3.5 years before the later local IoT record.
Until the delivered source is normalised and its provenance resolved, this
chapter cannot claim a reproduced Viefhues trajectory or compare it with later
CO2 events. The regional recurrence/spatial-extent analysis can still proceed.

On receipt, produce:

- `data/interim/viefhues_iot.csv` with `timestamp_utc`, `sensor_era`,
  `iot_co2_ppm` and `iot_air_pressure_hpa` at the supplied or documented
  resolution;
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

Status: **not yet requested; first priority**.

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

## 3. Long public weather — blocking design/data decision

Status: **held sources inspected; primary source and assignment not selected**.

Temperature, relative humidity and pressure are fixed primary signals, so they
need the same explicit treatment as rainfall. The current repository has about
ten years of Visual Crossing values at four city points and a KNMI table from
2020 onward. Neither has yet been assigned prospectively to the eventual
watercourse cohort, and the narrow coverage boundary cannot be assumed to yield
ten joint years with discharge and RADOLAN.

Choose one rule with the supervisor before protocol lock, without viewing event
contrasts. Plausible routes are a nearest official station archive, a fixed
public gridded product, or a justified extension of the held point series. The
choice must state whether the values are observations or reanalysis, how each
watercourse is assigned, and how elevation/distance and cross-border coverage
are handled. Convenience or event performance is not a selection rule.

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
hydrologically checked. The existing combined KNMI/DWD point series remains a
sensitivity only. ERA5-Land (~9 km) and retired REGNIE are not substitutes.

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

Ready-to-personalise messages are in `external-request-drafts.md`. They have
not been sent by this repository work.
