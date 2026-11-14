"""Regression fixtures for the six paired-source design/code audit findings."""

import fcntl
import json
import runpy
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.eo_individual_evaluation import common_context
from src.eo_individual_readout import prequential_heads
from src.eo_individual_review import paired_summary
from src.geoglows_experiment import (
    align_channels,
    correction_modes,
    exclude_channels,
    execution_status,
    paired_summary_table,
    sha,
    validate_acquisition,
)


def test_excluded_eys_cannot_affect_inputs_or_normalization():
    bank = {
        "q_0": np.ones((1, 10, 72)),
        "donor_q_0": np.ones((1, 10, 72)),
        "input_quality_0": np.ones((1, 10, 72), bool),
        "q_mean_0_0": np.ones((1, 10, 72)),
        "q_pairvar_0_0": np.ones((1, 10, 72)),
        "rain_0_1_0": np.ones((1, 8, 7)),
    }
    perturbed = {k: v.copy() for k, v in bank.items()}
    for name in ["q_0", "donor_q_0", "q_mean_0_0", "q_pairvar_0_0"]:
        perturbed[name][:, 0] = 1e9
    a, b = exclude_channels(bank, [0], [0]), exclude_channels(perturbed, [0], [0])
    for name in a:
        np.testing.assert_array_equal(a[name], b[name])
    row = pd.DataFrame(
        dict(query=[0], site=[1], offset_h=[0], issue_utc=pd.to_datetime(["2020-01-01"], utc=True))
    )
    ca = common_context(a, row, "rich_basin", None, np.array([False]), np.array([False]))[0]
    cb = common_context(b, row, "rich_basin", None, np.array([False]), np.array([False]))[0]
    np.testing.assert_array_equal(ca, cb)
    assert (bank["q_0"] == 1).all(), "Original data mutated"
    assert not a["input_quality_0"][:, 0].any()


def test_same_training_rows_validation_and_hydro_fallback_without_future_labels():
    rng = np.random.default_rng(7)
    years = np.repeat(np.arange(2017, 2022), 4)
    n = len(years)
    common = rng.normal(size=(n, 3))
    raw, eo = rng.normal(size=(n, 2)), rng.normal(size=(n, 2))
    available = np.arange(n) % 3 != 0
    encoder_available = available & (np.arange(n) % 2 != 0)
    raw[~available], eo[~encoder_available] = np.nan, np.nan
    y = np.repeat((4 + common[:, :1]) * np.linspace(1, 2, 24)[None], 1, axis=0)
    baseline = np.ones((n, 24))
    storms = np.array([f"s{i}" for i in range(n)])
    empty = np.empty((n, 0))

    def run(outcomes):
        args = (
            common[:, :2],
            outcomes,
            baseline,
            years,
            np.ones(n, bool),
            lambda year: years < year,
            storms,
        )
        hydro, _, h_records = prequential_heads(
            common,
            empty,
            empty,
            *args,
            np.ones(n, bool),
            np.zeros(n, bool),
            alphas=(0.1, 1),
            eo_weights=(),
        )
        r, e, records = prequential_heads(
            common,
            raw,
            eo,
            *args,
            available,
            encoder_available,
            alphas=(0.1, 1),
            eo_weights=(0.1,),
            training_available=np.ones(n, bool),
            raw_fallback=hydro,
        )
        for h, s in zip(h_records, records, strict=True):
            assert h.get("training_rows", []) == s.get("training_rows", [])
            assert h.get("validation_years", []) == s.get("validation_years", [])
        np.testing.assert_array_equal(r[~available], hydro[~available])
        np.testing.assert_array_equal(e[~available], hydro[~available])
        np.testing.assert_array_equal(e[~encoder_available], r[~encoder_available])
        return hydro, r, e

    predictions = run(y)
    changed = y.copy()
    changed[years == years.max()] += 1e6
    for before, after in zip(predictions, run(changed), strict=True):
        np.testing.assert_allclose(before, after, rtol=1e-10, atol=1e-10)


def test_fixed_site_bootstrap_counts_partial_draws_as_undefined():
    cases = pd.DataFrame(
        dict(
            gauge=["a", "b"],
            physical_river=["r1", "r2"],
            storm_id=["s1", "s2"],
            cutoff_utc=pd.to_datetime(["2020-01-01", "2021-01-01"], utc=True),
        )
    )
    draws = np.array([[2, 0], [0, 2], [1, 1]])
    result = paired_summary(
        cases, np.array([1.0, 100.0]), [2020, 2021], draws, fixed_population=True
    )
    assert result["estimate"] == 50.5
    assert result["bootstrap_partial_sites"] == result["bootstrap_nonfinite"] == 2
    missing = paired_summary(
        cases, np.array([1.0, np.nan]), [2020, 2021], draws, fixed_population=True
    )
    assert np.isnan(missing["estimate"]) and missing["point_missing_sites"] == 1


