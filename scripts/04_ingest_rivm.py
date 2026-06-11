"""Week 4 RIVM/Luchtmeetnet transfer-site starter ingestion."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd
import requests

from src.io_data import load_rivm


RAW_DIR = Path("data/raw/transfer/rivm")
INTERIM_DIR = Path("data/interim")
RESULTS_DIR = Path("results/rivm")

ANALYSIS_PATH = INTERIM_DIR / "analysis_hourly.csv"
OUTPUT_PATH = INTERIM_DIR / "rivm_hourly.csv"
STATION_CANDIDATES_PATH = RESULTS_DIR / "candidate_stations.csv"

BASE_URL = "https://api.luchtmeetnet.nl/open_api"
PORTAL_BASE_URL = "https://data.rivm.nl/data/luchtmeetnet"
DEFAULT_COMPONENTS = ("PM10", "PM25", "NO2", "O3")
DEFAULT_LOCATION_KEYWORDS = ("maastricht", "roermond", "heerlen")


def get_json(url, params=None):
    """Request JSON from the public Luchtmeetnet API."""
    response = requests.get(url, params=params, timeout=60)
    response.raise_for_status()
    return response.json()


def cache_json(payload, path):
    """Write a raw API payload for reproducible offline parsing."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(f"wrote {path}")


