"""Scientific checks for the bounded event-level footprint model."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import expit

ROOT = Path(__file__).resolve().parents[1]
spec = spec_from_file_location(
    "footprint_model", ROOT / "scripts/55_fit_cross_tributary_footprint.py"
)
model = module_from_spec(spec)
spec.loader.exec_module(model)


def test_working_mean_fit_recovers_bounded_event_probabilities():
    rng = np.random.default_rng(45)
    exposure = rng.normal(size=5000)
    x = np.column_stack([np.ones(len(exposure)), exposure])
    expected = expit(-0.4 + 0.7 * exposure)
    high_sites = rng.binomial(6, expected)
    coefficients, iterations = model.fit_working_binomial(x, high_sites)
    assert iterations < 10
    assert np.allclose(coefficients, [-0.4, 0.7], atol=0.06)
    fitted = 6 * expit(x @ coefficients)
    assert (fitted > 0).all() and (fitted < 6).all()


def test_model_requires_observed_pre_rain_state():
    events = pd.DataFrame(
        [
            {
                "episode_id": "good",
                "n_sites_low_coverage": 0,
                "n_sites_incomplete_rain": 0,
                "n_sites_missing_pre_rain": 0,
                "n_sites_preexisting": 0,
            },
            {
                "episode_id": "missing_prior",
                "n_sites_low_coverage": 0,
                "n_sites_incomplete_rain": 0,
                "n_sites_missing_pre_rain": 1,
                "n_sites_preexisting": 0,
            },
            {
                "episode_id": "already_high",
                "n_sites_low_coverage": 0,
                "n_sites_incomplete_rain": 0,
                "n_sites_missing_pre_rain": 0,
                "n_sites_preexisting": 1,
            },
        ]
    )
    sites = pd.DataFrame(
        {
            "episode_id": ["good", "missing_prior", "already_high"],
            "valid_hour_fraction": [1.0, 1.0, 1.0],
        }
    )
    assert model.eligible_frame(events, sites).episode_id.tolist() == ["good"]
