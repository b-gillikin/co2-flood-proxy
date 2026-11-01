"""Exercise scientific invariants added after the applied design review."""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from applied_evaluation import CompleteBatches, label_accounting, paired_event_summary
from applied_local_reference import summarize_cases
from applied_physical import candidates, predict, source_features
from applied_timing import acquisition_context

ROOT = Path(__file__).resolve().parents[1]


def test_every_selected_example_survives_short_batches():
    for n in range(2, 81):
        for batch in [2, 8, 16, 64]:
            sampler = CompleteBatches(n, batch, 42)
            batches = list(sampler)
            flat = [v for b in batches for v in b]
            assert sorted(flat) == list(range(n))
            assert all(2 <= len(b) <= batch + 1 for b in batches)
            assert len(batches) == len(sampler)
            assert batches == list(CompleteBatches(n, batch, 42))
    assert list(CompleteBatches(21, 16, 42))[0].__len__() == 16
    with pytest.raises(ValueError):
        CompleteBatches(1, 8, 42)


def test_validation_labels_are_in_total_cost():
    rows = {"train": list(range(5)), "valid": list(range(40)), "test": list(range(10))}
    a = label_accounting(rows, 100, 5)
    assert a["training_label_fraction"] == 0.05
    assert a["combined_selection_label_fraction"] == pytest.approx(45 / 140)
    assert a["unique_selection_labels"] == 45


def test_optical_control_uses_actual_green_nir_swir_bands():
    # Prithvi six bands are B2,B3,B4,B8A,B11,B12.
    raw = np.array([100, 2000, 100, 500, 1000, 100], dtype=np.float32)[:, None, None]
    means = np.array([1087, 1342, 1433, 2734, 1958, 1363])[:, None, None]
    std = np.array([2248, 2179, 2178, 1850, 1242, 1049])[:, None, None]
    features = source_features((raw - means) / std, "prithvi")
    assert features["ndwi"][0, 0] == pytest.approx(0.6, abs=1e-6)
    assert features["mndwi"][0, 0] == pytest.approx(1 / 3, abs=1e-6)
    assert predict(features, dict(method="mndwi", threshold=0.4)).item() == 0
    assert predict(features, dict(method="ndwi", threshold=0.4)).item() == 1
    assert len(candidates("prithvi")) == 66


def test_radar_change_distinguishes_persistent_and_new_dark_water():
    raw = np.array(
        [[0.005, 0.08, 0.08], [0.005, 0.08, 0.08], [0.004, 0.002, 0.09], [0.004, 0.002, 0.09]]
    )[:, None, :]
    means = np.array([0.0981, 0.0253, 0.0981, 0.0253])[:, None, None]
    std = np.array([0.043, 0.0174, 0.0981, 0.0253])[:, None, None]
    features = source_features((raw - means) / std, "copernicus")
    y = predict(features, dict(method="radar_change", polarization=0, threshold_db=-20, drop_db=3))
    assert y.tolist() == [[1, 2, 0]]


def test_case_scores_pool_counts_not_tile_ious_and_keep_coverage():
    rows = []
    for tp, fn, fp, tn, eligible in [(1, 0, 0, 1, 4), (0, 8, 2, 10, 20)]:
        metrics = dict(tp=tp, fn=fn, fp=fp, tn=tn)
        rows.append(
            dict(
                case="same-acquisition",
                model="one",
                metrics=metrics,
                individual_metrics=metrics,
                eligible_reference_pixels=eligible,
                reference_offset_hours=6.6,
                reference_dependence="different sensor",
            )
        )
    summary = summarize_cases(rows)[0]["support"]["common"]
    assert summary["iou"] == pytest.approx(1 / 11)
    assert summary["coverage_fraction"] == pytest.approx(22 / 24)
    assert summary["unknown_or_unobserved_reference_pixels"] == 2
    rows[1]["reference_offset_hours"] = 12
    with pytest.raises(ValueError, match="one acquisition"):
        summarize_cases(rows)


def test_event_bootstrap_does_not_hide_undefined_or_one_case():
    a = paired_event_summary({"a": 0.8, "b": 0.3, "c": None}, {"a": 0.6, "b": 0.4, "c": 0.5})
    assert a["undefined_events"] == ["c"]
    assert a["mean_difference"] == pytest.approx(0.05)
    assert a == paired_event_summary(
        {"a": 0.8, "b": 0.3, "c": None}, {"a": 0.6, "b": 0.4, "c": 0.5}
    )
    assert paired_event_summary({"a": 1}, {"a": 0.5})["event_bootstrap_interval"] is None
    with pytest.raises(ValueError, match="census"):
        paired_event_summary({"a": 1}, {"b": 1})


