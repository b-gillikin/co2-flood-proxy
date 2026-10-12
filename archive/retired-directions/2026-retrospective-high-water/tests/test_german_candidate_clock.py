"""Prevent a cross-border hour or quarter-hour aggregation error."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
spec = spec_from_file_location("german_candidate", ROOT / "scripts/57_audit_german_candidate.py")
audit = module_from_spec(spec)
spec.loader.exec_module(audit)


def test_fixed_utc_plus_one_and_right_edge_hour(tmp_path):
    path = tmp_path / "lanuk.csv"
    metadata = "Field;Value\n" * 32
    data = "\n".join(
        [
            "01.01.2021 00:00:00;1,0",
            "01.01.2021 00:15:00;2,0",
            "01.01.2021 00:30:00;3,0",
            "01.01.2021 00:45:00;4,0",
            "01.01.2021 01:00:00;5,0",
        ]
    )
    path.write_text(metadata + data + "\n")
    quarters = audit.read_station(path)
    assert quarters.index[0] == pd.Timestamp("2020-12-31 23:00", tz="UTC")
    hourly = audit.complete_hourly(quarters)
    assert pd.isna(hourly.iloc[0])
    assert hourly.loc[pd.Timestamp("2021-01-01 00:00", tz="UTC")] == 3.5
