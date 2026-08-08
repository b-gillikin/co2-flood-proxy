"""Audit the hard inputs before any prospective event-study outcome is run."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.event_study import cluster_regional_storms, episode_onsets, episode_table

CORE_FILES = {
    "long discharge": Path("data/interim/event_study_discharge_hourly.csv"),
    "gauge metadata": Path("data/interim/event_study_gauges.csv"),
    "RADOLAN catchment rainfall": Path("data/interim/radolan_catchment_hourly.csv"),
    "catchment polygons": Path("data/interim/event_study_catchments.gpkg"),
    "long public weather": Path("data/interim/event_study_weather_hourly.csv"),
    "public weather provenance": Path("data/interim/event_study_weather_sources.csv"),
}
KERKRADE_FILES = {
    "original IoT": Path("data/interim/viefhues_iot.csv"),
    "later IoT": Path("data/interim/iot_hourly.csv"),
    "IoT sensor-era metadata": Path("data/interim/kerkrade_iot_eras.csv"),
}
OUTPUT_DIR = Path("results/event_study")
JULY_2021_ANCHOR = pd.Timestamp("2021-07-15", tz="UTC")
MIN_OVERALL_COVERAGE = 0.80
MIN_ANNUAL_COVERAGE = 0.70
MIN_SPATIAL_OVERALL_AVAILABILITY = 0.80
MIN_SPATIAL_STRATUM_AVAILABILITY = 0.70
EARTH_RADIUS_KM = 6371.0088
QA_COLUMNS = [
    "rating_curve_verified",
    "timezone_verified",
    "units_verified",
    "zero_sentinel_verified",
    "sampling_semantics_verified",
]


def add(rows, name, passed, observed, required, component="core", status=None):
    """Append one readable gate result."""
    rows.append(
        {
            "component": component,
            "gate": name,
            "status": status or ("PASS" if passed else "FAIL"),
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
    """Apply the draft density floor to every required series."""
    if summary.empty:
        return False
    return bool(
        summary.overall_coverage.ge(MIN_OVERALL_COVERAGE).all()
        and summary.minimum_annual_coverage.ge(MIN_ANNUAL_COVERAGE).all()
    )


def contains_july_2021(start, end):
    """Require the independently specified anchor inside the common period."""
    return bool(start <= JULY_2021_ANCHOR <= end)


def episode_feasibility(frame, start, end):
    """Count p99 episodes and chaining only inside the comparable period."""
    study = frame.loc[start:end]
    counts = {}
    chains = {}
    event_rows = []
    for gauge in study:
        threshold = study[gauge].quantile(0.99)
        episodes = episode_table(study[gauge], threshold, merge_hours=72)
        counts[gauge] = len(episodes)
        chains[gauge] = {
            "maximum_crossings": int(episodes.n_crossings.max()) if len(episodes) else 0,
            "maximum_span_hours": float(episodes.chain_span_hours.max()) if len(episodes) else 0.0,
        }
        event_rows.extend({"gauge": gauge, "onset_utc": onset} for onset in episodes.onset_utc)
    return counts, chains, pd.DataFrame(event_rows, columns=["gauge", "onset_utc"])


def spatial_pair_table(gauges):
    """List every ordered receiver-donor pair and its great-circle distance."""
    coordinates = gauges.set_index("gauge")[["latitude", "longitude"]].astype(float)
    radians = np.radians(coordinates)
    rows = []
    for receiver, point in radians.iterrows():
        latitude = radians.latitude - point.latitude
        longitude = radians.longitude - point.longitude
        a = (
            np.sin(latitude / 2) ** 2
            + np.cos(point.latitude) * np.cos(radians.latitude) * np.sin(longitude / 2) ** 2
        )
        distance = 2 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(a.clip(0, 1)))
        rows.extend(
            {
                "receiver_gauge": str(receiver),
                "donor_gauge": str(donor),
                "distance_km": float(distance.loc[donor]),
            }
            for donor in distance.index
            if donor != receiver
        )
    columns = ["receiver_gauge", "donor_gauge", "distance_km", "distance_stratum"]
    if not rows:
        return pd.DataFrame(columns=columns)
    pairs = pd.DataFrame(rows).sort_values(["receiver_gauge", "distance_km", "donor_gauge"])
    lower, upper = pairs.distance_km.quantile([1 / 3, 2 / 3])
    if lower < upper:
        pairs["distance_stratum"] = pd.cut(
            pairs.distance_km,
            bins=[-np.inf, lower, upper, np.inf],
            labels=["near", "middle", "far"],
            include_lowest=True,
        ).astype("string")
    else:
        pairs["distance_stratum"] = pd.NA
    return pairs.reset_index(drop=True)[columns]


def spatial_event_availability(discharge, events, gauges):
    """Check every donor's level/change window at every receiver event."""
    pairs = spatial_pair_table(gauges)
    rows = []
    for pair in pairs.itertuples(index=False):
        receiver, donor = pair.receiver_gauge, pair.donor_gauge
        onsets = events.loc[events.gauge.eq(receiver), "onset_utc"]
        complete = 0
        for onset in onsets:
            required = pd.date_range(
                onset - pd.Timedelta(hours=13),
                onset - pd.Timedelta(hours=1),
                freq="h",
            )
            complete += int(discharge[donor].reindex(required).notna().all())
        rows.append(
            {
                "receiver_gauge": receiver,
                "donor_gauge": donor,
                "distance_km": pair.distance_km,
                "distance_stratum": pair.distance_stratum,
                "n_receiver_events": len(onsets),
                "n_donor_complete": complete,
                "availability": complete / len(onsets) if len(onsets) else 0.0,
            }
        )
    return pd.DataFrame(rows)


