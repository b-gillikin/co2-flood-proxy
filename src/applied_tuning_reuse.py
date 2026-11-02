"""Validation-only tuning reuse across seeds with identical annotation masks."""

import json
from pathlib import Path

from applied_execution import sha
from applied_selection import select_trial


def fixed_learning_rate(source, arguments, partitions, epochs):
    source = Path(source)
    manifest = json.loads((source / "manifest.json").read_text())
    complete = json.loads((source / "complete.json").read_text())
    selected = json.loads((source / "selection.json").read_text())
    trials = json.loads((source / "trials.json").read_text())
    original = manifest["arguments"]
    if (
        arguments["seed"] == 42
        or original["seed"] != 42
        or arguments["budget"] != original["budget"]
    ):
        raise ValueError("Reuse requires seed42 source, repeat seed, and the same label budget")
    if arguments["budget"] != 1.0 and not (
        arguments.get("shared_label_mask") and original.get("shared_label_mask")
    ):
        raise ValueError("Reduced-label reuse requires an explicit fixed shared annotation mask")
    defaults = dict(
        shared_label_mask=False,
        early_stop_patience=0,
        early_stop_min_epochs=0,
        early_stop_min_delta=0.0001,
    )
    for key in [
        "task",
        "learner",
        "fold",
        "batch_size",
        "device",
        "precision",
        "tensor_cache",
        "feature_cache",
        "on_device_pool",
        "evaluation_dir",
        "shared_label_mask",
        "early_stop_patience",
        "early_stop_min_epochs",
        "early_stop_min_delta",
    ]:
        if original.get(key, defaults.get(key)) != arguments.get(key, defaults.get(key)):
            raise ValueError("Tuning source has different configuration: " + key)
    if manifest["epochs"] != epochs or manifest["partitions"] != partitions:
        raise ValueError("Tuning source has different epoch or train/validation/test membership")
    if complete.get("status") != "verified_complete" or complete["manifest_sha256"] != sha(
        source / "manifest.json"
    ):
        raise ValueError("Source fit is not verified complete")
    if len(manifest["rates"]) != 3 or len(trials) != 3:
        raise ValueError("Source must retain the independent three-rate search")
    if any(float(r["lr"]) != float(manifest["rates"][r["trial"]]) for r in trials):
        raise ValueError("Source candidate rates differ from manifest")
    winner = select_trial(trials)
    if (
        selected["trial"] != winner["trial"]
        or selected["validation_iou"] != winner["validation_iou"]
        or complete["selected_trial"] != winner["trial"]
    ):
        raise ValueError("Source selection is not its validation winner")
    return float(winner["lr"]), dict(
        source=str(source),
        selection="Same-label-mask seed42 validation winner; no held-test score read",
        source_hashes={
            name: sha(source / name)
            for name in ["manifest.json", "selection.json", "trials.json", "complete.json"]
        },
        source_seed=42,
        target_seed=arguments["seed"],
        learning_rate=float(winner["lr"]),
    )
