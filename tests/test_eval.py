"""Offline checks for discharge-label evaluation and July anomaly helpers."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.eval import (
    deduplicate_event_episodes,
    hourly_discharge_soft_labels,
    sustained_exceedance_events,
)
from src.models.july import anomaly_table, contiguous_blocks, robust_zscore


def ascending_discharge(with_gap=False):
    """One gauge with strictly ascending values so p90 exceedance is the tail."""
    index = pd.date_range("2025-01-01", periods=100, freq="h", tz="UTC")
    values = np.arange(100, dtype=float)
    if with_gap:
        values[95] = np.nan
    return pd.DataFrame({"discharge_test_m3s": values}, index=index)


class SoftLabelTests(unittest.TestCase):
    """Missing discharge must not read as calm conditions."""

    def test_unobserved_hours_get_nan_labels(self):
        discharge = ascending_discharge(with_gap=True)
        labels = hourly_discharge_soft_labels(discharge, quantiles=(0.90,))

        gap_hour = discharge.index[95]
        high_hour = discharge.index[99]
        low_hour = discharge.index[0]

        self.assertTrue(pd.isna(labels.loc[gap_hour, "test_current_level"]))
        self.assertEqual(labels.loc[high_hour, "test_current_level"], 1.0)
        self.assertEqual(labels.loc[low_hour, "test_current_level"], 0.0)

    def test_antecedent_max_skips_missing_hours(self):
        discharge = ascending_discharge(with_gap=True)
        labels = hourly_discharge_soft_labels(
            discharge, quantiles=(0.90,), antecedent_windows=(24,)
        )
        # The last hour's 24h antecedent window contains the gap but also
        # observed exceedance hours, so the maximum must still be 1.
        self.assertEqual(labels.iloc[-1]["test_antecedent_24h_level"], 1.0)


class SustainedEventTests(unittest.TestCase):
    """Exceedance runs must not bridge coverage gaps."""

    def test_contiguous_exceedance_is_one_event(self):
        events = sustained_exceedance_events(
            ascending_discharge(),
            quantiles=(0.90,),
            min_duration_hours=7,
        )
        self.assertEqual(len(events), 1)
        self.assertEqual(events.iloc[0]["duration_hours"], 10)

    def test_missing_hour_splits_the_run(self):
        events = sustained_exceedance_events(
            ascending_discharge(with_gap=True),
            quantiles=(0.90,),
            min_duration_hours=7,
        )
        # The NaN hour splits the exceedance tail into 6h + 4h fragments,
        # both below the 7-hour minimum duration.
        self.assertEqual(len(events), 0)


class EpisodeDeduplicationTests(unittest.TestCase):
    """Overlapping gauge/quantile rows collapse into physical episodes."""

    def test_overlapping_rows_merge(self):
        start = pd.Timestamp("2025-06-01 00:00", tz="UTC")
        events = pd.DataFrame(
            {
                "source": ["discharge_a_m3s", "discharge_a_m3s", "discharge_b_m3s", "discharge_a_m3s"],
                "threshold_quantile": [0.90, 0.95, 0.90, 0.90],
                "start_timestamp_utc": [
                    start,
                    start + pd.Timedelta(hours=2),
                    start + pd.Timedelta(hours=5),
                    start + pd.Timedelta(days=10),
                ],
                "end_timestamp_utc": [
                    start + pd.Timedelta(hours=12),
                    start + pd.Timedelta(hours=8),
                    start + pd.Timedelta(hours=20),
                    start + pd.Timedelta(days=10, hours=6),
                ],
            }
        )
        episodes = deduplicate_event_episodes(events)

        self.assertEqual(len(episodes), 2)
        first = episodes.iloc[0]
        self.assertEqual(first["n_source_events"], 3)
        self.assertEqual(first["n_sources"], 2)
        self.assertEqual(first["max_threshold_quantile"], 0.95)
        self.assertEqual(first["end_timestamp_utc"], start + pd.Timedelta(hours=20))
        self.assertEqual(episodes.iloc[1]["n_source_events"], 1)

    def test_empty_catalogue(self):
        episodes = deduplicate_event_episodes(pd.DataFrame())
        self.assertTrue(episodes.empty)


class AnomalyScoreTests(unittest.TestCase):
    """Shared scoring helpers behave sensibly at the edges."""

    def test_anomaly_table_flags_outlier_and_skips_nan(self):
        index = pd.date_range("2025-01-01", periods=50, freq="h", tz="UTC")
        score = np.zeros(50)
        score[10] = 10.0
        score[20] = np.nan
        table = anomaly_table(index, score, prefix="demo")

        self.assertTrue(bool(table.loc[10, "demo_anomaly"]))
        self.assertFalse(bool(table.loc[20, "demo_anomaly"]))
        self.assertEqual(int(table["demo_anomaly"].sum()), 1)

    def test_robust_zscore_uses_reference_sample(self):
        z = robust_zscore([2.0, 12.0], reference=[0.0, 1.0, 2.0, 3.0, 4.0])
        self.assertAlmostEqual(float(z.iloc[0]), 0.0)
        self.assertAlmostEqual(float(z.iloc[1]), 0.6745 * 10.0, places=6)

    def test_contiguous_blocks_split_and_filter(self):
        early = pd.date_range("2025-01-01 00:00", periods=6, freq="h", tz="UTC")
        late = pd.date_range("2025-01-02 00:00", periods=12, freq="h", tz="UTC")
        blocks = contiguous_blocks(early.append(late))
        self.assertEqual([len(index) for _, index in blocks], [6, 12])

        filtered = contiguous_blocks(early.append(late), min_hours=8)
        self.assertEqual([len(index) for _, index in filtered], [12])


if __name__ == "__main__":
    unittest.main()
