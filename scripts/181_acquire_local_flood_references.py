"""Retrieve public CEMS vector products and inspect their actual spatial support.

Uses the working public HTML links, not the API route that returned 403. AOI
overlap is a lead, never a declaration that a polygon is independent truth.
"""

from __future__ import annotations

import hashlib
import html
import json
import os
import re
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault(
    "PROJ_DATA", str((ROOT / ".venv-foundation/bin/python").resolve().parents[1] / "share/proj")
)

import geopandas as gpd
from shapely.geometry import shape

BASE = ROOT / "data/raw/limburg_applied_tasks/local_references"
OUT = ROOT / "results/applied_study_v1/local_references"


def acquire(url):
    path = BASE / url.rsplit("/", 1)[-1]
    if not path.exists():
        temp = path.with_suffix(".partial")
        with urllib.request.urlopen(url, timeout=120) as source, temp.open("wb") as dest:
            while block := source.read(1024**2):
                dest.write(block)
        temp.replace(path)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return dict(url=url, path=str(path.relative_to(ROOT)), bytes=path.stat().st_size, sha256=digest)


def main():
    BASE.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    urls = []
    for activation in ["EMSR517", "EMSR520"]:
        page = BASE / f"{activation}.html"
        if not page.exists():
            page.write_bytes(
                urllib.request.urlopen(
                    f"https://mapping.emergency.copernicus.eu/activations/{activation}/", timeout=60
                ).read()
            )
        urls += re.findall(r'href="(https://[^\"]+_vector\.zip)"', html.unescape(page.read_text()))
    receipts = []
    failures = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [(u, pool.submit(acquire, u)) for u in sorted(set(urls))]
        for url, future in futures:
            try:
                row = future.result()
                receipts.append(row)
                print(row["path"], row["bytes"], flush=True)
            except Exception as exc:
                failures.append(dict(url=url, error=f"{type(exc).__name__}: {exc}"))
    (OUT / "downloads.json").write_text(
        json.dumps(dict(files=receipts, failures=failures), indent=2) + "\n"
    )
    roi = json.loads((ROOT / "data/raw/limburg_compact_eo/roi.geojson").read_text())
    if roi["type"] == "Feature":
        roi = roi["geometry"]
    if roi["type"] == "FeatureCollection":
        from shapely.ops import unary_union

        region = unary_union([shape(f["geometry"]) for f in roi["features"]])
    else:
        region = shape(roi)
    layers = []
    for row in receipts:
        path = ROOT / row["path"]
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            for name in names:
                if name.endswith(".shp"):
                    try:
                        frame = gpd.read_file(f"/vsizip/{path}/{name}")
                        wgs = frame.to_crs(4326)
                        relevant = wgs.intersects(region)
                        fields = [c for c in frame.columns if c != "geometry"]
                        data = dict(
                            archive=path.name,
                            layer=name,
                            records=len(frame),
                            crs=str(frame.crs),
                            bounds=wgs.total_bounds.tolist() if len(wgs) else None,
                            records_intersecting_study_roi=int(relevant.sum()),
                            fields=fields,
                            sample_attributes=json.loads(
                                frame.drop(columns="geometry")
                                .head(3)
                                .to_json(orient="records", date_format="iso")
                            ),
                        )
                        layers.append(data)
                        if relevant.any():
                            dest = OUT / "overlap" / path.stem
                            dest.mkdir(parents=True, exist_ok=True)
                            wgs.loc[relevant].to_parquet(
                                dest / (Path(name).stem + ".parquet"), index=False
                            )
                    except Exception as exc:
                        layers.append(
                            dict(
                                archive=path.name, layer=name, error=f"{type(exc).__name__}: {exc}"
                            )
                        )
            text_members = [
                n
                for n in names
                if Path(n).suffix.lower() in [".xml", ".txt", ".csv", ".html", ".json"]
            ]
            for name in text_members:
                target = OUT / "source_metadata" / path.stem / Path(name).name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.read(name))
    (OUT / "layer-inventory.json").write_text(json.dumps(layers, indent=2, allow_nan=False) + "\n")
    (OUT / "summary.json").write_text(
        json.dumps(
            dict(
                status="inventoried",
                listed_vector_urls=len(set(urls)),
                downloaded=len(receipts),
                failures=failures,
                layers=len(layers),
                layer_errors=sum("error" in r for r in layers),
                overlapping_layers=sum(
                    r.get("records_intersecting_study_roi", 0) > 0 for r in layers
                ),
                interpretation="ROI intersection only; acquisition/label independence and dry/unknown support still need assessment",
            ),
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
