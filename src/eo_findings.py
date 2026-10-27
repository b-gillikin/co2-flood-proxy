"""Combine saved nominal uncertainty views without fitting or selecting winners."""

import numpy as np

KEYS = [
    "family",
    "kind",
    "cohort",
    "scenario",
    "analysis",
    "policy",
    "target_k",
    "query_country",
    "reference",
    "challenger",
    "metric",
]


def collapse_intervals(frame):
    """Keep both block-bootstrap views; zero overlap is not an equivalence test."""
    units = {"query_storm_id": "storm", "storm_year": "year"}
    if set(frame.resampling_unit) - set(units):
        raise ValueError("Unexpected resampling unit")
    parts = []
    values = ["difference", "lower", "upper", "query_count", "cluster_count"]
    for unit, label in units.items():
        f = frame[frame.resampling_unit.eq(unit)][KEYS + values]
        if f.duplicated(KEYS).any():
            raise ValueError("Duplicate contrast/unit; check cohorts and pairing")
        parts.append(f.rename(columns={c: label + "_" + c for c in values}))
    out = parts[0].merge(parts[1], on=KEYS, how="outer", validate="one_to_one")
    paired = out.storm_difference.notna() & out.year_difference.notna()
    if not np.allclose(
        out.loc[paired, "storm_difference"], out.loc[paired, "year_difference"], rtol=0, atol=1e-12
    ):
        raise ValueError("Point estimates differ between uncertainty views")
    if not out.loc[paired, "storm_query_count"].eq(out.loc[paired, "year_query_count"]).all():
        raise ValueError("Query counts differ between uncertainty views")
    out["difference"] = out.storm_difference.combine_first(out.year_difference)
    out["query_count"] = out.storm_query_count.combine_first(out.year_query_count)
    finite = np.isfinite(out[["storm_lower", "storm_upper", "year_lower", "year_upper"]]).all(
        axis=1
    )
    negative = out.storm_upper.lt(0) & out.year_upper.lt(0)
    positive = out.storm_lower.gt(0) & out.year_lower.gt(0)
    contains = (
        out.storm_lower.le(0) & out.storm_upper.ge(0) & out.year_lower.le(0) & out.year_upper.ge(0)
    )
    out["nominal_interval_pattern"] = np.select(
        [~finite, negative, positive, contains],
        ["undefined", "both_below_zero", "both_above_zero", "both_include_zero"],
        default="resampling_sensitive",
    )
    return out


def reverse_contrast(frame):
    """Reverse a saved difference and both confidence bounds exactly."""
    out = frame.copy()
    out["reference"], out["challenger"] = frame.challenger, frame.reference
    out["difference"] = -frame.difference
    out["lower"], out["upper"] = -frame.upper, -frame.lower
    return out
