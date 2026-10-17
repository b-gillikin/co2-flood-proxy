"""Run the unchanged census logic with a separately fingerprinted MPS adapter."""

import importlib.util
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.eo_inputs import sha256
from src.eo_mps import install


def main():
    spec = importlib.util.spec_from_file_location(
        "eo_original_census", ROOT / "scripts/100_extract_limburg_eo_sequences.py"
    )
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    original_identity = runner.identity

    def identity(model):
        value = original_identity(model)
        value["execution_device"] = "mps"
        value["platform"] = platform.platform()
        for path in [
            Path(__file__).resolve(),
            ROOT / "src/eo_mps.py",
            ROOT / "infrastructure/eo_census/prepare_cloud.py",
        ]:
            value["code"][str(path.relative_to(ROOT))] = sha256(path)
        return value

    runner.identity = identity
    install()
    if "--output" not in sys.argv:
        sys.argv.extend(["--output", str(ROOT / "data/processed/limburg_eo_mps_sequences")])
    return runner.main()


if __name__ == "__main__":
    raise SystemExit(main())
