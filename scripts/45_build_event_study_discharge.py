"""Build the hourly discharge outcome series for the event study (protocol §3).

The four-quarter-hour rule, the documented-failure mask and the aggregation
are implemented and unit-tested (`tests/test_event_study_discharge.py`). What
is NOT implemented is a silent choice of timezone or zero semantics: Waterschap's
2026-09-07 reply gave the 15-minute mean convention and the blank-cell meaning,
but not whether the source's stated "GMT+1" is a fixed offset or Dutch civil
time, and not what a delivered zero means (`docs/data-requests.md`). The
protocol requires a *verified* timezone conversion (§3); guessing one into the
core file would let a wrong hour label pass every downstream gate silently.

So this script always requires an explicit `--timezone` and `--zero` choice,
and always writes to `results/discharge_ingest_candidates/`, never to the core
gate file `data/interim/event_study_discharge_hourly.csv`. `--commit` writes
the core file too, but only once `data/interim/event_study_gauges.csv` records
`timezone_verified` and `zero_semantics_verified` as true for every cohort
gauge, which they are not yet (D3/D5, `scripts/44_build_event_study_gauges.py`).

Reads only the six cohort series named in `config/event_study_cohort.csv`
from the raw 15-minute delivery already parsed by
`scripts/35_audit_waterschap_delivery.py`, which this script imports rather
than re-parsing.

Example (candidate output only):
    python scripts/45_build_event_study_discharge.py --timezone civil_amsterdam --zero true_zero
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
COHORT = ROOT / "config/event_study_cohort.csv"
GAUGES = ROOT / "data/interim/event_study_gauges.csv"
CANDIDATE_DIR = ROOT / "results/discharge_ingest_candidates"
CORE_OUTPUT = ROOT / "data/interim/event_study_discharge_hourly.csv"

TIMEZONE_ASSUMPTIONS = {
    "fixed_utc_plus_1": "the source's 'GMT+1' label is a fixed offset all year",
    "civil_amsterdam": "the source's 'GMT+1' label is Dutch civil time (CET/CEST, DST-aware)",
}
ZERO_ASSUMPTIONS = {
    "true_zero": "a delivered 0.0 means zero discharge",
    "missing_sentinel": "a delivered 0.0 means no reliable reading, like a blank cell",
}

# Dated intervals to mask regardless of timezone/zero assumption, keyed by
# gauge code. None of the six cohort gauges have a documented outright failure
# in July 2021 (`data/processed/waterschap_station_source_qa.csv`); Cottessen
# and Rimburg exceeded their rating domain, which `rating_domain_admissible()`
# handles downstream from the era table, not here.
FAILURE_INTERVALS: dict[str, list[tuple[str, str]]] = {}


def load_audit_module():
    """Import script 35's raw-delivery reader instead of re-parsing the source."""
    spec = importlib.util.spec_from_file_location(
        "waterschap_audit", ROOT / "scripts" / "35_audit_waterschap_delivery.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def convert_timestamps(local_naive, assumption):
    """Source timestamps (naive, 'GMT+1' per the delivery header) to UTC.

    `local_naive` is a Series of naive datetime64 values (not a DatetimeIndex),
    so the tz operations go through the `.dt` accessor.
    """
    if assumption == "fixed_utc_plus_1":
        return local_naive.dt.tz_localize("Etc/GMT-1").dt.tz_convert("UTC")
    if assumption == "civil_amsterdam":
        return local_naive.dt.tz_localize(
            "Europe/Amsterdam", ambiguous="NaT", nonexistent="NaT"
        ).dt.tz_convert("UTC")
    raise ValueError(f"unknown timezone assumption: {assumption}")


def apply_zero_assumption(values, assumption):
    """A delivered 0.0, under one candidate reading of what zero means."""
    if assumption == "true_zero":
        return values
    if assumption == "missing_sentinel":
        return values.mask(values.eq(0.0))
    raise ValueError(f"unknown zero assumption: {assumption}")


def mask_failure_intervals(values, gauge):
    """Blank out dated intervals documented as an outright instrument failure."""
    for start, end in FAILURE_INTERVALS.get(gauge, []):
        values = values.mask(values.index.to_series().between(start, end))
    return values


def four_quarter_hour_mean(quarter_hourly, utc_index):
    """Protocol §3: an hour is populated only when all four quarters are present.

    `quarter_hourly` is a Series on the original 15-minute grid, already under
    one zero assumption; `utc_index` gives each row's converted UTC timestamp.
    A quarter that fell on a DST-ambiguous or nonexistent civil-time instant is
    NaT and its hour is dropped, not silently reassigned.
    """
    frame = pd.DataFrame({"value": quarter_hourly.to_numpy(), "utc": utc_index})
    frame = frame.dropna(subset=["utc"])
    frame["hour"] = frame.utc.dt.floor("h")
    grouped = frame.groupby("hour")
    complete = grouped.value.count().eq(4)
    mean = grouped.value.mean()
    return mean.where(complete)


def build_series(gauge, station, data, series_spec, timezone_assumption, zero_assumption):
    """One gauge's candidate hourly series under one pair of assumptions."""
    key = next(row[0] for row in series_spec if row[3] == station)
    values = pd.to_numeric(data[key], errors="coerce")
    values = apply_zero_assumption(values, zero_assumption)
    values.index = data.timestamp_source
    values = mask_failure_intervals(values, gauge)
    utc_index = convert_timestamps(pd.Series(values.index), timezone_assumption)
    return four_quarter_hour_mean(values, utc_index)


def build_candidate(timezone_assumption, zero_assumption):
    """The six-gauge wide table for one pair of assumptions."""
    cohort = pd.read_csv(COHORT)
    audit = load_audit_module()
    data = audit.read_source()  # read the 15-minute delivery once for all six gauges
    columns = {}
    for row in cohort.itertuples():
        columns[row.gauge] = build_series(
            row.gauge, row.station, data, audit.SERIES, timezone_assumption, zero_assumption
        )
    frame = pd.DataFrame(columns)
    frame.index.name = "timestamp_utc"
    return frame.sort_index()


def gauges_fully_verified():
    if not GAUGES.exists():
        return False, "data/interim/event_study_gauges.csv does not exist yet"
    gauges = pd.read_csv(GAUGES)
    verified = gauges.timezone_verified.all() and gauges.zero_semantics_verified.all()
    if not verified:
        return False, (
            "timezone_verified and zero_semantics_verified are not both true for every "
            "cohort gauge; see docs/data-requests.md"
        )
    return True, "verified"


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--timezone", choices=TIMEZONE_ASSUMPTIONS, required=True)
    parser.add_argument("--zero", choices=ZERO_ASSUMPTIONS, required=True)
    parser.add_argument(
        "--commit",
        action="store_true",
        help="also write the core gate file; refused until Waterschap's semantics are verified",
    )
    args = parser.parse_args()

    frame = build_candidate(args.timezone, args.zero)
    CANDIDATE_DIR.mkdir(parents=True, exist_ok=True)
    candidate_path = CANDIDATE_DIR / f"discharge_hourly_{args.timezone}_{args.zero}.csv"
    frame.to_csv(candidate_path)
    print(f"Wrote candidate series to {candidate_path}")
    print(frame.describe().T[["count", "mean", "min", "max"]].to_string())

    if args.commit:
        ok, reason = gauges_fully_verified()
        if not ok:
            sys.exit(f"Refusing --commit: {reason}")
        CORE_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(CORE_OUTPUT)
        print(f"Committed to the core gate file {CORE_OUTPUT}")


if __name__ == "__main__":
    main()
