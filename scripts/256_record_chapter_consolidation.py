#!/usr/bin/env python3
"""Record compact validity findings and available execution costs, not prose."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from limburg_chapter_evaluation import atomic_json, sha256

BASE = ROOT / "results/limburg_chapter_sized_v1"
OUT = BASE / "validity"


def json_lines(path):
    rows = []
    for line in path.read_text().splitlines():
        if line.startswith("{"):
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def records(frame):
    return json.loads(frame.to_json(orient="records", double_precision=12))


def main():
    geometry = pd.read_parquet(OUT / "external_geometry.parquet")
    local = pd.read_parquet(OUT / "local_geometry.parquet")
    performance = pd.read_parquet(OUT / "performance.parquet")
    contrasts = pd.read_parquet(OUT / "contrasts.parquet")
    coverage = pd.read_parquet(BASE / "evaluation/support/tile_coverage.parquet")
    labels = pd.read_parquet(OUT / "event_target_construction.parquet")
    original = pd.read_parquet(BASE / "evaluation/summary/contrasts.parquet")
    actual = contrasts.loc[
        (contrasts.validity_scope == "full_recorded_cohort")
        & (contrasts.endpoint == "fixed_event_flood")
    ]
    merged = original.loc[original.stratum == "all"].merge(
        actual, on=["variant", "contrast"], suffixes=("_old", "_new"), validate="one_to_one"
    )
    if len(merged) != len(actual) or any(
        not merged[f"{field}_old"].equals(merged[f"{field}_new"])
        for field in ("estimate", "interval_low", "interval_high", "blocks")
    ):
        raise ValueError("Consolidation does not reproduce original all-cohort contrasts")
    costs, sources = [], {}
    for model in ("native", "unet"):
        for seed in (42, 1729, 31415):
            path = BASE / f"engineering/final-{model}-{seed}.log"
            manifest = BASE / f"final_source/{model}-{seed}/manifest.json"
            rows = [r for r in json_lines(path) if "elapsed_epoch_s" in r]
            epochs = {r["completed_epoch"]: r for r in rows}
            expected = json.loads(manifest.read_text())["epochs"]
            if set(epochs) != set(range(1, expected + 1)):
                raise ValueError("Source-fit log lacks complete epoch timing")
            costs.append(
                dict(
                    model=model,
                    seed=seed,
                    completed_epochs=expected,
                    successful_epoch_seconds=sum(r["elapsed_epoch_s"] for r in epochs.values()),
                    all_logged_epoch_seconds=sum(r["elapsed_epoch_s"] for r in rows),
                )
            )
            sources[str(path.relative_to(ROOT))] = sha256(path)
            sources[str(manifest.relative_to(ROOT))] = sha256(manifest)
    queue = BASE / "engineering/mapping-queue.log"
    execution = json_lines(queue)
    windows = []
    for model in ("native", "unet"):
        starts = [
            r["unix_time"]
            for r in execution
            if r.get("status") == "running" and r.get("model") == model
        ]
        ends = [
            r["unix_time"]
            for r in execution
            if r.get("status") == "completed" and r.get("model") == model
        ]
        if starts and ends:
            windows.append(
                dict(model=model, elapsed_execution_window_seconds=max(ends) - min(starts))
            )
    ledgers = [json.loads(p.read_text()) for p in (BASE / "external/archives").glob("*.json")]
    if not all(r["status"] == "remote_readback_verified" for r in ledgers):
        raise ValueError("Prediction archive not verified")
    sources[str(queue.relative_to(ROOT))] = sha256(queue)
    main = (
        (performance.variant == "composed")
        & (performance.dataset == "ee")
        & (performance.support == "paired")
    )
    keep = contrasts.variant.isin(["composed", "mask_composition"])
    meta = geometry.merge(
        coverage[["key", "ee_common_owned", "post_label_offset_days"]],
        on="key",
        validate="one_to_one",
    )
    counts = []
    for scope, mask in (
        ("full_paired", meta.paired),
        ("compatible_paired", meta.paired & (meta.p0_post_status == "compatible")),
        (
            "compatible_paired_listed_timing_24h",
            meta.paired
            & (meta.p0_post_status == "compatible")
            & (meta.post_label_offset_days.abs() <= 1),
        ),
    ):
        g = meta.loc[mask]
        counts.append(
            dict(
                scope=scope,
                tiles=len(g),
                activations=g.event.nunique(),
                owned_pixels=int(g.ee_common_owned.sum()),
            )
        )
    output = {
        "status": "consolidated_validity_readout",
        "original_all_cohort_contrasts_reproduced": len(merged),
        "support": counts,
        "local_geometry": records(
            local.groupby(["p0_post_status", "p1_post_status"], dropna=False)
            .size()
            .reset_index(name="records")
        ),
        "geometry_by_event": records(
            geometry.loc[geometry.paired]
            .groupby(["event", "p0_post_status"])
            .size()
            .reset_index(name="tiles")
        ),
        "performance": records(performance.loc[main]),
        "contrasts": records(contrasts.loc[keep]),
        "target_construction": records(labels),
        "costs": {
            "final_source_fits": costs,
            "external_execution_windows": windows,
            "verified_archive_count": len(ledgers),
            "verified_archive_bytes": sum(r["archive_bytes"] for r in ledgers),
            "limits": "Epoch times omit source development, shared cache preparation and startup. Mapping windows include IO/archive/retry/sleep overhead; not compute-only latency. No measured annotation-hours, complete retrieval cost or operational service latency is claimed.",
        },
        "provenance": {
            **sources,
            **{
                str((OUT / name).relative_to(ROOT)): sha256(OUT / name)
                for name in (
                    "audit.json",
                    "complete.json",
                    "performance.parquet",
                    "contrasts.parquet",
                )
            },
            str(Path(__file__).relative_to(ROOT)): sha256(Path(__file__)),
        },
    }
    atomic_json(ROOT / "docs/reviews/limburg-validity-consolidation-2026-11-11.json", output)
    print(json.dumps({"support": counts, "costs": output["costs"]}, indent=2))


if __name__ == "__main__":
    main()
