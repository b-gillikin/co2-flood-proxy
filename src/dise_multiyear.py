"""Chronological/grouped reconstruction folds and fixed-population evaluation."""

from __future__ import annotations

import hashlib

import numpy as np
import pandas as pd

from src.dise_corrected import (
    choose_donor,
    donor_fdc_apply,
    donor_fdc_fit,
    fdc_apply,
    fdc_fit,
    population,
    score,
    weights,
)


def extended_assignment(frame, original, count, seed):
    """Keep every benchmark fold; add previously withheld groups without rebalance."""
    assignment = dict(original)
    groups = frame.loc[frame.source_role.isin(["local", "regional_donor"]), "river_group"]
    for group in sorted(set(groups) - set(assignment)):
        assignment[group] = int(hashlib.sha256(f"{seed}:{group}".encode()).hexdigest(), 16) % count
    if set(assignment.values()) - set(range(count)):
        raise ValueError("Invalid inner fold")
    return assignment


def jobs_for(plan):
    jobs = []
    for year in plan["test_years"]:
        jobs.append(dict(id=f"temporal_{year}", year=year, held=None))
        for group in plan["local_groups"]:
            jobs.append(dict(id=f"held_{group}_{year}", year=year, held=group))
    # Reuse a completed diagnostic first; external scores from it are not pooled.
    jobs.sort(key=lambda j: j["id"] != "held_Wurm_2021")
    return jobs


def masks(frame, job, external_years):
    good = np.isfinite(frame[["q_observed", "q_model"]]).all(axis=1).to_numpy()
    allowed = frame.source_role.isin(["local", "regional_donor"]).to_numpy()
    if job["held"] is not None:
        allowed = allowed & frame.river_group.ne(job["held"]).to_numpy()
    year = job["year"]
    train = (
        allowed
        & frame.day.ge("2018-01-01").to_numpy()
        & frame.day.lt(f"{year - 1}-01-01").to_numpy()
        & good
    )
    valid = allowed & frame.day.dt.year.eq(year - 1).to_numpy() & good
    targets = frame.source_role.eq("local")
    if job["held"] is not None:
        targets &= frame.river_group.eq(job["held"])
    elif year in external_years:
        targets |= frame.source_role.eq("reserved_external")
    test = targets.to_numpy() & frame.day.dt.year.eq(year).to_numpy() & good
    if (frame.loc[train | valid, "source_role"] == "reserved_external").any():
        raise ValueError("External verification labels entered fitting")
    if job["held"] is not None and set(frame.loc[train | valid, "gauge"]) & set(
        frame.loc[test, "gauge"]
    ):
        raise ValueError("Held gauge entered fitting")
    if not train.any() or not valid.any() or not test.any():
        raise ValueError("Empty outer split: retain and investigate, never silently skip")
    return train, valid, test, targets


def split_weight_table(frame, train, valid, test, assignment, folds):
    selected = train | valid | test
    table = pd.DataFrame(
        {
            "row_id": frame.index[selected].to_numpy(),
            "train": train[selected],
            "validation": valid[selected],
            "test": test[selected],
        }
    )
    table = table.set_index("row_id")
    sets = {"training_weight": train, "validation_weight": valid, "final_fit_weight": train | valid}
    for fold in range(folds):
        member = frame.river_group.map(assignment).eq(fold).to_numpy()
        sets[f"inner_training_weight_{fold}"] = train & ~member
        sets[f"inner_validation_weight_{fold}"] = valid & member
    for name, use in sets.items():
        if not use.any():
            raise ValueError(f"Empty weight population: {name}")
        table[name] = pd.Series(weights(frame.loc[use]), index=frame.index[use])
    return table.reset_index()


def annotate(frame, predictions, job):
    p = predictions.copy()
    before = frame.day.ge("2018-01-01") & frame.day.lt(f"{job['year']}-01-01")
    thresholds = frame.loc[before].groupby("gauge").q_observed.quantile(0.99)
    p["p99_reference"] = p.gauge.map(thresholds)
    p["high_water"] = pd.Series(pd.NA, index=p.index, dtype="boolean")
    known = p.p99_reference.notna()
    p.loc[known, "high_water"] = p.loc[known, "q_observed"].ge(p.loc[known, "p99_reference"])
    p["test_year"] = job["year"]
    p["regime"] = "spatial" if job["held"] else "temporal"
    p["outer_job"] = job["id"]
    return p, thresholds


def scopes_for(p):
    local = p.source_role.eq("local").to_numpy()
    external = p.source_role.eq("reserved_external").to_numpy()
    scopes = {"local_all": local}
    for group in sorted(p.loc[local, "river_group"].unique()):
        scopes["local:" + group] = local & p.river_group.eq(group).to_numpy()
    if external.any():
        scopes["external_all"] = external
        for group in sorted(p.loc[external, "river_group"].unique()):
            scopes[group] = external & p.river_group.eq(group).to_numpy()
        for key, col in [
            ("external_high_overlap", "spatial_view_high_overlap"),
            ("external_high_overlap_location_consistent", "spatial_view_location_consistent"),
            ("external_mapping_stress", "spatial_view_stress"),
        ]:
            scopes[key] = external & p[col].to_numpy(dtype=bool)
        for group in sorted(p.loc[external, "overlap_stratum"].unique()):
            scopes["external_overlap:" + group] = external & p.overlap_stratum.eq(group).to_numpy()
    return scopes


