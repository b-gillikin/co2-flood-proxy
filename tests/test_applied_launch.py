"""Scientific census, exact input reuse and recovery checks before launch."""

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import rasterio
from rasterio.transform import from_origin

from applied_execution import atomic, retire_verified_checkpoints, sha, verify_completed
from applied_io_cache import galileo_source
from applied_local_inputs import optical_clear, pair_rows, spectral_support
from applied_water import galileo_radar_norm, valid_labels

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_refreshed_plan_keeps_exact_grid_and_declares_first_wave():
    old = json.loads((ROOT / "results/applied_study_v2/execution-plan.json").read_text())
    new = load("213_prepare_spatial_launch.py").refreshed_plan(old)
    assert {r["id"] for r in new["jobs"]} == {r["id"] for r in old["jobs"]}
    assert len({r["output"] for r in new["jobs"]}) == 1961
    neural = [r for r in new["jobs"] if r["learner"] != "physical"]
    assert len(neural) == 1908 and new["neural_candidate_fits"] == 5724
    wave = neural[:16]
    assert len({(r["task"], r["learner"]) for r in wave}) == 16
    assert all(r["budget"] == 1.0 and r["seed"] == 42 for r in wave)
    assert all(r["resource"] == "mps" for r in neural)
    assert new["jobs"] != old["jobs"]
    assert all(r["local_application"] == (r["budget"] == 1.0) for r in neural)


def fixture_fit(tmp_path):
    d = tmp_path / "fit"
    d.mkdir()
    (d / "predictions").mkdir()
    trials = []
    for i, v in enumerate([0.4, 0.7, 0.7]):
        p = d / f"trial-{i}.pt"
        p.write_bytes(f"weights-{i}".encode())
        trials.append(dict(trial=i, status="completed", validation_iou=v, checkpoint_sha256=sha(p)))
    atomic(
        d / "manifest.json",
        dict(
            rates=[1e-4, 1e-3, 1e-2], arguments={"task": "galileo"}, partitions={"test": ["chip"]}
        ),
    )
    atomic(d / "trials.json", trials)
    atomic(d / "selection.json", trials[1])
    atomic(d / "selected-test.json", dict(confusion={"event": [[512 * 512, 0], [0, 0]]}))
    np.savez_compressed(d / "predictions/chip.npz", prediction=np.zeros((512, 512), dtype=np.uint8))
    return d


def test_completion_checks_selection_masks_and_full_prediction_census(tmp_path):
    d = fixture_fit(tmp_path)
    r = verify_completed(d)
    assert r["selected_trial"] == 1 and r["test_predictions"] == 1
    atomic(d / "selection.json", json.loads((d / "trials.json").read_text())[2])
    with pytest.raises(ValueError, match="winner"):
        verify_completed(d)
    atomic(d / "selection.json", json.loads((d / "trials.json").read_text())[1])
    np.savez_compressed(
        d / "predictions/chip.npz", prediction=np.full((512, 512), 255, dtype=np.uint8)
    )
    with pytest.raises(ValueError, match="coverage"):
        verify_completed(d)
    (d / "predictions/chip.npz").unlink()
    with pytest.raises(ValueError, match="census"):
        verify_completed(d)


def test_cleanup_requires_verified_exact_remote_checkpoint(tmp_path):
    d = fixture_fit(tmp_path)
    complete = verify_completed(d)
    atomic(d / "complete.json", complete)
    receipt = tmp_path / "receipt.json"
    inventory = {f"fit/{k}": v for k, v in complete["checkpoints"].items()}
    atomic(receipt, dict(status="uploaded_only", inventory=inventory))
    with pytest.raises(ValueError, match="unverified"):
        retire_verified_checkpoints(d, receipt)
    atomic(receipt, dict(status="remote_readback_and_every_member_verified", inventory=inventory))
    assert len(retire_verified_checkpoints(d, receipt)) == 3
    assert (d / "predictions/chip.npz").exists() and (d / "selected-test.json").exists()


