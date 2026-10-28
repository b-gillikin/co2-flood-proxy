"""Full-census scarcity review: coverage, paired loss, high water and donor support."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.eo_inputs import sha256
from src.eo_integrity import fresh_output
from src.scarcity_review import joint_summary, severity_labels

OUT = ROOT / json.loads((ROOT / "config/limburg_scarcity_v1.json").read_text())["output"]


def labels(bank, meta, u, normalizer, register):
    n = len(meta) // 8
    pos = normalizer.index.get_indexer(meta.cutoff_utc) + u
    thresholds = np.full((n * 8, 24), np.nan)
    for i, row in enumerate(meta.itertuples()):
        if 0 <= pos[i] and pos[i] + 24 < len(normalizer):
            thresholds[i] = normalizer[row.gauge].iloc[pos[i] + 1 : pos[i] + 25]
    high, phase = severity_labels(
        bank[f"outcome_{u}"], thresholds.reshape(n, 8, 24), bank[f"q_{u}"][:, :8, -1]
    )
    f = meta[["gauge", "country", "physical_river", "storm_id", "cutoff_utc"]].copy()
    f["case"] = np.arange(len(f))
    f["offset_h"] = u
    f["future_p99"] = high.ravel()
    f["phase"] = phase.ravel()
    f["verification_available"] = bank[f"outcome_valid_{u}"].ravel()
    f["verification_clean"] = bank[f"outcome_quality_{u}"].ravel()
    f["documented_flood_overlap"] = False
    issue = f.cutoff_utc + pd.Timedelta(hours=u)
    for row in register.itertuples():
        start, end = pd.to_datetime(row.start, utc=True), pd.to_datetime(row.end, utc=True)
        if pd.notna(start) and pd.notna(end):
            f.loc[
                f.gauge.eq(row.gauge) & (issue <= end) & (issue + pd.Timedelta(hours=24) >= start),
                "documented_flood_overlap",
            ] = True
    f["verification_status"] = np.where(f.verification_available, "complete", "source_gap_unscored")
    return f


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark", action="store_true", help="Label partial review explicitly")
    args = parser.parse_args()
    prep = OUT / "preparation"
    config = json.loads((prep / "config.json").read_text())
    manifest = json.loads((prep / "manifest.json").read_text())
    paths = sorted((OUT / "scores").glob("*/manifest.json"))
    if not args.benchmark:
        audit = json.loads((OUT / "audit.json").read_text())
        if not audit["complete_matrix"] or len(paths) != manifest["jobs"]:
            raise ValueError("Full review requires every configured job and its audit")
    meta = pd.read_parquet(prep / "cases.parquet")
    storms = pd.read_parquet(prep / "storms.parquet")
    groups = json.loads((prep / "groups.json").read_text())
    network_inventory = []
    for group in groups:
        for replication, subset in enumerate(group.get("subsets", [])):
            stations = meta.iloc[list(subset)]
            network_inventory.append(
                dict(
                    scenario=group["name"],
                    replication=replication,
                    tributary_gauges=";".join(stations.gauge),
                    nl_gauges=int(stations.country.eq("NL").sum()),
                    de_gauges=int(stations.country.eq("DE").sum()),
                    wurm_gauges=int(
                        stations.physical_river.str.contains("wurm|worm", case=False).sum()
                    ),
                    maas_retained=group["family"] == "network",
                )
            )
    bank = dict(np.load(prep / "bank.npz"))
    npth = ROOT / "results/storm_response/hourly_normalizer.parquet"
    rpth = ROOT / "results/flood_case_review_2026_10_27/register.parquet"
    normalizer, register = pd.read_parquet(npth), pd.read_parquet(rpth)
    metadata = {u: labels(bank, meta, u, normalizer, register) for u in config["issue_offsets_h"]}
    years = storms.cutoff_utc.dt.year.to_numpy()
    reps = manifest["representations"]
    recent = [i for i, rep in enumerate(reps) if rep["kind"] == "recent"]
    summaries, diagnostics, opportunities, traces, bridges = [], [], [], [], []
    inputs = {
        str(p.relative_to(ROOT)): sha256(p)
        for p in [
            Path(__file__),
            ROOT / "src/scarcity_review.py",
            prep / "manifest.json",
            npth,
            rpth,
        ]
    }
    old_path = (
        ROOT
        / "results/limburg_monitoring_2026_10_28/scores/baseline__none__same_gauge/scores.parquet"
    )
    old = pd.read_parquet(old_path)
    inputs[str(old_path.relative_to(ROOT))] = sha256(old_path)
    for path in paths:
        inputs[str(path.relative_to(ROOT))] = sha256(path)
        run = json.loads(path.read_text())
        spec, u = run["group"], run["offset_h"]
        name = spec["name"]
        lab = metadata[u]
        with np.load(path.parent / "paired_replicates.npz") as z:
            paired = z["paired"]
            conventional = z["conventional"]
            used = z["eo_used"]
            clean = z["clean_pairs"]
            age = z["local_age"]
            selected = z["target_selected"]
        reference_name = "rich_basin_measured" if spec.get("measured_support") else "rich_basin"
        reference = OUT / "scores" / f"{reference_name}__u{u}" / "paired_replicates.npz"
        if not reference.exists():
            raise ValueError("Missing rich reference for paired deterioration")
        with np.load(reference) as z:
            rich_paired, rich_conventional, rich_age = (
                z["paired"],
                z["conventional"],
                z["local_age"],
            )
        population = {
            "all": np.ones((1, 8, len(storms)), bool),
            "future_p99": lab.future_p99.to_numpy().reshape(-1, 8).T[None] == 1,
            "not_future_p99": lab.future_p99.to_numpy().reshape(-1, 8).T[None] == 0,
            "undefined_p99": lab.future_p99.to_numpy().reshape(-1, 8).T[None] == -1,
            "rising_high_water": lab.phase.to_numpy().reshape(-1, 8).T[None] == "rising_high_water",
            "falling_high_water": lab.phase.to_numpy().reshape(-1, 8).T[None]
            == "falling_high_water",
            "clean_verification": bank[f"outcome_quality_{u}"].T[None],
            "equal_age": age == rich_age,
            "documented_flood_overlap": lab.documented_flood_overlap.to_numpy()
            .reshape(-1, 8)
            .T[None],
            "target_retained": selected,
            "target_removed": ~selected,
        }
        random = spec["family"] in ["missing", "combined_missing"]
        for j, rep in enumerate(reps):
            support = dict(
                population,
                eo_supported=used[..., j],
                common_eo_support=used[..., recent].all(axis=-1),
                clean_selected_donors=clean[..., j, 0],
            )
            effects = {
                "total_eo_increment": paired[..., j, 0, 0],
                "matched_representation_increment": paired[..., j, 0, 1],
                "donor_restriction": paired[..., j, 0, 2],
                "scarcity_interaction": paired[..., j, 0, 0] - rich_paired[..., j, 0, 0],
                "conventional_deterioration": conventional[..., 0] - rich_conventional[..., 0],
                "augmented_deterioration": (conventional[..., 0] + paired[..., j, 0, 0])
                - (rich_conventional[..., 0] + rich_paired[..., j, 0, 0]),
            }
            for subset, mask in support.items():
                if rep["kind"] != "recent" and subset != "all":
                    continue
                for effect, values in effects.items():
                    inference = (
                        rep["kind"] == "recent"
                        and subset in ["all", "future_p99", "eo_supported"]
                        and effect
                        in [
                            "total_eo_increment",
                            "matched_representation_increment",
                            "scarcity_interaction",
                        ]
                        and spec["family"] != "history"
                    )
                    stats = joint_summary(
                        np.where(mask, values, np.nan),
                        years,
                        random_masks=random,
                        draws=999 if inference else 0,
                    )
                    summaries.append(
                        dict(
                            scenario=name,
                            offset_h=u,
                            model=rep["model"],
                            readout=rep["kind"],
                            population=subset,
                            effect=effect,
                            country="all",
                            **stats,
                        )
                    )
            # Country is a site comparison; the two DE sites are both Wurm.
            if rep["kind"] == "recent":
                countries = meta.country.to_numpy().reshape(-1, 8)[0]
                for country in ["NL", "DE"]:
                    x = paired[..., j, 0, 0][:, countries == country]
                    summaries.append(
                        dict(
                            scenario=name,
                            offset_h=u,
                            model=rep["model"],
                            readout="recent",
                            population="all",
                            effect="total_eo_increment",
                            country=country,
                            **joint_summary(x, years, random_masks=random, draws=0),
                        )
                    )
        frame = pd.read_parquet(path.parent / "scores.parquet")
        opportunity = lab.copy()
        opportunity["scenario"] = name
        conventional_rows = frame[frame.method.eq("conventional") & frame.target_k.eq(5)]
        opportunity = opportunity.merge(
            conventional_rows[
                [
                    "case",
                    "valid_replicas",
                    "replicas",
                    "input_observed_mean",
                    "observation_age_mean_h",
                    "input_age_equal_rich_fraction",
                    "available_station_mean",
                    "trace_observing_channels",
                ]
            ],
            on="case",
            how="left",
            validate="one_to_one",
        )
        opportunity["prediction_status"] = np.where(
            opportunity.valid_replicas.fillna(0) > 0, "available", "unavailable"
        )
        names = list(meta.gauge.iloc[:8]) + ["sint_pieter", "venlo"]
        opportunity["trace_observing_gauges"] = opportunity.trace_observing_channels.map(
            lambda ids, _names=names: (
                [_names[int(i)] for i in ids] if isinstance(ids, (list, np.ndarray)) else []
            )
        )
        opportunities.append(opportunity)
        for keys, rows in frame.groupby(["gauge", "country", "method", "target_k"], sort=False):
            diagnostics.append(
                dict(
                    scenario=name,
                    offset_h=u,
                    gauge=keys[0],
                    country=keys[1],
                    method=keys[2],
                    target_k=keys[3],
                    cases=len(rows),
                    **{
                        c: float(rows[c].mean())
                        for c in [
                            "crps",
                            "crps_specific",
                            "crps_h6_specific",
                            "crps_h12_specific",
                            "crps_h24_specific",
                            "rmse_specific",
                            "peak_error_specific",
                            "peak_time_error_h",
                            "coverage80",
                            "width80_specific",
                            "donor_measured_fraction",
                            "donor_held_fraction",
                            "donor_mean_filled_fraction",
                            "donor_clean_fraction",
                            "eo_used_fraction",
                            "actual_members_mean",
                        ]
                    },
                )
            )
        # Date-selected high-water illustrations, never selected by EO gain.
        illustration = (
            lab[lab.future_p99.eq(1)].sort_values("cutoff_utc").groupby("gauge").head(2)["case"]
        )
        trace = frame[frame["case"].isin(illustration) & frame.target_k.eq(5)].copy()
        trace["donor_dates"] = trace.trace_members.map(
            lambda ids: [str(storms.cutoff_utc.iloc[i]) for i in ids]
        )
        trace["donor_months"] = trace.trace_members.map(
            lambda ids: [int(storms.cutoff_utc.iloc[i].month) for i in ids]
        )
        traces.append(trace)
        if name == "rich_local":
            prior = old[old.role.eq("natural_conventional") & old.offset_h.eq(u) & old.cap_h.eq(u)]
            bridge = frame[frame.method.eq("conventional")][
                ["case", "target_k", "crps_specific"]
            ].merge(
                prior[["case", "target_k", "crps_specific"]],
                on=["case", "target_k"],
                suffixes=("_new", "_old"),
                validate="one_to_one",
            )
            bridge["offset_h"] = u
            bridge["difference"] = bridge.crps_specific_new - bridge.crps_specific_old
            bridges.append(bridge)
        print("reviewed", path.parent.name, flush=True)
    target = OUT / ("benchmark_review" if args.benchmark else "review")
    with fresh_output(target) as work:
        pd.DataFrame(summaries).to_parquet(work / "paired-effects.parquet", index=False)
        pd.DataFrame(diagnostics).to_csv(work / "site-method-diagnostics.csv", index=False)
        pd.concat(opportunities, ignore_index=True).to_parquet(
            work / "coverage-ledger.parquet", index=False
        )
        pd.concat(traces, ignore_index=True).to_parquet(
            work / "analogue-traces.parquet", index=False
        )
        if bridges:
            pd.concat(bridges, ignore_index=True).to_csv(
                work / "prior-method-bridge.csv", index=False
            )
        pd.DataFrame(network_inventory).to_csv(
            work / "network-placement-inventory.csv", index=False
        )
        (work / "interpretation-guide.md").write_text(
            "# Controlled scarcity: interpretation guide\n\n"
            "Retrospective, nominal-availability analysis at historically monitored sites. "
            "The reference is the held-data analogue method, not the agencies' FEWS.\n\n"
            "Negative EO increments mean lower error. A negative scarcity interaction means "
            "the EO increment improved relative to its rich reference; it need not imply an absolute benefit. "
            "Read total, matched representation and donor-restriction effects together.\n\n"
            "Show the full census, EO-supported and common-support estimates alongside high-water strata. "
            "The p99 and net-rising/net-falling labels are hindsight evaluation strata. "
            "Documented flood overlap uses the existing reviewed register; it is not a new flood label.\n\n"
            "The bootstrap resamples whole years, preserving their storms, sites and issue clocks, "
            "and R shared mask IDs for random-mask means. Enumerated phases/subsets are averaged exactly. "
            "Each site has equal mass within an issue; available case-mask pairs have equal mass within site. "
            "Intervals are exploratory pointwise intervals, not family-controlled winner tests. "
            "Offsets are reported separately; do not count them as independent storms.\n\n"
            "Monthly readouts, K10, archive caps, country contrasts and secondary scores are diagnostics. "
            "Country labels describe these sites; both German gauges are Wurm. "
            "Review donor measured/held/mean-filled fractions and measured-support sensitivity, "
            "coverage, interval calibration and actual analogue dates before interpreting a gain. "
            "Null findings concern these fixed representations and 50/50 fusion. "
            "No actual latency frequency, real-time release replay, inundation skill or warning benefit is established.\n"
        )
        report = dict(
            status="benchmark_only" if args.benchmark else "completed",
            jobs=len(paths),
            planned_jobs=manifest["jobs"],
            sources_sha256=inputs,
            outputs_sha256={p.name: sha256(p) for p in work.iterdir()},
            emails_sent=False,
        )
        (work / "manifest.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
