"""Tests for the regionalisation analysis logic.

Every defect found in this repository on 2026-08-06 was in analysis-script code
of exactly this kind, while the test suite guarded loaders that were fine. Each
test below corresponds to a specific bug that reached results:

- coordinates matched by fuzzy name tokens, misplacing 18 of 57 gauges;
- managed structures left in, giving a negative baseflow index;
- zero sentinels averaged into hourly means;
- a best-lag search reported without calibrating its own selection bias.
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def load_similarity_module():
    """Import the numbered script, whose name is not a valid identifier."""
    spec = importlib.util.spec_from_file_location(
        "similarity", ROOT / "scripts" / "23_catchment_similarity.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


sim = load_similarity_module()


class StructureFilterTests(unittest.TestCase):
    """A weir gauge measures a controlled release, not a catchment response."""

    def setUp(self):
        self.clean = pd.Series([1.0, 1.2, 0.9, 1.1] * 30)

    def test_flags_managed_structures_by_name(self):
        for name in (
            "Kwistbeek, Stuw Ingweg",
            "Everlose Beek, Duiker Eindhovenseweg",
            "Peelkanaal, Verdeelwerk De Halte",
            "Weteringbeek, Inlaat",
        ):
            self.assertTrue(sim.is_structure(name, self.clean), name)

    def test_keeps_natural_streams(self):
        for name in ("Geul, Hommerich", "Worm, Rimburg", "Roer, Stah"):
            self.assertFalse(sim.is_structure(name, self.clean), name)

    def test_flags_sustained_negative_flow(self):
        # Reversing flow indicates a controlled structure regardless of name.
        reversing = pd.Series([-0.5] * 10 + [1.0] * 90)
        self.assertTrue(sim.is_structure("Some Beek", reversing))

    def test_tolerates_isolated_negative_readings(self):
        # One bad reading in 1000 is noise, not a reversing structure.
        noisy = pd.Series([1.0] * 999 + [-0.1])
        self.assertFalse(sim.is_structure("Some Beek", noisy))


class SignatureTests(unittest.TestCase):
    def _series(self, values):
        index = pd.date_range("2024-01-01", periods=len(values), freq="h", tz="UTC")
        return pd.Series(values, index=index)

    def test_returns_none_below_minimum_record(self):
        self.assertIsNone(sim.signatures(self._series([1.0] * 100)))

    def test_low_flow_ratio_stays_in_unit_interval(self):
        # A negative low-flow ratio is impossible for a ratio of flow
        # percentiles; it was the symptom that exposed the structure gauges.
        rng = np.random.default_rng(0)
        flow = np.abs(rng.lognormal(0, 0.6, sim.MIN_HOURS + 50))
        result = sim.signatures(self._series(flow))
        self.assertGreaterEqual(result["low_flow_ratio"], 0.0)
        self.assertLessEqual(result["low_flow_ratio"], 1.0)

    def test_flashiness_rises_with_volatility(self):
        n = sim.MIN_HOURS + 50
        steady = self._series(np.full(n, 2.0) + np.linspace(0, 0.1, n))
        flashy = self._series(2.0 + np.tile([1.5, -1.0], n // 2)[:n])
        self.assertLess(
            sim.signatures(steady)["flashiness"], sim.signatures(flashy)["flashiness"]
        )

    def test_zero_sentinels_would_distort_signatures(self):
        """Regression guard for the Waterschap `0.0` missing-value marker.

        Zeros left in behave like measured zero flow. The damage is confined to
        *first-difference* statistics — here flashiness inflates roughly
        nineteen-fold — while percentile statistics such as the baseflow index
        barely move, because a sparse scatter of zeros shifts a quantile very
        little.

        That asymmetry is why the bug survived so long: every summary that would
        have exposed it (min, median, baseflow index) looked plausible, and the
        contamination surfaced only in the response correlations, which are
        computed on differences.
        """
        # Long enough that blanking 5% still clears MIN_HOURS, which is the
        # point: blanked sentinels become missing data, not zero flow.
        n = int(sim.MIN_HOURS * 1.5)
        rng = np.random.default_rng(1)
        # Smooth, autocorrelated flow, as real discharge is. An isolated zero
        # in a smooth series is a full-magnitude excursion and back.
        clean = 2.0 + np.sin(np.arange(n) / 240.0) + rng.normal(0, 0.01, n)
        contaminated = clean.copy()
        contaminated[::20] = 0.0  # sentinel every 20th hour

        good = sim.signatures(self._series(clean))
        bad = sim.signatures(self._series(contaminated))

        # First-difference statistics are wrecked.
        self.assertGreater(bad["flashiness"], good["flashiness"] * 10)
        # Percentile statistics are not, which is what hid the bug.
        self.assertAlmostEqual(
            bad["low_flow_ratio"], good["low_flow_ratio"], delta=0.05
        )

        # Blanking restores flashiness to the clean value.
        blanked = pd.Series(contaminated).replace(0.0, np.nan)
        repaired = sim.signatures(self._series(blanked.to_numpy()))
        self.assertAlmostEqual(repaired["flashiness"], good["flashiness"], delta=0.001)


    def test_differences_do_not_span_coverage_gaps(self):
        """Regression guard for differencing a compacted series.

        `dropna()` then `.diff()` joins the hours either side of an outage, so a
        gauge offline for months contributes one fabricated step of the full
        flow magnitude to flashiness. Differencing on the grid must leave that
        pair as NaN instead.
        """
        n = int(sim.MIN_HOURS * 1.6)
        rng = np.random.default_rng(11)
        flow = 2.0 + np.sin(np.arange(n) / 240.0) + rng.normal(0, 0.01, n)
        gapped = pd.Series(flow, index=pd.date_range("2024-01-01", periods=n, freq="h", tz="UTC"))
        # A long outage, with markedly different flow either side of it.
        gapped.iloc[1000:3000] = np.nan
        gapped.iloc[3000:] = gapped.iloc[3000:] + 40.0

        result = sim.signatures(gapped)

        # The old behaviour, reproduced inline: compact first, difference after.
        compact = gapped.dropna()
        old_flashiness = float(compact.diff().abs().sum() / compact.sum())

        # The compacted version invents a single ~40 m3/s step across the gap.
        self.assertLess(result["flashiness"], old_flashiness)
        self.assertGreater(old_flashiness / result["flashiness"], 1.5)

        # And passing an already-compacted series must not reintroduce the bug:
        # signatures() restores the hourly grid before differencing.
        self.assertAlmostEqual(
            sim.signatures(compact)["flashiness"], result["flashiness"], places=12
        )


class BestLagTests(unittest.TestCase):
    def _pair(self, n=2000, lag=0, noise=0.0, seed=0):
        rng = np.random.default_rng(seed)
        index = pd.date_range("2024-01-01", periods=n, freq="h", tz="UTC")
        base = np.cumsum(rng.normal(0, 1, n)) + 50
        shifted = np.roll(base, lag) + rng.normal(0, noise, n)
        return pd.Series(base, index=index), pd.Series(shifted, index=index)

    def test_recovers_a_known_lag_with_documented_sign(self):
        """`b` delayed by L hours is recovered at lag -L.

        The sign matters for reading routing times out of the pair table:
        a negative `response_lag_h` means gauge B responds *later* than gauge A.
        """
        a, b = self._pair(lag=4, noise=0.01)  # b(t) = a(t-4): b is delayed by 4 h
        mask = pd.Series(True, index=a.index)
        r, lag, n = sim.best_lag_corr(a, b, mask)
        self.assertEqual(lag, -4)
        self.assertGreater(abs(r), 0.9)
        self.assertEqual(n, len(a))

    def test_lag_sign_is_antisymmetric(self):
        a, b = self._pair(lag=3, noise=0.01)
        mask = pd.Series(True, index=a.index)
        _, forward, _ = sim.best_lag_corr(a, b, mask)
        _, reverse, _ = sim.best_lag_corr(b, a, mask)
        self.assertEqual(forward, -reverse)

    def test_returns_nan_below_minimum_event_hours(self):
        a, b = self._pair(n=300)
        mask = pd.Series(False, index=a.index)
        mask.iloc[:10] = True
        r, lag, n = sim.best_lag_corr(a, b, mask)
        self.assertTrue(np.isnan(r))
        self.assertEqual(n, 10)

    def test_selection_bias_exists_on_unrelated_series(self):
        """The reason a time-shifted null is mandatory, not optional.

        Two independent series still yield a non-trivial |r| once the maximum
        is taken over 25 candidate lags. Reporting the raw best-lag correlation
        without this baseline overstates co-response.
        """
        rng = np.random.default_rng(7)
        index = pd.date_range("2024-01-01", periods=1200, freq="h", tz="UTC")
        peaks = []
        for seed in range(12):
            local = np.random.default_rng(seed)
            a = pd.Series(np.cumsum(local.normal(0, 1, 1200)), index=index)
            b = pd.Series(np.cumsum(rng.normal(0, 1, 1200)), index=index)
            r, _, _ = sim.best_lag_corr(a, b, pd.Series(True, index=index))
            peaks.append(abs(r))
        self.assertGreater(np.median(peaks), 0.02)

    def test_selection_bias_is_positive_so_the_null_can_measure_it(self):
        """The lag maximum must be taken on signed r, not |r|.

        Selecting on |r| and returning the signed value gives a near-symmetric
        sign on unrelated series, so the time-shifted null averages to roughly
        zero and subtracts almost nothing — while the bias it exists to remove
        sits in the magnitude. Measured on the real pair table before the fix:
        median null +0.016 against median |null| +0.036, 35% of nulls negative,
        and 37% of pairs where the "correction" made the statistic larger.

        On unrelated series the peak must come out reliably positive, because
        that positive value is exactly the procedural floor the null reports.
        """
        rng = np.random.default_rng(11)
        index = pd.date_range("2024-01-01", periods=1200, freq="h", tz="UTC")
        peaks = []
        for seed in range(20):
            local = np.random.default_rng(seed)
            a = pd.Series(np.cumsum(local.normal(0, 1, 1200)), index=index)
            b = pd.Series(np.cumsum(rng.normal(0, 1, 1200)), index=index)
            r, _, _ = sim.best_lag_corr(a, b, pd.Series(True, index=index))
            peaks.append(r)
        peaks = np.array(peaks)
        self.assertTrue((peaks > 0).all(), "a signed maximum over lags cannot be negative")
        self.assertGreater(np.median(peaks), 0.02)


class MantelTests(unittest.TestCase):
    """Pairs from N gauges are not N-choose-2 independent observations."""

    def _matrices(self, n=12, coupling=0.0, seed=0):
        rng = np.random.default_rng(seed)
        coords = rng.uniform(0, 100, (n, 2))
        distance = np.full((n, n), np.nan)
        response = np.full((n, n), np.nan)
        for i in range(n):
            for j in range(i + 1, n):
                d = float(np.hypot(*(coords[i] - coords[j])))
                distance[i, j] = distance[j, i] = d
                value = -coupling * d + rng.normal(0, 1)
                response[i, j] = response[j, i] = value
        return distance, response

    def test_detects_no_association_when_there_is_none(self):
        d, r = self._matrices(coupling=0.0, seed=3)
        observed, p, _, _ = sim.mantel(d, r, 400, np.random.default_rng(0))
        self.assertGreater(p, 0.05)
        self.assertLess(abs(observed), 0.6)

    def test_detects_a_planted_association(self):
        d, r = self._matrices(n=20, coupling=0.4, seed=1)
        observed, p, _, _ = sim.mantel(d, r, 400, np.random.default_rng(0))
        self.assertLess(observed, 0)
        self.assertLess(p, 0.05)

    def test_null_distribution_is_centred_near_zero(self):
        d, r = self._matrices(n=15, coupling=0.3, seed=2)
        _, _, null, _ = sim.mantel(d, r, 600, np.random.default_rng(0))
        self.assertAlmostEqual(float(np.median(null)), 0.0, delta=0.15)

    def test_counts_only_usable_pairs(self):
        d, r = self._matrices(n=10, seed=4)
        r[0, 1] = r[1, 0] = np.nan
        _, _, _, n_valid = sim.mantel(d, r, 100, np.random.default_rng(0))
        self.assertEqual(n_valid, 10 * 9 // 2 - 1)


if __name__ == "__main__":
    unittest.main()


class MantelInputTests(unittest.TestCase):
    """Guards the defect that reached a published number.

    The Mantel test must run on the null-calibrated excess, not the raw
    best-lag correlation. `docs/scope-decisions.md` section 2 mandates it, and
    for one release the script computed the calibrated metric, stored it, and
    then tested the raw one anyway. Nothing caught it because both are real
    columns with plausible values.
    """

    def test_script_feeds_the_excess_matrix_to_mantel(self):
        source = (ROOT / "scripts" / "23_catchment_similarity.py").read_text()
        # The headline call must use the calibrated matrix.
        self.assertIn("mantel(\n        distance_matrix, excess_matrix", source)
        # And the excess matrix must actually be populated from the null.
        self.assertIn("excess_matrix[i, j] = excess_matrix[j, i] = r - r_null", source)

    def test_excess_is_response_minus_null(self):
        """The stored column must equal the difference, not be a re-derivation."""
        import csv

        path = ROOT / "results" / "regionalisation" / "similarity_pairs.csv"
        if not path.exists():
            self.skipTest("pair table not built")
        checked = 0
        with path.open() as handle:
            for row in csv.DictReader(handle):
                try:
                    r = float(row["response_corr"])
                    null = float(row["response_corr_null"])
                    excess = float(row["response_excess"])
                except (ValueError, KeyError):
                    continue
                self.assertAlmostEqual(excess, r - null, places=9)
                checked += 1
                if checked >= 50:
                    break
        self.assertGreater(checked, 0, "no complete rows to check")
