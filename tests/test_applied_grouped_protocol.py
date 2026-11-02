"""Whole-event coverage, nested annotation accounting and validation stopping."""

import numpy as np
import pandas as pd
import pytest

from applied_grouped_protocol import ValidationStop, grouped_partitions


def inventory():
    return pd.DataFrame(
        [
            dict(chip=f"{event}-{i}", event=f"event{event}")
            for event in range(11)
            for i in range(2 + event)
        ]
    )


def test_all_events_and_records_tested_once_and_roles_disjoint():
    data = inventory()
    folds, subsets = grouped_partitions(data)
    assert folds.fold.nunique() == 5
    tests = folds[folds.role == "test"]
    assert set(tests.chip) == set(data.chip) and not tests.chip.duplicated().any()
    assert tests.groupby("event").fold.nunique().eq(1).all()
    assert folds.groupby(["fold", "event"]).role.nunique().eq(1).all()
    assert folds.groupby("fold").chip.nunique().eq(len(data)).all()
    for fold, part in subsets.groupby("fold"):
        train = set(folds[(folds.fold == fold) & (folds.role == "train")].chip)
        assert set(part.chip) == train
        masks = {}
        for budget in [1, 0.2, 0.05]:
            selected = [
                set(part[(part.seed == seed) & (part.budget == budget)].chip)
                for seed in [42, 1729, 31415]
            ]
            assert selected[0] == selected[1] == selected[2]
            masks[budget] = selected[0]
        assert masks[0.05] <= masks[0.2] <= masks[1]


def test_fold_assignment_ignores_row_order_and_labels():
    data = inventory()
    first, _ = grouped_partitions(data)
    shuffled = data.sample(frac=1, random_state=31415).assign(water_pixels=np.arange(len(data)))
    second, _ = grouped_partitions(shuffled)
    pd.testing.assert_frame_equal(first, second)


def test_stopping_waits_minimum_and_meaningful_plateau():
    stop = ValidationStop(patience=3, minimum=6, min_delta=0.001)
    assert not stop.update(1, 0.5)
    assert not stop.update(2, 0.50001)
    assert not stop.update(3, 0.50002)
    assert not stop.update(4, 0.50003)
    assert not stop.update(5, 0.50004)
    assert stop.update(6, 0.50005)


def test_improvement_resets_stopping_and_undefined_is_not_failure_evidence():
    stop = ValidationStop(patience=3, minimum=3, min_delta=0.001)
    assert not stop.update(1, 0.1)
    assert not stop.update(3, 0.2)
    assert not stop.update(4, float("nan"))
    assert not stop.update(5, None)
    assert stop.update(6, 0.2)
    disabled = ValidationStop()
    assert not disabled.update(100, 0.1)
    assert not disabled.update(1000, 0.1)


def test_rejects_invalid_identity_and_controls():
    data = inventory()
    with pytest.raises(ValueError):
        grouped_partitions(pd.concat([data, data.iloc[:1]]))
    with pytest.raises(ValueError):
        ValidationStop(patience=-1)


def test_ready_grid_retains_all_tasks_budgets_seeds_and_stopping():
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    path = root / "results/applied_study_v5/ready-v1/execution-plan.json"
    if not path.exists():
        pytest.skip("Held prepared grid unavailable")
    plan = json.loads(path.read_text())
    neural = [j for j in plan["jobs"] if j["learner"] != "physical"]
    assert len(neural) == 720 and len({j["output"] for j in neural}) == 720
    assert sum(j["learning_rate_candidates"] for j in neural) == 1200
    assert sum(j["learner"] == "physical" for j in plan["jobs"]) == 20
    sources = {
        (j["task"], j["learner"], j["fold"], j["budget"]): j["output"]
        for j in neural
        if j["seed"] == 42
    }
    for j in neural:
        assert "--epochs" not in j["command"]
        assert "--shared-label-mask" in j["command"]
        assert j["command"][j["command"].index("--early-stop-patience") + 1] == "10"
        assert "--evaluation-dir" in j["command"]
        if j["seed"] != 42:
            assert (
                j["tuning_source_output"]
                == sources[j["task"], j["learner"], j["fold"], j["budget"]]
            )
        else:
            assert "--fixed-lr-from" not in j["command"]


def test_supervisor_attaches_to_actual_owner_after_lock_rejection(monkeypatch):
    import importlib.util
    from pathlib import Path
    from types import SimpleNamespace

    path = Path(__file__).resolve().parents[1] / "scripts/223_run_optimized_spatial_queue.py"
    spec = importlib.util.spec_from_file_location("grouped_supervisor_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "alive", lambda pid: pid == 123)
    rejected = SimpleNamespace(pid=456, returncode=1)
    assert not module.controller_exit_is_failure(
        rejected, dict(controller_pid=123, status="running")
    )
    assert module.controller_exit_is_failure(rejected, dict(controller_pid=456, status="running"))