def spatial_availability_summary(availability):
    """Return weighted all-pair availability overall, by receiver and by distance."""
    if availability.empty:
        return 0.0, pd.DataFrame(), pd.DataFrame()

    def aggregate(columns):
        grouped = availability.groupby(columns, observed=True)[
            ["n_receiver_events", "n_donor_complete"]
        ].sum()
        grouped["availability"] = grouped.n_donor_complete / grouped.n_receiver_events.replace(
            0, np.nan
        )
        return grouped.reset_index()

    total_events = availability.n_receiver_events.sum()
    overall = availability.n_donor_complete.sum() / total_events if total_events else 0.0
    return overall, aggregate(["receiver_gauge"]), aggregate(["distance_stratum"])


def validate_catchments(path, watercourses):
    """Open the GeoPackage and verify the polygons used for spatial rainfall."""
    try:
        import geopandas as gpd
    except ImportError:
        return False, "geopandas is not installed"

    try:
        frame = gpd.read_file(path)
    except Exception as error:  # pragma: no cover - backend messages vary
        return False, f"could not read GeoPackage: {error}"

    required = set(map(str, watercourses))
    if "watercourse" not in frame:
        return False, "missing watercourse field"
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
    )
    observed = (
        f"{len(frame)} polygons; CRS={frame.crs}; "
        f"matched={len(required & set(names))}/{len(required)}; valid={bool(valid)}"
    )
    return bool(valid), observed


def read_long_weather(path):
    """Read the tidy watercourse-weather contract and check each hourly grid."""
    frame = pd.read_csv(path)
    required = {
        "timestamp_utc",
        "watercourse",
        "temperature_c",
        "relative_humidity_pct",
        "pressure_hpa",
    }
    if not required.issubset(frame):
        return frame, False, required

    frame["timestamp_utc"] = pd.to_datetime(frame.timestamp_utc, utc=True, errors="coerce")
    for column in ["temperature_c", "relative_humidity_pct", "pressure_hpa"]:
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
    return frame, bool(regular), required


def complete_precursor_events(onsets, frame, columns, hours=72):
    """Count onsets whose full pre-event window is observed for every signal."""
    count = 0
    for onset in onsets:
        window = pd.date_range(
            onset - pd.Timedelta(hours=hours),
            onset - pd.Timedelta(hours=1),
            freq="h",
        )
        observed = frame.reindex(window)[columns].notna()
        count += int(len(observed) == hours and observed.all().all())
    return count


