#!/usr/bin/env python3
"""Independently reconstruct cross-border pair metrics and saved country means.

Verifies inputs/outputs before reading; no retrieval, labels or empirical changes.
"""

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "m", root / "scripts/84_complete_cross_border_analogues.py"
)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
out = m.OUT
manifest = json.loads((out / "manifest.json").read_text())
for name, digest in manifest["input_sha256"].items():
    assert m.E.S.TTM.sha256(root / name) == digest, name
for name, digest in manifest["source_sha256"].items():
    assert m.E.S.TTM.sha256(root / name) == digest, name
for name, digest in manifest["outputs_sha256"].items():
    assert m.E.S.TTM.sha256(out / name) == digest, name
_, _, index, windows = m.C.REVIEW.load_inputs()
response, _, _ = m.C.CENSUS.load_curves(index, windows)
fields = ["query_event_id", "analogue_event_id", *m.C.CENSUS.METRICS]
maximum = 0.0
count = 0
for chunk in pd.read_csv(
    out / "selected_donors.csv", usecols=fields, chunksize=10000, float_precision="round_trip"
):
    q = response.loc[chunk.query_event_id].to_numpy(float)
    d = response.loc[chunk.analogue_event_id].to_numpy(float)
    qp = q.max(axis=1)
    dp = d.max(axis=1)
    checks = {
        "level_rmse_p99": np.sqrt(((q - d) ** 2).mean(axis=1)),
        "peak_scaled_shape_rmse": np.sqrt(((q / qp[:, None] - d / dp[:, None]) ** 2).mean(axis=1)),
        "peak_time_difference_h": abs(q.argmax(axis=1) - d.argmax(axis=1)),
        "high_water_duration_difference_h": abs((q >= 1).sum(axis=1) - (d >= 1).sum(axis=1)),
        "excess_area_difference_p99_h": abs(
            np.maximum(q - 1, 0).sum(axis=1) - np.maximum(d - 1, 0).sum(axis=1)
        ),
        "terminal_peak_ratio_difference": abs(
            q[:, -24:].mean(axis=1) / qp - d[:, -24:].mean(axis=1) / dp
        ),
    }
    for metric, expected in checks.items():
        delta = float(np.max(abs(chunk[metric].to_numpy() - expected)))
        maximum = max(maximum, delta)
        assert delta <= 1e-12, (metric, delta)
    count += len(chunk)
summary = pd.read_csv(out / "summary_by_country.csv", float_precision="round_trip")
rows = pd.read_csv(out / "event_assessments.csv", float_precision="round_trip")
keys = ["cohort", "scenario", "analysis", "policy", "arm", "target_k", "query_country"]
expected = rows.groupby(keys)[m.METRICS].mean().sort_index()
saved = summary.set_index(keys)[m.METRICS].sort_index()
np.testing.assert_allclose(expected, saved, rtol=0, atol=1e-12)
receipt = {
    "independently_reconstructed_pair_slots": count,
    "maximum_pair_metric_difference": maximum,
    "summary_rows_reconstructed": len(summary),
    "input_output_hashes": "pass",
    "source_hashes": "pass",
    "audit_source_sha256": m.E.S.TTM.sha256(Path(__file__)),
    "run_manifest_sha256": m.E.S.TTM.sha256(out / "manifest.json"),
}
(out / "independent_pair_audit.json").write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps(receipt))
