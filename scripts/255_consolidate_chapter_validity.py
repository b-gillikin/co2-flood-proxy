#!/usr/bin/env python3
"""Consolidate geometry-restricted and target-semantic checks from saved counts.

Post-result validity analysis, not an independent replication or new model run.
Preserves original counting ownership and full-cohort outputs.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from limburg_chapter_evaluation import atomic_json, sha256

BASE = ROOT / "results/limburg_chapter_sized_v1"
OUT = BASE / "validity"
COUNTS = [f"c{i}{j}" for i in range(3) for j in range(3)]


def summary_module():
    spec = importlib.util.spec_from_file_location(
        "chapter_summary", ROOT / "scripts/244_summarize_chapter_scores.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def water_counts(scores):
    """Collapse both target and prediction consistently; unknown already excluded."""
    result = scores.copy()
    for field in COUNTS:
        result[field] = 0
    result["c00"] = scores.c00
    result["c02"] = scores.c01 + scores.c02
    result["c20"] = scores.c10 + scores.c20
    result["c22"] = scores.c11 + scores.c12 + scores.c21 + scores.c22
    if not np.array_equal(result[COUNTS].sum(axis=1), scores[COUNTS].sum(axis=1)):
        raise ValueError("Water collapse lost support")
    return result


def main():
    audit = json.loads((OUT / "audit.json").read_text())
    if audit["missing_product_metadata"]:
        raise ValueError("Resolve missing external product metadata first")
    geometry_path = OUT / "external_geometry.parquet"
    geometry = pd.read_parquet(geometry_path)
    score_path = BASE / "evaluation/summary/tile_scores.parquet"
    scores = pd.read_parquet(score_path)
    coverage = pd.read_parquet(BASE / "evaluation/support/tile_coverage.parquet")
    config_path = ROOT / "config/limburg_chapter_evaluation_v1.json"
    config = json.loads(config_path.read_text())
    module = summary_module()
    matching = set(geometry.loc[geometry.p0_post_status == "compatible", "key"])
    paired_matching = set(
        geometry.loc[
            geometry.paired
            & (geometry.p0_post_status == "compatible")
            & (geometry.p1_post_status == "compatible"),
            "key",
        ]
    )
    performances, contrasts, events, omissions = [], [], [], []
    for scope, keys in (
        ("full_recorded_cohort", set(geometry.key)),
        ("compatible_geometry", matching),
        (
            "compatible_geometry_listed_timing_24h",
            matching & set(coverage.loc[coverage.post_label_offset_days.abs() <= 1, "key"]),
        ),
    ):
        selected = scores.loc[scores.key.isin(keys)].copy()
        # Every paired member must independently pass both reference comparisons.
        selected = selected.loc[
            (selected.dataset != "ee")
            | selected.key.isin(paired_matching)
            | (scope == "full_recorded_cohort")
        ]
        for endpoint, current in (
            ("fixed_event_flood", selected),
            ("water_union", water_counts(selected)),
        ):
            e, estimates, _, leave = module.summarize_table(current, coverage, config)
            p = module.performance_table(e, config)
            for table, destination in (
                (p, performances),
                (estimates, contrasts),
                (e, events),
                (leave, omissions),
            ):
                table = table.loc[table.stratum == "all"].copy()
                table["validity_scope"] = scope
                table["endpoint"] = endpoint
                destination.append(table)
    outputs = {}
    for name, parts in (
        ("performance", performances),
        ("contrasts", contrasts),
        ("event_scores", events),
        ("leave_one_block_out", omissions),
    ):
        path = OUT / f"{name}.parquet"
        pd.concat(parts, ignore_index=True).to_parquet(path, index=False)
        outputs[path.name] = sha256(path)
    label = pd.read_parquet(OUT / "target_construction.parquet")
    transition_fields = [f"y{i}_z{j}" for i in range(4) for j in range(4)]
    label.groupby(["event", "support"], as_index=False)[transition_fields].sum().to_parquet(
        OUT / "event_target_construction.parquet", index=False
    )
    physical_pre = ROOT / "data/raw/limburg_chapter_geoid_code_v1/scripts/eval_flood_paired.py"
    paths = [
        geometry_path,
        score_path,
        config_path,
        OUT / "audit.json",
        Path(__file__),
        ROOT / "scripts/244_summarize_chapter_scores.py",
        physical_pre,
    ]
    atomic_json(
        OUT / "complete.json",
        {
            "status": "validity_restricted_consolidation_complete",
            "paired_geometry_compatible_tiles": len(paired_matching),
            "paired_geometry_mismatch_tiles": int(geometry.paired.sum()) - len(paired_matching),
            "support": "original prediction-blind native ownership retained; restriction does not reclaim excluded owners' overlap",
            "timing_24h": "descriptive stricter subset, not a universal truth-validity cutoff",
            "interpretation": "fixed-event target map agreement; water union diagnostic is not a validated incremental-inundation target",
            "post_result": True,
            "sources": {str(path.relative_to(ROOT)): sha256(path) for path in paths},
            "outputs": outputs,
        },
    )
    final = pd.concat(contrasts, ignore_index=True)
    print(
        final.loc[
            (final.variant == "composed")
            & (final.endpoint == "fixed_event_flood")
            & final.contrast.isin(["native_minus_unet__ee_p0", "reference_P1_minus_P0__native"]),
            ["validity_scope", "contrast", "estimate", "interval_low", "interval_high", "blocks"],
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
