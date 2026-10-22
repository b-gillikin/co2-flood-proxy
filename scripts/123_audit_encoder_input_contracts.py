"""Independent pre-correction checks against pinned publisher input conventions.

Engineering diagnostics only: capture inputs without loading learned weights.
Exit success means the audit ran; each finding explicitly reports conformance.
Use the model's isolated runtime. No input, model, running score or result is changed.
"""

import argparse
import ast
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.eo_inputs import S2_BANDS, sha256


def satmae():
    import torch

    from src.eo_encoders import Encoder

    source = ROOT / "data/raw/limburg_dynamic_model_weights/code/satmae/util/datasets.py"
    tree = ast.parse(source.read_text())
    normalize = next(
        n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "SentinelNormalize"
    )
    dataset = next(
        n
        for n in tree.body
        if isinstance(n, ast.ClassDef) and n.name == "SentinelIndividualImageDataset"
    )
    constants = {
        n.targets[0].id: ast.literal_eval(n.value)
        for n in dataset.body
        if isinstance(n, ast.Assign)
        and isinstance(n.targets[0], ast.Name)
        and n.targets[0].id in {"mean", "std"}
    }
    keep = [i for i in range(13) if i not in {0, 9, 10}]
    mean = np.asarray(constants["mean"])[keep]
    std = np.asarray(constants["std"])[keep]
    namespace = {"np": np}
    exec(compile(ast.Module(body=[normalize], type_ignores=[]), str(source), "exec"), namespace)
    values = (
        np.broadcast_to(mean[:, None, None] + std[:, None, None] * np.array([-3, 0, 3]), (10, 2, 3))
        .astype("float32")
        .copy()
    )
    mask = np.ones((2, 3), bool)
    mask[1, 1] = False
    filled = np.where(mask[None], values, mean[:, None, None])
    # The reference SentinelNormalize -> ToTensor path quantizes uint8 then /255.
    expected = (
        namespace["SentinelNormalize"](mean, std)(filled.transpose(1, 2, 0)).transpose(2, 0, 1)
        / 255.0
    )
    captured = []

    class Capture:
        def forward_features(self, x):
            captured.append(x.numpy().copy()[0])
            return torch.ones(1, 768)

    encoder = Encoder.__new__(Encoder)
    encoder.name, encoder.model = "satmae", Capture()
    encoder(
        {
            "values": values,
            "valid": mask,
            "metadata": {"representative_date": "2018-09-01T00:00:00+00:00"},
        }
    )
    actual = captured[0]
    return {
        "conforms_to_pinned_normalizer": bool(np.allclose(actual, expected, rtol=0, atol=1e-7)),
        "actual_at_channel_mean": float(actual[0, 0, 1]),
        "reference_at_channel_mean": float(expected[0, 0, 1]),
        "actual_range": [float(actual.min()), float(actual.max())],
        "reference_range": [float(expected.min()), float(expected.max())],
        "max_absolute_input_difference": float(np.abs(actual - expected).max()),
        "reference": str(source.relative_to(ROOT)),
        "reference_sha256": sha256(source),
        "interpretation": "Current SatMAE z-score input differs from its publisher's clipped eight-bit stretch followed by /255. No model score inferred.",
    }


def presto():
    import torch

    from src.eo_encoders import Encoder

    # Model loading normally adds its publisher package; this audit bypasses loading.
    sys.path.insert(0, str(ROOT / "data/raw/limburg_dynamic_model_weights/code/presto"))

    days = np.array([[np.datetime64("2018-08-31"), np.datetime64("2018-09-01")]])
    captured = []

    def capture(**kwargs):
        captured.append(kwargs["month"].numpy().tolist())
        return torch.ones(kwargs["x"].shape[0], 128)

    frame = {
        "values": np.full((10, 1, 2), 1000, dtype="float32"),
        "valid": np.ones((1, 2), bool),
        "days": days.astype("datetime64[D]").astype(float),
        "metadata": {
            "representative_date": "2018-08-31T12:00:00+00:00",
            "bounds": [297600, 5625600, 297620, 5625610],
            "resolution_m": 10,
            "crs": "EPSG:32632",
            "bands": S2_BANDS,
        },
    }
    encoder = Encoder.__new__(Encoder)
    encoder.name, encoder.model = "presto", SimpleNamespace(encoder=capture)
    encoder({**frame, "frames": [frame]})
    expected = [[7], [8]]
    return {
        "uses_actual_pixel_acquisition_months": captured[0] == expected,
        "supplied_months": captured[0],
        "actual_pixel_months_zero_based": expected,
        "interpretation": "Patch-median month is repeated for every pixel. Monthly bins have one month; cross-month weekly composites can mix actual months. This is a temporal approximation that available per-pixel dates can remove.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, choices=["satmae", "presto"])
    args = parser.parse_args()
    result = {
        "model": args.model,
        "checked_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "engineering diagnostic; no model weights loaded or empirical scoring",
        "encoder_source_sha256": sha256(ROOT / "src/eo_encoders.py"),
        **(satmae() if args.model == "satmae" else presto()),
    }
    out = ROOT / "logs/eo-pre-correction-audit" / (args.model + "-input-contract.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
