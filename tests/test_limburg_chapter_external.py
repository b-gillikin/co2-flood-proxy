"""Protect unknown pixels, checkpoint identity and verified offload recovery."""

import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest


def load_script(number, name):
    path = Path(__file__).resolve().parents[1] / "scripts" / f"{number}_{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_prediction_keeps_unknown_and_float32_decision(tmp_path):
    module = load_script(237, "run_chapter_external")
    module.OUT = tmp_path
    valid = np.array([[True, False]])
    values = np.array([[[0.33330, np.nan]], [[0.33335, np.nan]], [[0.33335, np.nan]]], dtype=np.float32)
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
