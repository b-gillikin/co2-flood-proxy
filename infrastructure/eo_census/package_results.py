"""Create a compact, hash-verified per-model result download; no raw gauge data."""

import argparse
import hashlib
import json
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def package(folder, output):
    manifest = json.loads((folder / "manifest.json").read_text())
    if manifest["errors"]:
        raise ValueError("Aggregation contains errors; do not label a package completed")
    names = list(manifest["outputs_sha256"])
    for name in names:
        if Path(name).name != name or sha256(folder / name) != manifest["outputs_sha256"][name]:
            raise ValueError("Invalid aggregate path or checksum")
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = output.with_suffix(output.suffix + ".partial")
    with tarfile.open(temp, "w:gz") as tar:
        for name in [*names, "manifest.json"]:
            tar.add(folder / name, arcname=name, recursive=False)
    temp.replace(output)
    digest = sha256(output)
    output.with_suffix(output.suffix + ".sha256").write_text(f"{digest}  {output.name}\n")
    return digest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--model", required=True)
    args = parser.parse_args()
    folder = ROOT / "results/eo_catchment_representations/per_model" / args.model / "census"
    output = ROOT / "results/eo_result_packages" / (args.model + ".tar.gz")
    print(json.dumps({"file": str(output), "sha256": package(folder, output)}))
