"""Check local checkpoint/architecture binding only; no forward pass or event data."""

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


def load(name):
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

        model = vit_base_patch16(num_classes=0, global_pool=False)
        state = torch.load(
            weights / "CopernicusFM_ViT_base_varlang_e100.pth",
            map_location="cpu",
            weights_only=True,
        )
        mismatch = model.load_state_dict(state.get("model", state), strict=False)
        if mismatch.missing_keys or mismatch.unexpected_keys:
            raise ValueError(str(mismatch))
    model.eval().requires_grad_(False)
    return {
        "status": "checkpoint_loaded_no_forward_test",
        "torch": torch.__version__,
        "parameters": sum(p.numel() for p in model.parameters()),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model",
        required=True,
        choices=["olmoearth", "galileo", "prithvi", "anysat", "croma", "dofa", "copernicus_fm"],
    )
    args = parser.parse_args()
    try:
        result = load(args.model)
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
    return int(result["status"] != "checkpoint_loaded_no_forward_test")


if __name__ == "__main__":
    raise SystemExit(main())
