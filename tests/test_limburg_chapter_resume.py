"""The unattended final fit must recover a whole previous epoch after corruption."""

import importlib.util
from pathlib import Path

import numpy as np  # noqa: F401 — initialize NumPy before torch in the held OpenMP runtime
import torch


def test_two_generation_checkpoint_fallback(tmp_path):
    script = Path(__file__).resolve().parents[1] / "scripts/233_fit_chapter_source.py"
    spec = importlib.util.spec_from_file_location("chapter_source_fit", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    current = tmp_path / "checkpoint-current.pt"
    module.checkpoint(current, {"manifest_sha256": "fixed", "completed_epoch": 1,
                                "model": {"weight": torch.tensor([1.0])}})
    module.checkpoint(current, {"manifest_sha256": "fixed", "completed_epoch": 2,
                                "model": {"weight": torch.tensor([2.0])}})
    assert module.resume(current, "fixed")["completed_epoch"] == 2
    current.write_bytes(b"interrupted checkpoint")
    recovered = module.resume(current, "fixed")
    assert recovered["completed_epoch"] == 1
    assert recovered["model"]["weight"].item() == 1.0
