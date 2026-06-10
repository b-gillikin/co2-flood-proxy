"""Download/update and normalize the Kerkrade IoT stream for Task 1.1."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.io_data import load_iot


DEFAULT_ACCOUNT = "stkerkradeprod01bg"
DEFAULT_CONTAINER = "air-quality-device-data-1"
DEFAULT_PREFIX = "air_quality"

RAW_DIR = Path("data/raw/iot")
INTERIM_DIR = Path("data/interim")


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

    print(
        f"checked {len(blobs)} IoT blobs in {container_name}; "
        f"downloaded/updated {downloaded}"
    )


def write_normalized():
    """Build the hourly IoT frame used by downstream analysis scripts."""
    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    iot = load_iot(raw_dir=RAW_DIR, frequency="h")
    target = INTERIM_DIR / "iot_hourly.csv"
    iot.to_csv(target, index_label="timestamp_utc")
    print(f"wrote {target}")
    print(iot.agg(["count", "min", "max"]).to_string())


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
    write_normalized()


if __name__ == "__main__":
    main()