def audit_kerkrade_inputs():
    """Audit the optional CO2 case without affecting the regional chapter gate."""
    rows = []
    iot = pd.read_csv(KERKRADE_FILES["original IoT"])
    iot_columns = {"timestamp_utc", "sensor_era", "iot_co2_ppm", "iot_air_pressure_hpa"}
    iot_schema = iot_columns.issubset(iot)
    add(
        rows,
        "Original IoT schema",
        iot_schema,
        sorted(iot),
        sorted(iot_columns),
        component="kerkrade_case",
    )
    if not iot_schema:
        return rows, None

    iot["timestamp_utc"] = pd.to_datetime(iot.timestamp_utc, utc=True, errors="coerce")
    start, end = iot.timestamp_utc.min(), iot.timestamp_utc.max()
    span_ok = start <= pd.Timestamp("2020-08-25", tz="UTC") and end >= pd.Timestamp(
        "2021-09-01", tz="UTC"
    )
    add(
        rows,
        "Original IoT span",
        span_ok,
        f"{start} to {end}",
        "2020-08-25 to 2021-09-01",
        component="kerkrade_case",
    )
    anchor = iot[iot.timestamp_utc.between("2021-06-29", "2021-07-19 23:59:59")]
    counts = anchor[["iot_co2_ppm", "iot_air_pressure_hpa"]].notna().sum()
    add(
        rows,
        "July 2021 IoT signals",
        counts.gt(0).all(),
        counts.to_dict(),
        "CO2 and pressure both observed",
        component="kerkrade_case",
    )

    later_iot, later_axis = read_hourly(KERKRADE_FILES["later IoT"])
    later_columns = {"iot_co2_ppm", "iot_air_pressure_hpa"}
    later_schema = later_columns.issubset(later_iot)
    add(
        rows,
        "Later IoT schema",
        later_schema,
        sorted(later_iot),
        sorted(later_columns),
        component="kerkrade_case",
    )
    add(
        rows,
        "Later IoT time axis",
        later_axis,
        "hourly table",
        "regular hourly UTC",
        component="kerkrade_case",
    )
    if not later_schema or not later_axis:
        return rows, None
    later_counts = later_iot[list(later_columns)].notna().sum()
    add(
        rows,
        "Later IoT signals",
        later_counts.gt(0).all(),
        later_counts.to_dict(),
        "CO2 and pressure both observed",
        component="kerkrade_case",
    )

    iot_meta = pd.read_csv(KERKRADE_FILES["IoT sensor-era metadata"])
    meta_columns = {
        "sensor_era",
        "era_start_utc",
        "era_end_utc",
        "device_id",
        "calibration_notes",
        "abc_processing_notes",
        "source_resolution",
    }
    meta_schema = meta_columns.issubset(iot_meta)
    meta_complete = (
        meta_schema
        and not iot_meta.empty
        and (
            iot_meta[list(meta_columns)]
            .fillna("")
            .astype(str)
            .apply(lambda values: values.str.strip().ne(""))
        )
        .all()
        .all()
    )
    era_start = (
        pd.to_datetime(iot_meta["era_start_utc"], utc=True, errors="coerce")
        if meta_schema
        else pd.Series(dtype="datetime64[ns, UTC]")
    )
    era_end = (
        pd.to_datetime(iot_meta["era_end_utc"], utc=True, errors="coerce")
        if meta_schema
        else pd.Series(dtype="datetime64[ns, UTC]")
    )
    era_intervals = meta_complete and era_start.notna().all() and era_end.notna().all()
    era_intervals = bool(era_intervals and era_start.le(era_end).all())
    era_names = set(iot_meta.sensor_era.astype(str)) if meta_schema else set()
    original_eras = set(iot.sensor_era.dropna().astype(str))
    all_iot_times = pd.DatetimeIndex(iot.timestamp_utc).append(later_iot.index)
    era_coverage = pd.Series(0, index=all_iot_times)
    if era_intervals:
        for start_time, end_time in zip(era_start, era_end, strict=True):
            era_coverage += era_coverage.index.to_series().between(start_time, end_time).astype(int)
    era_assignment = (
        era_intervals
        and original_eras.issubset(era_names)
        and not era_coverage.empty
        and era_coverage.eq(1).all()
    )
    add(
        rows,
        "IoT provenance",
        meta_complete and era_assignment,
        sorted(iot_meta),
        "both sensor periods assigned once; device, calibration, ABC and resolution complete",
        component="kerkrade_case",
    )
    case_ready = all(row["status"] == "PASS" for row in rows)
    return rows, later_iot if case_ready else None


