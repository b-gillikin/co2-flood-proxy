"""Check that rainfall defines episodes before discharge can enter the analysis."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
spec = spec_from_file_location(
    "rain_episodes", ROOT / "scripts/53_cross_tributary_rain_episodes.py"
)
analysis = module_from_spec(spec)
spec.loader.exec_module(analysis)


def test_longest_high_run_uses_consecutive_hours():
    assert analysis.longest_true_run([False, True, True, False, True]) == 2
    assert analysis.longest_true_run([False, False]) == 0


def test_episode_separation_and_response_capped_by_next_rain():
    index = pd.date_range("2020-01-01", periods=60, freq="h", tz="UTC")
    values = np.zeros(60)
    values[[2, 3, 15, 17, 31, 32]] = [6, 6, 6, 6, 6, 6]
    rain = pd.DataFrame({"Eyserbeek": values}, index=index)
    episodes = analysis.rain_episodes(rain, dry_gap_hours=12, material_mm_24h=10)
    assert len(episodes) == 2
    assert episodes.iloc[0].rain_start_utc == index[2]
    assert episodes.iloc[0].rain_end_utc == index[17]
    assert episodes.iloc[0].response_end_utc == index[30]
    assert episodes.iloc[1].rain_start_utc == index[31]
    assert episodes.iloc[1].response_end_utc == index[56]
    assert analysis.rain_episodes(rain, dry_gap_hours=24, material_mm_24h=10).shape[0] == 1


def test_footprint_distinguishes_missing_and_preexisting_from_no_onset():
    index = pd.date_range("2020-01-01", periods=5, freq="h", tz="UTC")
    episodes = pd.DataFrame(
        [
            {
                "episode_id": "rain_0001",
                "rain_start_utc": index[1],
                "rain_end_utc": index[2],
                "response_end_utc": index[4],
            }
        ]
    )
    rain = pd.DataFrame({site: [0, 6, 6, 0, 0] for site in analysis.SITES}, index=index)
    states = {
        site: pd.DataFrame(
            {
                "q": [0.5] * 5,
                "p99": [1.0] * 5,
                "valid": [True] * 5,
                "rating_max": [5.0] * 5,
            },
            index=index,
        )
        for site in analysis.SITES
    }
    states["Geul"].loc[index[0] : index[1], "q"] = 1.2
    states["Gulp"].loc[index[1] :, "valid"] = False
    reviewed = pd.DataFrame(
        [
            {
                "watercourse": "Eyserbeek",
                "onset_utc": index[3],
                "review_decision": "include_exact",
                "measurement_concern": False,
            }
        ]
    )
    sites = analysis.footprint(episodes, reviewed, states, rain).set_index("watercourse")
    assert sites.loc["Eyserbeek", "n_reviewed_onsets"] == 1
    assert sites.loc["Geul", "pre_rain_already_high"]
    assert sites.loc["Geul", "any_high_water"]
    assert sites.loc["Geul", "n_reviewed_onsets"] == 0
    assert sites.loc["Gulp", "valid_hour_fraction"] == 0
    assert sites.loc["Worm", "n_reviewed_onsets"] == 0
    assert not sites.loc["Worm", "any_high_water"]
    assert sites.loc["Worm", "valid_hour_fraction"] == 1
