"""Audit the hard inputs before any case-crossover outcome is estimated.

Implements the gates of protocol draft 0.9 §2. The audit reads timestamps,
counts, flags, geometry and discharge ranks only. It never reads rainfall or
weather values beyond their presence and physical range, and it estimates no
association. Rows marked non-binding report a fallback, not a failure.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.event_study import (
    assign_eras,
    at_risk_hours,
    cluster_regional_storms,
    episode_table,
    era_thresholds,
    rating_domain_admissible,
    storm_table,
    stratum_labels,
)

CORE_FILES = {
    "long discharge": Path("data/interim/event_study_discharge_hourly.csv"),
    "gauge metadata": Path("data/interim/event_study_gauges.csv"),
    "rating eras": Path("data/interim/event_study_rating_eras.csv"),
    "radar catchment rainfall": Path("data/interim/radolan_catchment_hourly.csv"),
    "catchment polygons": Path("data/interim/event_study_catchments.gpkg"),
    "long public weather": Path("data/interim/event_study_weather_hourly.csv"),
    "public weather provenance": Path("data/interim/event_study_weather_sources.csv"),
}
OUTPUT_DIR = Path("results/event_study")
JULY_2021_ANCHOR = pd.Timestamp("2021-07-15", tz="UTC")
MIN_WATERCOURSES = 5
MIN_WATERCOURSES_SIGN_TEST = 6
MIN_YEARS = 10
MIN_STORMS = 40
MIN_STORMS_PER_SEASON = 15
MIN_EPISODES = 20
MIN_OVERALL_COVERAGE = 0.80
MIN_ANNUAL_COVERAGE = 0.70
QA_COLUMNS = [
    "rating_eras_documented",
    "timezone_verified",
    "units_verified",
    "zero_semantics_verified",
    "sampling_semantics_verified",
]
GAUGE_COLUMNS = {
    "gauge",
    "watercourse",
    "independence_unit",
    "latitude",
    "longitude",
    "include_primary",
    "natural_tributary",
    "july_2021_status",
    *QA_COLUMNS,
}
ERA_COLUMNS = {
    "gauge",
    "era_id",
    "valid_from_utc",
    "valid_to_utc",
    "domain_min_m3s",
    "domain_max_m3s",
    "source_document",
}
WEATHER_COLUMNS = {"timestamp_utc", "watercourse", "relative_humidity_pct", "surface_pressure_hpa"}


def add(rows, name, passed, observed, required, binding=True):
    """Append one readable gate result."""
    if binding:
        status = "PASS" if passed else "FAIL"
    else:
        status = "PASS" if passed else "FALLBACK"
    rows.append(
        {
            "gate": name,
            "status": status,
            "binding": binding,
            "observed": str(observed),
            "requirement": required,
        }
    )


def as_bool(series):
    return series.astype(str).str.strip().str.lower().isin({"true", "1", "yes"})


def read_hourly(path):
    """Read a regular wide UTC table; keep missing values on its hourly grid."""
    frame = pd.read_csv(path)
    if "timestamp_utc" not in frame:
        return frame, False
    index = pd.DatetimeIndex(pd.to_datetime(frame.pop("timestamp_utc"), utc=True, errors="coerce"))
    step = index.to_series().diff().dropna()
    valid = (
        len(index) > 0
        and index.notna().all()
        and index.is_monotonic_increasing
        and not index.has_duplicates
        and (index.minute == 0).all()
        and (index.second == 0).all()
        and step.eq(pd.Timedelta(hours=1)).all()
    )
    frame = frame.apply(pd.to_numeric, errors="coerce")
    return frame.set_axis(index), bool(valid)


def common_span(frame):
    """Overlap between the latest first observation and earliest last one."""
    bounds = [
        (column.first_valid_index(), column.last_valid_index()) for _, column in frame.items()
    ]
    if not bounds or any(start is None or end is None for start, end in bounds):
        return pd.NaT, pd.NaT, 0.0
    start = max(start for start, _ in bounds)
    end = min(end for _, end in bounds)
    years = max(0.0, (end - start + pd.Timedelta(hours=1)) / pd.Timedelta(days=365))
    return start, end, years


def coverage_summary(frame, start, end):
    """Summarise observed hours over one fixed common period."""
    expected = pd.date_range(start, end, freq="h")
    observed = frame.reindex(expected).notna()
    overall = observed.mean()
    annual_minimum = observed.groupby(observed.index.year).mean().min()
    return pd.DataFrame(
        {
            "overall_coverage": overall,
            "minimum_annual_coverage": annual_minimum,
        }
    )


def coverage_passes(summary):
    """Apply the density floor to every required series."""
    if summary.empty:
        return False
    return bool(
        summary.overall_coverage.ge(MIN_OVERALL_COVERAGE).all()
        and summary.minimum_annual_coverage.ge(MIN_ANNUAL_COVERAGE).all()
    )


def contains_july_2021(start, end):
    """Require the independently specified anchor inside the common period."""
    return bool(start <= JULY_2021_ANCHOR <= end)


def read_rating_eras(path, gauges):
    """Read the rating-era table and check one non-overlapping era set per gauge."""
    eras = pd.read_csv(path)
    if not ERA_COLUMNS.issubset(eras):
        return eras, False, f"missing columns {sorted(ERA_COLUMNS - set(eras))}"
    problems = []
    for gauge in gauges:
        table = eras.loc[eras.gauge.astype(str).eq(gauge)]
        if table.empty:
            problems.append(f"{gauge}: no era")
            continue
        if not table.era_id.astype(str).is_unique:
            problems.append(f"{gauge}: duplicate era ids")
        try:
            assign_eras(pd.DatetimeIndex([], tz="UTC"), table)
        except ValueError as error:
            problems.append(f"{gauge}: {error}")
    return eras, not problems, problems or f"{len(eras)} eras for {len(gauges)} gauges"


def gauge_hourly_state(series, era_table, start, end):
    """Era labels, admissibility and era thresholds over the joint period."""
    study = series.loc[start:end]
    eras = assign_eras(study.index, era_table)
    admissible = rating_domain_admissible(study, eras, era_table)
    _, threshold = era_thresholds(study, eras)
    return study, eras, admissible, threshold


def episode_feasibility(frame, era_tables, start, end):
    """Count episodes, censored onsets and at-risk hours per gauge (blinded audit)."""
    counts, chains, risk_rows, event_rows = {}, {}, [], []
    for gauge in frame:
        study, eras, admissible, threshold = gauge_hourly_state(
            frame[gauge], era_tables[gauge], start, end
        )
        episodes = episode_table(study, threshold, 72, admissible, eras)
        censored = episodes.onset_censored.astype(bool)
        counts[gauge] = {"uncensored": int((~censored).sum()), "censored": int(censored.sum())}
        chains[gauge] = {
            "maximum_crossings": int(episodes.n_crossings.max()) if len(episodes) else 0,
            "maximum_span_hours": float(episodes.chain_span_hours.max()) if len(episodes) else 0.0,
        }
        event_rows.extend(
            {"gauge": gauge, "onset_utc": onset, "onset_censored": flag}
            for onset, flag in zip(episodes.onset_utc, censored, strict=True)
        )
        risk = at_risk_hours(study, threshold, admissible, eras)
        strata = stratum_labels(study.index, gauge)
        per_stratum = risk.at_risk.groupby(strata).sum()
        risk_rows.append(
            {
                "gauge": gauge,
                "at_risk_hours": int(risk.at_risk.sum()),
                "strata_with_onset": int(risk.onset.groupby(strata).any().sum()),
                "median_at_risk_per_stratum": float(per_stratum.median()),
            }
        )
    events = pd.DataFrame(event_rows, columns=["gauge", "onset_utc", "onset_censored"])
    return counts, chains, events, pd.DataFrame(risk_rows)


def validate_catchments(path, watercourses):
    """Open the GeoPackage and verify the polygons used for catchment rainfall."""
    try:
        import geopandas as gpd
    except ImportError:
        return False, "geopandas is not installed"

    try:
        frame = gpd.read_file(path)
    except Exception as error:  # pragma: no cover - backend messages vary
        return False, f"could not read GeoPackage: {error}"

    required = set(map(str, watercourses))
    if "watercourse" not in frame or "dem_source" not in frame:
        return False, "missing watercourse or dem_source field"
    names = frame.watercourse.astype(str)
    geometries = frame.geometry
    projected = frame.crs is not None and bool(frame.crs.is_projected)
    polygonal = geometries.geom_type.isin({"Polygon", "MultiPolygon"}).all()
    valid = (
        not frame.empty
        and names.is_unique
        and set(names) == required
        and geometries.notna().all()
        and not geometries.is_empty.any()
        and geometries.is_valid.all()
        and polygonal
        and projected
        and geometries.area.gt(0).all()
        and frame.dem_source.fillna("").astype(str).str.strip().ne("").all()
    )
    observed = (
        f"{len(frame)} polygons; CRS={frame.crs}; "
        f"matched={len(required & set(names))}/{len(required)}; valid={bool(valid)}"
    )
    return bool(valid), observed


def read_long_weather(path):
    """Read the tidy watercourse-weather contract and check each hourly grid."""
    frame = pd.read_csv(path)
    if not WEATHER_COLUMNS.issubset(frame):
        return frame, False, WEATHER_COLUMNS

    frame["timestamp_utc"] = pd.to_datetime(frame.timestamp_utc, utc=True, errors="coerce")
    for column in ["relative_humidity_pct", "surface_pressure_hpa"]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    no_duplicates = not frame.duplicated(["watercourse", "timestamp_utc"]).any()
    regular = no_duplicates and frame.timestamp_utc.notna().all()
    for _, group in frame.groupby("watercourse"):
        index = pd.DatetimeIndex(group.timestamp_utc).sort_values()
        step = index.to_series().diff().dropna()
        regular &= (
            len(index) > 0
            and (index.minute == 0).all()
            and (index.second == 0).all()
            and step.eq(pd.Timedelta(hours=1)).all()
        )
    return frame, bool(regular), WEATHER_COLUMNS


def audit():
    """Audit the regional inputs without calculating signal outcomes."""
    rows = []
    for name, path in CORE_FILES.items():
        add(rows, f"File: {name}", path.exists(), path, "file exists")

    # Downstream checks cannot be evaluated until every regional file exists.
    if not all(path.exists() for path in CORE_FILES.values()):
        return pd.DataFrame(rows)

    gauges = pd.read_csv(CORE_FILES["gauge metadata"])
    gauge_schema = GAUGE_COLUMNS.issubset(gauges)
    add(rows, "Gauge metadata schema", gauge_schema, sorted(gauges), sorted(GAUGE_COLUMNS))
    if not gauge_schema:
        return pd.DataFrame(rows)

    primary = gauges[as_bool(gauges.include_primary) & as_bool(gauges.natural_tributary)].copy()
    n_units = primary.independence_unit.nunique()
    add(
        rows,
        "Independent natural watercourses (core)",
        n_units >= MIN_WATERCOURSES,
        n_units,
        f">={MIN_WATERCOURSES}",
    )
    add(
        rows,
        "Independent natural watercourses (S3 sign test)",
        n_units >= MIN_WATERCOURSES_SIGN_TEST,
        n_units,
        f">={MIN_WATERCOURSES_SIGN_TEST}; otherwise S3 is descriptive with no sign test",
        binding=False,
    )
    one_gauge_each = (
        not primary.empty
        and primary.gauge.astype(str).is_unique
        and primary.watercourse.astype(str).is_unique
        and primary.independence_unit.astype(str).is_unique
    )
    add(
        rows,
        "One representative gauge per independent watercourse",
        one_gauge_each,
        f"{primary.gauge.nunique()} gauges / {n_units} independence units",
        "one gauge per watercourse; split branches share one independence unit",
    )
    coordinates = primary[["latitude", "longitude"]].apply(pd.to_numeric, errors="coerce")
    coordinate_ok = (
        not coordinates.empty
        and coordinates.latitude.between(-90, 90).all()
        and coordinates.longitude.between(-180, 180).all()
    )
    add(rows, "Gauge coordinates", coordinate_ok, coordinates.notna().sum().to_dict(), "all valid")

    qa_ok = not primary.empty and primary[QA_COLUMNS].apply(as_bool).all().all()
    july_ok = not primary.empty and primary.july_2021_status.fillna("").str.strip().ne("").all()
    add(rows, "Gauge QA", qa_ok, primary[QA_COLUMNS].apply(as_bool).sum().to_dict(), "all true")
    add(
        rows,
        "July 2021 gauge status",
        july_ok,
        primary.july_2021_status.notna().sum(),
        "all documented",
    )

    gauge_names = primary.gauge.astype(str).tolist()
    eras, eras_ok, eras_observed = read_rating_eras(CORE_FILES["rating eras"], gauge_names)
    add(
        rows,
        "Rating eras",
        eras_ok,
        eras_observed,
        "every primary gauge has documented, non-overlapping eras with rating domains",
    )
    if not eras_ok:
        return pd.DataFrame(rows)
    era_tables = {gauge: eras.loc[eras.gauge.astype(str).eq(gauge)] for gauge in gauge_names}

    discharge, discharge_axis = read_hourly(CORE_FILES["long discharge"])
    discharge_columns = set(gauge_names).issubset(discharge)
    add(
        rows,
        "Discharge time axis",
        discharge_axis,
        f"{discharge.index.min()} to {discharge.index.max()}",
        "regular hourly UTC",
    )
    add(
        rows,
        "Primary discharge series",
        discharge_columns,
        len(set(gauge_names) & set(discharge)),
        len(gauge_names),
    )
    if not discharge_axis or not discharge_columns:
        return pd.DataFrame(rows)

    discharge = discharge[gauge_names]
    discharge_start, discharge_end, discharge_years = common_span(discharge)
    add(
        rows,
        "Common discharge span",
        discharge_years >= MIN_YEARS,
        f"{discharge_years:.2f} years",
        f">={MIN_YEARS} years",
    )
    if pd.isna(discharge_start) or pd.isna(discharge_end):
        return pd.DataFrame(rows)

    catchments_ok, catchments_observed = validate_catchments(
        CORE_FILES["catchment polygons"], primary.watercourse.astype(str)
    )
    add(
        rows,
        "Catchment polygon contents",
        catchments_ok,
        catchments_observed,
        "one valid projected polygon per primary watercourse, with its cross-border DEM named",
    )

    rain, rain_axis = read_hourly(CORE_FILES["radar catchment rainfall"])
    watercourses = primary.watercourse.astype(str).unique().tolist()
    rain_columns = set(watercourses).issubset(rain)
    add(
        rows,
        "Radar rainfall time axis",
        rain_axis,
        f"{rain.index.min()} to {rain.index.max()}",
        "regular hourly UTC",
    )
    add(
        rows,
        "Radar rainfall catchment assignment",
        rain_columns,
        len(set(watercourses) & set(rain)),
        len(watercourses),
    )
    if not rain_axis or not rain_columns:
        return pd.DataFrame(rows)

    negative_rain = int(rain[watercourses].lt(0).sum().sum())
    add(rows, "Radar missing codes", negative_rain == 0, negative_rain, "no negative sentinels")

    rain_start, rain_end, rain_years = common_span(rain[watercourses])
    add(
        rows,
        "Common radar span",
        rain_years >= MIN_YEARS,
        f"{rain_years:.2f} years",
        f">={MIN_YEARS} years",
    )
    if pd.isna(rain_start) or pd.isna(rain_end):
        return pd.DataFrame(rows)

    weather, weather_axis, weather_columns = read_long_weather(CORE_FILES["long public weather"])
    add(
        rows,
        "Public weather schema",
        weather_columns.issubset(weather),
        sorted(weather),
        sorted(weather_columns),
    )
    add(rows, "Public weather time axes", weather_axis, "tidy hourly rows", "regular hourly UTC")
    if not weather_columns.issubset(weather) or not weather_axis:
        return pd.DataFrame(rows)

    weather_watercourses = set(weather.watercourse.astype(str))
    weather_assignment = set(watercourses).issubset(weather_watercourses)
    add(
        rows,
        "Public weather assignment",
        weather_assignment,
        len(set(watercourses) & weather_watercourses),
        len(watercourses),
    )

    weather_sources = pd.read_csv(CORE_FILES["public weather provenance"])
    source_columns = {
        "watercourse",
        "source_id",
        "source_type",
        "spatial_assignment",
        "timezone_verified",
        "units_verified",
    }
    source_schema = source_columns.issubset(weather_sources)
    source_rows = (
        weather_sources[weather_sources.watercourse.astype(str).isin(watercourses)]
        if source_schema
        else pd.DataFrame()
    )
    source_complete = (
        source_schema
        and source_rows.watercourse.astype(str).is_unique
        and set(watercourses).issubset(set(source_rows.watercourse.astype(str)))
        and source_rows[["source_id", "source_type", "spatial_assignment"]]
        .fillna("")
        .astype(str)
        .apply(lambda column: column.str.strip().ne(""))
        .all()
        .all()
        and source_rows[["timezone_verified", "units_verified"]].apply(as_bool).all().all()
    )
    add(
        rows,
        "Public weather provenance",
        source_complete,
        sorted(weather_sources) if source_schema else "schema incomplete",
        "one complete, verified assignment per primary watercourse",
    )
    if not weather_assignment or not source_complete:
        return pd.DataFrame(rows)

    weather_plausible = (
        weather.relative_humidity_pct.dropna().between(0, 100).all()
        and weather.surface_pressure_hpa.dropna().between(850, 1100).all()
    )
    add(
        rows,
        "Public weather value ranges",
        weather_plausible,
        "RH [0,100], surface pressure [850,1100]",
        "all observed values physically plausible",
    )

    weather_wide = weather.pivot(
        index="timestamp_utc",
        columns="watercourse",
        values=["relative_humidity_pct", "surface_pressure_hpa"],
    )
    selected_weather = weather_wide.loc[
        :, weather_wide.columns.get_level_values(1).isin(watercourses)
    ]
    weather_start, weather_end, weather_years = common_span(selected_weather)
    add(
        rows,
        "Common public weather span",
        weather_years >= MIN_YEARS,
        f"{weather_years:.2f} years",
        f">={MIN_YEARS} years",
    )
    if pd.isna(weather_start) or pd.isna(weather_end):
        return pd.DataFrame(rows)

    joint_start = max(discharge_start, rain_start, weather_start)
    joint_end = min(discharge_end, rain_end, weather_end)
    joint_years = max(
        0.0,
        (joint_end - joint_start + pd.Timedelta(hours=1)) / pd.Timedelta(days=365),
    )
    add(
        rows,
        "Joint analysis span",
        joint_years >= MIN_YEARS,
        f"{joint_years:.2f} years",
        f">={MIN_YEARS} years",
    )
    includes_anchor = contains_july_2021(joint_start, joint_end)
    add(
        rows,
        "July 2021 in joint span",
        includes_anchor,
        f"{joint_start} to {joint_end}",
        f"contains {JULY_2021_ANCHOR}",
    )
    if joint_years < MIN_YEARS or not includes_anchor:
        return pd.DataFrame(rows)

    density = f">={MIN_OVERALL_COVERAGE:.0%} overall and >={MIN_ANNUAL_COVERAGE:.0%} in every calendar year"
    discharge_coverage = coverage_summary(discharge, joint_start, joint_end)
    add(
        rows,
        "Discharge observation density",
        coverage_passes(discharge_coverage),
        discharge_coverage.round(3).to_dict(orient="index"),
        density,
    )
    rain_coverage = coverage_summary(rain[watercourses], joint_start, joint_end)
    add(
        rows,
        "Radar rainfall observation density",
        coverage_passes(rain_coverage),
        rain_coverage.round(3).to_dict(orient="index"),
        density,
    )
    weather_coverage = coverage_summary(selected_weather, joint_start, joint_end)
    weather_coverage.index = [" / ".join(map(str, column)) for column in weather_coverage.index]
    add(
        rows,
        "Public weather observation density",
        coverage_passes(weather_coverage),
        weather_coverage.round(3).to_dict(orient="index"),
        density,
    )

    counts, chains, events, risk = episode_feasibility(
        discharge, era_tables, joint_start, joint_end
    )
    minimum_episodes = min((count["uncensored"] for count in counts.values()), default=0)
    add(
        rows,
        "Uncensored p99 episodes per watercourse",
        minimum_episodes >= MIN_EPISODES,
        counts,
        f">={MIN_EPISODES} uncensored episodes each within the joint period",
    )
    add(
        rows,
        "Episode single-linkage diagnostics",
        True,
        chains,
        "reported for every primary gauge",
        binding=False,
    )
    add(
        rows,
        "At-risk hours",
        not risk.empty and risk.at_risk_hours.gt(0).all(),
        risk.to_dict(orient="records"),
        "every primary gauge contributes at-risk hours",
    )
    storms = storm_table(cluster_regional_storms(events))
    estimable = storms.loc[storms.n_uncensored.gt(0)] if not storms.empty else storms
    add(
        rows,
        "Regional storms",
        len(estimable) >= MIN_STORMS,
        {"with_uncensored_onset": len(estimable), "all": len(storms)},
        f">={MIN_STORMS} storms with at least one uncensored onset",
    )
    warm = int(estimable.warm_season.sum()) if len(estimable) else 0
    cold = len(estimable) - warm
    add(
        rows,
        "Regional storms per season",
        min(warm, cold) >= MIN_STORMS_PER_SEASON,
        {"warm": warm, "cold": cold},
        f">={MIN_STORMS_PER_SEASON} per season; otherwise S1 becomes primary (protocol §2)",
        binding=False,
    )

    return pd.DataFrame(rows)


def write_report(table):
    """Write the tidy audit as CSV and a small Markdown table."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    table.to_csv(OUTPUT_DIR / "gate_audit.csv", index=False)
    columns = ["gate", "status", "binding", "observed", "requirement"]
    markdown = [
        "| " + " | ".join(columns) + " |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in table[columns].itertuples(index=False, name=None):
        cells = [str(value).replace("|", "\\|").replace("\n", " ") for value in row]
        markdown.append("| " + " | ".join(cells) + " |")
    binding = table.loc[table.binding.astype(bool)] if not table.empty else table
    passed = not binding.empty and binding.status.eq("PASS").all()
    report = [
        "# Event-study data-gate audit",
        "",
        f"Core regional inputs: **{'PASS' if passed else 'FAIL'}**",
        "",
        "This is an input-feasibility audit, not a chapter result. FALLBACK rows are "
        "non-binding and name the protocol's fixed fallback.",
        "",
        *markdown,
        "",
    ]
    (OUTPUT_DIR / "gate_audit.md").write_text("\n".join(report), encoding="utf-8")
    return passed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--report-only", action="store_true", help="return zero when the regional gates fail"
    )
    args = parser.parse_args()
    table = audit()
    passed = write_report(table)
    print(table.to_string(index=False))
    if not passed and not args.report_only:
        raise SystemExit("Regional data gates failed; do not run the event study")


if __name__ == "__main__":
    main()
