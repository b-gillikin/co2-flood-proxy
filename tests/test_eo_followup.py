"""Scientific follow-up contracts: required inputs, matching, references and provenance."""

import numpy as np
import pandas as pd
import pytest

from src.eo_followup import archive_metrics, eligible_archive, feature_complete, review_input_note


def test_parallel_stage_reuses_verified_files_without_linking_mutable_summaries(tmp_path):
    import json
    import runpy
    from pathlib import Path

    from src.eo_inputs import sha256

    ns = runpy.run_path(
        str(Path(__file__).resolve().parents[1] / "scripts/137_eo_archive_and_route_followup.py")
    )
    reuse = ns["reuse_independent"]
    reuse.__globals__["ROOT"] = tmp_path
    folder, destination = tmp_path / "independent", tmp_path / "final"
    folder.mkdir()
    destination.mkdir()
    (tmp_path / "input").write_text("held input")
    (tmp_path / "source.py").write_text("frozen source")
    names = [
        "common_route_assessments.parquet",
        "archive_reference/main/monthly.parquet",
        "archive_summary.parquet",
        "archive_intervals.parquet",
        "archive_progress.json",
    ]
    for name in names:
        p = folder / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(name)
    manifest = {
        "status": "completed",
        "stage": "independent",
        "input_sha256": {"input": sha256(tmp_path / "input")},
        "source_sha256": {"source.py": sha256(tmp_path / "source.py")},
        "outputs_sha256": {name: sha256(folder / name) for name in names},
    }
    (folder / "manifest.json").write_text(json.dumps(manifest))
    reuse(folder, destination)
    for name in names[:2]:
        assert (destination / name).stat().st_ino == (folder / name).stat().st_ino
    for name in names[2:]:
        assert not (destination / name).exists()
    assert not (destination / "manifest.json").exists()
    (tmp_path / "input").write_text("changed")
    with pytest.raises(ValueError, match="dependency changed"):
        reuse(folder, destination)
    (tmp_path / "input").write_text("held input")
    (folder / names[0]).write_text("corrupt")
    with pytest.raises(ValueError, match="output changed"):
        reuse(folder, destination)


def test_independent_archive_specs_exclude_unfinished_rainfall_run():
    import runpy
    from pathlib import Path

    ns = runpy.run_path(
        str(Path(__file__).resolve().parents[1] / "scripts/137_eo_archive_and_route_followup.py")
    )
    assert [s[0] for s in ns["archive_specs"](False)] == [
        "main",
        "satmae_toa_qa60",
        "copernicus_fm_toa_qa60",
        "croma_ascending_15",
        "croma_ascending_161",
    ]
    assert ns["archive_specs"]()[-1][0] == "rain168"


def test_actual_predictor_completeness_does_not_require_unused_rain_history():
    f = pd.DataFrame(
        {
            "complete_scoring_sample": [True, True, False],
            "rain168": [1, np.nan, 2],
            "rain512_complete": [False, True, True],
        }
    )
    assert feature_complete(f, ["rain168"]).tolist() == [True, False, False]


def test_archive_rules_exclude_unfinished_same_storm_and_wrong_river():
    t = pd.Timestamp("2020-02-01", tz="UTC")
    pop = pd.DataFrame(
        {
            "event_id": ["q", "valid", "same", "unfinished", "same_river"],
            "onset_utc": [
                t,
                t - pd.Timedelta(hours=100),
                t - pd.Timedelta(hours=100),
                t - pd.Timedelta(hours=1),
                t - pd.Timedelta(hours=100),
            ],
            "storm_id": ["q", "a", "q", "b", "c"],
            "physical_river_group": ["Wurm", "Geul", "Geul", "Geul", "Wurm"],
            "country": ["DE", "NL", "NL", "NL", "NL"],
            "measurement_concern": [False] * 5,
            "complete_scoring_sample": [True] * 5,
        }
    )
    out = eligible_archive(pop, pop.iloc[0], "other_rivers", "foreign", False)
    assert out.event_id.tolist() == ["valid"]
    assert eligible_archive(pop, pop.iloc[0], "other_rivers", "domestic", False).empty


def test_generic_archive_weights_storms_not_gauge_count():
    q = np.full(72, 4.0)
    a = np.stack([np.ones(72), np.full(72, 3.0), np.full(72, 10.0)])
    m = archive_metrics(q, a, ["a", "a", "b"])
    assert m["ensemble_curve_level_rmse"] == pytest.approx(2.0)
    assert m["mean_donor_peak_absolute_error"] == pytest.approx(2.0)
    assert m["mean_peak_scaled_shape_rmse"] == pytest.approx(0.0)


def test_generic_reference_separates_shape_from_peak_estimate():
    q = np.arange(1, 73, dtype=float)
    a = np.stack([q * 0.5, q * 1.5])
    m = archive_metrics(q, a, ["a", "b"])
    assert m["mean_peak_scaled_shape_rmse"] == pytest.approx(0.0)
    assert m["mean_donor_peak_absolute_error"] == pytest.approx(0.0)
    assert m["ensemble_curve_level_rmse"] == pytest.approx(0.0)
    assert m["duration_estimate_absolute_error_h"] > 0


def test_provenance_identifies_expanded_route_without_false_reuse_claim():
    contract = {
        "satmae": {
            "input_policy": "s2_toa_same_utc_day_qa60_clear_v1",
            "input_population": {
                "jobs_location": {
                    "path": "data/processed/eo_expansion_input_views/satmae_toa_qa60/jobs.json"
                }
            },
        }
    }
    note = review_input_note(contract)
    assert "Includes supplemental Azure-acquired imagery" in note
    assert "satmae_toa_qa60" in note
    assert "not included" not in note
    assert "three native-product models are reused" not in note


def test_versioned_review_writer_keeps_audits_and_valid_payload(tmp_path, monkeypatch):
    import runpy
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    fixture = runpy.run_path(str(root / "tests/test_eo_actual_analogue_review.py"))
    revised = runpy.run_path(str(root / "scripts/135_review_eo_followup.py"))
    function = fixture["test_complete_review_writes_browser_tables_and_verifiable_receipt"]
    monkeypatch.setitem(function.__globals__, "MODULE", revised)
    function(tmp_path, monkeypatch)


def test_chunked_multi_bootstrap_matches_established_scalar_estimator():
    import runpy
    from pathlib import Path

    from src.eo_followup import cluster_intervals_multi

    root = Path(__file__).resolve().parents[1]
    scalar = runpy.run_path(str(root / "scripts/73_analogue_uncertainty_review.py"))[
        "cluster_interval"
    ]
    frame = pd.DataFrame(
        {
            "storm": ["a", "a", "b", "c", "c", "c"],
            "x": [1.0, 2.0, 3.0, 4.0, 6.0, 7.0],
            "y": [8.0, 2.0, 1.0, 3.0, 2.0, 4.0],
        }
    )
    multi = cluster_intervals_multi(frame, "storm", ["x", "y"], draws=1001, seed=42)
    for column in ["x", "y"]:
        single = scalar(frame.assign(difference=frame[column]), "storm", draws=1001, seed=42)
        for key in ["difference", "lower", "upper"]:
            assert multi[column][key] == pytest.approx(single[key], rel=1e-13, abs=1e-13)
    one = cluster_intervals_multi(frame[frame.storm.eq("a")], "storm", ["x"])["x"]
    assert one["draws"] == 0 and np.isnan(one["lower"])
