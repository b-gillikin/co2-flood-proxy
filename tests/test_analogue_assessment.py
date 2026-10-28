import numpy as np
import pandas as pd
import pytest

from src.analogue_assessment import (
    add_context,
    baseline_distance,
    decompose,
    fallback_choice,
    scores,
    selected_rows,
)
from src.analogue_distributions import score_distribution
from src.eo_comparison import load_script


def test_baseline_distances_match_frozen_retrieval_formula():
    b = load_script("65_hydrological_analogue_baseline.py", "distance_validation")
    ids = ["a", "b", "c", "q"]
    f = pd.DataFrame([[0, 1], [1, 2], [3, 6], [9, 10]], index=ids)
    s = f * 3
    c = pd.DataFrame({"event_id": ids[:3]})
    query = pd.Series({"event_id": "q"})
    d, _ = baseline_distance(ids[:3], "q", temporal=f, state=s)
    old, _ = b.block_distances(c, query, {"temporal": f, "state": s}, ("state",))
    np.testing.assert_allclose(d, old, rtol=0, atol=1e-14)
    d, _ = baseline_distance(ids[:3], "q", conventional=f)
    prior = f.loc[ids[:3]]
    iqr = prior.quantile(0.75) - prior.quantile(0.25)
    expected = np.sqrt((((prior - f.loc["q"]) / iqr) ** 2).sum(axis=1))
    np.testing.assert_allclose(d, expected)


def test_context_prior_scaling_is_independent_of_outcomes_and_future_vectors():
    p = np.array([[0.0, 1.0], [1.0, 3.0], [2.0, 5.0]])
    base = np.array([1.0, 2.0, 3.0])
    d, _, _ = add_context(base, 2.0, p, np.array([1.0, 1.0]))
    np.testing.assert_allclose(d, add_context(base, 2.0, p.copy(), np.array([1.0, 1.0]))[0])
    assert np.isfinite(add_context(base, 1.0, np.ones((3, 2)), np.ones(2))[0]).all()


def test_decomposition_is_paired_identity_and_missing_not_zero():
    x = decompose(0.2, 0.4, 0.3)
    assert x["archive_difference"] + x["representation_difference"] == pytest.approx(
        x["total_difference"]
    )
    with pytest.raises(ValueError):
        decompose(0.1, np.nan, 0.3)


def test_selection_distinct_storms_stable_ties_and_fallback():
    c = pd.DataFrame(
        dict(
            event_id=["b", "a", "c"],
            storm_id=["s1", "s1", "s2"],
            onset_utc=pd.to_datetime(["2020-01-01"] * 3, utc=True),
        )
    )
    assert selected_rows(c, [1.0, 1.0, 2.0]).event_id.tolist() == ["a", "c"]
    assert fallback_choice(False, 3) == "full_baseline"
    assert fallback_choice(True, 0) == "full_baseline"
    assert fallback_choice(True, 1) == "augmented"


def test_empirical_scores_agree_with_direct_pairwise_crps():
    a = np.vstack([np.arange(1, 73), np.arange(1, 73) * 2]).astype(float)
    q = np.arange(1, 73) * 1.4
    out = scores(q, a)
    expected = np.abs(a[:, :24] - q[:24]).mean(0) - 0.5 * np.abs(
        a[:, None, :24] - a[None, :, :24]
    ).mean((0, 1))
    assert out["crps_mean_24h"] == pytest.approx(expected.mean())
    assert out["crps_h24"] == pytest.approx(
        score_distribution(q[:24], a[:, :24], [0.5, 0.5]).crps.iloc[-1]
    )
