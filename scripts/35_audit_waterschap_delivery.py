"""Audit the delivered Waterschap discharge table without analysing outcomes.

The source contains a complete 15-minute time grid and blank gauge cells. This
script measures availability only. It does not calculate discharge thresholds,
events, peaks or signal contrasts while source semantics remain unresolved.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (
    ROOT / "data/raw/external_deliveries/waterschap_limburg/2026-08-19" / "databriangillikin.csv"
)
QC_PATH = ROOT / "data/processed/waterschap_discharge_qc.csv"
ANNUAL_PATH = ROOT / "data/processed/waterschap_discharge_annual_coverage.csv"

START = pd.Timestamp("2010-01-01 00:00")
END = pd.Timestamp("2026-01-01 00:00")

# Keys are unique even where the source repeats station ID 6.Q.27 in two
# columns. Descriptions reproduce source distinctions; none implies inclusion.
SERIES = [
    ("11.Q.32", "11.Q.32", "Eyserbeek", "Eys", ""),
    ("6.Q.18", "6.Q.18", "Geleenbeek", "Brommelen", ""),
    (
        "6.Q.24",
        "6.Q.24",
        "Geleenbeek",
        "Millen",
        "split branch; email says flow is capped at 1 m3/s",
    ),
    ("6.Q.22", "6.Q.22", "Geleenbeek", "Munstergeleen", "source says measured from 2.5 m3/s"),
    ("10.Q.29", "10.Q.29", "Geul", "Cottessen", ""),
    ("10.Q.30", "10.Q.30", "Geul", "Hommerich", ""),
    ("13.Q.34", "13.Q.34", "Gulp", "Azijnfabriek", ""),
    ("12.Q.31", "12.Q.31", "Selzerbeek", "Partij", "main branch named in email"),
    (
        "6.Q.25",
        "6.Q.25",
        "Vloedgraaf",
        "Nieuwstadt",
        "receives split Geleenbeek and Rode Beek flow",
    ),
    ("15.Q.41", "15.Q.41", "Voer", "Mesch", ""),
    ("18.Q.45", "18.Q.45", "Worm", "Rimburg", ""),
    ("6.Q.27_indicatie", "6.Q.27", "Geleenbeek", "Oud-Roosteren", "source column marked indicatie"),
    ("12.Q.46", "12.Q.46", "Selzerbeek", "molentak", "split branch named in email"),
    (
        "6.Q.27",
        "6.Q.27",
        "Geleenbeek",
        "Oud-Roosteren",
        "second source column with same station ID",
    ),
    ("10.Q.36", "10.Q.36", "Geul", "Meerssen", "provider reports continuing gravel-bar problems"),
]


def read_source() -> pd.DataFrame:
    """Read the value-equivalent CSV and verify its fixed source time grid."""
    keys = [row[0] for row in SERIES]
    station_ids = [row[1] for row in SERIES]
    header = pd.read_csv(
        SOURCE,
        nrows=6,
        header=None,
        dtype=str,
        keep_default_na=False,
        encoding="utf-8-sig",
    )
    if header.iloc[0, 0] != "GMT+1":
        raise ValueError("Unexpected Waterschap source time label")
    if header.iloc[4, 1:].tolist() != station_ids:
        raise ValueError("Waterschap station columns or order changed")
    if set(header.iloc[5, 1:]) != {"MEAN (15 minuten)"}:
        raise ValueError("Unexpected Waterschap aggregation label")

    data = pd.read_csv(
        SOURCE,
        skiprows=6,
        header=None,
        names=["timestamp_source", *keys],
        encoding="utf-8-sig",
        low_memory=False,
    )
    data["timestamp_source"] = pd.to_datetime(
        data["timestamp_source"], format="%d/%m/%Y %H:%M", errors="raise"
    )
    if data.timestamp_source.duplicated().any():
        raise ValueError("Waterschap delivery contains duplicate timestamps")

    # The export includes midnight 2026 as one endpoint. Preserve it in raw
    # data but exclude it from the requested 2010-2025 audit.
    extra = data.loc[data.timestamp_source >= END, "timestamp_source"]
    if extra.tolist() != [END]:
        raise ValueError(f"Unexpected rows outside 2010-2025: {extra.tolist()}")
    data = data.loc[data.timestamp_source.between(START, END, inclusive="left")].copy()

    expected = pd.Series(
        pd.date_range(START, END - pd.Timedelta(minutes=15), freq="15min"),
        name="timestamp_source",
    )
    if not data.timestamp_source.reset_index(drop=True).equals(expected):
        raise ValueError("Waterschap timestamps are not the complete expected 15-minute grid")
    return data.reset_index(drop=True)


def longest_missing_hours(observed: pd.Series) -> float:
    """Return the longest consecutive blank-cell run on the 15-minute grid."""
    missing = ~observed.to_numpy()
    if not missing.any():
        return 0.0
    padded = np.r_[False, missing, False]
    starts = np.flatnonzero(~padded[:-1] & padded[1:])
    ends = np.flatnonzero(padded[:-1] & ~padded[1:])
    return float((ends - starts).max() / 4)


def availability_tables(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build series summaries and one row per series-year."""
    source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    hours = data.timestamp_source.iloc[::4].reset_index(drop=True)
    july = data.timestamp_source.between("2021-07-01", "2021-08-01", inclusive="left")
    summaries = []
    annual_rows = []

    for key, station, watercourse, gauge, note in SERIES:
        raw = data[key]
        values = pd.to_numeric(raw, errors="coerce")
        if (raw.notna() & values.isna()).any():
            raise ValueError(f"Non-numeric nonblank values in {key}")

        observed = values.notna()
        complete_hour = observed.to_numpy().reshape(-1, 4).all(axis=1)
        annual_15m = observed.groupby(data.timestamp_source.dt.year).agg(["sum", "count"])
        annual_hour = pd.Series(complete_hour).groupby(hours.dt.year).agg(["sum", "count"])
        annual_coverage = annual_hour["sum"] / annual_hour["count"]

        for year in annual_15m.index:
            annual_rows.append(
                {
                    "series_key": key,
                    "station_id": station,
                    "watercourse": watercourse,
                    "gauge": gauge,
                    "year": year,
                    "observed_15m_cells": int(annual_15m.loc[year, "sum"]),
                    "expected_15m_cells": int(annual_15m.loc[year, "count"]),
                    "coverage_15m": annual_15m.loc[year, "sum"] / annual_15m.loc[year, "count"],
                    "complete_hours": int(annual_hour.loc[year, "sum"]),
                    "expected_hours": int(annual_hour.loc[year, "count"]),
                    "complete_hour_coverage": annual_coverage.loc[year],
                }
            )

        present = np.flatnonzero(observed.to_numpy())
        july_hours = observed[july].to_numpy().reshape(-1, 4).all(axis=1)
        summaries.append(
            {
                "series_key": key,
                "station_id": station,
                "watercourse": watercourse,
                "gauge": gauge,
                "source_note": note,
                "source_sha256": source_hash,
                "first_observed_source_time": data.loc[present[0], "timestamp_source"],
                "last_observed_source_time": data.loc[present[-1], "timestamp_source"],
                "observed_15m_cells": int(observed.sum()),
                "coverage_15m": observed.mean(),
                "complete_hours": int(complete_hour.sum()),
                "complete_hour_coverage": complete_hour.mean(),
                "minimum_annual_complete_hour_coverage": annual_coverage.min(),
                "years_at_least_70pct": int(annual_coverage.ge(0.70).sum()),
                "years_at_least_80pct": int(annual_coverage.ge(0.80).sum()),
                "years_at_least_90pct": int(annual_coverage.ge(0.90).sum()),
                "july_2021_complete_hours": int(july_hours.sum()),
                "july_2021_expected_hours": len(july_hours),
                "zero_cells": int(values.eq(0).sum()),
                "negative_cells": int(values.lt(0).sum()),
                "longest_missing_run_hours": longest_missing_hours(observed),
                "passes_provisional_80_70_availability": bool(
                    complete_hour.mean() >= 0.80 and annual_coverage.min() >= 0.70
                ),
            }
        )

    return pd.DataFrame(summaries), pd.DataFrame(annual_rows)


def main() -> None:
    summary, annual = availability_tables(read_source())
    QC_PATH.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(QC_PATH, index=False)
    annual.to_csv(ANNUAL_PATH, index=False)
    shown = summary[
        [
            "series_key",
            "watercourse",
            "gauge",
            "complete_hour_coverage",
            "minimum_annual_complete_hour_coverage",
            "july_2021_complete_hours",
            "passes_provisional_80_70_availability",
        ]
    ]
    print(shown.to_string(index=False))
    print(f"\nWrote {len(summary)} series to {QC_PATH}")
    print(f"Wrote {len(annual)} series-years to {ANNUAL_PATH}")


if __name__ == "__main__":
    main()
