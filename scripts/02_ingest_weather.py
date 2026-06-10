"""Download/update and normalize Visual Crossing weather blobs for Task 1.2."""

from __future__ import annotations

import argparse
import calendar
import json
import subprocess
import sys
import urllib.parse
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.io_data import load_weather


DEFAULT_ACCOUNT = "stkerkradeprod01bg"
DEFAULT_CONTAINERS = [
    "kerkrada-weather-data",
    "maastricht-weather-data",
    "aachen-weather-data",
    "liege-weather-data",
]
DEFAULT_FUNCTION_RESOURCE_GROUP = "rg-kerkrade-prod"
DEFAULT_FUNCTION_APP = "func-kerkrade-monthly-pull-bg"
DEFAULT_DIRECT_LOCATION = "Kerkrade"
DEFAULT_DIRECT_CONTAINER = "kerkrada-weather-data"
DIRECT_ELEMENTS = (
    "name,datetime,datetimeEpoch,tempmax,tempmin,temp,dew,humidity,cloudcover,"
    "visibility,precip,precipprob,precipcover,preciptype,snow,snowdepth,"
    "windspeed,windspeedmean,windgust,winddir,pressure,solarradiation,"
    "solarenergy,uvindex,sunrise,sunset,moonphase,conditions,aquius,aqieur,"
    "aqielement,pm1,pm2p5,pm10,so1,no2,o3,co,cape,cin,latitude,longitude,"
    "timezone,description,stations,source"
)

RAW_DIR = Path("data/raw/weather")
INTERIM_DIR = Path("data/interim")


def run_az(args):
    """Run an Azure CLI command and echo useful failure output."""
    command = ["az", *args]
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as exc:
        if exc.stdout:
            print(exc.stdout, file=sys.stdout)
        if exc.stderr:
            print(exc.stderr, file=sys.stderr)
        raise
    return completed.stdout


def list_blobs(account_name, container_name):
    """List monthly weather CSV blobs in one weather container."""
    output = run_az(
        [
            "storage",
            "blob",
            "list",
            "--account-name",
            account_name,
            "--container-name",
            container_name,
            "--auth-mode",
            "key",
            "--query",
            "[].{name:name,size:properties.contentLength,lastModified:properties.lastModified}",
            "-o",
            "json",
        ]
    )
    blobs = json.loads(output)
    return sorted(
        [
            blob
            for blob in blobs
            if blob["name"].startswith("weather_") and blob["name"].endswith(".csv")
        ],
        key=lambda blob: blob["name"],
    )


def download_container_batch(account_name, container_name, destination):
    """Hydrate one weather container quickly with Azure's batch downloader."""
    destination.mkdir(parents=True, exist_ok=True)
    run_az(
        [
            "storage",
            "blob",
            "download-batch",
            "--account-name",
            account_name,
            "--source",
            container_name,
            "--destination",
            str(destination),
            "--pattern",
            "weather_*.csv",
            "--auth-mode",
            "key",
            "--overwrite",
            "true",
            "--max-connections",
            "8",
            "--no-progress",
            "--only-show-errors",
            "-o",
            "none",
        ]
    )


def update_raw(account_name, containers):
    """Refresh local monthly weather CSVs from Azure Blob Storage."""
    total_blobs = 0

    for container_name in containers:
        blobs = list_blobs(account_name, container_name)
        download_container_batch(account_name, container_name, RAW_DIR / container_name)
        local_count = len(list((RAW_DIR / container_name).glob("weather_*.csv")))
        total_blobs += len(blobs)
        print(
            f"synced {container_name}: {local_count} local weather CSVs "
            f"from {len(blobs)} Azure blobs"
        )

    print(f"synced {total_blobs} weather blobs total")


def get_visualcrossing_api_keys(resource_group, function_app):
    """Read Visual Crossing API keys from the existing Azure Function settings."""
    output = run_az(
        [
            "functionapp",
            "config",
            "appsettings",
            "list",
            "--resource-group",
            resource_group,
            "--name",
            function_app,
            "-o",
            "json",
        ]
    )
    settings = {item["name"]: item.get("value", "") for item in json.loads(output)}

    hourly_key = settings.get("HOURLY_API_KEY", "").strip()
    keys = []
    if hourly_key:
        keys.append(hourly_key)

    for api_key in settings.get("API_KEYS", "").split(","):
        api_key = api_key.strip()
        if api_key and api_key not in keys:
            keys.append(api_key)

    if not keys:
        raise RuntimeError("No Visual Crossing API key found in Azure Function settings.")

    return keys


def month_start_end(year, month, today):
    """Return the first and last date to request for a month."""
    start = date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    end = date(year, month, last_day)
    if year == today.year and month == today.month:
        end = today
    return start, end


def previous_month(today):
    """Return the previous calendar month as a ``(year, month)`` tuple."""
    if today.month == 1:
        return today.year - 1, 12
    return today.year, today.month - 1


def month_range(start, end):
    """Yield ``(year, month)`` pairs touched by an inclusive date range."""
    year = start.year
    month = start.month
    stop = (end.year, end.month)

    while (year, month) <= stop:
        yield year, month
        if month == 12:
            year += 1
            month = 1
        else:
            month += 1


