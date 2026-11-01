"""Compare supplied prediction rasters on identical CEMS/local valid support.

JSON manifest: list of {case, model, grid, prediction, valid, reference, kind,
reference_offset_hours, reference_dependence}. A case is one AOI/acquisition
comparison; grid is a nonoverlapping tile, repeated once per model. Valid is a
0/1 raster incorporating source nodata and model-specific input availability
(including optical QA where available). All models must supply the same grids.
Do not combine multiple dates or overlapping scene footprints into one case.
"""

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault(
    "PROJ_DATA", str((ROOT / ".venv-foundation/bin/python").resolve().parents[1] / "share/proj")
)
import numpy as np
import rasterio
from shapely.geometry import box

from applied_local_reference import reference_agreement, summarize_cases


def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument("manifest", type=Path)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise FileExistsError("Preserve existing scores; choose a new output")
    entries = json.loads(a.manifest.read_text())
    cases, hashes = {}, {str(a.manifest): hashlib.sha256(a.manifest.read_bytes()).hexdigest()}
    for row in entries:
        for field in [
            "case",
            "model",
            "grid",
            "prediction",
            "valid",
            "reference",
            "kind",
            "reference_offset_hours",
            "reference_dependence",
        ]:
            if field not in row:
                raise ValueError("Missing manifest field: " + field)
        key = (row["case"], row["grid"])
        if row["model"] in cases.setdefault(key, {}):
            raise ValueError("Duplicate model/grid; avoid counting overlapping scene tiles twice")
        cases[key][row["model"]] = row
    results, seen_bounds, case_models = [], {}, {}
    for (case, grid), models in sorted(cases.items()):
        if case in case_models and set(models) != case_models[case]:
            raise ValueError("All models require identical case grids")
        case_models[case] = set(models)
        reference_paths = {r["reference"] for r in models.values()}
        if len(reference_paths) != 1:
            raise ValueError("Models must use the same reference bytes")
        arrays, individual, common, signature, extent = {}, {}, None, None, None
        reference = None
        for name, row in models.items():
            values = {}
            for field in ["reference", "prediction", "valid"]:
                path = Path(row[field])
                path = path if path.is_absolute() else ROOT / path
                hashes[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
                with rasterio.open(path) as ds:
                    current = (ds.shape, tuple(ds.transform), str(ds.crs))
                    if ds.crs is None:
                        raise ValueError("Missing raster CRS")
                    if signature is not None and current != signature:
                        raise ValueError("Raster grids differ; explicit aligned export required")
                    signature = current
                    extent = box(*ds.bounds)
                    pixel_area_m2 = None
                    if ds.crs.is_projected:
                        _, factor = ds.crs.linear_units_factor
                        pixel_area_m2 = (
                            abs(ds.transform.a * ds.transform.e - ds.transform.b * ds.transform.d)
                            * factor**2
                        )
                    values[field] = ds.read(1)
                    if field == "valid" and not set(np.unique(values[field])) <= {0, 1}:
                        raise ValueError("Valid support must be an explicit 0/1 raster")
            reference = values["reference"]
            if not set(np.unique(reference)) <= {0, 1, 255}:
                raise ValueError("Unknown reference coding")
            allowed = [0, 1] if row["kind"] == "surface_water" else [0, 1, 2]
            valid = (values["valid"] == 1) & np.isin(values["prediction"], allowed)
            common = valid if common is None else common & valid
            individual[name] = valid
            arrays[name] = values["prediction"]
        for prior, prior_crs in seen_bounds.setdefault(case, []):
            if signature[2] != prior_crs or extent.intersection(prior).area > 1e-6:
                raise ValueError("Overlapping/incomparable grids within case; mosaic first")
        seen_bounds[case].append((extent, signature[2]))
        for name, prediction in arrays.items():
            row = models[name]
            metrics = reference_agreement(reference, prediction, common, row["kind"])
            results.append(
                dict(
                    case=case,
                    grid=grid,
                    model=name,
                    metrics=metrics,
                    individual_metrics=reference_agreement(
                        reference, prediction, individual[name], row["kind"]
                    ),
                    eligible_reference_pixels=int((reference != 255).sum()),
                    pixel_area_m2=pixel_area_m2,
                    reference_offset_hours=row["reference_offset_hours"],
                    reference_dependence=row["reference_dependence"],
                )
            )
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(
        json.dumps(
            dict(
                results=results,
                case_summaries=summarize_cases(results),
                input_hashes=hashes,
                interpretation="Reference-map agreement; individual coverage and common-support comparison. Case counts pool nonoverlapping grids. July2021 AOIs are not independent floods; no country ranking or field-accuracy claim.",
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
