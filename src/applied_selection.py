"""Small, explicit validation policies for the named spatial task comparisons."""

import math


def learning_rates(task, learner):
    """Equal three-trial allowance; rates need not be numerically identical."""
    if learner not in {"native", "unet", "linear"}:
        raise ValueError("Unknown learner")
    if task not in {"terramind", "galileo", "prithvi", "copernicus"}:
        raise ValueError("Unknown task")
    if learner != "native":
        return [1e-4, 1e-3, 1e-2]
    center = {"terramind": 2e-5, "galileo": 1e-3, "prithvi": 5e-5, "copernicus": 1e-3}[task]
    return [center / 5, center, center * 5]


def select_trial(trials):
    """Validation only. Stable earlier-trial tie break; no test-derived ordering."""
    valid = [
        r
        for r in trials
        if r.get("status") == "completed"
        and r.get("validation_iou") is not None
        and math.isfinite(r["validation_iou"])
    ]
    if not valid:
        raise ValueError("No finite validation result; retain failures and do not score test")
    return max(valid, key=lambda r: r["validation_iou"])
