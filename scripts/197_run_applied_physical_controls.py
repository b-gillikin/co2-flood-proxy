"""Validation-only physical controls, then one selected full held-event test.

Uses exactly the named task's input tensors and target masks. Fixed threshold0
optical controls are reported on validation, alongside selection over the
declared grid; test is evaluated only for the validation-selected candidate.
No training-chip labels are used. A deterministic control is reused across
neural label budgets/seeds, not counted as repeated independent evidence.
"""

import argparse
import hashlib
import importlib.util
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault(
    "PROJ_DATA", str((ROOT / ".venv-foundation/bin/python").resolve().parents[1] / "share/proj")
)

import numpy as np
import pandas as pd
import torch
from torch.nn import functional as F
from torch.utils.data import DataLoader

from applied_physical import candidates, predict, source_features
from applied_selection import select_trial
from applied_water import audit_partitions, class_scores, confusion


def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument(
        "--task", choices=["terramind", "galileo", "prithvi", "copernicus"], required=True
    )
    p.add_argument("--fold", required=True)
    p.add_argument("--run", action="store_true")
    p.add_argument("--evaluate-selected", action="store_true")
    p.add_argument("--output-root", type=Path, default=ROOT / "results/applied_study_v2/physical")
    a = p.parse_args()
    grid = candidates(a.task)
    fixed = (
        [dict(method=m, threshold=0.0) for m in ["ndwi", "mndwi"]]
        if a.task in {"terramind", "prithvi"}
        else []
    )
    print(
        json.dumps(
            dict(
                task=a.task,
                fold=a.fold,
                candidates=len(grid),
                test_passes=int(a.evaluate_selected),
                predefined_fixed_optical_controls=len(fixed),
            )
        )
    )
    if not a.run:
        return
    torch.set_num_threads(1)
    spec = importlib.util.spec_from_file_location(
        "held_water_task", ROOT / "scripts/185_run_applied_water.py"
    )
    w = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(w)
    if a.task == "copernicus":
        import applied_change_task as w
    prefix = "radar-change" if a.task == "copernicus" else "sen1"
    invpath = w.PARTITIONS / (
        "radar-change-inventory.parquet"
        if a.task == "copernicus"
        else "sen1-chip-inventory.parquet"
    )
    inv = pd.read_parquet(invpath).rename(columns={"record": "chip"})
    foldpath = w.PARTITIONS / f"{prefix}-grouped-folds.parquet"
    folds = pd.read_parquet(foldpath)
    audit_partitions(folds)
    fold = folds[folds.fold == a.fold]
    if fold.empty:
        raise ValueError("Unknown fold")
    rows = {
        role: inv[inv.chip.isin(fold.loc[fold.role == role, "chip"])].copy()
        for role in ["valid", "test"]
    }
    out = a.output_root / f"{a.task}-{a.fold}"
    out.mkdir(parents=True, exist_ok=False)
    sourcepaths = [
        Path(__file__),
        ROOT / "src/applied_physical.py",
        ROOT / "src/applied_selection.py",
        ROOT / "scripts/185_run_applied_water.py",
        ROOT / "src/applied_water.py",
        ROOT / "src/applied_change_task.py",
        ROOT / "src/applied_copernicus.py",
        invpath,
        foldpath,
    ]
    manifest = dict(
        task=a.task,
        fold=a.fold,
        learner="physical",
        threshold_grid=grid,
        fixed_optical_controls=fixed,
        partitions={k: sorted(v.chip) for k, v in rows.items()},
        source_hashes={
            str(s.relative_to(ROOT)): hashlib.sha256(s.read_bytes()).hexdigest()
            for s in sourcepaths
        },
        label_accounting=dict(
            training_chips=0,
            validation_chips=len(rows["valid"]),
            test_chips=len(rows["test"]),
            note="Only validation labels select thresholds",
        ),
        support="Same task tensors and masks; optical index uses available green/NIR/SWIR subset; simple SAR control is not an operational GFM reproduction",
    )
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    classes = 3 if a.task == "copernicus" else 2
    target = classes - 1

    def evaluate(role, options, destination=None):
        matrices = [{} for _ in options]
        predictions = {}
        start = time.perf_counter()
        for batch in DataLoader(w.Chips(rows[role], a.task), batch_size=1, shuffle=False):
            label = batch["y"][0].numpy()
            features = source_features(batch["x"][0].numpy(), a.task)
            # Retain the224px Prithvi input information, project continuous
            # indices to the common target grid before thresholding.
            if next(iter(features.values())).shape[-2:] != label.shape:
                features = {
                    k: F.interpolate(
                        torch.tensor(v.copy())[None, None].float(),
                        size=label.shape,
                        mode="bilinear",
                        align_corners=False,
                    )[0, 0].numpy()
                    for k, v in features.items()
                }
            for i, option in enumerate(options):
                predicted = predict(features, option)
                event = batch["event"][0]
                matrices[i].setdefault(event, np.zeros((classes, classes), dtype=np.int64))
                matrices[i][event] += confusion(label, predicted, classes=classes)
                if destination:
                    chip = batch["chip"][0]
                    part = int(batch["part"][0])
                    predictions.setdefault(
                        chip,
                        np.full(
                            label.shape if a.task == "copernicus" else (512, 512),
                            255,
                            dtype=np.uint8,
                        ),
                    )
                    y = np.where(label >= 0, predicted, 255).astype(np.uint8)
                    if a.task == "galileo":
                        top, left = (part // 8) * 64, (part % 8) * 64
                        predictions[chip][top : top + 64, left : left + 64] = y
                    else:
                        predictions[chip] = y
        if destination:
            destination.mkdir(parents=True, exist_ok=False)
            for chip, y in predictions.items():
                np.savez_compressed(destination / f"{chip}.npz", prediction=y, unknown_code=255)
        results = []
        for option, counts in zip(options, matrices, strict=True):
            scores = {
                e: float(v) if np.isfinite(v) else None
                for e, m in counts.items()
                for v in [class_scores(m)["iou"][target]]
            }
            valid = [v for v in scores.values() if v is not None]
            results.append(
                dict(
                    candidate=option,
                    event_iou=scores,
                    mean_event_iou=float(np.mean(valid)) if valid else None,
                    confusion={e: m.tolist() for e, m in counts.items()},
                )
            )
        return results, time.perf_counter() - start

    values, elapsed = evaluate("valid", grid)
    trials = [
        dict(trial=i, status="completed", validation_iou=v["mean_event_iou"], **v)
        for i, v in enumerate(values)
    ]
    (out / "trials.json").write_text(json.dumps(trials, indent=2))
    winner = select_trial(trials)
    selection = dict(
        winner,
        validation_wall_s=elapsed,
        selection="Validation-only equal-event target IoU; first candidate wins ties",
    )
    (out / "selection.json").write_text(json.dumps(selection, indent=2))
    if a.evaluate_selected:
        result, elapsed = evaluate("test", [winner["candidate"]], out / "predictions")
        (out / "selected-test.json").write_text(
            json.dumps(dict(**result[0], test_scoring_wall_s=elapsed), indent=2)
        )
        if fixed:
            values, elapsed = evaluate("test", fixed)
            (out / "fixed-test.json").write_text(
                json.dumps(
                    dict(
                        controls=values,
                        test_scoring_wall_s=elapsed,
                        interpretation="Threshold0 declared before test; no test-based choice among fixed controls",
                    ),
                    indent=2,
                )
            )


if __name__ == "__main__":
    main()