def iot_overlap_months():
    """Return weather months needed to cover the current IoT cache."""
    path = Path("data/interim/iot_hourly.csv")
    if not path.exists():
        return []

    frame = pd.read_csv(path, parse_dates=["timestamp_utc"])
    if frame.empty:
        return []

    start = frame["timestamp_utc"].min()
    end = frame["timestamp_utc"].max()
    if pd.isna(start) or pd.isna(end):
        return []

    return list(month_range(start.date(), end.date()))


def build_visualcrossing_url(location, api_key, start, end):
    """Build a monthly Visual Crossing hourly CSV request URL."""
    params = urllib.parse.urlencode(
        {
            "unitGroup": "metric",
            "key": api_key,
            "contentType": "csv",
            "include": "hours",
            "elements": DIRECT_ELEMENTS,
            "maxDistance": "25000",
        }
    )
    safe_location = urllib.parse.quote(location)
    return (
        "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/"
        f"timeline/{safe_location}/{start.isoformat()}/{end.isoformat()}?{params}"
    )


def read_http_error_body(error):
    """Best-effort body extraction for Visual Crossing HTTP errors."""
    try:
        return error.read().decode("utf-8", errors="replace")
    except Exception:
        return ""


def fetch_direct_month(location, api_keys, year, month, today, target):
    """Download one direct Visual Crossing month, rotating keys on 429s."""
    start, end = month_start_end(year, month, today)
    payload = None

    for idx, api_key in enumerate(api_keys, start=1):
        url = build_visualcrossing_url(location, api_key, start, end)
        try:
            with urllib.request.urlopen(url, timeout=120) as response:
                payload = response.read()
            break
        except urllib.error.HTTPError as error:
            body = read_http_error_body(error)
            if error.code == 429:
                print(f"Visual Crossing key #{idx} is rate-limited; trying next key")
                continue
            raise RuntimeError(f"Visual Crossing HTTP {error.code}: {body}") from error

    if payload is None:
        raise RuntimeError("All configured Visual Crossing API keys were rate-limited.")

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(payload)
    print(f"direct Visual Crossing update: wrote {target} ({len(payload)} bytes)")


def update_kerkrade_direct_api(
    resource_group,
    function_app,
    location=DEFAULT_DIRECT_LOCATION,
    container=DEFAULT_DIRECT_CONTAINER,
    full_refresh=False,
):
    """Direct-refresh Kerkrade months that matter for the current analysis.

    Blob storage is the durable source, but it may lag the current month or the
    exact IoT overlap. This catch-up step keeps Week 1/2 analysis frames filled.
    """
    today = date.today()
    current_year_month = (today.year, today.month)
    previous_year_month = previous_month(today)

    target_dir = RAW_DIR / container
    months = [current_year_month]

    previous_target = (
        target_dir
        / f"weather_{location}_{previous_year_month[0]:04d}-{previous_year_month[1]:02d}.csv"
    )
    if full_refresh or not previous_target.exists():
        months.insert(0, previous_year_month)

    for year_month in iot_overlap_months():
        if year_month not in months:
            months.insert(0, year_month)

    months = sorted(set(months))
    api_keys = get_visualcrossing_api_keys(resource_group, function_app)
    for year, month in months:
        target = target_dir / f"weather_{location}_{year:04d}-{month:02d}.csv"
        fetch_direct_month(location, api_keys, year, month, today, target)


def write_normalized():
    """Write long and wide hourly weather frames for analysis."""
    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    weather_long = load_weather(raw_dir=RAW_DIR, frequency="h", wide=False)
    weather_wide = load_weather(raw_dir=RAW_DIR, frequency="h", wide=True)

    long_target = INTERIM_DIR / "weather_hourly_long.csv"
    wide_target = INTERIM_DIR / "weather_hourly.csv"
    weather_long.to_csv(long_target, index=False)
    weather_wide.to_csv(wide_target, index_label="timestamp_utc")

    print(f"wrote {long_target}")
    print(f"wrote {wide_target}")
    print(
        weather_long.groupby("weather_location")["timestamp"]
        .agg(["count", "min", "max"])
        .to_string()
    )


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--account-name", default=DEFAULT_ACCOUNT)
    parser.add_argument(
        "--container",
        action="append",
        dest="containers",
        help="weather container to sync; may be supplied multiple times",
    )
    parser.add_argument(
        "--full-refresh",
        action="store_true",
        help="force direct Kerkrade API catch-up to refresh the previous month too",
    )
    parser.add_argument(
        "--skip-blob-sync",
        action="store_true",
        help="skip Azure weather blob sync but still run direct Kerkrade API catch-up",
    )
    parser.add_argument(
        "--skip-direct-api",
        action="store_true",
        help="skip direct Kerkrade Visual Crossing current-month catch-up",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="only rebuild normalized output from existing raw files",
    )
    parser.add_argument("--function-resource-group", default=DEFAULT_FUNCTION_RESOURCE_GROUP)
    parser.add_argument("--function-app", default=DEFAULT_FUNCTION_APP)
    return parser.parse_args()


def main():
    """Command-line entry point."""
    args = parse_args()
    containers = args.containers or DEFAULT_CONTAINERS
    if not args.skip_download:
        if not args.skip_blob_sync:
            update_raw(
                account_name=args.account_name,
                containers=containers,
            )
        if not args.skip_direct_api:
            update_kerkrade_direct_api(
                resource_group=args.function_resource_group,
                function_app=args.function_app,
                full_refresh=args.full_refresh,
            )
    write_normalized()


if __name__ == "__main__":
    main()
