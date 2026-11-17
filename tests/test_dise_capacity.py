"""Fair capacity reuse and selection must not respond to held-out scores."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.dise_capacity import reuse_early_stopped, same_final_spec, select_validation


def test_only_genuine_early_stops_are_reusable():
    assert reuse_early_stopped(dict(fitted_boosting_rounds=700, tree_cap_hit=False), 1500)
    assert not reuse_early_stopped(dict(fitted_boosting_rounds=1500, tree_cap_hit=True), 1500)
    with pytest.raises(ValueError):
        reuse_early_stopped(dict(fitted_boosting_rounds=1500, tree_cap_hit=False), 1500)


def test_validation_selection_weights_groups_not_fold_count():
    records = []
    for candidate, values in [(0, [1.0, 3.0]), (1, [2.5, 2.5])]:
        for fold, (rmse, n) in enumerate(zip(values, [1, 9], strict=True)):
            records.append(
                dict(
                    candidate_index=candidate,
                    fold=fold,
                    validation_rmse=rmse,
                    validation_mae=rmse,
                    validation_groups=n,
                    best_iteration=29 + 10 * fold,
                )
            )
    result = select_validation(records, "native_rmse", [{"max_depth": 2}, {"max_depth": 4}])
    assert result["candidate_index"] == 1 and result["trees"] == 35 and result["criterion"] == 6.25
    with pytest.raises(ValueError):
        select_validation(records + records[:1], "native_rmse", [{}, {}])


def test_final_reuse_requires_same_fitted_model_specification():
    original = dict(parameters={"max_depth": 4, "learning_rate": 0.1}, trees=500, criterion=0.7)
    assert same_final_spec(original, dict(original, criterion=0.6))
    assert not same_final_spec(original, dict(original, trees=501))
    assert not same_final_spec(
        original, dict(original, parameters={"max_depth": 2, "learning_rate": 0.1})
    )
