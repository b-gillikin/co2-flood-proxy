"""Stream model-specific EO/raw features into resumable tile contributions.

--smoke is an isolated availability-selected engineering fixture. --benchmark
finishes one full production context and retains it for --run; --run processes
all planned contexts, including empty-source entries, without sampling events.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import resource
import runpy
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault(
    "PROJ_DATA", str((ROOT / ".venv-foundation/bin/python").resolve().parents[1] / "share/proj")
)
sys.path.insert(0, str(ROOT))
import geopandas as gpd
import numpy as np
import pandas as pd
from rasterio.transform import from_origin
from shapely.geometry import box

from src.eo_event_inputs import completed_windows, context_id
from src.eo_individual_archive import Archive
from src.eo_individual_features import (
    Moments,
    channel_features,
    grid_weights,
    texture,
)
from src.eo_individual_output import assemble_features
from src.eo_individual_spatial import (
    SpatialInputs,
    blank_tile,
    fast_patch,
    fixed_elevation_cuts,
    region_weights,
)
from src.eo_inputs import ROUTES, Tile, sha256

DIM = {
    "presto": 128,
    "anysat": 768,
    "galileo": 128,
    "olmoearth": 192,
    "croma": 768,
    "prithvi": 192,
    "copernicus_fm": 768,
    "terramind": 192,
    "dofa": 768,
    "satmae": 768,
}
CACHED = {"dofa", "satmae"}
KIND = {
    m: (
        "monthly"
        if m in {"presto", "galileo", "dofa"}
        else "monthly_snapshot"
        if m == "satmae"
        else "recent"
    )
    for m in DIM
}
OUT = ROOT / "results/limburg_individual_experiments_v1"


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(value, indent=2) + "\n")
    tmp.replace(path)


def init_moments(target, key, dim):
    if key not in target:
        target[key] = Moments.empty(dim)
    return target[key]


def add_maps(target, gauge, bundle, weights, model):
    for label, values in bundle.items():
        if label.endswith("_support"):
            continue
        support = bundle[label + "_support"]
        if len(support) != len(values):
            raise ValueError("Encoder time/support mismatch")
        for ti, features in enumerate(values):
            for region, area in enumerate(weights):
                w = grid_weights(area * support[ti], features.shape[:2])
                init_moments(target, f"{gauge}|{label}|{ti}|{region}", features.shape[-1]).add(
                    features.reshape(-1, features.shape[-1]), w.ravel()
                )


def add_raw(target, gauge, frames, weights, model, physical):
    for ti, p in enumerate(frames):
        values = p["values"]
        bands = p["metadata"]["bands"]
        valid = p["valid"]
        if model == "dofa":
            values = values[[3, 4, 5, 6, 8, 9]]
            bands = [bands[i] for i in [3, 4, 5, 6, 8, 9]]
        data, names = channel_features(values, bands)
        # Acquisition day and geometry are known metadata, not future labels.
        data = np.concatenate([data, p["days"][None]])
        full = Moments.empty(data.shape[0])
        full.add(data.reshape(len(data), -1).T, valid.ravel())
        for region, area in enumerate(weights):
            observed = area * valid
            init_moments(target, f"{gauge}|raw|{ti}|{region}", len(data)).add(
                data.reshape(len(data), -1).T, observed.ravel()
            )
            summary = np.r_[
                full.output(),
                texture(values, valid, np.ones(valid.shape)),
                valid.mean(),
                p["metadata"]["latitude"],
                p["metadata"]["longitude"],
                p["metadata"]["padding_pixels"] / valid.size,
            ]
            init_moments(target, f"{gauge}|context|{ti}|{region}", len(summary)).add(
                summary[None], np.array([observed.sum()])
            )
            if physical is not None:
                climate = physical["climate"][ti]
                init_moments(target, f"{gauge}|climate|{ti}|{region}", 2).add(
                    climate[None], np.array([area.sum()])
                )
                terrain = physical["terrain"]
                if ti == 0:
                    init_moments(target, f"{gauge}|terrain|0|{region}", 2).add(
                        terrain.reshape(2, -1).T, area.ravel()
                    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, choices=list(DIM))
    parser.add_argument("--device", choices=["cpu", "mps"], default="cpu")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--smoke", action="store_true")
    mode.add_argument("--benchmark", action="store_true")
    mode.add_argument("--run", action="store_true")
    args = parser.parse_args()
    model = args.model
    plan_path = ROOT / "config/limburg_individual_encoder_experiments_v1.json"
    plan = json.loads(plan_path.read_text())
    cases = pd.read_parquet(ROOT / plan["shared"]["source"] / "preparation/cases.parquet")
    kind = KIND[model]
    contexts = {}
    for cutoff in cases.cutoff_utc.unique():
        windows = completed_windows(cutoff, kind)
        cid = context_id(kind, windows)
        contexts[cid] = {"context_id": cid, "kind": kind, "windows": windows}
    all_contexts = sorted(contexts.values(), key=lambda c: c["windows"][-1]["end"])
    engineering = [c for c in all_contexts if c["windows"][-1]["start"].startswith("2018-")]
    if not engineering:
        raise ValueError("Fixed engineering year has no planned contexts")
    # An availability-only fixture; not an event/outcome sample for inference.
    chosen = [engineering[0]] if args.smoke or args.benchmark else all_contexts
    geometry_path = ROOT / "results/eo_comparison_preparation/catchments.gpkg"
    catchments = gpd.read_file(geometry_path)
    archive = Archive(ROOT, model)
    product, size, _ = ROUTES[model]
    bounds = sorted(
        {
            tuple(j["bounds"])
            for j in archive.index.values()
            if j["product"] == product
            and any(g.intersects(box(*j["bounds"])) for g in catchments.geometry)
        }
    )
    spatial = SpatialInputs(ROOT)
    dest = OUT / ("engineering" if args.smoke else "features") / model
    dest.mkdir(parents=True, exist_ok=True)
    lock = (dest / ".lock").open("w")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    cuts_path = OUT / "spatial/elevation-thirds.json"
    cuts_path.parent.mkdir(parents=True, exist_ok=True)
    with cuts_path.with_suffix(".lock").open("w") as cuts_lock:
        fcntl.flock(cuts_lock, fcntl.LOCK_EX)
        if cuts_path.exists():
            cuts = json.loads(cuts_path.read_text())
        else:
            cuts = {
                str(c.gauge): fixed_elevation_cuts(c.geometry, bounds, spatial)
                for c in catchments.itertuples()
            }
            atomic_json(cuts_path, cuts)
    source_paths = [
        plan_path,
        ROOT / plan["shared"]["source"] / "preparation/cases.parquet",
        ROOT / plan["shared"]["source"] / "preparation/manifest.json",
        geometry_path,
        Path(__file__),
        *(
            ROOT / "src" / n
            for n in [
                "eo_individual_features.py",
                "eo_individual_encoders.py",
                "eo_individual_archive.py",
                "eo_individual_spatial.py",
                "eo_individual_output.py",
                "eo_event_inputs.py",
                "eo_inputs.py",
                "eo_coherent_inputs.py",
                "eo_encoder_corrections.py",
                "eo_token_masks.py",
                "eo_expansion_inputs.py",
            ]
        ),
        *archive.catalogues,
        cuts_path,
        ROOT / "config/limburg_eo_model_assets.json",
        *sorted((ROOT / "data/raw/dem/glo30").glob("*.tif")),
    ]
    if model == "galileo":
        physical_manifest = ROOT / "data/raw/limburg_galileo_physical/manifest.json"
        source_paths.append(physical_manifest)
        source_paths.append(
            ROOT / "data/raw/limburg_dynamic_model_weights/code/galileo/config/normalization.json"
        )
        for record in json.loads(physical_manifest.read_text())["files"]:
            path = ROOT / record["path"]
            assert sha256(path) == record["sha256"], "Galileo physical input changed"
            receipt_path = path.with_suffix(".receipt.json")
            assert json.loads(receipt_path.read_text())["bands"] == record["bands"]
            source_paths.extend([path, receipt_path])
    if model in CACHED:
        selection_path = ROOT / (
            "config/limburg_eo_supplemental_selected_runs/satmae_toa_qa60.json"
            if model == "satmae"
            else "config/limburg_eo_coherent_selected_runs.json"
        )
        selected_cached = json.loads(selection_path.read_text())["models"][model]
        source_paths.extend(
            [
                selection_path,
                ROOT / selected_cached["run"] / "manifest.json",
                ROOT / selected_cached["aggregate"] / f"{model}.parquet",
                ROOT / selected_cached["aggregate"] / "patch_areas.parquet",
            ]
        )

    identity = {str(p.relative_to(ROOT)): sha256(p) for p in source_paths}
    publisher = runpy.run_path(str(ROOT / "scripts/100_extract_limburg_eo_sequences.py"))[
        "identity"
    ](model)
    publisher["legacy_helper_readout"] = publisher.pop("temporal_readout")
    actual_runtime = dict(python=sys.version, numpy=np.__version__, executable=sys.executable)
    if model not in CACHED:
        import torch

        actual_runtime["torch"] = torch.__version__
    identity["execution_contract"] = dict(
        model=model,
        device=args.device,
        publisher=publisher,
        actual_runtime=actual_runtime,
        individual_readout=next(e["model_use"] for e in plan["experiments"] if e["model"] == model),
    )
    fingerprint = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    if args.smoke:
        dest = dest / fingerprint
        dest.mkdir(parents=True, exist_ok=True)
    bound = dest / "identity.json"
    if bound.exists():
        assert json.loads(bound.read_text())["fingerprint"] == fingerprint, (
            "Feature code/data changed; version output instead of mixing"
        )
    else:
        atomic_json(
            bound,
            {
                "fingerprint": fingerprint,
                "sources": identity,
                "model": model,
                "device": args.device,
                "context_count": len(all_contexts),
            },
        )
    selected = json.loads((ROOT / "config/limburg_eo_coherent_selected_runs.json").read_text())[
        "models"
    ]
    accepted = {}
    accepted_tiles = set()
    cached_data = None
    run = None
    if model in CACHED:
        if model == "satmae":
            selected = json.loads(
                (
                    ROOT / "config/limburg_eo_supplemental_selected_runs/satmae_toa_qa60.json"
                ).read_text()
            )["models"]
        source = ROOT / selected[model]["aggregate"]
        run = ROOT / selected[model]["run"]
        ledger = pd.read_parquet(source / "patch_areas.parquet")
        accepted = {
            (r.context_id, r.tile, int(r.row), int(r.col), str(r.gauge))
            for r in ledger.itertuples()
        }
        accepted_tiles = {(k[0], k[1]) for k in accepted}
        cached_data = pd.read_parquet(source / f"{model}.parquet")
        cached_data = cached_data[cached_data.kind.eq(kind)].set_index(
            ["context_id", "catchment_gauge"]
        )
    # Import before loading publishers that use their own package named src.
    encoder = None
    if model not in CACHED:
        from src.eo_individual_encoders import IndividualEncoder

        encoder = IndividualEncoder(model, args.device)
    began = time.monotonic()
    completed = 0
    patches = 0
    fixture_done = False
    for context in chosen:
        cid = context["context_id"]
        windows = context["windows"]
        context_started = time.monotonic()
        for b in bounds:
            tile_name = f"{int(b[0])}_{int(b[1])}"
            target = dest / "tiles" / cid / (tile_name + ".npz")
            receipt = target.with_suffix(".json")
            if target.exists() and receipt.exists():
                record = json.loads(receipt.read_text())
                assert record["fingerprint"] == fingerprint and sha256(target) == record["sha256"]
                continue
            archive.current_inputs = {}
            intersect = [c for c in catchments.itertuples() if c.geometry.intersects(box(*b))]
            if model in CACHED and (cid, tile_name) not in accepted_tiles:
                tiles = []
            else:
                tiles = [archive.tile(w, b, product) for w in windows]
            sums = {}
            errors = []
            tile_patches = 0
            if tiles:
                resolution = 30 if model == "prithvi" else 10
                n = round(9600 / resolution)
                template = next(
                    (t for t in tiles if t is not None),
                    Tile(
                        np.zeros(
                            (
                                6 if product == "hls" else 2 if product == "s1_ascending" else 10,
                                n,
                                n,
                            ),
                            np.float32,
                        ),
                        np.zeros((n, n), bool),
                        np.zeros((n, n)),
                        ["blue", "green", "red", "nir", "swir1", "swir2"]
                        if product == "hls"
                        else ["VV", "VH"]
                        if product == "s1_ascending"
                        else ["B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A", "B11", "B12"],
                        from_origin(b[0], b[3], resolution, resolution),
                        "EPSG:32632",
                        [],
                        windows[0],
                    ),
                )
                tiles = [
                    t if t is not None else blank_tile(template, w)
                    for t, w in zip(tiles, windows, strict=True)
                ]
                dem = spatial.elevation(b, resolution)
                weights = {
                    str(c.gauge): region_weights(c.geometry, b, resolution, dem, cuts[str(c.gauge)])
                    for c in intersect
                }
                physical_tile = (
                    spatial.physical_tile(b, windows, resolution) if model == "galileo" else None
                )
                origins = [(r, c) for r in range(0, n, size) for c in range(0, n, size)]
                if args.smoke:
                    origins = sorted(
                        origins,
                        key=lambda rc: (
                            -sum(
                                t.valid[rc[0] : rc[0] + size, rc[1] : rc[1] + size].sum()
                                for t in tiles
                            )
                        ),
                    )
                for row, col in origins:
                    owners = [
                        c
                        for c in intersect
                        if weights[str(c.gauge)][0, row : row + size, col : col + size].sum() > 0
                        and (
                            model not in CACHED
                            or (cid, tile_name, row, col, str(c.gauge)) in accepted
                        )
                    ]
                    if not owners:
                        continue
                    frames = [fast_patch(t, row, col, size) for t in tiles]
                    if not any(p["valid"].any() for p in frames) and model != "galileo":
                        continue
                    if model in CACHED:
                        path = run / cid / tile_name / f"{row}_{col}.npz"
                        with np.load(path) as saved:
                            for i, p in enumerate(frames):
                                if not np.array_equal(p["valid"], saved["valid"][i]):
                                    raise ValueError("Cached encoder/raw source support differs")
                                if not np.array_equal(
                                    p["days"][p["valid"]], saved["acquired_day"][i][p["valid"]]
                                ):
                                    raise ValueError("Cached encoder/raw acquisition differs")
                    physical = None
                    if physical_tile is not None:
                        terrain = np.full((2, size, size), np.nan)
                        source = physical_tile[0][:, row : row + size, col : col + size]
                        h, w = source.shape[-2:]
                        terrain[:, :h, :w] = source
                        climate = np.stack(
                            [
                                np.nanmean(x[:, row : row + size, col : col + size], axis=(1, 2))
                                for x in physical_tile[1]
                            ]
                        )
                        physical = {"terrain": terrain, "climate": climate}
                    bundle = encoder(frames, physical) if encoder else None
                    if args.smoke and encoder:
                        repeated = encoder(frames, physical)
                        for key in bundle:
                            if not np.allclose(bundle[key], repeated[key], rtol=1e-5, atol=1e-5):
                                raise ValueError(f"Repeatability failure: {model}/{key}")

                    for c in owners:
                        gauge = str(c.gauge)
                        area = np.zeros((4, size, size), np.float32)
                        source = weights[gauge][:, row : row + size, col : col + size]
                        h, w = source.shape[-2:]
                        area[:, :h, :w] = source
                        add_raw(sums, gauge, frames, area, model, physical)
                        if physical is None:
                            elevation = np.full((size, size), np.nan)
                            elevation[:h, :w] = dem[row : row + size, col : col + size]
                            for region in range(4):
                                init_moments(sums, f"{gauge}|terrain|0|{region}", 1).add(
                                    elevation.reshape(-1, 1), area[region].ravel()
                                )
                        if bundle is not None:
                            add_maps(sums, gauge, bundle, area, model)
                    tile_patches += 1
                    patches += 1
                    if tile_patches % 100 == 0:
                        atomic_json(
                            dest / "progress.json",
                            {
                                "status": "running",
                                "model": model,
                                "context": cid,
                                "contexts_done": completed,
                                "contexts_total": len(chosen),
                                "tile": tile_name,
                                "tile_patches": tile_patches,
                                "patches_this_process": patches,
                                "elapsed_s": time.monotonic() - began,
                            },
                        )
                    if args.smoke:
                        fixture_done = True
                        break
                if args.smoke and not fixture_done:
                    continue
            target.parent.mkdir(parents=True, exist_ok=True)
            tmp = target.with_suffix(".partial")
            with tmp.open("wb") as f:
                np.savez_compressed(f, **{k: v.arrays() for k, v in sums.items()})
            tmp.replace(target)
            atomic_json(
                receipt,
                {
                    "fingerprint": fingerprint,
                    "sha256": sha256(target),
                    "patches": tile_patches,
                    "input_hashes": archive.current_inputs.copy(),
                    "errors": errors,
                },
            )
            atomic_json(
                dest / "progress.json",
                {
                    "status": "running",
                    "model": model,
                    "context": cid,
                    "contexts_done": completed,
                    "contexts_total": len(chosen),
                    "patches": patches,
                    "elapsed_s": time.monotonic() - began,
                },
            )
            if args.smoke and fixture_done:
                break
        completed += 1
        atomic_json(
            dest / "context-status" / f"{cid}.json",
            {
                "status": "complete" if not args.smoke else "engineering_partial",
                "elapsed_s": time.monotonic() - context_started,
                "fingerprint": fingerprint,
            },
        )
        if args.smoke:
            break
    if args.smoke:
        if not fixture_done:
            raise ValueError("No fixed-year observed fixture available")
        fixture, _ = assemble_features(
            dest, chosen, catchments.gauge, model, DIM[model], cached_data
        )
        fixture_path = dest / "context_features.parquet"
        fixture.to_parquet(fixture_path, index=False)
        pd.testing.assert_frame_equal(fixture, pd.read_parquet(fixture_path))

        atomic_json(
            dest / "smoke.json",
            {
                "status": "completed",
                "fingerprint": fingerprint,
                "patches": patches,
                "elapsed_s": time.monotonic() - began,
                "peak_rss_gib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024**3,
                "compact_bytes": sum(p.stat().st_size for p in (dest / "tiles").rglob("*.*")),
                "projected_compact_gib": sum(
                    p.stat().st_size for p in (dest / "tiles").rglob("*.*")
                )
                * len(all_contexts)
                / 1024**3,
                "contexts_in_census": len(all_contexts),
                "repeatability_checked": encoder is not None,
            },
        )
        return
    if args.benchmark:
        atomic_json(
            dest / "benchmark.json",
            {
                "status": "completed",
                "fingerprint": fingerprint,
                "contexts": 1,
                "tiles": len(bounds),
                "elapsed_s": time.monotonic() - began,
                "peak_rss_gib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024**3,
                "compact_bytes": sum(p.stat().st_size for p in (dest / "tiles").rglob("*.*")),
                "projected_compact_gib": sum(
                    p.stat().st_size for p in (dest / "tiles").rglob("*.*")
                )
                * len(all_contexts)
                / 1024**3,
                "contexts_in_census": len(all_contexts),
            },
        )
        return
    frame, recovered_hashes = assemble_features(
        dest, all_contexts, catchments.gauge, model, DIM[model], cached_data
    )
    archive.inputs.update(recovered_hashes)
    frame.to_parquet(dest / "context_features.parquet", index=False)
    atomic_json(
        dest / "manifest.json",
        {
            "status": "completed",
            "model": model,
            "fingerprint": fingerprint,
            "contexts": len(all_contexts),
            "rows": len(frame),
            "sources": identity,
            "outputs": {"context_features.parquet": sha256(dest / "context_features.parquet")},
            "input_hashes": archive.inputs,
            "elapsed_s": time.monotonic() - began,
            "new_encoding": model not in CACHED,
        },
    )
    atomic_json(
        dest / "progress.json",
        {
            "status": "completed",
            "model": model,
            "contexts_done": len(all_contexts),
            "contexts_total": len(all_contexts),
        },
    )


if __name__ == "__main__":
    main()
