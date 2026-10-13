#!/usr/bin/env python3
"""Plot the tidy representation-check results without selecting a winning arm."""

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "results/basin_ai_representation_checks"
LABELS = {
    "r0": "Rain/Q signatures",
    "r1": "Raw Q",
    "r2": "TTM mean",
    "ttm_ordered": "TTM ordered",
    "raw_state": "Raw + state",
    "ttm_mean_state": "TTM mean + state",
    "ttm_ordered_state": "TTM ordered + state",
    "r2_area": "TTM + area",
    "r2_identity": "TTM + gauge identity",
    "r3_alphaearth": "TTM + annual AlphaEarth",
    "r3_static_2017": "TTM + static AlphaEarth",
    "r3_metric_grid": "TTM + metric-grid AlphaEarth",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT)
    args = parser.parse_args()
    source = args.results_dir / "cohort_summary.csv"
    results = pd.read_csv(source)
    for analysis in ["main", "quality_sensitivity"]:
        fig, axes = plt.subplots(3, 3, figsize=(17, 14))
        for row, cohort in enumerate(["dutch", "pooled", "context"]):
            sample = results.loc[results.cohort.eq(cohort) & results.analysis.eq(analysis)].copy()
            sample["label"] = sample.arm.map(LABELS)
            for column, (measure, title, unit) in enumerate(
                [
                    (
                        "mean_peak_scaled_shape_rmse",
                        "Individual-donor response shape",
                        "Peak-scaled RMSE",
                    ),
                    (
                        "mean_donor_peak_absolute_error",
                        "Mean-of-five peak estimate",
                        "MAE in Q/p99 ratios",
                    ),
                    (
                        "mean_peak_time_difference_h",
                        "Individual-donor peak timing",
                        "Mean absolute difference, hours",
                    ),
                ]
            ):
                ax = axes[row, column]
                ax.barh(sample.label, sample[measure], color="#2878b5")
                ax.invert_yaxis()
                ax.set_title(f"{cohort}: {title}", fontsize=10)
                ax.set_xlabel(unit + "; lower is closer", fontsize=9)
                ax.grid(axis="x", alpha=0.2)
                ax.tick_params(labelsize=8)
        fig.suptitle(
            f"Representation checks: {analysis}\nPaired events within each cohort; point summaries, not equivalence tests. Intervals are in the paired table.",
            fontsize=12,
        )
        fig.tight_layout(rect=(0, 0, 1, 0.96))
        fig.savefig(args.results_dir / f"{analysis}_representation_comparison.png", dpi=160)
        plt.close(fig)
    manifest = {
        "input_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "plot_code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "figures": [
            "main_representation_comparison.png",
            "quality_sensitivity_representation_comparison.png",
        ],
    }
    (args.results_dir / "plot_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
