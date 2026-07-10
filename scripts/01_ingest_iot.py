"""Download/update and normalize the Kerkrade IoT stream for Task 1.1."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd

from src.io_data import load_iot, load_iot_observations

DEFAULT_ACCOUNT = "stkerkradeprod01bg"
DEFAULT_CONTAINER = "air-quality-device-data-1"
DEFAULT_PREFIX = "air_quality"

RAW_DIR = Path("data/raw/iot")
EXPORT_DIR = Path("iot-device-data")
INTERIM_DIR = Path("data/interim")
PROCESSED_DIR = Path("data/processed")


def run_az(args):
    """Run an Azure CLI command and show stdout/stderr if it fails."""
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


def list_blobs(account_name, container_name, prefix):
    """List daily IoT CSV blobs for the configured device stream."""
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
            "--prefix",
            prefix,
            "--query",
            "[].{name:name,size:properties.contentLength,lastModified:properties.lastModified}",
            "-o",
            "json",
        ]
    )
    blobs = json.loads(output)
    return sorted(
        [blob for blob in blobs if blob["name"].endswith(".csv")],
        key=lambda blob: blob["name"],
    )


def should_download(blob, target, full_refresh):
    """Use blob size as a cheap freshness check for the local raw cache."""
    if full_refresh or not target.exists():
        return True
    expected_size = blob.get("size")
    return expected_size is not None and target.stat().st_size != expected_size


def download_blob(account_name, container_name, blob_name, target):
    """Download one IoT CSV blob into the raw data directory."""
    target.parent.mkdir(parents=True, exist_ok=True)
    run_az(
        [
            "storage",
            "blob",
            "download",
            "--account-name",
            account_name,
            "--container-name",
            container_name,
            "--name",
            blob_name,
            "--file",
            str(target),
            "--auth-mode",
            "key",
            "--overwrite",
            "true",
            "-o",
            "none",
        ]
    )


def update_raw(account_name, container_name, prefix, full_refresh=False):
    """Sync missing or changed IoT raw files from Azure Blob Storage."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    blobs = list_blobs(account_name, container_name, prefix)
    downloaded = 0

    for blob in blobs:
        blob_name = blob["name"]
        target = RAW_DIR / Path(blob_name).name
        if should_download(blob, target, full_refresh):
            download_blob(account_name, container_name, blob_name, target)
            downloaded += 1

    print(f"checked {len(blobs)} IoT blobs in {container_name}; downloaded/updated {downloaded}")


def source_summary(observations):
    """Summarize raw IoT rows by source and device."""
    rows = []
    for keys, group in observations.groupby(
        ["iot_source", "iot_device_name", "iot_device_id"],
        dropna=False,
    ):
        source, device_name, device_id = keys
        rows.append(
            {
                "iot_source": source,
                "iot_device_name": device_name,
                "iot_device_id": device_id,
                "raw_rows_after_dedup": len(group),
                "start_utc": group["timestamp"].min(),
                "end_utc": group["timestamp"].max(),
                "co2_nonmissing": int(group["iot_co2_ppm"].notna().sum()),
                "source_files": int(group["iot_source_file"].nunique()),
            }
        )
    return pd.DataFrame(rows).sort_values(["start_utc", "iot_device_id"])


def coverage_gaps(iot):
    """Find gaps between non-empty hourly IoT CO2 observations."""
    observed = iot.loc[iot["iot_co2_ppm"].notna()].index.sort_values()
    rows = []
    for previous, current in zip(observed[:-1], observed[1:], strict=False):
        gap_hours = int((current - previous) / pd.Timedelta(hours=1)) - 1
        if gap_hours > 0:
            rows.append(
                {
                    "gap_start_utc": previous + pd.Timedelta(hours=1),
                    "gap_end_utc": current - pd.Timedelta(hours=1),
                    "gap_hours": gap_hours,
                    "previous_observed_utc": previous,
                    "next_observed_utc": current,
                }
            )
    return pd.DataFrame(rows)


def write_coverage_reports(observations, iot):
    """Write source and gap tables for the merged IoT record."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    source_path = PROCESSED_DIR / "iot_source_summary.csv"
    gaps_path = PROCESSED_DIR / "iot_coverage_gaps.csv"
    source_summary(observations).to_csv(source_path, index=False)
    coverage_gaps(iot).to_csv(gaps_path, index=False)
    print(f"wrote {source_path}")
    print(f"wrote {gaps_path}")


def write_normalized(export_dir=EXPORT_DIR, skip_exports=False):
    """Build the hourly IoT frame used by downstream analysis scripts."""
    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    blynk_export_dir = None if skip_exports else export_dir
    observations = load_iot_observations(
        raw_dir=RAW_DIR,
        blynk_export_dir=blynk_export_dir,
    )
    iot = load_iot(
        raw_dir=RAW_DIR,
        blynk_export_dir=blynk_export_dir,
        frequency="h",
    )
    target = INTERIM_DIR / "iot_hourly.csv"
    iot.to_csv(target, index_label="timestamp_utc")
    print(f"wrote {target}")
    print(iot.agg(["count", "min", "max"]).to_string())
    write_coverage_reports(observations, iot)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--account-name", default=DEFAULT_ACCOUNT)
    parser.add_argument("--container-name", default=DEFAULT_CONTAINER)
    parser.add_argument("--prefix", default=DEFAULT_PREFIX)
    parser.add_argument(
        "--full-refresh",
        action="store_true",
        help="download every matching IoT CSV blob even when a local copy exists",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="only rebuild normalized output from existing raw files",
    )
    parser.add_argument(
        "--export-dir",
        type=Path,
        default=EXPORT_DIR,
        help="Blynk device export folder to merge when present",
    )
    parser.add_argument(
        "--skip-exports",
        action="store_true",
        help="ignore local Blynk export folders and use Azure raw files only",
    )
    return parser.parse_args()


def main():
    """Command-line entry point."""
    args = parse_args()
    if not args.skip_download:
        update_raw(
            account_name=args.account_name,
            container_name=args.container_name,
            prefix=args.prefix,
            full_refresh=args.full_refresh,
        )
    write_normalized(export_dir=args.export_dir, skip_exports=args.skip_exports)


if __name__ == "__main__":
    main()
