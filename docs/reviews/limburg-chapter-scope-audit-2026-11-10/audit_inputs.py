"""Read-only census/receipt audit for the accepted mapping study; no model fitting.

Run with .venvs-eo/legacy/bin/python from the chapter root. Outputs go beside
this research-aid script. Target data remain catalogue-only until acquisition.
"""

import hashlib
import json
import math
import re
import shutil
import statistics
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import rasterio
from pyproj import Transformer
from rasterio.warp import transform_bounds
from shapely import from_wkb, union_all
from shapely.geometry import box
from shapely.ops import transform

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
GIB = 1024**3


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def acquisition(products):
    return [pd.Timestamp(re.search(r"_(\d{8}T\d{6})_", p).group(1)) for p in products]


def source_bounds(row):
    folder = (
        ROOT / "data/raw/limburg_applied_tasks/flood_s1/extracted/flood_s1/data" / row.source_path
    )
    (path,) = folder.glob("MS1_IVV*.tif")
    with rasterio.open(path) as ds:
        bounds = transform_bounds(ds.crs, "EPSG:4326", *ds.bounds, densify_pts=21)
        return dict(
            record=row.record,
            event=row.event,
            crs=str(ds.crs),
            width=ds.width,
            height=ds.height,
            res_x=ds.res[0],
            res_y=ds.res[1],
            minlon=bounds[0],
            minlat=bounds[1],
            maxlon=bounds[2],
            maxlat=bounds[3],
        )


