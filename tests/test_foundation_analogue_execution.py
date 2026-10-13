"""Scientific safeguards for context distances, German clocks and frozen TTM."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).parents[1]


def load(number, filename):
    spec = importlib.util.spec_from_file_location(
        f"execution_{number}", ROOT / "scripts" / f"{number}_{filename}.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BASE = load(65, "hydrological_analogue_baseline")
TTM = load(70, "ttm_analogue_comparison")
GERMAN = load(72, "german_wurm_analogue_extension")


def test_prior_pair_scale_is_known_and_excludes_query():
    candidates = pd.DataFrame({"event_id": ["a", "b"]})
    vectors = pd.DataFrame({"x": [0.0, 4.0, 100.0]}, index=["a", "b", "q"])
    distances, details = BASE.block_distances(
        candidates, SimpleNamespace(event_id="q"), {"x": vectors}
    )
    np.testing.assert_allclose(details.x_prior_scale, 4.0)
    np.testing.assert_allclose(distances, [25.0, 24.0])
    vectors.loc["q"] = 200.0
    _, updated = BASE.block_distances(candidates, SimpleNamespace(event_id="q"), {"x": vectors})
    np.testing.assert_allclose(details.x_prior_scale, updated.x_prior_scale)


def test_repeated_catchment_vectors_do_not_change_distance_scale():
    vectors = pd.DataFrame({"x": [0.0, 0.0, 4.0, 2.0]}, index=["a", "duplicate", "b", "q"])
    _, details = BASE.block_distances(
        pd.DataFrame({"event_id": ["a", "duplicate", "b"]}),
        SimpleNamespace(event_id="q"),
        {"context": vectors},
    )
    np.testing.assert_allclose(details.context_prior_scale, 4.0)


def test_equal_blocks_and_constant_prior_block_are_explicit():
    candidates = pd.DataFrame({"event_id": ["a", "b"]})
    a = pd.DataFrame({"x": [0.0, 4.0, 2.0]}, index=["a", "b", "q"])
    b = pd.DataFrame({"x": [0.0, 0.0, 2.0]}, index=["a", "b", "q"])
    distance, details = BASE.block_distances(
        candidates, SimpleNamespace(event_id="q"), {"a": a, "b": b}
    )
    np.testing.assert_allclose(details.b_prior_scale, 1.0)
    np.testing.assert_allclose(distance, np.sqrt((0.5**2 + 2**2) / 2))


def test_q_only_retrieval_does_not_require_fabricated_rain():
    rows = [
        {
            "event_id": f"e{i}",
            "storm_id": f"s{i}",
            "watercourse": "Wurm",
            "onset_utc": pd.Timestamp("2020-01-01", tz="UTC") + pd.Timedelta(days=i * 4),
            "complete_scoring_sample": True,
            "measurement_concern": False,
            "outcome_peak_over_p99_72h": 1 + i / 10,
            **dict.fromkeys(BASE.FEATURE_COLUMNS, np.nan),
        }
        for i in range(4)
    ]
    signatures = pd.DataFrame(rows)
    vectors = pd.DataFrame({"x": [0.0, 1.0, 2.0, 3.0]}, index=signatures.event_id)
    predictions, neighbors = BASE.retrieve_prior_analogues(
        signatures, top_k=2, min_candidates=2, representation_vectors=vectors
    )
    assert set(predictions.query_event_id) == {"e2", "e3"}
    assert neighbors.analogue_storm_id.ne(neighbors.query_storm_id).all()


def test_german_fixed_clock_and_complete_trailing_hour(tmp_path):
    header = {
        "Station": "Test",
        "Stationsnummer": "123",
        "Gewässer": "Wurm",
        "Parameter": "Abfluss",
        "Einheit": "m³/s",
        "Lebenslauf": "Mittelwerte je 15 Minuten",
        "Zeitangabe": "Rechte Seite des Zeitintervalls mit Intervallwert",
    }
    lines = [f"{k};{v}" for k, v in header.items()] + [f"unused{i};" for i in range(25)]
    for month in [1, 7]:
        path = tmp_path / f"q{month}.csv"
        # Chronological trailing quarter-hour window ending at 01:00 source time.
        path.write_text(
            "\n".join(
                lines
                + [
                    f"01.{month:02d}.2020 {time};{value}"
                    for time, value in [
                        ("00:15:00", "1,0"),
                        ("00:30:00", "2,0"),
                        ("00:45:00", "3,0"),
                        ("01:00:00", "4,0"),
                    ]
                ]
            ),
            encoding="latin1",
        )
        series = GERMAN.read_quarters(path, "123", "Test", "Abfluss")
        hourly = GERMAN.complete_hourly(series)
        assert hourly.index[-1] == pd.Timestamp(f"2020-{month:02d}-01T00:00:00Z")
        assert hourly.iloc[-1] == 2.5
        series.iloc[1] = np.nan
        assert pd.isna(GERMAN.complete_hourly(series).iloc[-1])


def quality_fixture(onset):
    index = pd.date_range(onset, periods=73, freq="h")
    q = pd.Series(10.0, index=index)
    stage = pd.Series(100.0, index=index)
    era = pd.Series("era", index=index)
    period = pd.Series("period", index=index)
    periods = pd.DataFrame(
        {
            "era_id": ["era"],
            "domain_min_m3s": [0.0],
            "domain_max_m3s": [20.0],
            "stage_min_cm": [0.0],
            "stage_max_cm": [200.0],
        }
    )
    return q, stage, era, period, periods, onset


def test_exact_q_score_requires_domain_period_and_measured_stage():
    args = quality_fixture(pd.Timestamp("2020-01-01", tz="UTC"))
    assert GERMAN.quality_for_window(*args)["outcome_score_admissible"]
    args[1].iloc[-1] = 250.0
    assert GERMAN.quality_for_window(*args)["response_out_of_rating_domain"]
    assert not GERMAN.quality_for_window(*args)["outcome_score_admissible"]
    args[1].iloc[-1] = np.nan
    assert not GERMAN.quality_for_window(*args)["response_stage_complete"]
    args[1].iloc[-1] = 100.0
    args[3].iloc[-1] = "new_period"
    assert GERMAN.quality_for_window(*args)["response_crosses_rating_period"]


def test_provisional_response_is_retained_but_not_scored():
    result = GERMAN.quality_for_window(*quality_fixture(pd.Timestamp("2021-07-14", tz="UTC")))
    assert result["provisional_high_flow"] and result["measurement_concern"]
    assert not result["outcome_score_admissible"]


def test_rating_periods_use_fixed_clock_and_pool_recurring_verified_curve():
    periods = GERMAN.read_periods()
    recurring = periods.loc[
        periods.station.eq("herzogenrath1")
        & periods.quality.eq("pre_flood")
        & periods.curve.eq("109")
    ]
    assert recurring.era_id.nunique() == 1
    assert recurring.period_id.nunique() == 2
    assert (
        periods.loc[periods.valid_from_source.eq("2021-07-01"), "valid_from_utc"]
        .eq(pd.Timestamp("2021-06-30T23:00:00Z"))
        .all()
    )


def test_frozen_backbone_is_finite_repeatable_and_batch_invariant():
    pytest.importorskip("torch")
    histories = pd.read_parquet(TTM.RAW.DEFAULT_OUT / "standardized_histories.parquet").iloc[:2]
    first, info = TTM.extract_embeddings(histories, batch_size=1)
    second, _ = TTM.extract_embeddings(histories, batch_size=2)
    assert first.shape == (2, 192)
    assert info["trainable_parameters"] == 0 and info["training"] is False
    assert info["loading_info"]["missing_keys"] == []
    np.testing.assert_allclose(np.linalg.norm(first, axis=1), 1.0, atol=1e-6)
    np.testing.assert_allclose(first, second, atol=1e-6)
    with pytest.raises(ValueError, match="512-hour"):
        TTM.extract_embeddings(histories.iloc[:, :511])
