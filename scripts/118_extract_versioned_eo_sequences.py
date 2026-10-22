"""Future extraction with bound input population and same-UTC-day S2 validity.

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
from src.eo_coherent_inputs import POLICY, read_coherent_tile
from src.eo_inputs import ROUTES, sha256
from src.eo_integrity import input_population
from src.eo_token_masks import token_observations


def main():
    parser = argparse.ArgumentParser(description=__doc__, add_help=False)
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
    args, rest = parser.parse_known_args()
    if args.runtime_profile != "native" and (args.model, args.device) != ("presto", "cpu"):
        raise ValueError("Presto profile requires Presto on CPU")
    spec = importlib.util.spec_from_file_location(
        "versioned_eo_loop", ROOT / "scripts/100_extract_limburg_eo_sequences.py"
    )
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    original_identity = runner.identity
    population = input_population(args.archive, args.preparation, args.context)
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
        )
        saved["mask_policy"] = (
            "all_pixels_observed_in_native_token_block_v1"
            if model in {"olmoearth", "galileo"}
            else "native_pixel_mask_v1"
        )
        for name in [
            "scripts/118_extract_versioned_eo_sequences.py",
            "src/eo_coherent_inputs.py",
            "src/eo_integrity.py",
            "src/eo_token_masks.py",
        ]:
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
        tile = read_coherent_tile(root, job, companions)
        if args.model in {"olmoearth", "galileo"}:
            # Grid/patch sizes are multiples of the native stride. Mask before
            # get_patch so coordinates, dates and valid-count metadata agree.
            tile.valid = token_observations(tile.valid, 4 if args.model == "olmoearth" else 8)
        return tile

    runner.identity, runner.read_tile = identity, read_tile
    if args.runtime_profile == "presto-torch291-cpu4":
        from src.eo_encoders import loaders

        original_builder = loaders.build_model

        def build_model(name):
            import torch

            model = original_builder(name)
            torch.set_num_threads(4)
            return model

        loaders.build_model = build_model
    if args.device == "mps":
        from src.eo_mps import install

        install()
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
