"""Regressions for the reproduced audit failures, using isolated geospatial fixtures."""

import json

import numpy as np
import pandas as pd
import pytest
from rasterio.transform import from_origin

from src.eo_coherent_inputs import read_coherent_tile
from src.eo_inputs import sha256
from src.eo_integrity import (
    fresh_output,
    input_population,
    merge_selected,
    selected_aggregates,
    validate_aggregate,
    validate_run,
)
from src.eo_retrieval_cache import RetrievalCache


def complete_run(root, model="example", name="new", **status_changes):
    run = root / "runs" / model / name
    run.mkdir(parents=True)
    (run / "manifest.json").write_text(
        json.dumps(
            {"model": model, "purpose": "context_census", "code": {}, "mask_policy": "fixed"}
        )
    )
    status = {
        "run": name,
        "status": "completed",
        "errors": 0,
        "contexts_total": 1,
        **status_changes,
    }
    (run / "status.json").write_text(json.dumps(status))
    return run


def complete_aggregate(root, run, model="example", name="fixed"):
    out = root / "aggregates" / model / name
    out.mkdir(parents=True)
    pd.DataFrame(
        {"run": [run.name], "context_id": ["ctx"], "catchment_gauge": ["g"], "e0000": [2.0]}
    ).to_parquet(out / (model + ".parquet"))
    for file in ["coverage.parquet", "patch_areas.parquet"]:
        pd.DataFrame({"run": [run.name], "model": [model]}).to_parquet(out / file)
    report = {
        "engineering": False,
        "partial": False,
        "errors": [],
        "contexts_by_model": {model: 1},
        "catchments_sha256": "geometry",
        "source_sha256": {
            str((run / "manifest.json").relative_to(root)): sha256(run / "manifest.json")
        },
        "outputs_sha256": {p.name: sha256(p) for p in out.glob("*.parquet")},
    }
    (out / "manifest.json").write_text(json.dumps(report))
    return out


@pytest.mark.parametrize(
    "change",
    [
        {"status": "running"},
        {"status": "completed_with_errors", "errors": 1},
        {"status": "completed", "errors": 1},
        {"run": "other"},
    ],
)
def test_bad_extraction_is_never_complete(tmp_path, change):
    run = complete_run(tmp_path, **change)
    with pytest.raises(ValueError):
        validate_run(tmp_path, run)


def test_partial_is_explicit_and_not_a_complete_aggregate(tmp_path):
    run = complete_run(tmp_path, status="completed_with_errors", errors=1)
    validate_run(tmp_path, run, allow_partial=True)
    out = complete_aggregate(tmp_path, run)
    with pytest.raises(ValueError, match="incomplete"):
        validate_aggregate(tmp_path, out, "example")


def test_zero_contexts_or_stale_parquet_cannot_be_recertified(tmp_path):
    run = complete_run(tmp_path)
    out = complete_aggregate(tmp_path, run)
    (out / "leftover.parquet").write_bytes(b"old")
    with pytest.raises(ValueError, match="stale"):
        validate_aggregate(tmp_path, out, "example")
    (out / "leftover.parquet").unlink()
    p = out / "manifest.json"
    r = json.loads(p.read_text())
    r["contexts_by_model"] = {}
    p.write_text(json.dumps(r))
    with pytest.raises(ValueError, match="No accepted"):
        validate_aggregate(tmp_path, out, "example")


def test_fresh_output_preserves_previous_and_rolls_back_errors(tmp_path):
    out = tmp_path / "census"
    out.mkdir()
    (out / "old.parquet").write_bytes(b"old")
    with pytest.raises(ValueError):
        with fresh_output(out) as stage:
            (stage / "new.parquet").write_bytes(b"new")
            raise ValueError("bad aggregation")
    assert (out / "old.parquet").read_bytes() == b"old"
    with fresh_output(out) as stage:
        (stage / "new.parquet").write_bytes(b"new")
    assert not (out / "old.parquet").exists()
    assert (out / "new.parquet").read_bytes() == b"new"
    assert list(tmp_path.glob("census.previous-*/old.parquet"))


