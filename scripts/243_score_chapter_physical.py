#!/usr/bin/env python3
"""Score the frozen physical rule on the identical prepared evaluation support."""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from limburg_chapter_evaluation import OUT, atomic_json, score_prediction, sha256


def main():
    base = ROOT / "results/limburg_chapter_sized_v1/physical_external"
    rows = []
    paths = sorted((base / "maps").rglob("*.npz"))
    if len(paths) != 3127:
        raise ValueError("Physical output census differs")
    for count, path in enumerate(paths, 1):
        dataset, event, filename = path.relative_to(base / "maps").parts
        key, reference = Path(filename).stem.rsplit("-", 1)
        receipt = json.loads(
            (base / "receipts" / dataset / event / f"{key}-{reference}.json").read_text()
        )
        if sha256(path) != receipt["output_sha256"]:
            raise ValueError("Physical output checksum differs")
        with np.load(path) as data:
            rows.extend(
                score_prediction(
                    key, dataset, reference, "physical", 0, data["prediction"], data["radar_valid"]
                )
            )
        if count % 250 == 0:
            print(json.dumps({"physical_scored": count, "total": len(paths)}), flush=True)
    target = OUT / "physical_scores.parquet"
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".partial.parquet")
    pd.DataFrame(rows).to_parquet(temporary, index=False)
    temporary.replace(target)
    atomic_json(
        OUT / "physical-complete.json",
        {
            "status": "physical_scoring_complete",
            "predictions": len(paths),
            "rows": len(rows),
            "score_sha256": sha256(target),
            "support_manifest_sha256": sha256(OUT / "support/manifest.json"),
        },
    )
    print(json.dumps({"physical_complete": len(paths), "rows": len(rows)}), flush=True)


if __name__ == "__main__":
    main()
