# Data Requests

Track requested external datasets, contact history, and receipt status.

## Open — blocking

### Long discharge history for the Limburg tributaries

Status: **Not yet requested. Highest priority for the chapter's main analysis.**

Why it matters. The Waterschap Limburg OData endpoint is a rolling ~2-year
window, not an archive: earliest record 2024-08-06. That window contains no
event approaching July 2021, and it is dominated by a single month — January
2025 is 4% of the record and supplies 58% of all gauge-hours above p99.
Everything about statistical power in the transfer experiment follows from
this.

**What was established by direct testing on 2026-08-06** (endpoints probed, not
inferred from documentation):

| Source | Gauges | Resolution | Depth | Licence | Verified |
| --- | --- | --- | --- | --- | --- |
| LANUK NRW opengeodata | Rur, Wurm, Niers, Schwalm — 30 in the Rur zip alone | **15 min** | **1950-2026** | DL-DE Zero 2.0 | yes — parsed |
| RWS Waterwebservices | Maas main stem: Borgharen, Eijsden, Venlo, Lith, Megen | **10 min** | **~2000-now**, `Gecontroleerd` | CC0 | yes — parsed |
| RWS Waterwebservices | Geul at Cottessen | 10 min | **rolling, ~late 2025 only**, `Ongecontroleerd` | CC0 | yes — 204 before then |
| **Waterschap Limburg** | **Geul, Geleenbeek, Worm, Eyserbeek, Gulp, Selzerbeek, Voer, Vlootbeek** | ? | ? | ? | **must ask** |

**Corrections to earlier notes in this session.** EStreams lists provider
`NL_RWS` (CC0, 1901-2023) for Eyserbeek/Eys, Gulp/Azijnfabriek,
Selzerbeek/Partij, Voer/Mesch, Vlootbeek and Roer/Stah. That attribution does
not match what Rijkswaterstaat actually serves: none of those station names
appear anywhere in the live RWS catalogue (2,635 locations searched), and the
only South Limburg tributary RWS carries is Epen Geul Cottessen — which returns
HTTP 204 for every date before roughly late 2025. **Waterschap Limburg is the
holder for the tributaries.** EStreams itself ships no streamflow series at all,
only monthly and seasonal indices; verified against the archive's 15,143
members.

**What to request from Waterschap Limburg** (`info@waterschaplimburg.nl`,
088 88 90 100):

1. Full available discharge history, all Drainage-type gauges, earliest record
   to present. Name the priorities: **Geul** (Cottessen, Hommerich, Meerssen),
   **Worm** (Rimburg), **Geleenbeek** (Brommelen, Munstergeleen, Millen,
   Oud-Roosteren), Eyserbeek, Gulp, Selzerbeek, Voer.
2. Native temporal resolution, and whether sub-hourly exists for the older
   record.
3. Validation status, and any rating-curve changes or gauge relocations — the
   Geul rating curves were revised after 2021.
4. Whether gauges failed during July 2021. Randerath and Herzogenrath 2 in the
   NRW archive both stop dead at 2021-07-01, so survivorship is a real issue.
5. The Fase1/2/3 alarm thresholds as a time series, not just current values, in
   case they were revised after 2021.

Note their own published evaluations (`analyse_overstroming_valkenburg.pdf`,
`analyse_overstromingen_geulmonding.pdf`) draw on exactly these series, so the
data exists in usable form.

**Precedent to cite in the request.** Tsakiris et al., *HESS* 28, 3327 (2024),
"Flood drivers and trends: a case study of the Geul River catchment over the
past half century", states that Waterschap Limburg supplied **15-minute
discharge at Meerssen from 1970 to August 2021**. So the archive exists at
sub-hourly resolution across five decades, and the water board has released it
to academic users before. Ask for the same series plus the other gauges.

**Alternative routes, in the order worth trying.**

1. **The HESS 2024 authors directly.** They hold a cleaned 1970-2021 15-minute
   Meerssen series. An author request is usually faster than an institutional
   one and comes with the quality caveats already known.
2. **JCAR ATRACE** — `https://www.jcar-atrace.eu`. Deltares-led joint research
   programme, Nov 2023 to Nov 2028, eight-plus institutes across DE/BE/LU/NL,
   created specifically in response to the 2021 floods, with **the Geul and the
   Roer as named basins**. This is the strongest non-obvious route: not a data
   portal but a consortium that has almost certainly already assembled the
   transboundary series this chapter needs, and whose remit is cross-border
   regional-basin research. Worth approaching as a collaborator rather than a
   data requester.
