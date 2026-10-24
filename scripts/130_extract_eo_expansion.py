"""Supplemental route extraction with separate TOA/QA60 and radar-orbit identities.

Uses the maintained frozen encoder loop in a separate output root. Never rewrites
or resumes the historical, currently running extractions. Default is inventory.
"""

import argparse
import importlib.metadata
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.eo_encoder_corrections import VERSION as INPUT_CORRECTIONS
from src.eo_encoder_corrections import install as install_corrections
from src.eo_expansion_inputs import POLICY, read_coherent_tile
from src.eo_inputs import ROUTES, sha256
from src.eo_population import input_population
from src.eo_token_masks import token_observations


def configure_encoder(model, device, runtime_profile):
    if runtime_profile != "native" and (model, device) != ("presto", "cpu"):
        raise ValueError("Presto profile requires Presto on CPU")
    if runtime_profile == "presto-torch291-cpu4":
        import torch

        from src.eo_encoders import loaders

        if torch.__version__.split("+")[0] != "2.9.1":
            raise ValueError("Validated Presto profile requires torch 2.9.1")
        original_builder = loaders.build_model

        def build_model(name):
            instance = original_builder(name)
            torch.set_num_threads(4)
            return instance

        loaders.build_model = build_model
    if device == "mps":
        from src.eo_mps import install

        install()
    module = __import__("src.eo_encoders", fromlist=["Encoder"])
    install_corrections(module)
    return module.Encoder


def versioned_tile(root, job, companions, model):
    tile = read_coherent_tile(root, job, companions)
    if model in {"olmoearth", "galileo"}:
        tile.valid = token_observations(tile.valid, 4 if model == "olmoearth" else 8)
    return tile


def argument_parser():
    # Wrapper-only arguments must not consume the delegated --run mode as an
    # abbreviation of --runtime-profile.
    parser = argparse.ArgumentParser(description=__doc__, add_help=False, allow_abbrev=False)
    parser.add_argument("--model", required=True, choices=list(ROUTES))
    parser.add_argument("--device", choices=["cpu", "mps"], default="cpu")
    parser.add_argument(
        "--runtime-profile", choices=["native", "presto-torch291-cpu4"], default="native"
    )
    parser.add_argument("--archive", type=Path, default=ROOT / "data/raw/limburg_compact_eo")
    parser.add_argument(
        "--preparation", type=Path, default=ROOT / "results/eo_comparison_preparation"
    )
    parser.add_argument("--context")
    return parser


def main():
    args, rest = argument_parser().parse_known_args()
    if args.runtime_profile != "native" and (args.model, args.device) != ("presto", "cpu"):
        raise ValueError("Presto profile requires Presto on CPU")
    spec = importlib.util.spec_from_file_location(
        "versioned_eo_loop", ROOT / "scripts/100_extract_limburg_eo_sequences.py"
    )
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    original_identity = runner.identity
    population = input_population(args.archive, args.preparation, args.context, root=ROOT)
    if "--smoke" in rest:
        kind = rest[rest.index("--smoke-kind") + 1] if "--smoke-kind" in rest else "two"
        population.update(
            selection="engineering", expected_context_ids=["engineering_" + kind + "_real_months"]
        )

    def identity(model):
        saved = original_identity(model)
        saved.update(
            input_population=population,
            input_policy=POLICY if ROUTES[model][0] == "s2_10m" else "native_product_v1",
            execution_device=args.device,
            runtime_profile=args.runtime_profile,
            input_corrections=INPUT_CORRECTIONS,
        )
        saved["mask_policy"] = (
            "all_pixels_observed_in_native_token_block_v1"
            if model in {"olmoearth", "galileo"}
            else "native_pixel_mask_v1"
        )
        for name in [
            "scripts/118_extract_versioned_eo_sequences.py",
            "scripts/130_extract_eo_expansion.py",
            "src/eo_expansion_inputs.py",
            "src/eo_coherent_inputs.py",
            "src/eo_population.py",
            "src/eo_token_masks.py",
            "src/eo_encoder_corrections.py",
        ]:
            saved["code"][name] = sha256(ROOT / name)
        if model == "galileo":
            name = "data/raw/limburg_dynamic_model_weights/code/galileo/config/normalization.json"
            saved["code"][name] = sha256(ROOT / name)
        if args.device == "mps":
            for name in ["src/eo_mps.py", "infrastructure/eo_census/prepare_cloud.py"]:
                saved["code"][name] = sha256(ROOT / name)
        if args.runtime_profile == "presto-torch291-cpu4":
            import torch

            if torch.__version__.split("+")[0] != "2.9.1":
                raise ValueError("Validated Presto profile requires torch 2.9.1")
            saved["packages"] = {
                name: importlib.metadata.version(name) for name in saved["packages"]
            }
            saved["packages"]["torch"] = torch.__version__
            name = "environments/eo-screen/presto-torch291-macos-arm64.lock.txt"
            saved["code"][name] = sha256(ROOT / name)
            saved.update(torch_threads=4, pixel_batch_size=128)
        return saved

    def read_tile(root, job, companions):
        return versioned_tile(root, job, companions, args.model)

    runner.identity, runner.read_tile = identity, read_tile
    configure_encoder(args.model, args.device, args.runtime_profile)
    rest += [
        "--model",
        args.model,
        "--archive",
        str(args.archive),
        "--preparation",
        str(args.preparation),
    ]
    if args.context:
        rest += ["--context", args.context]
    if "--output" not in rest:
        rest += ["--output", str(ROOT / "data/processed/limburg_eo_coherent_sequences")]
    old = sys.argv
    try:
        sys.argv = [__file__, *rest]
        return runner.main()
    finally:
        sys.argv = old


if __name__ == "__main__":
    raise SystemExit(main())