def test_interpolated_display_peak_is_not_measured_peak():
    index = pd.date_range("2021-07-15", periods=4, freq="h", tz="UTC")
    f = pd.DataFrame({"q_strict": [1, np.nan, 4, 2], "q_display": [1, 3, 4, 2]}, index=index)
    a = acquisition_context(f, "2021-07-15T01:30Z", index[0], index[-1])
    assert not a["measured_peak_verified_in_window"]
    assert a["measured"]["window_peak_utc"] is None
    assert a["display_proxy"]["window_peak_utc"] == "2021-07-15T02:00:00+00:00"
    assert a["display_proxy"]["local_trend"] == "rising"
    assert a["display_proxy"]["acquisition_hours_from_window_peak"] == -0.5
    with pytest.raises(ValueError, match="timezone"):
        acquisition_context(f, "2021-07-15T01:30", index[0], index[-1])


def test_standard_unet_supports_binary_and_three_class_odd_grids():
    torch = pytest.importorskip("torch")
    from applied_unet import StandardUNet

    torch.set_num_threads(1)
    for channels, classes in [(2, 2), (4, 3)]:
        model = StandardUNet(channels, classes)
        y = model(torch.randn(2, channels, 33, 35))
        assert tuple(y.shape) == (2, classes, 33, 35)
        y.mean().backward()
        assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in model.parameters())


def test_execution_manifest_preserves_full_crossproduct(tmp_path):
    if not (
        ROOT / "results/applied_study_v1/evaluation/radar-change-grouped-folds.parquet"
    ).exists():
        pytest.skip("Acquired full inventory is local-only")
    path = tmp_path / "plan.json"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/199_prepare_applied_execution.py"),
            "--output",
            str(path),
        ],
        check=True,
    )
    p = json.loads(path.read_text())
    assert p["neural_candidate_fits"] == 5724
    assert p["physical_calibrations"] == 53
    assert len({j["id"] for j in p["jobs"]}) == 1961
    for task, folds in [("terramind", 11), ("galileo", 11), ("prithvi", 11), ("copernicus", 20)]:
        for learner in ["native", "unet", "unet_standard", "linear"]:
            jobs = [j for j in p["jobs"] if j["task"] == task and j["learner"] == learner]
            assert len(jobs) == folds * 3 * 3
            assert {j["budget"] for j in jobs} == {1.0, 0.2, 0.05}
            assert {j["seed"] for j in jobs} == {42, 1729, 31415}


def test_pending_census_never_becomes_a_small_final_comparison(tmp_path):
    plan = tmp_path / "plan.json"
    plan.write_text(
        json.dumps(
            {
                "jobs": [
                    dict(
                        id="terramind-native-fold-1-42",
                        task="terramind",
                        learner="native",
                        budget=1.0,
                        fold="fold",
                        seed=42,
                        output=str(tmp_path / "absent"),
                    )
                ]
            }
        )
    )
    out = tmp_path / "summary.json"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/198_summarize_applied_comparisons.py"),
            "--plan",
            str(plan),
            "--output",
            str(out),
        ],
        check=True,
    )
    summary = json.loads(out.read_text())
    for c in summary["comparisons"]:
        if c["task"] == "terramind" and c["budget"] == 1:
            assert not c["complete_census"] and c["summary"] is None and c["missing_jobs"]


def test_completed_seed_repeats_remain_one_event_for_uncertainty(tmp_path):
    jobs = []
    for seed in [42, 1729, 31415]:
        for learner, matrix in [("native", [[10, 0], [2, 8]]), ("unet", [[10, 0], [6, 4]])]:
            folder = tmp_path / f"{learner}-{seed}"
            folder.mkdir()
            (folder / "manifest.json").write_text(
                json.dumps({"partitions": {"test": ["held-chip"]}})
            )
            (folder / "selection.json").write_text(json.dumps({"status": "completed"}))
            (folder / "selected-test.json").write_text(
                json.dumps({"confusion": {"one-storm": matrix}})
            )
            jobs.append(
                dict(
                    id=f"terramind-{learner}-fold-1-{seed}",
                    task="terramind",
                    learner=learner,
                    budget=1.0,
                    seed=seed,
                    fold="fold",
                    output=str(folder),
                )
            )
    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps({"jobs": jobs}))
    out = tmp_path / "summary.json"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/198_summarize_applied_comparisons.py"),
            "--plan",
            str(plan),
            "--output",
            str(out),
        ],
        check=True,
    )
    c = next(
        c
        for c in json.loads(out.read_text())["comparisons"]
        if c["task"] == "terramind" and c["budget"] == 1 and c["control"] == "unet"
    )
    assert c["complete_census"]
    assert c["summary"]["mean_difference"] == pytest.approx(0.4)
    assert c["summary"]["defined_events"] == ["one-storm"]
    assert c["summary"]["event_bootstrap_interval"] is None