def test_joint_high_water_support_and_median_contrast_are_reported():
    c = pd.DataFrame(
        dict(
            gauge=["a"] * 3,
            physical_river=["r"] * 3,
            storm_id=["s1", "s2", "s3"],
            cutoff_utc=pd.to_datetime(["2020-01-01"] * 3, utc=True),
            outcome_valid=[True] * 3,
            future_p99=[1, 1, 0],
            verification_clean=[True] * 3,
            documented_flood_overlap=[False] * 3,
            country=["NL"] * 3,
            local_model_reach_mapped=[True] * 3,
            raw_available=[True, False, True],
            encoder_available=[True, False, True],
        )
    )
    names = [
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
    report = paired_summary_table(
        c, {name: np.ones((3, 24)) for name in names}, [2020], np.ones((5, 1), int)
    )
    joint = report[
        (report.reference == "raw_correction")
        & (report.subset == "mapped_high_water_encoder_supported")
    ].iloc[0]
    assert joint.assessments == 1
    assert "conventional_median" in report.reference.values


def test_reordered_channel_labels_are_aligned_not_silently_renamed():
    frame = pd.DataFrame({str(i): [float(i)] for i in reversed(range(10))})
    aligned = align_channels(frame)
    np.testing.assert_array_equal(aligned.iloc[0], np.arange(10))
    duplicate = frame.copy()
    duplicate.columns = ["0"] * 10
    with pytest.raises(ValueError, match="Duplicate"):
        align_channels(duplicate)


@pytest.mark.parametrize("stale", ["config", "mapping"])
def test_stale_acquisition_identities_are_rejected(tmp_path, stale):
    raw = tmp_path / "raw"
    raw.mkdir()
    config = tmp_path / "old.json"
    config.write_text("{}")
    mapping = tmp_path / "config/limburg_geoglows_reaches_v1.json"
    mapping.parent.mkdir()
    mapping.write_text("[]")
    receipt = dict(config_sha256=sha(config), mapping_sha256=sha(mapping), outputs={})
    receipt["config_sha256" if stale == "config" else "mapping_sha256"] = "stale"
    (raw / "download_manifest.json").write_text(json.dumps(receipt))
    with pytest.raises(ValueError, match="Stale acquisition"):
        validate_acquisition(tmp_path, dict(raw="raw", acquisition_config="old.json"))


def test_execution_status_tracks_interruption_failure_completion_and_review(tmp_path):
    plan = dict(stages=["observed", "geoglows"], models=["presto"])
    assert execution_status(tmp_path, plan)["full_analysis_launched"] is False
    state = tmp_path / "run_state.json"
    state.write_text(json.dumps(dict(status="running", history=[{}])))
    assert execution_status(tmp_path, plan)["execution_status"] == "interrupted"
    with (tmp_path / ".controller.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        assert execution_status(tmp_path, plan)["execution_status"] == "running"
    state.write_text(json.dumps(dict(status="failed", error="fixture", history=[{}])))
    assert execution_status(tmp_path, plan)["execution_status"] == "failed"
    for stage in plan["stages"]:
        p = tmp_path / f"scores/{stage}__presto"
        p.mkdir(parents=True)
        (p / "manifest.json").write_text('{"status":"completed"}')
    assert execution_status(tmp_path, plan)["execution_status"] == "completed"
    p = tmp_path / "review"
    p.mkdir()
    (p / "manifest.json").write_text('{"status":"completed"}')
    assert execution_status(tmp_path, plan)["execution_status"] == "reviewed"
    assert execution_status(tmp_path, plan)["full_analysis_launched"] is True


def test_failed_controller_retains_error_and_resume_history(tmp_path, monkeypatch):
    ns = runpy.run_path(str(ROOT / "scripts/261_run_geoglows_comparison.py"))
    run_all = ns["run_all"]
    monkeypatch.setitem(run_all.__globals__, "ROOT", tmp_path)
    config = tmp_path / "config.json"
    config.write_text("{}")
    monkeypatch.setitem(run_all.__globals__, "CONFIG", config)

    def reject(_):
        raise ValueError("fixture input mismatch")

    monkeypatch.setitem(run_all.__globals__, "verify_receipt", reject)
    out = tmp_path / "work"
    out.mkdir()
    for _ in range(2):
        with pytest.raises(ValueError, match="fixture input mismatch"):
            run_all(dict(output="work"))
    state = json.loads((out / "run_state.json").read_text())
    assert state["status"] == "failed" and len(state["history"]) == 2
    assert "fixture input mismatch" in state["error"]


def test_revised_plan_has_seven_targets_and_nine_active_inputs():
    p = json.loads((ROOT / "config/limburg_geoglows_stages12_v2.json").read_text())
    assert p["target_channels"] == list(range(1, 8))
    assert p["active_input_channels"] == list(range(1, 10))
    assert not any(s["gauge"] == "11.Q.32" for s in p["sites"])
    assert 481 * len(p["target_channels"]) * len(p["issue_offsets_h"]) == 13468


def test_modes_describe_encoder_absence_and_hydrology_fallback():
    records = [dict(year=2020, training=5, raw_parameters=0.1, eo_parameters="baseline")]
    modes = correction_modes(records, [2020] * 3, [True, True, False], [True, False, False])
    assert list(modes["raw_prediction_mode"]) == [
        "raw_correction",
        "raw_correction",
        "hydro_fallback",
    ]
    assert list(modes["encoder_prediction_mode"]) == [
        "conventional",
        "raw_correction",
        "hydro_fallback",
    ]


def test_calibrated_baseline_handles_seven_target_rows_and_prior_years(tmp_path, monkeypatch):
    """Exercise the actual baseline/calibration loop, not pre-made predictions."""
    ns = runpy.run_path(str(ROOT / "scripts/261_run_geoglows_comparison.py"))
    baselines = ns["baselines"]
    monkeypatch.setitem(baselines.__globals__, "ROOT", tmp_path)
    monkeypatch.setitem(baselines.__globals__, "source_identity", lambda _: {})
    dates = pd.to_datetime(["2018-06-01", "2019-06-01", "2020-06-01"], utc=True)
    index = pd.DatetimeIndex(
        np.concatenate(
            [pd.date_range(t - pd.Timedelta(hours=71), t, freq="h").to_numpy() for t in dates]
        )
    )
    hourly = pd.DataFrame(np.repeat(np.arange(1, 4), 72)[:, None] * np.ones((1, 10)), index=index)
    hourly.columns = range(10)
    hourly[0] = np.nan
    monkeypatch.setitem(baselines.__globals__, "validate_acquisition", lambda *_: hourly)
    prep = tmp_path / "work/preparation"
    prep.mkdir(parents=True)
    (prep / "manifest.json").write_text("{}")
    (hourly * 2).to_parquet(prep / "calibration_observed.parquet")
    epochs = index.as_unit("ns").asi8 // pd.Timedelta(hours=1).value
    np.save(prep / "epochs.npy", epochs)
    q = hourly.to_numpy().reshape(3, 72, 10).transpose(0, 2, 1)
    bank = dict(
        q_0=q,
        donor_q_0=q.copy(),
        positions_0=np.arange(216).reshape(3, 72),
        prior_0_0=np.tri(3, k=-1, dtype=bool),
        outcome_valid_0=np.ones((3, 8), bool),
        outcome_0=np.repeat(np.arange(1, 4)[:, None, None] * 2, 8 * 24, axis=1).reshape(3, 8, 24),
        rain_0_1_0=np.ones((3, 8, 7)),
        q_mean_0_0=np.ones((3, 10, 72)),
        q_pairvar_0_0=np.ones((3, 10, 72)),
        rain_mean_0_0=np.ones((3, 8, 7)),
        rain_var_0_0=np.ones((3, 8, 7)),
    )
    np.savez_compressed(prep / "geoglows_bank.npz", **bank)
    cases = pd.DataFrame(
        [
            dict(
                query=i,
                site=j,
                offset_h=0,
                area_km2=100.0,
                issue_utc=t,
                end_utc=t + pd.Timedelta(hours=6),
                response_end_utc=t + pd.Timedelta(hours=24),
                assessment_id=f"{i}_{j}",
            )
            for i, t in enumerate(dates)
            for j in range(1, 8)
        ]
    )
    cases.to_parquet(prep / "cases.parquet", index=False)
    baselines(
        dict(output="work", issue_offsets_h=[0], free_space_reserve_gib=0), "geoglows", prep, cases
    )
    result = np.load(tmp_path / "work/baselines/geoglows/predictions.npz")
    assert result["conventional_mean"].shape == (21, 24)
    assert np.isnan(result["monthly_qm_persistence"][:7]).all()
    np.testing.assert_allclose(result["monthly_qm_persistence"][14:], 6 * 3.6 / 100)