def download_file(url, path):
    """Download one public RIVM data-portal file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(url, timeout=120)
    if response.status_code == 404:
        print(f"not found {url}")
        return False
    response.raise_for_status()
    path.write_bytes(response.content)
    print(f"wrote {path}")
    return True


def fetch_all_pages(endpoint, params, raw_prefix):
    """Fetch paginated Luchtmeetnet resources within the fair-use limit."""
    pages = []
    page = 1
    while True:
        page_params = {**params, "page": page}
        payload = get_json(f"{BASE_URL}/{endpoint}", params=page_params)
        cache_json(payload, RAW_DIR / f"{raw_prefix}_page_{page}.json")
        pages.extend(payload.get("data", []))

        pagination = payload.get("pagination", {})
        last_page = int(pagination.get("last_page", page))
        if page >= last_page:
            break
        page += 1
    return pages


def station_text(row):
    """Flatten likely station name/location fields for keyword matching."""
    parts = []
    for key in ["station_number", "name", "location", "municipality", "street"]:
        value = row.get(key)
        if isinstance(value, dict):
            parts.extend(str(item) for item in value.values())
        elif value is not None:
            parts.append(str(value))
    return " ".join(parts).lower()


def candidate_stations(stations, keywords):
    """Select transfer-site candidates by place-name keywords."""
    candidates = [
        row
        for row in stations
        if any(keyword.lower() in station_text(row) for keyword in keywords)
    ]
    return pd.DataFrame(candidates)


def candidate_stations_from_metadata(path, keywords):
    """Select candidate stations from RIVM data-portal metadata CSV."""
    metadata = pd.read_csv(path, sep=";", comment="#")
    text = (
        metadata["meetlocatie_naam"].fillna("")
        + " "
        + metadata["meetlocatie_plaatsnaam"].fillna("")
    ).str.lower()
    mask = text.apply(lambda value: any(keyword.lower() in value for keyword in keywords))
    return metadata.loc[mask].copy()


def default_window():
    """Use the current Kerkrade analysis window as the first transfer window."""
    frame = pd.read_csv(ANALYSIS_PATH, parse_dates=["timestamp_utc"])
    return frame["timestamp_utc"].min(), frame["timestamp_utc"].max()


def analysis_months(start, end):
    """Return monthly period labels touched by a timestamp range."""
    start_month = pd.Timestamp(start).tz_localize(None).to_period("M")
    end_month = pd.Timestamp(end).tz_localize(None).to_period("M")
    return pd.period_range(start_month, end_month, freq="M")


def fetch_measurements(stations, components, start, end):
    """Cache station/component measurement payloads for the analysis window."""
    for station in stations:
        for component in components:
            fetch_all_pages(
                "measurements",
                params={
                    "station_number": str(station),
                    "formula": str(component).upper(),
                    "order_by": "timestamp_measured",
                    "order_direction": "asc",
                    "start": pd.Timestamp(start).isoformat(),
                    "end": pd.Timestamp(end).isoformat(),
                },
                raw_prefix=f"measurements_{station}_{str(component).lower()}",
            )


def fetch_portal_files(args):
    """Fallback to official RIVM current-year CSV files when the API is down."""
    start, end = args.start, args.end
    if start is None or end is None:
        start, end = default_window()

    metadata_path = RAW_DIR / "portal_luchtmeetnet_meetlocaties.csv"
    download_file(
        f"{PORTAL_BASE_URL}/Metadata/luchtmeetnet_meetlocaties.csv",
        metadata_path,
    )
    candidates = candidate_stations_from_metadata(metadata_path, args.candidate_keywords)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    candidates.to_csv(STATION_CANDIDATES_PATH, index=False)
    print(f"wrote {STATION_CANDIDATES_PATH} ({len(candidates)} rows)")

    for month in analysis_months(start, end):
        for component in args.components:
            component = str(component).upper()
            filename = f"{month.year}_{month.month:02d}_{component}.csv"
            download_file(
                f"{PORTAL_BASE_URL}/Actueel-jaar/{filename}",
                RAW_DIR / f"portal_{filename}",
            )


def cached_candidate_station_numbers(args):
    """Return cached portal candidate station IDs when available."""
    metadata_path = RAW_DIR / "portal_luchtmeetnet_meetlocaties.csv"
    if not metadata_path.exists():
        return []
    candidates = candidate_stations_from_metadata(metadata_path, args.candidate_keywords)
    if "meetlocatie_id" not in candidates:
        return []
    return candidates["meetlocatie_id"].dropna().astype(str).tolist()


def maybe_download(args):
    """Download station metadata and current-window measurements when allowed."""
    if args.skip_download:
        print("RIVM download skipped; using cached raw files only.")
        return

    stations = fetch_all_pages(
        "stations",
        params={"order_by": "location"},
        raw_prefix="stations",
    )
    candidates = candidate_stations(stations, args.candidate_keywords)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    candidates.to_csv(STATION_CANDIDATES_PATH, index=False)
    print(f"wrote {STATION_CANDIDATES_PATH} ({len(candidates)} rows)")

    station_numbers = list(args.stations)
    if not station_numbers and not candidates.empty and "station_number" in candidates:
        station_numbers = candidates["station_number"].dropna().astype(str).head(2).tolist()
    if not station_numbers:
        print("No RIVM candidate station numbers found; cached station metadata only.")
        return

    start, end = args.start, args.end
    if start is None or end is None:
        start, end = default_window()
    fetch_measurements(station_numbers, args.components, start, end)


def write_hourly(components, stations=None):
    """Normalize cached RIVM measurements to an hourly wide frame."""
    frame = load_rivm(
        RAW_DIR,
        frequency="h",
        stations=stations,
        components=components,
        wide=True,
    )
    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    frame.to_csv(OUTPUT_PATH, index_label="timestamp_utc")
    print(f"wrote {OUTPUT_PATH} ({len(frame)} rows)")


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-download", action="store_true")
    parser.add_argument("--stations", nargs="*", default=[])
    parser.add_argument("--components", nargs="*", default=list(DEFAULT_COMPONENTS))
    parser.add_argument("--candidate-keywords", nargs="*", default=list(DEFAULT_LOCATION_KEYWORDS))
    parser.add_argument("--use-portal", action="store_true")
    parser.add_argument("--start")
    parser.add_argument("--end")
    return parser.parse_args()


def main():
    """Command-line entry point."""
    args = parse_args()
    try:
        if args.use_portal:
            fetch_portal_files(args)
        else:
            maybe_download(args)
    except requests.RequestException as exc:
        print(f"RIVM live download failed: {exc}")
        print("Trying the official RIVM data-portal CSV fallback.")
        try:
            fetch_portal_files(args)
        except requests.RequestException as portal_exc:
            print(f"RIVM portal fallback failed: {portal_exc}")
            print("Using any cached RIVM payloads already present.")

    try:
        stations = args.stations or cached_candidate_station_numbers(args) or None
        write_hourly(args.components, stations)
    except (FileNotFoundError, ValueError) as exc:
        print(exc)
        print(
            "Next step: rerun without --skip-download when the public "
            "Luchtmeetnet API is reachable, or place cached measurement JSON "
            "files under data/raw/transfer/rivm/."
        )


if __name__ == "__main__":
    main()
