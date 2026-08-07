"""The chapter's single experimental design: can a substitute replace a local instrument?

Score two predictors on one binary target, compare AUROC, and decide whether B
is close enough to A to stand in. Eryilmaz set the rule — **B substitutes if it
is within 0.05 AUROC of A** — and this module keeps it, so every rung is reported
in one currency and the threshold is inherited rather than chosen. The ladder
itself is in `docs/chapter-synthesis.md`; this file is the machinery.

Three things it insists on, each because getting it wrong changed a number:

**Paired resampling.** The interval on ``auroc_a - auroc_b`` comes from scoring
both models on the *same* resample. Differencing two independent intervals
ignores that the models move together and gives a gap interval far too wide.

**Never pool a score across groups.** AUROC is rank-based, so probabilities from
models fitted on different data — CV folds, or leave-one-storm-out — are not
commensurable. Pooling them answers a cross-period ranking question nobody asked
and is sensitive to calibration drift between fits. Pass ``groups`` and the gap
is computed *within* each group and averaged. This is not hypothetical: pooling
across forward-chaining folds moved the Eryilmaz gap from -0.012 to -0.088 and
produced a sign flip that was withdrawn on 2026-08-07.

**Resample the real unit.** With ``groups``, the bootstrap resamples groups, not
hours — the right unit when 24 storms supply the events, and it sidesteps the
moving-block bootstrap's assumption of a gapless positional index.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from sklearn.metrics import roc_auc_score

# Eryilmaz's rule, inherited rather than invented.
SUBSTITUTION_THRESHOLD = 0.05

# A moving block long enough to carry the autocorrelation of an hourly
# hydrological series. Used only when no `groups` are supplied.
DEFAULT_BLOCK_HOURS = 72
DEFAULT_REPLICATES = 1000


@dataclass
class SubstitutionResult:
    """One substitution test: does B stand in for A on this target?"""

    name_a: str
    name_b: str
    auroc_a: float
    auroc_b: float
    gap: float
    gap_ci: tuple[float, float]
    ci_a: tuple[float, float]
    ci_b: tuple[float, float]
    n_scored: int
    n_positive: int
    n_replicates: int
    threshold: float
    # Populated only when `groups` was supplied.
    n_groups: int = 0
    group_gaps: tuple[float, ...] = field(default_factory=tuple)
    pooled_gap: float = np.nan

    @property
    def substitutes(self):
        """True when B is no worse than A by more than the threshold.

        Deliberately **one-sided**. Eryilmaz's wording is "within 0.05 AUROC of
        A", which reads two-sided, but a substitute that *beats* the instrument
        it replaces has plainly substituted — the CO2-versus-rainfall case,
        where B wins by 0.41.
        """
        return bool(np.isfinite(self.gap) and self.gap <= self.threshold)

    @property
    def gap_excludes_zero(self):
        """True when the paired interval on the gap excludes no difference."""
        low, high = self.gap_ci
        return bool(np.isfinite(low) and np.isfinite(high) and (low > 0 or high < 0))

    def verdict(self):
        """One line, phrased so it cannot be read as stronger than it is."""
        if not np.isfinite(self.gap):
            return "inconclusive: AUROC could not be computed"
        direction = "substitutes" if self.substitutes else "does NOT substitute"
        certainty = (
            "gap interval excludes zero"
            if self.gap_excludes_zero
            else "gap interval spans zero, so the two are not distinguishable"
        )
        return f"{self.name_b} {direction} for {self.name_a} (gap {self.gap:+.3f}; {certainty})"


def _clean(scores_a, scores_b, outcome, groups):
    """Align the series and drop rows any of them lack."""
    a = np.asarray(scores_a, dtype=float)
    b = np.asarray(scores_b, dtype=float)
    y = np.asarray(outcome, dtype=float)
    if not (len(a) == len(b) == len(y)):
        raise ValueError(f"length mismatch: A={len(a)}, B={len(b)}, outcome={len(y)}")
    keep = np.isfinite(a) & np.isfinite(b) & np.isfinite(y)
    if groups is None:
        return a[keep], b[keep], y[keep], None
    g = np.asarray(groups)
    if len(g) != len(y):
        raise ValueError(f"length mismatch: groups={len(g)}, outcome={len(y)}")
    return a[keep], b[keep], y[keep], g[keep]


def _auroc(y, s):
    """AUROC, or NaN when the slice holds a single class."""
    return float(roc_auc_score(y, s)) if len(np.unique(y)) > 1 else np.nan


def _block_indices(count, block_hours, rng):
    """One moving-block resample of positions 0..count-1."""
    starts = np.arange(count - block_hours + 1)
    needed = int(np.ceil(count / block_hours))
    picks = rng.choice(starts, needed, replace=True)
    return np.concatenate([np.arange(s, s + block_hours) for s in picks])[:count]


def _interval(draws):
    if len(draws) < 2:
        return (np.nan, np.nan)
    low, high = np.percentile(draws, [2.5, 97.5])
    return (float(low), float(high))


def _by_group(a, b, y, g):
    """Per-group AUROCs. Groups with one outcome class drop out."""
    rows = []
    for key in np.unique(g):
        m = g == key
        ra, rb = _auroc(y[m], a[m]), _auroc(y[m], b[m])
        if np.isfinite(ra) and np.isfinite(rb):
            rows.append((ra, rb))
    return np.array(rows, dtype=float).reshape(-1, 2)


def substitution_test(
    scores_a,
    scores_b,
    outcome,
    name_a="A",
    name_b="B",
    groups=None,
    rng=None,
    block_hours=DEFAULT_BLOCK_HOURS,
    replicates=DEFAULT_REPLICATES,
    threshold=SUBSTITUTION_THRESHOLD,
):
    """Compare two predictors on one binary target and decide on substitution.

    ``scores_a`` / ``scores_b`` are scores, not models: the caller decides
    whether they come from cross-validated predictions, a raw rolling predictor,
    or a fitted transfer model. Higher must mean more likely positive for both.

    ``groups`` labels the unit the scores were produced on — a CV fold, a
    held-out storm. **Supply it whenever the scores come from more than one
    fitted model.** The gap is then computed within each group and averaged, and
    the bootstrap resamples groups. Without it the scores are treated as one
    comparable ranking and the bootstrap resamples moving blocks of rows.
    """
    rng = np.random.default_rng() if rng is None else rng
    a, b, y, g = _clean(scores_a, scores_b, outcome, groups)
    count, positives = len(y), int(y.sum())
    nan_ci = (np.nan, np.nan)

    if count == 0 or len(np.unique(y)) < 2:
        return SubstitutionResult(
            name_a,
            name_b,
            np.nan,
            np.nan,
            np.nan,
            nan_ci,
            nan_ci,
            nan_ci,
            count,
            positives,
            0,
            threshold,
        )

    pooled_gap = _auroc(y, a) - _auroc(y, b)

    if g is None:
        # One comparable ranking: score pooled, resample moving blocks of rows.
        auroc_a, auroc_b = _auroc(y, a), _auroc(y, b)
        draws_a, draws_b, draws_gap = [], [], []
        if count >= block_hours * 2:
            for _ in range(replicates):
                index = _block_indices(count, block_hours, rng)
                ra, rb = _auroc(y[index], a[index]), _auroc(y[index], b[index])
                if np.isfinite(ra) and np.isfinite(rb):
                    draws_a.append(ra)
                    draws_b.append(rb)
                    draws_gap.append(ra - rb)
        return SubstitutionResult(
            name_a,
            name_b,
            auroc_a,
            auroc_b,
            auroc_a - auroc_b,
            _interval(draws_gap),
            _interval(draws_a),
            _interval(draws_b),
            count,
            positives,
            len(draws_gap),
            threshold,
            pooled_gap=pooled_gap,
        )

    # Grouped: never rank one group's scores against another's.
    per_group = _by_group(a, b, y, g)
    if not len(per_group):
        return SubstitutionResult(
            name_a,
            name_b,
            np.nan,
            np.nan,
            np.nan,
            nan_ci,
            nan_ci,
            nan_ci,
            count,
            positives,
            0,
            threshold,
            n_groups=0,
            pooled_gap=pooled_gap,
        )

    gaps = per_group[:, 0] - per_group[:, 1]
    n = len(per_group)
    # Cluster bootstrap: the group is the independent unit, so resample groups.
    draws_a, draws_b, draws_gap = [], [], []
    if n >= 2:
        for _ in range(replicates):
            pick = rng.integers(0, n, n)
            draws_a.append(per_group[pick, 0].mean())
            draws_b.append(per_group[pick, 1].mean())
            draws_gap.append(gaps[pick].mean())

    return SubstitutionResult(
        name_a,
        name_b,
        float(per_group[:, 0].mean()),
        float(per_group[:, 1].mean()),
        float(gaps.mean()),
        _interval(draws_gap),
        _interval(draws_a),
        _interval(draws_b),
        count,
        positives,
        len(draws_gap),
        threshold,
        n_groups=n,
        group_gaps=tuple(float(v) for v in gaps),
        pooled_gap=pooled_gap,
    )


def format_result(result):
    """Render one test as the block that goes into a results file."""
    grouped = result.n_groups > 0
    unit = f"mean over {result.n_groups} groups" if grouped else "pooled"
    lines = [
        f"  {result.name_a:28} AUROC {result.auroc_a:.3f}  "
        f"95% CI [{result.ci_a[0]:.3f}, {result.ci_a[1]:.3f}]  ({unit})",
        f"  {result.name_b:28} AUROC {result.auroc_b:.3f}  "
        f"95% CI [{result.ci_b[0]:.3f}, {result.ci_b[1]:.3f}]  ({unit})",
        f"  {'gap (A - B)':28} {result.gap:+.3f}  "
        f"95% CI [{result.gap_ci[0]:+.3f}, {result.gap_ci[1]:+.3f}]",
        f"  scored rows {result.n_scored:,} ({result.n_positive:,} positive), "
        f"{result.n_replicates} valid bootstrap replicates",
    ]
    if grouped:
        gaps = np.array(result.group_gaps)
        lines.append(
            f"  per-group gap: min {gaps.min():+.3f}, median {np.median(gaps):+.3f}, "
            f"max {gaps.max():+.3f}; A better in {int((gaps > 0).sum())}/{len(gaps)}"
        )
        # The pooled figure is reported only so the contrast is visible. It ranks
        # scores from different fits against each other and is not the estimate.
        lines.append(
            f"  pooled across groups (NOT the estimate, shown for contrast): "
            f"{result.pooled_gap:+.3f}"
        )
    lines.append(f"  decision rule: substitutes if gap <= {result.threshold:.2f} AUROC (Eryilmaz)")
    lines.append(f"  -> {result.verdict()}")
    return "\n".join(lines)
