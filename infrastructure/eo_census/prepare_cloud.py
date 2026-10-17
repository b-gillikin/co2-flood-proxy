"""Prepare a credential-free code payload; never provision or alter live adapters."""

import hashlib
import json
import shutil
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "logs/eo-cloud/payload"


def gpu_overlay(source):
    source = source.replace("import json\n", "import json\nimport os\n", 1)
    source = source.replace(
        "def tensor(x):\n    return torch.from_numpy(np.ascontiguousarray(x)).float()",
        """DEVICE = os.environ.get("LIMBURG_EO_DEVICE", "cpu")


def from_numpy(x):
    return torch.from_numpy(x).to(DEVICE)


def tensor(x):
    return from_numpy(np.ascontiguousarray(x)).float()""",
    )
    source = source.replace(
        "self.model = loaders.build_model(name)",
        """self.model = loaders.build_model(name).to(DEVICE)
        if DEVICE.startswith("cuda"):
            torch.backends.cuda.matmul.allow_tf32 = False
            torch.backends.cudnn.allow_tf32 = False""",
    )
    source = source.replace(
        "with torch.inference_mode():", "with torch.inference_mode(), torch.device(DEVICE):"
    )
    # Explicit NumPy tensors are not affected by a default-device context.
    source = source.replace("torch.from_numpy(mask)", "from_numpy(mask)")
    source = source.replace("torch.from_numpy(~mask)", "from_numpy(~mask)")
    source = source.replace(
        "torch.from_numpy(pixel_missing[offset * 128 : offset * 128 + len(batch)])",
        "from_numpy(pixel_missing[offset * 128 : offset * 128 + len(batch)])",
    )
    return source


def main():
    files = [
        "scripts/97_download_limburg_eo_models.py",
        "scripts/100_extract_limburg_eo_sequences.py",
        "scripts/101_aggregate_limburg_eo_catchments.py",
        "src/eo_inputs.py",
        "src/eo_event_inputs.py",
        "src/eo_encoders.py",
        "config/limburg_eo_model_assets.json",
        "environments/eo-screen/check_load.py",
        "results/eo_comparison_preparation/contexts.json",
        "results/eo_comparison_preparation/catchments.gpkg",
        "data/raw/limburg_compact_eo/jobs.json",
        "data/raw/limburg_compact_eo/staging-progress.json",
    ]
    files += [str(p.relative_to(ROOT)) for p in (ROOT / "environments/eo-screen").glob("*lock.txt")]
    files += [
        str(p.relative_to(ROOT))
        for p in (ROOT / "infrastructure/eo_census").glob("*")
        if p.is_file()
    ]
    for name in files:
        target = OUT / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    encoder = OUT / "src/eo_encoders.py"
    encoder.write_text(gpu_overlay(encoder.read_text()))
    runner = OUT / "scripts/100_extract_limburg_eo_sequences.py"
    source = runner.read_text().replace(
        "import json\n", "import json\nimport os\nimport platform\n", 1
    )
    source = source.replace(
        '"model": model,\n        "checkpoint":',
        '"device": os.environ.get("LIMBURG_EO_DEVICE", "cpu"),\n        "platform": platform.platform(),\n        "model": model,\n        "checkpoint":',
        1,
    )
    runner.write_text(source)
    # Freeze platform-specific dependency candidates separately, never edit Mac environments.
    for lock in (ROOT / "environments/eo-screen").glob("*-macos-arm64.lock.txt"):
        text = lock.read_text()
        text = (
            "\n".join(
                "torch==2.2.1" if line.startswith("torch @ file:") else line
                for line in text.splitlines()
            )
            + "\n"
        )
        (
            OUT / "environments/eo-screen" / lock.name.replace("macos-arm64", "linux-candidate")
        ).write_text(text)
    paths = [OUT / name for name in files]
    paths += list((OUT / "environments/eo-screen").glob("*-linux-candidate.lock.txt"))
    hashes = {str(p.relative_to(OUT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    manifest = {
        "files_sha256": hashes,
        "purpose": "Cloud code and geometry only; no provider gauge data, credentials or weights.",
        "validation": "CUDA and Linux compatibility remain to be benchmarked; not a completed cloud deployment.",
    }
    (OUT / "payload-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    archive = OUT.parent / "eo-cloud-code.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        for name in [*hashes, "payload-manifest.json"]:
            tar.add(OUT / name, arcname=name, recursive=False)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix(".gz.sha256").write_text(f"{digest}  {archive.name}\n")
    print(json.dumps({"archive": str(archive), "bytes": archive.stat().st_size, "sha256": digest}))


if __name__ == "__main__":
    main()
