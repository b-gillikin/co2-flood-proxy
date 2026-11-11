#!/usr/bin/env python3
"""Run a fixed source-trained flood model on one native 1024px SAR tile."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import rasterio
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from applied_copernicus import CopernicusRadarChange, normalize_radar
from applied_unet import StandardUNet
from limburg_chapter_grid import patch_metadata, stitch_probabilities, windows

AUDIT = ROOT / "data/processed/limburg_chapter_geoid_audit_v1/tile_audit.parquet"
EE = ROOT / "data/raw/limburg_chapter_ee_triplets_v1/tiles"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def acquired(product: str) -> datetime:
    return datetime.strptime(product.split("_")[4], "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc)


def input_tile(key: str, source: str, reference: str):
    rows = pd.read_parquet(AUDIT)
    found = rows.loc[(rows.event_id + "-" + rows.tile_id + "-" + rows.bbox_id) == key]
    if len(found) != 1:
        raise ValueError(f"Expected one audited target tile for {key}")
    row = found.iloc[0]
    if source == "ee":
        path = EE / row.event_id / f"{key}.tif"
        receipt = json.loads(path.with_suffix(".receipt.json").read_text())
        if sha256(path) != receipt["sha256"]:
            raise ValueError("Changed harmonized SAR triplet")
        with rasterio.open(path) as ds:
            raw = ds.read()
            transform, crs = ds.transform, ds.crs
        if raw.shape != (6, 1024, 1024):
            raise ValueError("Harmonized triplet must have six native-grid bands")
        start = 0 if reference == "p0" else 2
        raw = raw[[start, start + 1, 4, 5]]
        products = receipt["products"]
        times = acquired(products[reference]), acquired(products["post"])
        provenance = {"source": "ee_harmonized", "input_sha256": receipt["sha256"],
                      "products": products, "ee_assets": receipt["ee_assets"]}
    else:
        if reference != "p0":
            raise ValueError("Delivered data have only P0; P1 requires harmonized triplet")
        with rasterio.open(row.pre_vsi) as pre, rasterio.open(row.post_vsi) as post:
            if (pre.shape, pre.transform, pre.crs) != (post.shape, post.transform, post.crs):
                raise ValueError("Delivered radar grids differ")
            raw = np.concatenate([pre.read(), post.read()])
            transform, crs = pre.transform, pre.crs
            pre_products = json.loads(pre.tags()["SOURCE_PRODUCTS"])
            post_products = json.loads(post.tags()["SOURCE_PRODUCTS"])
        times = max(map(acquired, pre_products)), max(map(acquired, post_products))
        provenance = {"source": "geoid_delivered", "pre_vsi": row.pre_vsi,
                      "post_vsi": row.post_vsi, "products": {"p0": pre_products, "post": post_products}}
    if not times[0] < times[1]:
        raise ValueError("Pre-event image must precede post-event image")
    return raw, transform, crs, times, provenance


def model_from_checkpoint(kind: str, checkpoint: Path, device: str):
    model = CopernicusRadarChange() if kind == "native" else StandardUNet(4, 3)
    state = torch.load(checkpoint, map_location="cpu", weights_only=True)
    if isinstance(state, dict) and "model" in state:
        state = state["model"]
    result = model.load_state_dict(state, strict=kind != "native")
    if kind == "native" and (result.unexpected_keys or any(not x.startswith("encoder.") for x in result.missing_keys)):
        raise ValueError("Native checkpoint omits non-encoder model weights")
    model.eval()
    model.to(device)
    if kind == "native":
        model.encoder.cpu()
    return model


def infer(raw, transform, crs, times, kind: str, model, device: str, batch: int):
    normalized, valid = normalize_radar(raw)
    pieces = []
    positions = windows(raw.shape[1], raw.shape[2])
    if kind == "native":
        batch = 1  # frozen CPU encoder and MPS head have different device paths
    with torch.inference_mode():
        for start in range(0, len(positions), batch):
            group = positions[start:start+batch]
            tiles = np.stack([normalized[:, top:top+224, left:left+224] for top, left in group])
            x = torch.from_numpy(tiles).to(device)
            if kind == "native":
                metadata = np.stack([patch_metadata(transform, crs, top, left, 224, *times) for top, left in group])
                logits = model(x, torch.from_numpy(metadata).to(device))[0]
            else:
                logits = model(x)
            probabilities = torch.softmax(logits, dim=1).cpu().numpy()
            for (top, left), prob in zip(group, probabilities, strict=True):
                prob[:, ~valid[top:top+224, left:left+224]] = np.nan
                pieces.append((top, left, prob))
    probabilities, covered = stitch_probabilities(pieces, raw.shape[1], raw.shape[2])
    if not np.array_equal(covered, valid):
        raise ValueError("Window stitching changed valid radar support")
    return probabilities, valid


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--key", required=True)
    parser.add_argument("--source", choices=["ee", "delivered"], required=True)
    parser.add_argument("--reference", choices=["p0", "p1"], required=True)
    parser.add_argument("--model", choices=["native", "unet"], required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--device", choices=["cpu", "mps"], default="mps")
    parser.add_argument("--batch", type=int, default=4)
    parser.add_argument("--output", type=Path, default=ROOT / "results/limburg_chapter_sized_v1/engineering")
    args = parser.parse_args()
    if args.batch < 1:
        parser.error("Batch must be positive")
    torch.set_num_threads(2)
    raw, transform, crs, times, source = input_tile(args.key, args.source, args.reference)
    model = model_from_checkpoint(args.model, args.checkpoint, args.device)
    probabilities, valid = infer(raw, transform, crs, times, args.model, model, args.device, args.batch)
    args.output.mkdir(parents=True, exist_ok=True)
    name = f"{args.key}-{args.source}-{args.reference}-{args.model}"
    target = args.output / f"{name}.npz"
    partial = args.output / f"{name}.partial.npz"
    np.savez_compressed(partial, probability=probabilities.astype(np.float32), radar_valid=valid)
    partial.replace(target)
    record = {"key": args.key, "reference": args.reference, "model": args.model,
              "checkpoint": str(args.checkpoint), "checkpoint_sha256": sha256(args.checkpoint),
              "input": source, "pre_time": times[0].isoformat(), "post_time": times[1].isoformat(),
              "crs": str(crs), "transform": list(transform)[:6], "valid_pixels": int(valid.sum()),
              "output_sha256": sha256(target), "windows": len(windows(*valid.shape)),
              "data_only_engineering_smoke": "engineering" in str(args.output)}
    (args.output / f"{name}.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps({"output": str(target), "valid_pixels": record["valid_pixels"],
                      "windows": record["windows"]}))


if __name__ == "__main__":
    main()
