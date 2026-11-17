"""Outcome-blind capacity reuse and validation selection rules."""

from __future__ import annotations

import numpy as np
import pandas as pd


def reuse_early_stopped(record, old_limit):
    rounds = int(record["fitted_boosting_rounds"])
    if bool(record["tree_cap_hit"]) != (rounds == old_limit):
        raise ValueError("Inconsistent original tree-cap metadata")
    if rounds > old_limit or rounds < 1:
        raise ValueError("Original boosting rounds outside declared budget")
    return rounds < old_limit


def select_validation(records, policy, candidates):
    table = pd.DataFrame(records)
    if table.duplicated(["candidate_index", "fold"]).any():
        raise ValueError("Duplicated candidate/fold")
    if not table.validation_groups.gt(0).all():
        raise ValueError("Validation group weight must be positive")
    metric = table.validation_rmse**2 if policy == "native_rmse" else table.validation_mae
    weighted = metric * table.validation_groups
    criterion = (
        weighted.groupby(table.candidate_index).sum()
        / table.groupby("candidate_index").validation_groups.sum()
    )
    winner = int(criterion.idxmin())
    trees = int(np.median(table.loc[table.candidate_index.eq(winner), "best_iteration"])) + 1
    return dict(
        candidate_index=winner,
        parameters=candidates[winner],
        trees=trees,
        criterion=float(criterion.loc[winner]),
        criterion_scale="MSE" if policy == "native_rmse" else "MAE",
    )


def same_final_spec(original, reselected):
    return (
        original["parameters"] == reselected["parameters"]
        and original["trees"] == reselected["trees"]
    )
