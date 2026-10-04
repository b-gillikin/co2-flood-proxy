"""Read-only candidate cross-border clock and coverage audit for LANUK exports.

Global p99 below is only a provisional diagnostic. Do not pool German labels
with the Dutch chapter fit before provider reconstruction/rating answers.
"""

from __future__ import annotations

import hashlib
import json
from datetime import timedelta, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/raw/external_deliveries/lanuk_nrw/2026-09-23"
OUT = ROOT / "results/event_study/cross_tributary_rain_v1"
STATIONS = {
    "herzogenrath1": "Wurm upstream",
    "randerath": "Wurm downstream",
    "herzogenrath2": "Broicher Bach",
    "honsdorf": "Beeckfließ",
}
FIXED_UTC_PLUS_ONE = timezone(timedelta(hours=1))


def read_station(path):
    table = pd.read_csv(
        path, sep=";", skiprows=32, names=["source_time", "value"], encoding="latin1", dtype=str
    )
    source_time = pd.to_datetime(table.source_time, format="%d.%m.%Y %H:%M:%S")
    source_time = source_time.dt.tz_localize(FIXED_UTC_PLUS_ONE).dt.tz_convert("UTC")
    value = pd.to_numeric(
        table.value.str.strip().str.replace(",", ".", regex=False), errors="coerce"
    )
    series = pd.Series(value.to_numpy(), index=pd.DatetimeIndex(source_time), name="q_m3s")
    if series.index.has_duplicates or not series.index.is_monotonic_increasing:
        raise ValueError(f"Duplicate/unordered source timestamps: {path}")
    if not series.index.to_series().diff().iloc[1:].eq(pd.Timedelta(minutes=15)).all():
        raise ValueError(f"Non-quarter-hour source grid: {path}")
    return series


def complete_hourly(quarters):
    grouped = quarters.resample("h", closed="right", label="right")
    mean = grouped.mean()
    count = grouped.count()
    return mean.where(count.eq(4))


def main():
    rain_events = pd.read_csv(
        OUT / "rain_episodes.csv", parse_dates=["rain_start_utc", "response_end_utc"]
    )
    july = rain_events.loc[
        rain_events.rain_start_utc.between(
            pd.Timestamp("2021-07-13", tz="UTC"), pd.Timestamp("2021-07-15", tz="UTC")
        )
    ]
    if len(july) != 1:
        raise ValueError("Cannot identify the July 2021 Dutch rain episode")
    event = july.iloc[0]
    rows = []
    hashes = {}
    for station, watercourse in STATIONS.items():
        matches = list(
            (SOURCE / station).glob("*abfluss_mit_m_s_csv_export_mittelwerte_15minuten*.csv")
        )
        if len(matches) != 1:
            raise ValueError(f"Expected one LANUK discharge export for {station}")
        path = matches[0]
        quarters = read_station(path)
        hourly = complete_hourly(quarters)
        july_hourly = hourly.loc[event.rain_start_utc : event.response_end_utc]
        provisional_p99 = float(hourly.quantile(0.99))
        rows.append(
            {
                "station": station,
                "watercourse": watercourse,
                "first_utc": quarters.index.min(),
                "last_utc": quarters.index.max(),
                "quarter_hour_rows": len(quarters),
                "blank_quarter_hours": int(quarters.isna().sum()),
                "complete_hourly_rows": int(hourly.notna().sum()),
                "provisional_full_series_p99_m3s": provisional_p99,
                "july2021_window_complete_hours": int(july_hourly.notna().sum()),
                "july2021_window_max_m3s": float(july_hourly.max()),
                "july2021_window_any_above_provisional_p99": bool(
                    july_hourly.gt(provisional_p99).any()
                ),
            }
        )
        hashes[station] = hashlib.sha256(path.read_bytes()).hexdigest()
    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(OUT / "german_candidate_source_audit.csv", index=False)
    manifest = {
        "status": "candidate source compatibility only; p99 is not provider-validated",
        "source_clock": "fixed UTC+1, trailing 15-minute means; hourly mean at right edge",
        "july_dutch_rain_episode": event.episode_id,
        "source_sha256": hashes,
        "pending": "provider reconstruction periods, provisional rating histories, academic reuse terms",
    }
    (OUT / "german_candidate_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
