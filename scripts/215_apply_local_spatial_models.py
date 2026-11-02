"""Apply a completed full-label spatial fit to every compatible held local case.

Pairing/QA are fixed independently of maps and scores. Each fold/seed remains
identified. This is source-qualified July2021 map agreement, not field truth.
"""

import argparse
import fcntl
import hashlib
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault(
    "PROJ_DATA", str((ROOT / ".venv-foundation/bin/python").resolve().parents[1] / "share/proj")
)
import numpy as np
import pandas as pd
import rasterio
import torch
from rasterio.warp import transform
from torch import nn
from torch.nn import functional as F

from applied_execution import atomic, sha
from applied_local_inputs import pair_rows, read_inputs
from applied_spatial_models import CompactUNet, GalileoRadar, prithvi, terramind
from applied_unet import StandardUNet


def make_model(task, learner):
    classes = 3 if task == "copernicus" else 2
    channels = {"terramind": 15, "galileo": 2, "prithvi": 6, "copernicus": 4}[task]
    if learner == "native":
        if task == "copernicus":
            from applied_copernicus import CopernicusRadarChange

            return CopernicusRadarChange()
        return {"terramind": terramind, "galileo": GalileoRadar, "prithvi": prithvi}[task]()
    if learner == "linear":
        return nn.Conv2d(channels, classes, 1)
    if learner == "unet_standard":
        return StandardUNet(channels, classes)
    model = CompactUNet(channels)
    model.head = nn.Conv2d(16, classes, 1)
    return model


