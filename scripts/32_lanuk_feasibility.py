"""Audit whether the held LANUK gauges can support the prospective chapter.

This is a data-feasibility analysis, not an outcome analysis. It never joins
rainfall, weather or CO2 and never calculates a signal contrast.
"""

from __future__ import annotations

import io
import re
import sys
import zipfile
from pathlib import Path
from urllib.request import urlopen

import numpy as np
import pandas as pd
from pyproj import Transformer

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.event_study import episode_onsets, episode_table

SERIES_PATH = Path("data/interim/lanuk_discharge_hourly.csv")
INVENTORY_PATH = Path("data/interim/lanuk_stations.csv")
LATER_IOT_PATH = Path("data/interim/iot_hourly.csv")
RAW_DIR = Path("data/raw/discharge/lanuk")
RESULTS_DIR = Path("results/feasibility")
REPORT_PATH = Path("docs/lanuk-feasibility.md")

HYDRO_URL = (
    "https://www.opengeodata.nrw.de/produkte/umwelt_klima/wasser/"
    "oberflaechengewaesser/hydro/Hydrologische-Stationen-NRW_EPSG25832_CSV.zip"
)
HYGON_URL = (
    "https://www.opengeodata.nrw.de/produkte/umwelt_klima/wasser/"
    "oberflaechengewaesser/hygon/OpenHygon_meta.zip"
)

# Complete calendar windows containing July 2021. The 20-year window describes
# the RADOLAN era; the four 10-year windows show whether feasibility depends on
# choosing one convenient decade.
WINDOWS = {
    "2005-2024": ("2005-01-01", "2024-12-31 23:00"),
    "2012-2021": ("2012-01-01", "2021-12-31 23:00"),
    "2013-2022": ("2013-01-01", "2022-12-31 23:00"),
    "2014-2023": ("2014-01-01", "2023-12-31 23:00"),
    "2015-2024": ("2015-01-01", "2024-12-31 23:00"),
}
MIN_OVERALL_COVERAGE = 0.80
MIN_ANNUAL_COVERAGE = 0.70
MIN_EPISODES = 20
MAX_WATERCOURSE_MATCH_METRES = 100

UMLAUTS = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"})


def slugify(value):
    """Match station labels used by the existing LANUK ingest."""
    value = str(value).lower().translate(UMLAUTS)
    return re.sub(r"[^a-z0-9]+", "_", value).strip("_")


def download(url):
    """Cache one small official metadata archive beside the source series."""
    path = RAW_DIR / url.rsplit("/", 1)[-1]
    if path.exists():
        return path
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    with urlopen(url, timeout=120) as response:
        path.write_bytes(response.read())
    return path


def station_metadata():
    """Join verified-discharge stations to HYGON watercourse metadata."""
    hydro_path = download(HYDRO_URL)
    hygon_path = download(HYGON_URL)

    with zipfile.ZipFile(hydro_path) as archive:
        hydro = pd.read_csv(
            io.BytesIO(archive.read("Hydrologische-Stationen-NRW_EPSG25832.csv")),
            sep=";",
            encoding="cp1252",
            dtype={"station_id": "string"},
        ).dropna(subset=["station_name"])
    with zipfile.ZipFile(hygon_path) as archive:
        hygon = pd.read_csv(
            io.BytesIO(archive.read("OpenHygon_Pegel_EPSG25832_ASCII.txt")),
            sep=";",
            encoding="cp1252",
        ).dropna(subset=["Name", "east", "north"])

    hydro["gauge"] = hydro.station_name.map(slugify)
    hydro = hydro.rename(
        columns={
            "station_id": "source_station_id",
            "KOORDX": "easting_epsg25832",
            "KOORDYY": "northing_epsg25832",
            "Name": "source_basin",
            "Zweck": "station_purpose",
            "Betreiber": "operator",
        }
    )
    coordinates = hydro[["easting_epsg25832", "northing_epsg25832"]].apply(
        pd.to_numeric, errors="coerce"
    )
    hydro[["easting_epsg25832", "northing_epsg25832"]] = coordinates

    hygon[["east", "north"]] = hygon[["east", "north"]].apply(pd.to_numeric, errors="coerce")
    watercourses = []
    for station in hydro.itertuples():
        distance = np.hypot(
            hygon.east - station.easting_epsg25832,
            hygon.north - station.northing_epsg25832,
        )
        nearest = distance.idxmin()
        metres = float(distance.loc[nearest])
        verified = metres <= MAX_WATERCOURSE_MATCH_METRES
        watercourses.append(
            {
                "gauge": station.gauge,
                "watercourse": hygon.loc[nearest, "Gewaesser"] if verified else pd.NA,
                "watercourse_match_station": hygon.loc[nearest, "Name"],
                "watercourse_match_distance_m": metres,
                "watercourse_verified": verified,
            }
        )
    hydro = hydro.merge(pd.DataFrame(watercourses), on="gauge", how="left")

    transformer = Transformer.from_crs(25832, 4326, always_xy=True)
    longitude, latitude = transformer.transform(
        hydro.easting_epsg25832.to_numpy(), hydro.northing_epsg25832.to_numpy()
    )
    hydro["latitude"] = latitude
    hydro["longitude"] = longitude
    return hydro[
        [
            "gauge",
            "source_station_id",
            "station_name",
            "watercourse",
            "watercourse_verified",
            "watercourse_match_station",
            "watercourse_match_distance_m",
            "source_basin",
            "station_purpose",
            "operator",
            "easting_epsg25832",
            "northing_epsg25832",
            "latitude",
            "longitude",
        ]
    ]


