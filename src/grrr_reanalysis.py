"""Read verified GRRR daily means on the pinned November 2026 archive clock."""

import json

import numpy as np
import pandas as pd

from src.geoglows_experiment import sha

VERSION = "distributed_model_2026_11"


def same_source(clock, archive):
    """Bind the timing check to the same release and shared source objects."""
    checked = clock["provenance"]
    used = archive["provenance"]
    fields = ("version", "url", "metadata_sha256")
    shared = checked["objects"].keys() & used["objects"].keys()
    return (
        all(checked[key] == used[key] for key in fields)
        and any(key.startswith("streamflow/") for key in shared)
        and all(
            checked["objects"][key]["sha256"] == used["objects"][key]["sha256"] for key in shared
        )
    )


def read_daily_flow(path, clock_path, ids, days):
    clock = json.loads(clock_path.read_text())
    manifest = json.loads(path.with_suffix(".manifest.json").read_text())
    check = clock["reanalysis"]
    if (
        clock["status"] != "passed"
        or not clock["daily_windows_equal"]
        or clock["maximum_absolute_difference_m3s"] != 0
        or clock["compared_cells"] <= 0
        or check["version"] != VERSION
        or check["product"] != "reanalysis"
        or [x["gauge_id"] for x in check["outlet_audit"]] != ids
        or manifest["version"] != VERSION
        or manifest["product"] != "reanalysis"
        or [x["gauge_id"] for x in manifest["outlet_audit"]] != ids
        or not same_source(check, manifest)
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
