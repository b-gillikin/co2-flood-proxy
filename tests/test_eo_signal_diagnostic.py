"""Falsification and chronology checks for model-specific diagnostic probes."""

import numpy as np
import pandas as pd

from src.eo_comparison import load_script
from src.eo_signal_diagnostic import (
    chronology,
    kernel_predictions,
    kernels,
    partial_rank_correlation,
    readout_fold,
    seasonal_sources,
    transform_pair,
    validation_splits,
)


def test_train_only_scaling_retains_zero_and_ignores_unknown_columns():
    train = np.array([[0.0, np.nan], [2.0, np.nan]])
    a, b = transform_pair(train, np.array([[1.0, 1e9]]))
    aa, bb = transform_pair(train, np.array([[1e9, -1e9]]))
    np.testing.assert_array_equal(a, aa)
    np.testing.assert_allclose(a[:, 0], [-1.0, 1.0])
    assert b.shape == (1, 1) and b[0, 0] == 0
    assert bb[0, 0] > 1


def test_closed_year_boundary_uses_explicit_time_units_and_storm_closure():
    times = pd.Series(
        pd.to_datetime(["2020-12-30T00:00Z", "2020-12-31T12:00Z", "2021-01-01T00:00Z"])
    )
    ends = pd.Series(
        pd.to_datetime(["2020-12-31T10:00Z", "2020-12-31T14:00Z", "2021-01-01T01:00Z"])
    )
    actual = chronology(
        times.dt.as_unit("us"), ends.dt.as_unit("us"), pd.Timestamp("2021-01-01", tz="UTC")
    )
    assert actual.tolist() == [True, False, False]


def test_seasonal_null_preserves_training_quarters_and_never_reads_test_vectors():
    quarter = np.arange(40) % 4
    train, test = np.arange(32), np.arange(32, 40)
    perm, source, relaxed = seasonal_sources(train, test, quarter, seed=7)
    np.testing.assert_array_equal(quarter[perm], quarter[train])
    np.testing.assert_array_equal(quarter[source], quarter[test])
    assert set(perm) == set(train) and set(source) <= set(train)
    assert not relaxed.any()


def test_probe_detects_planted_signal_and_zero_weight_is_exact_ground_control():
    rng = np.random.default_rng(13)
    e = rng.normal(size=(120, 4))
    g = np.zeros((120, 1))
    y = np.repeat((10 + 2 * e[:, 0])[:, None], 24, axis=1)
    train, test = np.arange(100), np.arange(100, 120)
    parts = kernels(g, e, train, test)
    base = kernel_predictions(parts, y[train], [0], [0.001])[(0.0, 0.001)]
    actual = kernel_predictions(parts, y[train], [1], [0.001])[(1.0, 0.001)]
    assert np.mean(np.abs(actual - y[test])) < 0.05
    assert np.mean(np.abs(base - y[test])) > 1
    poisoned = list(parts)
    poisoned[2], poisoned[3] = np.ones_like(parts[2]) * 1e9, np.ones_like(parts[3]) * 1e9
    np.testing.assert_allclose(
        kernel_predictions(poisoned, y[train], [0], [0.001])[(0.0, 0.001)], base
    )


def test_nested_readout_never_tunes_or_fits_on_outer_test_labels():
    rng = np.random.default_rng(21)
    g, e = rng.normal(size=(30, 3)), rng.normal(size=(30, 4))
    y = np.repeat((5 + g[:, 0] + e[:, 0])[:, None], 24, axis=1)
    train, test = np.arange(20), np.arange(20, 30)
    validation = [(np.arange(10), np.arange(10, 20))]
    cfg = dict(permutations=2, alphas=[0.01, 1.0], eo_weights=[0.0, 1.0])
    args = (g, e, y, train, train, test, validation, validation, np.arange(30) % 4, cfg)
    prediction, parameters, source = readout_fold(*args, seed=7)
    changed = y.copy()
    changed[test] = 1e9
    result, alternate, _ = readout_fold(g, e, changed, *args[3:], seed=7)
    assert parameters == alternate
    np.testing.assert_array_equal(prediction, result)
    assert (source < 20).all()


def test_eo_absence_is_not_a_fake_fitted_augmented_model():
    g = np.arange(20, dtype=float)[:, None]
    e = np.full((20, 4), np.nan)
    y = np.repeat((1 + g), 24, axis=1)
    cfg = dict(permutations=2, alphas=[1.0], eo_weights=[0.0, 1.0])
    pred, parameters, sources = readout_fold(
        g,
        e,
        y,
        np.arange(10),
        np.array([], int),
        np.arange(10, 20),
        [],
        [],
        np.arange(20) % 4,
        cfg,
        seed=7,
    )
    assert np.isfinite(pred[0]).all() and np.isnan(pred[1:]).all()
    assert [p["arm"] for p in parameters] == ["ground_full"]
    assert (sources == -1).all()


def test_inner_validation_keeps_only_completed_earlier_years():
    times = pd.Series(pd.date_range("2018-01-01", periods=36, freq="MS", tz="UTC"))
    ends = times + pd.Timedelta(hours=12)
    years = times.dt.year.to_numpy()
    for training, held in validation_splits(times, ends, years, np.arange(36)):
        assert years[training].max() < years[held].min()
        assert len(held) == 12


def test_partial_association_detects_signal_after_nuisance_control_without_pair_pvalues():
    rng = np.random.default_rng(8)
    season = rng.normal(size=500)
    target = rng.normal(size=500)
    distance = target + 3 * season + rng.normal(scale=0.01, size=500)
    coefficient, count = partial_rank_correlation(distance, target, season[:, None])
    assert coefficient > 0.8 and count == 500


def test_raw_model_reader_handles_read_only_arrow_arrays_and_real_zero_vectors(
    tmp_path, monkeypatch
):
    run = load_script("164_diagnose_eo_signal.py", "signal_reader_fixture")
    monkeypatch.setattr(run, "ROOT", tmp_path)
    path = (
        tmp_path / "results/eo_catchment_representations/coherent_v1/selected/census/croma.parquet"
    )
    path.parent.mkdir(parents=True)
    pd.DataFrame(
        dict(
            context_id=["c"] * 8,
            catchment_gauge=list("abcdefgh"),
            kind=["recent"] * 8,
            observed_mean_fraction=[1.0] * 8,
            e0000=[0.0, 1, 2, 3, 4, 5, 6, 7],
            e0001=[0.0, 1, 1, 1, 1, 1, 1, 1],
        )
    ).to_parquet(path)
    run.STATE.clear()
    run.STATE["meta"] = pd.DataFrame(
        dict(recent_context_id=["c"] * 8, catchment_gauge=list("abcdefgh"))
    )
    values, coverage, valid, _ = run.raw_features("croma", "recent")
    assert values.shape == (1, 8, 2) and coverage.shape == (1, 8)
    assert valid.tolist() == [[False, True, True, True, True, True, True, True]]
    assert np.isnan(values[0, 0]).all()
