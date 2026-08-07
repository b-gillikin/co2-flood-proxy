"""Catchment signatures, the pairwise similarity space, and honest inference on it.

Produces two tidy tables that the rest of the regionalisation analysis reads:

    results/regionalisation/gauge_signatures.csv   one row per gauge
    results/regionalisation/similarity_pairs.csv   one row per gauge pair

**Signatures** are *descriptive only*: mean and median flow, coefficient of
variation, Richards-Baker flashiness, low-flow ratio, coverage, and gauge
elevation. They tell a reader what kind of catchments these are. They are not an
inferential axis.

The similarity space they used to feed was cut on 2026-08-07. `signature_distance`
explained nothing the ladder consumes, and two of its five components could not
be defended: `recession_constant` rested on an arbitrary 0.5 floor that censors
exactly the fast recessions that distinguish flashy tributaries, and
`winter_summer_ratio` had n = 2 winters, so it carried no sampling distribution
into a test that assumed one.

**Pairwise axes** are the candidate explanations for transfer decay: great-circle
distance, response correlation against a time-shifted null, and scale ratio.

Three things here are corrections to earlier versions, and each one changed a
number that had already been written down:

1. **Coordinates join on station id, not on name tokens.** The station id is in
   the cached raw filename and is authoritative. The previous fuzzy name match
   put 18 of 57 gauges more than 0.5 km from their true position and 11 of them
   more than 5 km, worst case 66 km, which is fatal for a distance-decay claim.

2. **Response correlation is event-conditioned and lag-aligned**, per
   `docs/scope-decisions.md` section 2. Full-series zero-lag correlation averages
   over long quiet stretches and forces zero lag between catchments with
   different response times. It is the wrong number and is not computed here.

3. **Inference is permutation-based.** 42 gauges give 861 pairs, but pairs are
   not independent observations: each gauge appears in 41 of them. A Pearson
   p-value on the pair list is wrong by orders of magnitude. Distance decay is
   tested with a Mantel permutation over gauge labels, and the best-lag
   procedure is calibrated against a time-shifted null that destroys shared
   weather while keeping the procedure identical.

Managed structures are excluded by default (`docs/scope-decisions.md` section 1).
The name filter is a heuristic and is recorded as such in the output: it still
needs a manual pass against the map before anything reaches the chapter.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.fetching import fetch_json, great_circle_km

SERIES_PATH = Path("data/interim/waterschap_discharge_hourly.csv")
INVENTORY_PATH = Path("data/interim/waterschap_locations.csv")
RAW_DIR = Path("data/raw/discharge/waterschap")
ELEVATION_CACHE = Path("data/interim/gauge_elevation.json")
OUTPUT_DIR = Path("results/regionalisation")

ELEVATION_API = "https://api.opentopodata.org/v1/eudem25m"

MIN_HOURS = 4000  # a gauge needs this much record to get a signature
MIN_EVENT_HOURS = 100  # a pair needs this many joint high-flow hours
MAX_LAG = 12  # hours searched either side for the response peak
EVENT_QUANTILE = 0.90  # "high flow" is above a gauge's own p90

# Minimum share of the hourly grid a gauge must actually observe. Stated as a
# floor rather than left implicit, because the repository claimed "91-100%
# coverage" for the candidate set and that was never true of the full 42: five
# gauges sit below 90% and selzerbeek_molentak observes only 53% of hours while
# carrying 0.04 m3/s mean flow and 47% zero sentinels. A gauge that is absent
# half the time cannot support an event-conditioned pair statistic.
MIN_COVERAGE = 0.80

# Managed structures. A weir gauge measures a controlled release, not a
# catchment response, and that is a different physical object however good the
# record is. Dutch terms, matched against the station name.
STRUCTURE_TERMS = (
    "stuw",  # weir
    "duiker",  # culvert
    "inlaat",  # inlet
    "verdeelwerk",  # distribution works
    "kanaal",  # canal
    "sloot",  # ditch
    "gemaal",  # pumping station
    "dijk",  # dike
)


def gauge_coordinates():
    """Map each gauge label to its inventory coordinates via the station id.

    Raw payloads are cached as ``{label}_{station_id}.json``, so the id that was
    used to fetch the series is recoverable and unambiguous. This replaces a name
    matcher that silently mis-placed a third of the network.
    """
    inventory = pd.read_csv(INVENTORY_PATH).set_index("Id")
    coordinates, names = {}, {}
    for path in sorted(RAW_DIR.glob("*.json")):
        match = re.fullmatch(r"(.+)_(\d+)\.json", path.name)
        if match is None:
            continue
        label, station_id = match.group(1), int(match.group(2))
        if station_id not in inventory.index:
            continue
        row = inventory.loc[station_id]
        if pd.isna(row["Latitude"]) or pd.isna(row["Longitude"]):
            continue
        coordinates[label] = (float(row["Latitude"]), float(row["Longitude"]))
        names[label] = str(row["Name"])
    return coordinates, names


def is_structure(station_name, series):
    """True when a gauge measures a managed structure rather than a stream."""
    if any(term in station_name.lower() for term in STRUCTURE_TERMS):
        return True
    # Sustained negative flow means reversing or controlled discharge.
    flow = series.dropna()
    return bool(len(flow) and (flow < 0).mean() > 0.01)


def fetch_elevations(coordinates, refresh=False):
    """Gauge elevation from the public EU-DEM endpoint, cached to disk.

    Failures are reported rather than swallowed. An earlier version caught the
    exception silently and left 40 of 57 gauges without elevation, so the axis
    was quietly absent rather than known to be missing.
    """
    if ELEVATION_CACHE.exists() and not refresh:
        cached = json.loads(ELEVATION_CACHE.read_text())
        if any(cached.get(label) is not None for label in coordinates):
            return cached
    elevations = {}
    labels = list(coordinates)
    failures = 0
    for start in range(0, len(labels), 90):  # endpoint caps locations per request
        chunk = labels[start : start + 90]
        query = "|".join(f"{coordinates[c][0]},{coordinates[c][1]}" for c in chunk)
        try:
            payload = fetch_json(f"{ELEVATION_API}?locations={query}", timeout=90) or {}
            for label, result in zip(chunk, payload.get("results", []), strict=False):
                elevations[label] = result.get("elevation")
        except Exception as exc:  # noqa: BLE001 - report and continue; elevation is one axis
            failures += len(chunk)
            print(f"  elevation lookup FAILED for {len(chunk)} gauges: {exc}")
    if failures:
        print(f"  elevation missing for {failures}/{len(labels)} gauges — axis is incomplete")
    ELEVATION_CACHE.parent.mkdir(parents=True, exist_ok=True)
    ELEVATION_CACHE.write_text(json.dumps(elevations))
    return elevations


def signatures(series):
    """Behavioural descriptors for one gauge's hourly discharge.

    **Differences are taken on the hourly grid, not on the compacted series.**
    Calling ``dropna()`` first and differencing afterwards silently joins the
    hours either side of a coverage gap, so a gauge that was offline for three
    months contributes one enormous fabricated step to flashiness and one
    fabricated ratio to the recession constant. Those are the same two
    statistics the zero-sentinel bug corrupted, and the repo's own convention
    already forbids it: "Contiguous blocks break at any gap over one hour."

    Differencing on the grid leaves NaN wherever either endpoint is missing, so
    gap-spanning pairs drop out instead of being invented.
    """
    grid = series.asfreq("h") if series.index.freq is None else series
    flow = grid.dropna()
    if len(flow) < MIN_HOURS or flow.sum() <= 0:
        return None
    # Differences on the full grid; NaN where a neighbour is missing.
    deltas = grid.diff().abs()
    return {
        "n_hours": len(flow),
        "mean_q": float(flow.mean()),
        "median_q": float(flow.median()),
        "cv": float(flow.std() / flow.mean()),
        # Normalised by the flow over the hours that actually contributed a
        # difference, so a gappy gauge is not flattered by a shorter numerator.
        "flashiness": float(
            deltas.sum() / flow[deltas.notna().reindex(flow.index, fill_value=False)].sum()
        )
        if deltas.notna().any()
        else np.nan,
        # q10/q50 is a flow-duration ratio, not a filtered baseflow index in the
        # Lyne-Hollick or UKIH sense. Named for what it is.
        "low_flow_ratio": float(flow.quantile(0.10) / flow.quantile(0.50)),
    }


def best_lag_corr(a, b, mask, rng=None, subsample=None):
    """Peak correlation of two differenced series over +/- MAX_LAG hours.

    ``mask`` selects the hours that enter the comparison — high-flow hours in
    both catchments. Returns (r, lag, n) or (nan, nan, 0).

    The lag search is a maximum over 2*MAX_LAG+1 candidates and therefore biased
    upward on its own; ``main`` calibrates that bias with a time-shifted null run
    through this same function, at a matched sample size.

    **The maximum is taken on signed r, not |r|, and that choice is what makes
    the calibration work.** Until 2026-08-07 it selected on ``abs(r)`` and
    returned the signed value. Under the null there is no true correlation, so
    that picks the largest *magnitude* noise excursion with a near-symmetric
    sign: 249 of 703 nulls came out negative and the median null was +0.016,
    while the median |null| was +0.036. The bias being corrected for lives in
    the magnitude, so subtracting a signed mean that sits near zero removed
    almost none of it — and for 37% of pairs it made the "corrected" statistic
    *larger* than the raw one, which is not a bias correction.

    Selecting on signed r is also the physically right rule: two catchments
    responding to the same weather should be positively correlated at the lag
    that aligns their response times. Anti-correlation at some lag is noise, not
    a shorter route between them.
    """
    index = mask[mask].index
    if subsample is not None and len(index) > subsample:
        index = pd.Index(rng.choice(index, size=subsample, replace=False))
    if len(index) < MIN_EVENT_HOURS:
        return np.nan, np.nan, len(index)
    da, db = a.diff(), b.diff()
    best_r, best_lag = np.nan, np.nan
    for lag in range(-MAX_LAG, MAX_LAG + 1):
        joined = pd.DataFrame({"a": da, "b": db.shift(lag)}).loc[index].dropna()
        if len(joined) < MIN_EVENT_HOURS:
            continue
        if joined["a"].std() == 0 or joined["b"].std() == 0:
            continue
        r = float(np.corrcoef(joined["a"], joined["b"])[0, 1])
        if np.isnan(best_r) or r > best_r:
            best_r, best_lag = r, lag
    return best_r, best_lag, len(index)


def mantel(matrix_a, matrix_b, n_permutations, rng):
    """Permutation test for association between two symmetric pair matrices.

    Gauge labels are permuted jointly across rows and columns, which preserves
    the dependence structure that makes a naive Pearson p-value on the pair list
    meaningless.
    """
    n = matrix_a.shape[0]
    upper = np.triu_indices(n, 1)
    valid = ~np.isnan(matrix_a[upper]) & ~np.isnan(matrix_b[upper])
    observed = float(np.corrcoef(matrix_a[upper][valid], matrix_b[upper][valid])[0, 1])
    null = np.empty(n_permutations)
    for i in range(n_permutations):
        order = rng.permutation(n)
        permuted = matrix_a[np.ix_(order, order)]
        keep = ~np.isnan(permuted[upper]) & ~np.isnan(matrix_b[upper])
        null[i] = np.corrcoef(permuted[upper][keep], matrix_b[upper][keep])[0, 1]
    p_value = float((np.abs(null) >= abs(observed)).mean())
    return observed, p_value, null, int(valid.sum())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh-elevation", action="store_true")
    parser.add_argument("--keep-structures", action="store_true", help="Skip the structure filter")
    parser.add_argument("--permutations", type=int, default=5000)
    parser.add_argument(
        "--null-draws",
        type=int,
        default=50,
        help="Time-shifted null draws averaged per pair. One draw leaves the "
        "null too noisy and attenuates the calibrated excess toward zero.",
    )
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)
    discharge = pd.read_csv(SERIES_PATH, parse_dates=["timestamp_utc"]).set_index("timestamp_utc")
    coordinates, station_names = gauge_coordinates()

    missing = [c for c in discharge.columns if c not in coordinates]
    if missing:
        print(f"no inventory coordinates for {len(missing)} gauges: {', '.join(missing[:5])}")

    # Structure filter, section 1 of docs/scope-decisions.md.
    excluded = {}
    for column in discharge.columns:
        if column in coordinates and is_structure(station_names[column], discharge[column]):
            excluded[column] = station_names[column]
    if not args.keep_structures:
        print(f"structure filter: excluding {len(excluded)} managed-structure gauges")

    rows, below_floor = {}, {}
    for column in discharge.columns:
        if column not in coordinates:
            continue
        if column in excluded and not args.keep_structures:
            continue
        signature = signatures(discharge[column])
        if signature is None:
            continue
        coverage = signature["n_hours"] / len(discharge)
        if coverage < MIN_COVERAGE:
            below_floor[column] = (station_names[column], coverage)
            continue
        signature["coverage"] = coverage
        signature["station_name"] = station_names[column]
        signature["latitude"], signature["longitude"] = coordinates[column]
        rows[column] = signature

    elevations = fetch_elevations({k: coordinates[k] for k in rows}, refresh=args.refresh_elevation)
    for label in rows:
        rows[label]["elevation_m"] = elevations.get(label)

    table = pd.DataFrame(rows).T
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    table.to_csv(OUTPUT_DIR / "gauge_signatures.csv", index_label="gauge")

    labels = list(rows)
    n = len(labels)
    print(f"gauges with usable records: {n}")

    # High-flow mask per gauge: above its own p90.
    thresholds = {label: discharge[label].quantile(EVENT_QUANTILE) for label in labels}
    high = {label: discharge[label] > thresholds[label] for label in labels}

    distance_matrix = np.full((n, n), np.nan)
    response_matrix = np.full((n, n), np.nan)
    # The MANDATED metric. docs/scope-decisions.md section 2 is explicit that the
    # raw best-lag correlation carries procedural bias and must not be quoted;
    # the Mantel test runs on this one, and the raw matrix is kept only so the
    # two can be reported side by side.
    excess_matrix = np.full((n, n), np.nan)
    pairs = []
    for i, a in enumerate(labels):
        for j in range(i + 1, n):
            b = labels[j]
            mask = high[a] & high[b]
            r, lag, n_hours = best_lag_corr(discharge[a], discharge[b], mask)

            # Time-shifted null: identical procedure, shared weather destroyed by
            # rolling one series a long random offset. Sample size is matched to
            # the real pair so the lag-selection bias is comparable.
            #
            # Averaged over many draws, not one. A single draw makes the null a
            # very noisy estimate of the procedural floor, and because the
            # calibrated metric is `response_corr - response_corr_null`, that
            # noise sits in the subtrahend and attenuates the excess toward
            # zero. With one draw the distance decay on the calibrated metric
            # measured -0.143 (p = 0.14); that figure is a lower bound on the
            # true value, not an estimate of it.
            null_draws = []
            for _ in range(args.null_draws):
                offset = int(rng.integers(2000, len(discharge) - 2000))
                shifted = pd.Series(np.roll(discharge[b].values, offset), index=discharge.index)
                null_mask = high[a] & (shifted > shifted.quantile(EVENT_QUANTILE))
                draw, _, _ = best_lag_corr(
                    discharge[a], shifted, null_mask, rng=rng, subsample=n_hours or None
                )
                if not np.isnan(draw):
                    null_draws.append(draw)
            r_null = float(np.mean(null_draws)) if null_draws else np.nan
            null_sd = float(np.std(null_draws)) if len(null_draws) > 1 else np.nan

            distance = great_circle_km(coordinates[a], coordinates[b])
            distance_matrix[i, j] = distance_matrix[j, i] = distance
            response_matrix[i, j] = response_matrix[j, i] = r
            if not np.isnan(r_null):
                excess_matrix[i, j] = excess_matrix[j, i] = r - r_null
            pairs.append(
                {
                    "gauge_a": a,
                    "gauge_b": b,
                    "distance_km": distance,
                    "response_corr": r,
                    "response_lag_h": lag,
                    "response_corr_null": r_null,
                    "response_corr_null_sd": null_sd,
                    "n_null_draws": len(null_draws),
                    "response_excess": r - r_null if not np.isnan(r_null) else np.nan,
                    "n_event_hours": n_hours,
                    # Magnitude only: the pair table is symmetric, and a signed
                    # ratio would encode nothing but which gauge sorted first.
                    # Directional analyses recover the sign from mean_q.
                    "scale_log_ratio": float(
                        abs(np.log10(table.loc[a, "mean_q"] / table.loc[b, "mean_q"]))
                    ),
                    "same_river": a.split("_")[0] == b.split("_")[0],
                }
            )
        print(f"  pairs from {a[:40]:40} {i + 1}/{n}", end="\r")
    print()

    similarity = pd.DataFrame(pairs)
    similarity.to_csv(OUTPUT_DIR / "similarity_pairs.csv", index=False)

    # ---- Inference -------------------------------------------------------
    observed, p_value, null, n_valid = mantel(
        distance_matrix, excess_matrix, args.permutations, rng
    )
    raw_observed, raw_p, _, raw_valid = mantel(
        distance_matrix, response_matrix, args.permutations, rng
    )

    lines = ["Catchment Signatures and Similarity Space", ""]
    lines.append(
        f"Gauges: {n}   Pairs: {len(similarity)}   Pairs with a usable response: {n_valid}"
    )
    lines.append(
        f"Structure filter: {'DISABLED' if args.keep_structures else f'excluded {len(excluded)}'}"
    )
    lines.append(
        f"Coverage floor: {MIN_COVERAGE:.0%} of the hourly grid; excluded {len(below_floor)} gauges"
    )
    for name, cov in sorted(below_floor.values(), key=lambda kv: kv[1]):
        lines.append(f"    {cov:5.0%}  {name}")
    retained_coverage = pd.to_numeric(table["coverage"], errors="coerce").dropna()
    if len(retained_coverage):
        lines.append(
            f"Coverage of the retained set: {retained_coverage.min():.0%} to "
            f"{retained_coverage.max():.0%} (median {retained_coverage.median():.0%})"
        )
    lines.append(
        f"Response metric: event-conditioned (both gauges above own p{EVENT_QUANTILE * 100:.0f}), "
        f"best lag within +/-{MAX_LAG} h"
    )
    lines.append("")

    lines.append("Signature ranges:")
    for column in (
        "mean_q",
        "cv",
        "flashiness",
        "low_flow_ratio",
        "elevation_m",
    ):
        if column in table:
            values = pd.to_numeric(table[column], errors="coerce").dropna()
            if len(values):
                lines.append(
                    f"  {column:22} {values.min():8.3f} to {values.max():8.3f} "
                    f"(median {values.median():.3f}, n={len(values)})"
                )
    lines.append("")

    valid = similarity.dropna(subset=["response_corr"])
    paired = similarity.dropna(subset=["response_corr", "response_corr_null"])
    lines.append("Response correlation, real against time-shifted null:")
    lines.append(
        f"  all real pairs        n={len(valid):4d}  median {valid['response_corr'].median():+.3f}"
    )
    lines.append("")
    lines.append(f"  paired comparison, pairs holding both estimates (n={len(paired)}):")
    lines.append(f"    real                       median {paired['response_corr'].median():+.3f}")
    lines.append(
        f"    time-shifted null          median {paired['response_corr_null'].median():+.3f}"
    )
    difference = paired["response_corr"] - paired["response_corr_null"]
    lines.append(f"    paired difference          median {difference.median():+.3f}")
    lines.append(f"    real exceeds null in       {(difference > 0).mean() * 100:.0f}% of pairs")
    if len(paired) > 20:
        statistic, p_paired = wilcoxon(paired["response_corr"], paired["response_corr_null"])
        lines.append(f"    Wilcoxon signed-rank       p = {p_paired:.3g}")
    lines.append("")
    share = paired["response_corr_null"].median() / paired["response_corr"].median()
    lines.append(
        "The null runs the identical procedure on time-shifted series, so it carries\n"
        "the same lag-selection and tail-conditioning bias but no shared weather. "
        f"{share:.0%} of the\nraw median is that bias; the paired difference is the part "
        "attributable to catchments\nactually co-responding. Quote the difference, not the "
        "raw median.\n\n"
        "The null resolves for only some pairs, because time-shifting destroys the\n"
        "co-occurrence of high-flow hours that the mask requires. The paired comparison\n"
        "above is restricted to pairs holding both estimates, so the two are computed on\n"
        "the same pairs at matched sample size."
    )
    lines.append("")

    # Lag diagnostic. A real co-response should peak away from the search
    # boundary; mass piling up at +/-MAX_LAG is the signature of pairs with no
    # peak, where the maximum lands wherever noise is largest.
    lags = valid["response_lag_h"].dropna()
    at_edge = (lags.abs() == MAX_LAG).mean()
    lines.append("Lag diagnostic:")
    lines.append(
        f"  modal lag {int(lags.mode().iloc[0]):+d} h, median |lag| {lags.abs().median():.0f} h"
    )
    lines.append(
        f"  {at_edge * 100:.0f}% of pairs peak at the +/-{MAX_LAG} h search boundary "
        f"({'acceptable' if at_edge < 0.15 else 'HIGH — widen the window or treat these as no-peak'})"
    )
    lines.append("")

    lines.append("Does response similarity decay with distance? (Mantel, gauge-label permutation)")
    lines.append("  Headline is the NULL-CALIBRATED metric, per docs/scope-decisions.md section 2.")
    lines.append(f"  observed corr(distance, response excess) = {observed:+.3f}   [HEADLINE]")
    lines.append(f"  permutation p (two-sided, n={args.permutations}) = {p_value:.4f}")
    lines.append(
        f"  null 95% range = [{np.percentile(null, 2.5):+.3f}, {np.percentile(null, 97.5):+.3f}]"
    )
    lines.append(f"  variance explained by distance = {observed**2 * 100:.1f}%")
    lines.append(
        f"  raw metric, for comparison only: {raw_observed:+.3f}, p = {raw_p:.4f}, "
        f"{raw_valid} pairs"
    )
    lines.append(
        f"  The calibrated and raw metrics differ by {abs(observed - raw_observed):.3f}. Both are\n"
        "  reported because the calibration is now doing work: until 2026-08-07 the lag\n"
        "  maximum was taken on |r| and returned signed, so the null came out near zero\n"
        "  and subtracted almost nothing. Selecting on signed r makes the procedural\n"
        "  floor measurable, and it is large."
    )
    lines.append("")
    for label, subset in (
        ("same river", valid[valid["same_river"]]),
        ("different rivers", valid[~valid["same_river"]]),
    ):
        if len(subset) > 5:
            r = np.corrcoef(subset["distance_km"], subset["response_corr"])[0, 1]
            lines.append(
                f"  {label:18} n={len(subset):4d}  corr(distance, response) = {r:+.3f}  "
                f"median response {subset['response_corr'].median():+.3f}"
            )
    lines.append("")
    lines.append(
        "Same-river and different-river pairs are reported separately because within a\n"
        "river, similarity partly reflects routing of the same water rather than\n"
        "transferability. No p-value is quoted for these subsets: they are subsets of\n"
        "the same dependent pair structure the Mantel test exists to handle."
    )
    lines.append("")
    lines.append("Excluded as managed structures (name heuristic — NEEDS A MANUAL MAP PASS):")
    for name in sorted(excluded.values()):
        lines.append(f"  {name}")

    (OUTPUT_DIR / "similarity_summary.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\nwrote {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
