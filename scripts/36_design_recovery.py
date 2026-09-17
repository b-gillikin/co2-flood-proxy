"""Run design simulations and build a stage/discharge recovery comparison.

No actual thresholds, floods, weather contrasts or model outcomes are read.
Example: python scripts/36_design_recovery.py --replicates 100 --bootstrap 199
Outputs are design diagnostics, not a change to the prospective protocol.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.design_recovery import (
    availability_for_synthetic_storms,
    distances_km,
    hourly_presence,
    simulate_once,
    spatial_subset,
)

SPEC = importlib.util.spec_from_file_location(
    "delivery", ROOT / "scripts/35_audit_waterschap_delivery.py"
)
DELIVERY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DELIVERY)

# One provisional gauge per potentially natural watercourse. Managed branches
# are not promoted to independent tributaries to reach a numerical floor.
CANDIDATES = ["11.Q.32", "6.Q.18", "10.Q.29", "13.Q.34", "12.Q.31", "15.Q.41", "18.Q.45"]
STAGE_IDS = {
    "11.Q.32": "11.H.61",
    "6.Q.18": "6.H.46",
    "10.Q.29": "10.H.56",
    "13.Q.34": "13.H.66",
    "12.Q.31": "12.H.62",
    "15.Q.41": "15.H.69",
    "18.Q.45": "18.H.72",
}


def build_inputs(output):
    source = DELIVERY.read_source()
    # Discard numeric measurements immediately; no magnitude is used below.
    presence = source.set_index("timestamp_source")[CANDIDATES].notna()
    del source
    hourly = hourly_presence(presence)
    locations_path = ROOT / "data/interim/waterschap_locations.csv"
    locations = pd.read_csv(locations_path).set_index("ExternalReference")
    metadata = DELIVERY.station_metadata_table().set_index("series_key")
    info = {key: (watercourse, gauge) for key, _, watercourse, gauge, _ in DELIVERY.SERIES}
    rows = []
    for key in CANDIDATES:
        location = locations.loc[key]
        if isinstance(location, pd.DataFrame):
            raise ValueError(f"Ambiguous coordinate match for {key}")
        rows.append(
            {
                "series_key": key,
                "watercourse": info[key][0],
                "gauge": info[key][1],
                "latitude": location.Latitude,
                "longitude": location.Longitude,
                "coordinate_status": "public_portal_provisional_gauge_not_catchment_centroid",
                "hourly_raw_presence": hourly[key].mean(),
                "stage_reference_candidate": STAGE_IDS[key],
                "stage_timeseries_received": False,
                "stage_retained_hours": None,
                "july_stage_source_status": metadata.loc[key, "july_2021_instrument_status"],
                "july_discharge_source_status": metadata.loc[key, "july_2021_discharge_status"],
                "stage_recovery_route": "instrument_failure_needs_censoring"
                if "failed" in metadata.loc[key, "july_2021_instrument_status"]
                else "request_stage_and_datum_history",
                "source_qa": "docs/waterschap-source-metadata.md",
                "cohort_status": "design_candidate_not_approved",
            }
        )
    sites = pd.DataFrame(rows)
    sites.to_csv(output / "stage_discharge_comparison.csv", index=False)
    hourly.groupby(hourly.index.year).mean().rename_axis("source_year").to_csv(
        output / "raw_presence_by_year.csv"
    )
    return hourly, sites, locations_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replicates", type=int, default=100)
    parser.add_argument("--bootstrap", type=int, default=199)
    parser.add_argument("--seed", type=int, default=20260917)
    parser.add_argument("--output", type=Path, default=ROOT / "results/design_recovery")
    args = parser.parse_args()
    if args.replicates < 10 or args.bootstrap < 20:
        parser.error("At least 10 Monte Carlo replicates and 20 bootstrap draws required")
    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    choice_path = ROOT / "config/recovery_choices.json"
    choices = json.loads(choice_path.read_text())
    pd.DataFrame(choices["design_comparison"]).to_csv(output / "design_comparison.csv", index=False)
    hourly, sites, location_path = build_inputs(output)
    distance = distances_km(sites.latitude.to_numpy(), sites.longitude.to_numpy())
    pd.DataFrame(distance, index=CANDIDATES, columns=CANDIDATES).to_csv(
        output / "gauge_distances_km.csv"
    )
    rng = np.random.default_rng(args.seed)
    rows = []
    subsets = {n: spatial_subset(distance, n) for n in (4, 6, 7)}
    pd.DataFrame(
        [
            {"n_sites": n, "series_key": CANDIDATES[j], "selection_order": k + 1}
            for n, subset in subsets.items()
            for k, j in enumerate(subset)
        ]
    ).to_csv(output / "geometry_subsets.csv", index=False)
    # Random source-clock dates; no real high-water dates enter the experiment.
    dates = hourly.index[
        (hourly.index.hour == 12) & (hourly.index > hourly.index[0] + pd.Timedelta(days=8))
    ]
    for n, storms in itertools.product((4, 6, 7), (20, 40, 80)):
        subset = subsets[n]
        d = distance[np.ix_(subset, subset)]
        for replicate in range(args.replicates):
            anchors = pd.DatetimeIndex(rng.choice(dates, size=storms, replace=False)).sort_values()
            available = availability_for_synthetic_storms(hourly.iloc[:, subset], anchors, rng)
            for slope, rho, failure in itertools.product((0.0, -0.25), (0.2, 0.7), (False, True)):
                estimate, ci, valid = simulate_once(
                    d, available, slope, rho, rng, bootstrap=args.bootstrap, extreme_failure=failure
                )
                for k, (name, truth) in enumerate(
                    (("local_contrast", 0.5), ("distance_slope", slope))
                ):
                    rows.append(
                        {
                            "n_sites": n,
                            "n_synthetic_storms": storms,
                            "true_slope": slope,
                            "storm_variance_fraction": rho,
                            "extreme_failure": failure,
                            "replicate": replicate,
                            "estimand": name,
                            "truth": truth,
                            "estimate": estimate[k],
                            "lower": ci[0, k],
                            "upper": ci[1, k],
                            "valid_bootstrap_fraction": valid[k],
                            "raw_pair_availability": available.mean(),
                        }
                    )
        print(f"Completed {n} sites / {storms} synthetic storms", flush=True)
    results = pd.DataFrame(rows)
    results.to_csv(output / "simulation_replicates.csv", index=False)
    keys = [
        "n_sites",
        "n_synthetic_storms",
        "true_slope",
        "storm_variance_fraction",
        "extreme_failure",
        "estimand",
    ]
    summary = []
    for key, group in results.groupby(keys):
        valid = group.dropna(subset=["lower", "upper"])
        estimates = group.dropna(subset=["estimate"])
        coverage = ((valid.lower <= valid.truth) & (valid.upper >= valid.truth)).mean()
        detection = ((valid.lower > 0) | (valid.upper < 0)).mean()
        summary.append(
            dict(zip(keys, key, strict=True))
            | {
                "replicates": len(group),
                "estimable_fraction": len(estimates) / len(group),
                "interval_available_fraction": len(valid) / len(group),
                "bias_when_estimable": (estimates.estimate - estimates.truth).mean(),
                "rmse_when_estimable": np.sqrt(
                    ((estimates.estimate - estimates.truth) ** 2).mean()
                ),
                "coverage_when_interval_available": coverage,
                "coverage_mcse": np.sqrt(coverage * (1 - coverage) / len(valid))
                if len(valid)
                else np.nan,
                "excludes_zero_when_interval_available": detection,
                "median_interval_width": (valid.upper - valid.lower).median(),
            }
        )
    summary = pd.DataFrame(summary)
    summary.to_csv(output / "precision_summary.csv", index=False)
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(2, 2, figsize=(11, 8), constrained_layout=True)
    for col, estimand in enumerate(("local_contrast", "distance_slope")):
        selected = summary.loc[
            (summary.estimand == estimand)
            & (summary.true_slope == -0.25)
            & (summary.storm_variance_fraction == 0.7)
            & ~summary.extreme_failure
        ]
        for n, group in selected.groupby("n_sites"):
            axes[0, col].plot(
                group.n_synthetic_storms, group.median_interval_width, "o-", label=f"{n} sites"
            )
            axes[1, col].plot(group.n_synthetic_storms, group.interval_available_fraction, "o-")
        axes[0, col].set_title(estimand.replace("_", " "))
        axes[0, col].set_ylabel("Median 95% interval width")
        axes[0, col].legend()
        axes[1, col].set(
            xlabel="Synthetic storms", ylabel="Fraction with interval", ylim=(-0.03, 1.03)
        )
    fig.suptitle(
        "Design simulation — synthetic effects; raw flow-presence upper bound\nProvisional gauge geometry; rho = 0.7; slope = −0.25"
    )
    fig.savefig(output / "precision.png", dpi=180)
    fig.savefig(output / "precision.pdf")
    plt.close(fig)
    manifest = {
        "status": "design_simulation_not_empirical_evidence",
        "seed": args.seed,
        "replicates": args.replicates,
        "bootstrap": args.bootstrap,
        "minimum_pair_contrasts": 5,
        "minimum_pair_status": "simulation_setting_not_protocol_floor",
        "effect_units": "hypothetical_standardized_signal",
        "local_estimand": "mean_of_site_median_local_contrasts",
        "distance_estimand": "equal_weight_OLS_of_ordered_pair_medians_on_log1p_gauge_distance",
        "source_clock_timezone": "unresolved_not_converted",
        "missingness_scope": "raw_discharge_presence_only_not_joint_signal_or_validity_coverage",
        "quiet_controls": "hypothetical_no_actual_receiver_p95_or_storm_detection",
        "extreme_failure": "synthetic_MNAR_stress_test_not_estimated",
        "stage_hours": "unknown_until_stage_delivery",
        "protocol_changed": False,
        "input_sha256": {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (
                DELIVERY.SOURCE,
                location_path,
                choice_path,
                Path(__file__),
                ROOT / "src/design_recovery.py",
                ROOT / "scripts/35_audit_waterschap_delivery.py",
            )
        },
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(output)


if __name__ == "__main__":
    main()
