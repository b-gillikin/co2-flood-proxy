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


def test_completed_aggregate_cannot_substitute_cpu_for_mps(tmp_path, monkeypatch):
    root = tmp_path
    geometry = root / "results/eo_comparison_preparation/catchments.gpkg"
    geometry.parent.mkdir(parents=True)
    geometry.write_bytes(b"held geometry")
    source = root / "data/processed/run/manifest.json"
    source.parent.mkdir(parents=True)
    source.write_text(json.dumps({"execution_device": "cpu", "code": {}}))
    base = root / "results/eo_catchment_representations"
    folder = make_model(base, "example", M["sha256"](geometry))
    saved = json.loads((folder / "manifest.json").read_text())
    saved["source_sha256"] = {str(source.relative_to(root)): M["sha256"](source)}
    (folder / "manifest.json").write_text(json.dumps(saved))
    fn = M["completed_aggregate"]
    monkeypatch.setitem(fn.__globals__, "ROOT", root)
    assert fn(base, "example", "cpu")
    assert not fn(base, "example", "mps")
