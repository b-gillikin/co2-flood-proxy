"""Validation-only full-label tuning reuse across independent seed repeats."""

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
        arguments["budget"] != 1.0
        or arguments["seed"] == 42
        or original["budget"] != 1.0
        or original["seed"] != 42
    ):
        raise ValueError("Reuse is only from full-label seed42 to full-label repeat seeds")
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
    ]:
        if original.get(key) != arguments.get(key):
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
        selection="Full-label seed42 validation winner; no held-test score read",
        source_hashes={
            name: sha(source / name)
            for name in ["manifest.json", "selection.json", "trials.json", "complete.json"]
        },
        source_seed=42,
        target_seed=arguments["seed"],
        learning_rate=float(winner["lr"]),
    )
