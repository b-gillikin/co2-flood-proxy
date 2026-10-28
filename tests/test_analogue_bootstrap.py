import numpy as np
import pandas as pd
import pytest

from src.analogue_bootstrap import joint_intervals
from src.eo_followup import cluster_intervals_multi


def test_joint_matrix_bootstrap_matches_existing_chunked_draws():
    rng = np.random.default_rng(77)
    f = pd.DataFrame(rng.normal(size=(67, 6)), columns=list("abcdef"))
    f["storm"] = ["s" + str(i % 13) for i in range(len(f))]
    old = cluster_intervals_multi(f, "storm", list("abcdef"), draws=9999, seed=20261013)
    new = joint_intervals(f, "storm", list("abcdef"), draws=9999, seed=20261013)
    for col in old:
        for key in old[col]:
            assert new[col][key] == pytest.approx(old[col][key], abs=1e-12)


def test_single_cluster_is_undefined_and_missing_is_rejected():
    f = pd.DataFrame({"storm": ["a", "a"], "error": [1.0, 2.0]})
    assert np.isnan(joint_intervals(f, "storm", ["error"])["error"]["lower"])
    f.loc[0, "error"] = np.nan
    with pytest.raises(ValueError):
        joint_intervals(f, "storm", ["error"])