def longest_missing_run(series):
    """Longest consecutive run of missing hourly cells."""
    missing = series.isna()
    if not missing.any():
        return 0
    groups = missing.ne(missing.shift(fill_value=False)).cumsum()
    return int(missing.groupby(groups).sum().max())


def window_audit(discharge, metadata):
    """One tidy row per gauge and predeclared diagnostic window."""
    rows = []
    for label, (start, end) in WINDOWS.items():
        window = discharge.loc[start:end]
        annual = window.notna().groupby(window.index.year).mean()
        for gauge in window:
            series = window[gauge]
            threshold = series.quantile(0.99)
            episodes = episode_table(series, threshold, merge_hours=72)
            overall_coverage = series.notna().mean()
            minimum_annual_coverage = annual[gauge].min()
            rows.append(
                {
                    "window": label,
                    "window_start_utc": window.index.min(),
                    "window_end_utc": window.index.max(),
                    "gauge": gauge,
                    "expected_hours": len(window),
                    "observed_hours": int(series.notna().sum()),
                    "overall_coverage": overall_coverage,
                    "minimum_annual_coverage": minimum_annual_coverage,
                    "longest_missing_run_hours": longest_missing_run(series),
                    "p99_m3s": threshold,
                    "p99_episodes": len(episodes),
                    "maximum_episode_crossings": (
                        int(episodes.n_crossings.max()) if len(episodes) else 0
                    ),
                    "maximum_episode_chain_hours": (
                        float(episodes.chain_span_hours.max()) if len(episodes) else 0.0
                    ),
                    "passes_draft_density": bool(
                        overall_coverage >= MIN_OVERALL_COVERAGE
                        and minimum_annual_coverage >= MIN_ANNUAL_COVERAGE
                    ),
                    "passes_episode_count": len(episodes) >= MIN_EPISODES,
                }
            )
    audit = pd.DataFrame(rows).merge(metadata, on="gauge", how="left")
    audit["passes_data_metrics"] = audit.passes_draft_density & audit.passes_episode_count
    audit["eligible_verified_watercourse"] = (
        audit.passes_data_metrics & audit.watercourse_verified.fillna(False)
    )
    return audit


def july_status(discharge, metadata):
    """Describe held observations around the censored anchor without imputing it."""
    start = pd.Timestamp("2021-07-10", tz="UTC")
    end = pd.Timestamp("2021-07-25", tz="UTC")
    anchor = pd.Timestamp("2021-07-15", tz="UTC")
    rows = []
    for gauge in discharge:
        series = discharge[gauge].dropna()
        before = series.loc[series.index < anchor]
        after = series.loc[series.index >= anchor]
        rows.append(
            {
                "gauge": gauge,
                "july_window_observed_hours": int(series.loc[start:end].count()),
                "last_observation_before_anchor": before.index.max() if len(before) else pd.NaT,
                "first_observation_after_anchor": after.index.min() if len(after) else pd.NaT,
            }
        )
    return pd.DataFrame(rows).merge(
        metadata[["gauge", "watercourse", "watercourse_verified"]], on="gauge", how="left"
    )


