"""Cache parity, deterministic augmentation and full-census batching."""

import importlib.util
import json
import random
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
import torch
from torch.utils.data import DataLoader

from applied_evaluation import CompleteBatches
from applied_fast_data import CachedChips, EpochBatches, UnscaledSteps, fast_loss, make_scaler

ROOT = Path(__file__).resolve().parents[1]


def water_module():
    spec = importlib.util.spec_from_file_location(
        "water_fast_test", ROOT / "scripts/185_run_applied_water.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("task", ["terramind", "prithvi", "galileo", "copernicus"])
def test_actual_cached_inputs_equal_legacy(task):
    w = water_module()
    if task == "copernicus":
        import applied_change_task as w
    name = "radar-change" if task == "copernicus" else "sen1-chip"
    rows = (
        pd.read_parquet(w.PARTITIONS / f"{name}-inventory.parquet")
        .rename(columns={"record": "chip"})
        .iloc[:2]
    )
    path = ROOT / "data/processed/limburg_tensor_cache_v1" / task
    if not path.exists():
        pytest.skip("Held raw tensor cache unavailable")
    fast = CachedChips(rows, task, path)
    old = w.Chips(rows, task, augment=False)
    for i in [0, len(old) - 1]:
        a, b = fast[i], old[i]
        for key in ["x", "y", "temporal", "location", "metadata"]:
            if key in b:
                torch.testing.assert_close(a[key], b[key], rtol=0, atol=0)
        assert a["chip"] == b["chip"] and a["event"] == b["event"]


@pytest.mark.parametrize("task", ["terramind", "prithvi"])
def test_cached_augmentation_reproduces_legacy_draw_order(task):
    w = water_module()
    rows = pd.read_parquet(w.PARTITIONS / "sen1-chip-inventory.parquet").iloc[:5]
    path = ROOT / "data/processed/limburg_tensor_cache_v1" / task
    if not path.exists():
        pytest.skip("Held raw tensor cache unavailable")
    fast = CachedChips(rows, task, path, augment=True, seed=42)
    old = w.Chips(rows, task, augment=True)
    for epoch in [0, 1]:
        fast.set_epoch(epoch)
        random.seed(42 + epoch)
        for batch in CompleteBatches(len(old), 2, 42 + epoch):
            for i in batch:
                a, b = fast[i], old[i]
                torch.testing.assert_close(a["x"], b["x"], rtol=0, atol=0)
                assert torch.equal(a["y"], b["y"])


def test_epoch_batches_preserve_every_example(tmp_path):
    np.save(tmp_path / "x.npy", np.zeros((5, 6, 8, 8), dtype=np.float32))
    np.save(tmp_path / "y.npy", np.zeros((5, 8, 8), dtype=np.int8))
    rows = [{"chip": str(i), "event": "event", "position": i} for i in range(5)]
    (tmp_path / "index.json").write_text(json.dumps({"status": "complete", "rows": rows}))
    dataset = CachedChips(pd.DataFrame(rows), "prithvi", tmp_path, augment=True)
    sampler = EpochBatches(len(dataset), 2, 42, dataset.epoch)
    loader = DataLoader(dataset, batch_sampler=sampler, num_workers=0)
    for epoch in [0, 1]:
        dataset.set_epoch(epoch)
        found = [chip for batch in loader for chip in batch["chip"]]
        expected = [str(i) for batch in CompleteBatches(5, 2, 42 + epoch) for i in batch]
        assert found == expected


def test_fp32_scaler_supports_older_torch():
    assert isinstance(make_scaler(SimpleNamespace(), "cpu", "float32"), UnscaledSteps)
    p = torch.nn.Parameter(torch.tensor(1.0))
    optimizer = torch.optim.SGD([p], lr=0.1)
    scaler = make_scaler(torch, "cpu", "float32")
    scaler.scale(p * 2).backward()
    scaler.step(optimizer)
    assert float(p.detach()) == pytest.approx(0.8)


@pytest.mark.parametrize(
    "task,learner", [("galileo", "linear"), ("prithvi", "native"), ("copernicus", "linear")]
)
def test_fast_ce_preserves_ignore_mask(task, learner):
    torch.manual_seed(42)
    logits = torch.randn(2, 3 if task == "copernicus" else 2, 8, 8)
    labels = torch.randint(0, 2, (2, 8, 8))
    labels[:, 0] = -1
    expected = torch.nn.functional.cross_entropy(logits, labels, ignore_index=-1)
    torch.testing.assert_close(fast_loss(logits, labels, task, learner), expected)


def test_batched_scoring_preserves_event_counts():
    w = water_module()
    torch.manual_seed(42)
    items = []
    for i in range(5):
        items.append(
            dict(
                x=torch.randn(2, 64, 64),
                y=torch.randint(-1, 2, (64, 64)),
                chip=f"chip{i}",
                event=f"event{i % 2}",
                part=0,
            )
        )
    model = torch.nn.Conv2d(2, 2, 1)
    args = SimpleNamespace(task="galileo", learner="linear")
    old = w.score(model, DataLoader(items, batch_size=1), args, torch.device("cpu"))
    fast = w.score(model, DataLoader(items, batch_size=3), args, torch.device("cpu"))
    assert old["confusion"] == fast["confusion"]
    assert old["event_water_iou"] == fast["event_water_iou"]


def test_optimized_lanes_preserve_exact_research_grid():
    spec = importlib.util.spec_from_file_location(
        "optimized_plan_test", ROOT / "scripts/222_prepare_optimized_spatial_queue.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    parent = json.loads(
        (ROOT / "results/applied_study_v3/local-date-recovery-v1/execution-plan.json").read_text()
    )
    plan = module.optimized_plan(parent)
    old = {j["id"]: j for j in parent["jobs"]}
    assert len(plan["jobs"]) == 1961
    assert {j["id"] for j in plan["jobs"]} == set(old)
    neural = [j for j in plan["jobs"] if j["learner"] != "physical"]
    assert len(neural) == 1908
    assert plan["neural_candidate_fits"] == 4876
    assert len({j["output"] for j in neural}) == 1908
    for job in neural:
        previous = old[job["id"]]
        assert all(job[k] == previous[k] for k in ["task", "learner", "fold", "seed", "budget"])
        assert job["worker_lane"] in {"cpu-0", "cpu-1", "mps"}
        assert "--epochs" not in job["command"]
        assert ("--fixed-lr-from" in job["command"]) == (job["budget"] == 1.0 and job["seed"] != 42)
        if job["task"] == "galileo" and job["resource"] == "mps":
            assert "--foreach" not in job["command"]
        assert job["command"][job["command"].index("--data-workers") + 1] == (
            "2" if job["resource"] == "mps" else "0"
        )
        assert job["output"].startswith("results/applied_study_v4/tuning/")
