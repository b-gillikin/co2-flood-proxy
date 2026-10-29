import numpy as np

from src.eo_individual_features import Moments, channel_features, grid_weights, texture
from src.eo_individual_readout import conditional_parts, encoded_fold, fit_grid


def test_streaming_moments_match_direct_weighted_pixels_and_resume():
    x = np.array([[1.0, 2.0], [3.0, np.nan], [8.0, 6.0]])
    w = np.array([1.0, 2.0, 3.0])
    a = Moments.empty(2)
    a.add(x[:2], w[:2])
    a = Moments.from_arrays(a.arrays())
    a.add(x[2:], w[2:])
    expected = []
    sd = []
    for i in range(2):
        ok = np.isfinite(x[:, i])
        mean = np.average(x[ok, i], weights=w[ok])
        expected.append(mean)
        sd.append(np.sqrt(np.average((x[ok, i] - mean) ** 2, weights=w[ok])))
    np.testing.assert_allclose(a.output(), expected + sd)


def test_absent_rgb_does_not_create_indices_and_area_is_conserved():
    channels, names = channel_features(np.ones((6, 4, 4)), ["B5", "B6", "B7", "B8", "B11", "B12"])
    assert "NDVI" not in names and "MNDWI" not in names and "NDRE" in names
    assert channels.shape[0] == 8
    weights = np.arange(16).reshape(4, 4)
    assert grid_weights(weights, (2, 2)).sum() == weights.sum()


def test_texture_never_uses_missing_neighbours():
    x = np.ones((1, 3, 3))
    valid = np.ones((3, 3), bool)
    valid[1, 1] = False
    first = texture(x, valid, np.ones((3, 3)))
    x[:, 1, 1] = 1e99
    np.testing.assert_allclose(texture(x, valid, np.ones((3, 3))), first, equal_nan=True)
    assert np.isnan(first[[1, 3]]).all()


def test_residual_can_reduce_baseline_and_matches_direct_weighted_ridge():
    rng = np.random.default_rng(42)
    n = 12
    ground = rng.normal(size=(n, 2))
    raw = rng.normal(size=(n, 3))
    eo = rng.normal(size=(n, 2))
    z = rng.normal(size=(n, 2))
    train = np.arange(8)
    test = np.arange(8, 12)
    w = np.arange(1, 9, dtype=float)
    base = np.full((n, 2), 10.0)
    y = base - 2
    pred = fit_grid(ground, raw, eo, z, y, base, train, test, w, [1.0], [0.0])[0.0, 1.0]
    np.testing.assert_allclose(pred, 8.0)
    # Pure kernel solution with a weighted intercept for nonconstant residuals.
    y = rng.normal(size=(n, 2)) + base
    parts = conditional_parts(ground, raw, eo, z, train, test, w)
    q = w / w.sum()
    sw = np.sqrt(q)
    mean = (q[:, None] * (y[train] - base[train])).sum(0)
    k = parts[0] + 0.1 * parts[2]
    cross = parts[1] + 0.1 * parts[3]
    coef = np.linalg.solve(
        k * sw[:, None] * sw[None, :] + 0.01 * np.eye(len(train)),
        sw[:, None] * (y[train] - base[train] - mean),
    )
    expected = np.maximum(base[test] + (cross * sw[None, :]) @ coef + mean, 0)
    got = fit_grid(ground, raw, eo, z, y, base, train, test, w, [0.01], [0.1])[0.1, 0.01]
    np.testing.assert_allclose(got, expected, rtol=1e-10, atol=1e-10)


def test_future_outcomes_cannot_change_predictions_and_zero_eo_is_exact_raw():
    rng = np.random.default_rng(3)
    n = 16
    g = rng.normal(size=(n, 2))
    r = rng.normal(size=(n, 3))
    e = rng.normal(size=(n, 4))
    z = rng.normal(size=(n, 2))
    b = np.full((n, 2), 8.0)
    y = b.copy()
    raw = b.copy()
    train = np.arange(12)
    test = np.arange(12, 16)
    val = [(np.arange(6), np.arange(6, 12))]
    avail = np.ones(n, bool)
    pred, param = encoded_fold(g, r, e, z, y, b, raw, train, test, val, np.ones(n), avail, avail)
    assert param["parameters"] == "raw_only"
    np.testing.assert_array_equal(pred, raw[test])
    a = fit_grid(g, r, e, z, y, b, train, test, np.ones(len(train)), [1.0], [0.1])[0.1, 1.0]
    y[test] = 1e99
    c = fit_grid(g, r, e, z, y, b, train, test, np.ones(len(train)), [1.0], [0.1])[0.1, 1.0]
    np.testing.assert_array_equal(a, c)


