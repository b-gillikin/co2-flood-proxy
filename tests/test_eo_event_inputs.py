"""Temporal leakage, exact area support and inherited retrieval contracts."""

import numpy as np
import pandas as pd
import pytest
from shapely.geometry import Polygon, box

from src.eo_comparison import event_vectors, matched_pools, retrieve
from src.eo_event_inputs import (
    aggregate_vectors,
    completed_windows,
    context_id,
    observed_patch_area,
    pixel_area_weights,
)
from src.eo_inputs import standardize, validate_frames


def test_calendar_windows_are_completed_chronological_and_fixed():
    for cutoff in ["2021-07-15T13:00:00+00:00", "2020-03-01T00:00:00+00:00"]:
        for kind, n in [("monthly", 12), ("recent", 4)]:
            windows = completed_windows(cutoff, kind)
            assert len(windows) == n
            assert all(pd.Timestamp(w["end"]) <= pd.Timestamp(cutoff) for w in windows)
            assert all(
                a["end"] == b["start"] for a, b in zip(windows[:-1], windows[1:], strict=True)
            )
            assert context_id(kind, windows) == context_id(kind, completed_windows(cutoff, kind))
    assert (
        completed_windows("2020-03-01T00:00:00+00:00", "monthly")[-1]["start"]
        == "2020-02-01T00:00:00+00:00"
    )
    with pytest.raises(ValueError):
        completed_windows("2020-03-01", "monthly")


def test_exact_area_including_sliver_and_hole():
    polygon = Polygon(
        [(0.2, 0.2), (3.8, 0.2), (3.8, 3.8), (0.2, 3.8)],
        holes=[[(1.2, 1.2), (2.8, 1.2), (2.8, 2.8), (1.2, 2.8)]],
    )
    weights = pixel_area_weights(polygon, [0, 0, 4, 4], 1)
    assert np.isclose(weights.sum(), polygon.area)
    assert np.isclose(weights[0, 0], 0.64)
    sliver = pixel_area_weights(box(0.01, 0, 0.02, 4), [0, 0, 4, 4], 1)
    assert np.isclose(sliver.sum(), 0.04) and (sliver[:, 0] > 0).all()


def test_area_weighting_retains_full_denominator_and_rejects_overlap():
    vector, fraction = aggregate_vectors([[1, 0], [0, 1]], [1, 3], 8)
    np.testing.assert_allclose(vector, [0.25, 0.75])
    assert fraction == 0.5
    assert aggregate_vectors([[1, 2]], [0], 8) == (None, 0)
    with pytest.raises(ValueError, match="double-counted"):
        aggregate_vectors([[1, 2]], [9], 8)
    assert observed_patch_area(np.ones((2, 2)), np.ones((4, 4), bool), 1, 1) == 1


def test_temporal_standardization_preserves_missing_pixels():
    data = np.full((2, 3, 4, 4), 20, dtype="float32")
    valid = np.ones((3, 4, 4), bool)
    valid[1, 0, 0] = False
    value = standardize(data, valid, [10, 20], [5, 10])
    assert value.shape == data.shape and value[0, 0, 0, 0] == 2
    np.testing.assert_array_equal(value[:, 1, 0, 0], [0, 0])


def frame(end, bounds=None, valid=True):
    return {
        "valid": np.full((2, 2), valid),
        "metadata": {
            "window": {"end": end},
            "bounds": bounds or [0, 0, 2, 2],
            "bands": ["VV", "VH"],
            "crs": "EPSG:32632",
            "resolution_m": 1,
        },
    }


def test_sequence_cannot_bridge_missing_frame_or_change_grid():
    a = frame("2020-01-01T00:00:00+00:00")
    b = frame("2020-02-01T00:00:00+00:00")
    assert len(validate_frames([a, b])) == 2
    with pytest.raises(ValueError, match="chronological"):
        validate_frames([b, a])
    with pytest.raises(ValueError, match="Missing frame"):
        validate_frames([a, frame("2020-02-01T00:00:00+00:00", valid=False)])
    with pytest.raises(ValueError, match="grid"):
        validate_frames([a, frame("2020-02-01T00:00:00+00:00", [1, 0, 3, 2])])


def test_model_available_population_survives_missing_other_model():
    vectors = {"a": pd.DataFrame([[1]], index=["x"])}
    available, common = matched_pools(["x", "y"], vectors, ["a", "b"])
    assert available == {"a": ["x"]} and common == []


