"""Fetch BRO GLD groundwater-level dossiers for wells near the Kerkrade site.

The Dutch Basisregistratie Ondergrond (BRO) publishes groundwater level data
through a public REST service that needs no certificate or registration:

    https://publiek.broservices.nl/gm/gld/v1

This script preserves the source-native XML under ``data/raw/groundwater/bro/``
and writes the readings and series metadata in the shape required by
``docs/groundwater-data-contract.md``. Re-running is safe; cached XML is reused
unless ``--refresh`` is passed.

Well discovery (documented here so the selection is reproducible): a 5 km
enclosing-circle search of the GMW characteristics endpoint around the Kerkrade
site returned 26 monitoring wells. Cross-referencing every GLD dossier held by
the three owning bronhouders identified four dossiers on those wells, of which
three carry a usable time series. The fourth (GLD000000097270 on
GMW000000009914) holds four measurements across three years and is excluded.

Note on coverage: as of the 2026-08-05 pull these series end 2025-08-26/28 under
both ``filtered=JA`` and ``filtered=NEE``, so the stop is real rather than a
validation filter. Whether it reflects a submission delay is an open provider
question -- see ``docs/data-requests.md``.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from urllib.request import urlopen

import pandas as pd

BRO_GLD_BASE = "https://publiek.broservices.nl/gm/gld/v1/objects"
RAW_DIR = Path("data/raw/groundwater/bro")
READINGS_PATH = Path("data/raw/groundwater/bro_gld_readings.csv")
METADATA_PATH = Path("data/raw/groundwater/bro_gld_series_metadata.csv")

WATERML = "{http://www.opengis.net/waterml/2.0}"

# Wells retained from the 5 km search. Distances are to the Kerkrade site
# (50.866 N, 6.062 E); ground level is the BRO groundLevelPosition in m NAP.
SERIES = {
    "GLD000000031997": {
        "series_id": "bro_gmw13210",
        "gmw_id": "GMW000000013210",
        "distance_km": 2.85,
        "ground_level_m_nap": 158.760,
    },
    "GLD000000031998": {
        "series_id": "bro_gmw13172",
        "gmw_id": "GMW000000013172",
        "distance_km": 2.97,
        "ground_level_m_nap": 149.110,
    },
    "GLD000000031996": {
        "series_id": "bro_gmw13161",
        "gmw_id": "GMW000000013161",
        "distance_km": 3.60,
        "ground_level_m_nap": 151.340,
    },
}

PROVIDER = "Gemeente Heerlen (KvK 14128451), published via BRO / DINOloket"


def fetch_dossier(gld_id, refresh=False):
    """Download one GLD dossier, reusing the cached source-native XML."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / f"{gld_id}.xml"
    if path.exists() and not refresh:
        return path
    url = f"{BRO_GLD_BASE}/{gld_id}?filtered=JA"
    with urlopen(url, timeout=180) as response:
        payload = response.read()
    path.write_bytes(payload)
    return path


def parse_readings(path, series_id):
    """Return timestamped levels from a GLD dossier's MeasurementTVP points."""
    text = path.read_text(errors="ignore")
    rows = []
    for chunk in re.findall(r"<waterml:MeasurementTVP>(.*?)</waterml:MeasurementTVP>", text, re.S):
        time = re.search(r"<waterml:time>([^<]+)", chunk)
        value = re.search(r"<waterml:value[^>]*>([-\d.]+)", chunk)
        if time and value:
            rows.append(
                {
                    "timestamp": time.group(1),
                    "series_id": series_id,
                    "water_level_value": float(value.group(1)),
                }
            )
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True, format="mixed")
    return frame.drop_duplicates(subset=["timestamp", "series_id"]).sort_values("timestamp")


def build_metadata(readings):
    """Assemble the contract metadata table, one row per series."""
    rows = []
    for spec in SERIES.values():
        series = readings.loc[readings["series_id"].eq(spec["series_id"])]
        depth = spec["ground_level_m_nap"] - series["water_level_value"].mean()
        rows.append(
            {
                "series_id": spec["series_id"],
                "provider": PROVIDER,
                "measurement_name": "groundwater level (hydraulic head), tube screen depth not published",
                "unit": "m",
                "datum": "NAP",
                "source_tier": 2,
                "site_relationship": (
                    f"{spec['gmw_id']}, {spec['distance_km']} km from the Kerkrade site; "
                    f"ground level {spec['ground_level_m_nap']} m NAP; "
                    f"water table approximately {depth:.1f} m below ground"
                ),
                "higher_value_means_higher_water": True,
                "operational_notes": (
                    "Shallow/phreatic groundwater, not a connected mine-water shaft. "
                    "Screen top/bottom absent from BRO; constructionStandard 'onbekend'. "
                    f"Record {series['timestamp'].min():%Y-%m-%d} to {series['timestamp'].max():%Y-%m-%d}; "
                    "nominal 6-hourly sampling; no 2026 data published as of 2026-08-05."
                ),
            }
        )
    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="Re-download cached dossiers")
    args = parser.parse_args()

    frames = []
    for gld_id, spec in SERIES.items():
        path = fetch_dossier(gld_id, refresh=args.refresh)
        frame = parse_readings(path, spec["series_id"])
        print(
            f"{gld_id} -> {spec['series_id']}: {len(frame):,} readings "
            f"({frame['timestamp'].min():%Y-%m-%d} to {frame['timestamp'].max():%Y-%m-%d})"
        )
        frames.append(frame)

    readings = pd.concat(frames, ignore_index=True).sort_values(["series_id", "timestamp"])
    READINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    readings.to_csv(READINGS_PATH, index=False)
    build_metadata(readings).to_csv(METADATA_PATH, index=False)
    print(f"\nWrote {len(readings):,} readings to {READINGS_PATH}")
    print(f"Wrote {len(SERIES)} series rows to {METADATA_PATH}")


if __name__ == "__main__":
    main()
