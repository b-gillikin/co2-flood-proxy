#!/usr/bin/env python3
"""Convert LANUK Wurm deliveries and evaluate paired Q-only NL/DE analogues."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.event_study import (  # noqa: E402
    assign_eras,
    cluster_regional_storms,
    episode_table,
    era_thresholds,
    rating_domain_admissible,
)

SPEC = importlib.util.spec_from_file_location(
    "ttm_extension", ROOT / "scripts/70_ttm_analogue_comparison.py"
)
TTM = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(TTM)
SOURCE = ROOT / "data/raw/external_deliveries/lanuk_nrw/2026-09-23"
PERIODS = ROOT / "config/lanuk_rating_periods.csv"
DEFAULT_OUT = ROOT / "results/basin_ai_german_extension"
SOURCE_CLOCK = timezone(timedelta(hours=1))
PROVISIONAL_START = pd.Timestamp("2021-07-01", tz=SOURCE_CLOCK).tz_convert("UTC")
STATIONS = {
    "herzogenrath1": ("2828300000200", "Herzogenrath 1"),
    "randerath": ("2828900000200", "Randerath"),
}


def read_quarters(path, station_id, station_name, parameter):
    lines = path.read_text(encoding="latin1").splitlines()
    header = dict(line.split(";", 1) for line in lines[:32])
    expected = {
        "Stationsnummer": station_id,
        "Station": station_name,
        "Gewässer": "Wurm",
        "Parameter": parameter,
        "Einheit": "m³/s" if parameter == "Abfluss" else "cm",
        "Zeitangabe": "Rechte Seite des Zeitintervalls mit Intervallwert",
    }
    if any(
        header.get(key) != value for key, value in expected.items()
    ) or "15 Minuten" not in header.get("Lebenslauf", ""):
        raise ValueError(f"Unexpected station/parameter/clock metadata: {path}")
    table = pd.read_csv(
        path, sep=";", skiprows=32, names=["source_time", "value"], encoding="latin1", dtype=str
    )
    times = (
        pd.to_datetime(table.source_time, format="%d.%m.%Y %H:%M:%S")
        .dt.tz_localize(SOURCE_CLOCK)
        .dt.tz_convert("UTC")
    )
    text = table.value.fillna("").str.strip().str.replace(",", ".", regex=False)
    values = pd.to_numeric(text, errors="coerce")
    if (text.ne("") & values.isna()).any():
        raise ValueError(f"Unparseable nonblank values: {path}")
    series = pd.Series(values.to_numpy(), index=pd.DatetimeIndex(times))
    if series.index.has_duplicates or not series.index.is_monotonic_increasing:
        raise ValueError("LANUK timestamps are duplicated or unordered")
    if not series.index.to_series().diff().iloc[1:].eq(pd.Timedelta(minutes=15)).all():
        raise ValueError("LANUK delivery must have a complete quarter-hour grid")
    return series


def complete_hourly(quarters):
    grouped = quarters.resample("h", closed="right", label="right")
    return grouped.mean().where(grouped.count().eq(4))


def read_periods():
    periods = pd.read_csv(PERIODS, dtype={"curve": str})
    for row in periods.itertuples():
        if TTM.sha256(ROOT / row.source_pdf) != row.source_pdf_sha256:
            raise ValueError("Provider curve-validity document changed")
    for source, target in [
        ("valid_from_source", "valid_from_utc"),
        ("valid_to_source", "valid_to_utc"),
    ]:
        periods[target] = (
            pd.to_datetime(periods[source]).dt.tz_localize(SOURCE_CLOCK).dt.tz_convert("UTC")
        )
    return periods


def quality_for_window(q, stage, era, period, periods, onset):
    """Keep uncertain events; classify whether an exact-Q response can be scored."""
    response_times = pd.date_range(onset, periods=73, freq="h")
    q_response = q.reindex(response_times)
    stage_response = stage.reindex(response_times)
    label = era.loc[onset]
    row = periods.set_index("era_id").loc[label]
    if isinstance(row, pd.DataFrame):
        row = row.iloc[0]
    out_of_domain = (
        q_response.lt(row.domain_min_m3s)
        | q_response.gt(row.domain_max_m3s)
        | stage_response.lt(row.stage_min_cm)
        | stage_response.gt(row.stage_max_cm)
    ).any()
    same_period = period.reindex(response_times).eq(period.loc[onset]).all()
    provisional = response_times[-1] >= PROVISIONAL_START
    complete = q_response.notna().all() and stage_response.notna().all()
    exact_score = bool(complete and not out_of_domain and same_period and not provisional)
    return {
        "provisional_high_flow": bool(provisional),
        "response_out_of_rating_domain": bool(out_of_domain),
        "response_crosses_rating_period": bool(not same_period),
        "response_stage_complete": bool(stage_response.notna().all()),
        "outcome_score_admissible": exact_score,
        "measurement_concern": bool(
            provisional or out_of_domain or not same_period or not complete
        ),
    }


def build_german_library():
    periods = read_periods()
    rows, windows, audit, thresholds, hashes = (
        [],
        [],
        [],
        [],
        {str(PERIODS.relative_to(ROOT)): TTM.sha256(PERIODS)},
    )
    offsets = np.arange(-511, 73)
    for station, (station_id, station_name) in STATIONS.items():
        (q_path,) = (SOURCE / station).glob(
            "*abfluss_mit_m_s_csv_export_mittelwerte_15minuten*.csv"
        )
        (stage_path,) = (SOURCE / station).glob(
            "*wasserstand_mit_cm_csv_export_mittelwerte_15minuten*.csv"
        )
        q_quarters = read_quarters(q_path, station_id, station_name, "Abfluss")
        stage_quarters = read_quarters(stage_path, station_id, station_name, "Wasserstand")
        if not q_quarters.index.equals(stage_quarters.index):
            raise ValueError("Stage and Q source grids differ")
        q, stage = complete_hourly(q_quarters), complete_hourly(stage_quarters)
        station_periods = periods.loc[periods.station.eq(station)]
        eras = assign_eras(q.index, station_periods)
        literal_periods = assign_eras(
            q.index, station_periods.assign(era_id=station_periods.period_id)
        )
        per_era, threshold = era_thresholds(q, eras)
        admissible = rating_domain_admissible(q, eras, station_periods, threshold)
        # Literal boundaries censor onset transitions even when curve versions
        # recur; threshold grouping can still pool identical verified versions.
        episodes = episode_table(q, threshold, admissible=admissible, eras=literal_periods)
        for label, value in per_era.items():
            thresholds.append(
                {
                    "gauge": station_id,
                    "era_id": label,
                    "p99_m3s": value,
                    "observed_hours": int(q.loc[eras.eq(label)].notna().sum()),
                }
            )
        for episode in episodes.itertuples(index=False):
            onset = pd.Timestamp(episode.onset_utc)
            event_id = f"{station_id}|{onset.isoformat()}"
            times = onset + pd.to_timedelta(offsets, unit="h")
            q_values = q.reindex(times).to_numpy()
            history_complete = bool(np.isfinite(q_values[:512]).all())
            onset_known = not bool(episode.onset_censored)
            flags = quality_for_window(q, stage, eras, literal_periods, station_periods, onset)
            status = (
                "provisional_high_flow"
                if flags["provisional_high_flow"]
                else "pre_flood_rating_documented"
            )
            rows.append(
                {
                    "event_id": event_id,
                    "gauge": station_id,
                    "watercourse": "Wurm",
                    "country": "DE",
                    "station_name": station_name,
                    "physical_river_group": "Wurm/Worm",
                    "onset_utc": onset,
                    "p99_m3s": float(threshold.loc[onset]),
                    "rating_era": eras.loc[onset],
                    "rating_period": literal_periods.loc[onset],
                    "onset_censored": not onset_known,
                    "n_crossings": episode.n_crossings,
                    "primary_usable": onset_known,
                    "temporal_input_sample": onset_known and history_complete,
                    "provider_status": status,
                    "redundant_sensor_substitution_unflagged": True,
                    "history_start_utc": times[0],
                    "outcome_end_utc": times[-1],
                    "history_discharge_fraction": float(np.isfinite(q_values[:512]).mean()),
                    "history_rainfall_fraction": 0.0,
                    "history_weather_fraction": 0.0,
                    "outcome_discharge_fraction": float(np.isfinite(q_values[512:]).mean()),
                    **flags,
                }
            )
            frame = pd.DataFrame(
                {
                    "event_id": event_id,
                    "gauge": station_id,
                    "watercourse": "Wurm",
                    "onset_utc": onset,
                    "timestamp_utc": times,
                    "relative_hour": offsets,
                    "evidence_phase": np.where(
                        offsets <= 0, "assessment_history", "withheld_outcome"
                    ),
                    "target_discharge_m3s": q_values,
                    "target_stage_cm": stage.reindex(times).to_numpy(),
                    "catchment_rainfall_mm": np.nan,
                    "relative_humidity_pct": np.nan,
                    "surface_pressure_hpa": np.nan,
                    "pressure_change_6h_hpa": np.nan,
                }
            )
            windows.append(frame)
        audit.append(
            {
                "station": station,
                "gauge": station_id,
                "country": "DE",
                "physical_river_group": "Wurm/Worm",
                "first_utc": q.index[0],
                "last_utc": q.index[-1],
                "quarter_rows": len(q_quarters),
                "blank_q_quarters": int(q_quarters.isna().sum()),
                "complete_q_hours": int(q.notna().sum()),
                "complete_stage_hours": int(stage.notna().sum()),
                "candidate_episodes": len(episodes),
                "sensor_continuity": "redundant local stage sensor; substitutions not row-flagged",
                "datum_scope": "stage in gauge cm; current datum is not a historical datum guarantee",
            }
        )
        for path in [q_path, stage_path, ROOT / station_periods.source_pdf.iloc[0]]:
            hashes[str(path.relative_to(ROOT))] = TTM.sha256(path)
    return (
        pd.DataFrame(rows),
        pd.concat(windows, ignore_index=True),
        pd.DataFrame(audit),
        pd.DataFrame(thresholds),
        hashes,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    german, german_windows, audit, thresholds, hashes = build_german_library()
    dutch_path = TTM.RAW.DEFAULT_EVENT_DIR / "event_index.csv"
    dutch_windows_path = TTM.RAW.DEFAULT_EVENT_DIR / "event_windows.parquet"
    dutch = pd.read_csv(dutch_path, parse_dates=["onset_utc"])
    dutch["country"] = "NL"
    dutch["physical_river_group"] = dutch.watercourse.replace({"Worm": "Wurm/Worm"})
    # The explicit Q-only German override must not alter the fixed Dutch sample.
    dutch["temporal_input_sample"] = (
        dutch.primary_usable
        & dutch.history_discharge_fraction.eq(1)
        & dutch.history_rainfall_fraction.eq(1)
        & dutch.history_weather_fraction.eq(1)
    )
    dutch["outcome_score_admissible"] = True
    pooled = cluster_regional_storms(pd.concat([dutch, german], ignore_index=True))
    storm_lookup = pooled.set_index("event_id").storm_id
    german["storm_id"] = german.event_id.map(storm_lookup)
    german_windows["storm_id"] = german_windows.event_id.map(storm_lookup)
    german.to_csv(args.output_dir / "german_event_index.csv", index=False)
    german_windows.to_parquet(args.output_dir / "german_event_windows.parquet", index=False)
    pooled.to_csv(args.output_dir / "pooled_event_index.csv", index=False)
    audit.to_csv(args.output_dir / "source_audit.csv", index=False)
    thresholds.to_csv(args.output_dir / "era_thresholds.csv", index=False)
    full_windows = pd.concat(
        [pd.read_parquet(dutch_windows_path), german_windows], ignore_index=True
    )
    signatures = TTM.RAW.BASELINE.build_signatures(pooled, full_windows)
    german_ids = signatures.loc[
        signatures.common_representation_sample
        & signatures.gauge.isin([x[0] for x in STATIONS.values()]),
        "event_id",
    ]
    german_raw, checks = TTM.RAW.standardized_histories(german_ids, german_windows)
    german_vectors, model_info = TTM.extract_embeddings(german_raw)
    german_raw.to_parquet(args.output_dir / "german_standardized_histories.parquet")
    german_vectors.to_parquet(args.output_dir / "german_ttm_embeddings.parquet")
    checks.to_csv(args.output_dir / "german_standardization.csv", index=False)
    raw_path = TTM.RAW.DEFAULT_OUT / "standardized_histories.parquet"
    ttm_path = TTM.DEFAULT_OUT / "event_embeddings.parquet"
    vectors = {
        "r1": pd.concat([pd.read_parquet(raw_path), german_raw]),
        "r2": pd.concat([pd.read_parquet(ttm_path), german_vectors]),
    }
    metadata = pooled.set_index("event_id")
    summaries = {}
    scores = []
    for quality in [False, True]:
        label = "quality_sensitivity" if quality else "main"
        outputs = {}
        for arm, representation in vectors.items():
            predictions, neighbors = TTM.RAW.BASELINE.retrieve_prior_analogues(
                signatures,
                top_k=5,
                min_candidates=20,
                exclude_measurement_concerns=quality,
                representation_vectors=representation,
            )
            outputs[arm] = predictions
            for table in [predictions, neighbors]:
                table["query_country"] = table.query_event_id.map(metadata.country)
                table["query_river_group"] = table.query_event_id.map(metadata.physical_river_group)
            neighbors["analogue_country"] = neighbors.analogue_event_id.map(metadata.country)
            neighbors["analogue_river_group"] = neighbors.analogue_event_id.map(
                metadata.physical_river_group
            )
            predictions.to_csv(args.output_dir / f"{label}_{arm}_predictions.csv", index=False)
            neighbors.to_csv(args.output_dir / f"{label}_{arm}_neighbors.csv", index=False)
            scores.append(predictions.assign(arm=arm, analysis=label))
            summaries[f"{label}_{arm}"] = {
                "queries": len(predictions),
                "storms": int(predictions.query_storm_id.nunique()),
                "mae": float(predictions.analogue_absolute_error.mean()),
                "median_mae": float(predictions.median_absolute_error.mean()),
                "cross_country_donor_slots": int(
                    neighbors.query_country.ne(neighbors.analogue_country).sum()
                ),
            }
        TTM.compare_arms(outputs["r1"], outputs["r2"], "r1", "r2").to_csv(
            args.output_dir / f"{label}_r1_r2_paired.csv", index=False
        )
    pd.concat(scores).groupby(
        ["analysis", "arm", "query_country", "query_watercourse"], as_index=False
    ).agg(
        queries=("query_event_id", "size"),
        storms=("query_storm_id", "nunique"),
        mae=("analogue_absolute_error", "mean"),
        median_mae=("median_absolute_error", "mean"),
    ).to_csv(args.output_dir / "scores_by_country_watercourse.csv", index=False)
    german.assign(
        complete_scoring_sample=german.temporal_input_sample
        & german.outcome_discharge_fraction.eq(1)
        & german.outcome_score_admissible
    ).groupby(["gauge", "provider_status"], as_index=False).agg(
        events=("event_id", "size"),
        input_events=("temporal_input_sample", "sum"),
        exact_q_score_events=("complete_scoring_sample", "sum"),
        censored_onsets=("onset_censored", "sum"),
        domain_concerns=("response_out_of_rating_domain", "sum"),
    ).to_csv(args.output_dir / "german_sample_counts.csv", index=False)
    for path in [
        dutch_path,
        dutch_windows_path,
        raw_path,
        ttm_path,
        Path(__file__),
        ROOT / "src/event_study.py",
        ROOT / "docs/lanuk-provider-clarification-2026-10-13.md",
        ROOT / "scripts/69_raw_hydrograph_analogue_baseline.py",
        ROOT / "scripts/65_hydrological_analogue_baseline.py",
        ROOT / "scripts/70_ttm_analogue_comparison.py",
    ]:
        hashes[str(path.relative_to(ROOT))] = TTM.sha256(path)
    manifest = {
        "status": "Wurm converted; pooled Q-only R1/R2 comparison executed",
        "german_events": len(german),
        "german_input_events": len(german_raw),
        "model_info": model_info,
        "german_exact_q_score_events": int(
            signatures.loc[
                signatures.gauge.isin(german.gauge.unique()), "complete_scoring_sample"
            ].sum()
        ),
        "source_clock": "fixed UTC+1; complete four-quarter trailing mean at UTC hour-end",
        "provisional_start_utc": PROVISIONAL_START.isoformat(),
        "outcome_rule": "Known onset, complete stage/Q response, same literal period, within stage/Q domains, pre-provisional regime",
        "unscored_events": "retained with measured stage and uncertainty flags; not a chapter stop",
        "input_difference": "German rain/weather unavailable; R0 and AlphaEarth excluded from this common Q-only pass",
        "storm_rule": "72-hour linkage over full NL/DE inventory, not separate country clusters",
        "river_identity": "two German stations plus Dutch Worm are one Wurm/Worm river group",
        "results": summaries,
        "input_sha256": hashes,
        "interpretation": "Descriptive paired errors, not forecast skill; German provisional peaks are not exact-Q targets. Step 6 remains.",
    }
    (args.output_dir / "summary.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({k: v for k, v in manifest.items() if k != "input_sha256"}, indent=2))


if __name__ == "__main__":
    main()
