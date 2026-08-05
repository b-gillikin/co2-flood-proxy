# Groundwater and Mine-Water Data Contract

Status date: 2026-08-05

Status: **partially satisfied.** Three tier-2 series received from the public
BRO service on 2026-08-05 and normalized through this contract without
modification. Tier-1 mine-water data still outstanding; requested from Provincie
Limburg, see `docs/data-requests.md`.

In hand: GMW000000013210, GMW000000013172, GMW000000013161 — shallow phreatic
wells 2.85-3.60 km from the site, nominal 6-hourly, 2021-01-01 to 2025-08-27.
Source-native XML under `data/raw/groundwater/bro/`; readings and metadata in
the schema below.

Two amendments in light of what arrived:

- **Screen depths are unavailable** for these wells, and `datum` is NAP with
  `constructionStandard` recorded as `onbekend`. The contract's requirement to
  resolve `unknown` only after provider follow-up is now an open item rather
  than a satisfied one.
- **Barometric correction is mandatory before use.** Estimated well barometric
  efficiency is 0.20-0.34, so raw level carries a pressure component. See
  `docs/decisions.md` (2026-08-05) and `scripts/05b_barometric_efficiency.py`.

The locked direct-state analysis this contract originally fed is withdrawn; see
`docs/chapter-direction.md`. The receipt, metadata and normalization
requirements below remain in force and are unchanged.

This contract is the handoff between source receipt and analysis. Delivered
files must first be preserved unchanged under `data/raw/groundwater/`;
normalization must never overwrite those files or fill unobserved dates.

## Required Metadata

Provide one row per series with these columns:

| Column | Meaning |
| --- | --- |
| `series_id` | Stable local identifier; must be unique. |
| `provider` | Organization or named data provider. |
| `measurement_name` | What the value physically measures. |
| `unit` | Source unit, retained without silent conversion. |
| `datum` | Vertical/reference datum or `unknown` only after provider follow-up. |
| `source_tier` | `1` for a connected shaft/mine-water series; `2` for a physically relevant nearby groundwater series. |
| `site_relationship` | Physical and spatial relationship to the Kerkrade site. |
| `higher_value_means_higher_water` | Boolean orientation of the source value. |
| `operational_notes` | Sensor changes, pumping, maintenance, corrections, or known discontinuities. |

Tier assignment is a physical/provenance decision made before looking at the
CO2 association. It must not be inferred from model fit.

## Required Readings

Provide a long table with `timestamp`, `series_id`, and
`water_level_value`. An optional `is_usable` boolean can exclude provider-flagged
observations without deleting them from the source-native file; an optional
`quality_flag` is retained in the daily audit field. Timestamps must
include an offset or be paired with an explicit `--source-timezone`.

Normalize with:

```bash
python scripts/05_ingest_groundwater.py \
  --readings data/raw/groundwater/<delivered-readings.csv> \
  --metadata data/raw/groundwater/<series-metadata.csv> \
  --source-timezone Europe/Amsterdam
```

The command writes:

- `data/interim/groundwater_daily.csv`: observed series-days only;
- `data/interim/groundwater_series.csv`: validated source metadata.

Multiple valid readings on one UTC day are averaged. Missing days remain
absent. `water_level_value` retains the source orientation;
`hydrologic_level` is sign-oriented so larger always means higher water. This
handles depth-below-surface series without reversing the scientific meaning of
the reported coefficient.

## Locked Selection and Analysis

`src.io_groundwater.select_primary_series` applies this hierarchy:

1. choose the lowest available source tier;
2. within that tier, choose the greatest overlap with eligible IoT days;
3. break an exact tie by stable `series_id` ordering;
4. retain every other series as a sensitivity analysis.

Run `python scripts/16_direct_state.py` after normalization. The primary model,
coverage gate, HAC inference, moving-block bootstrap, block-sign replication,
7-day future-water placebo, 1/3/7/14-day lags, daily change, alternative-series
tests, and Benjamini-Hochberg correction are fixed in `src/direct_state.py`.

The script may report only:

- `direct_state_primary_supported` when every locked direct-state criterion passes;
- `inconclusive_because_of_coverage` when the paired-day/block gate fails;
- `null_boundary_result` when coverage is adequate but any scientific criterion fails.

No result is available yet. Passing synthetic fixtures demonstrate the code
path only and are not evidence about Kerkrade. A supported direct-state result
still requires the chapter claim-decision synthesis; the script does not infer
portability from proxy or transfer evidence.
