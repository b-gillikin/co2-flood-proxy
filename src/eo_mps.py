"""Isolated MPS version of the tested frozen adapter; live CPU code is untouched."""

import importlib.util
import os
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def install():
    import torch

    if not torch.backends.mps.is_available():
        raise RuntimeError("MPS unavailable; production GPU jobs do not silently fall back")
    helper_path = ROOT / "infrastructure/eo_census/prepare_cloud.py"
    spec = importlib.util.spec_from_file_location("eo_device_helper", helper_path)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    original = ROOT / "src/eo_encoders.py"
    text = helper.gpu_overlay(original.read_text())
    os.environ["LIMBURG_EO_DEVICE"] = "mps"
    module = types.ModuleType("src.eo_encoders")
    module.__file__ = str(original)
    module.__package__ = "src"
    sys.modules["src.eo_encoders"] = module
    exec(compile(text, str(original), "exec"), module.__dict__)
