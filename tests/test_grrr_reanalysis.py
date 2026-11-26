import json
from copy import deepcopy

import numpy as np
import pandas as pd
import pytest

from src.geoglows_experiment import sha
from src.grrr_reanalysis import VERSION, read_daily_flow


def test_timing_receipt_matches_the_archive_and_preserves_missing_days(tmp_path):
    path = tmp_path / "archive.npz"
    clock_path = tmp_path / "clock.json"
    days = pd.date_range("2024-10-09", periods=2, tz="UTC")
    ids = ["subhybas_1"]
    np.savez(
        path,
        gauge_id=ids,
        valid_start_utc=days.strftime("%Y-%m-%d").to_numpy(dtype=str),
        valid_end_utc=(days + pd.Timedelta(days=1)).strftime("%Y-%m-%d").to_numpy(dtype=str),
        streamflow_m3s=[[2.0, np.nan]],
        valid_discharge=[[True, False]],
    )
    receipt = dict(
        version=VERSION,
        product="reanalysis",
        outlet_audit=[{"gauge_id": ids[0]}],
        provenance=dict(
            version=VERSION,
            url="https://example.org/streamflow.zarr",
            metadata_sha256="metadata",
            objects={"streamflow/c/0/0": {"sha256": "chunk"}},
        ),
    )
    manifest = {**receipt, "output": {"sha256": sha(path)}}
    path.with_suffix(".manifest.json").write_text(json.dumps(manifest))
    clock = dict(
        status="passed",
        daily_windows_equal=True,
        maximum_absolute_difference_m3s=0,
        compared_cells=1,
        reanalysis=deepcopy(receipt),
    )
    clock_path.write_text(json.dumps(clock))
    flow = read_daily_flow(path, clock_path, ids, days)
    assert flow.iloc[0, 0] == 2.0
    assert pd.isna(flow.iloc[1, 0])

    clock["reanalysis"]["provenance"]["objects"]["streamflow/c/0/0"]["sha256"] = "stale chunk"
    clock_path.write_text(json.dumps(clock))
    with pytest.raises(ValueError, match="source or clock receipt"):
        read_daily_flow(path, clock_path, ids, days)
