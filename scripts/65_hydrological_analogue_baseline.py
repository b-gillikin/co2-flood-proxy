#!/usr/bin/env python3
"""Build and evaluate an interpretable historical-event analogue baseline.

Only observations at or before each onset form retrieval features. Candidate
analogues must precede the query and belong to another storm. Post-onset values
are labels used to test whether retrieved events had similar subsequent shapes.
This is a representation baseline, not an operational forecast.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EVENT_LIBRARY_SCRIPT = ROOT / "scripts/64_build_basin_ai_event_library.py"
DEFAULT_EVENT_DIR = ROOT / "results/basin_ai_event_library"
DEFAULT_OUT = ROOT / "results/basin_ai_analogue_baseline"

FEATURE_COLUMNS = [
    "rain_sum_6h_mm",
    "rain_sum_24h_mm",
    "rain_sum_72h_mm",
    "rain_sum_168h_mm",
    "rain_max_1h_24h_mm",
    "q_over_p99_m24",
    "q_over_p99_m6",
    "q_over_p99_onset",
    "q_change_6h_over_p99",
    "q_change_24h_over_p99",
]


def _load_event_builder():
    spec = importlib.util.spec_from_file_location("event_library", EVENT_LIBRARY_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _point(group: pd.DataFrame, column: str, hour: int) -> float:
    value = group.loc[group.relative_hour.eq(hour), column]
    return float(value.iloc[0]) if len(value) == 1 and pd.notna(value.iloc[0]) else np.nan


def _rain_sum(group: pd.DataFrame, hours: int) -> float:
    values = group.loc[
        group.relative_hour.gt(-hours) & group.relative_hour.le(0),
        "catchment_rainfall_mm",
    ]
    return float(values.sum()) if len(values) == hours and values.notna().all() else np.nan


def build_signatures(index: pd.DataFrame, windows: pd.DataFrame) -> pd.DataFrame:
    metadata = index.set_index("event_id")
    rows = []
    for event_id, group in windows.groupby("event_id", sort=False):
        meta = metadata.loc[event_id]
        p99 = float(meta.p99_m3s)
        q_m24 = _point(group, "target_discharge_m3s", -24)
        q_m6 = _point(group, "target_discharge_m3s", -6)
        q_0 = _point(group, "target_discharge_m3s", 0)
        recent_rain = group.loc[
            group.relative_hour.gt(-24) & group.relative_hour.le(0),
            "catchment_rainfall_mm",
        ]
        outcome = group.loc[
            group.relative_hour.ge(0) & group.relative_hour.le(72),
            ["relative_hour", "target_discharge_m3s"],
        ].dropna()
        if outcome.empty:
            peak_ratio = time_to_peak = hours_above = excess = np.nan
        else:
            peak_position = outcome.target_discharge_m3s.idxmax()
            peak_ratio = float(outcome.loc[peak_position, "target_discharge_m3s"] / p99)
            time_to_peak = int(outcome.loc[peak_position, "relative_hour"])
            normalized = outcome.target_discharge_m3s / p99
            hours_above = int(normalized.ge(1).sum())
            excess = float(normalized.sub(1).clip(lower=0).sum())

        rows.append(
            {
                "event_id": event_id,
                "storm_id": meta.storm_id,
                "gauge": meta.gauge,
                "watercourse": meta.watercourse,
                "onset_utc": meta.onset_utc,
                "measurement_concern": bool(meta.measurement_concern),
                "primary_usable": bool(meta.primary_usable),
                "rain_sum_6h_mm": _rain_sum(group, 6),
                "rain_sum_24h_mm": _rain_sum(group, 24),
                "rain_sum_72h_mm": _rain_sum(group, 72),
                "rain_sum_168h_mm": _rain_sum(group, 168),
                "rain_max_1h_24h_mm": (
                    float(recent_rain.max())
                    if len(recent_rain) == 24 and recent_rain.notna().all()
                    else np.nan
                ),
                "q_over_p99_m24": q_m24 / p99,
                "q_over_p99_m6": q_m6 / p99,
                "q_over_p99_onset": q_0 / p99,
                "q_change_6h_over_p99": (q_0 - q_m6) / p99,
                "q_change_24h_over_p99": (q_0 - q_m24) / p99,
                "outcome_peak_over_p99_72h": peak_ratio,
                "outcome_time_to_peak_h": time_to_peak,
                "outcome_hours_at_or_above_p99": hours_above,
                "outcome_excess_area_p99_hours": excess,
            }
        )
    signatures = pd.DataFrame(rows)
    signatures["onset_utc"] = pd.to_datetime(signatures.onset_utc, utc=True)
    return signatures.sort_values(["onset_utc", "gauge"]).reset_index(drop=True)


def retrieve_prior_analogues(
    signatures: pd.DataFrame, top_k: int = 5, min_candidates: int = 20
) -> tuple[pd.DataFrame, pd.DataFrame]:
    complete = signatures.dropna(subset=FEATURE_COLUMNS + ["outcome_peak_over_p99_72h"]).copy()
    neighbors = []
    predictions = []
    for query in complete.itertuples(index=False):
        candidates = complete[
            complete.onset_utc.lt(query.onset_utc)
            & complete.storm_id.ne(query.storm_id)
            & complete.event_id.ne(query.event_id)
        ].copy()
        if len(candidates) < min_candidates:
            continue

        center = candidates[FEATURE_COLUMNS].median()
        scale = candidates[FEATURE_COLUMNS].quantile(0.75) - candidates[FEATURE_COLUMNS].quantile(
            0.25
        )
        scale = scale.mask(scale.eq(0), 1.0)
        query_values = pd.Series({column: getattr(query, column) for column in FEATURE_COLUMNS})
        distances = np.sqrt(
            (
                ((candidates[FEATURE_COLUMNS] - center) / scale - (query_values - center) / scale)
                ** 2
            ).sum(axis=1)
        )
        selected = candidates.assign(distance=distances).nsmallest(top_k, "distance")
        if len(selected) < top_k:
            continue
        baseline = float(candidates.outcome_peak_over_p99_72h.median())
        analogue = float(selected.outcome_peak_over_p99_72h.mean())
        observed = float(query.outcome_peak_over_p99_72h)
        predictions.append(
            {
                "query_event_id": query.event_id,
                "query_storm_id": query.storm_id,
                "query_watercourse": query.watercourse,
                "query_onset_utc": query.onset_utc,
                "candidate_count": len(candidates),
                "observed_peak_over_p99_72h": observed,
                "analogue_prediction": analogue,
                "expanding_median_prediction": baseline,
                "analogue_absolute_error": abs(analogue - observed),
                "median_absolute_error": abs(baseline - observed),
            }
        )
        for rank, row in enumerate(selected.itertuples(index=False), start=1):
            neighbors.append(
                {
                    "query_event_id": query.event_id,
                    "query_storm_id": query.storm_id,
                    "query_onset_utc": query.onset_utc,
                    "rank": rank,
                    "analogue_event_id": row.event_id,
                    "analogue_storm_id": row.storm_id,
                    "analogue_watercourse": row.watercourse,
                    "analogue_onset_utc": row.onset_utc,
                    "distance": row.distance,
                }
            )
    return pd.DataFrame(predictions), pd.DataFrame(neighbors)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--min-candidates", type=int, default=20)
    parser.add_argument("--event-dir", type=Path, default=DEFAULT_EVENT_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    event_index_path = args.event_dir / "event_index.csv"
    windows_path = args.event_dir / "event_windows.parquet"
    if not event_index_path.exists() or not windows_path.exists():
        builder = _load_event_builder()
        event_index, windows = builder.build_event_library()
    else:
        event_index = pd.read_csv(event_index_path, parse_dates=["onset_utc"])
        windows = pd.read_parquet(windows_path)

    signatures = build_signatures(event_index, windows)
    predictions, neighbors = retrieve_prior_analogues(
        signatures, top_k=args.top_k, min_candidates=args.min_candidates
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    signatures.to_csv(args.output_dir / "event_signatures.csv", index=False)
    predictions.to_csv(args.output_dir / "analogue_predictions.csv", index=False)
    neighbors.to_csv(args.output_dir / "analogue_neighbors.csv", index=False)

    summary = {
        "status": "interpretable analogue baseline complete; no foundation model used",
        "feature_columns": FEATURE_COLUMNS,
        "feature_time_boundary": "relative_hour <= 0 only",
        "candidate_boundary": "strictly earlier onset and different storm",
        "top_k": args.top_k,
        "minimum_candidates": args.min_candidates,
        "event_count": int(len(signatures)),
        "complete_signature_count": int(signatures[FEATURE_COLUMNS].notna().all(axis=1).sum()),
        "evaluated_query_count": int(len(predictions)),
        "analogue_peak_ratio_mae": (
            float(predictions.analogue_absolute_error.mean()) if len(predictions) else None
        ),
        "expanding_median_peak_ratio_mae": (
            float(predictions.median_absolute_error.mean()) if len(predictions) else None
        ),
        "interpretation": "A feasibility baseline for later representation comparisons; not forecast skill or operational validation.",
    }
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