def later_iot_overlap(discharge, metadata):
    """Count discharge onsets whose full 72-hour window has later IoT data."""
    iot = pd.read_csv(LATER_IOT_PATH, parse_dates=["timestamp_utc"]).set_index("timestamp_utc")
    required = ["iot_co2_ppm", "iot_air_pressure_hpa"]
    iot = iot[required]
    rows = []
    for gauge in discharge:
        series = discharge[gauge]
        onsets = episode_onsets(series, series.quantile(0.99), merge_hours=72)
        overlapping = onsets[(onsets >= iot.index.min()) & (onsets <= iot.index.max())]
        complete = 0
        for onset in overlapping:
            window = pd.date_range(
                onset - pd.Timedelta(hours=72),
                onset - pd.Timedelta(hours=1),
                freq="h",
            )
            complete += int(iot.reindex(window).notna().all().all())
        rows.append(
            {
                "gauge": gauge,
                "p99_onsets_in_later_iot_span": len(overlapping),
                "complete_72h_iot_windows": complete,
            }
        )
    return pd.DataFrame(rows).merge(
        metadata[["gauge", "watercourse", "watercourse_verified"]], on="gauge", how="left"
    )


def window_summary(audit):
    """Summarise the strict diagnostic without mistaking gauges for rivers."""
    eligible = audit[audit.passes_data_metrics]
    verified = audit[audit.eligible_verified_watercourse]
    rows = []
    for label in WINDOWS:
        rows.append(
            {
                "window": label,
                "gauges_passing_data_metrics": int(eligible.window.eq(label).sum()),
                "verified_watercourses_represented": int(
                    verified.loc[verified.window.eq(label), "watercourse"].nunique()
                ),
                "all_gauges_with_80pct_overall": int(
                    audit.loc[
                        audit.window.eq(label) & audit.overall_coverage.ge(0.80), "gauge"
                    ].nunique()
                ),
            }
        )
    return pd.DataFrame(rows)