def test_prequential_folds_purge_cross_year_storms_and_ignore_future_labels():
    from src.eo_individual_readout import prequential_heads

    rng = np.random.default_rng(41)
    n = 12
    years = np.repeat([2010, 2011, 2012], 4)
    storm = np.arange(n)
    storm[4] = storm[3]  # same storm straddles the held-year boundary
    common = rng.normal(size=(n, 2))
    raw = rng.normal(size=(n, 2))
    eo = rng.normal(size=(n, 2))
    z = rng.normal(size=(n, 2))
    y = np.full((n, 2), 10.0)
    baseline = y.copy()
    available = np.ones(n, bool)
    pred, encoded, records = prequential_heads(
        common,
        raw,
        eo,
        z,
        y,
        baseline,
        years,
        available,
        lambda year: years < year,
        storm,
        available,
        available,
        alphas=[1.0],
        eo_weights=[0.1],
    )
    assert next(r for r in records if r["year"] == 2011)["training"] == 3
    y[years == 2012] = 1e20
    a, b, _ = prequential_heads(
        common,
        raw,
        eo,
        z,
        y,
        baseline,
        years,
        available,
        lambda year: years < year,
        storm,
        available,
        available,
        alphas=[1.0],
        eo_weights=[0.1],
    )
    np.testing.assert_array_equal(pred[years == 2012], a[years == 2012])
    np.testing.assert_array_equal(encoded[years == 2012], b[years == 2012])


def test_bounded_memory_primal_solver_matches_the_exact_dual_objective():
    from src.eo_individual_readout import (
        conditional_design,
        primal_predictions,
        residual_predictions,
    )

    rng = np.random.default_rng(9)
    n = 50
    g = rng.normal(size=(n, 3))
    r = rng.normal(size=(n, 6))
    e = rng.normal(size=(n, 5))
    z = rng.normal(size=(n, 2))
    y = rng.normal(size=(n, 3))
    train = np.arange(40)
    test = np.arange(40, 50)
    weights = np.arange(1, 41, dtype=float)
    design = conditional_design(g, r, e, z, train, test, weights)
    parts = conditional_parts(g, r, e, z, train, test, weights)
    expected = residual_predictions(parts, y[train], weights, [0.01, 1.0], [0.0, 0.1, 1.0])
    actual = primal_predictions(design, y[train], weights, [0.01, 1.0], [0.0, 0.1, 1.0])
    for key in expected:
        np.testing.assert_allclose(actual[key], expected[key], rtol=1e-6, atol=1e-7)


def test_fast_patch_has_identical_numerical_grid_date_and_padding_contract():
    from rasterio.transform import from_origin

    from src.eo_individual_spatial import fast_patch
    from src.eo_inputs import Tile, get_patch

    values = np.arange(50, dtype=np.float32).reshape(2, 5, 5)
    tile = Tile(
        values,
        np.ones((5, 5), bool),
        np.full((5, 5), 17540.0),
        ["a", "b"],
        from_origin(280000, 5635200, 10, 10),
        "EPSG:32632",
        [],
        {"id": "test", "start": "2018-01-01T00:00:00+00:00", "end": "2018-02-01T00:00:00+00:00"},
    )
    original = get_patch(tile, 4, 4, 4)
    fast = fast_patch(tile, 4, 4, 4)
    for key in ["values", "valid", "days"]:
        np.testing.assert_array_equal(original[key], fast[key])
    for key in fast["metadata"]:
        assert original["metadata"][key] == fast["metadata"][key], key


def test_common_predictors_are_invariant_to_hidden_q_and_never_read_responses():
    import pandas as pd

    from src.eo_individual_evaluation import common_context

    bank = {"q_0": np.arange(720, dtype=float).reshape(1, 10, 72), "rain_0_1_0": np.ones((1, 8, 7))}
    rows = pd.DataFrame(
        {
            "query": [0],
            "site": [2],
            "offset_h": [0],
            "issue_utc": [pd.Timestamp("2020-01-01", tz="UTC")],
        }
    )
    before, rain = common_context(
        bank, rows, "local_q_absent", None, np.array([True]), np.array([True])
    )
    bank["q_0"][0, 2] = 1e100
    bank["outcome_0"] = np.full((1, 8, 24), 1e100)
    after, _ = common_context(
        bank, rows, "local_q_absent", None, np.array([True]), np.array([True])
    )
    np.testing.assert_array_equal(before, after)


