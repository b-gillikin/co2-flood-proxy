"""Rasterize CEMS assessed domains and mapped flood proxies on held tile grids.

Uses post-image footprint minus source-specific Not Analysed, intersect AOI.
Excludes mapped hydrography and trace-only inundation from instantaneous-water
comparisons. Does not assert that mapped non-flood is independently observed dry.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault(
    "PROJ_DATA", str((ROOT / ".venv-foundation/bin/python").resolve().parents[1] / "share/proj")
)
import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import rasterize
from shapely.ops import unary_union

from applied_local_reference import reference_labels

BASE = ROOT / "data/raw/limburg_applied_tasks/local_references"
SCENES = ROOT / "data/raw/limburg_applied_tasks/local_scenes"
OUT = ROOT / "results/applied_study_v1/local_references/scoring"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    inventory = pd.read_parquet(OUT.parent / "local-scene-pixel-inventory.parquet")
    source_tables = json.loads((OUT.parent / "selected-source-tables.json").read_text())
    report, inputs = [], {}
    for aoi, rows in inventory.groupby("aoi"):
        (archive,) = BASE.glob(aoi + "*zip")
        inputs[str(archive.relative_to(ROOT))] = hashlib.sha256(archive.read_bytes()).hexdigest()
        (table,) = [t for t in source_tables if t["archive"] == archive.name]
        postids = {r["src_id"] for r in table["rows"] if r["eventphase"] == "Post-event"}
        layers = {}
        with zipfile.ZipFile(archive) as z:
            for name in z.namelist():
                if name.endswith(".shp"):
                    key = name.split("_PRODUCT_")[1].split("_r1_")[0]
                    layers[key] = gpd.read_file(f"/vsizip/{archive}/{name}").to_crs(32631)
        footprints = layers["imageFootprintA"]
        post = footprints[footprints.or_src_id.isin(postids)]
        assessed = unary_union(post.loc[post.obj_type == "Image Footprint", "geometry"])
        if assessed.is_empty:
            raise ValueError("No known post-event assessed footprint: " + aoi)
        excluded = unary_union(
            post.loc[post.obj_type.str.contains("Not Analysed", case=False), "geometry"]
        )
        assessed = assessed.intersection(
            unary_union(layers["areaOfInterestA"].geometry)
        ).difference(excluded)
        events = layers["observedEventA"]
        flood = events[events.event_type == "5-Flood"]
        wet = unary_union(flood.loc[flood.notation == "Flooded area", "geometry"])
        trace = unary_union(flood.loc[flood.notation == "Flood trace", "geometry"])
        hydro = unary_union(layers["hydrographyA"].geometry)
        streams = unary_union(layers["hydrographyL"].geometry)
        grids = {}
        for row in rows.itertuples():
            path = SCENES / row.path
            with rasterio.open(path) as ds:
                key = Path(row.path).name
                signature = (ds.width, ds.height, tuple(ds.transform), str(ds.crs))
                if key in grids:
                    if grids[key] != signature:
                        raise ValueError("Grid filename reused for different spatial support")
                    continue
                grids[key] = signature

                def burn(geom, touched=False):
                    if geom.is_empty:
                        return np.zeros(ds.shape, dtype=bool)
                    return rasterize(
                        [(geom, 1)],
                        out_shape=ds.shape,
                        transform=ds.transform,
                        all_touched=touched,
                        dtype="uint8",
                    ).astype(bool)

                masks = [burn(assessed), burn(wet), burn(trace), burn(hydro), burn(streams, True)]
                label = reference_labels(*masks)
                profile = ds.profile.copy()
                profile.update(count=1, dtype="uint8", nodata=255, compress="deflate")
                destination = OUT / aoi / key
                destination.parent.mkdir(exist_ok=True)
                with rasterio.open(destination, "w", **profile) as target:
                    target.write(label, 1)
                    target.update_tags(
                        target="mapped flood proxy excluding hydrography and trace-only polygons",
                        outside_flood="mapped non-flood, not confirmed dry",
                        source=archive.name,
                    )
                report.append(
                    dict(
                        aoi=aoi,
                        grid=key,
                        path=str(destination.relative_to(ROOT)),
                        assessed_pixels=int(masks[0].sum()),
                        trace_pixels=int(masks[2].sum()),
                        eligible_pixels=int((label != 255).sum()),
                        mapped_flood_pixels=int((label == 1).sum()),
                        sha256=hashlib.sha256(destination.read_bytes()).hexdigest(),
                    )
                )
    scene_rows = inventory.to_dict("records")
    for row in scene_rows:
        row["comparison_role"] = (
            "conditioning_only_not_postevent_reference_scoring"
            if row["sensor"] == "s1_pre"
            else "qualified_acquisition_case_comparison"
        )
        row["reference_path"] = str((OUT / row["aoi"] / Path(row["path"]).name).relative_to(ROOT))
        row["reference_dependence"] = (
            "shared radar source"
            if row["aoi"] == "EMSR520_AOI01" and row["sensor"].startswith("s1")
            else "different sensor or acquisition; not field truth"
        )
    pd.DataFrame(scene_rows).to_parquet(OUT / "scene-reference-pairs.parquet", index=False)
    inputs["scripts/194_prepare_local_reference_scoring.py"] = hashlib.sha256(
        Path(__file__).read_bytes()
    ).hexdigest()
    inputs["src/applied_local_reference.py"] = hashlib.sha256(
        (ROOT / "src/applied_local_reference.py").read_bytes()
    ).hexdigest()
    (OUT / "reference-inventory.json").write_text(
        json.dumps(
            dict(
                grids=report,
                input_hashes=inputs,
                convention="pixel-center polygons; all-touched stream exclusion; unknown=255",
                unit="AOI/acquisition, not chips or countries; do not pool multiple dates into one confusion matrix",
                temporal_rule="retain actual signed time offsets; closest acquisition is a case comparison, not simultaneity",
                warning="DE Flood trace polygons describe prior inundation; excluded from instantaneous water target",
            ),
            indent=2,
        )
    )
    print(
        json.dumps(
            dict(
                grids=len(report),
                scene_pairs=len(scene_rows),
                eligible_pixels=sum(r["eligible_pixels"] for r in report),
                mapped_flood_pixels=sum(r["mapped_flood_pixels"] for r in report),
            )
        )
    )


if __name__ == "__main__":
    main()