def markdown_table(frame):
    """Render a small frame without adding a report dependency."""
    columns = list(frame)
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in frame.itertuples(index=False, name=None):
        values = [str(value).replace("|", "\\|") for value in row]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def write_report(metadata, audit, summary, july, later):
    """Write a concise, tracked feasibility decision note."""
    mapped = metadata[metadata.watercourse_verified.fillna(False)]
    wurm = metadata[metadata.watercourse.astype("string").str.casefold().eq("wurm")]
    best = summary.sort_values(
        ["verified_watercourses_represented", "gauges_passing_data_metrics"],
        ascending=False,
    ).iloc[0]
    best_windows = summary.loc[
        summary.verified_watercourses_represented.eq(best.verified_watercourses_represented)
        & summary.gauges_passing_data_metrics.eq(best.gauges_passing_data_metrics),
        "window",
    ].str.cat(sep=" and ")
    table = markdown_table(summary)
    wurm_display = wurm[
        ["gauge", "station_name", "watercourse", "watercourse_match_distance_m"]
    ].copy()
    wurm_display["watercourse_match_distance_m"] = wurm_display[
        "watercourse_match_distance_m"
    ].round(1)
    wurm_table = markdown_table(wurm_display)
    critical = july[july.gauge.isin(["herzogenrath_1", "herzogenrath_2", "honsdorf", "randerath"])]
    critical = critical.copy()
    for column in ["last_observation_before_anchor", "first_observation_after_anchor"]:
        critical[column] = critical[column].astype("string").fillna("none held")
    july_table = markdown_table(critical)
    later_critical = later[
        later.gauge.isin(["herzogenrath_1", "herzogenrath_2", "honsdorf", "randerath"])
    ]
    later_table = markdown_table(later_critical)
    archive_description = (
        f"The held archive contains {len(metadata)} named gauges. Official station and HYGON "
        f"metadata support a <= {MAX_WATERCOURSE_MATCH_METRES} m watercourse match for "
        f"{len(mapped)} gauges representing {mapped.watercourse.nunique()} named watercourses. "
        "Natural/managed status and the meaning of omitted verified-discharge timestamps "
        "remain unverified."
    )
    gate_result = (
        f"Under the draft density rule (>={MIN_OVERALL_COVERAGE:.0%} overall and "
        f">={MIN_ANNUAL_COVERAGE:.0%} in every calendar year) plus >={MIN_EPISODES} p99 "
        f"episodes, the strongest tested windows are **{best_windows}**, each with "
        f"**{best.gauges_passing_data_metrics} gauges across "
        f"{best.verified_watercourses_represented} verified watercourses**. It does not meet "
        "the ten-watercourse gate. This is a feasibility failure, not a chapter null result "
        "and not permission to lower the rule."
    )
    text = f"""# LANUK feasibility audit

Status: **source reconnaissance only; the German cohort does not currently pass**
(generated by `scripts/32_lanuk_feasibility.py`). No weather, rainfall, CO2 or
signal contrast is used here.

## Decision

{archive_description}

{gate_result}

## Window diagnostics

{table}

`gauges_passing_data_metrics` requires both density and episode count.
`verified_watercourses_represented` then deduplicates those gauges by the
officially matched watercourse. No natural-tributary claim is made.

## Wurm correction

An earlier review treated `herzogenrath_2` and `honsdorf` as Wurm gauges.
The official HYGON metadata instead assigns them to **Broicher Bach** and
**Beeckflies**. The matched Wurm gauges are:

{wurm_table}

The July table below documents archive gaps only. A last observation before the
event and a much later first observation do not, without damage or hydraulic
evidence, bound high-water onset.

{july_table}

The same correction matters for the later recurrence case. Using each held
series' p99 and requiring complete CO2 and pressure from -72 to -1 hours gives:

{later_table}

Neither held Wurm gauge overlaps the later IoT era. Counts on Broicher Bach or
Beeckflies cannot be relabelled as Wurm/Kerkrade recurrence evidence.

## Timestamp semantics

The verified-discharge CSVs contain irregular timestamps, including non-quarter
hours. The official HYGON data-model note describes regular quarter-hour raw
water-level observations but does not define the omission or hold-forward rule
for these verified discharge archives. Therefore the audit conservatively counts
an hour as observed only when the published file contains a value in that hour.
LANUK clarification is required before interpreting the density failure as
physical gauge downtime or carrying observations forward.

## Reproducible artifacts

- `results/feasibility/lanuk_gauge_metadata.csv`
- `results/feasibility/lanuk_gauge_windows.csv`
- `results/feasibility/lanuk_window_summary.csv`
- `results/feasibility/lanuk_july_2021_status.csv`
- `results/feasibility/lanuk_later_iot_overlap.csv`

Official sources:

- [verified hydrological data and station metadata]({HYDRO_URL.rsplit("/", 1)[0]}/)
- [HYGON raw-data metadata and data-model note]({HYGON_URL.rsplit("/", 1)[0]}/)
"""
    REPORT_PATH.write_text(text, encoding="utf-8")


def main():
    discharge = pd.read_csv(SERIES_PATH, parse_dates=["timestamp_utc"]).set_index("timestamp_utc")
    discharge.index = pd.DatetimeIndex(discharge.index)
    inventory = pd.read_csv(INVENTORY_PATH)
    metadata = inventory[["gauge", "station_name", "start", "end", "n_hours"]].merge(
        station_metadata(), on=["gauge", "station_name"], how="left"
    )
    audit = window_audit(discharge, metadata)
    summary = window_summary(audit)
    july = july_status(discharge, metadata)
    later = later_iot_overlap(discharge, metadata)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    metadata.to_csv(RESULTS_DIR / "lanuk_gauge_metadata.csv", index=False)
    audit.to_csv(RESULTS_DIR / "lanuk_gauge_windows.csv", index=False)
    summary.to_csv(RESULTS_DIR / "lanuk_window_summary.csv", index=False)
    july.to_csv(RESULTS_DIR / "lanuk_july_2021_status.csv", index=False)
    later.to_csv(RESULTS_DIR / "lanuk_later_iot_overlap.csv", index=False)
    write_report(metadata, audit, summary, july, later)
    print(summary.to_string(index=False))
    print(f"wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
