"""Protect temporal order, state timing and prior-only scale comparisons."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import torch

ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location(
    "strengthen", ROOT / "scripts/75_strengthen_foundation_representations.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_ordered_readout_retains_patch_distinctions_lost_by_mean():
    hidden = torch.tensor([[[[1.0, 0.0], [0.0, 2.0]]]])
    swapped = hidden.flip(dims=[2])
    torch.testing.assert_close(
        MODULE.TTM.pool_patch_states(hidden), MODULE.TTM.pool_patch_states(swapped)
    )
    ordered = MODULE.TTM.pool_patch_states(hidden, "ordered")
    other = MODULE.TTM.pool_patch_states(swapped, "ordered")
    assert not torch.allclose(ordered, other)
    assert ordered.shape == (1, 4)
    torch.testing.assert_close(torch.linalg.vector_norm(ordered, dim=1), torch.ones(1))


def test_discharge_state_contains_no_response_information():
    hours = np.arange(-511, 73)
    values = np.where(hours <= 0, np.linspace(1, 3, len(hours)), 500.0)
    windows = pd.DataFrame(
        {"event_id": "a", "relative_hour": hours, "target_discharge_m3s": values}
    )
    index = pd.DataFrame({"event_id": ["a"], "p99_m3s": [2.0]})
    state = MODULE.discharge_state(index, windows, ["a"])
    windows.loc[windows.relative_hour.gt(0), "target_discharge_m3s"] = 1e9
    pd.testing.assert_frame_equal(state, MODULE.discharge_state(index, windows, ["a"]))
    assert state.loc["a", "onset_over_p99"] == values[511] / 2
    assert state.loc["a", "mean_over_p99"] == np.mean(values[:512]) / 2


def state_fixture():
    candidates = pd.DataFrame({"event_id": ["a", "b", "c"]})
    vectors = pd.DataFrame(
        {"level": [1.0, 3.0, 8.0, 5.0], "variability": [0.01, 0.04, 0.02, 0.03]},
        index=["a", "b", "c", "q"],
    )
    return candidates, vectors


def test_state_scaling_uses_candidates_not_unused_or_future_events():
    candidates, vectors = state_fixture()
    query = SimpleNamespace(event_id="q")
    expected, details = MODULE.BASE.block_distances(
        candidates, query, {"state": vectors}, ("state",)
    )
    extended = pd.concat(
        [vectors, pd.DataFrame({"level": [1e9], "variability": [1e9]}, index=["future"])]
    )
    actual, other = MODULE.BASE.block_distances(candidates, query, {"state": extended}, ("state",))
    pd.testing.assert_series_equal(actual, expected)
    pd.testing.assert_frame_equal(other, details)


def test_robust_state_scaling_keeps_arbitrary_positive_unit_changes_out_of_distance():
    candidates, vectors = state_fixture()
    query = SimpleNamespace(event_id="q")
    expected, _ = MODULE.BASE.block_distances(candidates, query, {"state": vectors}, ("state",))
    vectors["variability"] = vectors.variability * 1000 + 400
    actual, _ = MODULE.BASE.block_distances(candidates, query, {"state": vectors}, ("state",))
    np.testing.assert_allclose(actual, expected)
