"""Scientific-clock, holdout and numerical invariants for daily reconstruction."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.dise import daily_hour_end, reconstruct, residual_target, specific_q, split_masks, weights


def test_midnight_hour_belongs_to_preceding_day_and_missing_hour_is_not_filled():
    t = pd.date_range("2021-07-14 01:00", periods=48, freq="h", tz="UTC")
    x = pd.DataFrame({"Q": np.r_[np.zeros(23), 24, np.ones(24)]}, index=t)
    q, n = daily_hour_end(x)
    assert q.loc["2021-07-14", "Q"] == 1  # midnight peak is in July 14.
    assert q.loc["2021-07-15", "Q"] == 1
    x.loc[t[12], "Q"] = np.nan
    q, n = daily_hour_end(x)
    assert np.isnan(q.loc["2021-07-14", "Q"])
    assert n.loc["2021-07-14", "Q"] == 23


def test_true_zeros_retain_identity_under_specific_q_and_log_correction():
    qo = specific_q([0, 1, 20], 86.4)
    qm = specific_q([0, 2, 10], 86.4)
    result, _ = reconstruct(qm, residual_target(qo, qm))
    np.testing.assert_allclose(result, qo)
    assert result[0] == 0
    with pytest.raises(ValueError):
        specific_q([1], 0)


def test_all_wurm_sites_are_absent_from_training_and_early_stopping():
    x = pd.DataFrame({"day": pd.to_datetime(["2018-06-01", "2019-06-01", "2020-06-01", "2021-07-14"] * 2, utc=True),
                      "river_group": ["Geul"] * 4 + ["Wurm"] * 4,
                      "q_observed": 1.0, "q_model": 1.0})
    tr, va, te = split_masks(x, 2021, "Wurm")
    assert tr.sum() == 2 and va.sum() == 1 and te.sum() == 1
    assert not x.loc[tr | va, "river_group"].eq("Wurm").any()
    x.loc[x.river_group.eq("Wurm"), "q_observed"] = 1e6
    changed = split_masks(x, 2021, "Wurm")
    for a, b in zip((tr, va, te), changed, strict=True):
        np.testing.assert_array_equal(a, b)


def test_river_weights_do_not_triple_count_three_nested_wurm_gauges():
    x = pd.DataFrame({"river_group": ["Wurm"] * 6 + ["Geul"] * 2,
                      "gauge": ["a", "a", "b", "b", "c", "c", "d", "d"]})
    x["weight"] = weights(x)
    total = x.groupby("river_group").weight.sum()
    assert total.Wurm == pytest.approx(total.Geul)


def test_fitted_model_survives_save_reload_in_pinned_environment(tmp_path):
    from xgboost import XGBRegressor
    x = np.arange(20, dtype=float).reshape(-1, 1)
    model = XGBRegressor(n_estimators=3, max_depth=2, n_jobs=1).fit(x, x[:, 0] / 10)
    path = tmp_path / "model.json"
    model.save_model(path)
    restored = XGBRegressor()
    restored.load_model(path)
    np.testing.assert_array_equal(model.predict(x), restored.predict(x))
