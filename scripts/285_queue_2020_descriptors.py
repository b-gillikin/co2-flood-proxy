"""Validate completed TESSERA extraction, acquire matched AlphaEarth, and audit both."""

import fcntl
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

os.environ.setdefault("PROJ_DATA", str(Path(sys.base_prefix) / "share/proj"))

import ee  # noqa: E402
import geopandas as gpd  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "results/limburg_representation_extension_v1"
SCRIPTS = ROOT / "scripts"
TESSERA = BASE / "tessera_census_2020"
OUT = BASE / "alphaearth_2020"


def main():
    OUT.mkdir(exist_ok=True)
    with (OUT / "queue.lock").open("a") as queue, (TESSERA / "worker.lock").open("a") as extraction:
        fcntl.flock(queue, fcntl.LOCK_EX | fcntl.LOCK_NB)
        print("Waiting for TESSERA extraction", flush=True)
        fcntl.flock(extraction, fcntl.LOCK_EX)
        subprocess.run(
            [
                ROOT / ".venv-tessera/bin/python",
                SCRIPTS / "284_validate_tessera_descriptors.py",
                "--year",
                "2020",
            ],
            check=True,
        )

        print("Acquiring 2020 AlphaEarth", flush=True)
        spec = importlib.util.spec_from_file_location(
            "regional_inputs", SCRIPTS / "267_acquire_dise_regional_inputs.py"
        )
        regional = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(regional)
        geometry = BASE / "catchments.gpkg"
        inventory = BASE / "catchment_inventory.csv"
        mapping = pd.read_csv(inventory, dtype={"gauge": str}).rename(columns={"gauge": "gauge_id"})
        mapping = mapping.sort_values("gauge_id")
        geometries = gpd.read_file(geometry).set_index("gauge").to_crs(4326).geometry
        if (
            len(mapping) != 394
            or not mapping.gauge_id.is_unique
            or set(mapping.gauge_id) != set(geometries.index)
        ):
            raise ValueError("AlphaEarth geometry and inventory differ from the intended census")
        regional.OUT = OUT
        regional.RAW = OUT
        regional.PLAN.update(alphaearth_year=2020, mapping=str(inventory), catchments=str(geometry))
        ee.Initialize(project=regional.PLAN["earth_engine_project"])
        regional.acquire_spatial(ee, mapping, geometries, kinds=("alphaearth",))

        print("Auditing 2020 descriptors", flush=True)
        subprocess.run(
            [
                "ruff",
                "check",
                SCRIPTS / "267_acquire_dise_regional_inputs.py",
                SCRIPTS / "282_pilot_tessera.py",
                SCRIPTS / "283_extract_tessera_census.py",
                SCRIPTS / "284_validate_tessera_descriptors.py",
                Path(__file__),
            ],
            check=True,
        )
        batches = sorted((OUT / "alphaearth").glob("*.parquet"))
        expected_batches = (
            len(mapping) + regional.PLAN["alphaearth_batch_size"] - 1
        ) // regional.PLAN["alphaearth_batch_size"]
        if len(batches) != expected_batches:
            raise ValueError("Unexpected AlphaEarth batch count")
        alpha = pd.concat([pd.read_parquet(path) for path in batches], ignore_index=True)
        tessera = pd.read_csv(TESSERA / "descriptors_2020.csv", dtype={"gauge": str})
        tessera_receipt = json.loads((TESSERA / "receipt_2020_direct.json").read_text())
        geometry_hash = regional.sha(geometry)
        if tessera_receipt["geometry_sha256"] != geometry_hash:
            raise ValueError("TESSERA and AlphaEarth did not use the same geometry file")
        expected = set(mapping.gauge_id)
        for frame in (alpha, tessera):
            if not frame.gauge.is_unique or set(frame.gauge) != expected:
                raise ValueError("Descriptor census mismatch")
        hashes = geometries.map(lambda geom: hashlib.sha256(geom.wkb).hexdigest())
        if not alpha.geometry_sha256.eq(alpha.gauge.map(hashes)).all():
            raise ValueError("AlphaEarth per-catchment geometry differs")
        if not alpha.embedding_year.eq(2020).all():
            raise ValueError("Unexpected AlphaEarth year")

        summary = {}
        for name, frame, bands in (
            ("alphaearth", alpha, regional.BANDS),
            ("tessera", tessera, [f"tessera_{i:03d}" for i in range(128)]),
        ):
            vectors = frame[bands].to_numpy(dtype=float)
            norms = np.linalg.norm(vectors, axis=1)
            if not np.isfinite(vectors).all() or not frame.valid_pixel_count.gt(0).all():
                raise ValueError(f"{name} contains missing features or invalid support")
            if np.any(norms == 0):
                raise ValueError(f"{name} contains zero vectors")
            repeats = frame.loc[frame.duplicated(bands, keep=False), ["gauge", *bands]].copy()
            repeats["geometry"] = repeats.gauge.map(hashes)
            shared = []
            for _, group in repeats.groupby(bands, sort=False):
                if group.geometry.nunique() != 1:
                    raise ValueError(f"{name} has identical vectors for distinct geometries")
                shared.append(sorted(group.gauge.tolist()))
            if name == "alphaearth" and norms.max() > 1.01:
                raise ValueError("AlphaEarth mean norm exceeds the expected unit-vector bound")
            summary[name] = {
                "rows": len(frame),
                "dimensions": len(bands),
                "identical_vectors_on_shared_geometry": shared,
                "norm_quantiles": np.quantile(norms, [0, 0.05, 0.5, 0.95, 1]).tolist(),
                "valid_pixel_count_quantiles": frame.valid_pixel_count.quantile(
                    [0, 0.05, 0.5, 0.95, 1]
                ).tolist(),
            }
        summary["tessera"]["min_coverage"] = float(tessera.coverage_fraction.min())
        area = mapping.set_index("gauge_id").geometry_area_km2
        support = alpha.valid_pixel_count * 100 / (alpha.gauge.map(area) * 1e6)
        summary["alphaearth"]["approximate_area_support_quantiles"] = support.quantile(
            [0, 0.05, 0.5, 0.95, 1]
        ).tolist()
        summary["alphaearth"]["below_95pct_approximate_support"] = alpha.loc[
            support.lt(0.95), "gauge"
        ].tolist()
        regional.save(
            alpha,
            OUT / "descriptors_2020.parquet",
            regional.identity("combined_alphaearth_2020"),
            source_hashes={str(path.relative_to(ROOT)): regional.sha(path) for path in batches},
        )
        regional.write_json(
            OUT / "quality_2020.json",
            {
                "status": "complete",
                "year": 2020,
                "geometry_sha256": geometry_hash,
                "tessera_csv_sha256": regional.sha(TESSERA / "descriptors_2020.csv"),
                "alphaearth_parquet_sha256": regional.sha(OUT / "descriptors_2020.parquet"),
                "summary": summary,
            },
        )
        print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