def test_selected_merge_uses_fixed_run_not_old_convenient_location(tmp_path):
    contexts = tmp_path / "contexts.json"
    contexts.write_text(json.dumps([{"context_id": "ctx"}]))
    new = complete_run(tmp_path)
    fixed = complete_aggregate(tmp_path, new)
    old = complete_run(tmp_path, name="old")
    complete_aggregate(tmp_path, old, name="original")
    selection = {
        "contexts": "contexts.json",
        "contexts_sha256": sha256(contexts),
        "models": {
            "example": {
                "run": str(new.relative_to(tmp_path)),
                "aggregate": str(fixed.relative_to(tmp_path)),
                "mask_policy": "fixed",
            }
        },
    }
    out = tmp_path / "selected"
    merged = merge_selected(tmp_path, selection, out)
    assert set(pd.read_parquet(out / "example.parquet").run) == {"new"}
    assert merged["selected_runs"]["example"]["run"].endswith("/new")
    selection["models"]["example"]["run"] = str(old.relative_to(tmp_path))
    accepted, status = selected_aggregates(tmp_path, selection)
    assert not accepted and status["example"]["status"] == "invalid"


def test_population_identity_changes_with_context_selection_or_ledger(tmp_path):
    (tmp_path / "jobs.json").write_text("[]")
    (tmp_path / "contexts.json").write_text(json.dumps([{"context_id": "a"}, {"context_id": "b"}]))
    full = input_population(tmp_path, tmp_path)
    single = input_population(tmp_path, tmp_path, "a")
    assert full != single and single["expected_context_ids"] == ["a"]
    (tmp_path / "jobs.json").write_text("[{}]")
    assert full != input_population(tmp_path, tmp_path)
    with pytest.raises(ValueError, match="Unknown"):
        input_population(tmp_path, tmp_path, "unknown")


def test_single_context_cannot_masquerade_as_census(tmp_path):
    run = complete_run(tmp_path)
    p = run / "manifest.json"
    saved = json.loads(p.read_text())
    saved["input_population"] = {"selection": "single_context", "expected_context_ids": ["ctx"]}
    p.write_text(json.dumps(saved))
    with pytest.raises(ValueError, match="Single-context"):
        validate_run(tmp_path, run)
    validate_run(tmp_path, run, allow_partial=True)


def test_same_day_loader_masks_mixed_spectra_without_fabrication(monkeypatch):
    import src.eo_coherent_inputs as module

    fine = {
        "product": "s2_10m",
        "bands": ["B2", "B3", "B4", "B8", "acquired_day"],
        "window": {
            "id": "w",
            "start": "2018-09-01T00:00:00+00:00",
            "end": "2018-10-01T00:00:00+00:00",
        },
        "bounds": [0, 0, 40, 40],
    }
    coarse = {
        **fine,
        "product": "s2_20m",
        "bands": ["B5", "B6", "B7", "B8A", "B11", "B12", "SCL", "acquired_day"],
    }
    a = np.full((5, 4, 4), 1000, dtype="float32")
    a[-1] = 17800
    b = np.full((8, 2, 2), 2000, dtype="float32")
    b[-1] = 17800
    b[-1, 0, 0] = 17801

    def product(root, job):
        x = a if job["product"] == "s2_10m" else b
        return (
            x,
            np.ones_like(x, dtype=bool),
            from_origin(0, 40, 10 if x is a else 20, 10 if x is a else 20),
            "EPSG:32632",
            {},
        )

    monkeypatch.setattr(module, "read_product", product)
    tile = read_coherent_tile(None, fine, {("w", (0, 0, 40, 40), "s2_20m"): coarse})
    assert tile.valid.sum() == 12 and not tile.valid[:2, :2].any()
    assert np.all(tile.days[tile.valid] == 17800)
    assert np.all(tile.values[0] == 1000) and np.all(tile.values[3] == 2000)
    b[-1] = 17800
    assert read_coherent_tile(None, fine, {("w", (0, 0, 40, 40), "s2_20m"): coarse}).valid.all()


