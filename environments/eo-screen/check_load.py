"""Check local model loading; optionally probe Copernicus normalization on synthetic data."""

import argparse
import importlib.util
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "data/raw/limburg_dynamic_model_weights"


def module_at(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_copernicus_output_norm(model, mismatch):
    """Permit only the exact output layer intentionally absent in the release."""
    import torch

    if set(mismatch.missing_keys) != {"fc_norm.weight", "fc_norm.bias"} or mismatch.unexpected_keys:
        raise ValueError(str(mismatch))
    if not torch.equal(model.fc_norm.weight, torch.ones_like(model.fc_norm.weight)):
        raise ValueError("Output LayerNorm scale is not the deterministic default")
    if not torch.equal(model.fc_norm.bias, torch.zeros_like(model.fc_norm.bias)):
        raise ValueError("Output LayerNorm bias is not the deterministic default")


def load(name, probe=False):
    import torch

    torch.set_num_threads(2)
    code, weights = ASSETS / "code" / name, ASSETS / "models" / name
    if name == "olmoearth":
        sys.path.insert(0, str(code))
        from olmoearth_pretrain.model_loader import load_model_from_path

        model = load_model_from_path(weights)
    elif name == "galileo":
        module = module_at("galileo", code / "single_file_galileo.py")
        weights = weights / "models/nano"
        config = json.loads((weights / "config.json").read_text())
        model = module.Encoder(**config["model"]["encoder"])
        state = torch.load(weights / "encoder.pt", map_location="cpu", weights_only=True)
        model.load_state_dict(
            {k.replace(".backbone", ""): v for k, v in state.items()}, strict=True
        )
    elif name == "prithvi":
        module = module_at("prithvi_mae", weights / "prithvi_mae.py")
        config = json.loads((weights / "config.json").read_text())["pretrained_cfg"]
        model = module.PrithviMAE(**config)
        state = torch.load(
            weights / "Prithvi_EO_V2_tiny_TL.pt", map_location="cpu", weights_only=True
        )
        # The publisher's inference code regenerates these fixed position grids.
        for key in list(state):
            if key == "encoder.pos_embed":
                state[key] = model.encoder.pos_embed
            elif key == "decoder.decoder_pos_embed":
                state[key] = model.decoder.decoder_pos_embed
        model.load_state_dict(state, strict=True)
    elif name == "anysat":
        os.chdir(code)
        sys.path = [str(code)] + [p for p in sys.path if p != str(ROOT)]
        module = module_at("hubconf", code / "hubconf.py")
        model = module.AnySat(model_size="base", flash_attn=False)
        state = torch.load(weights / "models/AnySat.pth", map_location="cpu", weights_only=True)
        model.model.load_state_dict(state["state_dict"], strict=True)
    elif name == "croma":
        module = module_at("use_croma", code / "use_croma.py")
        model = module.PretrainedCROMA(
            pretrained_path=str(weights / "CROMA_base.pt"),
            size="base",
            modality="SAR",
            image_resolution=120,
        )
    elif name == "dofa":
        sys.path.insert(0, str(code))
        from dofa_v1 import vit_base_patch16

        model = vit_base_patch16(global_pool=False, num_classes=0)
        state = torch.load(
            weights / "DOFA_ViT_base_e100.pth", map_location="cpu", weights_only=True
        )
        mismatch = model.load_state_dict(state, strict=False)
        if mismatch.missing_keys or set(mismatch.unexpected_keys) != {
            "mask_token",
            "projector.weight",
            "projector.bias",
        }:
            raise ValueError(str(mismatch))
    else:
        code = code / "Copernicus-FM"
        os.chdir(code)
        sys.path = [str(code), str(code / "src")] + [p for p in sys.path if p != str(ROOT)]
        from src.model_vit import vit_base_patch16

        model = vit_base_patch16(num_classes=0, global_pool=True)
        state = torch.load(
            weights / "CopernicusFM_ViT_base_varlang_e100.pth",
            map_location="cpu",
            weights_only=True,
        )
        mismatch = model.load_state_dict(state.get("model", state), strict=False)
        # The official benchmark explicitly expects this newly added output
        # LayerNorm, not missing Transformer/block or patch-embedding weights.
        validate_copernicus_output_norm(model, mismatch)
    model.eval().requires_grad_(False)
    result = {
        "status": "checkpoint_loaded_no_forward_test",
        "torch": torch.__version__,
        "parameters": sum(p.numel() for p in model.parameters()),
    }
    if probe:
        captured = []
        handle = model.fc_norm.register_forward_pre_hook(
            lambda module, inputs: captured.append(inputs[0])
        )
        image = torch.randn(1, 4, 224, 224, generator=torch.Generator().manual_seed(1729))
        metadata = torch.full((1, 4), float("nan"))  # Publisher's unknown-metadata example.
        inputs = (image, metadata, [490, 560, 665, 842], [65, 35, 30, 115], None, "spectral", 16)
        with torch.inference_mode():
            _, first = model(*inputs)
            _, second = model(*inputs)
            expected = torch.nn.functional.layer_norm(captured[0], (768,), eps=model.fc_norm.eps)
        handle.remove()
        if first.shape != (1, 768) or not torch.isfinite(first).all():
            raise ValueError("Invalid synthetic embedding")
        if not torch.equal(first, second) or not torch.allclose(
            first, expected, atol=1e-6, rtol=1e-6
        ):
            raise ValueError("Synthetic normalization/repeatability check failed")
        result.update(
            status="checkpoint_loaded_synthetic_probe_passed",
            synthetic_probe={
                "seed": 1729,
                "input_shape": list(image.shape),
                "embedding_shape": list(first.shape),
                "finite": True,
                "repeatable": True,
                "matches_nonaffine_layernorm": True,
                "layernorm_eps": model.fc_norm.eps,
            },
        )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model",
        required=True,
        choices=["olmoearth", "galileo", "prithvi", "anysat", "croma", "dofa", "copernicus_fm"],
    )
    parser.add_argument(
        "--probe", action="store_true", help="Synthetic Copernicus normalization check only"
    )
    args = parser.parse_args()
    if args.probe and args.model != "copernicus_fm":
        parser.error("--probe is only implemented for copernicus_fm")
    try:
        result = load(args.model, probe=args.probe)
    except Exception as error:
        result = {"status": "adapter_review_needed", "error": f"{type(error).__name__}: {error}"}
    result.update(
        model=args.model,
        checked_utc=datetime.now(timezone.utc).isoformat(),
        python=sys.version,
        executable=sys.executable,
    )
    output = ASSETS / "load_checks" / (args.model + ".json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return int(not result["status"].startswith("checkpoint_loaded"))


if __name__ == "__main__":
    raise SystemExit(main())
