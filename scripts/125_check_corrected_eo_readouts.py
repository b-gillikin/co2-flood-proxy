"""Small real-input checks of corrected 1/4/12-frame routes, not event scoring."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.eo_inputs import ROUTES, get_patch, patch_origins, sha256


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, choices=sorted(ROUTES))
    parser.add_argument("--device", choices=["cpu", "mps"], default="cpu")
    parser.add_argument("--runtime-profile", default="native")
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location(
        "corrected_entry", ROOT / "scripts/118_extract_versioned_eo_sequences.py"
    )
    entry = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(entry)
    Encoder = entry.configure_encoder(args.model, args.device, args.runtime_profile)
    encoder = Encoder(args.model)
    archive = ROOT / "data/raw/limburg_compact_eo"
    jobs = json.loads((archive / "jobs.json").read_text())
    index = {(j["window"]["id"], tuple(j["bounds"]), j["product"]): j for j in jobs}
    contexts = json.loads((ROOT / "results/eo_comparison_preparation/contexts.json").read_text())
    product, size, _ = ROUTES[args.model]
    rows = []
    for kind, count in [("monthly_snapshot", 1), ("recent", 4), ("monthly", 12)]:
        tested = False
        # Fixed engineering period; selection uses availability/support, never outcomes.
        for context in contexts:
            windows = context["windows"]
            if context["kind"] != kind or not windows[0]["start"].startswith("2018-"):
                continue
            if len(windows) != count:
                raise ValueError("Unexpected readout length")
            candidates = sorted(
                {
                    tuple(j["bounds"])
                    for j in jobs
                    if j["product"] == product and j["window"]["id"] == windows[0]["id"]
                }
            )
            for bounds in candidates:
                sequence = [index.get((w["id"], bounds, product)) for w in windows]
                companions = (
                    [index.get((w["id"], bounds, "s2_20m")) for w in windows]
                    if product == "s2_10m"
                    else []
                )
                if any(
                    j is None or not (archive / j["relative_path"]).exists()
                    for j in sequence + companions
                ):
                    continue
                tiles = [entry.versioned_tile(archive, j, index, args.model) for j in sequence]
                origins = patch_origins(tiles[0], size)
                origin = max(
                    origins,
                    key=lambda rc: min(
                        int(t.valid[rc[0] : rc[0] + size, rc[1] : rc[1] + size].sum())
                        for t in tiles
                    ),
                )
                patches = [get_patch(t, *origin, size) for t in tiles]
                if any(not p["valid"].any() for p in patches):
                    continue
                vector = encoder.sequence(patches)
                repeat = encoder.sequence(patches)
                if not np.array_equal(vector, repeat):
                    raise ValueError("Corrected real-input inference is not repeatable")
                masks = np.stack([p["valid"] for p in patches])
                days = np.stack([p["days"] for p in patches])
                with tempfile.TemporaryDirectory(prefix="eo-readout-", dir=ROOT / "logs") as tmp:
                    path = Path(tmp) / "fixture.npz"
                    np.savez_compressed(path, embedding=vector, valid=masks, acquired_day=days)
                    with np.load(path) as saved:
                        for key, expected in [
                            ("embedding", vector),
                            ("valid", masks),
                            ("acquired_day", days),
                        ]:
                            if not np.array_equal(saved[key], expected, equal_nan=True):
                                raise ValueError("Lossless output round trip failed: " + key)
                rows.append(
                    {
                        "kind": kind,
                        "frames": count,
                        "context": context["context_id"],
                        "bounds": bounds,
                        "origin": origin,
                        "dimension": len(vector),
                        "finite": bool(np.isfinite(vector).all()),
                        "repeatable": True,
                        "lossless_npz_roundtrip": True,
                        "observed_pixels_by_frame": [int(p["valid"].sum()) for p in patches],
                        "dates": [p["metadata"]["representative_date"] for p in patches],
                    }
                )
                print(json.dumps(rows[-1]), flush=True)
                tested = True
                break
            if tested:
                break
        if not tested:
            raise ValueError("No held 2018 engineering support for " + kind)
    report = {
        "model": args.model,
        "device": args.device,
        "status": "passed",
        "checked_utc": datetime.now(timezone.utc).isoformat(),
        "checks": rows,
        "corrections_sha256": sha256(ROOT / "src/eo_encoder_corrections.py"),
        "entry_sha256": sha256(ROOT / "scripts/118_extract_versioned_eo_sequences.py"),
        "check_script_sha256": sha256(Path(__file__)),
        "scope": "engineering support only; no event selection or empirical score",
    }
    dest = ROOT / "logs/eo-coherent-correction-v1" / (args.model + "-readouts.json")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