def test_full_output_merge_is_lossless_and_does_not_double_count_resumed_tiles(tmp_path):
    import json

    from src.eo_individual_output import assemble_features

    for i, values in enumerate(([1.0, 3.0], [5.0, 7.0])):
        folder = tmp_path / "tiles" / "ctx"
        folder.mkdir(parents=True, exist_ok=True)
        moment = Moments.empty(1)
        moment.add(np.array(values)[:, None], np.ones(2))
        np.savez_compressed(folder / f"{i}.npz", **{"g|primary|0|0": moment.arrays()})
        (folder / f"{i}.json").write_text(json.dumps({"input_hashes": {str(i): str(i)}}))
    contexts = [{"context_id": "ctx", "kind": "monthly"}]
    a, h = assemble_features(tmp_path, contexts, ["g", "missing"], "presto", 1)
    b, _ = assemble_features(tmp_path, contexts, ["g", "missing"], "presto", 1)
    assert a.equals(b)
    assert a.loc[0, "primary_t00_r0_0000"] == 4
    assert a.loc[0, "ablation_t00_r0_0000"] == 4
    assert a.loc[0, "primary_area_t00_r0"] == 4
    assert np.isnan(a.loc[1, "primary_t00_r0_0000"])
    assert len(h) == 2


def test_transfer_never_uses_held_river_q_or_response_labels():
    from src.eo_individual_baselines import transfer_reference

    rng = np.random.default_rng(4)
    n = 9
    groups = np.array(["a", "b", "c", "d", "wurm", "e", "wurm", "wurm", "maas", "maas"])
    bank = {
        "prior_0_0": np.tril(np.ones((n, n), bool), -1),
        "outcome_valid_0": np.ones((n, 8), bool),
        "outcome_0": rng.random((n, 8, 24)),
        "q_0": rng.random((n, 10, 72)),
        "donor_q_0": rng.random((n, 10, 72)),
        "q_mean_0_0": np.zeros((n, 10, 72)),
        "q_pairvar_0_0": np.ones((n, 10, 72)),
        "rain_0_1_0": rng.random((n, 8, 7)),
    }
    before = transfer_reference(bank, 8, 4, 0, "local_q_absent", groups, np.ones(8), {"wurm"})
    bank["q_0"][:, [4, 6, 7]] = 1e90
    bank["donor_q_0"][:, [4, 6, 7]] = -1e90
    bank["outcome_0"][:, [4, 6, 7]] = 1e90
    after = transfer_reference(bank, 8, 4, 0, "local_q_absent", groups, np.ones(8), {"wurm"})
    np.testing.assert_array_equal(before[0], after[0])
    assert before[2] == after[2]
    assert len(set(i for i, _ in after[2])) == len(after[2])
    assert all(groups[j] != "wurm" for _, j in after[2])


def test_transfer_training_excludes_target_river_and_cross_year_storm():
    import pandas as pd

    from src.eo_individual_transfer import transfer_training_mask

    cases = pd.DataFrame(
        dict(
            site=[4, 6, 7, 0, 1, 2],
            storm_id=["a", "b", "c", "spans", "old", "spans"],
            issue_utc=pd.to_datetime(["2018-01-01"] * 5 + ["2019-01-01"], utc=True),
            end_utc=pd.to_datetime(["2018-01-01"] * 6, utc=True),
            response_end_utc=pd.to_datetime(["2018-01-03"] * 6, utc=True),
            outcome_valid=True,
        )
    )
    groups = np.array(["a", "b", "c", "d", "wurm", "e", "wurm", "wurm"])
    mask = transfer_training_mask(
        cases, groups, {"wurm"}, 2019, np.ones((6, 24)), np.ones((6, 24)), np.ones(6, bool)
    )
    np.testing.assert_array_equal(mask, [False, False, False, False, True, False])


