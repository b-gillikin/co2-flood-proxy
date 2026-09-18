"""Build the rating-era table for the event study from the transcribed rating curves.

Decision D8 (2026-09-18) groups rating versions into eras: an era boundary
falls only where the relation changes for high flows, and a short version that
changes it is excluded rather than given its own p99. The grouping is an author
decision written in `config/rating_curves/event_study_eras.csv`; versions it
does not list are excluded, so their hours carry no era and are inadmissible.

For every era the script derives, from `waterschap_rating_versions.csv` and
`waterschap_structure_periods.csv`:

- the validity intervals, one row each (an era may have holes);
- the rating domain in m3/s: the range every version in the era defines,
  intersected with the stated discharge measuring range;
- `relation_uniform_above_m3s`: the discharge above which every version in
  the era agrees with the reference version to within 1% (0 for a single
  version, inf when they disagree at the top). Merging versions is valid only
  when the era's p99 lies at or above it, which the gate audit checks
  (`scripts/31_event_study_gates.py`).

It also writes the literal reading (every version its own era) for the
sensitivity analysis. Dates in the sheets are calendar dates, read as local
midnight in Europe/Amsterdam. It reads no discharge, rainfall or weather value.

Example: python scripts/43_build_rating_eras.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "config/rating_curves"
PRIMARY = ROOT / "data/interim/event_study_rating_eras.csv"
LITERAL = ROOT / "data/interim/event_study_rating_eras_literal.csv"
PERIOD_START = pd.Timestamp("2010-01-01")
AGREEMENT = 0.01
GRID = 4000


def discharge(version, stage):
    """Discharge from one version's segments; NaN outside them."""
    stage = np.asarray(stage, dtype=float)
    values = np.full(stage.shape, np.nan)
    segments = version.dropna(subset=["formula"])
    segments = segments[~segments.segment.astype(str).str.endswith("B")]
    for segment in segments.sort_values("stage_low_m").itertuples():
        inside = (stage >= segment.stage_low_m) & (stage <= segment.stage_high_m)
        values[inside] = eval(segment.formula, {"__builtins__": {}}, {"H": stage[inside]})  # noqa: S307
    return values


def local_midnight(date):
    """A sheet date as local midnight, written in UTC."""
    stamp = pd.Timestamp(date).tz_localize("Europe/Amsterdam")
    return stamp.tz_convert("UTC").strftime("%Y-%m-%dT%H:%MZ")


def intervals(versions):
    """[start, end) of every version, from its written end or the next start."""
    starts = versions.drop_duplicates(["gauge", "version_start"]).sort_values(
        ["gauge", "version_start"]
    )
    rows = []
    for _, group in starts.groupby("gauge"):
        following = list(group.version_start.iloc[1:]) + [pd.NaT]
        for row, next_start in zip(group.itertuples(), following, strict=True):
            if isinstance(row.version_end_as_written, str) and row.version_end_as_written:
                end = pd.Timestamp(row.version_end_as_written) + pd.Timedelta(days=1)
                if pd.notna(next_start):
                    end = min(end, next_start)
            else:
                end = next_start
            rows.append({"gauge": row.gauge, "version_start": row.version_start, "end": end})
    return pd.DataFrame(rows)


def stated_range(structures, gauge, start, end):
    """Stated discharge range over [start, end): intersection of the periods in force."""
    table = structures[structures.gauge.eq(gauge)].sort_values("period_start")
    ends = pd.to_datetime(table.period_end_as_written).fillna(pd.Timestamp.max)
    upper = end if pd.notna(end) else pd.Timestamp.max
    in_force = table[(table.period_start < upper) & (ends >= start)]
    if in_force.empty:
        in_force = table[table.period_start <= start].tail(1)
    return (
        float(in_force.discharge_range_min_m3s.max()),
        float(in_force.discharge_range_max_m3s.min()),
    )


