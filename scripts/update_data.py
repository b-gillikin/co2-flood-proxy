"""Bring available chapter data sources up to date."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(script_name, extra_args=None):
    """Run one chapter pipeline script with the current Python interpreter."""
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script_name), *(extra_args or [])],
        cwd=ROOT,
        check=True,
    )


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-iot", action="store_true")
    parser.add_argument("--skip-weather", action="store_true")
    parser.add_argument("--skip-discharge", action="store_true")
    parser.add_argument("--skip-events", action="store_true")
    parser.add_argument("--skip-eda", action="store_true")
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="rebuild normalized outputs from existing raw files only",
    )
    parser.add_argument(
        "--full-refresh",
        action="store_true",
        help="force source scripts to replace or re-download raw files where supported",
    )
    return parser.parse_args()


def main():
    """Command-line entry point for the local refresh workflow."""
    args = parse_args()
    source_args = []
    if args.skip_download:
        source_args.append("--skip-download")
    if args.full_refresh:
        source_args.append("--full-refresh")

    if not args.skip_iot:
        run("01_ingest_iot.py", source_args)
    if not args.skip_weather:
        run("02_ingest_weather.py", source_args)
    if not args.skip_discharge:
        run("01_ingest_discharge.py", source_args)
    if not args.skip_events:
        run("03_build_event_catalogue.py")
    if not args.skip_eda:
        run("01_eda.py")


if __name__ == "__main__":
    main()