def test_cached_galileo_loader_is_bit_identical_to_original_inputs(tmp_path):
    torch = pytest.importorskip("torch")
    w = load("185_run_applied_water.py")
    label = np.zeros((512, 512), dtype=np.int16)
    label[10:20] = 1
    label[0, 0] = -1
    radar = np.random.default_rng(42).normal(-15, 3, (2, 512, 512)).astype(np.float32)
    radar[0, 1, 1] = np.nan
    for kind, array in [("LabelHand", label[None]), ("S1Hand", radar)]:
        p = tmp_path / kind
        p.mkdir()
        with rasterio.open(
            p / f"chip_{kind}.tif",
            "w",
            driver="GTiff",
            height=512,
            width=512,
            count=len(array),
            dtype=array.dtype,
            transform=from_origin(1, 2, 1, 1),
        ) as ds:
            ds.write(array)
    w.DATA = tmp_path
    rows = pd.DataFrame([dict(chip="chip", event="event", s1_date="2021-07-16")])
    ds = w.Chips(rows, "galileo")
    cached_label, cached_raw = galileo_source(str(tmp_path), "chip")
    expected = valid_labels(label, s1=radar)
    raw = np.nan_to_num(galileo_radar_norm(radar), nan=0.5, posinf=0.5, neginf=0.5)
    np.testing.assert_array_equal(cached_label, expected)
    np.testing.assert_array_equal(cached_raw, raw)
    for part in [0, 7, 30, 63]:
        y, x = (part // 8) * 64, (part % 8) * 64
        r = ds[part]
        torch.testing.assert_close(
            r["x"], torch.from_numpy(raw[:, y : y + 64, x : x + 64]), rtol=0, atol=0
        )
        torch.testing.assert_close(
            r["y"], torch.from_numpy(expected[y : y + 64, x : x + 64]), rtol=0, atol=0
        )


def test_local_pairing_never_uses_future_or_wrong_orbit_and_qa_unknown_stays_unknown():
    base = dict(aoi="a", reference_path="ref", relative_orbit=15, orbit_pass="ASCENDING")
    f = pd.DataFrame(
        [
            dict(base, path=p, sensor=s, acquisition_utc=t, **extra)
            for p, s, t, extra in [
                ("event/grid.tif", "s1_event", "2021-07-16T10:00Z", {}),
                ("old/grid.tif", "s1_pre", "2021-07-10T10:00Z", {}),
                ("future/grid.tif", "s1_pre", "2021-07-17T10:00Z", {}),
                ("opt/grid.tif", "s2_event", "2021-07-16T09:00Z", {}),
            ]
        ]
    )
    cop = pair_rows(f, "copernicus")[0]
    assert cop["paired"]["path"] == "old/grid.tif"
    assert not pair_rows(f, "terramind")[0]["available"]
    a = np.ones((15, 2, 2))
    a[13] = 0
    a[13, 0, 0] = -9999
    a[13, 1, 1] = 1024
    assert spectral_support(a, 13).all()
    assert optical_clear(a).tolist() == [[False, True], [True, False]]


@pytest.mark.parametrize("task", ["galileo", "prithvi", "terramind", "copernicus"])
def test_local_adapter_full_grid_with_matched_physical_control(task, tmp_path, monkeypatch):
    import sys

    torch = pytest.importorskip("torch")
    module = load("215_apply_local_spatial_models.py")
    module.ROOT = tmp_path
    # Preserve real code-provenance hashing in the isolated filesystem fixture.
    script_copy = tmp_path / "scripts/215_apply_local_spatial_models.py"
    script_copy.parent.mkdir()
    script_copy.write_bytes((ROOT / "scripts/215_apply_local_spatial_models.py").read_bytes())
    module.__file__ = str(script_copy)
    for name in [
        "applied_local_inputs.py",
        "applied_spatial_models.py",
        "applied_copernicus.py",
        "applied_mps_pool.py",
    ]:
        target = tmp_path / "src" / name
        target.parent.mkdir(exist_ok=True)
        target.write_bytes((ROOT / "src" / name).read_bytes())
    channel = {"galileo": 2, "prithvi": 6, "terramind": 15, "copernicus": 4}[task]
    classes = 3 if task == "copernicus" else 2
    d = tmp_path / "fit"
    d.mkdir()
    model = torch.nn.Conv2d(channel, classes, 1)
    with torch.no_grad():
        model.weight.zero_()
        model.bias.zero_()
    torch.save(model.state_dict(), d / "trial-0.pt")
    atomic(d / "selection.json", dict(trial=0, checkpoint_sha256=sha(d / "trial-0.pt")))
    atomic(
        d / "manifest.json",
        dict(arguments=dict(task=task, learner="linear", budget=1.0, device="cpu", fold="fold")),
    )
    root = tmp_path / "data/raw/limburg_applied_tasks/local_scenes"
    root.mkdir(parents=True)
    profile = dict(
        driver="GTiff",
        height=512,
        width=512,
        dtype="float32",
        crs="EPSG:32631",
        transform=from_origin(700000, 5600000, 10, 10),
    )
    records = []
    for sensor, stamp in [
        ("s1_pre", "2021-07-01T00:00Z"),
        ("s1_event", "2021-07-15T00:00Z"),
        ("s2_event", "2021-07-16T00:00Z"),
    ]:
        array = np.ones((15 if sensor == "s2_event" else 4, 512, 512), np.float32)
        if sensor == "s2_event":
            array[:13] = 1000
            array[13] = 0
        else:
            array[:2] = -12
            array[2] = 35
        array[-1] = 1
        array[-1, 0, 0] = 0
        path = root / sensor / "grid.tif"
        path.parent.mkdir()
        with rasterio.open(path, "w", count=len(array), **profile) as dst:
            dst.write(array)
        records.append(
            dict(
                path=f"{sensor}/grid.tif",
                aoi="case",
                sensor=sensor,
                scene=sensor,
                acquisition_utc=stamp,
                relative_orbit=15,
                orbit_pass="ASCENDING",
                reference_path="reference.tif",
                reference_offset_hours=6.0,
                reference_dependence="qualified fixture",
            )
        )
    ref = np.zeros((512, 512), np.uint8)
    with rasterio.open(
        tmp_path / "reference.tif", "w", **dict(profile, dtype="uint8", count=1)
    ) as dst:
        dst.write(ref, 1)
    pairs = (
        tmp_path / "results/applied_study_v1/local_references/scoring/scene-reference-pairs.parquet"
    )
    pairs.parent.mkdir(parents=True)
    pd.DataFrame(records).to_parquet(pairs, index=False)
    monkeypatch.setattr(sys, "argv", ["adapter", str(d)])
    module.main()
    manifest = json.loads((d / "local/manifest.json").read_text())
    assert len(manifest) == 1
    with rasterio.open(manifest[0]["prediction"]) as ds:
        y = ds.read(1)
    assert y.shape == (512, 512) and y[0, 0] == 255 and np.all(y[1:] == 0)
    with rasterio.open(manifest[0]["valid"]) as ds:
        assert ds.read(1).sum() == 512 * 512 - 1
    p = tmp_path / f"results/applied_study_v2/physical/{task}-fold"
    p.mkdir(parents=True)
    candidate = (
        dict(method="radar_change", polarization=0, threshold_db=-17, drop_db=3)
        if task == "copernicus"
        else (
            dict(method="radar_dark", polarization=0, threshold_db=-17)
            if task == "galileo"
            else dict(method="mndwi", threshold=0.05)
        )
    )
    if task == "galileo":
        from applied_physical import candidates

        candidate = candidates(task)[0]
    atomic(p / "selection.json", dict(candidate=candidate))
    monkeypatch.setattr(sys, "argv", ["adapter", str(d), "--physical"])
    module.main()
    assert (d / "local-physical/complete.json").exists()


@pytest.mark.parametrize("resume,fail", [(False, False), (True, False), (False, True)])
def test_durable_controller_preserves_census_and_does_not_duplicate_surviving_child(
    tmp_path, monkeypatch, resume, fail
):
    import sys

    module = load("214_queue_spatial_comparisons.py")
    module.ROOT = tmp_path
    source = tmp_path / "source.txt"
    source.write_text("frozen")
    out = tmp_path / "results/applied_study_v3"
    out.mkdir(parents=True)
    output = "results/applied_study_v3/tuning/one"
    d = tmp_path / output
    plan = dict(
        jobs=[
            dict(
                id="one",
                learner="linear",
                task="galileo",
                budget=0.2,
                seed=42,
                fold="fold",
                output=output,
                command=["python", "scripts/192_tune_applied_water.py"],
            )
        ],
        source_hashes={"source.txt": sha(source)},
        cache_index_hashes={},
    )
    pp = out / "plan.json"
    atomic(pp, plan)
    calls = []
    objects = []

    def complete():
        d.mkdir(parents=True, exist_ok=True)
        atomic(d / "complete.json", dict(checkpoints={}))

    if resume:
        q = out / "queue"
        q.mkdir()
        atomic(
            q / "progress.json",
            dict(
                plan_sha256=sha(pp),
                jobs={"one": dict(status="running", phase="fit", output=output, pid=987654)},
                actor=dict(job="one", phase="fit", pid=987654),
                archiver=None,
                source_hashes=plan["source_hashes"],
            ),
        )

    class Child:
        def __init__(self, code=0):
            self.pid = 1000 + len(objects)
            self.code = code
            objects.append(self)

        def poll(self):
            return self.code

    def spawn(command, log):
        calls.append(command)
        log.touch()
        if "scripts/192_tune_applied_water.py" in command:
            if not fail:
                complete()
            return Child(1 if fail else 0)
        if "scripts/217_update_spatial_readout.py" in command:
            p = Path(command[command.index("--output") + 1])
            (p / "local").mkdir(parents=True)
            atomic(p / "local/ledger.json", {})
        elif "scripts/207_preserve_applied_results.py" in command:
            p = Path(command[command.index("--output") + 1])
            p.write_bytes(b"bundle")
            rb = p.with_suffix(".readback.tar.gz")
            rb.write_bytes(b"bundle")
            atomic(
                p.with_suffix(".recovery.json"),
                dict(
                    status="remote_readback_and_every_member_verified",
                    inventory={},
                    local_bundle=str(p),
                    restored_readback=str(rb),
                ),
            )
        return Child()

    monkeypatch.setattr(module, "spawn", spawn)
    monkeypatch.setattr(module.shutil, "which", lambda _: None)

    # Resume has an externally running child on first pass; its receipt appears
    # later. The controller must attach, never enqueue a second copy.
    def sleep(_):
        if resume:
            complete()

    monkeypatch.setattr(module.time, "sleep", sleep)
    monkeypatch.setattr(module, "alive", lambda pid: resume and not (d / "complete.json").exists())
    monkeypatch.setattr(module, "retire_verified_checkpoints", lambda d, r: [])
    monkeypatch.setattr(sys, "argv", ["queue", "--plan", str(pp), "--run"])
    module.main()
    state = json.loads((out / "queue/progress.json").read_text())
    assert state["neural_total"] == 1
    assert state["neural_failed"] == int(fail) and state["neural_completed"] == int(not fail)
    assert sum("scripts/192_tune_applied_water.py" in c for c in calls) == int(not resume)
    if not fail:
        assert state["jobs"]["one"]["offload_status"] == "verified"
    else:
        assert state["status"] == "complete_with_recorded_failures"


def test_local_dates_accept_iso_with_and_without_fractional_seconds():
    rows = []
    for time in ["2021-07-14T10:56:54+00:00", "2021-07-14T10:56:54.700000+00:00"]:
        rows.append(
            dict(
                path=time + "/grid.tif",
                sensor="s2_event",
                aoi="a",
                acquisition_utc=time,
                relative_orbit=np.nan,
                orbit_pass=None,
            )
        )
    pairs = pair_rows(pd.DataFrame(rows), "prithvi")
    assert len(pairs) == 2
    times = sorted(x["primary"]["time"] for x in pairs)
    assert (times[1] - times[0]).total_seconds() == 0.7
