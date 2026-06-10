"""Download/update and normalize Wurm/Geul discharge data for Task 1.3."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.io_data import load_discharge


RAW_DIR = Path("data/raw/discharge")
INTERIM_DIR = Path("data/interim")

SOURCES = {
    "wver_wurm_rimburg_discharge.json": {
        "kind": "replace",
        "url": "https://wver.de/karten_messwerte/Messdatenportal/Messdaten/Wurm%20Rimburg%20NLAbflussBasis.P.json",
        "encoding": "cp1252",
    },
    "waterstandlimburg_geul_hommerich_discharge.json": {
        "kind": "append",
        "station_id": 233,
        "start": "2025-01-01T00:00:00Z",
        "encoding": "utf-8",
    },
    "waterstandlimburg_geul_meerssen_discharge.json": {
        "kind": "append",
        "station_id": 1394,
        "start": "2025-01-01T00:00:00Z",
        "encoding": "utf-8",
    },
}


def encoded_url(url):
    """Encode spaces in query-bearing URLs without changing OData operators."""
    if " " not in url:
        return url
    base, query = url.split("?", 1)
    return f"{base}?{quote(query, safe='=$&():')}"


def waterstandlimburg_url(station_id, start):
    """Build the Waterstand Limburg API URL from a station and start time."""
    query = f"$filter=DateTime gt {start}&$orderby=DateTime"
    return encoded_url(
        f"https://www.waterstandlimburg.nl/api/Location({station_id})/Measurements?{query}"
    )


def read_json(path, encoding):
    """Read one raw source payload."""
    return json.loads(path.read_text(encoding=encoding))


def write_json(path, payload, encoding):
    """Write a raw source payload with stable Unicode handling."""
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding=encoding)


def fetch_json(url, encoding):
    """Fetch and parse one JSON source payload."""
    with urlopen(encoded_url(url), timeout=90) as response:
        body = response.read().decode(encoding)
    return json.loads(body)


def latest_waterstand_timestamp(payload):
    """Find the newest timestamp already cached for appendable sources."""
    values = payload.get("value", [])
    if not values:
        return None
    return max(item["DateTime"] for item in values if item.get("DateTime"))


def merge_waterstand_payload(existing, incoming):
    """Append Waterstand Limburg records without duplicating prior rows."""
    metadata = {k: v for k, v in existing.items() if k != "value"}
    if not metadata:
        metadata = {k: v for k, v in incoming.items() if k != "value"}

    by_key = {}
    for item in existing.get("value", []) + incoming.get("value", []):
        key = item.get("Id") or (item.get("DateTime"), item.get("Value"))
        by_key[key] = item

    metadata["value"] = sorted(
        by_key.values(),
        key=lambda item: (item.get("DateTime", ""), item.get("Id", 0)),
    )
    return metadata


def update_raw(full_refresh=False):
    """Refresh the raw discharge JSON cache."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for filename, source in SOURCES.items():
        target = RAW_DIR / filename
        encoding = source["encoding"]

        if source["kind"] == "replace":
            payload = fetch_json(source["url"], encoding)
            write_json(target, payload, encoding)
            rows = len(payload.get("data", []))
            print(f"refreshed {target} ({rows} rows)")
            continue

        if full_refresh or not target.exists():
            start = source["start"]
            existing = {"value": []}
        else:
            existing = read_json(target, encoding)
            start = latest_waterstand_timestamp(existing) or source["start"]

        payload = fetch_json(
            waterstandlimburg_url(source["station_id"], start),
            encoding,
        )
        merged = merge_waterstand_payload(existing, payload)
        write_json(target, merged, encoding)

        old_rows = len(existing.get("value", []))
        new_rows = len(payload.get("value", []))
        total_rows = len(merged.get("value", []))
        print(f"updated {target} (+{new_rows} fetched, {old_rows}->{total_rows} rows)")


def write_normalized():
    """Write the hourly wide discharge frame used for labels and joins."""
    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    discharge = load_discharge(raw_dir=RAW_DIR, frequency="h")
    target = INTERIM_DIR / "discharge_hourly.csv"
    discharge.to_csv(target, index_label="timestamp_utc")
    print(f"wrote {target}")
    print(discharge.agg(["count", "min", "max"]).to_string())


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--full-refresh",
        action="store_true",
        help="replace appendable Waterstand Limburg raw files from the configured start date",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="only rebuild normalized output from existing raw files",
    )
    return parser.parse_args()


def main():
    """Command-line entry point."""
    args = parse_args()
    if not args.skip_download:
        update_raw(full_refresh=args.full_refresh)
    write_normalized()


if __name__ == "__main__":
    main()