def test_event_join_is_exact_context_and_catchment():
    obs = pd.DataFrame(
        {
            "observation_id": ["x", "y"],
            "event_id": ["ex", "ey"],
            "cohort": ["high_water"] * 2,
            "catchment_gauge": ["NL", "DE"],
        }
    )
    links = pd.DataFrame(
        {"observation_id": ["x", "y"], "context_id": ["c1", "c2"], "kind": ["monthly"] * 2}
    )
    reps = pd.DataFrame(
        {"context_id": ["c1"], "catchment_gauge": ["NL"], "e0000": [3.0], "e0001": [4.0]}
    )
    result = event_vectors(obs, links, reps, "monthly")
    assert list(result.index) == ["ex"]
    np.testing.assert_allclose(result.iloc[0], [0.6, 0.8])
    with pytest.raises(ValueError, match="Multiple extraction"):
        event_vectors(obs, links, pd.concat([reps, reps]), "monthly")


def sample():
    dates = pd.to_datetime(
        ["2020-01-01", "2020-01-03", "2020-01-05", "2020-01-08", "2020-01-11"], utc=True
    )
    x = pd.DataFrame(
        {
            "event_id": list("abcde"),
            "onset_utc": dates,
            "storm_id": ["s1", "s2", "s1", "s3", "s4"],
            "watercourse": ["A", "B", "A", "B", "A"],
            "country": ["NL", "DE", "NL", "DE", "NL"],
            "physical_river_group": ["A", "B", "A", "B", "A"],
            "complete_scoring_sample": True,
            "measurement_concern": False,
            "outcome_peak_over_p99_72h": [1.0, 2.0, 3.0, 4.0, 5.0],
        }
    )
    v = pd.DataFrame([[1.0, 0], [0, 1], [1.0, 1], [0.5, 0.5], [0.2, 0.8]], index=x.event_id)
    return x, v


def test_existing_retrieval_purges_unfinished_same_storm_and_country_river():
    x, v = sample()
    _, donors = retrieve(x, {"eo": v}, exclude_same_river=True, policy="foreign")
    meta = x.set_index("event_id")
    for r in donors.itertuples():
        q = meta.loc[r.query_event_id]
        a = meta.loc[r.analogue_event_id]
        assert a.onset_utc + pd.Timedelta(hours=72) <= q.onset_utc
        assert (
            a.storm_id != q.storm_id
            and a.country != q.country
            and a.physical_river_group != q.physical_river_group
        )


def test_outcome_values_do_not_rank_donors():
    x, v = sample()
    _, a = retrieve(x, {"eo": v})
    x["outcome_peak_over_p99_72h"] = [55, 2, 88, 6, 10]
    _, b = retrieve(x, {"eo": v})
    pd.testing.assert_frame_equal(a, b)


def test_actual_scoring_uses_exact_five_or_ten_selected_donors():
    from src.eo_comparison import assess_selected, load_script

    evaluator = load_script("84_complete_cross_border_analogues.py", "eo_scoring_test")
    ids = [f"d{i}" for i in range(10)]
    curves = pd.DataFrame(
        np.repeat(np.arange(1, 12, dtype=float)[:, None], 72, axis=1),
        index=[*ids, "q"],
        columns=range(1, 73),
    )
    metadata = pd.DataFrame(
        {
            "physical_river_group": "river",
            "country": "NL",
            "measurement_concern": False,
            "cutoff_q_over_p99_h0": 1.0,
        },
        index=curves.index,
    )
    predictions = pd.DataFrame(
        {
            "query_event_id": ["q"],
            "query_storm_id": ["stormq"],
            "query_onset_utc": [pd.Timestamp("2021-07-14", tz="UTC")],
            "analogue_prediction": [999.0],
        }
    )
    selected = pd.DataFrame({"query_event_id": "q", "analogue_event_id": ids, "rank": range(1, 11)})
    for k, mean in [(5, 3.0), (10, 5.5)]:
        scored, _ = assess_selected(
            predictions, selected[selected["rank"].le(k)], curves, metadata, evaluator
        )
        assert scored.actual_donor_count.iloc[0] == k
        assert scored.analogue_prediction.iloc[0] == mean
        assert scored.estimated_high_water_hours.iloc[0] == 72
        assert "actual_donor_count_x" not in scored.columns
