"""Full held S2 band-day agreement census, exact catchment areas, resumable by tile.

No model inference, event subsampling or raw-data edits. Reports coverage lost
under same-day masking; this is not a downstream model-performance sensitivity.
"""

import argparse
import fcntl
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import box

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.eo_coherent_inputs import POLICY, s2_components
from src.eo_event_inputs import pixel_area_weights
from src.eo_inputs import sha256


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=ROOT / "data/raw/limburg_compact_eo")
    parser.add_argument(
        "--preparation", type=Path, default=ROOT / "results/eo_comparison_preparation"
    )
    parser.add_argument("--out", type=Path, default=ROOT / "results/eo_band_day_census")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    lock = (args.out / ".lock").open("w")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    os.nice(10)
    jobs = json.loads((args.archive / "jobs.json").read_text())
    indexed = {(j["window"]["id"], tuple(j["bounds"]), j["product"]): j for j in jobs}
    selected = [j for j in jobs if j["product"] == "s2_10m"]
    catchments = gpd.read_file(args.preparation / "catchments.gpkg").to_crs(32632)
    geometries = {str(c.gauge): c.geometry for c in catchments.itertuples()}
    geometries["__union__"] = catchments.geometry.union_all()
    source_hashes = {
        str(p.relative_to(ROOT)): sha256(p)
        for p in [
            Path(__file__),
            ROOT / "src/eo_coherent_inputs.py",
            ROOT / "src/eo_event_inputs.py",
            ROOT / "src/eo_inputs.py",
            args.archive / "jobs.json",
            args.preparation / "catchments.gpkg",
        ]
    }
    identity = hashlib.sha256(json.dumps(source_hashes, sort_keys=True).encode()).hexdigest()
    ledger = args.out / "tiles" / identity
    ledger.mkdir(parents=True, exist_ok=True)
    weights = {}
    failures = []
    rows = []
    for n, j in enumerate(selected, 1):
        companion = indexed.get((j["window"]["id"], tuple(j["bounds"]), "s2_20m"))
        token = hashlib.sha256(j["relative_path"].encode()).hexdigest()
        dest = ledger / (token + ".json")
        try:
            if companion is None:
                raise ValueError("Missing 20m companion in held job ledger")
            actual = {
                x["relative_path"]: sha256(args.archive / x["relative_path"])
                for x in [j, companion]
            }
            if dest.exists():
                saved = json.loads(dest.read_text())
                if saved["input_sha256"] == actual:
                    rows.extend(saved["rows"])
                    continue
            _, common, same, da, db, _, _, _ = s2_components(args.archive, j, indexed)
            mixed = common & ~same
            tile_rows = []
            for gauge, geom in geometries.items():
                key = (gauge, tuple(j["bounds"]))
                if not geom.intersects(box(*j["bounds"])):
                    continue
                if key not in weights:
                    weights[key] = pixel_area_weights(geom, j["bounds"], 10)
                w = weights[key]
                total, retained = float(w[common].sum()), float(w[same].sum())
                tile_rows.append(
                    {
                        "window": j["window"]["id"],
                        "tile": str(j["bounds"]),
                        "gauge": gauge,
                        "observed_area_m2": total,
                        "same_day_area_m2": retained,
                        "mixed_day_area_m2": total - retained,
                        "mixed_day_fraction": (total - retained) / total if total else None,
                        "maximum_band_day_gap": float(abs(da - db)[common & (w > 0)].max())
                        if (common & (w > 0)).any()
                        else None,
                        "valid_pixels": int((common & (w > 0)).sum()),
                        "mixed_day_pixels": int((mixed & (w > 0)).sum()),
                    }
                )
            saved = {"input_sha256": actual, "rows": tile_rows}
            temp = dest.with_suffix(".partial")
            temp.write_text(json.dumps(saved, indent=2) + "\n")
            temp.replace(dest)
            rows.extend(tile_rows)
        except Exception as exc:
            failures.append({"job": j["relative_path"], "error": str(exc)})
        finally:
            if n % 25 == 0 or n == len(selected):
                progress = {
                    "status": "running"
                    if n < len(selected)
                    else ("completed_with_errors" if failures else "completed"),
                    "visited": n,
                    "total": len(selected),
                    "errors": len(failures),
                    "updated_utc": datetime.now(timezone.utc).isoformat(),
                }
                tmp = args.out / "progress.partial"
                tmp.write_text(json.dumps(progress, indent=2) + "\n")
                tmp.replace(args.out / "progress.json")
                print(json.dumps(progress), flush=True)
    frame = pd.DataFrame(rows)
    frame.to_parquet(args.out / "tile_catchment_areas.parquet", index=False)
    if len(frame):
        summary = frame.groupby(["gauge", "window"], as_index=False)[
            ["observed_area_m2", "same_day_area_m2", "mixed_day_area_m2"]
        ].sum()
        summary["mixed_day_fraction"] = (
            summary.mixed_day_area_m2 / summary.observed_area_m2.replace(0, np.nan)
        )
        summary.to_csv(args.out / "catchment_window_coverage.csv", index=False)
    manifest = {
        "identity": identity,
        "policy": POLICY,
        "jobs_total": len(selected),
        "successful_jobs": len(selected) - len(failures),
        "errors": failures,
        "source_sha256": source_hashes,
        "interpretation": "Full held tile/window census; overlapping windows/catchments are not independent observations. Union rows avoid spatial double-counting; no downstream score change has been measured.",
    }
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
