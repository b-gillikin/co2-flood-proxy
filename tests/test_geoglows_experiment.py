"""Scientific input/clock/calibration contracts for the paired-source study."""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.geoglows_experiment import (
    closed_before,
    disk_check,
    hour_end,
    paired_summary_table,
    qm_apply,
    qm_fit,
    replace_histories,
)


def test_hour_end_does_not_expose_the_following_hour():
    q = pd.Series([0.0, 12.0, -1.0], index=pd.date_range("2020-01-01", periods=3, freq="h"))
    out = hour_end(q)
    assert out.index[0] == pd.Timestamp("2020-01-01T01:00Z")
    assert out.loc[:"2020-01-01T01:00Z"].tolist() == [0.0]
    assert np.isnan(out.iloc[2])  # unknown/invalid is not dry


def test_hour_end_rejects_duplicate_and_subhourly_stamps():
    for index in [["2020-01-01", "2020-01-01"], ["2020-01-01T00:30Z"]]:
        with pytest.raises(ValueError):
            hour_end(pd.Series(np.ones(len(index)), index=pd.to_datetime(index)))


def test_every_query_donor_channel_changes_but_labels_and_rain_do_not():
    periods = 75
    hourly = pd.DataFrame(
        np.arange(periods * 10).reshape(periods, 10),
        index=pd.date_range("2020-01-01", periods=periods, freq="h", tz="UTC"),
        dtype=float,
    )
    epochs = hourly.index.as_unit("ns").asi8 // pd.Timedelta(hours=1).value
    pos = np.array([np.arange(72), np.arange(1, 73)])
    bank = {
        "positions_0": pos,
        "q_0": np.full((2, 10, 72), 9999.0),
        "donor_q_0": np.full((2, 10, 72), 9999.0),
        "prior_0_0": np.array([[False, False], [True, False]]),
        "outcome_0": np.full((2, 8, 24), 55.0),
        "rain_0_1_0": np.ones((2, 8, 7)),
    }
    changed = replace_histories(bank, hourly, epochs, [0])
    np.testing.assert_array_equal(changed["q_0"][0, 9], hourly.iloc[:72, 9])
    np.testing.assert_array_equal(changed["donor_q_0"], changed["q_0"])
    assert changed["outcome_0"] is bank["outcome_0"]
    assert changed["rain_0_1_0"] is bank["rain_0_1_0"]
    assert (bank["q_0"] == 9999).all()  # original archive untouched


