#!/usr/bin/env python3
"""Build a systematic per-activation atlas from the full scored map census."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from limburg_chapter_evaluation import OUT, BITS, packet, atomic_json, sha256


def main():
    scores = pd.read_parquet(OUT / "summary/tile_scores.parquet")
    selected = scores.loc[(scores.dataset == "ee") & (scores.support == "paired") &
                          (scores.variant == "composed")]
    means = selected.groupby(["key", "event", "model", "reference"]).flood_iou.mean().reset_index()
    wide = means.pivot(index=["key", "event"], columns=["model", "reference"], values="flood_iou")
    wide["native_reference_change"] = wide[("native", "p1")] - wide[("native", "p0")]
    cases = []
    for event, rows in wide.groupby(level="event"):
        usable = rows["native_reference_change"].dropna()
        if usable.empty:
            continue
        maximum = usable.abs().max()
        key = sorted(usable.index[usable.abs() == maximum])[0][0]
        cases.append({"key": key, "event": event, "selection": "largest absolute native P1-P0 tile IoU change within activation; all-seed mean; key breaks ties",
                      "native_reference_change": float(usable.loc[(key, event)])})
    review = OUT / "map_review"
    review.mkdir(parents=True, exist_ok=True)
    spec = importlib.util.spec_from_file_location("chapter_tile_io", ROOT / "scripts/232_chapter_tile_infer.py")
    io = importlib.util.module_from_spec(spec); spec.loader.exec_module(io)
    cmap = ListedColormap(["#dddddd", "#287db8", "#e37732", "#ffffff"])
    norm = BoundaryNorm([-0.5, 0.5, 1.5, 2.5, 3.5], 4)
    coverage = pd.read_parquet(OUT / "support/tile_coverage.parquet").set_index("key")
    for case in cases:
        key, event = case["key"], case["event"]
        raw0, _, _, times0, _ = io.input_tile(key, "ee", "p0")
        raw1, _, _, times1, _ = io.input_tile(key, "ee", "p1")
        if not np.array_equal(raw0[2:], raw1[2:], equal_nan=True):
            raise ValueError("Reference substitution changed the event image")
        data = packet(key)
        support = (data["owner"] & BITS["ee_common"]) != 0
        images = [raw0[0], raw1[0], raw0[2], data["label"]]
        titles = [f"P0 VV: {times0[0].date()}", f"P1 VV: {times1[0].date()}",
                  f"Event VV: {times0[1].date()}", "Released target"]
        files = []
        for kind, reference in [("native", "p0"), ("native", "p1"), ("physical", "p0"), ("physical", "p1"), ("unet", "p1")]:
            if kind == "physical":
                path = ROOT / f"results/limburg_chapter_sized_v1/physical_external/maps/ee/{event}/{key}-{reference}.npz"
            else:
                path = OUT / f"compact/predictions/{kind}/ee/{event}/{key}-{reference}-42.npz"
            with np.load(path) as values:
                images.append(values["prediction"])
            titles.append(f"{kind} {reference.upper()}" + (" (seed 42)" if kind != "physical" else ""))
            files.append({"path": str(path.relative_to(ROOT)), "sha256": sha256(path)})
        fig, axes = plt.subplots(3, 3, figsize=(12, 12))
        for index, (axis, image, title) in enumerate(zip(axes.flat, images, titles, strict=True)):
            if index < 3:
                db = 10 * np.log10(np.where(image > 0, image, np.nan))
                axis.imshow(np.where(support, db, np.nan), cmap="gray", vmin=-30, vmax=0,
                            interpolation="nearest")
            else:
                display = np.where(support, image, 255)
                display = np.where(display == 255, 3, display)
                axis.imshow(display, cmap=cmap, norm=norm, interpolation="nearest")
            axis.set_title(title, fontsize=10)
            axis.set_axis_off()
        row = coverage.loc[key]
        fig.suptitle(f"{key}: native reference change {case['native_reference_change']:+.3f} IoU\n"
                     f"Listed radar–label offset {row.post_label_offset_days:+.2f} days; source-footprint overlap {bool(row.source_bbox_intersection)}\n"
                     "Gray=background; blue=permanent water; orange=flood; white=unscored. Illustrative seed 42, not an ensemble.", fontsize=10)
        fig.tight_layout(rect=[0, 0, 1, .92])
        path = review / f"{key}.png"
        fig.savefig(path, dpi=160)
        plt.close(fig)
        case.update({"image": path.name, "figure_sha256": sha256(path), "post_label_offset_days": float(row.post_label_offset_days),
                     "source_bbox_intersection": bool(row.source_bbox_intersection), "paired_owned_pixels": int(support.sum()),
                     "displayed_prediction_files": files})
        print(json.dumps({"reviewed_event": event, "key": key}), flush=True)
    atomic_json(review / "inventory.json", {"status": "systematic_case_atlas_complete", "cases": cases,
                "selection_scope": "one maximum absolute native reference-change tile per assessable activation; intentionally diagnostic, not representative accuracy",
                "score_table_sha256": sha256(OUT / "summary/tile_scores.parquet")})


if __name__ == "__main__":
    main()
