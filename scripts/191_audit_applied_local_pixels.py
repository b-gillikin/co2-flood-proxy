"""Measure actual local scene coverage and cloud flags on every acquired tile."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/raw/limburg_applied_tasks/local_scenes"
OUT = ROOT / "results/applied_study_v1/local_references"


def main():
    acquired = json.loads((OUT / "local-scene-progress.json").read_text())
    if acquired["status"] != "completed" or acquired["failures"]:
        raise ValueError("Complete acquisitions before the coverage census")
    manifest = json.loads((OUT / "local-scene-jobs.json").read_text())
    inventory = json.loads((OUT / "local-scene-inventory.json").read_text())
    dates = {a["aoi"]: pd.Timestamp(a["reference_time"]) for a in inventory["aois"]}
    rows = []
    for job in manifest["jobs"]:
        path = BASE / job["path"]
        with rasterio.open(path) as ds:
            x = ds.read()
            if ds.count != len(job["bands"]) or ds.shape != (512, 512):
                raise ValueError("Grid/band mismatch")
            valid = (x[-1] == 1) & np.isfinite(x[:-1]).all(0)
            if job["sensor"].startswith("s2"):
                valid &= (x[:13] != -9999).all(0)
                qa = x[13]
                known = valid & np.isfinite(qa) & (qa != -9999)
                flags = np.where(known, qa, 0).astype(np.int64)
                cloud = known & (((flags & (1 << 10)) != 0) | ((flags & (1 << 11)) != 0))
                qa_known = int(known.sum())
                clear = int((known & ~cloud).sum())
                cloudy = int(cloud.sum())
            else:
                valid &= (x[:3] != -9999).all(0)
                qa_known = clear = cloudy = None
            stamp = pd.Timestamp(job["scene"]["system:time_start"], unit="ms", tz="UTC")
            rows.append(
                dict(
                    path=job["path"],
                    aoi=job["aoi"],
                    sensor=job["sensor"],
                    scene=job["scene"]["scene_id"],
                    acquisition_utc=stamp.isoformat(),
                    reference_offset_hours=(stamp - dates[job["aoi"]]).total_seconds() / 3600,
                    valid_pixels=int(valid.sum()),
                    qa_known_pixels=qa_known,
                    qa_clear_pixels=clear,
                    qa_cloud_pixels=cloudy,
                    projected_observed_area_m2=int(valid.sum()) * 100,
                    relative_orbit=job["scene"].get("relativeOrbitNumber_start"),
                    orbit_pass=job["scene"].get("orbitProperties_pass"),
                    bytes=path.stat().st_size,
                )
            )
    frame = pd.DataFrame(rows)
    frame.to_parquet(OUT / "local-scene-pixel-inventory.parquet", index=False)
    summary = (
        frame.groupby(["aoi", "sensor", "scene"], dropna=False)
        .agg(
            tiles=("path", "size"),
            valid_pixels=("valid_pixels", "sum"),
            observed_area_m2=("projected_observed_area_m2", "sum"),
            qa_known_pixels=("qa_known_pixels", "sum"),
            qa_clear_pixels=("qa_clear_pixels", "sum"),
            qa_cloud_pixels=("qa_cloud_pixels", "sum"),
            reference_offset_hours=("reference_offset_hours", "first"),
        )
        .reset_index()
    )
    summary.to_parquet(OUT / "local-scene-coverage.parquet", index=False)
    (OUT / "local-scene-pixel-audit.json").write_text(
        json.dumps(
            dict(
                status="complete",
                tiles=len(frame),
                acquisitions=len(summary),
                bytes=int(frame.bytes.sum()),
                empty_tiles=int((frame.valid_pixels == 0).sum()),
                optical_quality="QA60 opaque cloud/cirrus bits only; no complete shadow/cloud guarantee",
                radar_units="VV/VH dB; angle degrees. Convert to linear intensity explicitly for Copernicus-FM change inputs",
                optical_units="13 TOA bands scaled x10000; nearest-resampled 10/20/60m native bands on a common 10m grid",
                area="valid-pixel count times projected 100m2; approximate edge support, not a flood area",
                reference="Time offsets and source dependence remain explicit; this audit does not establish flood-label accuracy",
            ),
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
