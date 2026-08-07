"""High-water events on the water authority's own thresholds, for every gauge.

The chapter's target is **not** a percentile. Waterschap Limburg publishes
Fase 1/2/3 discharge triggers per gauge — the Geel / Oranje / Rood escalation
levels of the statutory flood plan (Rampbestrijdingsplan Hoogwater Limburg
2023-2026): heightened vigilance, impending flooding, active flooding. They are
externally defined, operationally meaningful, and identical in meaning at every
gauge, which a p90 is not.

They were already on disk the whole time, in `waterschap_locations.csv`.
Verified against the plan: Maas St. Pieter 1250/2000/2600 matches its warning /
GRIP-2 / GRIP-4 milestones; Geul Hommerich 10/20/50 matches its worked tributary
example.

**This produces the TARGET, not the conditioning mask.** They are different jobs
and must not be conflated:

- *target* — "did something happen the water authority cares about?" Needs an
  external definition. Fase.
- *mask* — "which hours are active enough that a correlation between two
  catchments means anything?" Needs enough hours to estimate a correlation, is
  never interpreted, and so may be self-referential. Own p90, in
  `23_catchment_similarity.py`.

Fase is rare — median p99.7 of a gauge's own record — so using it as the mask
would leave 69% of gauge pairs with zero joint hours. That rarity is honest for
a target and fatal for a mask.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SERIES_PATH = Path("data/interim/waterschap_discharge_hourly.csv")
INVENTORY_PATH = Path("data/interim/waterschap_locations.csv")
RAW_DIR = Path("data/raw/discharge/waterschap")
EVENTS_PATH = Path("data/processed/fase_events.csv")
OUTPUT_DIR = Path("results/events")

LEVELS = {1: "Fase1Value", 2: "Fase2Value", 3: "Fase3Value"}

# Separate exceedance runs by less than this and they are one event. A gauge
# oscillating across its threshold during one storm is one episode, not twelve;
# a coverage gap inside a storm also splits the run and is rejoined here.
MIN_SEPARATION_H = 24

# A gauge above "heightened vigilance" more than this share of the time is not
# reporting a hazard, it is mis-thresholded. Niers at Kessel sits at 25%, which
# is 52% of every Fase-1 hour in the network; it is excluded by default rather
# than allowed to dominate the target.
IMPLAUSIBLE_SHARE = 0.05


def station_ids():
    """Map each gauge label to its station id, from the raw cache filenames.

    Payloads are cached as ``{label}_{station_id}.json``, so the id used to
    fetch the series is recoverable and authoritative. Same join as
    `23_catchment_similarity.py` uses for coordinates — a name match silently
    mis-placed a third of the network once, so ids only.
    """
    out = {}
    for path in RAW_DIR.glob("*.json"):
        match = re.fullmatch(r"(.+)_(\d+)\.json", path.name)
        if match:
            out[match.group(1)] = int(match.group(2))
    return out


def events(series, threshold):
    """Contiguous runs above `threshold`, merged across gaps under 24 h.

    Returns (onset, end, peak) triples. Runs are found on observed values only;
    an unobserved hour cannot be an exceedance, and the merge step means a
    coverage gap mid-storm does not split one event into two.
    """
    above = series.dropna()
    above = above[above > threshold]
    if above.empty:
        return []
    breaks = above.index.to_series().diff() > pd.Timedelta(hours=MIN_SEPARATION_H)
    out = []
    for _, run in above.groupby(breaks.cumsum()):
        out.append((run.index[0], run.index[-1], float(run.max())))
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--keep-implausible",
        action="store_true",
        help="Keep gauges above Fase 1 for an implausible share of the record",
    )
    args = parser.parse_args()

    discharge = pd.read_csv(SERIES_PATH, parse_dates=["timestamp_utc"]).set_index("timestamp_utc")
    inventory = pd.read_csv(INVENTORY_PATH).set_index("Id")
    ids = station_ids()

    rows, event_rows, dropped = [], [], {}
    for gauge in discharge.columns:
        station = ids.get(gauge)
        if station not in inventory.index:
            continue
        record = inventory.loc[station]
        series = discharge[gauge]
        observed = int(series.notna().sum())
        if not observed:
            continue

        thresholds = {n: record[column] for n, column in LEVELS.items()}
        if pd.isna(thresholds[1]):
            continue

        share = float((series > thresholds[1]).sum()) / observed
        if share > IMPLAUSIBLE_SHARE and not args.keep_implausible:
            dropped[gauge] = (str(record["Name"]), share)
            continue

        for level, threshold in thresholds.items():
            if pd.isna(threshold):
                continue
            found = events(series, threshold)
            hours = int((series > threshold).sum())
            rows.append(
                {
                    "gauge": gauge,
                    "station_name": record["Name"],
                    "water": record["WaterName"],
                    "fase": level,
                    "threshold_m3s": float(threshold),
                    "n_events": len(found),
                    "hours_above": hours,
                    "share_of_record": hours / observed,
                    # Where the threshold sits in this gauge's own record. Wide
                    # spread across gauges is the point: it encodes the
                    # authority's view of local vulnerability, not flow
                    # statistics. A percentile cannot carry that.
                    "threshold_as_percentile": 100 * float((series.dropna() <= threshold).mean()),
                    "n_observed_hours": observed,
                }
            )
            for onset, end, peak in found:
                event_rows.append(
                    {
                        "gauge": gauge,
                        "water": record["WaterName"],
                        "fase": level,
                        "threshold_m3s": float(threshold),
                        "start_timestamp_utc": onset,
                        "end_timestamp_utc": end,
                        "duration_hours": int((end - onset) / pd.Timedelta(hours=1)) + 1,
                        "peak_m3s": peak,
                    }
                )

    summary = pd.DataFrame(rows)
    catalogue = pd.DataFrame(event_rows).sort_values(["start_timestamp_utc", "gauge", "fase"])
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(OUTPUT_DIR / "fase_summary.csv", index=False)
    catalogue.to_csv(EVENTS_PATH, index=False)

    gauges = summary["gauge"].nunique()
    lines = ["High-Water Events on Published Fase Thresholds", ""]
    lines.append(f"Gauges with a published Fase 1 and a usable record: {gauges}")
    lines.append(
        f"Record: {len(discharge):,} hourly steps, {discharge.index.min():%Y-%m-%d} to "
        f"{discharge.index.max():%Y-%m-%d}"
    )
    lines.append(f"Events merged across breaks under {MIN_SEPARATION_H} h")
    lines.append("")
    lines.append(
        f"{'level':7} {'gauges reaching':>16} {'events':>8} {'hours':>8} "
        f"{'median events/gauge':>21} {'median threshold pctile':>24}"
    )
    for level in sorted(LEVELS):
        part = summary[summary["fase"].eq(level)]
        if part.empty:
            continue
        reached = part[part["n_events"] > 0]
        lines.append(
            f"Fase {level:<2} {len(reached):>10} of {len(part):<3} {int(part.n_events.sum()):>8} "
            f"{int(part.hours_above.sum()):>8} {part.n_events.median():>21.0f} "
            f"{part.threshold_as_percentile.median():>24.2f}"
        )
    lines.append("")
    lines.append(
        "Read the rightmost column before using this as a target. Fase 1 sits near the\n"
        "top of every gauge's own record, so events are few and unevenly spread: some\n"
        "gauges never reach it in this window. Report per-gauge counts, never a network\n"
        "mean, and treat any leave-one-event-out scheme as having that many folds."
    )
    if dropped:
        lines.append("")
        lines.append(
            f"Excluded — above Fase 1 for more than {IMPLAUSIBLE_SHARE:.0%} of the record,"
        )
        lines.append(
            "which is a mis-set threshold rather than a hazard (--keep-implausible to keep):"
        )
        for name, share in sorted(dropped.values(), key=lambda kv: -kv[1]):
            lines.append(f"    {share:6.1%}  {name}")

    (OUTPUT_DIR / "fase_summary.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\nwrote {OUTPUT_DIR}/ and {EVENTS_PATH}")


if __name__ == "__main__":
    main()
