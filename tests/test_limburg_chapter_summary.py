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
    assert np.isclose(result["activation_balanced_mean"], 1 / 3)
    assert sorted(row["estimate"] for row in omissions) == [0.1, 0.8]


def test_event_iou_uses_pooled_confusion_not_mean_tile_iou():
    m = module()
    counts = pd.DataFrame(
        {"c20": [2, 0], "c21": [0, 0], "c22": [2, 0], "c02": [0, 0], "c12": [0, 0]}
    )
    values = m.iou_from_counts(counts)
    assert values.iloc[0] == 0.5
    assert pd.isna(values.iloc[1])


def test_interaction_is_difference_of_paired_reference_effects():
    m = module()
    terms = m.contrasts()["interaction__native_minus_unet"]
    values = {
        ("native", "ee", "p1", "paired"): 0.7,
        ("native", "ee", "p0", "paired"): 0.4,
        ("unet", "ee", "p1", "paired"): 0.6,
        ("unet", "ee", "p0", "paired"): 0.5,
    }
    assert np.isclose(sum(values[key] * coefficient for key, coefficient in terms.items()), 0.2)


def test_full_summary_preserves_seed_means_and_paired_policy_effect():
    m = module()
    rows = []
    for event in ("a", "b"):
        for model, hits in [("native", (4, 7)), ("unet", (5, 6)), ("physical", (3, 5))]:
            for seed in (0,) if model == "physical" else (42, 1729, 31415):
                for reference, true_positive in zip(("p0", "p1"), hits, strict=True):
                    counts = {f"c{i}{j}": 0 for i in range(3) for j in range(3)}
                    counts.update(c00=10, c22=true_positive, c20=10 - true_positive)
                    rows.append(
                        {
                            "key": event,
                            "event": event,
                            "model": model,
                            "seed": seed,
                            "dataset": "ee",
                            "reference": reference,
                            "support": "paired",
                            "variant": "composed",
                            "known_pixels": 20,
                            **counts,
                        }
                    )
    coverage = pd.DataFrame(
        {
            "key": ["a", "b"],
            "post_label_offset_days": [0.0, 0.0],
            "source_bbox_intersection": [False, False],
        }
    )
    events, results, _, _ = m.summarize_table(
        pd.DataFrame(rows), coverage, {"episode_blocks": {"one": ["a"], "two": ["b"]}}
    )
    selected = results.loc[
        (results.stratum == "all") & (results.contrast == "interaction__native_minus_unet")
    ].iloc[0]
    assert np.isclose(selected.estimate, 0.2)
    assert selected.blocks == 2
    native = events.loc[(events.stratum == "all") & (events.model == "native")]
    assert set(native.seed) == {42, 1729, 31415}