def uniform_above(reference, others):
    """Lowest reference discharge above which every other version agrees within 1%.

    `others` pairs each version with its stage shift relative to the reference
    datum. Stages are compared on the range every version defines.
    """
    if not others:
        return 0.0
    low = max([reference.stage_low_m.min()] + [v.stage_low_m.min() - s for v, s in others])
    high = min([reference.stage_high_m.max()] + [v.stage_high_m.max() - s for v, s in others])
    stage = np.linspace(low, high, GRID)
    q_reference = discharge(reference, stage)
    disagree = np.zeros(GRID, dtype=bool)
    for version, shift in others:
        q_other = discharge(version, stage + shift)
        disagree |= ~(np.abs(q_other / q_reference - 1) <= AGREEMENT)
    if disagree[-1]:
        return np.inf
    if not disagree.any():
        return float(np.nanmin(q_reference))
    return float(q_reference[np.flatnonzero(disagree).max() + 1])


def relation_range(version):
    """Discharge at the lowest and highest stage the version defines."""
    segments = version.dropna(subset=["formula"])
    segments = segments[~segments.segment.astype(str).str.endswith("B")]
    return (
        float(discharge(version, [segments.stage_low_m.min()])[0]),
        float(discharge(version, [segments.stage_high_m.max()])[0]),
    )


def build(spec, versions, structures, spans):
    rows = []
    for (gauge, era_id), members in spec.groupby(["gauge", "era_id"], sort=False):
        members = members.sort_values("version_start")
        chosen = [
            (versions[versions.gauge.eq(gauge) & versions.version_start.eq(start)], shift)
            for start, shift in zip(members.version_start, members.stage_shift_m, strict=True)
        ]
        if any(version.empty for version, _ in chosen):
            raise ValueError(f"{era_id}: a listed version is not in the transcription")
        reference, reference_shift = chosen[0]
        others = [(version, shift - reference_shift) for version, shift in chosen[1:]]
        lows, highs = zip(*(relation_range(version) for version, _ in chosen), strict=True)
        spans_here = spans[spans.gauge.eq(gauge) & spans.version_start.isin(members.version_start)]
        stated = [
            stated_range(structures, gauge, row.version_start, row.end)
            for row in spans_here.itertuples()
        ]
        domain_min = max(max(lows), max(low for low, _ in stated))
        domain_max = min(min(highs), min(high for _, high in stated))
        agree = uniform_above(reference, others)
        source = f"afvoerrelatie {gauge.replace('.', '')} (Waterschap Limburg, 2026-09-07)"
        for row in spans_here.sort_values("version_start").itertuples():
            rows.append(
                {
                    "gauge": gauge,
                    "era_id": era_id,
                    "valid_from_utc": local_midnight(row.version_start),
                    "valid_to_utc": local_midnight(row.end) if pd.notna(row.end) else None,
                    "rating_version": row.version_start.date().isoformat(),
                    "domain_min_m3s": round(domain_min, 4),
                    "domain_max_m3s": round(domain_max, 3),
                    "relation_uniform_above_m3s": round(agree, 4),
                    "source_document": source,
                }
            )
    return pd.DataFrame(rows)


def build_tables():
    """The primary (D8) and literal era tables from the committed config."""
    versions = pd.read_csv(FOLDER / "waterschap_rating_versions.csv", dtype={"segment": str})
    structures = pd.read_csv(FOLDER / "waterschap_structure_periods.csv")
    spec = pd.read_csv(FOLDER / "event_study_eras.csv")
    for frame, column in [(versions, "version_start"), (spec, "version_start")]:
        frame[column] = pd.to_datetime(frame[column])
    structures["period_start"] = pd.to_datetime(structures.period_start)
    spans = intervals(versions)

    primary = build(spec, versions, structures, spans)
    in_period = spans[
        spans.gauge.isin(spec.gauge)
        & (spans.end.isna() | (spans.end > PERIOD_START))
        & spans.version_start.isin(versions.dropna(subset=["formula"]).version_start)
    ]
    literal_spec = in_period.assign(
        era_id=lambda f: f.gauge + "-" + f.version_start.dt.strftime("%Y%m%d"),
        stage_shift_m=0.0,
    )
    literal = build(literal_spec, versions, structures, spans)
    return primary, literal


def main():
    primary, literal = build_tables()
    PRIMARY.parent.mkdir(parents=True, exist_ok=True)
    primary.to_csv(PRIMARY, index=False)
    literal.to_csv(LITERAL, index=False)
    print(primary.to_string(index=False))
    print(
        f"\nliteral sensitivity: {literal.era_id.nunique()} eras for {literal.gauge.nunique()} gauges"
    )


if __name__ == "__main__":
    main()