def audit():
    """Return one tidy gate table; never substitute the rolling two-year files."""
    rows = []
    for name, path in CORE_FILES.items():
        add(rows, f"File: {name}", path.exists(), path, "file exists")
    for name, path in KERKRADE_FILES.items():
        exists = path.exists()
        add(
            rows,
            f"File: {name}",
            exists,
            path,
            "file exists for the optional Kerkrade case",
            component="kerkrade_case",
            status="PASS" if exists else "NOT AVAILABLE",
        )

    later_iot = None
    if all(path.exists() for path in KERKRADE_FILES.values()):
        case_rows, later_iot = audit_kerkrade_inputs()
        rows.extend(case_rows)

    # Missing case-study files do not block the regional chapter. Missing core
    # files do, and downstream checks cannot be evaluated without them.
    if not all(path.exists() for path in CORE_FILES.values()):
        return pd.DataFrame(rows)

    gauges = pd.read_csv(CORE_FILES["gauge metadata"])
    gauge_columns = {
        "gauge",
        "watercourse",
        "latitude",
        "longitude",
        "include_primary",
        "natural_tributary",
        "july_2021_status",
        *QA_COLUMNS,
    }
    gauge_schema = gauge_columns.issubset(gauges)
    add(rows, "Gauge metadata schema", gauge_schema, sorted(gauges), sorted(gauge_columns))
    if not gauge_schema:
        return pd.DataFrame(rows)

    primary = gauges[as_bool(gauges.include_primary) & as_bool(gauges.natural_tributary)].copy()
    n_watercourses = primary.watercourse.nunique()
    add(rows, "Natural tributary cohort", n_watercourses >= 10, n_watercourses, ">=10")
    one_gauge_each = (
        not primary.empty
        and primary.gauge.astype(str).is_unique
        and primary.watercourse.astype(str).is_unique
    )
    add(
        rows,
        "One representative gauge per watercourse",
        one_gauge_each,
        f"{primary.gauge.nunique()} gauges / {n_watercourses} watercourses",
        "one unique gauge for each unique watercourse",
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

    discharge, discharge_axis = read_hourly(CORE_FILES["long discharge"])
    gauge_names = primary.gauge.astype(str).tolist()
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
        discharge_years >= 10,
        f"{discharge_years:.2f} years",
        ">=10 years",
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
        "one unique, valid, non-empty projected polygon per primary watercourse",
    )

    radolan, radolan_axis = read_hourly(CORE_FILES["RADOLAN catchment rainfall"])
    watercourses = primary.watercourse.astype(str).unique().tolist()
    radolan_columns = set(watercourses).issubset(radolan)
    add(
        rows,
        "RADOLAN time axis",
        radolan_axis,
        f"{radolan.index.min()} to {radolan.index.max()}",
        "regular hourly UTC",
    )
    add(
        rows,
        "RADOLAN catchment assignment",
        radolan_columns,
        len(set(watercourses) & set(radolan)),
        len(watercourses),
    )
    if not radolan_axis or not radolan_columns:
        return pd.DataFrame(rows)

    negative_rain = int(radolan[watercourses].lt(0).sum().sum())
    add(rows, "RADOLAN missing codes", negative_rain == 0, negative_rain, "no negative sentinels")

    radolan_start, radolan_end, radolan_years = common_span(radolan[watercourses])
    add(
        rows, "Common RADOLAN span", radolan_years >= 10, f"{radolan_years:.2f} years", ">=10 years"
    )
    if pd.isna(radolan_start) or pd.isna(radolan_end):
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
        weather.temperature_c.dropna().between(-60, 60).all()
        and weather.relative_humidity_pct.dropna().between(0, 100).all()
        and weather.pressure_hpa.dropna().between(850, 1100).all()
    )
    add(
        rows,
        "Public weather value ranges",
        weather_plausible,
        "temperature [-60,60], RH [0,100], pressure [850,1100]",
        "all observed values physically plausible",
    )

    weather_wide = weather.pivot(
        index="timestamp_utc",
        columns="watercourse",
        values=["temperature_c", "relative_humidity_pct", "pressure_hpa"],
    )
    selected_weather = weather_wide.loc[
        :, weather_wide.columns.get_level_values(1).isin(watercourses)
    ]
    weather_start, weather_end, weather_years = common_span(selected_weather)
    add(
        rows,
        "Common public weather span",
        weather_years >= 10,
        f"{weather_years:.2f} years",
        ">=10 years",
    )
    if pd.isna(weather_start) or pd.isna(weather_end):
        return pd.DataFrame(rows)

    joint_start = max(discharge_start, radolan_start, weather_start)
    joint_end = min(discharge_end, radolan_end, weather_end)
    joint_years = max(
        0.0,
        (joint_end - joint_start + pd.Timedelta(hours=1)) / pd.Timedelta(days=365),
    )
    add(rows, "Joint analysis span", joint_years >= 10, f"{joint_years:.2f} years", ">=10 years")
    includes_anchor = contains_july_2021(joint_start, joint_end)
    add(
        rows,
        "July 2021 in joint span",
        includes_anchor,
        f"{joint_start} to {joint_end}",
        f"contains {JULY_2021_ANCHOR}",
    )
    if joint_years < 10 or not includes_anchor:
        return pd.DataFrame(rows)

    discharge_coverage = coverage_summary(discharge[gauge_names], joint_start, joint_end)
    add(
        rows,
        "Discharge observation density",
        coverage_passes(discharge_coverage),
        discharge_coverage.round(3).to_dict(orient="index"),
        f">={MIN_OVERALL_COVERAGE:.0%} overall and >="
        f"{MIN_ANNUAL_COVERAGE:.0%} in every calendar year",
    )
    radolan_coverage = coverage_summary(radolan[watercourses], joint_start, joint_end)
    add(
        rows,
        "RADOLAN observation density",
        coverage_passes(radolan_coverage),
        radolan_coverage.round(3).to_dict(orient="index"),
        f">={MIN_OVERALL_COVERAGE:.0%} overall and >="
        f"{MIN_ANNUAL_COVERAGE:.0%} in every calendar year",
    )
    weather_coverage = coverage_summary(selected_weather, joint_start, joint_end)
    weather_coverage.index = [" / ".join(map(str, column)) for column in weather_coverage.index]
    add(
        rows,
        "Public weather observation density",
        coverage_passes(weather_coverage),
        weather_coverage.round(3).to_dict(orient="index"),
        f">={MIN_OVERALL_COVERAGE:.0%} overall and >="
        f"{MIN_ANNUAL_COVERAGE:.0%} in every calendar year",
    )

    episode_counts, chain_diagnostics, event_rows = episode_feasibility(
        discharge[gauge_names], joint_start, joint_end
    )
    minimum_episodes = min(episode_counts.values(), default=0)
    add(
        rows,
        "p99 episodes per watercourse",
        minimum_episodes >= 20,
        episode_counts,
        ">=20 each within the joint analysis span",
    )
    add(
        rows,
        "Episode single-linkage diagnostics",
        True,
        chain_diagnostics,
        "reported for every primary gauge",
    )
    storms = cluster_regional_storms(event_rows)
    n_storms = storms.storm_id.nunique() if not storms.empty else 0
    add(
        rows,
        "Independent regional storms",
        n_storms >= 40,
        n_storms,
        ">=40 within the joint analysis span",
    )
    spatial_availability = spatial_event_availability(
        discharge.loc[joint_start:joint_end, gauge_names], event_rows, primary
    )
    distance_strata = set(spatial_availability.distance_stratum.dropna())
    distance_support_ok = (
        not spatial_availability.empty
        and spatial_availability.distance_km.gt(0).all()
        and distance_strata == {"near", "middle", "far"}
    )
    add(
        rows,
        "Spatial distance support",
        distance_support_ok,
        {
            "ordered_pairs": len(spatial_availability),
            "unique_distances": spatial_availability.distance_km.nunique(),
            "distance_strata": sorted(distance_strata),
        },
        "all ordered receiver-donor pairs have positive distances and populate near/middle/far strata",
    )
    overall, by_receiver, by_stratum = spatial_availability_summary(spatial_availability)
    spatial_availability_ok = (
        distance_support_ok
        and overall >= MIN_SPATIAL_OVERALL_AVAILABILITY
        and not by_receiver.empty
        and by_receiver.availability.ge(MIN_SPATIAL_STRATUM_AVAILABILITY).all()
        and not by_stratum.empty
        and by_stratum.availability.ge(MIN_SPATIAL_STRATUM_AVAILABILITY).all()
    )
    add(
        rows,
        "All-donor event availability",
        spatial_availability_ok,
        {
            "overall": round(overall, 3),
            "by_receiver": by_receiver.round({"availability": 3}).to_dict(orient="records"),
            "by_distance_stratum": by_stratum.round({"availability": 3}).to_dict(orient="records"),
        },
        f">={MIN_SPATIAL_OVERALL_AVAILABILITY:.0%} overall and >="
        f"{MIN_SPATIAL_STRATUM_AVAILABILITY:.0%} within every receiver and distance stratum "
        "for complete -13 to -1 h donor windows",
    )

    if later_iot is not None:
        case_metadata = {
            "july_2021_onset_lower_utc",
            "july_2021_onset_upper_utc",
        }
        case_schema = case_metadata.issubset(primary)
        add(
            rows,
            "Kerkrade gauge metadata",
            case_schema,
            sorted(primary),
            sorted(case_metadata),
            component="kerkrade_case",
        )
        if case_schema:
            worm = primary.watercourse.str.contains("worm|wurm", case=False, na=False)
            paired = (
                as_bool(primary.kerkrade_pair)
                if "kerkrade_pair" in primary
                else pd.Series(False, index=primary.index)
            )
            rationale = (
                primary.pairing_rationale.fillna("").str.strip().ne("")
                if "pairing_rationale" in primary
                else pd.Series(False, index=primary.index)
            )
            valid_pair = worm | (paired & rationale)
            pair_rows = primary.loc[valid_pair]
            add(
                rows,
                "Kerkrade hydrological pair",
                valid_pair.any(),
                pair_rows.watercourse.tolist(),
                "Worm/Wurm or flagged pair with rationale",
                component="kerkrade_case",
            )
            lower = pd.to_datetime(pair_rows.july_2021_onset_lower_utc, utc=True, errors="coerce")
            upper = pd.to_datetime(pair_rows.july_2021_onset_upper_utc, utc=True, errors="coerce")
            interval_ok = ((lower.notna()) & (upper.notna()) & lower.le(upper)).any()
            add(
                rows,
                "July 2021 censored onset interval",
                interval_ok,
                int(((lower.notna()) & (upper.notna()) & lower.le(upper)).sum()),
                ">=1 independently supported interval for the Kerkrade pair",
                component="kerkrade_case",
            )

            later_event_counts = {}
            for pair_gauge in pair_rows.gauge.astype(str):
                pair_onsets = episode_onsets(
                    discharge[pair_gauge],
                    discharge[pair_gauge].quantile(0.99),
                    merge_hours=72,
                )
                later_event_counts[pair_gauge] = complete_precursor_events(
                    pair_onsets,
                    later_iot,
                    ["iot_co2_ppm", "iot_air_pressure_hpa"],
                )
            complete_later_events = max(later_event_counts.values(), default=0)
            add(
                rows,
                "Later exact-onset Kerkrade events",
                complete_later_events >= 3,
                later_event_counts,
                ">=3 events at one valid pair gauge with complete -72 to -1 h CO2 and pressure",
                component="kerkrade_case",
            )
    return pd.DataFrame(rows)


