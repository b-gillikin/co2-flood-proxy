"""Extract native frozen radar spatial tokens once, retaining all 446 chips.

CPU-only, one thread. Float32 spatial features (not catchment averages), one
bounded file per source chip, reused across folds/label budgets/head epochs.
"""

from __future__ import annotations

import hashlib
import json
import resource
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import numpy as np
import pandas as pd
import rasterio
import torch

from applied_spatial_models import GalileoRadar
from applied_water import galileo_radar_norm

OUT = ROOT / "data/processed/limburg_applied_galileo_spatial_v1"
DATA = ROOT / "data/raw/limburg_applied_tasks/sen1floods11"
PROGRESS = ROOT / "results/applied_study_v1/galileo_spatial_cache"


def main():
    PROGRESS.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    import fcntl

    lock = (PROGRESS / ".lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    sources = [
        "src/applied_spatial_models.py",
        "src/applied_water.py",
        "scripts/190_extract_applied_galileo.py",
        "data/raw/limburg_dynamic_model_weights/models/galileo/models/nano/encoder.pt",
        "results/applied_study_v1/evaluation/sen1-chip-inventory.parquet",
    ]
    hashes = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in sources}
    manifest = dict(
        status="running",
        source_hashes=hashes,
        device="cpu",
        threads=1,
        dtype="float32",
        shape_per_chip=[64, 8, 8, 128],
        population="all 446 source chips, including dry and unknown subpatches; labels never enter encoder",
        normalization="OURS_S1 norm_no_clip std_multiplier2; real acquisition month",
        completed=0,
        total=446,
        bytes=0,
    )
    index_file = OUT / "index.json"
    if index_file.exists() and json.loads(index_file.read_text())["source_hashes"] != hashes:
        raise ValueError("Existing cache has different sources; retain it and choose a new version")
    frame = pd.read_parquet(ROOT / sources[-1])
    torch.set_num_threads(1)
    model = GalileoRadar().eval()
    started = time.perf_counter()
    rows = []
    for row in frame.itertuples():
        while shutil.disk_usage(ROOT).free < 53 * 1024**3:
            time.sleep(10)
        source = DATA / "S1Hand" / f"{row.chip}_S1Hand.tif"
        source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
        path = OUT / f"{row.chip}.npy"
        receipt = path.with_suffix(".receipt.json")
        if path.exists():
            record = json.loads(receipt.read_text())
            if (
                record["source_sha256"] != source_sha
                or record["sha256"] != hashlib.sha256(path.read_bytes()).hexdigest()
            ):
                raise ValueError("Cache/source checksum mismatch")
        else:
            with rasterio.open(source) as ds:
                s1 = ds.read()
            valid = np.isfinite(s1).all(0)
            x = galileo_radar_norm(s1)
            # Unknown source cells are mean-imputed, but their labels remain
            # excluded in the task loader. Never convert them to dry targets.
            x = np.where(np.isfinite(x), x, 0.5).astype(np.float32)
            patches = np.stack(
                [x[:, y : y + 64, z : z + 64] for y in range(0, 512, 64) for z in range(0, 512, 64)]
            )
            month = datetime.strptime(row.s1_date.replace("/", "-"), "%Y-%m-%d").month - 1
            features = []
            t = time.perf_counter()
            with torch.no_grad():
                for i in range(0, 64, 16):
                    tokens = model.features(
                        torch.from_numpy(patches[i : i + 16]),
                        torch.full((len(patches[i : i + 16]),), month),
                    )
                    features.append(tokens.cpu().numpy())
            feature = np.concatenate(features)
            if feature.shape != (64, 8, 8, 128) or not np.isfinite(feature).all():
                raise ValueError("Invalid spatial feature output")
            temp = path.with_suffix(".partial")
            with temp.open("wb") as stream:
                np.save(stream, feature, allow_pickle=False)
            temp.replace(path)
            record = dict(
                chip=row.chip,
                source_sha256=source_sha,
                month=month,
                valid_source_pixels=int(valid.sum()),
                sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                bytes=path.stat().st_size,
                feature_seconds=time.perf_counter() - t,
            )
            receipt.write_text(json.dumps(record, indent=2) + "\n")
        rows.append(record)
        manifest["completed"] += 1
        manifest["bytes"] += record["bytes"]
        manifest["elapsed_s"] = time.perf_counter() - started
        index_file.write_text(json.dumps(manifest, indent=2) + "\n")
        (PROGRESS / "progress.json").write_text(json.dumps(manifest, indent=2) + "\n")
    manifest.update(
        status="completed",
        feature_seconds=sum(r["feature_seconds"] for r in rows),
        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        files=rows,
    )
    index_file.write_text(json.dumps(manifest, indent=2) + "\n")
    (PROGRESS / "progress.json").write_text(
        json.dumps({k: v for k, v in manifest.items() if k != "files"}, indent=2) + "\n"
    )


if __name__ == "__main__":
    main()
