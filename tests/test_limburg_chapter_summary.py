import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd


def module():
    path = Path(__file__).resolve().parents[1] / "scripts/244_summarize_chapter_scores.py"
    spec = importlib.util.spec_from_file_location("chapter_summary", path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def test_bootstrap_resamples_blocks_not_tiles_or_activation_count():
    m = module()
    values = pd.Series({"a": 0.0, "b": 0.2, "c": 0.8})
    result, omissions = m.block_estimate(values, {"a": "one", "b": "one", "c": "two"})
    assert result["estimate"] == 0.45
    assert result["blocks"] == 2
    assert result["activations"] == 3
    assert np.isclose(result["activation_balanced_mean"], 1/3)
    assert sorted(row["estimate"] for row in omissions) == [0.1, 0.8]


def test_event_iou_uses_pooled_confusion_not_mean_tile_iou():
    m = module()
    counts = pd.DataFrame({"c20": [2, 0], "c21": [0, 0], "c22": [2, 0], "c02": [0, 0], "c12": [0, 0]})
    values = m.iou_from_counts(counts)
    assert values.iloc[0] == 0.5
    assert pd.isna(values.iloc[1])


def test_interaction_is_difference_of_paired_reference_effects():
    m = module()
    terms = m.contrasts()["interaction__native_minus_unet"]
    values = {("native", "ee", "p1", "paired"): 0.7,
              ("native", "ee", "p0", "paired"): 0.4,
              ("unet", "ee", "p1", "paired"): 0.6,
              ("unet", "ee", "p0", "paired"): 0.5}
    assert np.isclose(sum(values[key]*coefficient for key, coefficient in terms.items()), 0.2)
