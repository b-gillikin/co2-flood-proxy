#!/usr/bin/env python3
"""Build rainfall-defined storms and all eight gauge responses, including nonresponses."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.event_study import assign_eras, era_thresholds

OUT = ROOT / "results/storm_response"
HOUR = pd.Timedelta(hours=1)
GERMAN = {"herzogenrath_1": "2828300000200", "randerath": "2828900000200"}


def load_script(filename, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_hourly(path):
    frame = pd.read_csv(path, index_col=0)
    frame.index = pd.to_datetime(frame.index, utc=True)
    if frame.index.has_duplicates or not frame.index.is_monotonic_increasing:
        raise ValueError(f"Unordered/duplicate timestamps: {path}")
    return frame


def storm_catalogue(rain, dry_hours=12, minimum_mm=10):
    """Missing core cells break certainty; observed dry hours alone separate storms."""
    if not rain.index.equals(pd.date_range(rain.index[0], rain.index[-1], freq="h")):
        raise ValueError("Storm detection requires the complete hourly grid")
    complete = rain.notna().all(axis=1)
    wet = rain.ge(0.2).any(axis=1) & complete
    wet_positions = np.flatnonzero(wet)
    rows = []
    if not len(wet_positions):
        return pd.DataFrame()
    group_start = 0
    for k in range(1, len(wet_positions) + 1):
        finish = k == len(wet_positions)
        if not finish:
            previous, current = wet_positions[k - 1], wet_positions[k]
            finish = (
                current - previous - 1 >= dry_hours
                or not complete.iloc[previous + 1 : current].all()
            )
        if not finish:
            continue
        first, last = wet_positions[group_start], wet_positions[k - 1]
        block = rain.iloc[first : last + 1]
        totals = block.sum(min_count=len(block))
        before = complete.iloc[max(0, first - dry_hours) : first]
        after = complete.iloc[last + 1 : last + 1 + dry_hours]
        # Boundary truncation also means the true episode extent is uncertain.
        certain = (
            len(before) == dry_hours and before.all() and len(after) == dry_hours and after.all()
        )
        if totals.max() >= minimum_mm:
            n_catchments = int(totals.ge(10).sum())
            start, end = rain.index[first], rain.index[last]
            rows.append(
                {
                    "storm_id": f"rain|{start.isoformat()}",
                    "start_utc": start,
                    "end_utc": end,
                    "landmark_utc": start + 5 * HOUR,
                    "duration_h": last - first + 1,
                    "max_catchment_rain_mm": totals.max(),
                    "n_core_catchments_ge10mm": n_catchments,
                    "footprint": "broad"
                    if n_catchments >= 4
                    else "local"
                    if n_catchments <= 2
                    else "mixed",
                    "boundary_known": bool(certain),
                    "dry_separation_h": dry_hours,
                }
            )
        group_start = k
    return pd.DataFrame(rows)


def sum_complete(series):
    return float(series.sum()) if len(series) and series.notna().all() else np.nan


def response_metrics(values, baseline, landmark, scale):
    """Only complete windows define exact maxima, duration and excess volume proxies."""
    values = np.asarray(values, float)
    if (
        not np.isfinite(values).all()
        or not np.isfinite([baseline, landmark, scale]).all()
        or scale <= 0
    ):
        return {
            k: np.nan
            for k in [
                "peak_gain_72h",
                "peak_ratio_72h",
                "peak_hour",
                "hours_above_p99",
                "mean_excess_72h",
            ]
        }
    return {
        "peak_gain_72h": float((values.max() - landmark) / scale),
        "peak_ratio_72h": float(values.max() / scale),
        "peak_hour": int(values.argmax() + 1),
        "hours_above_p99": int((values > scale).sum()),
        "mean_excess_72h": float(np.maximum(values - baseline, 0).mean() / scale),
    }


def load_sources(hashes):
    cohort = pd.read_csv(ROOT / "config/event_study_cohort.csv")
    paths = [
        ROOT / p
        for p in [
            "config/event_study_cohort.csv",
            "data/interim/event_study_discharge_hourly.csv",
            "data/interim/radolan_catchment_hourly.csv",
            "data/interim/event_study_rating_eras.csv",
            "data/processed/waterschap_station_source_qa.csv",
            "config/lanuk_rating_periods.csv",
        ]
    ]
    q = read_hourly(paths[1])
    rain = read_hourly(paths[2])[cohort.watercourse].copy()
    rain.columns = cohort.gauge
    time = rain.index
    q = q.reindex(time)
    eras = pd.read_csv(paths[3])
    qa = pd.read_csv(paths[4]).set_index("series_key")
    warning = load_script("86_analyse_warning_threshold_progression.py", "storm_warning")
    german = load_script("72_german_wurm_analogue_extension.py", "storm_german")
    labels, scales, domain, strict = {}, {}, {}, {}
    for g in cohort.gauge:
        table = eras[eras.gauge.eq(g)]
        labels[g] = assign_eras(time, table)
        _, scales[g] = era_thresholds(q[g], labels[g])
        upper = labels[g].map(table.drop_duplicates("era_id").set_index("era_id").domain_max_m3s)
        domain[g] = q[g].notna() & labels[g].notna() & q[g].le(upper.fillna(np.inf))
        strict[g] = warning.reliable_mask(q[g], g, eras, qa, 26.0)
    periods = german.read_periods()
    metadata = cohort.assign(
        country="NL", physical_river=cohort.watercourse.replace({"Worm": "Wurm/Worm"})
    )[["gauge", "watercourse", "station", "country", "physical_river"]]
    for folder, (g, name) in german.STATIONS.items():
        found = {}
        for parameter, pattern in [
            ("Abfluss", "*abfluss_mit_m_s_csv_export_mittelwerte_15minuten*.csv"),
            ("Wasserstand", "*wasserstand_mit_cm_csv_export_mittelwerte_15minuten*.csv"),
        ]:
            (path,) = (german.SOURCE / folder).glob(pattern)
            paths.append(path)
            found[parameter] = german.complete_hourly(
                german.read_quarters(path, g, name, parameter)
            )
        table = periods[periods.station.eq(folder)]
        full_era = assign_eras(found["Abfluss"].index, table)
        _, full_scale = era_thresholds(found["Abfluss"], full_era)
        q[g] = found["Abfluss"].reindex(time)
        scales[g] = full_scale.reindex(time)
        labels[g] = assign_eras(time, table.assign(era_id=table.period_id))
        d = q[g].notna() & labels[g].notna()
        for row in table.itertuples():
            selected = labels[g].eq(row.period_id).fillna(False)
            stage = found["Wasserstand"].reindex(time)
            valid = q[g].between(row.domain_min_m3s, row.domain_max_m3s) & stage.between(
                row.stage_min_cm, row.stage_max_cm
            )
            d &= ~selected | valid
        domain[g] = d
        strict[g] = d & (time < german.PROVISIONAL_START)
        metadata.loc[len(metadata)] = [g, "Wurm", name, "DE", "Wurm/Worm"]
    path = ROOT / "results/basin_ai_cross_border_completion/german_catchment_hourly_rainfall.csv"
    paths.append(path)
    de_rain = read_hourly(path).rename(columns=GERMAN)
    rain = rain.join(de_rain)
    for path in paths:
        hashes[str(path.relative_to(ROOT))] = sha256(path)
    return (
        q,
        rain,
        pd.DataFrame(scales),
        pd.DataFrame(labels),
        pd.DataFrame(domain),
        pd.DataFrame(strict),
        metadata,
    )


def spatial_rainfall(hashes, out):
    """Exact existing geometry weights; cache bound to every held crop and source."""
    import geopandas as gpd

    cross = load_script("84_complete_cross_border_analogues.py", "storm_cross")
    manifest_path = ROOT / "data/raw/radolan_rw/manifest.json"
    geometry = ROOT / "data/interim/foundation_model_catchments.gpkg"
    manifest = json.loads(manifest_path.read_text())
    paths = [manifest_path, geometry, *sorted((manifest_path.parent / "crops").glob("*_rw_*.npz"))]
    fingerprints = {str(p.relative_to(ROOT)): sha256(p) for p in paths}
    hashes.update(fingerprints)
    cache, receipt = out / "spatial_rain_hourly.parquet", out / "spatial_receipt.json"
    code_hash = sha256(__file__)
    if receipt.exists() and cache.exists():
        old = json.loads(receipt.read_text())
        if (
            old["inputs"] == fingerprints
            and old["code"] == code_hash
            and old["output"] == sha256(cache)
        ):
            return pd.read_parquet(cache)
    catchments = gpd.read_file(geometry)
    catchments = catchments[catchments.experiment_role.ne("inventory")].copy()
    catchments["gauge"] = catchments.gauge.replace(GERMAN)
    weights = cross.radar_weights(catchments, manifest).reshape(len(catchments), -1)
    rows = []
    for path in paths[2:]:
        month = path.stem.rsplit("_", 1)[-1]
        if (
            fingerprints[str(path.relative_to(ROOT))]
            != manifest["months"][month[:4] + "-" + month[4:6]]["crop_sha256"]
        ):
            raise ValueError(f"Radar checksum changed: {path}")
        with np.load(path) as data:
            values = data["rain_0p1mm"].reshape(len(data["end_utc"]), -1).astype(float) / 10
            ends = pd.DatetimeIndex(data["end_utc"]).tz_localize("UTC").ceil("h")
        missing = values < 0
        values[missing] = 0
        means = values @ weights.T
        variances = np.maximum((values**2) @ weights.T - means**2, 0)
        wet_area = (values >= 0.2).astype(float) @ weights.T
        incomplete = missing.astype(float) @ (weights > 0).T.astype(float) > 0
        cv = np.sqrt(variances) / np.where(means > 0, means, 1)
        for k, gauge in enumerate(catchments.gauge):
            frame = pd.DataFrame(
                {
                    "timestamp_utc": ends,
                    "gauge": gauge,
                    "mean_mm": means[:, k],
                    "wet_area": wet_area[:, k],
                    "spatial_cv": cv[:, k],
                }
            )
            frame.loc[incomplete[:, k], ["mean_mm", "wet_area", "spatial_cv"]] = np.nan
            rows.append(frame)
    result = pd.concat(rows, ignore_index=True).sort_values(["gauge", "timestamp_utc"])
    if result.duplicated(["gauge", "timestamp_utc"]).any():
        raise ValueError("Duplicate spatial radar hours")
    result.to_parquet(cache, index=False)
    receipt.write_text(
        json.dumps({"inputs": fingerprints, "code": code_hash, "output": sha256(cache)}, indent=2)
        + "\n"
    )
    return result


def build_responses(storms, q, rain, scales, periods, domain, strict, metadata, spatial):
    rows, histories = [], []
    spatial = {g: x.set_index("timestamp_utc") for g, x in spatial.groupby("gauge")}
    for storm in storms.itertuples():
        first, cutoff = storm.start_utc, storm.landmark_utc
        for site in metadata.itertuples():
            g = site.gauge
            before = first - HOUR
            outcome_dates = pd.date_range(cutoff + HOUR, periods=72, freq="h")
            full_dates = pd.date_range(before, outcome_dates[-1], freq="h")
            scale = scales[g].reindex([cutoff]).iloc[0]
            base = q[g].reindex([before]).iloc[0]
            level = q[g].reindex([cutoff]).iloc[0]
            values = q[g].reindex(outcome_dates)
            all_q = q[g].reindex(full_dates)
            era = periods[g].reindex(full_dates)
            stable = era.notna().all() and era.nunique() == 1
            valid = bool(domain[g].reindex(full_dates).fillna(False).all())
            clean = bool(strict[g].reindex(full_dates).fillna(False).all())
            input_dates = pd.date_range(before, cutoff, freq="h")
            input_period = periods[g].reindex(input_dates)
            peer_input_ok = bool(
                storm.boundary_known
                and input_period.notna().all()
                and input_period.nunique() == 1
                and domain[g].reindex(input_dates).fillna(False).all()
                and q[g].reindex(input_dates).notna().all()
            )
            forcing_end = min(storm.end_utc, outcome_dates[-1])
            storm_rain = rain[g].loc[first:forcing_end]
            sp = spatial[g].reindex(storm_rain.index)
            total = sum_complete(storm_rain)
            # Radar geospatial summary must reproduce the held catchment means.
            spatial_total = sum_complete(sp.mean_mm)
            spatial_match = (
                np.isfinite(total)
                and np.isfinite(spatial_total)
                and abs(total - spatial_total) <= 0.0011 * len(sp)
            )
            if not spatial_match and np.isfinite(total) and np.isfinite(spatial_total):
                raise ValueError(f"Radar geometry/series mismatch: {g}, {storm.storm_id}")
            record = {**storm._asdict(), **site._asdict()}
            record.pop("Index", None)
            record.update(
                {
                    "row_id": f"{storm.storm_id}|{g}",
                    "year": first.year,
                    "warm": first.month in range(5, 11),
                    "season_sin": np.sin(2 * np.pi * first.dayofyear / 365.25),
                    "season_cos": np.cos(2 * np.pi * first.dayofyear / 365.25),
                    "forcing_duration_h": int((forcing_end - first) / HOUR) + 1,
                    "storm_continues_after_followup": storm.end_utc > outcome_dates[-1],
                    "normalizer_p99": scale,
                    "baseline_q": base,
                    "landmark_q": level,
                    "baseline_ratio": base / scale,
                    "landmark_ratio": level / scale,
                    "rise_6h": (level - base) / scale,
                    "response_fraction": values.notna().mean(),
                    "rating_period_stable": bool(stable),
                    "domain_ok": valid,
                    "measurement_concern": not clean,
                    "peer_state_usable": peer_input_ok,
                    "input_measurement_concern": not bool(
                        strict[g].reindex(input_dates).fillna(False).all()
                    ),
                    "numeric_usable": bool(
                        storm.boundary_known and stable and valid and all_q.notna().all()
                    ),
                    "rain_total_mm": total,
                    "rain_max_mm": storm_rain.max() if storm_rain.notna().all() else np.nan,
                    "wet_area": float((sp.wet_area * sp.mean_mm).sum() / spatial_total)
                    if spatial_match and spatial_total > 0
                    else np.nan,
                    "spatial_cv": float((sp.spatial_cv * sp.mean_mm).sum() / spatial_total)
                    if spatial_match and spatial_total > 0
                    else np.nan,
                    **response_metrics(values, base, level, scale),
                }
            )
            for hours in [6, 72, 168]:
                dates = (
                    pd.date_range(first - hours * HOUR, periods=hours, freq="h")
                    if hours != 6
                    else pd.date_range(first, periods=6, freq="h")
                )
                record[f"rain_{hours}h_mm"] = sum_complete(rain[g].reindex(dates))
            after_rain = rain[g].reindex(outcome_dates)
            record["rain_response_72h_mm"] = sum_complete(after_rain)
            record["rain_response_max_mm"] = (
                after_rain.max() if after_rain.notna().all() else np.nan
            )
            record["followup_end_utc"] = outcome_dates[-1]
            dates = pd.date_range(cutoff - 511 * HOUR, periods=512, freq="h")
            history = q[g].reindex(dates).to_numpy()
            record["history_complete"] = bool(np.isfinite(history).all())
            if record["history_complete"]:
                histories.append(pd.Series(history, name=record["row_id"]))
            rows.append(record)
    frame = pd.DataFrame(rows)
    next_start = storms.set_index("storm_id").start_utc.shift(-1)
    frame["next_regional_storm_utc"] = frame.storm_id.map(next_start)
    frame["followup_overlaps_next_storm"] = frame.next_regional_storm_utc.le(frame.followup_end_utc)
    return frame, pd.DataFrame(histories)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=OUT)
    parser.add_argument("--dry-hours", type=int, default=12)
    args = parser.parse_args()
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    hashes = {}
    q, rain, scale, periods, domain, strict, metadata = load_sources(hashes)
    print("Hourly sources aligned", flush=True)
    core = metadata[metadata.country.eq("NL")].gauge
    storms = storm_catalogue(rain[core], dry_hours=args.dry_hours)
    storms.to_csv(out / "storms.csv", index=False)
    storm_catalogue(rain[core], dry_hours=24).to_csv(out / "storms_24h_separation.csv", index=False)
    spatial = spatial_rainfall(hashes, out)
    print("Spatial rainfall derived", flush=True)
    rows, histories = build_responses(
        storms, q, rain, scale, periods, domain, strict, metadata, spatial
    )
    rows.to_parquet(out / "storm_gauge_responses.parquet", index=False)
    histories.to_parquet(out / "histories_512h.parquet")
    for name, frame in [
        ("discharge", q),
        ("rainfall", rain),
        ("normalizer", scale),
        ("period", periods),
        ("domain", domain),
        ("strict", strict),
    ]:
        frame.to_parquet(out / f"hourly_{name}.parquet")
    rows.groupby(["gauge", "country"]).agg(
        rows=("row_id", "size"),
        numeric=("numeric_usable", "sum"),
        complete_history=("history_complete", "sum"),
        measurement_concern=("measurement_concern", "sum"),
    ).to_csv(out / "coverage.csv")
    source_paths = [
        Path(__file__),
        ROOT / "scripts/72_german_wurm_analogue_extension.py",
        ROOT / "scripts/84_complete_cross_border_analogues.py",
        ROOT / "scripts/86_analyse_warning_threshold_progression.py",
        ROOT / "src/event_study.py",
        ROOT / "docs/limburg-storm-response-design-2026-10-15.md",
    ]
    hashes.update({str(p.relative_to(ROOT)): sha256(p) for p in source_paths})
    manifest = {
        "status": "storm catalogue and responses built; not model results",
        "input_sha256": hashes,
        "storms": len(storms),
        "gauge_rows": len(rows),
        "complete_histories": len(histories),
        "rules": {
            "wet_mm_per_h": 0.2,
            "dry_hours": args.dry_hours,
            "qualifying_mm": 10,
            "landmark_h_from_first_wet": 5,
            "response_h": 72,
        },
        "output_sha256": {
            p.name: sha256(p)
            for p in out.glob("*.parquet")
            if p.name.startswith(("hourly_", "storm_gauge", "histories_"))
        },
    }
    (out / "catalogue_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({k: v for k, v in manifest.items() if k != "input_sha256"}, indent=2))


if __name__ == "__main__":
    main()
