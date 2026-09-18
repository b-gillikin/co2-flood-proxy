"""Check the transcribed Waterschap rating curves against their own arithmetic.

The 14 rating-curve PDFs of the 2026-09-07 delivery were transcribed by hand
into `config/rating_curves/` (versions in force at any time in 2010-2025, and
the structure periods). A transcription error in a coefficient or an exponent
shows up as one of these:

- a jump in discharge where two segments of one version meet;
- discharge that does not rise with stage inside a segment;
- a top-of-relation discharge far from the station's stated measuring range.

Those arithmetic checks also flag properties of the sheets themselves, so the
decisive check is textual: every transcribed formula must appear verbatim in
its station's PDF text, the stage bounds printed on its line must match, and
the normalised formula must contain exactly the numbers of the verbatim one.

The script also lists gaps and overlaps between versions over 2010-2025. It
reads no discharge, rainfall or weather value.

Example: python scripts/42_check_rating_transcription.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "config/rating_curves"
PDFS = ROOT / "data/raw/external_deliveries/waterschap_limburg/2026-09-07/rating_curves"
NUMBER = re.compile(r"\d+(?:[.,]\d+)?(?:E-?\d+)?")
# Segments checked by eye against the PDF because the automatic match cannot work.
KNOWN_EXCEPTIONS = {
    ("10.Q.30", "2016-06-05", "1"): "segment printed on the line above the version dates",
    ("10.Q.30", "2016-08-05", "1"): "start printed as 5-6-2016, read as 2016-08-05 (see note)",
    ("12.Q.46", "1994-09-30", "1"): "zero-flow segment written as a bare 0",
    ("13.Q.34", "2012-10-15", "1"): "quadratic formula wraps onto a second line in the PDF",
}
DATE = re.compile(r"\b(\d{1,2})-(\d{1,2})-(\d{4}|\d{2})\b")
REPORT = ROOT / "results/rating"
PERIOD = (pd.Timestamp("2010-01-01"), pd.Timestamp("2025-12-31"))


def discharge(formula, stage):
    """Evaluate one transcribed relation Q = f(H) (our own table, not user input)."""
    return float(eval(formula, {"__builtins__": {}}, {"H": stage}))  # noqa: S307


def numbers(text):
    """Numbers in a formula, treating the decimal comma as a point."""
    return [float(value.replace(",", ".")) for value in NUMBER.findall(text)]


def dates(line):
    """Dates written d-m-yyyy or d-m-yy on a table line."""
    found = []
    for day, month, year in DATE.findall(line):
        year = int(year) + (2000 if len(year) == 2 else 0)
        found.append(pd.Timestamp(year=year, month=int(month), day=int(day)))
    return found


def pdf_text(gauge):
    import pypdf

    code = gauge.replace(".", "")
    path = next(PDFS.glob(f"afvoerrelatie {code} *.pdf"))
    reader = pypdf.PdfReader(path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def verbatim_checks(versions):
    """Each formula appears in its PDF, with matching bounds and numbers."""
    rows = []
    texts = {gauge: pdf_text(gauge) for gauge in versions.gauge.unique()}
    for row in versions.dropna(subset=["formula"]).itertuples():
        text = texts[row.gauge]
        lines = [line for line in text.splitlines() if row.formula_as_written in line]
        same_numbers = numbers(str(row.formula_as_written)) == numbers(
            str(row.formula).replace("**", "^")
        )
        written = [pd.Timestamp(row.version_start)]
        if isinstance(row.version_end_as_written, str) and row.version_end_as_written:
            written.append(pd.Timestamp(row.version_end_as_written))
        first_segment = str(row.segment) in {"1", "1B"}
        dates_found = not first_segment or any(
            dates(line)[: len(written)] == written for line in lines
        )
        bounds_found = False
        for line in lines:
            before = numbers(line.split(row.formula_as_written)[0])
            if len(before) >= 2 and np.allclose(
                before[-2:], [row.stage_low_m, row.stage_high_m], atol=5e-4
            ):
                bounds_found = True
        rows.append(
            {
                "gauge": row.gauge,
                "version_start": row.version_start,
                "segment": row.segment,
                "formula_in_pdf": bool(lines),
                "bounds_on_line": bounds_found,
                "numbers_match": same_numbers,
                "dates_on_line": dates_found,
            }
        )
    return pd.DataFrame(rows)


def version_checks(versions, structures):
    rows = []
    for (gauge, start), version in versions.groupby(["gauge", "version_start"], sort=True):
        segments = version.dropna(subset=["formula"]).sort_values("stage_low_m")
        if segments.empty:
            rows.append(
                {"gauge": gauge, "version_start": start, "check": "no relation", "ok": True}
            )
            continue
        for alternative, group in segments.groupby(segments.segment.astype(str).str.endswith("B")):
            label = "alternative B" if alternative else "main"
            group = group.sort_values("stage_low_m")
            for segment in group.itertuples():
                stages = np.linspace(segment.stage_low_m, segment.stage_high_m, 50)
                values = np.array([discharge(segment.formula, h) for h in stages])
                rows.append(
                    {
                        "gauge": gauge,
                        "version_start": start,
                        "relation": label,
                        "check": f"segment {segment.segment} rises with stage",
                        "value": float(np.min(np.diff(values))),
                        "ok": bool(np.all(np.diff(values) >= -1e-9)),
                    }
                )
            for left, right in zip(
                group.iloc[:-1].itertuples(), group.iloc[1:].itertuples(), strict=True
            ):
                boundary = right.stage_low_m
                q_left = discharge(left.formula, boundary)
                q_right = discharge(right.formula, boundary)
                jump = abs(q_right - q_left) / max(abs(q_right), 1e-6)
                rows.append(
                    {
                        "gauge": gauge,
                        "version_start": start,
                        "relation": label,
                        "check": f"continuity at {boundary:.3f} m ({left.segment}|{right.segment})",
                        "value": round(jump, 4),
                        "ok": jump <= 0.03,
                    }
                )
            top = group.iloc[-1]
            q_top = discharge(top.formula, top.stage_high_m)
            in_force = max(start, PERIOD[0])
            period = structures.loc[
                structures.gauge.eq(gauge) & structures.period_start.le(in_force)
            ].sort_values("period_start")
            stated = float(period.discharge_range_max_m3s.iloc[-1]) if len(period) else np.nan
            rows.append(
                {
                    "gauge": gauge,
                    "version_start": start,
                    "relation": label,
                    "check": f"top of relation {q_top:.2f} m3/s vs stated range max {stated:g}",
                    "value": round(q_top / stated - 1, 3) if stated else np.nan,
                    "ok": bool(abs(q_top / stated - 1) <= 0.15) if stated else False,
                }
            )
    return pd.DataFrame(rows)


def coverage(versions):
    """Gaps and overlaps between consecutive versions of each gauge over 2010-2025."""
    rows = []
    starts = versions.drop_duplicates(["gauge", "version_start"]).sort_values(
        ["gauge", "version_start"]
    )
    for gauge, group in starts.groupby("gauge"):
        group = group[group.version_start.le(PERIOD[1])]
        in_period = group[group.version_start.ge(PERIOD[0])]
        before = group[group.version_start.lt(PERIOD[0])].tail(1)
        group = pd.concat([before, in_period])
        for current, following in zip(
            group.iloc[:-1].itertuples(), group.iloc[1:].itertuples(), strict=True
        ):
            if pd.isna(current.version_end_as_written):
                continue
            end = pd.Timestamp(current.version_end_as_written)
            gap_days = (following.version_start - end).days
            if gap_days > 1:
                kind = f"gap of {gap_days - 1} days"
            elif gap_days < 0:
                kind = f"overlap of {-gap_days} days"
            else:
                kind = "contiguous" if gap_days == 1 else "shared boundary day"
            rows.append(
                {
                    "gauge": gauge,
                    "from_version": current.version_start.date(),
                    "to_version": following.version_start.date(),
                    "written_end": end.date(),
                    "transition": kind,
                }
            )
    return pd.DataFrame(rows)


def main():
    versions = pd.read_csv(FOLDER / "waterschap_rating_versions.csv", dtype={"segment": str})
    structures = pd.read_csv(FOLDER / "waterschap_structure_periods.csv")
    versions["version_start"] = pd.to_datetime(versions.version_start)
    structures["period_start"] = pd.to_datetime(structures.period_start)
    checks = version_checks(versions, structures)
    transitions = coverage(versions)
    verbatim = verbatim_checks(versions)
    flags = ["formula_in_pdf", "bounds_on_line", "numbers_match", "dates_on_line"]
    REPORT.mkdir(parents=True, exist_ok=True)
    verbatim.to_csv(REPORT / "verbatim_checks.csv", index=False)
    keys = list(
        zip(
            verbatim.gauge,
            verbatim.version_start.dt.strftime("%Y-%m-%d"),
            verbatim.segment.astype(str),
            strict=True,
        )
    )
    verbatim["known_exception"] = [KNOWN_EXCEPTIONS.get(key, "") for key in keys]
    verbatim.to_csv(REPORT / "verbatim_checks.csv", index=False)
    mismatched = ~verbatim[flags].all(axis=1)
    unexplained = verbatim[mismatched & verbatim.known_exception.eq("")]
    print(
        f"{len(verbatim)} transcribed segments; {int(mismatched.sum())} not matched "
        f"automatically, all checked by eye except {len(unexplained)}"
    )
    if len(unexplained):
        print(unexplained.to_string(index=False))
    checks.to_csv(REPORT / "transcription_checks.csv", index=False)
    transitions.to_csv(REPORT / "version_transitions.csv", index=False)
    failed = checks[~checks.ok.astype(bool)]
    print(f"{len(checks)} checks, {len(failed)} flagged")
    if len(failed):
        print(failed.to_string(index=False))
    print(
        transitions[transitions.transition.str.startswith(("gap", "overlap"))].to_string(
            index=False
        )
    )


if __name__ == "__main__":
    sys.exit(main())