3. **Deltares rapid assessment** — *checked 2026-08-06. No downloadable series,
   but it yields the benchmark values the chapter needs.* See below.

### Deltares rapid assessment — benchmark values, not data

`appendixRA_v3-compressed.pdf` (97 pp) and the main report
`4-rapid-assessment-geul-river-basin-2022.pdf`. Contributors include TU Delft
(Jonkman, Rutten, Rongen), Deltares (Becker, Bouaziz), KU Leuven (Willems,
Moustakas), RWTH Aachen (Klopries) and LIST (Pfister, Matgen).

No time series are distributed. What it does give is external calibration for
how extreme the chapter's two-year window is:

| Geul station | modelled July 2021 peak, m3/s | held record max | as % of 2021 |
| --- | ---: | ---: | ---: |
| Meerssen | 166 | 31.0 | 19% |
| Hommerich | 106 | 22.3 | 21% |
| Cottessen | 98 | no data | — |
| Gulp | 11 | 4.5 | 41% |
| Selzerbeek | 14 | 2.0 | 14% |
| Eyserbeek | 11 | 2.4 | 22% |

Peaks are modelled (wflow_sbm); the report notes the model "likely
overestimates the peaks." Treat as an upper bound.

Return-period anchors, which matter because two years supports no frequency
analysis of its own:

- **10-year ARI at Meerssen is 44 m3/s**, from gauging data. The held record
  maximum of 31.0 m3/s is **70% of a 10-year event** — high-end but sub-decadal.
- July 2021 discharge return periods across the catchment ran **50 to 500
  years**; precipitation 2 to 1000 years.
- Three peaks: 13 July 17:00, 14 July 08:00 and 13:00.
- The Geul contributed 76% of downstream discharge on the 14th, against a usual
  60-72%.

**The finding worth carrying into the chapter.** On the observed Geul data
during the event, the report states peaks are missing "due to damage to the
stations during the peak of this extreme event," and that the surviving
observations "are maybe not too trustworthy (since measuring discharges during
flood is very difficult)" — noting, for instance, almost no increase in observed
discharge between Kelmis and Sippenaeken despite a large intervening
subcatchment.

That is the same failure seen independently in the LANUK NRW archive, where
Randerath, Welz and Luchem all stop on 2021-07-01 and Herzogenrath 1 on
2021-06-30. **Gauge networks in this basin did not survive the event they most
needed to record, on both sides of the border.** For a chapter about where to
put monitoring, that is a finding rather than an inconvenience, and it is an
argument for donor-based transfer from instruments that do survive.

Practical consequence: any 2021 analysis must treat peak observations as
censored, not missing at random.

### JCAR ATRACE — a collaboration route, not a portal

*Checked 2026-08-06.* The knowledge base holds reports and theses only; there is
no data portal and no downloadable discharge.

What makes it worth approaching anyway: JCAR ATRACE is Deltares-coordinated,
runs Nov 2023 to Nov 2028, spans eight-plus institutes across DE/BE/LU/NL, was
created in response to the 2021 floods, and names **the Geul and the Roer** as
study basins. Its Geul workstream includes **installing climate-robust water and
debris monitoring systems** — that is monitoring network design, actively under
way, in this chapter's catchments.

So the approach is as a collaborator with a relevant question, not as a data
requester. They will hold the assembled transboundary series, and the chapter's
question is directly useful to what they are building.

- Dr. Ir. Kymo Slager, Programme Manager — `kymo.slager@deltares.nl`,
  +31 (0)88 335 82 73
- General — `info@jcar-atrace.eu`

**Also worth retrieving**: Asselman, Van Heeringen, De Jong and Geertsema (2022),
*Juli 2021 overstroming en wateroverlast in Zuid-Limburg: eerste bevindingen
voor Valkenburg, Geulmonding, Roermonding en Eygelshoven*, hosted on
waterschaplimburg.nl. It covers **Eygelshoven** — `anselderbeek_eygelshoven` in
the chapter's gauge set — so it is the water board's own evaluation of gauges
this chapter uses.

**Routes checked and ruled out**, so they are not retried:

- **Waterstandlimburg OData deeper history.** Hard-capped at 2024-08-06. A
  `$filter=DateTime lt 2024-01-01` returns an empty set, and an explicit
  `gt 2015-01-01` still returns 2024-08-06 as the first record. There is no
  hidden archive behind the endpoint.
