"""Read verified GRRR daily means on the pinned November 2026 archive clock."""

import json

import numpy as np
import pandas as pd

from src.geoglows_experiment import sha

VERSION = "distributed_model_2026_11"


def read_daily_flow(path, clock_path, ids, days):
    clock = json.loads(clock_path.read_text())
    manifest = json.loads(path.with_suffix(".manifest.json").read_text())
    if (
        clock["status"] != "passed"
        or not clock["daily_windows_equal"]
        or clock["maximum_absolute_difference_m3s"] != 0
        or clock["compared_cells"] <= 0
        or clock["reanalysis"]["version"] != VERSION
        or [x["gauge_id"] for x in clock["reanalysis"]["outlet_audit"]] != ids
        or manifest["version"] != VERSION
        or manifest["product"] != "reanalysis"
        or manifest["output"]["sha256"] != sha(path)
    ):
        raise ValueError("Google source or clock receipt failed verification")
    with np.load(path, allow_pickle=False) as z:
        start = pd.to_datetime(z["valid_start_utc"], utc=True)
        end = pd.to_datetime(z["valid_end_utc"], utc=True)
        values, valid = z["streamflow_m3s"], z["valid_discharge"]
        if (
            z["gauge_id"].tolist() != ids
            or not start.equals(days)
            or not end.equals(days + pd.Timedelta(days=1))
            or values.shape != (len(ids), len(days))
            or not np.array_equal(valid, np.isfinite(values) & (values >= 0))
        ):
            raise ValueError("Unexpected Google outlet, date support or flow validity")
        return pd.DataFrame(np.where(valid, values, np.nan).T, index=start, columns=ids)