def main():
    paths = {
        "source_inventory": ROOT
        / "results/applied_study_v5/evaluation/radar-change-inventory.parquet",
        "external_catalogue": ROOT
        / "results/three-capability-execution-planning-2026-11-10/geoid_heldout_catalog.parquet",
        "progress": ROOT / "results/applied_study_v5/ready-v2/progress.json",
        "feature_cache": ROOT / "data/processed/limburg_copernicus_spatial_v1/index.json",
        "core_manifest": ROOT / "config/limburg_chapter_sized_geoid_acquisition_v1.json",
        "adapter": ROOT / "src/applied_copernicus.py",
        "physical": ROOT / "src/applied_physical.py",
        "local_inference": ROOT / "scripts/215_apply_local_spatial_models.py",
    }
    source = pd.read_parquet(paths["source_inventory"])
    target = pd.read_parquet(paths["external_catalogue"])
    with ThreadPoolExecutor(max_workers=2) as pool:
        bounds = list(pool.map(source_bounds, source.itertuples()))
    pd.DataFrame(bounds).to_csv(OUT / "source-bounds.csv", index=False)
    source_union = union_all(
        [box(x["minlon"], x["minlat"], x["maxlon"], x["maxlat"]) for x in bounds]
    )
    external = []
    for row in target.itertuples():
        geometry = from_wkb(row.geometry)
        # Catalogue WKB uses lon/lat, while utm_crs names each RASTER grid.
        # The Parquet has no geo CRS metadata: validate this convention against
        # all reprojected 10,240m square footprints, not the first row alone.
        assert -180 <= geometry.bounds[0] < geometry.bounds[2] <= 180
        assert -90 <= geometry.bounds[1] < geometry.bounds[3] <= 90
        convert = Transformer.from_crs("EPSG:4326", row.utm_crs, always_xy=True).transform
        projected = transform(convert, geometry)
        assert abs(projected.area / (10240**2) - 1) < 0.01, "Catalogue CRS/footprint mismatch"
        geographic = geometry
        pre, post = acquisition(row.s1_pre_products), acquisition(row.s1_post_products)
        external.append(
            dict(
                event=row.event_id,
                tile=row.tile_id,
                bbox_id=row.bbox_id,
                country=row.countries,
                valid=bool(row.is_valid),
                invalid_pixel_frac=float(row.invalid_pixel_frac),
                event_time=row.event_time,
                pre_time=min(pre).isoformat(),
                post_time=max(post).isoformat(),
                pre_post_days=(max(post) - min(pre)).total_seconds() / 86400,
                pre_before_catalogue_event=bool(max(pre) < pd.Timestamp(row.event_time)),
                post_label_offset_days=(
                    max(post) - pd.Timestamp(row.delineation_time_post)
                ).total_seconds()
                / 86400,
                source_bbox_intersection=bool(source_union.intersects(geographic)),
                pre_platform=",".join(sorted({p[:3] for p in row.s1_pre_products})),
                post_platform=",".join(sorted({p[:3] for p in row.s1_post_products})),
            )
        )
    ext = pd.DataFrame(external)
    ext.to_csv(OUT / "external-metadata.csv", index=False)
    # Record original catalogue bounds to make the validated CRS convention visible.
    geometric_bounds = [list(from_wkb(x).bounds) for x in target.geometry]
    progress = json.loads(paths["progress"].read_text())
    jobs = []
    for key, value in progress["jobs"].items():
        if (
            not key.startswith(("copernicus-native-", "copernicus-unet_standard-"))
            or "-1-" not in key
        ):
            continue
        folder = ROOT / value["output"]
        selected = json.loads((folder / "selection.json").read_text())
        trials = json.loads((folder / "trials.json").read_text())
        receipt = json.loads((ROOT / value["recovery_receipt"]).read_text())
        jobs.append(
            dict(
                job=key,
                learner="native" if key.startswith("copernicus-native-") else "unet_standard",
                status=value["status"],
                selected_seconds=selected["elapsed_s"],
                best_epoch=selected["epoch"],
                boundary=bool(selected.get("learning_rate_grid_boundary")),
                candidate_count=len(trials),
                candidate_seconds=sum(x.get("elapsed_s", 0) for x in trials),
                training_population="source_crossfit_subset_not_all5000",
                checkpoint_local=False if value.get("retired_checkpoints") else None,
                recovery_receipt=value["recovery_receipt"],
                recovery_status=receipt.get("status"),
            )
        )
    pd.DataFrame(jobs).to_csv(OUT / "existing-source-fits.csv", index=False)
    cache = json.loads(paths["feature_cache"].read_text())
    fits = {}
    for name in ["native", "unet_standard"]:
        rows = [j for j in jobs if j["learner"] == name]
        fits[name] = dict(
            completed=len(rows),
            candidate_fits=sum(j["candidate_count"] for j in rows),
            selected_fit_median_minutes=statistics.median(j["selected_seconds"] for j in rows) / 60,
            selected_hours=sum(j["selected_seconds"] for j in rows) / 3600,
            candidate_hours=sum(j["candidate_seconds"] for j in rows) / 3600,
            rate_boundaries=sum(j["boundary"] for j in rows),
            best_epochs=[j["best_epoch"] for j in rows],
        )
    events = []
    for event, rows in ext.groupby("event"):
        events.append(
            dict(
                event=event,
                tiles=len(rows),
                countries=rows.country.iloc[0],
                pre_post_gap_min_days=float(rows.pre_post_days.min()),
                pre_post_gap_max_days=float(rows.pre_post_days.max()),
                label_sar_offset_max_abs_days=float(rows.post_label_offset_days.abs().max()),
                bbox_intersections=int(rows.source_bbox_intersection.sum()),
            )
        )
    n = len(target)
    windows = math.ceil(1024 / 224) ** 2
    payload = 4 * 768 * 14 * 14 * 4
    manifest = json.loads(paths["core_manifest"].read_text())
    summary = dict(
        date="2026-11-10",
        kind="metadata_and_existing_receipts_not_new_accuracy",
        source=dict(
            records=len(source),
            events=int(source.event.nunique()),
            post_min=source.post_date.min(),
            post_max=source.post_date.max(),
            no_water=int(((source.class1_pixels + source.class2_pixels) == 0).sum()),
            no_flood=int((source.class2_pixels == 0).sum()),
            native_grids=int(
                ((pd.DataFrame(bounds).width == 224) & (pd.DataFrame(bounds).height == 224)).sum()
            ),
        ),
        external=dict(
            tiles=n,
            event_ids=int(target.event_id.nunique()),
            catalogue_valid=int(target.is_valid.sum()),
            geometry_first_bounds=geometric_bounds[0],
            source_bbox_intersections=int(ext.source_bbox_intersection.sum()),
            geographic_check="WGS84 source bounding boxes versus WGS84 external footprints; all external polygons validated against10240m event-UTM squares; not river/region-wide independence",
            pre_not_before_catalogue_event=int((~ext.pre_before_catalogue_event).sum()),
            post_label_offsets_over_one_day=int((ext.post_label_offset_days.abs() > 1).sum()),
            post_platforms=ext.post_platform.value_counts().to_dict(),
            events=events,
        ),
        source_fits=fits,
        feature_cache={
            k: cache[k]
            for k in [
                "status",
                "completed",
                "bytes",
                "elapsed_s",
                "feature_seconds",
                "device",
                "threads",
                "shape",
            ]
        },
        storage=dict(
            free_gib=shutil.disk_usage(ROOT).free / GIB,
            reserve_gib=50,
            core_package_gib=manifest["selected_bytes"] / GIB,
            P0_uncompressed_four_float32_channels_gib=n * 1024 * 1024 * 4 * 4 / GIB,
            P1_uncompressed_two_float32_channels_gib=n * 1024 * 1024 * 2 * 4 / GIB,
            all_three_dates_feature_payload_gib=n * windows * 3 * payload / GIB,
            two_pair_difference_feature_payload_gib=n * windows * 2 * payload / GIB,
            learned_per_seed_full_probabilities_gib=n * 1024 * 1024 * 3 * 4 * 12 / GIB,
            learned_seed_mean_full_probabilities_gib=n * 1024 * 1024 * 3 * 4 * 4 / GIB,
            all14_argmax_maps_gib=n * 1024 * 1024 * 14 / GIB,
            assumptions="float32 uncompressed array payload; 25 padded224px windows/tile; 3 source seeds; all1301 tiles have a distinct P1; actual compression/support differs",
        ),
        inference=dict(
            illustrative_windows_per_tile=windows,
            unique_date_encoder_views=n * windows * 3,
            learned_head_or_unet_window_forwards=n * windows * 12,
            pure_encoder_hours_linear_extrapolation=(cache["elapsed_s"] / (2 * cache["completed"]))
            * (n * windows * 3)
            / 3600,
            limit="arithmetic from existing complete-pair cache receipt, not new workload profile; no I/O, full head inference, masking/stitching or archiving included",
        ),
        inputs_sha256={str(v.relative_to(ROOT)): sha(v) for v in paths.values()},
        new_fit=False,
        new_bulk_download=False,
    )
    (OUT / "metadata-and-compute.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n"
    )
    print(
        json.dumps(
            {k: v for k, v in summary.items() if k not in ["inputs_sha256", "feature_cache"]},
            indent=2,
            default=str,
        )
    )


if __name__ == "__main__":
    main()