def test_missing_model_history_never_falls_back_to_observed():
    index = pd.date_range("2020-01-01", periods=72, freq="h", tz="UTC")
    q = pd.DataFrame(np.nan, index=index, columns=range(10))
    bank = {
        "positions_0": np.arange(72)[None],
        "prior_0_0": np.zeros((1, 1), bool),
        "q_0": np.ones((1, 10, 72)),
    }
    out = replace_histories(bank, q, index.as_unit("ns").asi8 // pd.Timedelta(hours=1).value, [0])
    assert np.isnan(out["q_0"]).all() and np.isnan(out["donor_q_0"]).all()


def test_mapping_uses_only_past_observations_and_keeps_extreme_tail():
    index = pd.date_range("2019-12-28", periods=120, freq="h", tz="UTC")
    sim = pd.DataFrame({0: np.linspace(0, 100, len(index))}, index=index)
    obs = sim * 2
    boundary = pd.Timestamp("2020-01-01", tz="UTC")
    obs.loc[obs.index >= boundary] = 1e9
    fit = qm_fit(sim, obs, [1], boundary)
    curve = fit[(0, 1)]
    assert curve["annual_fallback"]
    assert pd.Timestamp(curve["last_training_time"]) < boundary
    np.testing.assert_allclose(
        qm_apply(np.array([0, 40, 200, np.nan]), 1, curve), [0, 80, 400, np.nan]
    )


def test_no_training_calibration_is_unknown_not_identity():
    index = pd.date_range("2020-01-01", periods=3, freq="h", tz="UTC")
    x = pd.DataFrame({0: [1.0, 2.0, 3.0]}, index=index)
    fit = qm_fit(x, x, [1], pd.Timestamp("2019-01-01", tz="UTC"))
    assert fit[(0, 1)] is None
    assert np.isnan(qm_apply(np.array([4.0]), 1, fit[(0, 1)])).all()


def test_training_closes_entire_storm_and_response_window():
    rows = pd.DataFrame(
        {
            "end_utc": pd.to_datetime(
                ["2019-12-30", "2019-12-31T20:00Z"], utc=True, format="mixed"
            ),
            "response_end_utc": pd.to_datetime(["2019-12-31", "2019-12-31"], utc=True),
        }
    )
    assert closed_before(rows, 2020).tolist() == [True, False]


def test_invalid_outcome_is_not_scored_even_if_finite():
    cases = pd.DataFrame(
        {
            "gauge": ["a", "a"],
            "physical_river": ["r", "r"],
            "storm_id": ["s1", "s2"],
            "cutoff_utc": pd.to_datetime(["2020-01-01", "2020-02-01"], utc=True),
            "outcome_valid": [True, False],
            "future_p99": [1, 1],
            "verification_clean": [True, False],
            "documented_flood_overlap": [False, False],
            "country": ["NL", "NL"],
        }
    )
    p = {
        name: np.ones((2, 24))
        for name in [
            "observed",
            "encoder_correction",
            "raw_correction",
            "hydro_correction",
            "conventional_mean",
            "conventional_median",
            "monthly_qm_analogue",
            "monthly_qm_persistence",
            "input_persistence",
        ]
    }
    p["encoder_correction"][1] = 1e6
    report = paired_summary_table(cases, p, [2020], np.ones((5, 1), int))
    r = report[(report.subset == "all") & (report.reference == "raw_correction")].iloc[0]
    assert r.assessments == 1 and r.estimate == 0


def test_disk_guard_accounts_for_pending_write(monkeypatch):
    from types import SimpleNamespace

    monkeypatch.setattr(
        "src.geoglows_experiment.shutil.disk_usage", lambda _: SimpleNamespace(free=51 * 2**30)
    )
    with pytest.raises(RuntimeError):
        disk_check(ROOT, 50, 2 * 2**30)


def test_config_preserves_full_census_and_no_hidden_observed_q():
    plan = json.loads((ROOT / "config/limburg_geoglows_stages12_v1.json").read_text())
    assert [s["channel"] for s in plan["sites"]] == list(range(10))
    assert sum(s["role"] == "response_and_input" for s in plan["sites"]) == 8
    assert plan["stages"] == ["observed", "geoglows"]
    assert plan["issue_offsets_h"] == [0, 6, 12, 24]
    assert plan["free_space_reserve_gib"] == 50
    assert plan["max_cpu_workers"] == 2


def test_complete_scoring_path_on_synthetic_years(tmp_path, monkeypatch):
    """Exercise the new scorer/empty-EO hydro arm without a real research run."""
    import runpy

    namespace = runpy.run_path(str(ROOT / "scripts/261_run_geoglows_comparison.py"))
    score = namespace["score"]
    monkeypatch.setitem(score.__globals__, "ROOT", tmp_path)
    monkeypatch.setitem(score.__globals__, "verify_receipt", lambda _: {})
    monkeypatch.setitem(score.__globals__, "source_identity", lambda _: {})
    from src.eo_event_inputs import completed_windows, context_id

    plan = {"output": "work"}
    prep = tmp_path / "work/preparation"
    prep.mkdir(parents=True)
    (prep / "manifest.json").write_text("{}")
    dates = pd.to_datetime(["2018-06-01", "2019-06-01", "2020-06-01"], utc=True)
    rows, features = [], []
    for query, cutoff in enumerate(dates):
        context = context_id("monthly", completed_windows(cutoff, "monthly"))
        for site in range(1, 8):
            gauge = f"g{site}"
            rows.append(
                dict(
                    query=query,
                    site=site,
                    offset_h=0,
                    cutoff_utc=cutoff,
                    issue_utc=cutoff,
                    end_utc=cutoff + pd.Timedelta(hours=6),
                    response_end_utc=cutoff + pd.Timedelta(hours=24),
                    assessment_id=f"{query}_{site}",
                    gauge=gauge,
                    catchment_gauge=gauge,
                    area_km2=100.0,
                    country="NL",
                    physical_river="r",
                    storm_id=str(query),
                    outcome_valid=True,
                    future_p99=1,
                    verification_clean=True,
                    documented_flood_overlap=False,
                )
            )
            features.append(
                dict(
                    context_id=context,
                    catchment_gauge=gauge,
                    primary_t0_r0_0=float(query + site + 1),
                    raw_t0_r0_0=float(query + 2),
                    raw_area_total=1e8,
                )
            )
    pd.DataFrame(rows).to_parquet(prep / "cases.parquet")
    bank = {
        "q_0": np.ones((3, 10, 72)),
        "rain_0_1_0": np.ones((3, 8, 7)),
        "outcome_0": np.ones((3, 8, 24)),
    }
    np.savez_compressed(prep / "observed_bank.npz", **bank)
    feature_dir = tmp_path / "results/limburg_individual_experiments_v1/features/presto"
    feature_dir.mkdir(parents=True)
    pd.DataFrame(features).to_parquet(feature_dir / "context_features.parquet")
    base = tmp_path / "work/baselines/observed"
    base.mkdir(parents=True)
    (base / "manifest.json").write_text("{}")
    np.savez_compressed(
        base / "predictions.npz",
        **{
            name: np.ones((21, 24))
            for name in [
                "conventional_mean",
                "conventional_median",
                "input_persistence",
                "monthly_qm_persistence",
                "monthly_qm_analogue",
            ]
        },
    )
    score(plan, "observed", "presto")
    dest = tmp_path / "work/scores/observed__presto"
    receipt = json.loads((dest / "manifest.json").read_text())
    assert receipt["status"] == "completed" and receipt["rows"] == 21
    scores = pd.read_parquet(dest / "scores.parquet")
    assert scores.method.nunique() == 8
    assert "mae_m3s" in scores
    assert len(scores) == 21 * 8
