"""Catchment merge must retain each model's verified output and geometry."""

import json
import runpy
import tempfile
from pathlib import Path

import pandas as pd
import pytest

M = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "scripts/105_run_limburg_eo_census.py")
)


def make_model(base, model, geometry="same"):
    folder = base / "per_model" / model / "census"
    folder.mkdir(parents=True)
    pd.DataFrame({"e0000": [1.0]}).to_parquet(folder / f"{model}.parquet")
    for name in ["coverage", "patch_areas"]:
        pd.DataFrame({"model": [model]}).to_parquet(folder / f"{name}.parquet")
    (folder / "manifest.json").write_text(
        json.dumps(
            {
                "catchments_sha256": geometry,
                "contexts_by_model": {model: 1},
                "source_sha256": {model: "digest"},
                "errors": [],
                "outputs_sha256": {p.name: M["sha256"](p) for p in folder.glob("*.parquet")},
            }
        )
    )
    return folder


def test_merge_preserves_models_and_metadata():
    with tempfile.TemporaryDirectory() as directory:
        base = Path(directory)
        for model in ["first", "second"]:
            make_model(base, model)
        M["merge_aggregates"](base, ["first", "second"])
        out = base / "census"
        assert set(pd.read_parquet(out / "coverage.parquet").model) == {"first", "second"}
        manifest = json.loads((out / "manifest.json").read_text())
        assert manifest["contexts_by_model"] == {"first": 1, "second": 1}
        assert set(manifest["source_sha256"]) == {"first", "second"}


def test_merge_rejects_corruption_and_geometry_mismatch():
    with tempfile.TemporaryDirectory() as directory:
        base = Path(directory)
        first = make_model(base, "first")
        make_model(base, "second", "different")
        with pytest.raises(ValueError, match="geometries"):
            M["merge_aggregates"](base, ["first", "second"])
        (first / "first.parquet").write_bytes(b"corrupt")
        with pytest.raises(ValueError, match="checksum"):
            M["merge_aggregates"](base, ["first"])
