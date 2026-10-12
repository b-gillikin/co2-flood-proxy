#!/usr/bin/env python3
"""Build aligned historical event windows for the Limburg basin-AI study.

The output separates observations available through the event onset from the
post-onset outcome. It creates an auditable event library, not model features,
analogue labels, predictions or new empirical results.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "results/basin_ai_event_library"

INPUTS = {
    "events": ROOT / "results/event_study/real_data_v1/event_analysis_status.csv",
    "discharge": ROOT / "data/interim/event_study_discharge_hourly.csv",
    "rainfall": ROOT / "data/interim/radolan_catchment_hourly.csv",
    "weather": ROOT / "data/interim/event_study_weather_hourly.csv",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def relative_hours(history_hours: int, outcome_hours: int) -> np.ndarray:
    if history_hours < 1 or outcome_hours < 1:
        raise ValueError("history_hours and outcome_hours must both be positive")
    return np.arange(-history_hours, outcome_hours + 1, dtype=int)


def _read_inputs() -> tuple[pd.DataFrame, ...]:
    events = pd.read_csv(INPUTS["events"])
    events["onset_utc"] = pd.to_datetime(events["onset_utc"], utc=True)

    discharge = pd.read_csv(INPUTS["discharge"])
    discharge["timestamp_utc"] = pd.to_datetime(discharge["timestamp_utc"], utc=True)
    discharge = discharge.set_index("timestamp_utc").sort_index()

    rainfall = pd.read_csv(INPUTS["rainfall"])
    rainfall["timestamp_utc"] = pd.to_datetime(rainfall["timestamp_utc"], utc=True)
    rainfall = rainfall.set_index("timestamp_utc").sort_index()

    weather = pd.read_csv(INPUTS["weather"])
    weather["timestamp_utc"] = pd.to_datetime(weather["timestamp_utc"], utc=True)
    weather = weather.set_index(["watercourse", "timestamp_utc"]).sort_index()
    return events, discharge, rainfall, weather


def build_event_library(history_hours: int = 168, outcome_hours: int = 72):
    events, discharge, rainfall, weather = _read_inputs()
    offsets = relative_hours(history_hours, outcome_hours)
    windows = []
    index_rows = []

    required_event_columns = {
        "event_id",
        "storm_id",
        "gauge",
        "watercourse",
        "onset_utc",
        "p99_m3s",
        "measurement_concern_y",
        "provider_status",
        "primary_usable",
    }
    missing = required_event_columns.difference(events.columns)
    if missing:
        raise ValueError(f"Event table is missing required columns: {sorted(missing)}")

    for event in events.itertuples(index=False):
        timestamps = event.onset_utc + pd.to_timedelta(offsets, unit="h")
        frame = pd.DataFrame(
            {
                "event_id": event.event_id,
                "storm_id": event.storm_id,
                "gauge": event.gauge,
                "watercourse": event.watercourse,
                "onset_utc": event.onset_utc,
                "timestamp_utc": timestamps,
                "relative_hour": offsets,
                "evidence_phase": np.where(offsets <= 0, "assessment_history", "withheld_outcome"),
            }
        )

        if event.gauge not in discharge.columns:
            raise ValueError(f"No discharge series for {event.gauge}")
        if event.watercourse not in rainfall.columns:
            raise ValueError(f"No rainfall series for {event.watercourse}")

        frame["target_discharge_m3s"] = discharge[event.gauge].reindex(timestamps).to_numpy()
        frame["catchment_rainfall_mm"] = rainfall[event.watercourse].reindex(timestamps).to_numpy()

        try:
            site_weather = weather.loc[event.watercourse]
        except KeyError as exc:
            raise ValueError(f"No weather series for {event.watercourse}") from exc
        aligned_weather = site_weather.reindex(timestamps)
        for column in (
            "relative_humidity_pct",
            "surface_pressure_hpa",
            "pressure_change_6h_hpa",
        ):
            frame[column] = aligned_weather[column].to_numpy()

        frame["target_discharge_observed"] = frame["target_discharge_m3s"].notna()
        frame["catchment_rainfall_observed"] = frame["catchment_rainfall_mm"].notna()
        frame["weather_observed"] = (
            frame[["relative_humidity_pct", "surface_pressure_hpa"]].notna().all(axis=1)
        )
        windows.append(frame)

        history = frame.relative_hour.le(0)
        outcome = frame.relative_hour.gt(0)
        index_rows.append(
            {
                "event_id": event.event_id,
                "storm_id": event.storm_id,
                "gauge": event.gauge,
                "watercourse": event.watercourse,
                "onset_utc": event.onset_utc,
                "p99_m3s": event.p99_m3s,
                "measurement_concern": bool(event.measurement_concern_y),
                "provider_status": event.provider_status,
                "primary_usable": bool(event.primary_usable),
                "history_start_utc": timestamps[0],
                "outcome_end_utc": timestamps[-1],
                "history_discharge_fraction": float(
                    frame.loc[history, "target_discharge_observed"].mean()
                ),
                "history_rainfall_fraction": float(
                    frame.loc[history, "catchment_rainfall_observed"].mean()
                ),
                "history_weather_fraction": float(frame.loc[history, "weather_observed"].mean()),
                "outcome_discharge_fraction": float(
                    frame.loc[outcome, "target_discharge_observed"].mean()
                ),
            }
        )

    event_windows = pd.concat(windows, ignore_index=True)
    event_index = pd.DataFrame(index_rows).sort_values(["onset_utc", "gauge"])
    if event_windows.duplicated(["event_id", "relative_hour"]).any():
        raise ValueError("Duplicate event-relative-hour rows")
    return event_index, event_windows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--history-hours", type=int, default=168)
    parser.add_argument("--outcome-hours", type=int, default=72)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    event_index, event_windows = build_event_library(
        history_hours=args.history_hours,
        outcome_hours=args.outcome_hours,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    event_index.to_csv(args.output_dir / "event_index.csv", index=False)
    event_windows.to_parquet(args.output_dir / "event_windows.parquet", index=False)

    manifest = {
        "status": "event library built; no representation model fitted",
        "history_hours": args.history_hours,
        "outcome_hours": args.outcome_hours,
        "assessment_cutoff": "relative_hour <= 0",
        "withheld_outcome": "relative_hour > 0",
        "event_count": int(len(event_index)),
        "window_row_count": int(len(event_windows)),
        "watercourses": sorted(event_index.watercourse.unique().tolist()),
        "primary_usable_events": int(event_index.primary_usable.sum()),
        "measurement_concern_events": int(event_index.measurement_concern.sum()),
        "complete_history": {
            "discharge": int(event_index.history_discharge_fraction.eq(1).sum()),
            "rainfall": int(event_index.history_rainfall_fraction.eq(1).sum()),
            "weather": int(event_index.history_weather_fraction.eq(1).sum()),
        },
        "input_sha256": {name: sha256(path) for name, path in INPUTS.items()},
    }
    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