def evaluation(p, names):
    records, populations = [], {}
    conditions = {
        "all_days": np.ones(len(p), bool),
        "high_water": p.high_water.fillna(False).to_numpy(bool),
        "clean_high_water": (
            p.high_water.fillna(False) & p.clean_verification.fillna(False)
        ).to_numpy(bool),
    }
    for scope, use in scopes_for(p).items():
        for stratum, mask in conditions.items():
            f = p.loc[use & mask]
            expected = population(f)  # Before examining any model's predictions.
            populations[scope + "/" + stratum] = expected
            arms = names + (["local_fdc"] if scope.startswith("local") else [])
            for arm in arms:
                records.append(
                    dict(scope=scope, stratum=stratum, arm=arm, **score(f, f[arm], expected))
                )
    return records, populations


def coverage(frame, test, targets, job):
    rows = []
    for gauge, f in frame.loc[targets & frame.day.dt.year.eq(job["year"])].groupby("gauge"):
        use = test[frame.index.get_indexer(f.index)]
        rows.append(
            dict(
                gauge=gauge,
                river_group=f.river_group.iloc[0],
                source_role=f.source_role.iloc[0],
                year=job["year"],
                calendar_rows=len(f),
                observed_days=int(np.isfinite(f.q_observed).sum()),
                model_days=int(np.isfinite(f.q_model).sum()),
                eligible_days=int(use.sum()),
                status="contributing" if use.any() else "no_complete_verification_pairs",
            )
        )
    return pd.DataFrame(rows)


def assert_census(predictions, expected):
    key = ["regime", "gauge", "day"]
    if predictions.duplicated(key).any():
        raise ValueError("Repeated gauge-day within an evaluation regime")
    if len(predictions) != expected:
        raise ValueError("Prediction census differs from frozen eligible census")


def calibration(frame, train, validation, test, year):
    """Established FDC recipe; donor selection always excludes the target river.

    This equals the benchmark recipe when that river was already withheld.
    Temporal fits allow target past labels, but a donor reference must not
    quietly choose the target itself and claim zero target-label access.
    """
    past = train | validation
    before = frame.day.ge("2018-01-01") & frame.day.lt(f"{year}-01-01")
    refs = pd.DataFrame(index=frame.index[test], columns=["local_fdc", "donor_fdc"], dtype=float)
    receipts = []
    descriptors = [c for c in frame if c.startswith("a_")]
    donor_descriptors = frame[["gauge", "day", *descriptors]]
    for target in sorted(frame.loc[test, "gauge"].unique()):
        query = test & frame.gauge.eq(target).to_numpy()
        target_frame = frame.loc[query]
        target_group = target_frame.river_group.iloc[0]
        record = dict(target=target, source_role=str(target_frame.source_role.iloc[0]))
        if target_frame.source_role.eq("local").all():
            local = (
                before
                & frame.gauge.eq(target)
                & frame.clean_verification.fillna(False).astype(bool)
                & frame.q_observed.notna()
            )
            h = frame.loc[local]
            curves = fdc_fit(h.q_model, h.q_observed, h.day.dt.month)
            refs.loc[frame.index[query], "local_fdc"] = fdc_apply(
                curves, target_frame.q_model.to_numpy(), target_frame.day.dt.month.to_numpy()
            )
            record.update(
                local_pairs=len(h),
                local_curves=curves,
                local_information_budget="past target clean labels; extra information in held-river testing",
            )
        donor_past = past & frame.river_group.ne(target_group).to_numpy()
        donor, selection = choose_donor(donor_descriptors, donor_past, target, descriptors)
        record.update(
            donor=donor,
            donor_selection=selection,
            excluded_target_river=target_group,
            donor_information_budget="permitted past labels from other river groups; no target-river observed Q",
            unknown_QA_not_recoded_clean=True,
        )
        if donor:
            dh = frame.loc[donor_past & frame.gauge.eq(donor).to_numpy()]
            th = frame.loc[before & frame.gauge.eq(target)]
            curves = donor_fdc_fit(
                dh.q_model, dh.q_observed, dh.day.dt.month, th.q_model, th.day.dt.month
            )
            refs.loc[frame.index[query], "donor_fdc"] = donor_fdc_apply(
                curves, target_frame.q_model.to_numpy(), target_frame.day.dt.month.to_numpy()
            )
            record.update(
                donor_pairs=len(dh),
                donor_curves=curves,
                donor_quality_values=dh.source_quality.value_counts().to_dict(),
            )
        receipts.append(record)
    return refs, receipts
