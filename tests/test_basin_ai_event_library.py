import importlib.util
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts/64_build_basin_ai_event_library.py"
SPEC = importlib.util.spec_from_file_location("event_library", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_relative_hours_include_one_cutoff_and_no_future_in_history():
    offsets = MODULE.relative_hours(168, 72)
    assert len(offsets) == 241
    assert offsets[0] == -168
    assert offsets[-1] == 72
    assert (offsets == 0).sum() == 1


def test_real_event_library_has_complete_identity_and_phase_boundary():
    event_index, windows = MODULE.build_event_library(24, 12)
    assert len(event_index) == windows.event_id.nunique()
    assert not windows.duplicated(["event_id", "relative_hour"]).any()
    assert windows.loc[windows.relative_hour <= 0, "evidence_phase"].eq("assessment_history").all()
    assert windows.loc[windows.relative_hour > 0, "evidence_phase"].eq("withheld_outcome").all()
    onset = windows.loc[windows.relative_hour.eq(0)]
    expected = pd.Series(event_index.event_id.unique()).sort_values().tolist()
    observed = onset.event_id.sort_values().tolist()
    assert observed == expected
