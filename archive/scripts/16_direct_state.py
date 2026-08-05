"""Run the locked direct groundwater/mine-water analysis."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".matplotlib"))

import matplotlib.pyplot as plt

from src.direct_state import BOOTSTRAP_REPLICATES, run_direct_state
from src.io_groundwater import load_groundwater
from src.models.july import load_signal_frame
from src.provenance import run_context

DAILY_PATH = Path("data/interim/groundwater_daily.csv")
METADATA_PATH = Path("data/interim/groundwater_series.csv")
RESULTS_DIR = Path("results/direct_state")


def write_plot(daily):
    """Plot aligned standardized residual and water state with gaps preserved."""
    plot = daily.sort_values("date_utc").copy()
    plot["residual_z"] = (plot["residual_ppm"] - plot["residual_ppm"].mean()) / plot[
        "residual_ppm"
    ].std(ddof=0)
    fig, axis = plt.subplots(figsize=(11, 4), constrained_layout=True)
    axis.plot(plot["date_utc"], plot["residual_z"], label="Pressure-separated CO2 residual")
    axis.plot(plot["date_utc"], plot["water_level_z"], label="Primary direct state")
    axis.set_ylabel("Standard deviations")
    axis.set_xlabel("UTC date")
    axis.set_title("Direct-state analysis coverage")
    axis.grid(True, alpha=0.25)
    axis.legend(loc="best")
    fig.savefig(RESULTS_DIR / "aligned_daily_state.png", dpi=160)
    plt.close(fig)


def main():
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--daily", type=Path, default=DAILY_PATH)
    parser.add_argument("--metadata", type=Path, default=METADATA_PATH)
    parser.add_argument("--bootstrap-replicates", type=int, default=BOOTSTRAP_REPLICATES)
    args = parser.parse_args()

    water, metadata = load_groundwater(args.daily, args.metadata)
    frame = load_signal_frame()
    results = run_direct_state(
        frame,
        water,
        metadata,
        bootstrap_replicates=args.bootstrap_replicates,
    )
    context = run_context(frame.index.max())
    results["summary"].update(context)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    for name in ("decision", "selection", "daily_analysis", "per_block", "sensitivities"):
        for column, value in reversed(context.items()):
            results[name].insert(0, column, value)
        results[name].to_csv(RESULTS_DIR / f"{name}.csv", index=False)
    (RESULTS_DIR / "summary.json").write_text(
        json.dumps(results["summary"], indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    write_plot(results["daily_analysis"])
    print(f"wrote {RESULTS_DIR}")
    print(f"primary series: {results['summary']['primary_series_id']}")
    print(f"outcome: {results['summary']['outcome']}")


if __name__ == "__main__":
    main()
