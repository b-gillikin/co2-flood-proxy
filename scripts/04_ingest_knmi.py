"""Week 4 KNMI reference meteorology starter ingestion."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".matplotlib"))

import matplotlib.pyplot as plt
import pandas as pd
import requests

from src.io_data import load_knmi


RAW_DIR = Path("data/raw/knmi")
INTERIM_DIR = Path("data/interim")
RESULTS_DIR = Path("results/knmi")

ANALYSIS_PATH = INTERIM_DIR / "analysis_hourly.csv"
OUTPUT_PATH = INTERIM_DIR / "knmi_hourly.csv"
COMPARISON_PATH = RESULTS_DIR / "knmi_visualcrossing_comparison.csv"
PLOT_PATH = RESULTS_DIR / "knmi_vs_visualcrossing_pressure_temp.png"

KDP_BASE_URL = "https://api.dataplatform.knmi.nl/open-data/v1"
DEFAULT_DATASET = "10-minute-in-situ-meteorological-observations"
DEFAULT_VERSION = "1.0"


def list_knmi_files(api_key, dataset, version, max_files):
    """List recent KNMI Data Platform files for a dataset."""
    response = requests.get(
        f"{KDP_BASE_URL}/datasets/{dataset}/versions/{version}/files",
        headers={"Authorization": api_key},
        params={"maxKeys": max_files, "orderBy": "created", "sorting": "desc"},
        timeout=60,
    )
    response.raise_for_status()
    payload = response.json()
    if "error" in payload:
        raise RuntimeError(payload["error"])
    return [row["filename"] for row in payload.get("files", [])]


def download_knmi_file(api_key, dataset, version, filename, raw_dir):
    """Download one KNMI file through its temporary download URL."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    destination = raw_dir / filename
    if destination.exists():
        print(f"cached {destination}")
        return destination

    url_response = requests.get(
        f"{KDP_BASE_URL}/datasets/{dataset}/versions/{version}/files/{filename}/url",
        headers={"Authorization": api_key},
        timeout=60,
    )
    url_response.raise_for_status()
    download_url = url_response.json()["temporaryDownloadUrl"]

    with requests.get(download_url, stream=True, timeout=120) as response:
        response.raise_for_status()
        with destination.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)
    print(f"downloaded {destination}")
    return destination


def maybe_download(args):
    """Download KNMI raw files unless running from cache only."""
    if args.skip_download:
        print("KNMI download skipped; using cached raw files only.")
        return

    api_key = os.environ.get("KNMI_API_KEY")
    if not api_key:
        print("KNMI_API_KEY is not set; using cached raw files only.")
        return

    filenames = list_knmi_files(
        api_key=api_key,
        dataset=args.dataset,
        version=args.version,
        max_files=args.max_files,
    )
    if not filenames:
        raise RuntimeError(f"No KNMI files returned for {args.dataset}/{args.version}")

    for filename in filenames:
        download_knmi_file(api_key, args.dataset, args.version, filename, args.raw_dir)


def write_knmi_hourly(args):
    """Normalize cached KNMI data to the repo's hourly UTC convention."""
    frame = load_knmi(
        raw_dir=args.raw_dir,
        frequency="h",
        station=args.station,
        start=args.start,
        end=args.end,
    )
    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    frame.to_csv(OUTPUT_PATH, index=False)
    print(f"wrote {OUTPUT_PATH} ({len(frame)} rows)")
    return frame


def write_visual_crossing_comparison(knmi):
    """Compare KNMI pressure/temp to the existing Kerkrade Visual Crossing frame."""
    analysis = pd.read_csv(ANALYSIS_PATH, parse_dates=["timestamp_utc"])
    comparison = analysis[
        [
            "timestamp_utc",
            "kerkrade_weather_pressure_hpa",
            "kerkrade_weather_temp_c",
        ]
    ].merge(knmi, on="timestamp_utc", how="inner")

    if comparison.empty:
        print("No overlapping KNMI/Visual Crossing rows; comparison outputs skipped.")
        return

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    comparison.to_csv(COMPARISON_PATH, index=False)

    fig, axes = plt.subplots(2, 1, figsize=(12, 7), sharex=True, constrained_layout=True)
    if "knmi_pressure_hpa" in comparison:
        axes[0].plot(
            comparison["timestamp_utc"],
            comparison["kerkrade_weather_pressure_hpa"],
            label="Visual Crossing pressure",
            linewidth=1,
        )
        axes[0].plot(
            comparison["timestamp_utc"],
            comparison["knmi_pressure_hpa"],
            label="KNMI pressure",
            linewidth=1,
        )
    axes[0].set_ylabel("hPa")
    axes[0].grid(True, alpha=0.25)
    axes[0].legend(loc="upper right")

    if "knmi_temperature_c" in comparison:
        axes[1].plot(
            comparison["timestamp_utc"],
            comparison["kerkrade_weather_temp_c"],
            label="Visual Crossing temp",
            linewidth=1,
        )
        axes[1].plot(
            comparison["timestamp_utc"],
            comparison["knmi_temperature_c"],
            label="KNMI temp",
            linewidth=1,
        )
    axes[1].set_ylabel("deg C")
    axes[1].set_xlabel("timestamp_utc")
    axes[1].grid(True, alpha=0.25)
    axes[1].legend(loc="upper right")

    fig.suptitle("KNMI reference meteorology vs Kerkrade Visual Crossing")
    fig.savefig(PLOT_PATH, dpi=160)
    plt.close(fig)
    print(f"wrote {COMPARISON_PATH}")
    print(f"wrote {PLOT_PATH}")


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-download", action="store_true")
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument("--version", default=DEFAULT_VERSION)
    parser.add_argument("--max-files", type=int, default=4)
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--station")
    parser.add_argument("--start")
    parser.add_argument("--end")
    return parser.parse_args()


def main():
    """Command-line entry point."""
    args = parse_args()
    maybe_download(args)
    try:
        knmi = write_knmi_hourly(args)
    except FileNotFoundError as exc:
        print(exc)
        print(
            "Next step: get a KNMI Open Data API key, export the selected "
            "station observations to CSV/JSON under data/raw/knmi/, or rerun "
            "without --skip-download once KNMI_API_KEY is set."
        )
        return
    write_visual_crossing_comparison(knmi)


if __name__ == "__main__":
    main()
