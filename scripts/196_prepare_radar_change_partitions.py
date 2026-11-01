"""Whole-activation radar-change folds, keeping the full 5,000-record census.

Published tile splits share all20 events; they cannot establish new-event
transfer. Validation rotates to the next sorted whole activation, as for Sen1.
"""

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import numpy as np
import pandas as pd

from applied_water import audit_partitions


def main():
    base = ROOT / "results/applied_study_v1/evaluation"
    source = base / "radar-change-inventory.parquet"
    inventory = pd.read_parquet(source).rename(columns={"record": "chip"})
    if inventory.chip.duplicated().any():
        raise ValueError("Duplicate source identities")
    groups = sorted(inventory.event.unique())
    folds = []
    for i, held in enumerate(groups):
        valid = groups[(i + 1) % len(groups)]
        part = inventory[["chip", "event"]].copy()
        part["fold"] = held
        part["role"] = np.where(
            part.event == held, "test", np.where(part.event == valid, "valid", "train")
        )
        folds.append(part)
    folds = pd.concat(folds, ignore_index=True)
    audit_partitions(folds)
    subsets = []
    for fold, part in folds[folds.role == "train"].groupby("fold"):
        for seed in [42, 1729, 31415]:
            for event, train in part.groupby("event"):
                chips = sorted(
                    train.chip, key=lambda c: hashlib.sha256(f"{seed}:{c}".encode()).digest()
                )
                for budget in [1.0, 0.2, 0.05]:
                    subsets += [
                        dict(fold=fold, seed=seed, budget=budget, chip=chip, event=event)
                        for chip in chips[: max(1, int(np.ceil(budget * len(chips))))]
                    ]
    folds.to_parquet(base / "radar-change-grouped-folds.parquet", index=False)
    pd.DataFrame(subsets).to_parquet(base / "radar-change-label-subsets.parquet", index=False)
    report = dict(
        events=len(groups),
        records=len(inventory),
        folds=len(groups),
        tested_once=not folds[folds.role == "test"].chip.duplicated().any(),
        budget_meaning="nested whole labeled chips within every training activation; not fewer independent events",
        inventory_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    )
    (base / "radar-change-partitions.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report))


if __name__ == "__main__":
    main()
