"""Spatial correlation length of high-flow response, against its own drivers.

One question, asked of every variable the chapter touches:

> **How far can you move from a place before a variable stops telling you about
> it?**

That single axis holds the whole substitution argument together, and it explains
why the inherited result works. Eryilmaz (2025) found public weather substitutes
for indoor sensing at a gap of 0.012 AUROC. The reason is spatial: indoor CO2 is
barometrically driven, and barometric pressure is effectively uniform over a
domain this size, so a station 22 km away is — barometrically — in the same
place. His result is a *spatial* substitution finding that was never labelled as
one. This script puts it on the same axis as rainfall and discharge.

Each variable's pairwise correlation is fitted against separation distance with

    c(d) = c_inf + (c0 - c_inf) * exp(-d / L)

- ``c0`` is the correlation between two co-located sensors: how alike two
  instruments are when distance is not the issue.
- ``L`` is the correlation length, and ``L ln 2`` the half-distance.
- ``c_inf`` is the regional floor that never decays away.

**Two decisions that matter more than the model choice.**

*Bootstrap over entities, not pairs.* N stations give N(N-1)/2 pairs but only N
independent units, so resampling pairs would give an interval several times too
narrow — the same error as a Pearson p-value on a pair list. Stations are
resampled with replacement and the fit repeated; pairs between two draws of the
same station are dropped rather than contributing a spurious zero-distance point.

*Compare at matched grain.* Daily rainfall decorrelates over roughly 110 km and
hourly rainfall over roughly 30 km, so a daily-versus-hourly comparison would
manufacture a difference out of aggregation alone. Hourly is the chapter's grain
and hourly is what the comparison uses; the daily fit is reported only to show
how large the grain effect is.

Discharge is reported twice: the raw event-conditioned correlation, which is the
quantity comparable to the meteorological correlations, and the null-calibrated
excess, which is the quantity `docs/scope-decisions.md` mandates for inference.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.fetching import great_circle_km

KNMI_PATH = Path("data/interim/knmi_hourly.csv")
DWD_PATH = Path("data/interim/dwd_precip_hourly.csv")
DWD_STATIONS = Path("data/interim/dwd_stations.csv")
PAIRS_PATH = Path("results/regionalisation/similarity_pairs.csv")
OUTPUT_DIR = Path("results/correlation_length")

# KNMI synoptic coordinates, from the 10-minute in-situ product.
KNMI_COORDS = {
    "6350": (51.5650, 4.9353),
    "6356": (51.8578, 5.1453),
    "6370": (51.4631, 5.3856),
    "6375": (51.6586, 5.7067),
    "6377": (51.1967, 5.7625),
    "6380": (50.9053, 5.7619),
    "6392": (51.4869, 6.0561),
}


def decay(distance, c0, length, c_inf):
    """Exponential decay from a co-located correlation to a regional floor."""
    return c_inf + (c0 - c_inf) * np.exp(-distance / length)


def fit_length(distance, corr, max_length=3000.0):
    """Fit the decay. Returns (c0, L, c_inf) or NaNs if it will not converge."""
    d = np.asarray(distance, dtype=float)
    c = np.asarray(corr, dtype=float)
    ok = np.isfinite(d) & np.isfinite(c)
    d, c = d[ok], c[ok]
    if len(d) < 6:
        return (np.nan, np.nan, np.nan)
    try:
        params, _ = curve_fit(
            decay,
            d,
            c,
            p0=[float(np.nanmax(c)), 20.0, float(np.nanmedian(c))],
            bounds=([-1.0, 1.0, -1.0], [2.0, max_length, 1.0]),
            maxfev=40000,
        )
        return tuple(float(v) for v in params)
    except Exception:  # noqa: BLE001 - a non-converging fit is a result, not a crash
        return (np.nan, np.nan, np.nan)


def pair_table(entities, coords, correlate):
    """All (entity_a, entity_b, distance, correlation) triples for one variable."""
    rows = []
    for i, a in enumerate(entities):
        for b in entities[i + 1 :]:
            value = correlate(a, b)
            if value is None or not np.isfinite(value):
                continue
            rows.append(
                {
                    "a": a,
                    "b": b,
                    "distance_km": great_circle_km(coords[a], coords[b]),
                    "corr": float(value),
                }
            )
    return pd.DataFrame(rows)


def bootstrap_length(pairs, entities, replicates, rng, max_length=3000.0):
    """Percentile interval on L, resampling ENTITIES rather than pairs.

    Pairs drawn between two copies of the same entity are dropped: they would
    contribute a zero-distance, unit-correlation point that no real pair of
    distinct stations can produce, dragging c0 upward and L downward.
    """
    lookup = {(r.a, r.b): (r.distance_km, r.corr) for r in pairs.itertuples()}
    lookup.update({(b, a): v for (a, b), v in lookup.items()})
    n = len(entities)
    draws = []
    for _ in range(replicates):
        picked = [entities[i] for i in rng.integers(0, n, n)]
        d, c = [], []
        for i in range(n):
            for j in range(i + 1, n):
                if picked[i] == picked[j]:
                    continue
                hit = lookup.get((picked[i], picked[j]))
                if hit is not None:
                    d.append(hit[0])
                    c.append(hit[1])
        if len(d) < 6:
            continue
        _, length, _ = fit_length(d, c, max_length=max_length)
        if np.isfinite(length):
            draws.append(length)
    if len(draws) < 20:
        return (np.nan, np.nan, len(draws))
    low, high = np.percentile(draws, [2.5, 97.5])
    return (float(low), float(high), len(draws))


def knmi_pressure_pairs():
    """Pairwise hourly pressure correlation between KNMI synoptic stations."""
    frame = pd.read_csv(KNMI_PATH, parse_dates=["timestamp_utc"])
    column = next((c for c in frame.columns if "press" in c.lower()), None)
    if column is None:
        return pd.DataFrame(), []
    wide = frame.pivot_table(index="timestamp_utc", columns="knmi_station", values=column)
    wide.columns = [str(c).split(".")[0] for c in wide.columns]
    stations = [c for c in wide.columns if c in KNMI_COORDS]

    def correlate(a, b):
        joined = wide[[a, b]].dropna()
        if len(joined) < 2000 or joined[a].std() == 0 or joined[b].std() == 0:
            return None
        return np.corrcoef(joined[a], joined[b])[0, 1]

    return pair_table(stations, KNMI_COORDS, correlate), stations


def dwd_rainfall_pairs(resample=None, min_obs=4000):
    """Pairwise rainfall correlation between DWD stations, at a chosen grain."""
    frame = pd.read_csv(DWD_PATH, parse_dates=["timestamp_utc"]).set_index("timestamp_utc")
    inventory = pd.read_csv(DWD_STATIONS).set_index("gauge")
    if resample:
        frame = frame.resample(resample).sum(min_count=12)
    coords = {
        g: (float(inventory.loc[g, "latitude"]), float(inventory.loc[g, "longitude"]))
        for g in inventory.index
    }
    stations = [c for c in frame.columns if c in coords]

    def correlate(a, b):
        joined = frame[[a, b]].dropna()
        if len(joined) < min_obs or joined[a].std() == 0 or joined[b].std() == 0:
            return None
        return np.corrcoef(joined[a], joined[b])[0, 1]

    return pair_table(stations, coords, correlate), stations


def discharge_pairs(column):
    """Reuse the pair table 23_catchment_similarity.py already produced."""
    frame = pd.read_csv(PAIRS_PATH).dropna(subset=[column, "distance_km"])
    pairs = frame.rename(columns={"gauge_a": "a", "gauge_b": "b", column: "corr"})[
        ["a", "b", "distance_km", "corr"]
    ]
    entities = sorted(set(pairs["a"]) | set(pairs["b"]))
    return pairs, entities


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replicates", type=int, default=400)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    rng = np.random.default_rng(args.seed)

    variables = []
    pressure, stations = knmi_pressure_pairs()
    if len(pressure):
        variables.append(("pressure, hourly", pressure, stations))
    for label, rule, min_obs in (("rainfall, hourly", None, 4000), ("rainfall, daily", "D", 365)):
        rain, rain_stations = dwd_rainfall_pairs(resample=rule, min_obs=min_obs)
        if len(rain):
            variables.append((label, rain, rain_stations))
    for label, column in (
        ("high-flow response, hourly", "response_corr"),
        ("high-flow response, null-calibrated", "response_excess"),
    ):
        pairs, gauges = discharge_pairs(column)
        if len(pairs):
            variables.append((label, pairs, gauges))

    rows = []
    for label, pairs, entities in variables:
        c0, length, c_inf = fit_length(pairs["distance_km"], pairs["corr"])
        low, high, valid = bootstrap_length(pairs, entities, args.replicates, rng)
        rows.append(
            {
                "variable": label,
                "n_entities": len(entities),
                "n_pairs": len(pairs),
                "c0": c0,
                "c_inf": c_inf,
                "length_km": length,
                "length_lo": low,
                "length_hi": high,
                "half_distance_km": length * np.log(2) if np.isfinite(length) else np.nan,
                "bootstrap_replicates": valid,
                "max_separation_km": float(pairs["distance_km"].max()),
            }
        )
    table = pd.DataFrame(rows)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    table.to_csv(OUTPUT_DIR / "correlation_length.csv", index=False)

    lines = ["Spatial Correlation Length", ""]
    lines.append("c(d) = c_inf + (c0 - c_inf) * exp(-d / L);  95% CI by resampling ENTITIES")
    lines.append("")
    lines.append(
        f"{'variable':38} {'n':>4} {'pairs':>6} {'c0':>6} {'c_inf':>6} "
        f"{'L km':>8} {'95% CI':>18} {'half':>6}"
    )
    for row in table.itertuples():
        interval = (
            f"[{row.length_lo:6.0f},{row.length_hi:7.0f}]"
            if np.isfinite(row.length_lo)
            else "        n/a       "
        )
        lines.append(
            f"{row.variable:38} {row.n_entities:4d} {row.n_pairs:6d} {row.c0:6.2f} "
            f"{row.c_inf:6.2f} {row.length_km:8.1f} {interval:>18} {row.half_distance_km:6.1f}"
        )
    lines.append("")
    lines.append("Reading this table:")
    lines.append(
        "  - Pressure does not decay over a domain this size. That is why an outdoor\n"
        "    station substitutes for an indoor sensor (Eryilmaz gap 0.012): the driving\n"
        "    variable is spatially uniform here, so 22 km away is the same place.\n"
        "  - Compare like with like. Daily rainfall decorrelates several times more\n"
        "    slowly than hourly rainfall, so grain alone can manufacture a difference.\n"
        "  - c0 and L answer different questions. c0 is how alike two co-located\n"
        "    catchments are; L is how fast that likeness decays with separation."
    )
    lines.append("")
    if len(table) >= 2:
        rain = table[table["variable"] == "rainfall, hourly"]
        flow = table[table["variable"] == "high-flow response, hourly"]
        if len(rain) and len(flow):
            lines.append(
                f"  Hourly rainfall L = {rain.iloc[0]['length_km']:.0f} km "
                f"[{rain.iloc[0]['length_lo']:.0f}, {rain.iloc[0]['length_hi']:.0f}]; "
                f"high-flow response L = {flow.iloc[0]['length_km']:.0f} km "
                f"[{flow.iloc[0]['length_lo']:.0f}, {flow.iloc[0]['length_hi']:.0f}]."
            )
            lines.append(
                f"  Co-located correlation differs far more than the length does: "
                f"{rain.iloc[0]['c0']:.2f} against {flow.iloc[0]['c0']:.2f}."
            )
    (OUTPUT_DIR / "correlation_length.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\nwrote {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
