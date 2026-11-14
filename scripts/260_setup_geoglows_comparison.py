"""Acquire and prepare the paired Stages 1–2 experiment, preserving prior work.

Each phase is explicit. Setup does not start the full model comparison.
Use .venv-geoglows/bin/python for inventory/download (Zarr overlay).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("PROJ_DATA", str(Path(sys.base_prefix) / "share/proj"))
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd

from src.geoglows_experiment import disk_check, download, hour_end, sha, write_json

CONFIG = ROOT / "config/limburg_geoglows_stages12_v1.json"


def inventory(plan):
    import geopandas as gpd
    import pyogrio
    from shapely.geometry import Point, box

    raw = ROOT / plan["raw"]
    network = raw / "streams_209.gpkg"
    download(plan["geoglows"]["hydrography_uri"], network, ROOT, plan["free_space_reserve_gib"])
    # Read the local bbox from the complete VPU network, not a generalized map.
    native_crs = pyogrio.read_info(network)["crs"]
    bounds = gpd.GeoSeries([box(5.4, 50.6, 6.4, 51.5)], crs=4326).to_crs(native_crs)
    streams = gpd.read_file(network, bbox=tuple(bounds.total_bounds)).to_crs(32631)
    if streams.empty:
        raise ValueError("Regional network query is empty; check bbox coordinate reference")
    write_json(
        raw / "hydrography_schema.json",
        dict(columns=list(streams.columns), crs=str(streams.crs), rows=len(streams)),
    )
    print("Network columns:", list(streams.columns), flush=True)
    # TDX-Hydro US/DSContArea are m2 at the two segment ends. Model discharge
    # is compared at the downstream end; do not use the upstream-end area.
    id_field = next(c for c in ["LINKNO", "river_id", "COMID", "comid"] if c in streams)
    area_field = next(c for c in ["DSContArea", "upstreamarea"] if c in streams)
    area_factor = 1e-6
    candidates = []
    for site in plan["sites"]:
        point = (
            gpd.GeoSeries([Point(site["longitude"], site["latitude"])], crs=4326)
            .to_crs(32631)
            .iloc[0]
        )
        distances = streams.geometry.distance(point)
        for rank, idx in enumerate(distances.nsmallest(5).index):
            row = streams.loc[idx]
            area = float(row[area_field]) * area_factor
            reference = site["reference_area_km2"]
            candidates.append(
                dict(
                    channel=site["channel"],
                    gauge=site["gauge"],
                    station=site["station"],
                    river=site["river"],
                    rank_distance=rank + 1,
                    river_id=int(row[id_field]),
                    distance_m=float(distances.loc[idx]),
                    model_area_km2=area,
                    model_upstream_end_area_km2=float(row["USContArea"]) / 1e6,
                    reference_area_km2=reference,
                    area_ratio=area / reference if reference else None,
                    dslinkno=int(row["DSLINKNO"]) if "DSLINKNO" in row else None,
                    original_attributes={k: str(v) for k, v in row.items() if k != "geometry"},
                )
            )
    write_json(raw / "reach_candidates.json", candidates)
    pd.DataFrame(
        [{k: v for k, v in r.items() if k != "original_attributes"} for r in candidates]
    ).to_csv(raw / "reach_candidates.csv", index=False)
    print(
        "Wrote reach candidates; select with topology/area evidence in the tracked reach register."
    )


def retrieve(plan):
    import importlib.metadata

    import s3fs
    import xarray as xr

    mapping = json.loads((ROOT / "config/limburg_geoglows_reaches_v1.json").read_text())
    if len(mapping) != 10 or any(
        r["status"] not in ["reviewed", "reviewed_unmapped"] for r in mapping
    ):
        raise ValueError("All ten source mappings require documented review; no observed fallback")
    raw = ROOT / plan["raw"]
    raw.mkdir(parents=True, exist_ok=True)
    record_path = raw / "download_manifest.json"
    if record_path.exists():
        old = json.loads(record_path.read_text())
        if old["config_sha256"] != sha(CONFIG) or old["mapping_sha256"] != sha(
            ROOT / "config/limburg_geoglows_reaches_v1.json"
        ):
            raise ValueError("Download identity changed; version instead of overwriting")
        if any(sha(raw / p) != h for p, h in old["outputs"].items()):
            raise ValueError("Downloaded series changed")
        print("Verified existing selected-series download")
        return
    disk_check(ROOT, plan["free_space_reserve_gib"], 512 * 2**20)
    fs = s3fs.S3FileSystem(
        anon=True, client_kwargs={"region_name": "us-west-2"}, default_fill_cache=False
    )
    prefix = plan["geoglows"]["uri"].removeprefix("s3://")
    source_metadata = fs.cat(prefix + "/.zmetadata")
    snapshot = raw / "hourly-zarr-metadata.json"
    if snapshot.exists() and snapshot.read_bytes() != source_metadata:
        raise ValueError("Remote archive changed during retrieval; retain snapshot and version")
    snapshot.write_bytes(source_metadata)
    ds = xr.open_zarr(fs.get_mapper(prefix), consolidated=True, chunks=None)
    if ds["Q"].attrs.get("units") not in ["m3 s-1", "m3/s"]:
        raise ValueError("Unexpected discharge units; inspect before conversion")
    if ds["Q"].attrs.get("aggregation_method") != "mean":
        raise ValueError("Expected hourly mean discharge, not instantaneous values")
    meta = pd.read_parquet(ROOT / plan["source"] / "storms.parquet")
    start = (meta.cutoff_utc.min() - pd.Timedelta(hours=72)).tz_localize(None)
    end = (meta.cutoff_utc.max() + pd.Timedelta(hours=24)).tz_localize(None)
    # Download continuously from the start of the held observed axis, also for
    # prior-only calibration; select BEFORE materializing the global array.
    observed_axis = pd.read_parquet(ROOT / "results/storm_response/hourly_discharge.parquet").index
    start = min(start, observed_axis.min().tz_localize(None) - pd.Timedelta(hours=1))
    end = max(end, observed_axis.max().tz_localize(None))
    pieces = []
    for site in mapping:
        if not site["mapped"]:
            print("No independent model reach:", site["gauge"], "(retained as missing)", flush=True)
            continue
        path = raw / f"q_{site['channel']:02d}_{site['river_id']}.parquet"
        receipt = path.with_suffix(".json")
        if path.exists():
            if not receipt.exists() or json.loads(receipt.read_text())["sha256"] != sha(path):
                raise ValueError("Unverified partial download")
            piece = pd.read_parquet(path)
        else:
            disk_check(ROOT, plan["free_space_reserve_gib"], 256 * 2**20)
            selected = ds["Q"].sel(river_id=site["river_id"], time=slice(start, end))
            series = hour_end(selected.to_series())
            # A scalar river coordinate must not survive as an extra index level.
            if not isinstance(series.index, pd.DatetimeIndex):
                raise ValueError("Unexpected retrospective series dimensions")
            piece = series.rename(str(site["channel"])).to_frame()
            temp = path.with_suffix(".partial")
            piece.to_parquet(temp)
            temp.replace(path)
            write_json(
                receipt,
                dict(
                    sha256=sha(path),
                    river_id=site["river_id"],
                    first=str(piece.index.min()),
                    last=str(piece.index.max()),
                    hourly_values=len(piece),
                    finite_values=int(piece.iloc[:, 0].notna().sum()),
                    attrs=dict(ds["Q"].attrs),
                    timestamp_shift_hours=1,
                ),
            )
        pieces.append(piece)
        print("Retrieved", site["gauge"], "reach", site["river_id"], flush=True)
    hourly = pd.concat(pieces, axis=1).sort_index()
    hourly = hourly.reindex(columns=[str(i) for i in range(10)])
    hourly.to_parquet(raw / "hourly_discharge.parquet")
    write_json(
        record_path,
        dict(
            status="completed",
            acquired_utc=datetime.now(timezone.utc).isoformat(),
            config_sha256=sha(CONFIG),
            mapping_sha256=sha(ROOT / "config/limburg_geoglows_reaches_v1.json"),
            uri=plan["geoglows"]["uri"],
            variable_attrs=dict(ds["Q"].attrs),
            dataset_attrs=dict(ds.attrs),
            metadata_sha256=sha(snapshot),
            packages={
                n: importlib.metadata.version(n) for n in ["xarray", "zarr", "s3fs", "numpy"]
            },
            outputs={
                p.name: sha(p)
                for p in [
                    snapshot,
                    raw / "hourly_discharge.parquet",
                    *sorted(raw.glob("q_*.parquet")),
                ]
            },
            simulation_clock="hour end UTC; retrospective release lag NOT replayed",
        ),
    )


def audit_mapping(plan):
    """Check full contributing polygons, independently of nearest-stream rank."""
    from collections import defaultdict

    import geopandas as gpd
    from shapely.ops import unary_union

    raw = ROOT / plan["raw"]
    polygons = raw / "catchments_209.parquet"
    download(plan["geoglows"]["catchments_uri"], polygons, ROOT, plan["free_space_reserve_gib"])
    streams = gpd.read_file(raw / "streams_209.gpkg")
    catchments = gpd.read_parquet(polygons).to_crs(3035)
    reference_path = ROOT / "results/eo_comparison_preparation/catchments.gpkg"
    reference = gpd.read_file(reference_path).to_crs(3035).set_index("gauge")
    mapping_path = ROOT / "config/limburg_geoglows_reaches_v1.json"
    mapping = json.loads(mapping_path.read_text())
    upstream = defaultdict(list)
    for row in streams[["LINKNO", "DSLINKNO"]].itertuples():
        upstream[int(row.DSLINKNO)].append(int(row.LINKNO))
    records = []
    for site, selected in zip(plan["sites"], mapping, strict=True):
        link = selected["river_id"] if selected["mapped"] else selected["rejected_nearest_id"]
        seen, queue = set(), [link]
        while queue:
            node = queue.pop()
            if node in seen:
                continue
            seen.add(node)
            queue.extend(upstream[node])
        geom = unary_union(catchments.loc[catchments.LINKNO.isin(seen), "geometry"])
        record = dict(
            gauge=site["gauge"],
            tested_river_id=link,
            mapped=selected["mapped"],
            polygon_area_km2=geom.area / 1e6,
        )
        if site["catchment_gauge"] in reference.index:
            held = reference.loc[site["catchment_gauge"]].geometry
            record.update(
                held_area_covered_fraction=geom.intersection(held).area / held.area,
                model_area_within_held_fraction=geom.intersection(held).area / geom.area,
            )
            if not np.isclose(
                record["held_area_covered_fraction"],
                selected["held_area_covered_fraction"],
                atol=1e-9,
            ):
                raise ValueError("Mapping overlap differs from reviewed register")
        records.append(record)
    write_json(
        raw / "mapping_audit.json",
        dict(
            status="completed",
            checks=records,
            source_hashes={
                str(p.relative_to(ROOT)): sha(p)
                for p in [mapping_path, raw / "streams_209.gpkg", polygons, reference_path]
            },
            note="Eys nearest reach rejected, not substituted. Model areas refer to reach outlets.",
        ),
    )
    print("Verified selected reaches and Eys's rejected nearest reach against polygons")


def readiness(plan):
    out = ROOT / plan["output"]
    checks = {}
    for model in plan["models"]:
        d = ROOT / "results/limburg_individual_experiments_v1/features" / model
        m = json.loads((d / "manifest.json").read_text())
        checks[model] = (
            m["status"] == "completed"
            and sha(d / "context_features.parquet") == m["outputs"]["context_features.parquet"]
        )
    raw = ROOT / plan["raw"]
    checks["downloaded"] = (raw / "download_manifest.json").exists()
    checks["mapping_audited"] = (raw / "mapping_audit.json").exists()
    checks["prepared"] = (out / "preparation/manifest.json").exists()
    checks["full_input_audit"] = (out / "setup_audit.json").exists()
    if checks["downloaded"]:
        receipt = json.loads((raw / "download_manifest.json").read_text())
        checks["downloaded"] = all(
            sha(raw / p) == digest for p, digest in receipt["outputs"].items()
        )
    if checks["prepared"]:
        import runpy

        runner = runpy.run_path(str(ROOT / "scripts/261_run_geoglows_comparison.py"))
        runner["verify_receipt"](out / "preparation/manifest.json")
    if checks["mapping_audited"]:
        mapping_audit = json.loads((raw / "mapping_audit.json").read_text())
        checks["mapping_audited"] = all(
            sha(ROOT / p) == digest for p, digest in mapping_audit["source_hashes"].items()
        )
    if checks["full_input_audit"]:
        audit = json.loads((out / "setup_audit.json").read_text())
        checks["full_input_audit"] = audit["status"] == "passed" and audit[
            "preparation_sha256"
        ] == sha(out / "preparation/manifest.json")
    free = disk_check(ROOT, plan["free_space_reserve_gib"])
    record = dict(
        status="ready_for_run" if all(checks.values()) else "setup_incomplete",
        checks=checks,
        disk_free_gib=free,
        full_analysis_launched=False,
        config_sha256=sha(CONFIG),
    )
    write_json(out / "readiness.json", record)
    print(json.dumps(record, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "phase",
        choices=[
            "inventory",
            "mapping-audit",
            "download",
            "prepare",
            "audit",
            "readiness",
            "run",
            "review",
        ],
    )
    args = parser.parse_args()
    plan = json.loads(CONFIG.read_text())
    disk_check(ROOT, plan["free_space_reserve_gib"])
    started = time.monotonic()
    if args.phase == "inventory":
        inventory(plan)
    elif args.phase == "mapping-audit":
        audit_mapping(plan)
    elif args.phase == "download":
        retrieve(plan)
    elif args.phase == "readiness":
        readiness(plan)
    else:
        subprocess.run(
            [sys.executable, str(ROOT / "scripts/261_run_geoglows_comparison.py"), args.phase],
            cwd=ROOT,
            check=True,
        )
    print("Phase elapsed seconds:", round(time.monotonic() - started, 1))


if __name__ == "__main__":
    main()
