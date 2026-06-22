"""Week 4 KNMI reference meteorology starter ingestion."""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".matplotlib"))

import pandas as pd

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
FILENAME_PREFIX = "KMDS__OPER_P___10M_OBS_L2"


def list_knmi_files(api_key, dataset, version, max_files):
    """List recent KNMI Data Platform files for a dataset."""
    import requests

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
    import requests

    raw_dir.mkdir(parents=True, exist_ok=True)
    destination = raw_dir / filename
    if destination.exists():
        print(f"cached {destination}")
        return "cached"

    url_response = requests.get(
        f"{KDP_BASE_URL}/datasets/{dataset}/versions/{version}/files/{filename}/url",
        headers={"Authorization": api_key},
        timeout=60,
    )
    if url_response.status_code == 404:
        print(f"not found {filename}")
        return "not_found"
    url_response.raise_for_status()
    download_url = url_response.json()["temporaryDownloadUrl"]

    with requests.get(download_url, stream=True, timeout=120) as response:
        response.raise_for_status()
        with destination.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)
    print(f"downloaded {destination}")
    return "downloaded"


def filename_window(start, end, max_files):
    """Build expected 10-minute KNMI filenames for a UTC timestamp window."""
    start_ts = pd.Timestamp(start)
    end_ts = pd.Timestamp(end)
    if start_ts.tzinfo is None:
        start_ts = start_ts.tz_localize("UTC")
    else:
        start_ts = start_ts.tz_convert("UTC")
    if end_ts.tzinfo is None:
        end_ts = end_ts.tz_localize("UTC")
    else:
        end_ts = end_ts.tz_convert("UTC")

    timestamps = pd.date_range(
        start=start_ts.floor("10min"),
        end=end_ts.ceil("10min"),
        freq="10min",
        inclusive="both",
    )
    filenames = [
        f"{FILENAME_PREFIX}_{timestamp.strftime('%Y%m%d%H%M')}.nc"
        for timestamp in timestamps
    ]
    return filenames[:max_files] if max_files else filenames


def maybe_download(args):
    """Download KNMI raw files unless running from cache only."""
    if args.skip_download:
        print("KNMI download skipped; using cached raw files only.")
        return

    api_key = os.environ.get("KNMI_API_KEY")
    if not api_key:
        print("KNMI_API_KEY is not set; using cached raw files only.")
        return

    date_window = args.start is not None or args.end is not None
    if date_window:
        if args.start is None or args.end is None:
            raise ValueError("KNMI date-window downloads require both --start and --end")
        expected_filenames = filename_window(args.start, args.end, args.max_files)
        missing_filenames = [
            filename
            for filename in expected_filenames
            if not (args.raw_dir / filename).exists()
        ]
        filenames = missing_filenames
        if args.max_downloads is not None:
            filenames = filenames[: args.max_downloads]
        sleep_seconds = (
            args.download_sleep_seconds
            if args.download_sleep_seconds is not None
            else (3.7 if args.max_downloads is None else 0.2)
        )
        print(
            f"KNMI date-window download: {len(expected_filenames)} expected files, "
            f"{len(expected_filenames) - len(missing_filenames)} cached, "
            f"{len(missing_filenames)} missing, {len(filenames)} planned this run, "
            f"sleep={sleep_seconds}s between API URL requests."
        )
    else:
        filenames = list_knmi_files(
            api_key=api_key,
            dataset=args.dataset,
            version=args.version,
            max_files=args.max_files,
        )
        sleep_seconds = args.download_sleep_seconds or 0.0

    if not filenames:
        print("No KNMI files to request in this run.")
        return

    counts = {"cached": 0, "downloaded": 0, "not_found": 0}
    for i, filename in enumerate(filenames, start=1):
        print(f"[{i}/{len(filenames)}] {filename}")
        status = download_knmi_file(api_key, args.dataset, args.version, filename, args.raw_dir)
        counts[status] = counts.get(status, 0) + 1
        if sleep_seconds and i < len(filenames):
            time.sleep(sleep_seconds)
    print(
        "KNMI download pass complete "
        f"(downloaded={counts['downloaded']}, cached={counts['cached']}, "
        f"not_found={counts['not_found']})."
    )


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
    comparison_cols = [
        column
        for column in ["knmi_pressure_hpa", "knmi_temperature_c"]
        if column in comparison
    ]
    if comparison_cols:
        comparison = comparison.dropna(subset=comparison_cols, how="all")

    if comparison.empty:
        for path in [COMPARISON_PATH, PLOT_PATH]:
            if path.exists():
                path.unlink()
        print("No overlapping KNMI/Visual Crossing rows; comparison outputs skipped.")
        return

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    comparison.to_csv(COMPARISON_PATH, index=False)

    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print(f"wrote {COMPARISON_PATH}")
        print("matplotlib is not installed; skipped KNMI comparison plot.")
        return

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
    parser.add_argument(
        "--max-downloads",
        type=int,
        default=None,
        help="For date-window pulls, request at most this many missing files in one run.",
    )
    parser.add_argument(
        "--download-sleep-seconds",
        type=float,
        default=None,
        help="Pause between KNMI API URL requests. Date-window downloads default to 3.7s.",
    )
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
    except (FileNotFoundError, ValueError) as exc:
        print(exc)
        if "xarray/netCDF4" in str(exc):
            print(
                "Next step: update the conda environment from environment.yml "
                "so cached KNMI NetCDF files can be normalized."
            )
        else:
            print(
                "Next step: get a KNMI Open Data API key, export the selected "
                "station observations to CSV/JSON under data/raw/knmi/, or rerun "
                "without --skip-download once KNMI_API_KEY is set."
            )
        return
    write_visual_crossing_comparison(knmi)


if __name__ == "__main__":
    main()
