"""Write a provenance manifest for the current chapter-analysis snapshot."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd

from src.provenance import write_run_manifest

ANALYSIS_PATH = Path("data/interim/analysis_hourly.csv")
MANIFEST_PATH = Path("results/run_manifest.json")

DEFAULT_INPUTS = [
    ANALYSIS_PATH,
    Path("data/interim/knmi_hourly.csv"),
    Path("data/interim/discharge_hourly.csv"),
    Path("data/processed/co2-residual-barometric.csv"),
    Path("data/processed/signal_characterization_frame.csv"),
    Path("data/processed/event_catalogue.csv"),
]

DEFAULT_COMMANDS = [
    "python scripts/01_eda.py",
    "python scripts/02_barometric_baseline.py",
    "python scripts/03_eryilmaz_replication.py",
    "python scripts/04_signal_characterization.py",
    "python scripts/05_sarimax.py",
    "python scripts/06_kalman.py",
    "python scripts/07_isolation_forest.py",
    "python scripts/08_ensemble_agreement.py",
    "python scripts/09_synthetic_injection.py",
    "python scripts/10_evaluation.py",
    "python scripts/12_distributed_lag.py",
    "python scripts/13_write_run_manifest.py",
]


def result_outputs(manifest_path=MANIFEST_PATH):
    """Inventory every current result artifact except the manifest itself."""
    manifest_path = Path(manifest_path).resolve()
    return sorted(
        path
        for path in Path("results").rglob("*")
        if path.is_file() and path.resolve() != manifest_path
    )


def analysis_cutoff(path=ANALYSIS_PATH):
    """Return the maximum timestamp in the canonical analysis grid."""
    timestamps = pd.read_csv(path, usecols=["timestamp_utc"])["timestamp_utc"]
    return pd.to_datetime(timestamps, utc=True).max()


def main():
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=MANIFEST_PATH)
    parser.add_argument(
        "--command",
        action="append",
        dest="commands",
        help="Executed command to record; repeat for multiple commands.",
    )
    args = parser.parse_args()

    manifest = write_run_manifest(
        path=args.output,
        input_paths=DEFAULT_INPUTS,
        output_paths=result_outputs(args.output),
        commands=args.commands or DEFAULT_COMMANDS,
        data_cutoff=analysis_cutoff(),
    )
    print(f"wrote {args.output}")
    print(f"run_id: {manifest['run_id']}")


if __name__ == "__main__":
    main()
