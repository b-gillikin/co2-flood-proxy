"""Scientific failure modes: selection leakage, trace/unknown masks, semantics."""

import numpy as np
import pytest

from applied_local_reference import reference_agreement, reference_labels
from applied_selection import learning_rates, select_trial


def test_selection_ignores_test_and_failed_candidates():
    trials = [
        dict(status="completed", validation_iou=0.4, test_iou=0.99),
        dict(status="completed", validation_iou=0.6, test_iou=0.1),
        dict(status="failed", validation_iou=0.9),
        dict(status="completed", validation_iou=float("nan")),
    ]
    assert select_trial(trials) is trials[1]
    with pytest.raises(ValueError):
        select_trial(trials[2:])
    assert select_trial([trials[0], dict(trials[0])]) is trials[0]


def test_equal_trial_allowance_not_same_rate():
    for task in ["terramind", "galileo", "prithvi", "copernicus"]:
        assert len(learning_rates(task, "native")) == len(learning_rates(task, "unet")) == 3
        assert learning_rates(task, "unet") == learning_rates(task, "linear")
    assert learning_rates("terramind", "native") != learning_rates("terramind", "unet")


def test_trace_is_not_dry_and_hydrography_is_not_flood():
    assessed = np.array([1, 1, 1, 1, 0, 1, 1], bool)
    wet = np.array([0, 1, 0, 1, 1, 0, 0], bool)
    trace = np.array([0, 0, 1, 1, 0, 0, 0], bool)
    hydro = np.array([0, 0, 0, 0, 0, 1, 0], bool)
    stream = np.array([0, 0, 0, 0, 0, 0, 1], bool)
    assert reference_labels(assessed, wet, trace, hydro, stream).tolist() == [
        0,
        1,
        255,
        1,
        255,
        255,
        255,
    ]


def test_task_semantics_and_unknown_support():
    ref = np.array([0, 1, 1, 255, 0])
    valid = np.array([1, 1, 0, 1, 1])
    water = reference_agreement(ref, np.array([0, 1, 0, 1, 1]), valid, "surface_water")
    change = reference_agreement(ref, np.array([0, 2, 0, 2, 2]), valid, "three_class_flood")
    assert water == change
    assert water["tp"] == water["fp"] == water["tn"] == 1
    assert water["support_pixels"] == 3
    empty = reference_agreement(np.array([255]), np.array([1]), np.array([1]), "surface_water")
    assert empty["recall"] is None and empty["iou"] is None


def test_local_cli_uses_intersection_and_rejects_misalignment(tmp_path):
    import json
    import subprocess
    import sys
    from pathlib import Path

    import rasterio
    from rasterio.transform import from_origin

    paths = {}
    for name, values in {
        "reference": [[0, 1], [1, 255]],
        "a": [[0, 1], [0, 1]],
        "b": [[0, 2], [2, 2]],
        "va": [[1, 1], [1, 1]],
        "vb": [[1, 1], [0, 1]],
    }.items():
        path = tmp_path / f"{name}.tif"
        with rasterio.open(
            path,
            "w",
            driver="GTiff",
            width=2,
            height=2,
            count=1,
            dtype="uint8",
            crs="EPSG:32631",
            transform=from_origin(0, 20, 10, 10),
        ) as ds:
            ds.write(np.array(values, dtype="uint8"), 1)
        paths[name] = str(path)
    rows = [
        dict(
            case="one-acquisition",
            grid="0",
            model=m,
            prediction=paths[m],
            valid=paths["v" + m],
            reference=paths["reference"],
            kind=k,
            reference_offset_hours=6.6,
            reference_dependence="different source sensor",
        )
        for m, k in [("a", "surface_water"), ("b", "three_class_flood")]
    ]
    manifest = tmp_path / "inputs.json"
    manifest.write_text(json.dumps(rows))
    runner = Path(__file__).resolve().parents[1] / "scripts/195_score_local_reference_agreement.py"
    out = tmp_path / "scores.json"
    subprocess.run([sys.executable, str(runner), str(manifest), "--output", str(out)], check=True)
    scores = json.loads(out.read_text())["results"]
    assert all(r["metrics"]["support_pixels"] == 2 for r in scores)
    assert all(r["metrics"]["iou"] == 1 for r in scores)
    with rasterio.open(paths["b"], "r+") as ds:
        ds.transform = from_origin(10, 20, 10, 10)
    failed = subprocess.run(
        [sys.executable, str(runner), str(manifest), "--output", str(tmp_path / "bad.json")],
        capture_output=True,
    )
    assert failed.returncode != 0 and b"Raster grids differ" in failed.stderr


def test_copernicus_source_scale_and_missingness():
    pytest.importorskip("torch")
    from applied_copernicus import normalize_radar

    raw = np.ones((4, 2, 2), dtype=np.float32) * 0.1
    raw[0, 0, 0] = 0
    raw[2, 1, 0] = np.nan
    normalized, valid = normalize_radar(raw)
    assert valid.tolist() == [[False, True], [False, True]]
    assert np.isfinite(normalized).all()
    assert (normalized[:, ~valid] == 0).all()
    # Preserve the author's unusual post std; do not silently substitute pre.
    assert normalized[0, 0, 1] == pytest.approx((0.1 - 0.0981) / 0.0430)
    assert normalized[2, 0, 1] == pytest.approx((0.1 - 0.0981) / 0.0981)


def test_radar_change_full_event_census():
    from pathlib import Path

    import pandas as pd

    from applied_water import audit_partitions

    base = Path(__file__).resolve().parents[1] / "results/applied_study_v1/evaluation"
    path = base / "radar-change-grouped-folds.parquet"
    if not path.exists():
        pytest.skip("Local acquired inventory not present in a clean checkout")
    folds = pd.read_parquet(path)
    audit_partitions(folds)
    assert len(folds[folds.role == "test"]) == 5000
    assert folds.fold.nunique() == 20
    subsets = pd.read_parquet(base / "radar-change-label-subsets.parquet")
    for _, rows in subsets.groupby(["fold", "seed"]):
        sets = {b: set(g.chip) for b, g in rows.groupby("budget")}
        assert sets[0.05] <= sets[0.2] <= sets[1.0]