def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument("directory", type=Path)
    p.add_argument("--physical", action="store_true")
    a = p.parse_args()
    d = a.directory
    manifest = json.loads((d / "manifest.json").read_text())
    args = manifest["arguments"]
    task = args["task"]
    learner = args["learner"]
    if args["device"] == "mps" and not a.physical:
        ownership = ROOT / "results/applied_study_v3/.mps-owner.lock"
        ownership.parent.mkdir(parents=True, exist_ok=True)
        device_lock = ownership.open("a")
        fcntl.flock(device_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)

    if args["budget"] != 1.0:
        raise ValueError("Local application protocol uses complete-label fits, all folds/seeds")
    out = d / ("local-physical" if a.physical else "local")
    out.mkdir(exist_ok=False)
    selection = json.loads((d / "selection.json").read_text())
    checkpoint = d / f"trial-{selection['trial']}.pt"
    if sha(checkpoint) != selection["checkpoint_sha256"]:
        raise ValueError("Selected state changed")
    device = torch.device(args["device"])
    if not a.physical:
        model = make_model(task, learner)
        state = torch.load(checkpoint, map_location="cpu", weights_only=True)
        if task == "galileo" and learner == "native":
            expected = {k for k in model.state_dict() if not k.startswith("encoder.")}
            if set(state) != expected:
                raise ValueError("Cached/native Galileo probe mismatch")
            result = model.load_state_dict(state, strict=False)
            if result.unexpected_keys or any(
                not k.startswith("encoder.") for k in result.missing_keys
            ):
                raise ValueError("Incomplete Galileo probe load")
        elif manifest.get("checkpoint_policy") == "omit_frozen_encoder_only":
            result = model.load_state_dict(state, strict=False)
            if result.unexpected_keys or any(
                not k.startswith("encoder.") for k in result.missing_keys
            ):
                raise ValueError("Missing task state")
        else:
            model.load_state_dict(state, strict=True)
        if args.get("on_device_pool"):
            from applied_fast_pool import install_on_device_pools

            install_on_device_pools(model)
        model.to(device).eval()
    else:
        physical_path = (
            ROOT / f"results/applied_study_v2/physical/{task}-{args['fold']}/selection.json"
        )
        physical = json.loads(physical_path.read_text())["candidate"]
    torch.set_num_threads(args.get("threads", 1))
    pairs_path = (
        ROOT / "results/applied_study_v1/local_references/scoring/scene-reference-pairs.parquet"
    )
    rows = pair_rows(pd.read_parquet(pairs_path), task)
    sources = ROOT / "data/raw/limburg_applied_tasks/local_scenes"
    entries = []
    ledger = []
    hashes = {str(pairs_path.relative_to(ROOT)): sha(pairs_path)}
    for source in [
        Path(__file__),
        ROOT / "src/applied_local_inputs.py",
        ROOT / "src/applied_spatial_models.py",
        ROOT / "src/applied_copernicus.py",
        ROOT / "src/applied_mps_pool.py",
        ROOT / "src/applied_fast_pool.py",
    ]:
        hashes[str(source.relative_to(ROOT))] = sha(source)
    started = time.perf_counter()
    for i, pair in enumerate(rows):
        row = pair["primary"]
        r = dict(path=row["path"], available=pair["available"], pair_rule=pair["pair_rule"])
        if not pair["available"]:
            ledger.append(dict(**r, status="missing_compatible_pair"))
            continue
        x, valid, profile = read_inputs(pair, task, sources)
        for srcrow in [row, pair["paired"]]:
            if srcrow:
                hashes[str((sources / srcrow["path"]).relative_to(ROOT))] = sha(
                    sources / srcrow["path"]
                )
        prediction = np.full(valid.shape, 255, dtype=np.uint8)
        if valid.any() and a.physical:
            from applied_physical import predict, source_features

            source = x
            if task == "prithvi":
                source = F.interpolate(
                    torch.from_numpy(x[None]), size=(224, 224), mode="bilinear", align_corners=False
                )[0].numpy()
            features = source_features(source, task)
            if task == "prithvi":
                features = {
                    k: F.interpolate(
                        torch.from_numpy(v.copy())[None, None],
                        size=(512, 512),
                        mode="bilinear",
                        align_corners=False,
                    )[0, 0].numpy()
                    for k, v in features.items()
                }
            prediction = predict(features, physical)
        elif valid.any():
            with torch.no_grad():
                if task == "galileo":
                    for top in range(0, 512, 64):
                        for left in range(0, 512, 64):
                            xx = torch.from_numpy(x[:, top : top + 64, left : left + 64][None]).to(
                                device
                            )
                            logits = (
                                model(xx, torch.tensor([row["time"].month - 1], device=device))
                                if learner == "native"
                                else model(xx)
                            )
                            prediction[top : top + 64, left : left + 64] = (
                                logits.argmax(1)[0].cpu().numpy()
                            )
                elif task == "copernicus":
                    for top in range(0, 512, 224):
                        for left in range(0, 512, 224):
                            h = min(224, 512 - top)
                            width = min(224, 512 - left)
                            chunk = np.zeros((4, 224, 224), dtype=np.float32)
                            chunk[:, :h, :width] = x[:, top : top + h, left : left + width]
                            xx = torch.from_numpy(chunk[None]).to(device)
                            if learner == "native":
                                east, north = rasterio.transform.xy(
                                    profile["transform"], top + 112, left + 112
                                )
                                lon, lat = transform(profile["crs"], "EPSG:4326", [east], [north])
                                dates = [pair["paired"]["time"], row["time"]]
                                metadata = torch.tensor(
                                    [
                                        [
                                            [
                                                lon[0],
                                                lat[0],
                                                (
                                                    t - pd.Timestamp("1970-01-01", tz="UTC")
                                                ).total_seconds()
                                                / 86400,
                                                0.0256,
                                            ]
                                            for t in dates
                                        ]
                                    ],
                                    dtype=torch.float32,
                                    device=device,
                                )
                                logits = model(xx, metadata)[0]
                            else:
                                logits = model(xx)
                            prediction[top : top + h, left : left + width] = (
                                logits.argmax(1)[0, :h, :width].cpu().numpy()
                            )
                else:
                    xx = torch.from_numpy(x[None]).to(device)
                    if task == "prithvi":
                        xx = F.interpolate(
                            xx, size=(224, 224), mode="bilinear", align_corners=False
                        )
                    if learner == "native" and task == "terramind":
                        logits = model({"S2L1C": xx[:, :13], "S1GRD": xx[:, 13:]}).output
                    elif learner == "native":
                        with rasterio.open(sources / row["path"]) as ds:
                            east, north = ds.xy(256, 256)
                        lon, lat = transform(profile["crs"], "EPSG:4326", [east], [north])
                        t = row["time"]
                        logits = model(
                            xx,
                            temporal_coords=torch.tensor(
                                [[[t.year, t.dayofyear]]], device=device, dtype=torch.float32
                            ),
                            location_coords=torch.tensor(
                                [[lat[0], lon[0]]], device=device, dtype=torch.float32
                            ),
                        ).output
                    else:
                        logits = model(xx)
                    logits = F.interpolate(
                        logits, size=(512, 512), mode="bilinear", align_corners=False
                    )
                    prediction = logits.argmax(1)[0].cpu().numpy().astype(np.uint8)
        prediction[~valid] = 255
        stem = hashlib.sha256(row["path"].encode()).hexdigest()[:20]
        pred = out / f"{stem}-prediction.tif"
        mask = out / f"{stem}-valid.tif"
        profile.update(driver="GTiff", count=1, dtype="uint8", compress="deflate")
        for path, array, nodata in [(pred, prediction, 255), (mask, valid.astype(np.uint8), 0)]:
            with rasterio.open(path, "w", **dict(profile, nodata=nodata)) as ds:
                ds.write(array, 1)
        case = f"{row['aoi']}:{row['sensor']}:{row['scene']}"
        entries.append(
            dict(
                case=case,
                model=(f"{task}-physical-{args['fold']}" if a.physical else d.name),
                grid=row["grid"],
                prediction=str(pred.resolve()),
                valid=str(mask.resolve()),
                reference=str((ROOT / row["reference_path"]).resolve()),
                kind="three_class_flood" if task == "copernicus" else "surface_water",
                reference_offset_hours=row["reference_offset_hours"],
                reference_dependence=row["reference_dependence"],
            )
        )
        r.update(
            status="predicted",
            paired_path=pair["paired"]["path"] if pair["paired"] else None,
            pair_lag_h=(row["time"] - pair["paired"]["time"]).total_seconds() / 3600
            if pair["paired"]
            else None,
            valid_pixels=int(valid.sum()),
        )
        ledger.append(r)
        if i % 20 == 0:
            atomic(out / "progress.json", dict(tiles_done=i + 1, total=len(rows)))
            print(json.dumps(dict(local_tiles=i + 1, total=len(rows))), flush=True)
    if a.physical:
        hashes[str(physical_path.relative_to(ROOT))] = sha(physical_path)
    atomic(out / "manifest.json", entries)
    atomic(
        out / "complete.json",
        dict(
            status="completed",
            source_hashes=hashes,
            prediction_hashes={str(p.relative_to(out)): sha(p) for p in out.glob("*.tif")},
            checkpoint_sha256=sha(checkpoint),
            cases=ledger,
            elapsed_s=time.perf_counter() - started,
            interpretation="All compatible source cases retained, including zero-support/cloudy cases. Fixed lagged pairing, QA masks and nonoverlapping windows. Different dates/granules are dependent; no independent-flood or peak-inundation claim. Copernicus operates in224px native-grid windows with normalized-mean padded edges.",
        ),
    )


if __name__ == "__main__":
    main()
