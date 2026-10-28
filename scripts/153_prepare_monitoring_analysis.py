"""Build full-census lawful inputs for the monitoring-loss assessment."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.eo_event_inputs import GERMAN_GAUGES, completed_windows, context_id
from src.eo_inputs import sha256
from src.eo_integrity import fresh_output
from src.monitoring_analogues import (
    OFFSETS,
    information_states,
    last_observed_positions,
    q_signature,
)

OUT = ROOT / "results/limburg_monitoring_2026_10_28/preparation"


def main():
    sources = {}

    def bind(name):
        path = ROOT / name
        sources[name] = sha256(path)
        return path

    q = pd.read_parquet(bind("results/storm_response/hourly_discharge.parquet"))
    rain = pd.read_parquet(bind("results/storm_response/hourly_rainfall.parquet"))
    strict = pd.read_parquet(bind("results/storm_response/hourly_strict.parquet")).fillna(False)
    domain = pd.read_parquet(bind("results/storm_response/hourly_domain.parquet")).fillna(False)
    periods = pd.read_parquet(bind("results/storm_response/hourly_period.parquet"))
    if not q.index.equals(rain.index) or not q.index.equals(
        pd.date_range(q.index[0], q.index[-1], freq="h")
    ):
        raise ValueError("Common complete hourly UTC axis required; value gaps stay missing")
    original = pd.read_parquet(bind("results/storm_response/storm_gauge_responses.parquet"))
    sites = (
        original[["gauge", "station", "country", "physical_river"]]
        .drop_duplicates()
        .set_index("gauge")
    )
    import geopandas as gpd

    geometry = gpd.read_file(bind("data/interim/foundation_model_catchments.gpkg"))
    areas = geometry.set_index("gauge").area_km2
    calendar = pd.read_parquet(
        bind("results/monitoring_acquisition_2026_10_28/rainfall_landmarks.parquet")
    )
    calendar = calendar[calendar.calendar.eq("eight_gauge_regional_candidate")].sort_values(
        "cutoff_utc"
    )
    if calendar.empty or calendar.storm_id.duplicated().any():
        raise ValueError("Nonempty unique source-audited regional episodes required")
    ledger = []
    for storm in calendar.itertuples():
        for gauge in q.columns:
            site = sites.loc[gauge]
            row = {
                **storm._asdict(),
                **site.to_dict(),
                "gauge": gauge,
                "catchment_gauge": GERMAN_GAUGES.get(gauge, gauge),
                "area_km2": float(areas[GERMAN_GAUGES.get(gauge, gauge)]),
                "case_id": f"{storm.storm_id}|{gauge}",
            }
            row.pop("Index", None)
            for kind in ["recent", "monthly_snapshot"]:
                windows = completed_windows(storm.cutoff_utc, kind)
                row[kind + "_context_id"] = context_id(kind, windows)
                row[kind + "_bin_age_days"] = (
                    storm.cutoff_utc - pd.Timestamp(windows[-1]["end"])
                ).total_seconds() / 86400
            ledger.append(row)
    meta = pd.DataFrame(ledger).reset_index(drop=True)
    positions = q.index.get_indexer(pd.DatetimeIndex(meta.cutoff_utc))
    if (positions < 0).any():
        raise ValueError("Landmark outside held continuous observation axis")
    n = len(meta)
    rolls = {h: rain.rolling(h, min_periods=h).sum() for h in [6, 24, 72, 168]}
    max24 = rain.rolling(24, min_periods=24).max()
    arrays = {}
    aliases = []
    for u in OFFSETS:
        states = information_states(u)
        rain_x = np.full((n, 5), np.nan)
        outcomes = np.full((n, 24), np.nan)
        quality = np.zeros(n, bool)
        for gauge in q.columns:
            ids = np.flatnonzero(meta.gauge.eq(gauge))
            ix = positions[ids] + u
            issue_times = pd.DatetimeIndex(meta.loc[ids, "cutoff_utc"]) + pd.Timedelta(hours=u)
            for col, h in enumerate([6, 24, 72, 168]):
                rain_x[ids, col] = rolls[h][gauge].reindex(issue_times).to_numpy()
            rain_x[ids, 4] = max24[gauge].reindex(issue_times).to_numpy()
            vals = q[gauge].to_numpy(float)
            good = (strict[gauge].astype(bool) & domain[gauge].astype(bool)).to_numpy()
            eras = periods[gauge].to_numpy()
            for row, pos in zip(ids, ix, strict=True):
                if pos < 0 or pos + 24 >= len(q):
                    continue
                outcomes[row] = vals[pos + 1 : pos + 25]
                quality[row] = bool(
                    good[pos + 1 : pos + 25].all() and len(set(eras[pos : pos + 25])) == 1
                )
        arrays[f"rain_{u}"] = rain_x
        arrays[f"outcome_{u}"] = outcomes
        arrays[f"quality_{u}"] = quality
        arrays[f"outcome_valid_{u}"] = np.isfinite(outcomes).all(axis=1)
        for cap, labels in states.items():
            feature = np.full((n, 6), np.nan)
            input_clean = np.zeros(n, bool)
            end_positions = np.full(n, -1)
            for gauge in q.columns:
                ids = np.flatnonzero(meta.gauge.eq(gauge))
                vals = q[gauge].to_numpy(float)
                latest = last_observed_positions(vals)
                good = (strict[gauge].astype(bool) & domain[gauge].astype(bool)).to_numpy()
                for row in ids:
                    feature[row], s = q_signature(vals, positions[row] + u, cap - u, latest)
                    end_positions[row] = s
                    if s >= 24:
                        input_clean[row] = good[[s, s - 6, s - 24]].all()
            # q_signature's age is measured from issue time, not from the hidden cap.
            arrays[f"q_{u}_{cap}"] = feature
            arrays[f"input_clean_{u}_{cap}"] = input_clean
            arrays[f"last_position_{u}_{cap}"] = end_positions
            aliases.extend({"offset_h": u, "cap_h": cap, "scenario": label} for label in labels)
        arrays[f"fixed_valid_{u}"] = (
            np.isfinite(rain_x).all(axis=1)
            & np.isfinite(outcomes).all(axis=1)
            & np.logical_and.reduce(
                [np.isfinite(arrays[f"q_{u}_{cap}"]).all(axis=1) for cap in states]
            )
        )
    source_code = [
        Path(__file__),
        ROOT / "src/monitoring_analogues.py",
        ROOT / "src/eo_event_inputs.py",
    ]
    with fresh_output(OUT) as work:
        meta.to_parquet(work / "cases.parquet", index=False)
        pd.DataFrame(aliases).to_parquet(work / "scenario_aliases.parquet", index=False)
        np.savez_compressed(work / "inputs.npz", **arrays)
        report = {
            "status": "prepared_not_scored",
            "calendar": "eight-gauge regional first observed-prefix 10mm",
            "storms": len(calendar),
            "cases": n,
            "issue_information_states": sum(len(information_states(u)) for u in OFFSETS) * n,
            "inputs_sha256": sources,
            "source_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in source_code},
            "outputs_sha256": {p.name: sha256(p) for p in work.iterdir()},
            "note": "Finite delivered values in main; provider/rating/boundary concerns retained for sensitivity. No p99 normalization. Optional land-state not required.",
        }
        (work / "manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {k: report[k] for k in ["status", "storms", "cases", "issue_information_states"]}
        )
    )


if __name__ == "__main__":
    main()