def test_retrieval_cache_reuses_only_identical_data_policy_and_code(tmp_path):
    calls = []

    def retrieve(sample, blocks, **options):
        calls.append(options)
        return sample.copy(), pd.DataFrame({"rank": [1]})

    cache = RetrievalCache(tmp_path, retrieve)
    sample = pd.DataFrame({"event_id": ["a"], "q": [1.0]})
    a = cache(sample, policy="pooled")
    b = cache(sample, policy="pooled")
    pd.testing.assert_frame_equal(a[0], b[0])
    assert len(calls) == 1
    cache(sample, policy="foreign")
    assert len(calls) == 2
    sample.loc[0, "q"] = 2
    cache(sample, policy="pooled")
    assert len(calls) == 3
    cache.code = {"changed": "source"}
    cache(sample, policy="pooled")
    assert len(calls) == 4
    assert cache.hits == 1


def test_empty_actual_aggregation_preserves_existing_stale_destination(tmp_path, monkeypatch):
    import geopandas as gpd
    from shapely.geometry import box

    from src.eo_comparison import load_script

    runner = load_script("101_aggregate_limburg_eo_catchments.py", "audit_aggregate_test")
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    preparation = tmp_path / "preparation"
    preparation.mkdir()
    gpd.GeoDataFrame({"gauge": ["g"]}, geometry=[box(0, 0, 20, 20)], crs=32632).to_file(
        preparation / "catchments.gpkg"
    )
    (preparation / "contexts.json").write_text(
        json.dumps([{"context_id": "ctx", "windows": [{"id": "w"}]}])
    )
    run = complete_run(tmp_path, status="completed_with_errors", errors=1)
    target = tmp_path / "out/census"
    target.mkdir(parents=True)
    (target / "example.parquet").write_bytes(b"stale model output")
    monkeypatch.setattr(
        "sys.argv",
        [
            "aggregate",
            "--preparation",
            str(preparation),
            "--sequences",
            str(tmp_path / "runs"),
            "--out",
            str(target.parent),
            "--model",
            "example",
        ],
    )
    with pytest.raises(ValueError, match="No accepted extraction"):
        runner.main()
    assert (target / "example.parquet").read_bytes() == b"stale model output"
    assert not (target / "manifest.json").exists()
    assert run.exists()


def test_run_scope_cannot_change_context_count(tmp_path):
    run = complete_run(tmp_path)
    with pytest.raises(ValueError, match="context count"):
        validate_run(tmp_path, run, expected_contexts=["ctx", "another"])


def test_retrieval_cache_detects_output_corruption(tmp_path):
    def retrieve(sample, blocks, **options):
        return sample, pd.DataFrame({"rank": [1]})

    cache = RetrievalCache(tmp_path, retrieve)
    sample = pd.DataFrame({"event_id": ["a"]})
    cache(sample)
    path = next(tmp_path.glob("*/predictions.parquet"))
    path.write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="differs from receipt"):
        cache(sample)


def test_explicit_partial_can_retain_a_smaller_documented_scope(tmp_path):
    run = complete_run(tmp_path, status="completed_with_errors", errors=1)
    validate_run(tmp_path, run, expected_contexts=["ctx", "other"], allow_partial=True)
    with pytest.raises(ValueError):
        validate_run(tmp_path, run, expected_contexts=["ctx", "other"])


def test_bound_input_ledgers_are_rechecked_before_acceptance(tmp_path):
    run = complete_run(tmp_path)
    (tmp_path / "jobs.json").write_text("[]")
    (tmp_path / "contexts.json").write_text(json.dumps([{"context_id": "ctx"}]))
    saved = json.loads((run / "manifest.json").read_text())
    saved["input_population"] = input_population(tmp_path, tmp_path)
    (run / "manifest.json").write_text(json.dumps(saved))
    validate_run(tmp_path, run)
    (tmp_path / "jobs.json").write_text("[{}]")
    with pytest.raises(ValueError, match="ledger changed"):
        validate_run(tmp_path, run)


