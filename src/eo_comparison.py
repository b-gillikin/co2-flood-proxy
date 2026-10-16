"""Adapters to the existing analogue retrieval; never rank by withheld outcomes."""

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def load_script(name, label):
    spec = importlib.util.spec_from_file_location(label, ROOT / "scripts" / name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def unit_vectors(frame):
    values = frame.to_numpy(float)
    norm = np.linalg.norm(values, axis=1)
    if not np.isfinite(values).all() or (norm == 0).any():
        raise ValueError("Finite nonzero EO vectors required")
    return pd.DataFrame(values / norm[:, None], index=frame.index, columns=frame.columns)


def matched_pools(base_ids, model_vectors, required_models):
    """Missing models never silently disappear from the all-model comparison."""
    common = set(base_ids)
    for model in required_models:
        common &= set(model_vectors.get(model, pd.DataFrame()).index)
    available = {m: sorted(set(base_ids) & set(v.index)) for m, v in model_vectors.items()}
    return available, sorted(common)


def retrieve(sample, blocks=None, *, exclude_same_river=False, quality=False, policy="pooled"):
    baseline = load_script("65_hydrological_analogue_baseline.py", "eo_baseline")
    return baseline.retrieve_prior_analogues(
        sample,
        top_k=10,
        min_candidates=1,
        min_candidate_storms=1,
        allow_short_archive=True,
        distance_blocks=blocks,
        robust_distance_blocks=("state",) if blocks and "state" in blocks else (),
        exclude_same_river=exclude_same_river,
        exclude_measurement_concerns=quality,
        donor_country=policy,
    )


def event_vectors(observations, links, representations, kind, cohort="high_water"):
    """One exact context/catchment join per observation; no nearest-date substitute."""
    contexts = links[links.kind.eq(kind)][["observation_id", "context_id"]].drop_duplicates()
    chosen = observations[observations.cohort.eq(cohort)].merge(
        contexts, on="observation_id", validate="one_to_one"
    )
    features = [c for c in representations if c.startswith("e") and c[1:].isdigit()]
    if not features:
        return pd.DataFrame()
    if representations.duplicated(["context_id", "catchment_gauge"]).any():
        raise ValueError(
            "Multiple extraction runs for one context/catchment; choose one explicitly"
        )
    joined = chosen.merge(
        representations, on=["context_id", "catchment_gauge"], how="inner", validate="many_to_one"
    )
    values = joined.set_index("event_id")[features].dropna()
    return unit_vectors(values)


def assess_selected(predictions, selected, response, metadata, evaluator):
    """Existing response scores plus phase evidence for this exact donor count."""
    evaluated, details = evaluator.C.assess(predictions, selected, response, metadata)
    phases = pd.DataFrame(
        [
            {
                "query_event_id": eid,
                **evaluator.E.phase_evidence(
                    response.loc[eid],
                    response.loc[g.analogue_event_id],
                    metadata.loc[eid, "cutoff_q_over_p99_h0"],
                ),
            }
            for eid, g in selected.groupby("query_event_id")
        ]
    )
    overlap = (set(phases.columns) & set(evaluated.columns)) - {"query_event_id"}
    if overlap:
        raise ValueError("Duplicate phase evidence fields: " + str(sorted(overlap)))
    return evaluated.merge(phases, on="query_event_id", validate="one_to_one"), details
