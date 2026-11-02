"""Training-only throughput, batching and memory measurements on real inputs.

Microbenchmarks select execution settings, never models by held-test accuracy.
No fitted states retained. CPU and MPS timings are reported with their device.
"""

import argparse
import importlib.util
import json
import os
import sys
import time
from contextlib import nullcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault(
    "PROJ_DATA", str((ROOT / ".venv-foundation/bin/python").resolve().parents[1] / "share/proj")
)
import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader

from applied_evaluation import CompleteBatches
from applied_execution import atomic
from applied_fast_data import CachedChips, cached_terramind_forward, fast_loss, make_scaler


def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument("--task", required=True)
    p.add_argument("--learner", required=True)
    p.add_argument("--device", required=True)
    p.add_argument("--batches", nargs="+", type=int, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--threads", type=int, default=1)
    p.add_argument("--layout", choices=["contiguous", "channels_last"], default="contiguous")
    p.add_argument("--precision", choices=["float32", "bfloat16", "float16"], default="float32")
    p.add_argument("--foreach", action="store_true")
    p.add_argument("--on-device-pool", action="store_true")
    a = p.parse_args()
    if a.output.exists():
        raise FileExistsError("Version benchmark results")
    prefix = "radar-change" if a.task == "copernicus" else "sen1"
    parts = ROOT / "results/applied_study_v1/evaluation"
    inv = pd.read_parquet(
        parts
        / (
            "radar-change-inventory.parquet"
            if a.task == "copernicus"
            else "sen1-chip-inventory.parquet"
        )
    ).rename(columns={"record": "chip"})
    folds = pd.read_parquet(parts / f"{prefix}-grouped-folds.parquet")
    fold = sorted(folds.fold.unique())[0]
    inv = inv[inv.chip.isin(set(folds.loc[(folds.fold == fold) & (folds.role == "train"), "chip"]))]
    features = {
        "galileo": ROOT / "data/processed/limburg_applied_galileo_spatial_v2",
        "copernicus": ROOT / "data/processed/limburg_copernicus_spatial_v1",
        "terramind": ROOT / "data/processed/limburg_terramind_encoder_v1",
    }.get(a.task)
    if a.learner != "native" or (
        features
        and (
            not (features / "index.json").exists()
            or json.loads((features / "index.json").read_text())["status"] != "completed"
        )
    ):
        features = None
    dataset = CachedChips(
        inv,
        a.task,
        ROOT / "data/processed/limburg_tensor_cache_v1" / a.task,
        feature_cache=features,
    )
    spec = importlib.util.spec_from_file_location(
        "applied_tuning_models", ROOT / "scripts/215_apply_local_spatial_models.py"
    )
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    # Cached Galileo training uses its published token probe, not re-encoding.
    torch.set_num_threads(a.threads)
    device = torch.device(a.device)
    reports = []
    for batch in a.batches:
        torch.manual_seed(42)
        model = None
        optimizer = None
        try:
            if a.task == "galileo" and a.learner == "native":
                from applied_spatial_models import GalileoSpatialProbe

                model = GalileoSpatialProbe()
            else:
                model = m.make_model(a.task, a.learner)
            if a.on_device_pool:
                from applied_fast_pool import install_on_device_pools

                install_on_device_pools(model)
            model.to(device).train()
            if a.layout == "channels_last":
                for layer in model.modules():
                    if isinstance(layer, (torch.nn.Conv2d, torch.nn.ConvTranspose2d)):
                        layer.weight.data = layer.weight.data.contiguous(
                            memory_format=torch.channels_last
                        )
                        layer.register_forward_pre_hook(
                            lambda module, inputs: (
                                (inputs[0].contiguous(memory_format=torch.channels_last),)
                                if inputs[0].ndim == 4
                                else inputs
                            )
                        )
            optimizer = torch.optim.AdamW(
                [p for p in model.parameters() if p.requires_grad],
                lr=1e-3,
                foreach=True if a.foreach else None,
            )
            loader = iter(
                DataLoader(
                    dataset, batch_sampler=CompleteBatches(len(dataset), batch, 42), num_workers=0
                )
            )
            scaler = make_scaler(torch, a.device, a.precision)
            actual_updates = [0]
            optimizer.register_step_post_hook(
                lambda *args, counter=actual_updates: counter.__setitem__(0, counter[0] + 1)
            )
            times = []
            peak = 0
            for _i in range(5):
                t = time.perf_counter()
                item = next(loader)
                optimizer.zero_grad(set_to_none=True)
                x = item["x"].to(device)
                context = (
                    torch.autocast(
                        a.device,
                        dtype=torch.bfloat16 if a.precision == "bfloat16" else torch.float16,
                    )
                    if a.precision != "float32"
                    else nullcontext()
                )
                with context:
                    if a.learner == "native" and a.task == "galileo":
                        output = model(item["features"].to(device))
                    elif a.learner == "native" and a.task == "copernicus":
                        output = model.forward_features(item["features"].unbind(1))
                    elif a.learner == "native" and a.task == "terramind" and features:
                        output = cached_terramind_forward(model, item["features"].to(device))
                    elif a.learner == "native" and a.task == "terramind":
                        model.encoder.eval()
                        output = model({"S2L1C": x[:, :13], "S1GRD": x[:, 13:]}).output
                    elif a.learner == "native":
                        output = model(
                            x,
                            temporal_coords=item["temporal"].to(device),
                            location_coords=item["location"].to(device),
                        ).output
                    else:
                        output = model(x)
                    loss = fast_loss(output, item["loss_y"].to(device), a.task, a.learner)
                scaler.scale(loss).backward()
                scaler.step(optimizer)
                scaler.update()
                if a.device == "mps":
                    torch.mps.synchronize()
                    peak = max(peak, torch.mps.current_allocated_memory())
                times.append(time.perf_counter() - t)
            if not torch.isfinite(loss):
                raise ValueError("Nonfinite profile loss")
            report = dict(
                task=a.task,
                learner=a.learner,
                device=a.device,
                threads=a.threads,
                batch=batch,
                status="passed",
                step_seconds=times,
                steady_median_s=float(np.median(times[1:])),
                examples_per_s=batch / float(np.median(times[1:])),
                sampled_mps_bytes=peak,
                optimizer_updates=actual_updates[0],
                final_loss_scale=scaler.get_scale(),
                cached_encoder=features is not None,
                layout=a.layout,
                precision=a.precision,
                foreach=a.foreach,
                on_device_pool=a.on_device_pool,
            )
        except (RuntimeError, ValueError) as e:
            report = dict(
                task=a.task,
                learner=a.learner,
                device=a.device,
                batch=batch,
                status="failed",
                error=str(e),
            )
        reports.append(report)
        a.output.parent.mkdir(parents=True, exist_ok=True)
        atomic(
            a.output,
            dict(
                profiles=reports,
                scope="Five real training batches per setting, first excluded from steady median; engineering only, no test access or retained model.",
            ),
        )
        print(json.dumps(report), flush=True)
        del model, optimizer
        if a.device == "mps":
            torch.mps.empty_cache()


if __name__ == "__main__":
    main()
