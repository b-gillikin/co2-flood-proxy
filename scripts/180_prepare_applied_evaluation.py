"""Audit every Sen1 hand chip and prepare explicit grouped evaluation rows.

Reads real rasters without resampling. Published reproduction and leave-event-
out transfer are separate designs; label budgets never thin the test census.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from shapely.geometry import Point, shape

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/raw/limburg_applied_tasks/sen1floods11"
EVIDENCE = ROOT / "docs/reviews/applied-task-config-2026-10-31"
OUT = ROOT / "results/applied_study_v1/evaluation"


def main():
    state = json.loads(
        (ROOT / "results/applied_study_v1/acquisition/sen1-progress.json").read_text()
    )
    if state["status"] != "completed" or state["verified_files"] != 1784:
        raise ValueError("Full verified acquisition is required for this inventory")
    OUT.mkdir(parents=True, exist_ok=True)
    metadata = json.loads((EVIDENCE / "Sen1Floods11_Metadata.geojson").read_text())["features"]
    by_location = {}
    for f in metadata:
        p = f["properties"]
        if p["location"] in by_location:
            raise ValueError("Ambiguous event/location metadata")
        by_location[p["location"]] = p
    split_map = {}
    for split in ["train", "valid", "test", "bolivia"]:
        with (EVIDENCE / f"flood_{split}_data.csv").open(newline="") as stream:
            for _, label in csv.reader(stream):
                if label in split_map:
                    raise ValueError("Published split overlaps")
                split_map[label] = split
    rows = []
    for path in sorted((DATA / "LabelHand").glob("*.tif")):
        chip = path.name.removesuffix("_LabelHand.tif")
        location = chip.rsplit("_", 1)[0]
        with rasterio.open(path) as ds:
            label = ds.read(1)
            classes = set(np.unique(label).tolist())
            if not classes <= {-1, 0, 1}:
                raise ValueError("Unrecognized label values")
            reference_shape, reference_crs = ds.shape, ds.crs
            reference_transform = np.array(tuple(ds.transform))
            bounds = list(ds.bounds)
        meta = by_location.get(location)
        metadata_match = "source_location_name"
        if meta is None:
            center = Point((bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2)
            matches = [f["properties"] for f in metadata if shape(f["geometry"]).covers(center)]
            if len(matches) != 1:
                raise ValueError("Ambiguous/unresolved event metadata for " + chip)
            meta = matches[0]
            metadata_match = "unique_source_event_geometry_contains_chip_center"
        arrays = {}
        for modality, bands in [("S1Hand", 2), ("S2Hand", 13)]:
            file = DATA / modality / f"{chip}_{modality}.tif"
            with rasterio.open(file) as ds:
                if ds.count != bands or ds.shape != reference_shape or ds.crs != reference_crs:
                    raise ValueError("Band/grid/CRS mismatch: " + str(file))
                if not np.allclose(
                    np.array(tuple(ds.transform)), reference_transform, rtol=0, atol=1e-9
                ):
                    raise ValueError("Affine mismatch: " + str(file))
                arrays[modality] = ds.read()
        s1 = np.isfinite(arrays["S1Hand"]).all(0)
        s2 = np.isfinite(arrays["S2Hand"]).all(0) & (arrays["S2Hand"] != 0).any(0)
        valid = label >= 0
        rows.append(
            dict(
                chip=chip,
                location=location,
                event=f"{location}_{meta['s1_date'].replace('/', '')}",
                published_split=split_map[path.name],
                s1_date=meta["s1_date"],
                s2_date=meta["s2_date"],
                metadata_location=meta["location"],
                metadata_match=metadata_match,
                label_valid_pixels=int(valid.sum()),
                water_pixels=int((label == 1).sum()),
                unknown_pixels=int((label == -1).sum()),
                radar_valid_labeled=int((valid & s1).sum()),
                optical_valid_labeled=int((valid & s2).sum()),
                paired_valid_labeled=int((valid & s1 & s2).sum()),
                optical_valid_water=int(((label == 1) & s2).sum()),
                left=bounds[0],
                bottom=bounds[1],
                right=bounds[2],
                top=bounds[3],
            )
        )
    frame = pd.DataFrame(rows)
    if len(frame) != 446 or len(split_map) != 446:
        raise ValueError("Incomplete published census")
    frame.to_parquet(OUT / "sen1-chip-inventory.parquet", index=False)
    groups = sorted(frame.event.unique())
    # Full leave-event-out evaluation: every event is tested once. Validation
    # is a different whole event; no tile from the held event enters training.
    folds = []
    for i, held in enumerate(groups):
        validation = groups[(i + 1) % len(groups)]
        for row in rows:
            role = (
                "test"
                if row["event"] == held
                else "valid"
                if row["event"] == validation
                else "train"
            )
            folds.append(dict(fold=held, chip=row["chip"], event=row["event"], role=role))
    pd.DataFrame(folds).to_parquet(OUT / "sen1-grouped-folds.parquet", index=False)
    # Budgets select complete labeled chips in a deterministic, nested ordering
    # within each training event. Report area/group counts; never call this the
    # same thing as reducing the number of independent training flood events.
    subsets = []
    for fold in groups:
        train = [r for r in folds if r["fold"] == fold and r["role"] == "train"]
        for seed in [42, 1729, 31415]:
            for event in sorted({r["event"] for r in train}):
                event_rows = sorted(
                    [r for r in train if r["event"] == event],
                    key=lambda r: hashlib.sha256(f"{seed}:{r['chip']}".encode()).digest(),
                )
                for budget in [1.0, 0.2, 0.05]:
                    for row in event_rows[: max(1, int(np.ceil(budget * len(event_rows))))]:
                        subsets.append(
                            dict(fold=fold, seed=seed, budget=budget, chip=row["chip"], event=event)
                        )
    pd.DataFrame(subsets).to_parquet(OUT / "sen1-label-subsets.parquet", index=False)
    summary = dict(
        status="complete_raster_and_partition_inventory",
        chips=len(frame),
        events=len(groups),
        published_splits=frame.published_split.value_counts().to_dict(),
        event_counts=frame.groupby("event").size().to_dict(),
        labeled_pixels=int(frame.label_valid_pixels.sum()),
        paired_valid_labeled_pixels=int(frame.paired_valid_labeled.sum()),
        unknown_label_pixels=int(frame.unknown_pixels.sum()),
        same_event_train_test_in_published_split=sorted(
            set(frame.loc[frame.published_split == "train", "event"])
            & set(frame.loc[frame.published_split == "test", "event"])
        ),
        budget_meaning="nested labeled chips within training events; all test chips retained",
        coverage_meaning="finite S1; finite S2 and not all-zero; not a cloud-quality certification",
        local_transfer="not established by this global benchmark inventory",
    )
    (OUT / "sen1-audit.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
