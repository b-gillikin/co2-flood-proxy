#!/usr/bin/env python3
"""Explain the completed fixed-model reference contrast over all 913 triplets.

Exploratory review after scoring: no fitting, changed thresholds or image selection.
Dark backscatter is a radar proxy, not independent confirmation of standing water.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from limburg_chapter_evaluation import BITS, atomic_json, packet, sha256

BASE = ROOT / "results/limburg_chapter_sized_v1"
OUT = BASE / "event_review"
TRIPLETS = ROOT / "data/raw/limburg_chapter_ee_triplets_v1/tiles"
SEEDS = (42, 1729, 31415)


def acquired(product):
    return datetime.strptime(product.split("_")[4], "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc)


def radar_metrics(db, mask, threshold):
    count = int(mask.sum())
    result = {"pixels": count}
    if not count:
        return result
    for phase, offset in [("p0", 0), ("p1", 2), ("post", 4)]:
        for polarization, delta in [("vv", 0), ("vh", 1)]:
            result[f"{phase}_{polarization}_db_sum"] = float(
                db[offset + delta, mask].sum(dtype=np.float64)
            )
        result[f"{phase}_dark_pixels"] = int((db[offset + 1, mask] < threshold).sum())
    pre0, pre1, post = db[1, mask], db[3, mask], db[5, mask]
    result["p0_post_absolute_vh_difference_sum"] = float(np.abs(post - pre0).sum(dtype=np.float64))
    result["p1_post_absolute_vh_difference_sum"] = float(np.abs(post - pre1).sum(dtype=np.float64))
    result["p1_closer_to_post_pixels"] = int((np.abs(post - pre1) < np.abs(post - pre0)).sum())
    result["new_dark_p1_pixels"] = int(((pre0 >= threshold) & (pre1 < threshold)).sum())
    return result


def prediction(key, model, reference, seed):
    event = key.split("-")[0]
    if model == "physical":
        path = BASE / f"physical_external/maps/ee/{event}/{key}-{reference}.npz"
    else:
        path = (
            BASE / f"evaluation/compact/predictions/{model}/ee/{event}/{key}-{reference}-{seed}.npz"
        )
    with np.load(path) as data:
        return data["prediction"]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    if not (BASE / "evaluation/summary/complete.json").exists():
        raise ValueError("Event explanation follows the complete comparison")
    catalogue = pd.read_parquet(
        ROOT
        / "data/raw/limburg_applied_tasks/local_references/geoid-flood-heldout-tile-catalog.parquet"
    )
    catalogue["key"] = catalogue.event_id + "-" + catalogue.tile_id + "-" + catalogue.bbox_id
    catalogue = catalogue.set_index("key")
    coverage = pd.read_parquet(BASE / "evaluation/support/tile_coverage.parquet")
    chosen = coverage.loc[coverage.paired_available].sort_values("key")
    calibration = json.loads((BASE / "physical/calibration.json").read_text())["selected"]
    if calibration["polarization"] != "VH":
        raise ValueError("Diagnostic must use the actual frozen physical polarization")
    threshold = calibration["threshold_db"]
    timing, radar_rows, transitions, losses = [], [], [], []
    manifest = {
        "scope": "all 913 harmonized paired tiles, existing owned common support",
        "status": "post_result_explanatory_review_not_confirmatory_mechanism_identification",
        "source_fixed_dark_threshold_db": threshold,
        "radar_proxy_caution": "Low return can reflect open water, smooth land, shadow or other effects; this is not a water truth label.",
        "runner_sha256": sha256(Path(__file__)),
        "support_manifest_sha256": sha256(BASE / "evaluation/support/manifest.json"),
        "comparison_complete_sha256": sha256(BASE / "evaluation/summary/complete.json"),
    }
    atomic_json(OUT / "manifest.json", manifest)
    for done, row in enumerate(chosen.itertuples(), 1):
        key, event = row.key, row.event
        path = TRIPLETS / event / f"{key}.tif"
        receipt = json.loads(path.with_suffix(".receipt.json").read_text())
        if sha256(path) != receipt["sha256"]:
            raise ValueError(f"Changed event triplet: {key}")
        with rasterio.open(path) as ds:
            raw = ds.read()
        data = packet(key)
        owned = (data["owner"] & BITS["ee_common"]) != 0
        db = 10 * np.log10(np.where(raw > 0, raw, np.nan))
        target = data["label"]
        meta = catalogue.loc[key]
        times = {role: acquired(product) for role, product in receipt["products"].items()}
        event_time = pd.Timestamp(meta.event_time).tz_localize("UTC")
        label_time = pd.Timestamp(meta.delineation_time_post).tz_localize("UTC")
        label_pre = pd.Timestamp(meta.delineation_time_pre).tz_localize("UTC")
        timing.append(
            {
                "key": key,
                "event": event,
                "country": row.country,
                **{f"{role}_time": value.isoformat() for role, value in times.items()},
                "catalogue_event_time": event_time.isoformat(),
                "label_time": label_time.isoformat(),
                "label_pre_time": label_pre.isoformat(),
                "p0_age_days": (times["post"] - times["p0"]).total_seconds() / 86400,
                "p1_age_days": (times["post"] - times["p1"]).total_seconds() / 86400,
                "p1_before_catalogue_event_days": (event_time - times["p1"]).total_seconds()
                / 86400,
                "post_label_offset_days": (times["post"] - label_time).total_seconds() / 86400,
                "owned_pixels": int(owned.sum()),
            }
        )
        for category, name in [(0, "background"), (1, "permanent"), (2, "flood")]:
            radar_rows.append(
                {
                    "key": key,
                    "event": event,
                    "target": name,
                    **radar_metrics(db, owned & (target == category), threshold),
                }
            )
        for model in ("physical", "unet", "native"):
            for seed in (0,) if model == "physical" else SEEDS:
                p0 = prediction(key, model, "p0", seed)
                p1 = prediction(key, model, "p1", seed)
                if (
                    not np.isin(p0[owned], [0, 1, 2]).all()
                    or not np.isin(p1[owned], [0, 1, 2]).all()
                ):
                    raise ValueError("Unknown prediction on owned scored support")
                encoded = 9 * target[owned].astype(np.int16) + 3 * p0[owned] + p1[owned]
                counts = np.bincount(encoded, minlength=27).reshape(3, 3, 3)
                transitions.append(
                    {
                        "key": key,
                        "event": event,
                        "model": model,
                        "seed": seed,
                        **{
                            f"y{y}_p0{a}_p1{b}": int(counts[y, a, b])
                            for y in range(3)
                            for a in range(3)
                            for b in range(3)
                        },
                    }
                )
                flood = owned & (target == 2)
                for kind, mask in [
                    ("lost_to_permanent", flood & (p0 == 2) & (p1 == 1)),
                    ("lost_to_background", flood & (p0 == 2) & (p1 == 0)),
                    ("retained_flood", flood & (p0 == 2) & (p1 == 2)),
                    ("gained_flood", flood & (p0 != 2) & (p1 == 2)),
                ]:
                    losses.append(
                        {
                            "key": key,
                            "event": event,
                            "model": model,
                            "seed": seed,
                            "transition": kind,
                            **radar_metrics(db, mask, threshold),
                        }
                    )
        if done % 50 == 0 or done == len(chosen):
            print(json.dumps({"reviewed_tiles": done, "total": len(chosen)}), flush=True)
    for name, records in [
        ("timing", timing),
        ("radar_by_target", radar_rows),
        ("prediction_transitions", transitions),
        ("radar_by_transition", losses),
    ]:
        pd.DataFrame(records).to_parquet(OUT / f"{name}.parquet", index=False)
    for name, groups in [
        ("radar_by_target", ["event", "target"]),
        ("prediction_transitions", ["event", "model", "seed"]),
        ("radar_by_transition", ["event", "model", "seed", "transition"]),
    ]:
        frame = pd.read_parquet(OUT / f"{name}.parquet")
        numeric = list(frame.select_dtypes(include=np.number).columns.difference(["seed"]))
        result = frame.groupby(groups, as_index=False)[numeric].sum()
        result.to_parquet(OUT / f"event_{name}.parquet", index=False)
    atomic_json(
        OUT / "complete.json",
        {
            "status": "all_paired_tiles_reviewed",
            "tiles": len(chosen),
            "activations": int(chosen.event.nunique()),
            "outputs": {p.name: sha256(p) for p in OUT.glob("*.parquet")},
        },
    )


if __name__ == "__main__":
    main()
