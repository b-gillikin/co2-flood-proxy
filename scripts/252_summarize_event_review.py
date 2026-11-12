#!/usr/bin/env python3
"""Separate water detection, flood attribution and observed reference contrast."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from limburg_chapter_evaluation import atomic_json, sha256

BASE = ROOT / "results/limburg_chapter_sized_v1"
OUT = BASE / "event_review"


def add_water_metrics(frame):
    result = frame.copy()
    water_tp = result.c11 + result.c12 + result.c21 + result.c22
    water_fn = result.c10 + result.c20
    water_fp = result.c01 + result.c02
    result["water_iou"] = water_tp / (water_tp + water_fn + water_fp).replace(0, np.nan)
    target_flood = result.c20 + result.c21 + result.c22
    result["flood_recall"] = result.c22 / target_flood.replace(0, np.nan)
    result["flood_as_permanent_fraction"] = result.c21 / target_flood.replace(0, np.nan)
    return result


def transition_metrics(frame):
    result = frame.copy()
    result["flood_target_pixels"] = sum(
        result[f"y2_p0{i}_p1{j}"] for i in range(3) for j in range(3)
    )
    result["old_flood_tp"] = sum(result[f"y2_p02_p1{j}"] for j in range(3))
    result["new_flood_tp"] = sum(result[f"y2_p0{i}_p12"] for i in range(3))
    result["gross_lost_flood_to_permanent"] = result.y2_p02_p11
    result["gross_lost_flood_to_background"] = result.y2_p02_p10
    result["gross_gained_flood"] = result.y2_p00_p12 + result.y2_p01_p12
    result["net_flood_tp_change"] = result.new_flood_tp - result.old_flood_tp
    expected = (
        result.gross_gained_flood
        - result.gross_lost_flood_to_permanent
        - result.gross_lost_flood_to_background
    )
    if not np.array_equal(result.net_flood_tp_change, expected):
        raise ValueError("Transition accounting does not recover the flood change")
    loss = result.gross_lost_flood_to_permanent + result.gross_lost_flood_to_background
    result["lost_flood_to_permanent_fraction"] = (
        result.gross_lost_flood_to_permanent / loss.replace(0, np.nan)
    )
    return result


def radar_means(frame):
    result = frame.copy()
    denominator = result.pixels.replace(0, np.nan)
    for column in frame.columns:
        if column.endswith("_db_sum") or column.endswith("_difference_sum"):
            result[column.removesuffix("_sum") + "_mean"] = result[column] / denominator
        elif column.endswith("_pixels") and column != "pixels":
            result[column.removesuffix("_pixels") + "_fraction"] = result[column] / denominator
    return result


def review_local():
    """The three changed local acquisition cases remain one historical flood."""
    local = BASE / "local"
    coverage = pd.read_parquet(local / "coverage.parquet")
    threshold = json.loads((BASE / "physical/calibration.json").read_text())["selected"][
        "threshold_db"
    ]
    records = []
    for row in coverage.loc[coverage.updated].itertuples():
        with np.load(local / "support" / f"{row.key}.npz") as data:
            mask = data["owner"] & (data["label"] == 2)
        triplet = ROOT / f"data/raw/limburg_chapter_local_triplets_v1/tiles/{row.aoi}/{row.key}.tif"
        with rasterio.open(triplet) as source:
            raw = source.read()
        db = 10 * np.log10(np.where(raw > 0, raw, np.nan))
        for model in ("physical", "native", "unet"):
            for seed in (0,) if model == "physical" else (42, 1729, 31415):
                predictions = []
                for reference in ("p0", "p1"):
                    with np.load(
                        local / f"predictions/{model}/{row.key}-{reference}-{seed}.npz"
                    ) as data:
                        predictions.append(data["prediction"])
                p0, p1 = predictions
                lost_perm = mask & (p0 == 2) & (p1 == 1)
                records.append(
                    {
                        "case": row.case,
                        "key": row.key,
                        "model": model,
                        "seed": seed,
                        "target_flood": int(mask.sum()),
                        "lost_to_permanent": int(lost_perm.sum()),
                        "lost_to_background": int((mask & (p0 == 2) & (p1 == 0)).sum()),
                        "gained_flood": int((mask & (p0 != 2) & (p1 == 2)).sum()),
                        "lost_perm_dark_p0": int((db[1, lost_perm] < threshold).sum()),
                        "lost_perm_dark_p1": int((db[3, lost_perm] < threshold).sum()),
                        "lost_perm_dark_post": int((db[5, lost_perm] < threshold).sum()),
                    }
                )
    frame = pd.DataFrame(records)
    frame.to_parquet(OUT / "local_tile_transitions.parquet", index=False)
    numeric = list(frame.select_dtypes(include=np.number).columns.difference(["seed"]))
    frame.groupby(["case", "model", "seed"], as_index=False)[numeric].sum().to_parquet(
        OUT / "local_case_transitions.parquet", index=False
    )


def main():
    if not (OUT / "complete.json").exists():
        raise ValueError("Explanation requires the complete paired census")
    events = pd.read_parquet(BASE / "evaluation/summary/event_scores.parquet")
    events = events.loc[
        (events.stratum == "all")
        & (events.variant == "composed")
        & (events.dataset == "ee")
        & (events.support == "paired")
    ]
    water = add_water_metrics(events)
    water.to_parquet(OUT / "water_and_flood_event_seed.parquet", index=False)
    values = ["flood_iou", "water_iou", "flood_recall", "flood_as_permanent_fraction"]
    event_means = water.groupby(["event", "model", "reference"], as_index=False)[values].mean()
    event_means.to_parquet(OUT / "water_and_flood_event_means.parquet", index=False)
    config = json.loads((ROOT / "config/limburg_chapter_evaluation_v1.json").read_text())
    lookup = {
        event: block for block, members in config["episode_blocks"].items() for event in members
    }
    spec = importlib.util.spec_from_file_location(
        "paired_summary", ROOT / "scripts/244_summarize_chapter_scores.py"
    )
    summary = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(summary)
    contrasts = []
    for model, rows in event_means.groupby("model"):
        for metric in values:
            wide = rows.pivot(index="event", columns="reference", values=metric)
            estimate, _ = summary.block_estimate(wide.p1 - wide.p0, lookup)
            contrasts.append({"model": model, "metric": metric, "contrast": "P1-P0", **estimate})
    pd.DataFrame(contrasts).to_parquet(OUT / "water_and_flood_contrasts.parquet", index=False)
    transitions = transition_metrics(pd.read_parquet(OUT / "event_prediction_transitions.parquet"))
    # The direct P0->P1 transitions must reconstruct the original score counts.
    check = water.pivot(index=["event", "model", "seed"], columns="reference", values="c22")
    for row in transitions.itertuples():
        if (
            row.old_flood_tp != check.loc[(row.event, row.model, row.seed), "p0"]
            or row.new_flood_tp != check.loc[(row.event, row.model, row.seed), "p1"]
        ):
            raise ValueError("Transition review and original scoring disagree")
    transitions.to_parquet(OUT / "transition_explanation.parquet", index=False)
    radar_means(pd.read_parquet(OUT / "event_radar_by_target.parquet")).to_parquet(
        OUT / "radar_target_means.parquet", index=False
    )
    radar_means(pd.read_parquet(OUT / "event_radar_by_transition.parquet")).to_parquet(
        OUT / "radar_transition_means.parquet", index=False
    )
    timing = pd.read_parquet(OUT / "timing.parquet")
    timing.groupby("event")[
        ["p0_age_days", "p1_age_days", "p1_before_catalogue_event_days", "post_label_offset_days"]
    ].agg(["min", "median", "max"]).to_parquet(OUT / "event_timing_ranges.parquet")
    review_local()
    atomic_json(
        OUT / "explanation-complete.json",
        {
            "status": "event_review_diagnostics_complete",
            "all_paired_tiles": 913,
            "score_transition_conservation_verified": True,
            "classification": "observed reclassification and radar contrast; physical water/onset explanations remain qualified",
            "runner_sha256": sha256(Path(__file__)),
            "outputs": {p.name: sha256(p) for p in OUT.glob("*.parquet")},
        },
    )
    print(pd.DataFrame(contrasts).to_string(index=False))


if __name__ == "__main__":
    main()
