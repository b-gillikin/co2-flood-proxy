"""Build the primary-gauge metadata table for the event study (protocol §2).

Assembles `data/interim/event_study_gauges.csv`, the CORE_FILES["gauge
metadata"] contract read by `scripts/31_event_study_gates.py`, from four
already-built sources:

- `config/event_study_cohort.csv`: the six-watercourse cohort of decision D3
  (2026-09-18), one representative gauge each;
- `data/interim/waterschap_locations.csv`: provisional pour-point coordinates
  from Waterschap's public portal (decision D5). A cross-check against
  Waterschap's own map pins from the 2026-09-07 reply
  (`config/waterschap_gauge_coordinates_crosscheck.csv`) is reported but not
  substituted: every offset is under one DEM cell (30 m), well inside the
  snap radius `scripts/39_delineate_catchments.py` already applies;
- `data/processed/waterschap_station_source_qa.csv`: the per-station source
  QA and July 2021 status built by `scripts/35_audit_waterschap_delivery.py`
  from Waterschap's 2026-09-07 reply and its attached July 2021 report;
- `config/rating_curves/event_study_eras.csv`: confirms every cohort gauge has
  a documented rating era (decision D8).

Two QA columns stay false because Waterschap's reply did not resolve them:
zero-cell semantics (a zero was never distinguished from a sentinel) and the
GMT+1 timezone (fixed offset or Dutch civil time was never asked). Both
remain open in `docs/data-requests.md`.

It reads no discharge, rainfall or weather value.

Example: python scripts/44_build_event_study_gauges.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
COHORT = ROOT / "config/event_study_cohort.csv"
LOCATIONS = ROOT / "data/interim/waterschap_locations.csv"
SOURCE_QA = ROOT / "data/processed/waterschap_station_source_qa.csv"
ERAS = ROOT / "config/rating_curves/event_study_eras.csv"
CROSSCHECK = ROOT / "config/waterschap_gauge_coordinates_crosscheck.csv"
OUTPUT = ROOT / "data/interim/event_study_gauges.csv"


def july_2021_status(row):
    """One readable line from the per-station source-QA registry (script 35)."""
    return (
        f"instrument {row.july_2021_instrument_status}; "
        f"discharge {row.july_2021_discharge_status}; "
        f"{row.structural_note} (Waterschap Limburg report, 2026-09-07)"
    )


def build_gauges():
    """The gauge metadata table, and the coordinate cross-check for reporting."""
    cohort = pd.read_csv(COHORT)
    locations = pd.read_csv(LOCATIONS)
    locations = locations[locations.LocationType.eq("Drainage")].set_index("ExternalReference")
    source_qa = pd.read_csv(SOURCE_QA).set_index("series_key")
    era_gauges = set(pd.read_csv(ERAS).gauge.astype(str))
    crosscheck = pd.read_csv(CROSSCHECK)

    missing_location = set(cohort.gauge) - set(locations.index)
    missing_qa = set(cohort.gauge) - set(source_qa.index)
    missing_era = set(cohort.gauge) - era_gauges
    if missing_location or missing_qa or missing_era:
        raise ValueError(
            f"cohort gauge missing a source: location={sorted(missing_location)}, "
            f"source_qa={sorted(missing_qa)}, rating_era={sorted(missing_era)}"
        )

    rows = []
    for row in cohort.itertuples():
        location = locations.loc[row.gauge]
        qa = source_qa.loc[row.gauge]
        rows.append(
            {
                "gauge": row.gauge,
                "watercourse": row.watercourse,
                "independence_unit": row.independence_unit,
                "latitude": location.Latitude,
                "longitude": location.Longitude,
                "coordinate_source": "Waterschap Limburg public portal (provisional, decision D5)",
                "include_primary": True,
                "natural_tributary": bool(row.natural_tributary),
                "july_2021_status": july_2021_status(qa),
                "rating_eras_documented": True,
                "timezone_verified": bool(qa.timezone_verified),
                "units_verified": bool(qa.units_verified),
                "zero_semantics_verified": bool(qa.zero_sentinel_verified),
                "sampling_semantics_verified": bool(qa.sampling_semantics_verified),
            }
        )
    return pd.DataFrame(rows), crosscheck


def main():
    gauges, crosscheck = build_gauges()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    gauges.to_csv(OUTPUT, index=False)
    print(gauges.to_string(index=False))
    print(f"\nWrote {len(gauges)} primary gauges to {OUTPUT}")
    print(
        "\nCoordinate cross-check (Waterschap's own map pins vs the public portal, "
        "both provisional under D5):"
    )
    print(crosscheck[["gauge", "station", "offset_m"]].to_string(index=False))
    print(f"maximum offset: {crosscheck.offset_m.max():.1f} m (one DEM cell = 30 m)")


if __name__ == "__main__":
    main()
