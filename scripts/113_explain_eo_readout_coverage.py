"""Census decomposition of snapshot versus four-week representation availability."""

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.eo_inputs import ROUTES, sha256
from src.eo_window_diagnostics import slot_reason, support_reason


def main():
    prep = ROOT / "results/eo_comparison_preparation"
    source = ROOT / "results/eo_completed_coverage_review/observation_coverage.parquet"
    ledger = pd.read_parquet(source)
    ledger = ledger[ledger.kind.isin(["monthly_snapshot", "recent"])]
    links = pd.read_parquet(prep / "observation_windows.parquet")
    raw = pd.read_parquet(prep / "observed_window_coverage.parquet")
    inventory = pd.read_parquet(prep / "window_coverage.parquet")
    rows, details = [], []
    for model in sorted(ledger.model.unique()):
        product = ROUTES[model][0]
        chosen = ledger[ledger.model.eq(model)].copy()
        slots = chosen[["observation_id", "kind", "catchment_gauge"]].merge(
            links.drop(columns=["context_id"]),
            on=["observation_id", "kind"],
            validate="one_to_many",
        )
        slots = slots.merge(
            inventory[inventory["product"].eq(product)],
            on=["window_id", "catchment_gauge"],
            how="left",
            validate="many_to_one",
        )
        slots = slots.merge(
            raw[raw["product"].eq(product)][["window_id", "catchment_gauge", "observed_fraction"]],
            on=["window_id", "catchment_gauge"],
            how="left",
            validate="many_to_one",
        )
        if slots.planned_source_tiles.isna().any():
            raise ValueError("Unknown source inventory slot")
        slots["slot_reason"] = [
            slot_reason(*r)
            for r in slots[
                [
                    "planned_source_tiles",
                    "local_tiles",
                    "local_companion_missing",
                    "observed_fraction",
                ]
            ].itertuples(index=False, name=None)
        ]
        groups = slots.groupby(["observation_id", "kind"]).agg(
            slot_reasons=("slot_reason", list),
            window_ids=("window_id", list),
            raw_observed_slots=("observed_fraction", lambda x: int(x.gt(0).sum())),
        )
        chosen = chosen.merge(groups, on=["observation_id", "kind"], validate="one_to_one")
        chosen["reason"] = [
            support_reason(r, encoded)
            for r, encoded in zip(chosen.slot_reasons, chosen.available, strict=True)
        ]
        chosen["assessment_year"] = chosen.cutoff_utc.dt.year
        rows.append(chosen)
        slots["model"] = model
        details.append(slots)
    reasons = pd.concat(rows, ignore_index=True)
    out = ROOT / "results/eo_readout_coverage_diagnostics"
    out.mkdir(parents=True, exist_ok=True)
    reasons.to_parquet(out / "observation_reasons.parquet", index=False)
    pd.concat(details, ignore_index=True).to_parquet(out / "window_reasons.parquet", index=False)
    keys = [
        "model",
        "cohort",
        "kind",
        "country",
        "gauge",
        "assessment_year",
        "scoring_eligible",
        "reason",
    ]
    reasons.groupby(keys).size().rename("observations").reset_index().to_parquet(
        out / "reason_summary.parquet", index=False
    )
    high = reasons[reasons.cohort.eq("high_water") & reasons.scoring_eligible]
    pair = high.pivot(
        index=["model", "observation_id", "country", "gauge", "assessment_year"],
        columns="kind",
        values="available",
    ).reset_index()
    pair["transition"] = [
        "both" if a and b else "snapshot_only" if a else "weekly_only" if b else "neither"
        for a, b in zip(pair.monthly_snapshot, pair.recent, strict=True)
    ]
    pair.to_parquet(out / "paired_readout_membership.parquet", index=False)
    summary = high.groupby(["model", "kind", "reason"]).size().unstack(fill_value=0)
    summary.to_parquet(out / "high_water_reason_counts.parquet")
    inputs = [
        source,
        prep / "observation_windows.parquet",
        prep / "observed_window_coverage.parquet",
        prep / "window_coverage.parquet",
        Path(__file__).resolve(),
        ROOT / "src/eo_window_diagnostics.py",
    ]
    report = {
        "scope": "All held observation rows for eight completed models. No performance scoring, new data or changed eligibility. Masked pixels cannot be assigned specifically to clouds from these retained products.",
        "input_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in inputs},
        "outputs_sha256": {p.name: sha256(p) for p in out.glob("*.parquet")},
        "high_water_reasons": summary.reset_index().to_dict("records"),
        "paired_transitions": pair.groupby(["model", "transition"])
        .size()
        .rename("events")
        .reset_index()
        .to_dict("records"),
    }
    (out / "manifest.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(summary.to_string())
    print(pair.groupby(["model", "transition"]).size().unstack(fill_value=0).to_string())


if __name__ == "__main__":
    main()
