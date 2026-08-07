"""Tests for the substitution harness.

This is the chapter's single experimental design, so the properties that matter
are the ones a reviewer would attack: that the decision rule is applied as
stated, that the gap interval is paired rather than differenced from two
independent intervals, and that an autocorrelated series does not produce
intervals that are too narrow.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.substitution import (
    SUBSTITUTION_THRESHOLD,
    format_result,
    substitution_test,
)


def synthetic(n=3000, signal_a=1.2, signal_b=1.0, seed=0, rate=0.15):
    """A binary target with two predictors of controllable quality."""
    rng = np.random.default_rng(seed)
    y = (rng.random(n) < rate).astype(float)
    a = y * signal_a + rng.normal(0, 1, n)
    b = y * signal_b + rng.normal(0, 1, n)
    return a, b, y


class DecisionRuleTests(unittest.TestCase):
    def test_close_predictors_substitute(self):
        a, b, y = synthetic(signal_a=1.2, signal_b=1.18, seed=1)
        r = substitution_test(a, b, y, rng=np.random.default_rng(0), replicates=200)
        self.assertLess(abs(r.gap), SUBSTITUTION_THRESHOLD)
        self.assertTrue(r.substitutes)

    def test_far_worse_substitute_is_rejected(self):
        a, b, y = synthetic(signal_a=2.0, signal_b=0.0, seed=2)
        r = substitution_test(a, b, y, rng=np.random.default_rng(0), replicates=200)
        self.assertGreater(r.gap, SUBSTITUTION_THRESHOLD)
        self.assertFalse(r.substitutes)

    def test_a_better_substitute_than_the_original_still_substitutes(self):
        # The rule is one-sided: B beating A is not a failure to substitute.
        # This is the CO2-versus-rainfall case, where the substitute wins.
        a, b, y = synthetic(signal_a=0.1, signal_b=2.0, seed=3)
        r = substitution_test(a, b, y, rng=np.random.default_rng(0), replicates=200)
        self.assertLess(r.gap, 0)
        self.assertTrue(r.substitutes)

    def test_threshold_is_configurable_but_defaults_to_eryilmaz(self):
        self.assertEqual(SUBSTITUTION_THRESHOLD, 0.05)
        a, b, y = synthetic(signal_a=1.5, signal_b=1.0, seed=4)
        loose = substitution_test(a, b, y, rng=np.random.default_rng(0), replicates=100)
        strict = substitution_test(
            a, b, y, rng=np.random.default_rng(0), replicates=100, threshold=0.001
        )
        self.assertEqual(loose.gap, strict.gap)
        self.assertFalse(strict.substitutes)


class PairedIntervalTests(unittest.TestCase):
    def test_gap_interval_is_narrower_than_differencing_independent_intervals(self):
        """The reason the gap is resampled in pairs.

        Two correlated models move together under resampling. Differencing
        their separate intervals ignores that and inflates the gap interval,
        which would let a real difference read as inconclusive.
        """
        a, b, y = synthetic(signal_a=1.4, signal_b=1.0, seed=5, n=4000)
        r = substitution_test(a, b, y, rng=np.random.default_rng(0), replicates=400)
        paired_width = r.gap_ci[1] - r.gap_ci[0]
        naive_width = (r.ci_a[1] - r.ci_a[0]) + (r.ci_b[1] - r.ci_b[0])
        self.assertLess(paired_width, naive_width)

    def test_identical_predictors_give_zero_gap_and_a_tight_interval(self):
        a, _, y = synthetic(seed=6)
        r = substitution_test(a, a, y, rng=np.random.default_rng(0), replicates=200)
        self.assertAlmostEqual(r.gap, 0.0, places=12)
        self.assertAlmostEqual(r.gap_ci[0], 0.0, places=9)
        self.assertAlmostEqual(r.gap_ci[1], 0.0, places=9)
        self.assertTrue(r.substitutes)
        self.assertFalse(r.gap_excludes_zero)

    def test_block_resampling_is_wider_when_the_residual_is_autocorrelated(self):
        """Blocks must not produce the over-narrow interval that hours do.

        The widening only appears when the predictor's *error* is serially
        dependent, which is the real case: an hourly discharge model is wrong in
        runs, not independently hour by hour. With white noise, hourly
        resampling is not biased and blocks buy nothing — so the test builds
        AR(1) error to reproduce the condition the block bootstrap exists for.
        """
        rng = np.random.default_rng(7)
        n = 4000
        phi = 0.97  # strong persistence, as in an hourly hydrological residual

        def ar1(scale):
            noise = rng.normal(0, scale, n)
            out = np.empty(n)
            out[0] = noise[0]
            for i in range(1, n):
                out[i] = phi * out[i - 1] + noise[i]
            return out

        y = (np.sin(np.arange(n) / 200.0) > 0.3).astype(float)
        a = y * 1.2 + ar1(0.3)
        b = y * 1.0 + ar1(0.3)

        blocks = substitution_test(
            a, b, y, rng=np.random.default_rng(0), block_hours=168, replicates=400
        )
        hours = substitution_test(
            a, b, y, rng=np.random.default_rng(0), block_hours=1, replicates=400
        )
        self.assertGreater(
            blocks.ci_a[1] - blocks.ci_a[0],
            hours.ci_a[1] - hours.ci_a[0],
        )


class GroupedScoringTests(unittest.TestCase):
    """Guards the defect that survived a full review cycle.

    Scores from separately fitted models are not one comparable ranking. Pooling
    them into a single AUROC is sensitive to calibration drift between fits, and
    on the real Eryilmaz data it moved the gap from -0.012 to -0.088 and flipped
    its sign. `groups` must make that impossible.
    """

    @staticmethod
    def drifting_folds(n=400, seed=11):
        """Two folds where A is better within each, but miscalibrated across them.

        Fold 2 carries most of the positives *and* a large negative offset on A,
        as happens when a model is refitted on more data. Within each fold A
        ranks better than B; pooled, A's ranking is destroyed by the offset.
        """
        rng = np.random.default_rng(seed)
        a, b, y, g = [], [], [], []
        for fold, (rate, offset) in enumerate([(0.10, 0.0), (0.60, -5.0)]):
            yi = (rng.random(n) < rate).astype(float)
            a.append(yi * 1.5 + rng.normal(0, 1, n) + offset)
            b.append(yi * 1.0 + rng.normal(0, 1, n))
            y.append(yi)
            g.append(np.full(n, fold))
        return tuple(np.concatenate(v) for v in (a, b, y, g))

    def test_grouped_gap_ignores_between_group_calibration_drift(self):
        a, b, y, g = self.drifting_folds()
        grouped = substitution_test(a, b, y, groups=g, rng=np.random.default_rng(0), replicates=300)
        pooled = substitution_test(a, b, y, rng=np.random.default_rng(0), replicates=300)

        # Within every fold, A is the better model.
        self.assertTrue(all(gap > 0 for gap in grouped.group_gaps))
        self.assertGreater(grouped.gap, 0)
        # Pooled, the offset reverses the verdict. That is the bug.
        self.assertLess(pooled.gap, 0)
        # And the grouped result carries the pooled figure only as a contrast.
        self.assertAlmostEqual(grouped.pooled_gap, pooled.gap, places=12)
        self.assertNotAlmostEqual(grouped.gap, grouped.pooled_gap, places=2)

    def test_groups_report_every_fold_not_just_the_mean(self):
        a, b, y, g = self.drifting_folds()
        r = substitution_test(a, b, y, groups=g, rng=np.random.default_rng(0), replicates=100)
        self.assertEqual(r.n_groups, 2)
        self.assertEqual(len(r.group_gaps), 2)
        self.assertAlmostEqual(r.gap, float(np.mean(r.group_gaps)), places=12)
        self.assertIn("per-group gap", format_result(r))
        self.assertIn("NOT the estimate", format_result(r))

    def test_single_class_groups_drop_out_rather_than_crash(self):
        a, b, y = synthetic(n=300, seed=12)
        g = np.concatenate([np.zeros(150), np.ones(150)])
        y[150:] = 0.0  # second group has no positives at all
        r = substitution_test(a, b, y, groups=g, rng=np.random.default_rng(0), replicates=50)
        self.assertEqual(r.n_groups, 1)
        self.assertTrue(np.isfinite(r.gap))

    def test_fewer_groups_give_a_wider_interval(self):
        """The cluster bootstrap must treat the group as the unit of evidence."""
        rng = np.random.default_rng(13)
        n_per = 200

        def build(n_groups):
            a, b, y, g = [], [], [], []
            for k in range(n_groups):
                yi = (rng.random(n_per) < 0.2).astype(float)
                a.append(yi * 1.3 + rng.normal(0, 1, n_per))
                b.append(yi * 1.0 + rng.normal(0, 1, n_per))
                y.append(yi)
                g.append(np.full(n_per, k))
            return tuple(np.concatenate(v) for v in (a, b, y, g))

        a4, b4, y4, g4 = build(4)
        a24, b24, y24, g24 = build(24)
        narrow = substitution_test(
            a24, b24, y24, groups=g24, rng=np.random.default_rng(0), replicates=400
        )
        wide = substitution_test(
            a4, b4, y4, groups=g4, rng=np.random.default_rng(0), replicates=400
        )
        self.assertGreater(
            wide.gap_ci[1] - wide.gap_ci[0],
            narrow.gap_ci[1] - narrow.gap_ci[0],
        )


class EdgeCaseTests(unittest.TestCase):
    def test_single_class_outcome_is_inconclusive_not_an_error(self):
        r = substitution_test([1.0, 2.0, 3.0], [3.0, 2.0, 1.0], [1.0, 1.0, 1.0])
        self.assertTrue(np.isnan(r.gap))
        self.assertFalse(r.substitutes)
        self.assertIn("inconclusive", r.verdict())

    def test_missing_values_are_dropped_pairwise(self):
        a, b, y = synthetic(n=500, seed=8)
        a = a.copy()
        a[:50] = np.nan
        r = substitution_test(a, b, y, rng=np.random.default_rng(0), replicates=50)
        self.assertEqual(r.n_scored, 450)

    def test_length_mismatch_raises(self):
        with self.assertRaises(ValueError):
            substitution_test([1.0, 2.0], [1.0], [0.0, 1.0])

    def test_too_short_for_blocks_returns_point_estimate_without_interval(self):
        a, b, y = synthetic(n=60, seed=9)
        r = substitution_test(a, b, y, block_hours=72, replicates=50)
        self.assertTrue(np.isfinite(r.gap))
        self.assertTrue(np.isnan(r.gap_ci[0]))
        self.assertEqual(r.n_replicates, 0)

    def test_format_result_reports_the_rule_and_the_verdict(self):
        a, b, y = synthetic(seed=10)
        text = format_result(
            substitution_test(a, b, y, rng=np.random.default_rng(0), replicates=50)
        )
        self.assertIn("decision rule", text)
        self.assertIn("gap (A - B)", text)
        self.assertIn("Eryilmaz", text)


if __name__ == "__main__":
    unittest.main()
