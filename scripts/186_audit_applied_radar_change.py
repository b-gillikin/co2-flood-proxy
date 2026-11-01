"""Audit every Flood-S1 task record, class mask and pre/post grid before fitting."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/raw/limburg_applied_tasks/flood_s1/extracted/flood_s1"
OUT = ROOT / "results/applied_study_v1/evaluation"


def one_file(folder, prefix):
    files = list(folder.glob(prefix + "*.tif"))
    if len(files) != 1:
        raise ValueError(f"Expected exactly one {prefix}, found {len(files)}")
    return files[0]


def main():
    rows = []
    errors = []
    seen = set()
    for split in ["train", "val", "test"]:
        records = json.loads((DATA / f"grid_dict_{split}.json").read_text())
        for ident, r in records.items():
            try:
                if ident in seen:
                    raise ValueError("Record occurs in more than one published split")
                seen.add(ident)
                folder = DATA / "data" / r["path"]
                arrays = {}
                grid = None
                for prefix in ["MK0_MLU", "MK0_MNA", "MS1_IVV", "MS1_IVH", "SL1_IVV", "SL1_IVH"]:
                    with rasterio.open(one_file(folder, prefix)) as ds:
                        current = (ds.shape, str(ds.crs), tuple(ds.transform))
                        if grid is not None and current != grid:
                            raise ValueError("Pre/post/reference grid mismatch")
                        grid = current
                        arrays[prefix] = ds.read(1)
                y, m = arrays["MK0_MLU"], arrays["MK0_MNA"]
                if not set(np.unique(y)) <= {0, 1, 2, 3}:
                    raise ValueError("Unknown target class")
                if not set(np.unique(m)) <= {0, 1}:
                    raise ValueError("Unknown MNA class")
                valid = (m == 1) & (y != 3)
                invalid_source = np.zeros(y.shape, dtype=bool)
                for prefix in ["MS1_IVV", "MS1_IVH", "SL1_IVV", "SL1_IVH"]:
                    # Source info.json declares 0 intensity nodata. Preserve
                    # that known missingness rather than clip/fill it as dry.
                    invalid_source |= ~np.isfinite(arrays[prefix]) | (arrays[prefix] == 0)
                valid &= ~invalid_source
                info = r["info"]
                rows.append(
                    dict(
                        record=ident,
                        published_split=split,
                        event=str(info["actid"]),
                        aoi=info["aoiid"],
                        source_path=r["path"],
                        post_date=info["sources"]["MS1"]["source_date"],
                        pre_date=info["sources"]["SL1"]["source_date"],
                        class0_pixels=int(((y == 0) & valid).sum()),
                        class1_pixels=int(((y == 1) & valid).sum()),
                        class2_pixels=int(((y == 2) & valid).sum()),
                        valid_pixels=int(valid.sum()),
                        unknown_pixels=int((~valid).sum()),
                        mna0_label_not_ignore=int(((m == 0) & (y != 3)).sum()),
                        source_invalid_label_valid=int(
                            (invalid_source & (y != 3) & (m == 1)).sum()
                        ),
                    )
                )
            except Exception as exc:
                errors.append(dict(record=ident, split=split, error=f"{type(exc).__name__}: {exc}"))
        print(json.dumps(dict(split=split, checked=len(rows), errors=len(errors))), flush=True)
    frame = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(OUT / "radar-change-inventory.parquet", index=False)
    groups = {
        s: set(frame.loc[frame.published_split == s, "event"]) for s in ["train", "val", "test"]
    }
    report = dict(
        status="complete" if not errors else "complete_with_errors",
        records=len(frame),
        errors=errors,
        splits=frame.published_split.value_counts().to_dict(),
        events=frame.groupby("event").size().to_dict(),
        published_event_overlap={
            a + "__" + b: sorted(groups[a] & groups[b])
            for a, b in [("train", "val"), ("train", "test"), ("val", "test")]
        },
        mna0_label_not_ignore=int(frame.mna0_label_not_ignore.sum()),
        source_invalid_label_valid=int(frame.source_invalid_label_valid.sum()),
        classes={
            "0": "no water",
            "1": "permanent water",
            "2": "flood",
            "3": "outside AOI / ignore",
        },
        classes_source="author cobench_floods1_wrapper.py plotting labels; raster nodata=3",
        source_nodata_policy="nonfinite or zero radar intensity excluded; source metadata declares nodata 0",
        normalization="Author asymmetric pre/post std retained as source issue, not silently corrected",
    )
    (OUT / "radar-change-audit.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
