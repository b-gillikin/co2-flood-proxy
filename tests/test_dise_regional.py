"""Scientific invariants for the regional extension of the local feature recipe."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.dise_regional import WEATHER, fold_assignments, gauge_features, inner_masks, regional_masks


def fixture():
    days = pd.date_range("2017-12-25", "2018-01-05", tz="UTC")
    f = pd.DataFrame(
        dict(day=days, gauge="a", q_model=np.arange(len(days), dtype=float), q_observed=4.0)
    )
    for c in WEATHER.values():
        f[c] = np.arange(len(days), dtype=float)
    f["h_temp_k"] = 273.0 + np.arange(len(days))
    f["h_dewpoint_k"] = f.h_temp_k - 2
    m = pd.Series(
        dict(
            reference_area_km2=100,
            gauge_lat=50,
            gauge_lon=6,
            model_outlet_area_km2=110,
            reference_covered=0.95,
        )
    )
    a = pd.Series({"a_slope_deg": 5})
    e = pd.Series({f"A{i:02d}": i / 100 for i in range(64)})
    return f, m, a, e


def test_feature_recipe_never_uses_observed_discharge_and_keeps_prior_year_lags():
    f, m, a, e = fixture()
    x = gauge_features(f, m, a, e)
    f.q_observed = 1e8
    y = gauge_features(f, m, a, e)
    cols = [c for c in x if c.startswith(("h_", "a_", "e_"))]
    pd.testing.assert_frame_equal(x[cols], y[cols])
    assert x.iloc[0].h_q_model_lag1 == 6 and x.iloc[0].h_q_model_lag7 == 0
    assert x.iloc[0].a_past_temp_mean_k == 276


def test_calendar_holes_rejected_and_negative_accumulations_not_filled():
    f, m, a, e = fixture()
    with pytest.raises(ValueError):
        gauge_features(f.drop(index=2), m, a, e)
    f.loc[7, "h_precip_m"] = -1
    x = gauge_features(f, m, a, e)
    assert np.isnan(x.iloc[0].h_precip_m) and np.isnan(x.iloc[1].h_precip_m_lag1)


def test_folds_are_topology_grouped_deterministic_and_do_not_need_outcomes():
    assignment = fold_assignments(["A", "B", "C", "D", "A"], 4, "fixed")
    assert assignment == fold_assignments(["D", "C", "B", "A"], 4, "fixed")
    f = pd.DataFrame(
        dict(
            day=pd.to_datetime(
                ["2018-01-01", "2020-01-01", "2021-01-01", "2018-01-01", "2021-01-01"], utc=True
            ),
            gauge=["a", "a", "w", "e", "e"],
            river_group=["A", "A", "Wurm", "external:Ahr", "external:Ahr"],
            source_role=[
                "regional_donor",
                "regional_donor",
                "local",
                "reserved_external",
                "reserved_external",
            ],
            q_observed=1.0,
            q_model=2.0,
        )
    )
    tr, va, te = regional_masks(f, 2021, "Wurm")
    assert tr.tolist() == [True, False, False, False, False]
    assert va.tolist() == [False, True, False, False, False]
    assert te.tolist() == [False, False, True, False, True]
    a, b = inner_masks(f, tr, va, assignment, assignment["A"])
    assert not a.any() and b.sum() == 1


def benchmark_module(tmp_path):
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "regional_benchmark_test",
        Path(__file__).resolve().parents[1] / "scripts/272_benchmark_dise_regional_fold.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.DEST = tmp_path
    module.PLAN = dict(module.PLAN, bootstrap_draws=7)
    return module


def test_scoring_keeps_undefined_high_water_and_unknown_quality_explicit(tmp_path):
    m = benchmark_module(tmp_path)
    f = pd.DataFrame(
        dict(
            day=pd.to_datetime(["2019-01-01", "2021-01-01", "2021-01-01"], utc=True),
            gauge=["w", "w", "e"],
            q_observed=[2.0, 10.0, 10.0],
        )
    )
    p = f.iloc[1:].copy()
    p["q_model"] = 8.0
    p["station"] = p.gauge
    p["source_role"] = ["local", "reserved_external"]
    p["river_group"] = ["Wurm", "external:Ahr"]
    p["reference_area_km2"] = 100.0
    p["clean_verification"] = pd.Series([True, pd.NA], index=p.index, dtype="boolean")
    p["overlap_stratum"] = "high_overlap_proxy"
    p["location_stratum"] = "on_or_near_reference_footprint"
    for c in [
        "spatial_view_high_overlap",
        "spatial_view_location_consistent",
        "spatial_view_stress",
    ]:
        p[c] = True
    p["donor_fdc"] = 8.0
    p["local_fdc"] = 8.0
    for policy in m.PLAN["policies"]:
        for arm in m.PLAN["arms"]:
            p[f"{policy}__{arm}"] = 8.0
    m.evaluate(f, p)
    saved = pd.read_parquet(tmp_path / "predictions.parquet").set_index("gauge")
    assert pd.isna(saved.loc["e", "high_water"]) and pd.isna(saved.loc["e", "clean_verification"])
    assert saved.loc["w", "high_water"]


def test_external_donor_calibration_never_reads_target_observations(tmp_path):
    m = benchmark_module(tmp_path)
    rows = []
    for gauge, area, role in [
        ("d1", 8.0, "regional_donor"),
        ("d2", 20.0, "regional_donor"),
        ("t", 10.0, "reserved_external"),
    ]:
        for year in [2018, 2019, 2020, 2021]:
            rows.append(
                dict(
                    gauge=gauge,
                    day=pd.Timestamp(f"{year}-01-01", tz="UTC"),
                    a_area=area,
                    q_model=float(year - 2017),
                    q_observed=float(2 * (year - 2017)),
                    source_role=role,
                    source_quality="unknown",
                    clean_verification=pd.NA,
                )
            )
    f = pd.DataFrame(rows)
    train = f.day.dt.year.lt(2020).to_numpy() & f.source_role.eq("regional_donor").to_numpy()
    val = f.day.dt.year.eq(2020).to_numpy() & f.source_role.eq("regional_donor").to_numpy()
    test = f.day.dt.year.eq(2021).to_numpy() & f.source_role.eq("reserved_external").to_numpy()
    a = m.calibration(f, train, val, test)
    f.loc[f.gauge.eq("t"), "q_observed"] = 1e10
    b = m.calibration(f, train, val, test)
    pd.testing.assert_frame_equal(a, b)
    assert a.donor_fdc.notna().all() and a.local_fdc.isna().all()