- **`open.waterschaplimburg.nl`.** The water board's open-data portal exists but
  is explicitly under construction; it publishes a live map and an app, no
  historical series.
- **GRDC.** Holds the Maas main stem only. In the EStreams gauge table the
  main-stem stations carry 7-digit GRDC identifiers (Borgharen 6421500, Venlo
  6421102, Lobith 6435060) while every tributary carries a small local integer
  (Eys 1132, Partij 1231, Azijnfabriek 1334), which is the signature of a
  non-GRDC source. Small tributaries are below GRDC's collection threshold.
- **CAMELS-NL / a Dutch Caravan extension.** Neither exists. CAMELS-DE covers
  Germany but is daily and ends December 2020, so it misses July 2021.

**Not blocking, do in parallel.** The NRW and RWS pulls need no permission and
can start immediately; see `docs/scope-decisions.md`.

### Catchment rainfall — no request needed, but real work

Status: **Not started. Blocks the transfer experiment.**

Why it blocks. The transfer experiment needs a **rainfall-only baseline**;
without it there is no way to separate genuine donor transfer from two
catchments simply having been rained on by the same storm. That confound is the
main threat to the chapter's claim. Scope and options are in
`docs/scope-decisions.md` section 4; this entry tracks what has been verified as
obtainable.

**The problem restated.** Seven KNMI synoptic stations, only 06380 Maastricht
regionally relevant at 22 km. Every southern gauge snaps to the same station, so
`met_similarity` degenerates to two values and has been dropped from the pair
table.

**New requirement created on 2026-08-06.** The LANUK NRW pull added 42 German
gauges with records to 1950. They are unusable in a transfer experiment without
matching German rainfall, so DWD is now a requirement rather than an option.

**Verified obtainable, no key and no registration** (endpoints probed
2026-08-06):

| Source | What | Verified |
| --- | --- | --- |
| DWD hourly station precipitation | **34 stations with usable archives**, 1995-2026, median 729 mm/yr, 30 current within 60 days | **pulled** — `scripts/27_ingest_dwd_precipitation.py` |
| DWD RADOLAN `RW` | gauge-adjusted radar, **1 km, hourly, 2005-present**, monthly tar.gz. `RW202107.tar.gz` is 48 MB and downloads clean — the flood month | HTTP 200, size confirmed; not yet pulled |
| KNMI radar RAD_NL25_RAC | 1 km, 5 min, Dutch side | API key already held; not yet pulled |

**Correction to an earlier count in this file: 34 usable stations, not 90.** The
box contains 110 entries in DWD's station description, but 76 are recent
installations (listed start 2019-2021) that are live yet publish no `historical`
or `recent` hourly archive — real-time only. They cannot be used.

**And station data alone does not fix the axis.** Measured against the 42
discharge gauges:

| nearest rain station | median | max | distinct stations serving 42 gauges | largest degenerate cluster |
| --- | ---: | ---: | ---: | ---: |
| KNMI synoptic (7) | 14.7 km | 41.2 km | 3 | 21 gauges |
| DWD hourly (34) | 14.9 km | 30.0 km | 7 | 10 gauges |
| **combined** | **8.0 km** | — | — | — |

Combining the networks halves the median distance and cuts the worst cluster
from 21 gauges to 10, so `met_similarity` stops being a two-value flag. But 8 km
is still coarse against catchments of 27-77 km2, whose linear scale is only
5-9 km — nearest-station rainfall still cannot reliably distinguish the rain
falling on two neighbouring catchments, which is exactly the discrimination the
shared-forcing control depends on.

**So radar is required, not optional.** That is a firmer conclusion than this
file carried before, and it makes `geopandas` a real dependency.

Two analysis notes worth recording before anyone builds on this. Nearest-station
assignment wastes the network: rainfall should be interpolated to catchment
centroids or polygons from all stations at once. And DWD `R1` uses **-999 for
missing**, which is blanked on ingest — summed as a number it would silently
destroy any total it entered.

**Not obtainable without action by the author:**

- **ERA5-Land needs a Copernicus CDS account and personal API key.** It cannot
  be fetched on the author's behalf. It is also the weakest option here: ~9 km
  cells against catchments of 27-77 km2, so a single cell spans several study
  catchments. **Recommendation: drop ERA5-Land** rather than pursue the key.
  RADOLAN at 1 km is the correct instrument.
- **DWD REGNIE** appears retired: both the daily and monthly directories now
  contain only `regnie_info.html` with no data. Do not plan around it; RADOLAN
  supersedes it.

