"""Recover OlmoEarth/Galileo with native block-consistent observation masks.

Default prints the plan. --smoke tests two real held monthly frames; --run
processes all currently complete tile sequences (or the named context), with no
random subsample. Missing calendar slots are not bridged or fabricated.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import runpy
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from importlib.metadata import distributions
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.eo_inputs import ROUTES, patch_origins, read_tile, sha256
from src.eo_inputs import get_patch as original_get_patch
from src.eo_mps import install
from src.eo_token_masks import token_observations


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.partial")
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    tmp.replace(path)


def identity(model):
    manifest = json.loads((ROOT / "config/limburg_eo_model_assets.json").read_text())
    asset = next(m for m in manifest["models"] if m["id"] == model)
    verify = runpy.run_path(str(ROOT / "scripts/97_download_limburg_eo_models.py"))["verify"]
    base = ROOT / manifest["destination"]
    weight_hashes = {
        a["path"]: verify(base / "models" / model / a["path"], a) for a in asset["assets"]
    }
    directories = (
        [ROOT / asset["source"]["path"]] if asset.get("source") else [base / "models" / model]
    )
    if model == "terramind":
        directories.append(base / "code/terratorch")
    paths = [
        Path(__file__).resolve(),
        ROOT / "scripts/100_extract_limburg_eo_sequences.py",
        ROOT / "src/eo_token_masks.py",
        ROOT / "src/eo_mps.py",
        ROOT / "infrastructure/eo_census/prepare_cloud.py",
        ROOT / "src/eo_inputs.py",
        ROOT / "src/eo_encoders.py",
        ROOT / "environments/eo-screen/check_load.py",
    ]
    paths.extend(p for d in directories for p in sorted(d.rglob("*.py")))
    env = ROUTES[model][2]
    paths.append(ROOT / f"environments/eo-screen/{env}-macos-arm64.lock.txt")
    return {
        "model": model,
        "checkpoint": asset["checkpoint"],
        "weights": weight_hashes,
        "code": {str(p.relative_to(ROOT)): sha256(p) for p in paths},
        "input_contract": asset["input_contract"],
        "python": sys.version,
        "packages": {d.metadata["Name"]: d.version for d in distributions()},
        "seed": 1729,
        "temporal_readout": "native_temporal"
        if model in {"olmoearth", "galileo", "anysat", "prithvi", "presto"}
        else "equal_frame_mean_order_invariant",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, choices=["olmoearth", "galileo"])
    parser.add_argument("--archive", type=Path, default=ROOT / "data/raw/limburg_compact_eo")
    parser.add_argument(
        "--preparation", type=Path, default=ROOT / "results/eo_comparison_preparation"
    )
    parser.add_argument(
        "--output", type=Path, default=ROOT / "data/processed/limburg_eo_token_consistent_sequences"
    )
    parser.add_argument("--context")
    parser.add_argument("--smoke-kind", choices=["two", "monthly"], default="two")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--run", action="store_true")
    modes.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    product, size, _ = ROUTES[args.model]
    stride = 4 if args.model == "olmoearth" else 8

    def get_patch(tile, row, col, size):
        patch = original_get_patch(tile, row, col, size)
        patch["valid"] = token_observations(patch["valid"], stride)
        return patch

    contexts = json.loads((args.preparation / "contexts.json").read_text())
    if args.context:
        contexts = [c for c in contexts if c["context_id"] == args.context]
    if args.context and not contexts:
        raise ValueError("Unknown context")
    if args.smoke:
        if args.smoke_kind == "monthly":
            ends = [datetime(2018, m, 1, tzinfo=timezone.utc) for m in range(1, 13)] + [
                datetime(2019, 1, 1, tzinfo=timezone.utc)
            ]
            windows = [
                {"id": f"monthly_{a:%Y%m%d}_{b:%Y%m%d}"}
                for a, b in zip(ends[:-1], ends[1:], strict=True)
            ]
        else:
            windows = [{"id": "monthly_20180801_20180901"}, {"id": "monthly_20180901_20181001"}]
        contexts = [
            {
                "context_id": "engineering_" + args.smoke_kind + "_real_months",
                "kind": "engineering",
                "windows": windows,
            }
        ]
    jobs = json.loads((args.archive / "jobs.json").read_text())
    indexed = {(j["window"]["id"], tuple(j["bounds"]), j["product"]): j for j in jobs}
    by_window = {}
    for j in jobs:
        if j["product"] == product:
            by_window.setdefault(j["window"]["id"], {})[tuple(j["bounds"])] = j
    print(
        json.dumps(
            {
                "model": args.model,
                "contexts": len(contexts),
                "mode": "smoke" if args.smoke else "run" if args.run else "inventory",
                "native_temporal": args.model
                in {"olmoearth", "galileo", "anysat", "prithvi", "presto"},
            }
        ),
        flush=True,
    )
    if not args.run and not args.smoke:
        return 0

    def local(j):
        p = args.archive / j["relative_path"]
        return p.exists() and p.with_suffix(".receipt.json").exists()

    fingerprint = identity(args.model)
    fingerprint["execution_device"] = "mps"
    fingerprint["mask_policy"] = "all_pixels_observed_in_native_token_block_v1"
    fingerprint["token_stride"] = stride
    fingerprint["purpose"] = "engineering" if args.smoke else "context_census"
    run = hashlib.sha256(json.dumps(fingerprint, sort_keys=True).encode()).hexdigest()
    target = args.output / args.model / run
    atomic_json(target / "manifest.json", fingerprint)
    install()
    from src.eo_encoders import Encoder

    encoder = Encoder(args.model)
    legacy_base = (
        ROOT
        / "data/processed"
        / ("limburg_eo_mps_sequences" if args.model == "olmoearth" else "limburg_eo_sequences")
        / args.model
    )
    legacy_runs = []
    for candidate in sorted(legacy_base.glob("*/manifest.json")):
        old = json.loads(candidate.read_text())
        if old.get("purpose") != "context_census" or old.get("execution_device") != "mps":
            continue
        if any(
            old.get(k) != fingerprint.get(k) for k in ("weights", "checkpoint", "packages", "seed")
        ):
            continue
        if all(sha256(ROOT / name) == digest for name, digest in old["code"].items()):
            legacy_runs.append(candidate.parent)

    counts = {
        "written": 0,
        "resumed": 0,
        "reused_unchanged": 0,
        "incomplete_tile_sequences": 0,
        "no_observation": 0,
        "errors": 0,
    }
    started = datetime.now(timezone.utc).isoformat()
    visited = 0

    def progress(status, context=None):
        snapshot = {
            "run": run,
            **counts,
            "status": status,
            "started_utc": started,
            "updated_utc": datetime.now(timezone.utc).isoformat(),
            "contexts_total": len(contexts),
            "current_context": context,
            "patches_visited": visited,
        }
        atomic_json(target / "status.json", snapshot)
        print(json.dumps(snapshot), flush=True)

    progress("running")
    for context in contexts:
        progress("running", context["context_id"])
        keys = [w["id"] for w in context["windows"]]
        bounds_set = set().union(*(set(by_window.get(k, {})) for k in keys))
        if args.smoke:
            bounds_set = {b for b in bounds_set if b[0] == 297600 and b[1] == 5625600}
        for bounds in sorted(bounds_set):
            sequence = [by_window.get(k, {}).get(bounds) for k in keys]
            if any(j is None or not local(j) for j in sequence):
                counts["incomplete_tile_sequences"] += 1
                continue
            if product == "s2_10m" and any(
                not indexed.get((k, bounds, "s2_20m")) or not local(indexed[(k, bounds, "s2_20m")])
                for k in keys
            ):
                counts["incomplete_tile_sequences"] += 1
                continue
            try:
                tiles = [read_tile(args.archive, j, indexed) for j in sequence]
                origins = patch_origins(tiles[0], size)
                if args.smoke:
                    origins = [
                        max(
                            origins,
                            key=lambda rc: min(
                                int(t.valid[rc[0] : rc[0] + size, rc[1] : rc[1] + size].sum())
                                for t in tiles
                            ),
                        )
                    ]
                for row, col in origins:
                    visited += 1
                    if visited % 100 == 1:
                        progress("running", context["context_id"])
                        if shutil.disk_usage(args.output).free < 60 * 2**30:
                            progress("paused_free_space", context["context_id"])
                            raise SystemExit(75)
                    try:
                        patches = [get_patch(t, row, col, size) for t in tiles]
                        key = f"{int(bounds[0])}_{int(bounds[1])}/{row}_{col}"
                        path = target / context["context_id"] / (key + ".npz")
                        meta = {
                            "context_id": context["context_id"],
                            "kind": context["kind"],
                            "frames": [p["metadata"] for p in patches],
                            "run": run,
                            "temporal_readout": fingerprint["temporal_readout"],
                        }
                        if any(not p["valid"].any() for p in patches):
                            atomic_json(
                                path.with_suffix(".json"),
                                {"status": "incomplete_native_token_sequence", "identity": meta},
                            )
                            counts["no_observation"] += 1
                            continue
                        receipt = path.with_suffix(".json")
                        if path.exists() and receipt.exists():
                            saved = json.loads(receipt.read_text())
                            if saved.get("identity") == meta and saved.get("sha256") == sha256(
                                path
                            ):
                                counts["resumed"] += 1
                                continue
                        reused = False
                        for legacy in legacy_runs:
                            old_path = legacy / context["context_id"] / (key + ".npz")
                            old_receipt = old_path.with_suffix(".json")
                            if not old_path.exists() or not old_receipt.exists():
                                continue
                            saved = json.loads(old_receipt.read_text())
                            old_meta = saved.get("identity", {})
                            if saved.get("status") != "finite_sequence" or any(
                                old_meta.get(k) != meta[k]
                                for k in ("context_id", "kind", "frames", "temporal_readout")
                            ):
                                continue
                            if saved.get("sha256") != sha256(old_path):
                                raise ValueError("Legacy embedding checksum mismatch")
                            with np.load(old_path) as previous:
                                if not np.array_equal(
                                    previous["valid"], np.stack([p["valid"] for p in patches])
                                ):
                                    continue
                                if not np.isfinite(previous["embedding"]).all():
                                    raise ValueError("Legacy embedding nonfinite")
                            path.parent.mkdir(parents=True, exist_ok=True)
                            # Identical values/masks/dates and unchanged frozen encoder: reuse bytes.
                            import os

                            os.link(old_path, path)
                            atomic_json(
                                receipt,
                                {
                                    **saved,
                                    "identity": meta,
                                    "reused_from": str(old_path.relative_to(ROOT)),
                                },
                            )
                            counts["reused_unchanged"] += 1
                            reused = True
                            break
                        if reused:
                            continue
                        vector = encoder.sequence(patches)
                        repeatable = None
                        if args.smoke:
                            repeatable = bool(np.array_equal(vector, encoder.sequence(patches)))
                            if not repeatable:
                                raise ValueError("Temporal output not repeatable")
                        masks = np.stack([p["valid"] for p in patches])
                        days = np.stack([p["days"] for p in patches])
                        path.parent.mkdir(parents=True, exist_ok=True)
                        with tempfile.NamedTemporaryFile(
                            dir=path.parent, suffix=".npz", delete=False
                        ) as f:
                            tmp = Path(f.name)
                            np.savez_compressed(f, embedding=vector, valid=masks, acquired_day=days)
                        tmp.replace(path)
                        atomic_json(
                            receipt,
                            {
                                "identity": meta,
                                "status": "finite_sequence",
                                "sha256": sha256(path),
                                "dimension": len(vector),
                                "repeatable": repeatable,
                            },
                        )
                        counts["written"] += 1
                    except Exception as e:
                        counts["errors"] += 1
                        atomic_json(
                            target
                            / "errors"
                            / context["context_id"]
                            / f"{int(bounds[0])}_{int(bounds[1])}_{row}_{col}.json",
                            {"error": f"{type(e).__name__}: {e}", "row": row, "col": col},
                        )
                        print(f"PATCH ERROR {args.model}: {type(e).__name__}: {e}", flush=True)

            except Exception as e:
                counts["errors"] += 1
                atomic_json(
                    target
                    / "errors"
                    / context["context_id"]
                    / (f"{int(bounds[0])}_{int(bounds[1])}.json"),
                    {"error": f"{type(e).__name__}: {e}"},
                )
                print(
                    f"ERROR {args.model} {context['context_id']}: {type(e).__name__}: {e}",
                    flush=True,
                )
    counts["updated_utc"] = datetime.now(timezone.utc).isoformat()
    progress("completed" if not counts["errors"] else "completed_with_errors")
    print(json.dumps({"run": run, **counts}), flush=True)
    return int(counts["errors"] > 0 or (args.smoke and counts["written"] + counts["resumed"] == 0))


if __name__ == "__main__":
    raise SystemExit(main())
