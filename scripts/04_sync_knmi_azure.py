"""Sync Azure-collected KNMI station-slim blobs into local analysis storage.

The Azure Timer Function does the slow historical KNMI backfill and writes
compact monthly CSV.GZ blobs. This script brings those compact blobs back into
``data/raw/knmi/azure_slim/`` and can then rebuild ``data/interim/knmi_hourly.csv``
from the local cache.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

DEFAULT_ACCOUNT = "stknmikerkradebg01"
DEFAULT_CONTAINER = "knmi-data"
DEFAULT_PREFIX = "slim/10-minute-in-situ"
DEFAULT_DESTINATION = Path("data/raw/knmi/azure_slim")
INGEST_SCRIPT = Path("scripts/04_ingest_knmi.py")


def run_command(command):
    """Run one command and show a compact error if it fails."""
    print("+ " + " ".join(str(part) for part in command))
    completed = subprocess.run(command, text=True, capture_output=True)
    if completed.stdout:
        print(completed.stdout.strip())
    if completed.returncode != 0:
        if completed.stderr:
            print(completed.stderr.strip(), file=sys.stderr)
        raise SystemExit(completed.returncode)
    return completed


def sync_slim_blobs(args):
    """Download monthly station-slim KNMI blobs from Azure Blob Storage."""
    args.destination.mkdir(parents=True, exist_ok=True)
    command = [
        "az",
        "storage",
        "blob",
        "download-batch",
        "--account-name",
        args.account_name,
        "--source",
        args.container,
        "--destination",
        str(args.destination),
        "--pattern",
        f"{args.prefix.strip('/')}/*",
        "--auth-mode",
        args.auth_mode,
        "--overwrite",
        "true" if args.overwrite else "false",
        # azure-cli's interactive progress reporter can crash on gzip blobs
        # (upstream AssertionError); the sync is non-interactive anyway.
        "--no-progress",
    ]
    run_command(command)


def download_state(args):
    """Keep a local copy of the Azure cursor state for quick inspection."""
    state_dir = args.destination / "_state"
    state_dir.mkdir(parents=True, exist_ok=True)
    for blob_name in [
        "state/knmi_backfill_state.json",
        "state/knmi_invocation_diagnostic.json",
    ]:
        target = state_dir / Path(blob_name).name
        command = [
            "az",
            "storage",
            "blob",
            "download",
            "--account-name",
            args.account_name,
            "--container-name",
            args.container,
            "--name",
            blob_name,
            "--file",
            str(target),
            "--auth-mode",
            args.auth_mode,
            "--overwrite",
            "true",
            "--no-progress",
        ]
        run_command(command)


def rebuild_hourly(args):
    """Rebuild the hourly KNMI analysis table from the synced slim cache."""
    command = [
        sys.executable,
        str(INGEST_SCRIPT),
        "--skip-download",
        "--raw-dir",
        str(args.destination),
        "--station-set",
        args.station_set,
        "--comparison-station",
        args.comparison_station,
    ]
    if args.start:
        command.extend(["--start", args.start])
    if args.end:
        command.extend(["--end", args.end])
    run_command(command)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--account-name", default=DEFAULT_ACCOUNT)
    parser.add_argument("--container", default=DEFAULT_CONTAINER)
    parser.add_argument("--prefix", default=DEFAULT_PREFIX)
    parser.add_argument("--destination", type=Path, default=DEFAULT_DESTINATION)
    parser.add_argument(
        "--auth-mode",
        choices=["key", "login"],
        default="key",
        help="Use 'login' if RBAC is configured; 'key' matches the other repo scripts.",
    )
    parser.add_argument(
        "--no-overwrite",
        dest="overwrite",
        action="store_false",
        help="Do not replace local monthly blobs. Default overwrites because Azure appends monthly blobs.",
    )
    parser.add_argument(
        "--skip-state",
        action="store_true",
        help="Skip downloading the Azure state/diagnostic JSON files.",
    )
    parser.add_argument(
        "--skip-rebuild",
        action="store_true",
        help="Only sync blobs; do not rebuild data/interim/knmi_hourly.csv.",
    )
    parser.add_argument("--station-set", default="meuse")
    parser.add_argument("--comparison-station", default="06380")
    parser.add_argument("--start")
    parser.add_argument("--end")
    return parser.parse_args()


def main():
    """Command-line entry point."""
    args = parse_args()
    sync_slim_blobs(args)
    if not args.skip_state:
        download_state(args)
    if not args.skip_rebuild:
        rebuild_hourly(args)


if __name__ == "__main__":
    main()
