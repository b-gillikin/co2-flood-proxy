# Data Requests

Track requested external datasets, contact history, and receipt status.

## Open — blocking

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

Status: Sent 2026-08-05 to `meetnetbeheer@avallo.nl`, cc
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

## Received

### BRO groundwater, three Gemeente Heerlen wells

Status: **Received 2026-08-05** via the public BRO REST service. No
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
