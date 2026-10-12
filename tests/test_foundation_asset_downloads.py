import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
MANIFEST_PATH = ROOT / "config/limburg_foundation_assets.json"
SCRIPT = ROOT / "scripts/66_download_limburg_foundation_assets.py"
SPEC = importlib.util.spec_from_file_location("foundation_downloads", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_manifest_is_bounded_and_pinned():
    manifest = json.loads(MANIFEST_PATH.read_text())
    ttm = manifest["ttm"]
    assert ttm["context_length"] == 512
    assert ttm["prediction_length"] == 96
    assert len(ttm["revision"]) == 40
    assert ttm["files"] == ["README.md", "config.json", "generation_config.json", "model.safetensors"]
    assert "training_args.bin" in ttm["excluded_files"]
    assert manifest["alphaearth"]["years"] == list(range(2017, 2025))
    assert manifest["alphaearth"]["bands"] == 64
    weights = next(asset for asset in manifest["downloads"] if asset["id"] == "ttm_weights")
    assert weights["hf_revision"] == ttm["revision"]
    assert weights["hf_filename"] == "model.safetensors"


def test_downloads_use_https_unique_relative_paths_and_safe_model_files():
    manifest = json.loads(MANIFEST_PATH.read_text())
    paths = []
    for asset in manifest["downloads"]:
        assert asset["url"].startswith("https://")
        destination = Path(asset["destination"])
        assert not destination.is_absolute()
        assert ".." not in destination.parts
        paths.append(destination)
        if asset["group"] == "model":
            assert destination.suffix != ".bin"
            assert "pickle" not in destination.name
    assert len(paths) == len(set(paths))


def test_group_selection_is_complete():
    manifest = json.loads(MANIFEST_PATH.read_text())
    all_assets = MODULE.selected_assets(manifest, "all")
    grouped = sum((MODULE.selected_assets(manifest, group) for group in ("model", "code", "documents")), [])
    assert {asset["id"] for asset in all_assets} == {asset["id"] for asset in grouped}


def test_existing_receipt_is_verified_before_skip(tmp_path):
    target = tmp_path / "asset.json"
    target.write_text('{"ok": true}\n')
    receipt = target.with_suffix(".json.receipt.json")
    receipt.write_text(
        json.dumps(
            {
                "bytes": target.stat().st_size,
                "sha256": MODULE.sha256(target),
                "asset_id": "test",
            }
        )
    )
    assert MODULE.existing_receipt(target)["status"] == "verified-existing"
    target.write_text("changed")
    assert MODULE.existing_receipt(target) is None
