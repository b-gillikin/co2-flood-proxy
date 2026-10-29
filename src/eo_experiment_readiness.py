"""Read-only readiness inventory for individually designed EO experiments.

Presence checks are preparation evidence, never a substitute for input-contract,
coverage, leakage, benchmark or numerical audits. This module launches no work.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

MODELS = frozenset(
    (
        "presto",
        "anysat",
        "galileo",
        "olmoearth",
        "croma",
        "prithvi",
        "copernicus_fm",
        "dofa",
        "terramind",
        "satmae",
    )
)
SIX = (
    "hypothesis",
    "inputs",
    "model_use",
    "matched_comparator",
    "high_water_contribution",
    "interpretation",
)


def validate_plan(plan):
    """Fail malformed/duplicate designs; do not equate a design with runnable code."""
    experiments = plan.get("experiments", [])
    models = [e.get("model") for e in experiments]
    if len(experiments) != 10 or set(models) != MODELS or len(set(models)) != 10:
        raise ValueError("Exactly ten distinct selected models are required")
    ids = [e.get("id") for e in experiments]
    if len(set(ids)) != 10:
        raise ValueError("Duplicate experiment IDs")
    for e in experiments:
        if any(not isinstance(e.get(k), str) or not e[k].strip() for k in SIX):
            raise ValueError(f"Missing six-part design: {e.get('id')}")
        if not isinstance(e.get("requires_encoding"), bool) or not e.get("preparation"):
            raise ValueError(f"Missing encoding/preparation specification: {e['id']}")
    contract = plan.get("readout_contract", {})
    if 0 not in contract.get("eo_weights", []) or not contract.get(
        "encoded_contains_raw_only_candidates"
    ):
        raise ValueError("Encoded arm must be able to retain raw-only correction")
    if (
        contract.get("pooled_error_units") != "mm/h"
        or contract.get("target_outcomes_are_predictors") is not False
    ):
        raise ValueError("Scoring units and hidden-outcome separation must be explicit")
    dofa = next(e for e in experiments if e["model"] == "dofa")
    override = dofa.get("evaluation_overrides", {})
    if not override.get("residual_crossfit") or not override.get("graph_exclusion"):
        raise ValueError("Transfer residuals and all-watercourse exclusion must be specified")
    if plan.get("status") != "designed_not_launched":
        raise ValueError("This preflight expects an unlaunched design")


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def validated_receipt(root, path):
    """Validate maintained engineering evidence; empty future markers prove nothing."""
    try:
        receipt = json.loads(path.read_text())
        hashes = receipt.get("source_hashes", {})
        return (
            receipt.get("status") == "validated"
            and bool(hashes)
            and all(
                (root / name).is_file() and sha256(root / name) == h for name, h in hashes.items()
            )
        )
    except (OSError, ValueError, TypeError):
        return False


def inspect_readiness(root, plan):
    validate_plan(plan)
    root = Path(root)
    selected_path = root / "config/limburg_eo_coherent_selected_runs.json"
    assets_path = root / "config/limburg_eo_model_assets.json"
    selected = json.loads(selected_path.read_text())["models"]
    assets = {m["id"]: m for m in json.loads(assets_path.read_text())["models"]}
    environments = {
        "presto": "presto-torch291",
        "anysat": "modern",
        "galileo": "galileo",
        "olmoearth": "modern",
        "croma": "modern",
        "prithvi": "modern",
        "copernicus_fm": "legacy",
        "dofa": "legacy",
        "terramind": "terramind",
        "satmae": "satmae",
    }
    output_root = root / "results/limburg_individual_experiments_v1"
    backbone = output_root / "readiness/shared_backbone_validated.json"
    backbone_valid = validated_receipt(root, backbone)
    dispatcher = (root / "scripts/173_queue_individual_experiments.py").is_file() and backbone_valid
    queue_path = output_root / "queue/progress.json"
    queue = json.loads(queue_path.read_text()) if queue_path.is_file() else {}
    rows = []
    for e in plan["experiments"]:
        model = e["model"]
        a = assets[model]
        run = root / selected[model]["run"]
        aggregate = root / selected[model]["aggregate"] / f"{model}.parquet"
        if model == "satmae":
            supplemental = json.loads(
                (
                    root / "config/limburg_eo_supplemental_selected_runs/satmae_toa_qa60.json"
                ).read_text()
            )
            run = root / supplemental["models"][model]["run"]
            aggregate = root / supplemental["models"][model]["aggregate"] / f"{model}.parquet"
        source = (a.get("source") or {}).get("path")
        runtime = root / ".venvs-eo" / environments[model] / "bin/python"
        fixture = output_root / f"readiness/{model}_contract_and_benchmark.json"
        feature_manifest = output_root / f"features/{model}/manifest.json"
        checks = {
            "selected_run_directory_present": run.is_dir(),
            "selected_aggregate_present": aggregate.is_file(),
            "publisher_source_present": (root / source).is_dir() if source else None,
            "runtime_executable_present": runtime.is_file(),
            "checkpoint_file_present": (
                root
                / "data/raw/limburg_dynamic_model_weights/models"
                / model
                / a["assets"][0]["path"]
            ).is_file(),
            "new_shared_backbone_receipt_present": backbone.is_file(),
            "new_contract_and_benchmark_receipt_present": fixture.is_file(),
            "new_feature_manifest_present": feature_manifest.is_file(),
        }
        contract_valid = validated_receipt(root, fixture)
        checks["shared_backbone_validated"] = backbone_valid
        checks["contract_and_benchmark_validated"] = contract_valid
        # Scientific coverage and losses are audited after extraction/fitting;
        # successful engineering is never evidence of a positive result.
        rows.append(
            {
                "id": e["id"],
                "model": model,
                "checkpoint": a["checkpoint"],
                "requires_encoding": e["requires_encoding"],
                "checks": checks,
                "status": "engineering_ready"
                if dispatcher and contract_valid
                else "benchmark_pending"
                if dispatcher
                else "preparation_needed",
                "readiness_limit": "Engineering evidence only; no scientific result or performance requirement",
                "runtime": str(runtime.relative_to(root)),
                "selected_run": str(run.relative_to(root)),
                "aggregate": str(aggregate.relative_to(root)),
                "aggregate_sha256": sha256(aggregate) if aggregate.is_file() else None,
                "next_actions": e["preparation"],
            }
        )
    land_path = root / "data/raw/limburg_monitoring_land_state/manifest.json"
    land = json.loads(land_path.read_text()) if land_path.is_file() else {}
    disk = shutil.disk_usage(root)
    return {
        "schema_version": 1,
        "scope": "Read-only design/assets/verified-engineering sweep; launches no work",
        "launched": queue.get("status") in {"running", "completed", "finished_with_failures"},
        "runnable_dispatcher_implemented": dispatcher,
        "status": queue.get(
            "status",
            "engineering_ready_benchmarks_pending" if dispatcher else "designed_preparation_needed",
        ),
        "designs_validated": len(rows),
        "experiments": rows,
        "soil_snow": {
            k: land.get(k)
            for k in (
                "status",
                "updated_utc",
                "completed_months",
                "planned_months",
                "percent_complete",
                "active_month",
                "failures",
            )
        },
        "disk_free_gib": disk.free / 1024**3,
        "disk_limit": "No reliable ten-part size/ETA until per-context benchmarks; dense tensors must not be retained",
        "shared_assets": {
            p: (root / p).exists()
            for p in (
                "results/limburg_scarcity_v2_2026_10_28/preparation/manifest.json",
                "results/limburg_scarcity_v2_2026_10_28/preparation/cases.parquet",
                "results/storm_response/hourly_discharge.parquet",
                "results/storm_response/hourly_rainfall.parquet",
                "results/event_study/real_data_v1/catchments.geojson",
                "data/raw/dem/glo30",
                "data/raw/limburg_compact_eo/jobs.json",
                "data/raw/limburg_eo_expansion/jobs.json",
            )
        },
        "source_hashes": {
            str(p.relative_to(root)): sha256(p) for p in (selected_path, assets_path)
        },
    }


def inspect_context_support(root, plan):
    """Join planned held contexts to every initial-landmark case, without fitting.

    New local/token/multimodal outputs can have different support; these counts
    describe the existing routes only and never certify future feature tables.
    """
    import numpy as np
    import pandas as pd

    from src.eo_event_inputs import completed_windows, context_id

    root = Path(root)
    cases = pd.read_parquet(root / plan["shared"]["source"] / "preparation/cases.parquet")
    monthly_ids = {
        t: context_id("monthly", completed_windows(t, "monthly")) for t in cases.cutoff_utc.unique()
    }
    out = {}
    for e in plan["experiments"]:
        model = e["model"]
        kind = (
            "monthly"
            if model in ("presto", "galileo", "dofa")
            else "monthly_snapshot"
            if model == "satmae"
            else "recent"
        )
        if model == "satmae":
            path = (
                root / "results/eo_expansion_representations/satmae_toa_qa60/census/satmae.parquet"
            )
        else:
            path = (
                root
                / f"results/eo_catchment_representations/coherent_v1/selected/census/{model}.parquet"
            )
        data = pd.read_parquet(path)
        data = data[data.kind.eq(kind)].set_index(["context_id", "catchment_gauge"])
        if not data.index.is_unique:
            raise ValueError(f"Duplicate context/gauge: {model}")
        contexts = (
            cases[kind + "_context_id"] if kind != "monthly" else cases.cutoff_utc.map(monthly_ids)
        )
        keys = pd.MultiIndex.from_arrays([contexts, cases.catchment_gauge])
        aligned = data.reindex(keys)
        columns = [c for c in data if c.startswith("e") and c[1:].isdigit()]
        if not columns:
            raise ValueError(f"No embedding dimensions: {model}")
        values = aligned[columns].to_numpy(dtype=float)
        valid = np.isfinite(values).all(axis=1) & (np.linalg.norm(values, axis=1) > 0)
        out[model] = {
            "kind": kind,
            "landmark_site_cases": len(cases),
            "finite_nonzero_existing_vector_cases": int(valid.sum()),
            "unsupported_cases": int((~valid).sum()),
            "represented_years": sorted(
                int(y) for y in cases.loc[valid, "cutoff_utc"].dt.year.unique()
            ),
            "per_site": {
                str(g): {
                    "total": int((cases.gauge == g).sum()),
                    "supported": int(valid[cases.gauge.eq(g).to_numpy()].sum()),
                }
                for g in cases.gauge.unique()
            },
            "limit": "Existing pooled-vector support only; not new-feature coverage, eligible training folds or scored outcomes",
        }
    return out
