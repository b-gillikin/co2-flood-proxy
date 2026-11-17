"""Audit regressions: complete calendars, honest populations, clocks and references."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.dise_corrected import (
    add_climate,
    choose_donor,
    donor_fdc_apply,
    donor_fdc_fit,
    fdc_apply,
    fdc_fit,
    fit_candidate,
    population,
    score,
    split_masks,
    year_bootstrap,
)


def test_january_one_is_valid_with_prior_predictor_history():
    f = pd.DataFrame(
        dict(
            day=pd.to_datetime(["2019-12-31", "2020-01-01", "2021-01-01"], utc=True),
            river_group="A",
            gauge="a",
            q_observed=1.0,
            q_model=1.0,
        )
    )
    tr, va, te = split_masks(f, 2021)
    assert tr.tolist() == [True, False, False]
    assert va.tolist() == [False, True, False]
    assert te.tolist() == [False, False, True]


def test_missing_site_and_nonfinite_predictions_do_not_change_population():
    f = pd.DataFrame(dict(gauge=["a", "b"], river_group=["A", "B"], q_observed=[10.0, 10.0]))
    expected = population(f)
    assert score(f, [11, 20], expected)["mae"] == 5.5
    missing = score(f.iloc[:1], [11], expected)
    assert missing["mae"] is None and missing["missing_gauges"] == ["b"]
    assert score(f, [11, np.nan], expected)["status"] == "undefined"


def test_climate_is_past_for_every_row_and_never_uses_discharge():
    f = pd.DataFrame(
        dict(
            day=pd.to_datetime(["2018-01-01", "2019-01-01", "2020-01-01"], utc=True),
            gauge="a",
            q_observed=[1.0, 2.0, 3.0],
        )
    )
    weather = pd.DataFrame(
        dict(
            day=pd.to_datetime(["2017-01-01", "2018-01-01", "2019-01-01", "2021-01-01"], utc=True),
            gauge="a",
            h_precip_m=[1.0, 3.0, 5.0, 100.0],
            h_temp_k=[270.0, 280.0, 290.0, 999.0],
        )
    )
    xy = {"a": dict(latitude=50.0, longitude=6.0)}
    a = add_climate(f, 2021, xy, weather)
    np.testing.assert_allclose(a.a_past_precip_mean_m, [1, 2, 3])
    weather.loc[weather.day.dt.year.eq(2021), "h_precip_m"] = 1e9
    f.q_observed = 1e8
    b = add_climate(f, 2021, xy, weather)
    np.testing.assert_array_equal(a.a_past_precip_mean_m, b.a_past_precip_mean_m)


def test_donor_uses_common_vintage_attributes_not_target_labels():
    f = pd.DataFrame(
        dict(
            gauge=["a", "b", "t"] * 2,
            river_group=["A", "B", "T"] * 2,
            day=pd.to_datetime(["2020-01-01"] * 3 + ["2021-01-01"] * 3, utc=True),
            a_area=[1.0, 10.0, 2.0] * 2,
            q_observed=[2.0, 20.0, 999.0] * 2,
        )
    )
    past = (f.day.dt.year.eq(2020) & f.gauge.ne("t")).to_numpy()
    d, _ = choose_donor(f, past, "t", ["a_area"])
    f.loc[f.gauge.eq("t"), "q_observed"] = 1e10
    assert choose_donor(f, past, "t", ["a_area"])[0] == d == "a"


def test_calibration_zero_and_positive_tail_and_donor_scale_transfer():
    curves = fdc_fit([0, 1, 2], [0, 2, 4], [1, 1, 1])
    np.testing.assert_allclose(fdc_apply(curves, [0, 4], [1, 1]), [0, 8])
    transferred = donor_fdc_fit([1, 2], [2, 4], [1, 1], [10, 20], [1, 1])
    np.testing.assert_allclose(donor_fdc_apply(transferred, [10, 100], [1, 1]), [20, 200])


def test_bootstrap_reuses_blocks_and_counts_undefined_draws():
    f = pd.DataFrame(
        dict(
            gauge=["a", "b"],
            river_group=["A", "B"],
            q_observed=[10.0, 10.0],
            block_year=[2021, 2022],
        )
    )
    draws, mult, blocks = year_bootstrap(
        f, {"x": [11, 20], "y": [12, 19]}, population(f), draws=40, seed=7
    )
    assert blocks == [2021, 2022] and mult.shape == (40, 2)
    assert draws.isna().any(axis=1).any() and draws.notna().all(axis=1).any()
    single, _, _ = year_bootstrap(f.iloc[:1], {"x": [11]}, population(f.iloc[:1]), draws=10)
    assert single.isna().all().all()


def test_native_early_stopping_matches_reported_discharge_rmse():
    train = pd.DataFrame(
        dict(
            gauge="a",
            river_group="A",
            h_x=np.arange(30),
            q_model=np.linspace(1, 3, 30),
            q_observed=np.linspace(2, 5, 30),
        )
    )
    valid = train.iloc[-8:].copy()
    model, cols, record = fit_candidate(
        train.iloc[:22],
        valid,
        ["h_x"],
        dict(max_depth=2, learning_rate=0.1, min_child_weight=1),
        tree_limit=60,
    )
    assert model.best_score == pytest.approx(record["validation_rmse"], abs=1e-5)
    assert record["selection_score"] == record["validation_rmse"]
