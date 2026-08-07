"""Fetch the Waterschap Limburg gauge inventory and selected discharge series.

Waterschap Limburg publishes water-level, groundwater and discharge locations
through a public OData endpoint with no key or registration.

    https://www.waterstandlimburg.nl/api/Location
    https://www.waterstandlimburg.nl/api/Location({id})/Measurements

Two things worth knowing before relying on this source:

- The archive is a rolling window, not a deep one. The earliest record available
  on 2026-08-06 was 2024-08-06, so roughly two years and two winters. Longer
  history needs a direct request to Waterschap Limburg, to WVER for the German
  gauges, or to GRDC.
- Coverage is not limited to the Netherlands. The inventory republishes German
  Lanuv gauges on the Roer and Worm, and Rijkswaterstaat gauges on the Maas, so
  cross-border and main-stem comparisons are available from the same endpoint.

The inventory is always refreshed; series are fetched only for the gauges named
in ``--stations`` or, by default, the source-reconnaissance candidate set.
"""

from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlopen

import pandas as pd

BASE = "https://www.waterstandlimburg.nl/api"
RAW_DIR = Path("data/raw/discharge/waterschap")
INVENTORY_PATH = Path("data/interim/waterschap_locations.csv")
SERIES_PATH = Path("data/interim/waterschap_discharge_hourly.csv")

# Reconnaissance set: tributaries carrying multiple discharge gauges plus those
# nearest Kerkrade. Multiple gauges help expose routing and source-quality
# problems before one representative per watercourse is fixed.
CANDIDATE_STATIONS = {
    232: "geul_cottessen",
    233: "geul_hommerich",
    1394: "geul_meerssen",
    242: "worm_rimburg",
    1715: "worm_randerath",
    227: "geleenbeek_brommelen",
    229: "geleenbeek_munstergeleen",
    230: "geleenbeek_millen",
    481: "geleenbeek_oud_roosteren",
    221: "roer_julich",
    222: "roer_stah",
    1712: "roer_linnich",
    236: "selzerbeek_partij",
    237: "selzerbeek_molentak",
    241: "anselderbeek_eygelshoven",
    235: "eyserbeek_eys",
    238: "gulp_azijnfabriek",
    866: "maas_borgharen",
}


def fetch_json(url, timeout=180):
    """Read one JSON payload, encoding spaces without touching OData operators."""
    if " " in url:
        base, query = url.split("?", 1)
        url = f"{base}?{quote(query, safe='$=&,()/:-T')}"
    with urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def records(payload):
    """OData responses wrap rows in `value`; bare lists are also accepted."""
    if isinstance(payload, dict):
        return payload.get("value", [])
    return payload


def write_inventory():
    """Refresh the full station inventory, all types."""
    payload = fetch_json(f"{BASE}/Location")
    frame = pd.DataFrame(records(payload))
    INVENTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(INVENTORY_PATH, index=False)
    counts = frame["LocationType"].value_counts().to_dict()
    print(f"wrote {INVENTORY_PATH} ({len(frame)} locations: {counts})")
    return frame


def fetch_series(station_id, label, refresh=False):
    """Fetch one gauge's full available series, caching the raw payload."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / f"{label}_{station_id}.json"
    if path.exists() and not refresh:
        payload = json.loads(path.read_text())
    else:
        payload = fetch_json(f"{BASE}/Location({station_id})/Measurements?$orderby=DateTime")
        path.write_text(json.dumps(payload))
    rows = records(payload)
    if not rows:
        return pd.DataFrame()
    frame = pd.DataFrame(rows)
    frame["timestamp_utc"] = pd.to_datetime(frame["DateTime"], utc=True)
    frame = frame[["timestamp_utc", "Value"]].rename(columns={"Value": label})
    frame = frame.set_index("timestamp_utc").sort_index()

    # Exact 0.0 is a missing-data sentinel in this feed, not a measurement.
    # Verified against the Rijkswaterstaat series for the same gauge: at
    # Borgharen on 2024-10-10 15:00 the raw ten-minute values are
    # [0, 0, 1336, 0, 0, 0], and RWS reports a steady ~1336 m3/s through that
    # hour. Averaging the zeros in gave 222.7 — a sixth of the true flow.
    #
    # This affected 26 of 57 gauges and 2.3% of all readings, worst at
    # Borgharen (7.9%). Left uncorrected it puts step changes of hundreds of
    # m3/s into the first-difference series that every response-correlation and
    # flashiness statistic is computed on.
    zeros = int((frame[label] == 0).sum())
    if zeros:
        share = zeros / len(frame)
        if share > 0.5:
            # A gauge that is mostly zero may genuinely be dry rather than
            # broken; blanking it would erase a real signal. Flag, do not touch.
            print(f"  {label}: {share:.0%} zeros — possibly a dry gauge, NOT blanked; check it")
        else:
            frame.loc[frame[label] == 0, label] = pd.NA
            print(f"  {label}: blanked {zeros:,} zero sentinels ({share:.2%})")
    return frame


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="Re-download cached series")
    parser.add_argument(
        "--stations",
        default="",
        help="Comma-separated station ids; defaults to the candidate set",
    )
    parser.add_argument(
        "--all-discharge",
        action="store_true",
        help="Fetch every Drainage-type gauge in the inventory, not just candidates",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=3,
        help="Attempts per gauge; the endpoint returns intermittent 504s",
    )
    args = parser.parse_args()

    inventory = write_inventory()

    wanted = CANDIDATE_STATIONS
    if args.all_discharge:
        # Every discharge gauge; candidate labels win so existing files are reused.
        discharge = inventory.loc[inventory["LocationType"].eq("Drainage")]
        wanted = {}
        for row in discharge.itertuples(index=False):
            label = CANDIDATE_STATIONS.get(row.Id)
            if label is None:
                water = re.sub(r"[^a-z0-9]+", "_", str(row.WaterName or "unknown").lower())
                name = re.sub(r"[^a-z0-9]+", "_", str(row.Name or "").lower())[:40]
                label = f"{water}_{name}".strip("_")
            wanted[int(row.Id)] = label
    if args.stations:
        ids = [int(value) for value in args.stations.split(",") if value.strip()]
        wanted = {i: CANDIDATE_STATIONS.get(i, f"station_{i}") for i in ids}

    frames = []
    for station_id, label in wanted.items():
        frame = None
        for attempt in range(1, args.retries + 1):
            try:
                frame = fetch_series(station_id, label, refresh=args.refresh)
                break
            except Exception as exc:  # noqa: BLE001 - one bad gauge must not stop the pull
                if attempt == args.retries:
                    print(f"  {label} [{station_id}]: FAILED after {attempt} ({exc})")
                else:
                    time.sleep(3 * attempt)
        if frame is None:
            continue
        if frame.empty:
            print(f"  {label} [{station_id}]: no records")
            continue
        # Hourly means; the source samples every 5-15 minutes and is irregular.
        hourly = frame.resample("h").mean()
        frames.append(hourly)
        print(
            f"  {label} [{station_id}]: {len(frame):,} records -> {hourly[label].notna().sum():,} h "
            f"({frame.index.min():%Y-%m-%d} to {frame.index.max():%Y-%m-%d})"
        )
        time.sleep(0.5)

    if not frames:
        print("no series fetched")
        return
    combined = pd.concat(frames, axis=1).sort_index()
    SERIES_PATH.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(SERIES_PATH, index_label="timestamp_utc")
    print(f"\nwrote {SERIES_PATH} ({len(combined)} hours, {combined.shape[1]} gauges)")


if __name__ == "__main__":
    main()
