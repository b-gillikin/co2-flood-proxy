"""Check synchronized uncertainty against explicit replication and missing support."""

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.dise_corrected import population, score
from src.dise_repeatability import (
    balanced_resamples,
    contrast_record,
    gauge_resamples,
    joint_multiplicities,
    regional_episodes,
)


def fixture():
    dates = pd.date_range("2024-01-01", periods=4, tz="UTC")
    rows = []
    for gauge, group in [("a1", "a"), ("a2", "a"), ("b1", "b")]:
        for k, day in enumerate(dates):
            rows.append(
                dict(
                    gauge=gauge,
                    river_group=group,
                    day=day,
                    q_observed=k + 1.0,
                    pred=k + (2 if gauge == "a1" else 5),
                    high_water=k > 1,
                )
            )
    return pd.DataFrame(rows), dates


def test_sufficient_sums_equal_explicit_paired_group_balanced_replication():
    f, calendar = fixture()
    # Unequal gauge coverage plus unequal date counts, nested a gauges stay together.
    f = f.drop(index=[0, 7]).reset_index(drop=True)
    multiplicity = np.array([[1, 1, 1, 1], [2, 0, 1, 3], [0, 0, 2, 0]])
    gs, counts, values = gauge_resamples(f, ["pred"], calendar, multiplicity)
    actual, missing = balanced_resamples(gs, counts, values, population(f))
    assert missing == 0
    for k, mult in enumerate(multiplicity):
        explicit = score(f, f.pred, population(f), mult[calendar.get_indexer(f.day)])
        np.testing.assert_allclose(actual[k, 0], [explicit[m] for m in ["mae", "rmse", "bias"]])


def test_undefined_draw_is_retained_when_a_gauge_is_not_sampled():
    f, dates = fixture()
    f = f[~(f.gauge.eq("b1") & f.day.ne(dates[0]))]
    gs, counts, values = gauge_resamples(f, ["pred"], dates, np.array([[0, 1, 1, 1]]))
    result, missing = balanced_resamples(gs, counts, values, population(f))
    assert missing == 1 and np.isnan(result).all()


def test_unsampled_nonfinite_values_do_not_poison_valid_draws():
    f, dates = fixture()
    f.loc[f.day.eq(dates[0]), "pred"] = np.nan
    gs, counts, values = gauge_resamples(f, ["pred"], dates, np.array([[0, 1, 1, 1], [1, 0, 0, 0]]))
    result, _ = balanced_resamples(gs, counts, values, population(f))
    assert np.isfinite(result[0]).all() and np.isnan(result[1]).all()


def test_moving_blocks_preserve_each_year_calendar_and_reproduce():
    calendar = pd.date_range("2023-01-01", "2024-12-31", tz="UTC")
    a = joint_multiplicities(calendar, 9, 123, 30)
    b = joint_multiplicities(calendar, 9, 123, 30)
    np.testing.assert_array_equal(a, b)
    np.testing.assert_array_equal(a[:, calendar.year == 2023].sum(axis=1), np.full(9, 365))
    np.testing.assert_array_equal(a[:, calendar.year == 2024].sum(axis=1), np.full(9, 366))
    # No gauge/model axis: every gauge and model receives the identical date draw.
    assert a.shape == (9, 731) and (a >= 0).all()


def test_joint_year_draws_share_one_constant_multiplicity_within_a_year():
    calendar = pd.date_range("2021-01-01", "2025-12-31", tz="UTC")
    mult = joint_multiplicities(calendar, 99, 123)
    counts = []
    for year in sorted(set(calendar.year)):
        part = mult[:, calendar.year == year]
        assert (part == part[:, :1]).all()
        counts.append(part[:, 0])
    np.testing.assert_array_equal(np.sum(counts, axis=0), np.full(99, 5))


def test_episode_grouping_crosses_year_boundary_and_ignores_predictions():
    f = pd.DataFrame(
        dict(
            river_group=["x"] * 3,
            day=pd.to_datetime(["2023-12-30", "2024-01-03", "2024-02-02"], utc=True),
            high_water=[True] * 3,
        )
    )
    result = regional_episodes(f, 7)
    assert len(result) == 2 and result[0]["high_water_dates"] == 2
    assert contrast_record(None, 1)["delta"] is None
    assert contrast_record(1, 2)["reduction_pct"] == 50


def test_year_influence_keeps_missing_gauge_undefined_instead_of_changing_population():
    path = Path(__file__).resolve().parents[1] / "scripts/277_assess_dise_repeatability.py"
    spec = importlib.util.spec_from_file_location("dise_repeatability_runner", path)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    f, _ = fixture()
    f["q_model"] = f.pred
    f["native_rmse__H+A"] = f.pred
    f["native_rmse__H+A+E"] = f.pred
    expected = population(f)
    subset = f[f.gauge.ne("b1")]
    result = runner.paired_rows(
        subset, ["native_rmse__H+A", "native_rmse__H+A+E"], {}, expected=expected
    )
    assert all(r["status"] == "undefined" and r["missing_population"] == ["b1"] for r in result)
