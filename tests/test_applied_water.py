import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("applied_water", ROOT / "src/applied_water.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def test_unknown_dry_and_partial_zero_bands():
    y = np.array([[0, 1], [-1, 0]])
    radar = np.ones((2, 2, 2))
    optical = np.ones((13, 2, 2))
    optical[0, 0, 0] = 0  # a zero single band is not an all-zero observation
    radar[0, 0, 1] = np.nan
    optical[:, 1, 1] = 0
    assert m.valid_labels(y, radar, optical).tolist() == [[0, -1], [-1, -1]]
    assert (m.valid_labels(np.zeros((2, 2), dtype=int), np.ones((2, 2, 2))) == 0).all()


def test_normalizer_is_author_default_not_z_score():
    mean = np.array([-11.728724389184965, -18.85558188024017])[:, None, None]
    assert np.allclose(m.galileo_radar_norm(mean), 0.5)
    assert m.PRITHVI_S2 == [1, 2, 3, 8, 11, 12]


def test_confusion_unknown_and_undefined():
    c = m.confusion(np.array([0, 0, 1, 1, -1]), np.array([0, 1, 0, 1, 99]))
    assert c.tolist() == [[1, 1], [1, 1]]
    assert np.allclose(m.class_scores(c)["iou"], [1 / 3, 1 / 3])
    dry = m.class_scores(m.confusion(np.array([0, 0]), np.array([0, 0])))
    assert np.isnan(dry["iou"][1]) and dry["iou"][0] == 1
    with pytest.raises(ValueError):
        m.confusion(np.array([0]), np.array([-1]))


def test_event_leakage_is_rejected():
    rows = []
    for i in range(3):
        for j in range(3):
            rows.append(
                dict(
                    fold=i,
                    chip=str(j),
                    event=str(j),
                    role="test" if i == j else "valid" if j == (i + 1) % 3 else "train",
                )
            )
    f = pd.DataFrame(rows)
    m.audit_partitions(f)
    bad = pd.concat([f, pd.DataFrame([dict(fold=0, chip="new", event="0", role="train")])])
    with pytest.raises(ValueError, match="Event leakage"):
        m.audit_partitions(bad)


def test_real_grouped_census_and_nested_budgets_if_prepared():
    base = ROOT / "results/applied_study_v1/evaluation"
    if not (base / "sen1-grouped-folds.parquet").exists():
        pytest.skip("Acquired dataset partition audit is not a repository fixture")
    folds = pd.read_parquet(base / "sen1-grouped-folds.parquet")
    m.audit_partitions(folds)
    subsets = pd.read_parquet(base / "sen1-label-subsets.parquet")
    for (fold, _seed), rows in subsets.groupby(["fold", "seed"]):
        low, mid, full = [set(rows.loc[rows.budget == b, "chip"]) for b in [0.05, 0.2, 1.0]]
        assert low <= mid <= full
        assert full == set(folds.loc[(folds.fold == fold) & (folds.role == "train"), "chip"])


def test_spatial_task_retains_dry_patches_and_uses_real_date(monkeypatch):
    pytest.importorskip("torch")
    spec = importlib.util.spec_from_file_location(
        "applied_runner", ROOT / "scripts/185_run_applied_water.py"
    )
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    y = np.zeros((512, 512), dtype=int)
    y[0, 0] = -1
    radar = np.full((2, 512, 512), -12, dtype=np.float32)
    optical = np.full((13, 512, 512), 1000, dtype=np.float32)
    monkeypatch.setattr(runner, "read_chip", lambda chip, task=None: (y, radar, optical))
    rows = pd.DataFrame(
        [
            dict(
                chip="example",
                event="event",
                s1_date="2021/01/16",
                s2_date="2021/01/19",
                top=51.0,
                bottom=50.0,
                left=6.0,
                right=7.0,
            )
        ]
    )
    radar_task = runner.Chips(rows, "galileo")
    assert len(radar_task) == 64
    assert radar_task[0]["y"][0, 0] == -1
    assert (radar_task[63]["y"] == 0).all()  # dry subpatch retained
    assert radar_task[0]["month"] == 0  # January, not a fabricated July default
    optical_task = runner.Chips(rows, "prithvi")[0]
    assert optical_task["x"].shape == (6, 224, 224)
    assert optical_task["y"].shape == (512, 512)  # original-grid evaluation
    assert optical_task["temporal"].tolist() == [[2021.0, 19.0]]


def test_restore_refuses_other_chapters_and_symlink(tmp_path):
    spec = importlib.util.spec_from_file_location(
        "applied_restore", ROOT / "scripts/182_restore_offloaded_expansion.py"
    )
    restore = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(restore)
    with pytest.raises(ValueError):
        restore.destination("../chapter3/data/file.tif", tmp_path)
    with pytest.raises(ValueError):
        restore.destination("data/raw/other_chapter/file.tif", tmp_path)
    directory = tmp_path / "data/raw/limburg_eo_expansion"
    directory.mkdir(parents=True)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    (directory / "images").symlink_to(elsewhere)
    with pytest.raises(ValueError, match="symlink"):
        restore.destination("data/raw/limburg_eo_expansion/images/x.tif", tmp_path)
