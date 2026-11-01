"""Recovery and coverage regressions for waiting-time preparation."""

import importlib.util
import io
import json
import tarfile
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]


def load(number):
    path = next((ROOT / "scripts").glob(number + "_*.py"))
    spec = importlib.util.spec_from_file_location("script_" + number, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_unknown_qa_does_not_mean_unobserved_spectrum():
    m = load("205")
    x = np.ones((15, 2, 2))
    x[13, 0, 0] = -9999
    assert m.source_support(x, 13).all()
    x[0, 1, 1] = -9999
    assert not m.source_support(x, 13)[1, 1]
    x[-1, 0, 1] = 0
    assert not m.source_support(x, 13)[0, 1]


def test_radar_reference_overlap_keeps_source_uncertainty():
    m = load("205")
    scene = "S1_20210716T054116_20210716T054141"
    assert "overlap candidate" in m.dependence(
        "EMSR520_AOI01", "s1_event", scene, "2021-07-16T05:41:27Z"
    )
    assert "different acquisition time" in m.dependence(
        "EMSR520_AOI01", "s1_event", scene, "2021-07-17T05:41:27Z"
    )
    assert "Different reference sensor" in m.dependence(
        "EMSR517_AOI09", "s1_event", scene, "2021-07-16T05:41:27Z"
    )


def test_execution_rejects_dropped_job_and_duplicated_outputs():
    m = load("206")
    plan = json.loads((ROOT / "results/applied_study_v2/execution-plan.json").read_text())
    assert sum(m.check_plan(plan).values()) == 1961
    plan["jobs"].pop()
    with pytest.raises(ValueError, match="crossproduct"):
        m.check_plan(plan)
    plan["jobs"].append(plan["jobs"][0])
    with pytest.raises(ValueError, match="Duplicate"):
        m.check_plan(plan)


def test_bundle_readback_checks_every_member_and_rejects_changes(tmp_path):
    m = load("207")
    data = b"restored inference checkpoint"
    inventory = {"nested/test.pt": {"bytes": len(data), "sha256": m.digest(io.BytesIO(data))}}

    def write(path, payload):
        with tarfile.open(path, "w:gz") as archive:
            for name, content in [
                ("nested/test.pt", payload),
                ("BUNDLE-INVENTORY.json", json.dumps(inventory).encode()),
            ]:
                member = tarfile.TarInfo(name)
                member.size = len(content)
                archive.addfile(member, io.BytesIO(content))

    good = tmp_path / "good.tar.gz"
    write(good, data)
    m.verify_bundle(good, inventory)
    bad = tmp_path / "bad.tar.gz"
    write(bad, b"x" * len(data))
    with pytest.raises(ValueError, match="hash"):
        m.verify_bundle(bad, inventory)
    with pytest.raises(ValueError, match="existing chapter"):
        m.inventory(["/etc/hosts"])


def test_independent_audit_keeps_unsigned_unknown_negative(tmp_path, monkeypatch):
    m = load("204")
    import pandas as pd
    import rasterio
    from rasterio.transform import from_origin

    folder = tmp_path / "chip"
    folder.mkdir()
    for prefix in ["SL1_IVV", "SL1_IVH", "MS1_IVV", "MS1_IVH", "MK0_MLU", "MK0_MNA"]:
        a = np.ones((2, 2), dtype=np.uint8)
        if prefix == "MK0_MNA":
            a[0, 0] = 0
        with rasterio.open(
            folder / f"{prefix}.tif",
            "w",
            driver="GTiff",
            height=2,
            width=2,
            count=1,
            dtype="uint8",
            transform=from_origin(1, 2, 1, 1),
        ) as dst:
            dst.write(a, 1)
    monkeypatch.setattr(m, "RADAR", tmp_path)
    inventory = pd.DataFrame({"source_path": ["chip"]}, index=["one"])
    label, _ = m.source("one", "copernicus", inventory)
    assert label.dtype == np.int64
    assert label.tolist() == [[-1, 1], [1, 1]]
