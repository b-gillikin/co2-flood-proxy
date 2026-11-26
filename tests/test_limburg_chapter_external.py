"""Protect unknown pixels, checkpoint identity and verified offload recovery."""

import importlib.util
import json
import shutil
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest


def load_script(number, name):
    path = Path(__file__).resolve().parents[1] / "scripts" / f"{number}_{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_verified_readback_supplies_scoring_without_a_second_download(tmp_path, monkeypatch):
    archive = load_script(238, "archive_chapter_predictions")
    scorer = load_script(242, "score_chapter_archives")
    root = tmp_path.resolve()
    external = root / "results/limburg_chapter_sized_v1/external"
    evaluation = external.parent / "evaluation"
    monkeypatch.setattr(archive, "ROOT", root)
    monkeypatch.setattr(archive, "OUT", external)
    monkeypatch.setattr(archive, "EVALUATION", evaluation)
    monkeypatch.setattr(scorer, "OUT", evaluation)
    monkeypatch.setattr(archive.shutil, "disk_usage", lambda _: SimpleNamespace(free=100 * 1024**3))

    name = "maps/unet/delivered/event/event-tile-box-p0-42.npz"
    source = external / name
    source.parent.mkdir(parents=True)
    prediction = np.array([[1, 2], [0, 255]], dtype=np.uint8)
    valid = prediction != 255
    np.savez_compressed(source, prediction=prediction, radar_valid=valid)
    receipt = external / "receipts/test.json"
    receipt.parent.mkdir()
    receipt.write_text(json.dumps({"files": {name: archive.sha256(source)}}))
    support = evaluation / "support/manifest.json"
    support.parent.mkdir(parents=True)
    support.write_text("{}")
    remote = tmp_path / "remote.tar"
    operations = []

    def fake_az(operation, *args):
        operations.append(operation)
        local = Path(args[args.index("--file") + 1])
        if operation == "upload":
            shutil.copyfile(local, remote)
        else:
            shutil.copyfile(remote, local)

    def score_prediction(key, dataset, reference, kind, seed, actual, mask):
        assert (key, dataset, reference, kind, seed) == (
            "event-tile-box",
            "delivered",
            "p0",
            "unet",
            42,
        )
        np.testing.assert_array_equal(actual, prediction)
        np.testing.assert_array_equal(mask, valid)
        return [{"valid": int(mask.sum())}]

    monkeypatch.setattr(sys, "argv", ["archive", "--root", str(external)])
    monkeypatch.setattr(archive, "blob_exists", lambda _: False)
    monkeypatch.setattr(archive, "run_az", fake_az)
    monkeypatch.setattr(scorer, "score_prediction", score_prediction)
    monkeypatch.setattr(scorer, "restore_archive", lambda *_: pytest.fail("Second download"))
    archive.main()
    (ledger,) = (external / "archives").glob("*.json")
    assert scorer.score_archive(ledger)["predictions"] == 1
    assert scorer.score_archive(ledger)["status"] == "reused"
    assert operations == ["upload", "download"]


def test_prediction_keeps_unknown_and_float32_decision(tmp_path):
    module = load_script(237, "run_chapter_external")
    module.OUT = tmp_path
    valid = np.array([[True, False]])
    values = np.array(
        [[[0.33330, np.nan]], [[0.33335, np.nan]], [[0.33335, np.nan]]], dtype=np.float32
    )
    module.save_one("prediction.npz", values, valid)
    with np.load(tmp_path / "prediction.npz") as saved:
        assert saved["prediction"].tolist() == [[1, 255]]
        assert np.isnan(saved["probability"][:, 0, 1]).all()
    values[:, 0, 1] = 0
    with pytest.raises(ValueError, match="Unknown"):
        module.save_one("bad.npz", values, valid)


def test_resume_requires_local_or_verified_remote_and_same_model(tmp_path):
    module = load_script(237, "run_chapter_external")
    module.OUT = tmp_path
    prediction = tmp_path / "prediction.npz"
    prediction.write_bytes(b"completed prediction")
    digest = module.sha256(prediction)
    receipt = tmp_path / "receipt.json"
    receipt.write_text(json.dumps({"files": {prediction.name: digest}, "model": "unet"}))
    assert module.verified_receipt(receipt, {}, {"model": "unet"})
    prediction.unlink()
    assert module.verified_receipt(receipt, {prediction.name: digest}, {"model": "unet"})
    with pytest.raises(ValueError, match="missing locally"):
        module.verified_receipt(receipt, {})
    with pytest.raises(ValueError, match="different inputs/model"):
        module.verified_receipt(receipt, {prediction.name: digest}, {"model": "native"})


def test_offload_rejects_changed_prediction_before_upload(tmp_path):
    module = load_script(238, "archive_chapter_predictions")
    (tmp_path / "receipts").mkdir()
    (tmp_path / "prediction.npz").write_bytes(b"changed")
    (tmp_path / "receipts/tile.json").write_text(json.dumps({"files": {"prediction.npz": "wrong"}}))
    with pytest.raises(ValueError, match="Missing/changed"):
        module.choose_groups(tmp_path, 10)