**Catchment averaging needs polygons.** EStreams ships delineated boundaries and
ranged access to the archive already works, but reading shapefiles needs
geopandas, which is not installed. That is the one dependency this line of work
adds.

### Viefhues 2020-2021 IoT record

Status: **Not yet requested. Highest priority.**

Purpose: The chapter's central question concerns the July 2021 flood, which
falls 3.5 years before the earliest locally held IoT observation (2025-01-31).
Without this record there is no flood in the analysis window.

Requested window: 2020-08-25 to 2021-09-01, the window analysed in Viefhues
(2022). Hourly or finer. Indoor CO2 required; indoor pressure, temperature and
relative humidity desirable.

Why it matters: groundwater already held in this repository runs from
2021-01-01, so this record would overlap it by roughly 243 days including the
flood period. Compare with 62 clean, flood-free paired days in the 2025-2026
record.

Possible routes:

- Blynk account history for the same house; the currently held exports are
  devices 455022 and 455025 but begin 2025-01-31.
- sustainably.io, under which the thesis work was carried out.
- Jan-Philipp Viefhues directly.
- Maastricht University, if thesis data were deposited.

Notes: Confirm what pre-processing was applied. Viefhues aggregated
minute-level readings to hourly; source-native minute data would be preferable
if it still exists. Record the device identity and any sensor changes between
2021 and 2025, since the analysis assumes the same house but not necessarily
the same instrument.

## Open — sent

### Provincial groundwater and mine-water data

Status: Sent 2026-08-06 to `meetnetbeheer@avallo.nl`, cc
`infopuntmijnbouw@prvlimburg.nl`. Awaiting reply.

Fallback contacts: `info@avallo.nl`; Provincie Limburg +31 43 389 99 99. The
route described in Viefhues (2022) named Jean Hacking at Provincie Limburg and
Rene Mols at Waterschap Limburg.

Questions asked:

1. Published level series for provincial wells within about 2 km of the site
   (GMW000000057847, GMW000000091726, GMW000000091599).
2. Whether nearby points belong to the mijnwatermeetnet or monitor phreatic
   groundwater, and which mine-water points lie closest to Kerkrade.
3. Measurement frequency and period of record for those mine-water points.
4. Scheduled pumping, drainage or extraction operations and their schedules.
5. Whether the Gemeente Heerlen series ending 2025-08-26 reflects a submission
   delay or the end of monitoring.
6. Screen depths, ground levels, reference datum, and hydrogeological unit.

Priority within the request: question 1 determines whether the 2026 IoT block
can be paired at all, and whether closer wells are available. Question 4 would
provide an exogenous change in water level, worth more than any observational
design.

## Series alignment

Not requests, but the held series have drifted apart and any joint analysis
inherits the earliest end date:

| Series | Latest |
| --- | --- |
| Discharge, Waterschap | 2026-08-06 |
| Discharge, LANUK NRW | 2026-06-30 |
| Discharge, RWS Maas | 2026-08-06 |
| IoT and Visual Crossing | 2026-07-21 |
| KNMI | 2026-06-24 |
| Groundwater, BRO | 2025-08-27 — publication stopped, confirmed real |

`scripts/update_data.py` closes the first four. The groundwater stop is question
5 of the provincial request above.

## Received

### BRO groundwater, three Gemeente Heerlen wells

Status: **Received 2026-08-06** via the public BRO REST service. No
registration, certificate or provider correspondence required.

Contents: GMW000000013210 (2.85 km), GMW000000013172 (2.97 km),
GMW000000013161 (3.60 km). Nominal 6-hourly, 2021-01-01 to 2025-08-27, 16,532
readings.

Source-native XML preserved under `data/raw/groundwater/bro/`. Re-fetch with
`python scripts/05a_fetch_bro_groundwater.py`.

Known limitations, to carry into the chapter's limitations section:

- Shallow phreatic wells, not connected mine-water shafts. Tier 2 under
  `docs/groundwater-data-contract.md`.
- Screen depths absent from BRO; `constructionStandard` recorded as `onbekend`.
- No data published after 2025-08-27 under either `filtered=JA` or
  `filtered=NEE`, so the stop is real rather than a validation filter.
- Estimated barometric efficiency 0.20-0.34; levels require barometric
  correction before use as an exposure.
- Movement during July 2021 was 0.10-0.36 m, against 1.2-1.9 m of seasonal
  range in 2024. These wells track seasonal recharge more than flood events.
