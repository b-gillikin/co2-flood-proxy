#!/usr/bin/env python3
"""Plot the already scored flood/water distinction without refitting models."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "results/limburg_chapter_sized_v1"
OUT = BASE / "event_review"
NAMES = {
    "EMSR857": "Mozambique",
    "EMSR858": "Italy, January",
    "EMSR861": "Spain / Portugal",
    "EMSR864": "Portugal",
    "EMSR865": "Colombia",
    "EMSR866": "France",
    "EMSR868": "Greece",
    "EMSR870": "Ecuador",
    "EMSR871": "Italy, March",
}


def main():
    frame = pd.read_parquet(OUT / "water_and_flood_event_means.parquet")
    events = sorted(frame.event.unique())
    positions = np.arange(len(events))
    figure, axes = plt.subplots(1, 3, figsize=(13, 5), sharex=True, sharey=True)
    for axis, model, title in zip(
        axes,
        ["native", "unet", "physical"],
        ["Copernicus-FM", "U-Net", "Physical rule"],
        strict=True,
    ):
        values = frame.loc[frame.model == model].pivot(
            index="event", columns="reference", values=["flood_iou", "water_iou"]
        )
        for metric, offset, color, label in [
            ("flood_iou", -0.17, "#d66a28", "Flood class"),
            ("water_iou", 0.17, "#327ca3", "Water versus land"),
        ]:
            delta = (values[(metric, "p1")] - values[(metric, "p0")]).reindex(events)
            axis.barh(positions + offset, delta, height=0.30, color=color, label=label)
        axis.axvline(0, color="black", linewidth=0.7)
        axis.set_title(title)
        axis.set_xlabel("Change in map agreement (P1 − P0 IoU)")
        axis.grid(axis="x", alpha=0.2)
        axis.set_axisbelow(True)
    axes[0].set_yticks(positions, [NAMES[event] for event in events])
    axes[0].invert_yaxis()
    axes[0].legend(loc="lower left", fontsize=8)
    figure.suptitle(
        "Newer references can preserve water detection while changing flood attribution",
        fontsize=12,
    )
    figure.tight_layout(rect=[0, 0, 1, 0.94])
    figure.savefig(OUT / "water-versus-flood.png", dpi=180)
    plt.close(figure)
    native = frame.loc[frame.model == "native"]
    figure, axis = plt.subplots(figsize=(10, 7))
    for index, event in enumerate(events):
        for reference, offset in [("p0", -0.16), ("p1", 0.16)]:
            row = native.loc[(native.event == event) & (native.reference == reference)].iloc[0]
            values = [
                row.flood_recall,
                row.flood_as_permanent_fraction,
                1 - row.flood_recall - row.flood_as_permanent_fraction,
            ]
            left = 0.0
            for value, color in zip(values, ["#d66a28", "#327ca3", "#cccccc"], strict=True):
                axis.barh(index + offset, value * 100, left=left, height=0.29, color=color)
                left += value * 100
            axis.text(101, index + offset, reference.upper(), va="center", fontsize=8)
    axis.set_yticks(positions, [NAMES[event] for event in events])
    axis.invert_yaxis()
    axis.set_xlim(0, 108)
    axis.set_xlabel("Percentage of reference flood pixels")
    axis.set_title(
        "Copernicus-FM classifications of the same reference flood pixels\nOrange=flood; blue=permanent water; gray=background. Three-seed means."
    )
    figure.tight_layout()
    figure.savefig(OUT / "flood-reclassification.png", dpi=180)
    plt.close(figure)
    print(json.dumps({"figures": ["water-versus-flood.png", "flood-reclassification.png"]}))


if __name__ == "__main__":
    main()
