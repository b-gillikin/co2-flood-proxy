"""Bounded engineering benchmark; never modifies the live census/adapter/assets.

Prepare a fixed held-data fixture once, then compare batch/thread settings on
CPU. Pixel population, weights, missingness, dates and mean pooling are unchanged.
Run with different existing runtimes to test runtime overhead independently.
"""

import argparse
import cProfile
import json
import pstats
import sys
import time
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--label", default="original")
    parser.add_argument("--configs", nargs="+", default=["128:2", "128:1", "512:2", "512:1"])
    parser.add_argument(
        "--fixture", type=Path, default=ROOT / "logs/presto-cpu-benchmark/fixture.npz"
    )
    args = parser.parse_args()
    import numpy as np

    from src.eo_inputs import get_patch, patch_origins, read_tile, sha256

    out = args.fixture.parent
    out.mkdir(parents=True, exist_ok=True)
    if args.prepare:
        archive = ROOT / "data/raw/limburg_compact_eo"
        jobs = json.loads((archive / "jobs.json").read_text())
        index = {(j["window"]["id"], tuple(j["bounds"]), j["product"]): j for j in jobs}
        bounds = (297600, 5625600, 307200, 5635200)
        windows = [f"monthly_2018{m:02d}01_2018{m + 1:02d}01" for m in range(1, 12)] + [
            "monthly_20181201_20190101"
        ]
        started = time.monotonic()
        tiles = [read_tile(archive, index[(w, bounds, "s2_10m")], index) for w in windows]
        origins = patch_origins(tiles[0], 64)
        counts = [
            min(int(t.valid[r : r + 64, c : c + 64].sum()) for t in tiles) for r, c in origins
        ]
        row, col = origins[int(np.argmax(counts))]
        patches = [get_patch(t, row, col, 64) for t in tiles]
        np.savez_compressed(
            args.fixture,
            values=np.stack([p["values"] for p in patches]),
            valid=np.stack([p["valid"] for p in patches]),
            days=np.stack([p["days"] for p in patches]),
            metadata=json.dumps([p["metadata"] for p in patches]),
        )
        (out / "fixture.json").write_text(
            json.dumps(
                dict(
                    row=row,
                    col=col,
                    months=windows,
                    sha256=sha256(args.fixture),
                    preparation_seconds=time.monotonic() - started,
                    observed_pixels=[int(p["valid"].sum()) for p in patches],
                ),
                indent=2,
            )
            + "\n"
        )
        print("Fixed held-imagery fixture prepared.", flush=True)
        return
    import torch

    with np.load(args.fixture, allow_pickle=False) as f:
        metadata = json.loads(str(f["metadata"]))
        patches = [
            dict(
                values=f["values"][i].copy(),
                valid=f["valid"][i].copy(),
                days=f["days"][i].copy(),
                metadata=meta,
            )
            for i, meta in enumerate(metadata)
        ]
    source = ROOT / "src/eo_encoders.py"
    text = source.read_text()
    before, presto = text.split('        if name == "presto":', 1)
    assert presto.count("pixels.split(128)") == 1 and presto.count("offset * 128") == 4
    presto = presto.replace("pixels.split(128)", "pixels.split(PRESTO_BATCH)")
    presto = presto.replace("offset * 128", "offset * PRESTO_BATCH")
    module = types.ModuleType("src.presto_cpu_probe")
    module.__file__ = str(source)
    module.__package__ = "src"
    module.PRESTO_BATCH = 128
    exec(
        compile(before + '        if name == "presto":' + presto, str(source), "exec"),
        module.__dict__,
    )
    encoder = module.Encoder("presto")
    configurations = [tuple(map(int, item.split(":"))) for item in args.configs]
    if configurations[0] != (128, 2):
        raise ValueError("Begin with the live 128:2 configuration as reference")
    records = []
    vectors = {}
    baseline = {}
    for frames in [1, 12]:
        selected = patches[-frames:]
        for batch, threads in configurations:
            torch.set_num_threads(threads)
            module.PRESTO_BATCH = batch
            durations = []
            repeats = []
            for repeat in range(2):
                started = time.monotonic()
                if batch == 128 and threads == 2 and repeat == 0:
                    profiler = cProfile.Profile()
                    profiler.enable()
                    v = encoder.sequence(selected)
                    profiler.disable()
                    profiler.dump_stats(str(out / f"{args.label}-{frames}frames.prof"))
                    with (out / f"{args.label}-{frames}frames-profile.txt").open("w") as stream:
                        pstats.Stats(profiler, stream=stream).sort_stats("cumtime").print_stats(30)
                else:
                    v = encoder.sequence(selected)
                durations.append(time.monotonic() - started)
                repeats.append(v)
            if batch == 128 and threads == 2:
                baseline[frames] = v
            ref = baseline[frames]
            result = dict(
                frames=frames,
                batch=batch,
                threads=threads,
                seconds=durations,
                finite=bool(np.isfinite(v).all()),
                exact_repeat=bool(np.array_equal(*repeats)),
                relative_l2=float(np.linalg.norm(v - ref) / max(np.linalg.norm(ref), 1e-12)),
                allclose=bool(np.allclose(v, ref, rtol=1e-5, atol=1e-6)),
            )
            vectors[f"f{frames}_b{batch}_t{threads}"] = v
            records.append(result)
            print(json.dumps(result), flush=True)
            (out / (args.label + ".json")).write_text(
                json.dumps(
                    dict(
                        torch=torch.__version__,
                        python=sys.version,
                        fixture_sha256=sha256(args.fixture),
                        source_sha256=sha256(source),
                        cases=records,
                        scope="Engineering only; production worker unchanged; no sampled scientific comparison",
                    ),
                    indent=2,
                )
                + "\n"
            )
            np.savez(out / (args.label + "-vectors.npz"), **vectors)


if __name__ == "__main__":
    main()
