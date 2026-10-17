"""Bounded CPU/MPS engineering comparison on actual held model inputs.

No census extraction, fitting or model ranking. An isolated adapter leaves live
CPU hashes unchanged. The controller suspends/resumes one CPU job in finally.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.eo_inputs import ROUTES, get_patch, patch_origins, read_tile, sha256

OUT = ROOT / "logs/eo-mps-benchmark"
NATIVE = {"olmoearth", "galileo", "prithvi", "anysat", "presto"}


def module_at(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def prepare_adapter():
    helper = module_at("eo_device_overlay", ROOT / "infrastructure/eo_census/prepare_cloud.py")
    text = helper.gpu_overlay((ROOT / "src/eo_encoders.py").read_text())
    text = text.replace("HERE = Path(__file__).resolve().parents[1]", f"HERE = Path({str(ROOT)!r})")
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / "device_adapter.py"
    target.write_text(text)
    return target


def worker(model):
    import gc

    import numpy as np
    import torch

    if not torch.backends.mps.is_available():
        raise RuntimeError("MPS unavailable in this runtime")
    product, size, _ = ROUTES[model]
    jobs = json.loads((ROOT / "data/raw/limburg_compact_eo/jobs.json").read_text())
    index = {(j["window"]["id"], tuple(j["bounds"]), j["product"]): j for j in jobs}
    bounds = (297600, 5625600, 307200, 5635200)
    windows = [f"monthly_2018{m:02d}01_2018{m + 1:02d}01" for m in range(1, 12)] + [
        "monthly_20181201_20190101"
    ]
    tiles = [
        read_tile(ROOT / "data/raw/limburg_compact_eo", index[(w, bounds, product)], index)
        for w in windows
    ]
    cases = []
    for frames in [1, 12]:
        selected = tiles[-frames:]
        origins = patch_origins(selected[0], size)
        scores = [
            (
                min(int(t.valid[row : row + size, col : col + size].sum()) for t in selected),
                (row, col),
            )
            for row, col in origins
        ]
        positive = sorted((n, rc) for n, rc in scores if n > 0)
        if not positive:
            raise ValueError("Fixture has no complete observed patch")
        candidates = [("most_observed", positive[-1][1])]
        partial = [(n, rc) for n, rc in positive if n < size * size]
        if partial:
            rc = partial[len(partial) // 2][1]
            if rc != candidates[0][1]:
                candidates.append(("partial", rc))
        for label, (row, col) in candidates:
            cases.append(
                (f"{frames}_frames_{label}", [get_patch(t, row, col, size) for t in selected])
            )
    record = {
        "model": model,
        "torch": torch.__version__,
        "device_checks": {},
        "cases": {},
        "source_adapter_sha256": sha256(ROOT / "src/eo_encoders.py"),
        "probe_adapter_sha256": sha256(OUT / "device_adapter.py"),
        "fallback_enabled": os.environ.get("PYTORCH_ENABLE_MPS_FALLBACK", "0"),
    }
    vectors = {}
    project_package = sys.modules["src"]
    project_inputs = sys.modules["src.eo_inputs"]
    for device in ["cpu", "mps"]:
        os.environ["LIMBURG_EO_DEVICE"] = device
        # AnySat/Copernicus upstream packages also use src; restore the project
        # namespace between the two independent device builds.
        for key in list(sys.modules):
            if key == "src" or key.startswith("src."):
                del sys.modules[key]
        sys.modules["src"] = project_package
        sys.modules["src.eo_inputs"] = project_inputs
        sys.path.insert(0, str(ROOT))
        adapter = module_at("src.eo_mps_probe_" + device, OUT / "device_adapter.py")
        encoder = adapter.Encoder(model)
        for label, patches in cases:
            times = []
            outputs = []
            for _repeat in range(4):
                if device == "mps":
                    torch.mps.synchronize()
                start = time.perf_counter()
                v = encoder.sequence(patches)
                if device == "mps":
                    torch.mps.synchronize()
                times.append(time.perf_counter() - start)
                outputs.append(v)
            vectors[(device, label)] = outputs[-1]
            record["cases"].setdefault(
                label,
                {
                    "frames": len(patches),
                    "valid_fractions": [p["metadata"]["valid_fraction"] for p in patches],
                },
            )[device] = {
                "cold_seconds": times[0],
                "warm_seconds": times[1:],
                "median_warm_seconds": float(np.median(times[1:])),
                "dimension": len(v),
                "finite": bool(np.isfinite(v).all()),
                "repeat_max_absolute_difference": float(
                    max(np.max(np.abs(x - outputs[-1])) for x in outputs)
                ),
            }
        del encoder, adapter
        gc.collect()
        if device == "mps":
            torch.mps.empty_cache()
    for label, _patches in cases:
        a, b = vectors[("cpu", label)], vectors[("mps", label)]
        result = record["cases"][label]
        result["comparison"] = {
            "same_shape": a.shape == b.shape,
            "relative_l2": float(np.linalg.norm(a - b) / max(float(np.linalg.norm(a)), 1e-12)),
            "cosine": float(
                np.dot(a, b) / max(float(np.linalg.norm(a) * np.linalg.norm(b)), 1e-12)
            ),
            "max_absolute_difference": float(np.max(np.abs(a - b))),
            "allclose": bool(np.allclose(a, b, rtol=1e-3, atol=1e-5)),
            "warm_speedup": result["cpu"]["median_warm_seconds"]
            / result["mps"]["median_warm_seconds"],
        }
    (OUT / f"{model}.json").write_text(json.dumps(record, indent=2, allow_nan=False) + "\n")
    print(json.dumps(record, allow_nan=False), flush=True)


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--worker", choices=list(ROUTES))
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--pause-pid", type=int)
    args = parser.parse_args()
    if args.worker:
        worker(args.worker)
        return 0
    if not args.run:
        print("Actual-input CPU/MPS tests for ten models; explicit --run and --pause-pid required.")
        return 0
    if not args.pause_pid:
        parser.error("A CPU slot must be paused explicitly")
    prepare_adapter()
    command = subprocess.check_output(
        ["ps", "-p", str(args.pause_pid), "-o", "command="], text=True
    )
    if "100_extract_limburg_eo_sequences.py --model dofa --run" not in command:
        raise ValueError("Pause PID is not the identified DOFA census worker")
    state = {
        "status": "running",
        "pause_pid": args.pause_pid,
        "models": {},
        "scope": "Engineering fixtures; no scientific ranking",
    }

    def save():
        tmp = OUT / "progress.partial"
        tmp.write_text(json.dumps(state, indent=2) + "\n")
        tmp.replace(OUT / "progress.json")

    def interrupted(signum, frame):
        raise KeyboardInterrupt()

    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    os.kill(args.pause_pid, signal.SIGSTOP)
    save()
    try:
        for model in [
            "terramind",
            "dofa",
            "croma",
            "prithvi",
            "copernicus_fm",
            "satmae",
            "olmoearth",
            "galileo",
            "anysat",
            "presto",
        ]:
            state["current_model"] = model
            save()
            env = {
                **os.environ,
                "PYTORCH_ENABLE_MPS_FALLBACK": "0",
                "MPLCONFIGDIR": "/tmp/limburg-eo-matplotlib",
            }
            runtime = ROOT / f".venvs-eo/{ROUTES[model][2]}/bin/python"
            with (OUT / f"{model}.log").open("w") as output:
                child = subprocess.Popen(
                    [str(runtime), "-u", str(Path(__file__).resolve()), "--worker", model],
                    cwd=ROOT,
                    env=env,
                    stdout=output,
                    stderr=subprocess.STDOUT,
                )
                try:
                    code = child.wait(timeout=300)
                    state["models"][model] = {"exit_code": code}
                except subprocess.TimeoutExpired:
                    state["models"][model] = {
                        "exit_code": 124,
                        "error": "Five-minute engineering timeout",
                    }
                finally:
                    if child.poll() is None:
                        child.kill()
                        child.wait()
            save()
        state["status"] = "completed"
    except BaseException:
        state["status"] = "interrupted"
        raise
    finally:
        os.kill(args.pause_pid, signal.SIGCONT)
        state["cpu_job_resumed"] = True
        save()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
