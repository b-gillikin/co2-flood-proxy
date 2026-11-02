"""Whole-event five-fold cross-fitting and fixed nested annotation masks.

Grouping uses source identity/count only, never class balance, model score or
local results. Every event/chip is tested once. Optimization seeds vary training,
not the labels available to it. Early stopping reads validation only.
"""

import hashlib
import math

from applied_water import audit_partitions

SEEDS = (42, 1729, 31415)
BUDGETS = (1.0, 0.2, 0.05)


def grouped_partitions(inventory, n_splits=5):
    import pandas as pd
    from sklearn.model_selection import GroupKFold

    inventory = inventory.rename(columns={"record": "chip"}).copy()
    if inventory.chip.duplicated().any() or inventory.event.nunique() < n_splits:
        raise ValueError("Require unique records and enough whole events")
    # Sorted input makes grouping deterministic across original file order.
    inventory = inventory.sort_values(["event", "chip"]).reset_index(drop=True)
    splitter = GroupKFold(n_splits=n_splits)
    group_sets = [
        set(inventory.iloc[test].event)
        for _, test in splitter.split(inventory, groups=inventory.event)
    ]
    folds = []
    for i, test_events in enumerate(group_sets):
        valid_events = group_sets[(i + 1) % n_splits]
        frame = inventory[["chip", "event"]].copy()
        frame["fold"] = f"group{i + 1:02d}"
        frame["role"] = [
            "test" if e in test_events else "valid" if e in valid_events else "train"
            for e in frame.event
        ]
        folds.append(frame)
    folds = pd.concat(folds, ignore_index=True)
    audit_partitions(folds)
    subsets = []
    for fold, training in folds[folds.role == "train"].groupby("fold"):
        for event, rows in training.groupby("event"):
            chips = sorted(
                rows.chip, key=lambda c: hashlib.sha256(f"label-mask-42:{c}".encode()).digest()
            )
            for budget in BUDGETS:
                selected = chips[: max(1, math.ceil(len(chips) * budget))]
                for seed in SEEDS:
                    subsets.extend(
                        dict(fold=fold, event=event, chip=c, budget=budget, seed=seed)
                        for c in selected
                    )
    return folds, pd.DataFrame(subsets)


class ValidationStop:
    def __init__(self, patience=0, minimum=0, min_delta=1e-4):
        if patience < 0 or minimum < 0 or min_delta < 0:
            raise ValueError("Stopping settings must be nonnegative")
        self.patience, self.minimum, self.min_delta = patience, minimum, min_delta
        self.best = None
        self.last_improvement = 0

    def update(self, epoch, value):
        if value is None or not math.isfinite(value):
            return False
        if self.best is None or value > self.best + self.min_delta:
            self.best = value
            self.last_improvement = epoch
        return bool(
            self.patience
            and epoch >= self.minimum
            and epoch - self.last_improvement >= self.patience
        )