def write_report(table):
    """Write the audit without adding a table-rendering dependency."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    table.to_csv(OUTPUT_DIR / "gate_audit.csv", index=False)
    columns = ["component", "gate", "status", "observed", "requirement"]
    markdown = [
        "| " + " | ".join(columns) + " |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in table[columns].itertuples(index=False, name=None):
        cells = [str(value).replace("|", "\\|").replace("\n", " ") for value in row]
        markdown.append("| " + " | ".join(cells) + " |")
    core = table[table.component.eq("core")]
    case = table[table.component.eq("kerkrade_case")]
    core_passed = not core.empty and core.status.eq("PASS").all()
    case_detailed = case[~case.gate.str.startswith("File:")]
    required_case_gates = {
        "IoT provenance",
        "Kerkrade hydrological pair",
        "July 2021 censored onset interval",
        "Later exact-onset Kerkrade events",
    }
    case_gates = set(case.gate)
    if case.status.eq("NOT AVAILABLE").any():
        case_status = "NOT AVAILABLE"
    elif case_detailed.empty:
        case_status = "NOT EVALUATED"
    elif required_case_gates.issubset(case_gates) and case.status.eq("PASS").all():
        case_status = "AVAILABLE"
    else:
        case_status = "INCOMPLETE"
    report = [
        "# Event-study data-gate audit",
        "",
        f"Core regional chapter: **{'PASS' if core_passed else 'FAIL'}**",
        f"Conditional Kerkrade CO2 case: **{case_status}**",
        "",
        "The Kerkrade case does not affect the core pass/fail result. This is a "
        "feasibility audit, not a chapter result.",
        "",
        *markdown,
        "",
    ]
    (OUTPUT_DIR / "gate_audit.md").write_text("\n".join(report), encoding="utf-8")
    return core_passed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--report-only", action="store_true", help="return zero when the core gates fail"
    )
    args = parser.parse_args()
    table = audit()
    passed = write_report(table)
    print(table.to_string(index=False))
    if not passed and not args.report_only:
        raise SystemExit("Core data gates failed; do not run the regional event study")


if __name__ == "__main__":
    main()