def test_full_selected_handoff_rejects_changed_selection_and_source_status(tmp_path):
    from src.eo_inputs import ROUTES
    from src.eo_integrity import validate_comparison_inputs

    contexts = tmp_path / "contexts.json"
    contexts.write_text(json.dumps([{"context_id": "ctx"}]))
    models = {}
    for model in ROUTES:
        run = complete_run(tmp_path, model=model)
        folder = complete_aggregate(tmp_path, run, model=model)
        models[model] = {
            "run": str(run.relative_to(tmp_path)),
            "aggregate": str(folder.relative_to(tmp_path)),
            "mask_policy": "fixed",
        }
    selection = {"contexts": "contexts.json", "contexts_sha256": sha256(contexts), "models": models}
    out = tmp_path / "merged"
    merge_selected(tmp_path, selection, out)
    report = validate_comparison_inputs(tmp_path, out, selection=selection)
    assert set(report["selected_runs"]) == set(ROUTES)
    with pytest.raises(ValueError, match="current selected-run"):
        validate_comparison_inputs(tmp_path, out, selection={**selection, "version": "changed"})
    status = tmp_path / models["galileo"]["run"] / "status.json"
    status.write_text(json.dumps({"status": "completed_with_errors", "errors": 1}))
    with pytest.raises(ValueError, match="Selected source changed"):
        validate_comparison_inputs(tmp_path, out, selection=selection)


def test_verified_subset_can_proceed_without_claiming_all_models_complete(tmp_path):
    from src.eo_inputs import ROUTES
    from src.eo_integrity import validate_comparison_inputs

    contexts = tmp_path / "contexts.json"
    contexts.write_text(json.dumps([{"context_id": "ctx"}]))
    models = {}
    for model in ROUTES:
        run = complete_run(tmp_path, model=model)
        folder = complete_aggregate(tmp_path, run, model=model)
        models[model] = {
            "run": str(run.relative_to(tmp_path)),
            "aggregate": str(folder.relative_to(tmp_path)),
            "mask_policy": "fixed",
        }
    (tmp_path / models["presto"]["run"] / "status.json").unlink()
    selection = {"contexts": "contexts.json", "contexts_sha256": sha256(contexts), "models": models}
    out = tmp_path / "available"
    report = merge_selected(tmp_path, selection, out, available_only=True)
    assert report["partial"] and "presto" not in report["selected_runs"]
    assert report["readiness"]["presto"]["status"] == "pending_extraction"
    with pytest.raises(ValueError, match="validated selected-run"):
        validate_comparison_inputs(tmp_path, out, selection=selection)
    validate_comparison_inputs(tmp_path, out, selection=selection, allow_partial=True)


def test_selected_merge_retains_geometry_and_corruption_checks(tmp_path):
    contexts = tmp_path / "contexts.json"
    contexts.write_text(json.dumps([{"context_id": "ctx"}]))
    models = {}
    for model in ["croma", "prithvi"]:
        run = complete_run(tmp_path, model=model)
        folder = complete_aggregate(tmp_path, run, model=model)
        models[model] = {
            "run": str(run.relative_to(tmp_path)),
            "aggregate": str(folder.relative_to(tmp_path)),
            "mask_policy": "fixed",
        }
    selection = {"contexts": "contexts.json", "contexts_sha256": sha256(contexts), "models": models}
    manifest = tmp_path / models["prithvi"]["aggregate"] / "manifest.json"
    saved = json.loads(manifest.read_text())
    saved["catchments_sha256"] = "different"
    manifest.write_text(json.dumps(saved))
    with pytest.raises(ValueError, match="geometries differ"):
        merge_selected(tmp_path, selection, tmp_path / "out")
    saved["catchments_sha256"] = "geometry"
    manifest.write_text(json.dumps(saved))
    (tmp_path / models["croma"]["aggregate"] / "croma.parquet").write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="not ready"):
        merge_selected(tmp_path, selection, tmp_path / "out")
