#!/usr/bin/env python3
"""Inspect tiles that contribute to event-level changes, not only tile extremes."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "results/limburg_chapter_sized_v1"


def select_cases(scores, effects):
    selected = scores.loc[
        (scores.model == "native")
        & (scores.dataset == "ee")
        & (scores.support == "paired")
        & (scores.variant == "composed")
    ]
    pivot = selected.pivot(
        index=["key", "event", "seed"],
        columns="reference",
        values=["c22", "c02", "c12", "target_flood_pixels"],
    )
    cases = []
    for event, group in selected.groupby("event"):
        marginal = []
        for seed, rows in group.groupby("seed"):
            baseline = rows.loc[
                rows.reference == "p0", ["c22", "c02", "c12", "target_flood_pixels"]
            ].sum()
            tiles = pivot.xs((event, seed), level=("event", "seed"))
            delta_tp = tiles[("c22", "p1")] - tiles[("c22", "p0")]
            delta_fp = (
                tiles[("c02", "p1")]
                + tiles[("c12", "p1")]
                - tiles[("c02", "p0")]
                - tiles[("c12", "p0")]
            )
            union = baseline.target_flood_pixels + baseline.c02 + baseline.c12
            change = (baseline.c22 + delta_tp) / (union + delta_fp) - baseline.c22 / union
            marginal.append(change.rename("change").reset_index())
        values = pd.concat(marginal).groupby("key").change.mean()
        delta = effects.loc[
            (effects.event == event)
            & (effects.contrast == "reference_P1_minus_P0__native")
            & (effects.stratum == "all")
            & (effects.variant == "composed"),
            "difference",
        ].iloc[0]
        extreme = values.min() if delta < 0 else values.max()
        key = sorted(values.index[values == extreme])[0]
        cases.append(
            {
                "event": event,
                "key": key,
                "event_marginal_change": float(values.loc[key]),
                "event_change": float(delta),
                "selection": "largest same-direction effect on whole-event IoU when only this tile is replaced by P1; averaged across three seeds; diagnostic selection after results",
            }
        )
    return cases


def main():
    summary = BASE / "evaluation/summary"
    cases = select_cases(
        pd.read_parquet(summary / "tile_scores.parquet"),
        pd.read_parquet(summary / "event_contrasts.parquet"),
    )
    target = BASE / "event_review"
    target.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(cases).to_parquet(target / "event_driver_cases.parquet", index=False)
    spec = importlib.util.spec_from_file_location(
        "review_figures", ROOT / "scripts/246_review_chapter_maps.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.main(cases_override=cases, review_override=target / "maps")


if __name__ == "__main__":
    main()
