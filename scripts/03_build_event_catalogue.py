"""Build the Task 1.4 discharge-based soft-label event catalogue."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.eval import (
    annotate_event_overlap,
    discharge_thresholds,
    hourly_discharge_soft_labels,
    sustained_exceedance_events,
)


INTERIM_DIR = Path("data/interim")
PROCESSED_DIR = Path("data/processed")


def load_hourly_csv(path):
    """Read a timestamp-indexed hourly CSV."""
    frame = pd.read_csv(path, parse_dates=["timestamp_utc"])
    return frame.set_index("timestamp_utc").sort_index()


def parse_csv_floats(value):
    """Parse a comma-separated CLI value into floats."""
    return tuple(float(item.strip()) for item in value.split(",") if item.strip())


def parse_csv_ints(value):
    """Parse a comma-separated CLI value into integers."""
    return tuple(int(item.strip()) for item in value.split(",") if item.strip())


def write_outputs(args):
    """Build thresholds, events, and hourly soft labels from discharge data."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    discharge = load_hourly_csv(INTERIM_DIR / "discharge_hourly.csv")
    thresholds = discharge_thresholds(discharge, quantiles=args.quantiles)
    labels = hourly_discharge_soft_labels(
        discharge,
        quantiles=args.quantiles,
        antecedent_windows=args.antecedent_windows,
    )
    events = sustained_exceedance_events(
        discharge,
        quantiles=args.quantiles,
        min_duration_hours=args.min_duration_hours,
        antecedent_windows=args.antecedent_windows,
    )

    iot_index = None
    iot_path = INTERIM_DIR / "iot_hourly.csv"
    if iot_path.exists():
        iot_index = load_hourly_csv(iot_path).index

    weather_index = None
    weather_path = INTERIM_DIR / "weather_hourly.csv"
    if weather_path.exists():
        weather_index = load_hourly_csv(weather_path).index

    events = annotate_event_overlap(
        events,
        iot_index=iot_index,
        weather_index=weather_index,
    )

    thresholds_target = PROCESSED_DIR / "discharge_thresholds.csv"
    events_target = PROCESSED_DIR / "event_catalogue.csv"
    labels_target = PROCESSED_DIR / "hourly_soft_labels.csv"

    thresholds.to_csv(thresholds_target, index=False)
    events.to_csv(events_target, index=False)
    labels.to_csv(labels_target, index_label="timestamp_utc")

    print(f"wrote {thresholds_target} ({len(thresholds)} rows)")
    print(f"wrote {events_target} ({len(events)} rows)")
    print(f"wrote {labels_target} ({len(labels)} rows)")

    if not events.empty:
        summary = (
            events.groupby(["source", "threshold_quantile"])["event_id"]
            .count()
            .rename("events")
            .reset_index()
        )
        print(summary.to_string(index=False))


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--quantiles",
        default="0.90,0.95,0.99",
        type=parse_csv_floats,
        help="comma-separated discharge percentiles used for soft labels",
    )
    parser.add_argument(
        "--antecedent-windows",
        default="24,72,168",
        type=parse_csv_ints,
        help="comma-separated antecedent windows in hours",
    )
    parser.add_argument(
        "--min-duration-hours",
        default=6,
        type=int,
        help="minimum contiguous exceedance duration for event catalogue rows",
    )
    return parser.parse_args()


if __name__ == "__main__":
    write_outputs(parse_args())
