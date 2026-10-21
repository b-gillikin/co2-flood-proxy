"""Coverage diagnostics; no outcomes, model scoring or new eligibility thresholds."""

import numpy as np
import pandas as pd


def coverage_issues(frame):
    issues = []
    if frame.duplicated(["context_id", "catchment_gauge"]).any():
        issues.append("duplicate_context_catchment")
    columns = ["observed_mean_fraction", "observed_min_fraction", "observed_common_fraction"]
    if not np.isfinite(frame[columns].to_numpy(float)).all():
        issues.append("nonfinite_coverage")
    if ((frame[columns] < -1e-7) | (frame[columns] > 1 + 1e-7)).any().any():
        issues.append("coverage_outside_full_catchment")
    if (frame.observed_min_fraction > frame.observed_mean_fraction + 1e-7).any():
        issues.append("minimum_exceeds_mean")
    if (frame.observed_common_fraction > frame.observed_min_fraction + 1e-7).any():
        issues.append("common_exceeds_minimum")
    return issues


def membership_table(base_ids, available, required):
    """Retain missing models explicitly; never label an available-model subset all-model."""
    table = pd.DataFrame(index=pd.Index(sorted(base_ids), name="event_id"))
    for model in required:
        table[model] = table.index.isin(available.get(model, []))
    table["common"] = table[required].all(axis=1)
    return table.reset_index()


def donor_support(population, scenario="all_rivers", policy="pooled", quality=False):
    """Count eligible storm groups before outcome-blind ranking, with existing rules."""
    population = population.copy()
    if quality:
        population = population.loc[~population.measurement_concern]
    if population.empty:
        return pd.DataFrame(columns=["event_id", "candidate_events", "candidate_storms"])
    # Query rows × candidate columns; no distances or outcomes enter this matrix.
    time = population.start_utc.map(lambda t: t.timestamp()).to_numpy()
    ids = population.event_id.to_numpy()
    storms = population.storm_id.to_numpy()
    mask = (
        (time[None, :] + 72 * 3600 <= time[:, None])
        & (time[None, :] < time[:, None])
        & (storms[None, :] != storms[:, None])
        & (ids[None, :] != ids[:, None])
    )
    if scenario == "other_rivers":
        rivers = population.physical_river_group.to_numpy()
        mask &= rivers[None, :] != rivers[:, None]
    if policy != "pooled":
        country = population.country.to_numpy()
        same = country[None, :] == country[:, None]
        mask &= same if policy == "domestic" else ~same
    groups = np.stack([mask[:, storms == storm].any(axis=1) for storm in pd.unique(storms)])
    return pd.DataFrame(
        {
            "event_id": ids,
            "candidate_events": mask.sum(axis=1),
            "candidate_storms": groups.sum(axis=0),
        }
    )
