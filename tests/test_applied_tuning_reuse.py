"""Reuse only full-label validation tuning, never information from other masks."""

import json

import pytest

from applied_execution import atomic, sha
from applied_tuning_reuse import fixed_learning_rate


def source_fit(tmp_path):
    args = dict(
        task="galileo",
        learner="linear",
        fold="event",
        batch_size=256,
        device="cpu",
        precision="float32",
        tensor_cache="/cache",
        feature_cache=None,
        on_device_pool=True,
        budget=1.0,
        seed=42,
    )
    parts = dict(train=["a", "b"], valid=["c"], test=["d"])
    manifest = dict(arguments=args, epochs=50, partitions=parts, rates=[1e-4, 1e-3, 1e-2])
    trials = [
        dict(trial=i, lr=rate, status="completed", validation_iou=value)
        for i, (rate, value) in enumerate(zip(manifest["rates"], [0.4, 0.7, 0.5], strict=True))
    ]
    atomic(tmp_path / "manifest.json", manifest)
    atomic(tmp_path / "selection.json", trials[1])
    atomic(tmp_path / "trials.json", trials)
    atomic(
        tmp_path / "complete.json",
        dict(
            status="verified_complete",
            manifest_sha256=sha(tmp_path / "manifest.json"),
            selected_trial=1,
        ),
    )
    return dict(args, seed=1729), parts


def test_reuses_validation_winner_without_test_results_or_checkpoint(tmp_path):
    args, parts = source_fit(tmp_path)
    rate, record = fixed_learning_rate(tmp_path, args, parts, 50)
    assert rate == 1e-3 and record["target_seed"] == 1729
    assert "selected-test.json" not in record["source_hashes"]


@pytest.mark.parametrize(
    "change",
    [
        dict(budget=0.2),
        dict(budget=0.05),
        dict(seed=42),
        dict(fold="other"),
        dict(learner="native"),
        dict(batch_size=64),
    ],
)
def test_rejects_changed_masks_or_configurations(tmp_path, change):
    args, parts = source_fit(tmp_path)
    with pytest.raises(ValueError):
        fixed_learning_rate(tmp_path, dict(args, **change), parts, 50)


def test_rejects_changed_partition_and_nonwinner(tmp_path):
    args, parts = source_fit(tmp_path)
    with pytest.raises(ValueError, match="membership"):
        fixed_learning_rate(tmp_path, args, dict(parts, train=["a"]), 50)
    selected = json.loads((tmp_path / "selection.json").read_text())
    selected["trial"] = 0
    atomic(tmp_path / "selection.json", selected)
    with pytest.raises(ValueError, match="winner"):
        fixed_learning_rate(tmp_path, args, parts, 50)