def test_paired_review_balances_sites_and_keeps_storm_years_together():
    import pandas as pd

    from src.eo_individual_review import paired_summary

    rows = pd.DataFrame(
        dict(
            gauge=["a", "a", "a", "b"],
            physical_river=["r"] * 4,
            storm_id=[1, 1, 2, 1],
            cutoff_utc=pd.to_datetime(
                ["2018-12-31", "2018-12-31", "2019-01-02", "2018-12-31"], utc=True
            ),
        )
    )
    summary = paired_summary(
        rows, np.array([1.0, 3.0, 6.0, 10.0]), [2018, 2019], np.array([[2, 0], [0, 2]])
    )
    # Site a: mean(storm1=2, storm2=6)=4; site b=10 -> 7.
    assert summary["estimate"] == 7
    assert summary["storms"] == 2
    assert summary["bootstrap_nonfinite"] == 0


def test_all_zero_eo_hyperparameters_are_admissible_and_return_exact_raw_candidate():
    from src.eo_individual_readout import prequential_heads

    rng = np.random.default_rng(42)
    years = np.repeat([2015, 2016, 2017], 4)
    n = len(years)
    g, r, z = rng.normal(size=(n, 2)), rng.normal(size=(n, 2)), rng.normal(size=(n, 2))
    y = np.full((n, 2), 5.0)
    available = np.ones(n, bool)
    _, _, records = prequential_heads(
        g,
        r,
        np.empty((n, 0)),
        z,
        y,
        y.copy(),
        years,
        available,
        lambda year: years < year,
        np.arange(n),
        available,
        available,
        alphas=[0.1, 1.0],
        eo_weights=[0.1],
    )
    last = records[-1]
    assert "(0.0, 0.1)" in last["eo_validation"]
    assert "(0.0, 1.0)" in last["eo_validation"]


def test_queue_obeys_dependencies_and_one_mps_two_cpu_limits():
    import runpy
    from pathlib import Path

    queue = runpy.run_path(
        str(Path(__file__).resolve().parents[1] / "scripts/173_queue_individual_experiments.py")
    )
    tasks = queue["task_graph"]()
    assert queue["eligible_tasks"](tasks, {}, {}) == ["preflight"]
    states = {"preflight": {"status": "completed"}}
    chosen = queue["eligible_tasks"](tasks, states, {})
    assert sum(tasks[k]["resource"] == "cpu" for k in chosen) == 2
    assert sum(tasks[k]["resource"] == "mps" for k in chosen) == 1
    assert all(k.startswith("smoke_") for k in chosen)
    active = {k: object() for k in chosen}
    states.update({k: {"status": "running"} for k in chosen})
    assert queue["eligible_tasks"](tasks, states, active) == []
    assert all("benchmark_" + m in tasks["extract_" + m]["dependencies"] for m in queue["MODELS"])


def test_transfer_reference_cache_retains_unavailable_early_cases(tmp_path):
    import pandas as pd

    from src.eo_individual_transfer import TransferReferences

    rng = np.random.default_rng(14)
    n = 3
    groups = ["a", "b", "c", "d", "wurm", "e", "wurm", "wurm"]
    times = pd.date_range("2018-01-02", periods=n, freq="10D", tz="UTC")
    rows = pd.DataFrame(
        [
            dict(
                query=q,
                site=g,
                physical_river=groups[g],
                area_km2=10.0 + g,
                issue_utc=t,
                cutoff_utc=t,
                end_utc=t + pd.Timedelta(hours=6),
                offset_h=0,
            )
            for q, t in enumerate(times)
            for g in range(8)
        ]
    )
    bank = dict(
        prior_0_0=np.tril(np.ones((n, n), bool), -1),
        outcome_valid_0=np.ones((n, 8), bool),
        outcome_0=rng.random((n, 8, 24)),
        q_0=rng.random((n, 10, 72)),
        donor_q_0=rng.random((n, 10, 72)),
        q_mean_0_0=np.zeros((n, 10, 72)),
        q_pairvar_0_0=np.ones((n, 10, 72)),
        rain_0_1_0=rng.random((n, 8, 7)),
    )
    cache = TransferReferences(tmp_path, "local_q_absent", rows, bank, {"fixture": "unit"})
    first = cache.get({"wurm"})
    assert not np.isfinite(first["mean"][:8]).any()
    assert np.isfinite(first["mean"][12]).all()
    assert not np.isfinite(first["fixed_mean"]).any()
    restored = TransferReferences(tmp_path, "local_q_absent", rows, bank, {"fixture": "unit"}).get(
        {"wurm"}
    )
    np.testing.assert_array_equal(first["mean"], restored["mean"])
    np.testing.assert_array_equal(first["donors"], restored["donors"])
