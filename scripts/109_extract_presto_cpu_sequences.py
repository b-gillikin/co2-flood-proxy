"""Full Presto census with isolated torch 2.9.1, CPU4 and separate provenance.

Preserves the original census, weights, batch128, float32, pixels and readout.
Never resumes patches from the earlier torch 2.2.1 output root.
"""

import importlib.metadata
import importlib.util
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
PROFILE = "presto-torch291-cpu4"


def main():
    import torch

    from src.eo_encoders import loaders
    from src.eo_inputs import sha256

    if torch.__version__.split("+")[0] != "2.9.1":
        raise RuntimeError("This profile requires the validated torch 2.9.1 runtime")
    spec = importlib.util.spec_from_file_location(
        "presto_cpu_census", ROOT / "scripts/100_extract_limburg_eo_sequences.py"
    )
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    original_identity = runner.identity
    original_builder = loaders.build_model

    def build_model(name):
        if name != "presto":
            raise ValueError("Dedicated Presto CPU profile")
        model = original_builder(name)
        torch.set_num_threads(4)
        return model

    def identity(model):
        if model != "presto":
            raise ValueError("Dedicated Presto CPU profile")
        value = original_identity(model)
        # Resolve the visible distribution, not the shadowed legacy torch entry.
        for name in value["packages"]:
            value["packages"][name] = importlib.metadata.version(name)
        value["packages"]["torch"] = torch.__version__
        value.update(
            execution_device="cpu",
            runtime_profile=PROFILE,
            torch_threads=4,
            pixel_batch_size=128,
            platform=platform.platform(),
            runtime_executable=sys.executable,
        )
        for path in [
            Path(__file__).resolve(),
            ROOT / "environments/eo-screen/presto-torch291-macos-arm64.lock.txt",
        ]:
            value["code"][str(path.relative_to(ROOT))] = sha256(path)
        return value

    loaders.build_model = build_model
    runner.identity = identity
    if "--model" not in sys.argv:
        sys.argv.extend(["--model", "presto"])
    if "--output" not in sys.argv:
        sys.argv.extend(
            ["--output", str(ROOT / "data/processed/limburg_eo_presto_torch291_sequences")]
        )
    return runner.main()


if __name__ == "__main__":
    raise SystemExit(main())
