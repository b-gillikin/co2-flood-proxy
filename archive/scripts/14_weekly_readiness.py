"""Compute weekly chapter-readiness coverage and optionally append the plan log."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd

ANALYSIS_PATH = Path("data/interim/analysis_hourly.csv")
KNMI_PATH = Path("data/interim/knmi_hourly.csv")
GROUNDWATER_PATH = Path("data/interim/groundwater_daily.csv")
WINDOWS_PATH = Path("results/evaluation/evaluation_windows.csv")
OUTPUT_PATH = Path("results/readiness/weekly_status.json")
PLAN_PATH = Path("docs/chapter-readiness-plan.md")

RESTORATION_START = pd.Timestamp("2026-07-09T00:00:00Z")
REFERENCE_STATION = "06380"
LOG_MARKER = "<!-- weekly-log-rows -->"


def contiguous_blocks(index):
    """Return strictly hourly blocks from a timestamp index."""
    index = pd.DatetimeIndex(index).sort_values().unique()
    if len(index) == 0:
        return []
    series = pd.Series(index)
    block_id = series.diff().gt(pd.Timedelta(hours=1)).cumsum()
    return [pd.DatetimeIndex(group) for _, group in series.groupby(block_id)]


def groundwater_paired_days(iot_days, path=GROUNDWATER_PATH):
    """Count IoT days paired with any normalized groundwater level column."""
    if not Path(path).exists():
        return 0
    groundwater = pd.read_csv(path)
    time_column = next(
        (column for column in ("date_utc", "timestamp_utc") if column in groundwater),
        None,
    )
    value_columns = [column for column in groundwater if "water_level" in column]
    if time_column is None or not value_columns:
        return 0
    groundwater_days = pd.to_datetime(groundwater[time_column], utc=True).dt.floor("D")
    observed = groundwater[value_columns].notna().any(axis=1)
    return len(set(groundwater_days[observed]) & set(iot_days))


def build_status(
    analysis_path=ANALYSIS_PATH,
    knmi_path=KNMI_PATH,
    groundwater_path=GROUNDWATER_PATH,
    windows_path=WINDOWS_PATH,
    refresh_date=None,
):
    """Build the weekly status record from normalized local artifacts."""
    analysis = pd.read_csv(analysis_path, parse_dates=["timestamp_utc"])
    analysis["timestamp_utc"] = pd.to_datetime(analysis["timestamp_utc"], utc=True)
    observed = pd.DatetimeIndex(analysis.loc[analysis["iot_co2_ppm"].notna(), "timestamp_utc"])
    blocks = contiguous_blocks(observed)
    longest_block_hours = max((len(block) for block in blocks), default=0)

    post_blocks = [block for block in blocks if block.max() >= RESTORATION_START]
    if post_blocks:
        latest_post_block = max(post_blocks, key=lambda block: block.max())
        latest_post_block = latest_post_block[latest_post_block >= RESTORATION_START]
    else:
        latest_post_block = pd.DatetimeIndex([], tz="UTC")

    knmi_overlap = None
    if Path(knmi_path).exists() and len(latest_post_block):
        knmi = pd.read_csv(knmi_path, usecols=["timestamp_utc", "knmi_station"])
        station = knmi["knmi_station"].astype(str).str.split(".").str[0].str.zfill(5)
        knmi_hours = pd.to_datetime(
            knmi.loc[station == REFERENCE_STATION, "timestamp_utc"], utc=True
        ).dt.floor("h")
        knmi_overlap = len(set(latest_post_block) & set(knmi_hours)) / len(latest_post_block)

    iot_days = observed.floor("D").unique()
    paired_days = groundwater_paired_days(iot_days, path=groundwater_path)

    usable_windows = 0
    if Path(windows_path).exists():
        windows = pd.read_csv(windows_path)
        usable_windows = int(
            (
                (windows["scheme"] == "official_30d_train_7d_eval") & (windows["status"] == "ok")
            ).sum()
        )

    return {
        "refresh_date": str(refresh_date or date.today()),
        "iot_latest_utc": observed.max().isoformat() if len(observed) else None,
        "co2_observed_share": len(observed) / len(analysis) if len(analysis) else None,
        "longest_block_hours": longest_block_hours,
        "post_restoration_block_days": len(latest_post_block) / 24,
        "knmi_06380_overlap": knmi_overlap,
        "groundwater_paired_days": paired_days,
        "usable_official_windows": usable_windows,
    }


def markdown_row(status, notes="Weekly coverage/QC refresh only"):
    """Render one canonical readiness-log row."""
    observed_share = status["co2_observed_share"]
    overlap = status["knmi_06380_overlap"]
    observed_token = f"{observed_share:.1%}" if observed_share is not None else "n/a"
    overlap_token = f"{overlap:.1%}" if overlap is not None else "pending"
    return (
        f"| {status['refresh_date']} | {status['iot_latest_utc'] or 'none'} | "
        f"{observed_token} | {status['longest_block_hours']} | "
        f"{status['post_restoration_block_days']:.1f} | "
        f"{overlap_token} | "
        f"{status['groundwater_paired_days']} | "
        f"{status['usable_official_windows']} | {notes} |"
    )


def append_plan_row(plan_path, row, refresh_date):
    """Insert or replace the row for one date immediately before the marker."""
    plan_path = Path(plan_path)
    text = plan_path.read_text(encoding="utf-8")
    if LOG_MARKER not in text:
        raise ValueError(f"Missing weekly log marker in {plan_path}")
    lines = text.splitlines()
    prefix = f"| {refresh_date} |"
    lines = [line for line in lines if not line.startswith(prefix)]
    marker_index = lines.index(LOG_MARKER)
    lines.insert(marker_index, row)
    plan_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--append-plan", action="store_true")
    parser.add_argument("--refresh-date", default=str(date.today()))
    parser.add_argument("--notes", default="Weekly coverage/QC refresh only")
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()

    status = build_status(refresh_date=args.refresh_date)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    row = markdown_row(status, notes=args.notes)
    print(row)
    if args.append_plan:
        append_plan_row(PLAN_PATH, row, args.refresh_date)
        print(f"updated {PLAN_PATH}")
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
