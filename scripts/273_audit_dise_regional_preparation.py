"""Check actual assembled clocks, units, recipe parity and withheld populations."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
import pandas as pd

from src.dise import feature_columns
from src.dise_regional import WEATHER, gauge_features, inner_masks, regional_masks
from src.geoglows_experiment import sha, write_json


def main():
    plan = json.loads((ROOT / "config/limburg_dise_regional_benchmark_v1.json").read_text())
    out = ROOT / plan["output"] / "preparation"
    f = pd.read_parquet(out / "features.parquet")
    manifest = json.loads((out / "manifest.json").read_text())
    assert sha(out / "features.parquet") == manifest["feature_sha256"]
    assert (
        len(f) == 394 * 2922
        and f.gauge.nunique() == 394
        and not f.duplicated(["gauge", "day"]).any()
    )
    assert (
        f.groupby("gauge")
        .day.agg(["min", "max"])["min"]
        .eq(pd.Timestamp("2018-01-01", tz="UTC"))
        .all()
    )
    assert np.allclose(f.q_model * f.reference_area_km2 / 86.4, f.q_model_m3s, equal_nan=True)
    assert np.allclose(f.q_observed * f.reference_area_km2 / 86.4, f.q_observed_m3s, equal_nan=True)
    tr, va, te = regional_masks(f, plan["test_year"], plan["withheld_local_group"])
    folds = json.loads((out / "inner_folds.json").read_text())
    fold_counts = []
    for fold in range(plan["inner_folds"]):
        a, b = inner_masks(f, tr, va, folds, fold)
        assert a.any() and b.any()
        assert not f.loc[a | b, "source_role"].eq("reserved_external").any()
        assert not f.loc[a | b, "river_group"].eq("Wurm").any()
        fold_counts.append(
            dict(
                fold=fold,
                train_rows=int(a.sum()),
                validation_rows=int(b.sum()),
                groups=int(f.loc[b, "river_group"].nunique()),
            )
        )
    # Rebuild every local gauge from the old raw tables using the new shared
    # recipe, then compare every predictor, not just a mirrored toy calculation.
    daily = pd.read_parquet(ROOT / "results/limburg_dise_v1/daily_reference.parquet")
    daily = daily.loc[daily.day.ge("2017-01-01")]
    weather = pd.concat(
        [
            pd.read_parquet(ROOT / f"data/raw/limburg_dise_v1/weather/local_daily_{y}.parquet")
            for y in range(2017, 2026)
        ],
        ignore_index=True,
    ).rename(columns=WEATHER)
    attrs = pd.read_parquet(
        ROOT / "data/raw/limburg_dise_v1/local_attributes_v2.parquet"
    ).set_index("gauge")
    mapping = {
        r["gauge"]: r for r in json.loads((ROOT / plan["local_mapping"]).read_text()) if r["mapped"]
    }
    local_source = pd.read_parquet(ROOT / plan["local_features"])
    sites = {
        r["gauge"]: r
        for r in json.loads((ROOT / "config/limburg_geoglows_stages12_v2.json").read_text())[
            "sites"
        ]
    }
    predictors = feature_columns(local_source, "H+A+E")
    max_delta = 0.0
    for gauge, old in local_source.groupby("gauge"):
        before = daily.loc[daily.gauge.eq(gauge), ["gauge", "day", "q_model", "q_observed"]].merge(
            weather.loc[weather.gauge.eq(gauge), ["gauge", "day", *WEATHER.values()]],
            on=["gauge", "day"],
            validate="one_to_one",
        )
        m = pd.Series(
            dict(
                reference_area_km2=sites[gauge]["reference_area_km2"],
                gauge_lat=sites[gauge]["latitude"],
                gauge_lon=sites[gauge]["longitude"],
                model_outlet_area_km2=mapping[gauge]["model_outlet_area_km2"],
                reference_covered=mapping[gauge]["held_area_covered_fraction"],
            )
        )
        embedding = pd.Series({f"A{i:02d}": old.iloc[0][f"e_A{i:02d}"] for i in range(64)})
        new = gauge_features(before, m, attrs.loc[gauge], embedding)
        old = old.sort_values("day")
        assert old.day.reset_index(drop=True).equals(new.day)
        a, b = old[predictors].to_numpy(float), new[predictors].to_numpy(float)
        assert np.allclose(a, b, rtol=1e-11, atol=1e-10, equal_nan=True)
        max_delta = max(max_delta, float(np.nanmax(np.abs(a - b))))
    # Check past-only regional climate on every gauge/year, including the first
    # year with only 2017 warm-up and later years with no target Q verification.
    regional_weather = pd.read_parquet(ROOT / plan["regional_inputs"] / "weather.parquet").rename(
        columns=WEATHER
    )
    regional_weather.h_precip_m = regional_weather.h_precip_m.where(
        regional_weather.h_precip_m.ge(0)
    )
    for year in range(2018, 2026):
        p = (
            regional_weather.loc[regional_weather.day.lt(f"{year}-01-01")]
            .groupby("gauge")
            .agg(
                a_past_precip_mean_m=("h_precip_m", "mean"),
                a_past_temp_mean_k=("h_temp_k", "mean"),
                a_past_temp_sd_k=("h_temp_k", "std"),
            )
        )
        got = (
            f.loc[f.source_role.ne("local") & f.day.eq(pd.Timestamp(f"{year}-01-01", tz="UTC"))]
            .set_index("gauge")
            .reindex(p.index)
        )
        assert np.allclose(got[p.columns], p, rtol=1e-10, atol=1e-9, equal_nan=True)
    missing = f[predictors].isna().sum()
    mapping_frame = pd.read_parquet(ROOT / plan["spatial_register"])
    targets = (
        mapping_frame.loc[mapping_frame.resolved_role.eq("reserved_external"), "gauge_id"].tolist()
        + f.loc[f.river_group.eq("Wurm"), "gauge"].unique().tolist()
    )
    coverage = (
        f.loc[f.day.dt.year.eq(plan["test_year"]) & f.gauge.isin(targets)]
        .groupby(["gauge", "source_role", "river_group"])
        .agg(calendar_days=("day", "size"), verified_available_days=("q_observed", "count"))
    )
    coverage.to_csv(out / "test_coverage.csv")
    report = dict(
        status="regional_preparation_audit_passed",
        rows=len(f),
        gauges=int(f.gauge.nunique()),
        predictors=len(predictors),
        feature_bytes=(out / "features.parquet").stat().st_size,
        local_recipe_parity_gauges=7,
        maximum_local_recipe_difference=max_delta,
        past_only_climate_verified_all_regional_gauge_years=True,
        common_predictor_missing_cells=int(missing.sum()),
        missing_predictors=missing.loc[missing.gt(0)].to_dict(),
        inner_folds=fold_counts,
        train_rows=int(tr.sum()),
        validation_rows=int(va.sum()),
        test_rows=int(te.sum()),
        no_outer_target_or_external_labels_in_fitting=True,
        requested_test_gauges=len(targets),
        contributing_test_gauges=int(f.loc[te, "gauge"].nunique()),
        no_verification_gauges=coverage.loc[coverage.verified_available_days.eq(0)]
        .reset_index()
        .gauge.tolist(),
        feature_sha256=sha(out / "features.parquet"),
        executed_audit_sha256=sha(Path(__file__)),
    )
    write_json(out / "audit.json", report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
