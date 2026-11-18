"""Selected EO run contracts and fresh output publication; no scientific filtering."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from src.eo_inputs import sha256

# Public compatibility import; future extractors fingerprint the small builder only.
from src.eo_population import input_population  # noqa: F401


def compatible_source(root, name, digest):
    path = root / name
    if path.exists() and sha256(path) == digest:
        return True
    registry = root / "config/limburg_eo_source_compatibility.json"
    if not registry.exists():
        return False
    item = json.loads(registry.read_text()).get("sources", {}).get(name, {}).get(digest)
    return bool(
        item
        and item["classification"] == "metadata_only_compatibility"
        and path.is_file()
        and sha256(path) == item["replacement_sha256"]
        and (root / item["snapshot"]).is_file()
        and sha256(root / item["snapshot"]) == digest
    )


def population_ledger(root, scope, kind, input_roots=None):
    """Resolve portable locations or an explicit relocation for old/external ledgers."""
    role = "archive" if kind == "jobs" else "preparation"
    overrides = input_roots or {}
    if role in overrides:
        location = Path(overrides[role])
        return (location if location.is_absolute() else root / location) / (
            "jobs.json" if kind == "jobs" else "contexts.json"
        )
    if scope.get("schema_version", 1) >= 2:
        item = scope[kind + "_location"]
        if item["base"] != "project":
            raise ValueError("External input role requires an explicit resolver: " + item["base"])
        return root / item["path"]
    return root / scope[kind + "_path"]


def validate_selection(root, selection):
    path = Path(root).resolve() / selection["contexts"]
    if sha256(path) != selection["contexts_sha256"]:
        raise ValueError("Selected input context ledger changed")
    return [c["context_id"] for c in json.loads(path.read_text())]


def validate_run(
    root, run, *, model=None, expected_contexts=None, allow_partial=False, input_roots=None
):
    """A finite patch or successful aggregator cannot certify a whole extraction."""
    root, run = Path(root).resolve(), Path(run).resolve()
    saved = json.loads((run / "manifest.json").read_text())
    status = json.loads((run / "status.json").read_text())
    if model is not None and saved["model"] != model:
        raise ValueError("Selected model differs from extraction")
    if saved.get("purpose") != "context_census":
        raise ValueError("Engineering extraction is not a census")
    if status.get("run") != run.name:
        raise ValueError("Extraction status/run mismatch")
    complete = status.get("status") == "completed" and status.get("errors") == 0
    if not complete and not allow_partial:
        raise ValueError("Extraction is incomplete or has errors")
    for path, digest in saved["code"].items():
        if not compatible_source(root, path, digest):
            raise ValueError("Extraction source code changed: " + path)
    scope = saved.get("input_population")
    if scope:
        for kind in ["jobs", "contexts"]:
            if kind + "_location" in scope or kind + "_path" in scope:
                if (
                    sha256(population_ledger(root, scope, kind, input_roots))
                    != scope[kind + "_sha256"]
                ):
                    raise ValueError("Extraction input ledger changed: " + kind)
        if scope["selection"] != "full_census" and not allow_partial:
            raise ValueError("Single-context extraction is not a full census")
        if status.get("contexts_total") != len(scope["expected_context_ids"]):
            raise ValueError("Extraction population/status mismatch")
    if expected_contexts is not None and not allow_partial:
        if status.get("contexts_total") != len(expected_contexts):
            raise ValueError("Extraction context count differs from selected census")
        if scope and scope["expected_context_ids"] != expected_contexts:
            raise ValueError("Extraction context identities differ from selected census")
    return saved, status


def validate_aggregate(
    root, folder, model, *, selected=None, expected_contexts=None, input_roots=None
):
    root, folder = Path(root).resolve(), Path(folder).resolve()
    report = json.loads((folder / "manifest.json").read_text())
    if report.get("engineering") or report.get("partial") or report.get("errors"):
        raise ValueError("Engineering, partial or errored aggregate cannot be labelled complete")
    if report.get("contexts_by_model", {}).get(model, 0) <= 0:
        raise ValueError("No accepted contexts for selected model")
    required = {model + ".parquet", "coverage.parquet", "patch_areas.parquet"}
    outputs = report["outputs_sha256"]
    if set(outputs) != required or {p.name for p in folder.glob("*.parquet")} != required:
        raise ValueError("Missing or stale aggregate outputs")
    for name, digest in outputs.items():
        if sha256(folder / name) != digest:
            raise ValueError("Aggregate checksum mismatch: " + name)
    manifests = [p for p in report["source_sha256"] if p.endswith("/manifest.json")]
    if len(manifests) != 1:
        raise ValueError("Select exactly one extraction run per model")
    source = root / manifests[0]
    if sha256(source) != report["source_sha256"][manifests[0]]:
        raise ValueError("Extraction manifest checksum mismatch")
    if selected and source.parent.resolve() != (root / selected["run"]).resolve():
        raise ValueError("Aggregate does not use the selected extraction run")
    saved, status = validate_run(
        root,
        source.parent,
        model=model,
        expected_contexts=expected_contexts,
        input_roots=input_roots,
    )
    if selected and saved.get("mask_policy", "native_pixel_mask_v1") != selected["mask_policy"]:
        raise ValueError("Selected mask policy differs")
    return report, saved, status


@contextmanager
def fresh_output(target):
    """Never recertify leftover files. Preserve the prior directory on replacement."""
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix="." + target.name + "-", dir=target.parent))
    backup = None
    try:
        yield stage
        if target.exists():
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
            backup = target.with_name(target.name + ".previous-" + stamp)
            target.rename(backup)
        try:
            os.replace(stage, target)
        except BaseException:
            if backup is not None:
                backup.rename(target)
            raise
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def selected_aggregates(root, selection):
    """Resolve the authoritative map without searching for newest/most convenient runs."""
    root = Path(root).resolve()
    contexts = validate_selection(root, selection)
    input_roots = selection.get("input_roots")
    accepted, readiness = {}, {}
    for model, item in selection["models"].items():
        run, folder = root / item["run"], root / item["aggregate"]
        try:
            # Distinguish a genuinely pending extraction from an invalid completed artifact.
            status_path = run / "status.json"
            if (
                not status_path.exists()
                or json.loads(status_path.read_text()).get("status") == "running"
            ):
                readiness[model] = {"status": "pending_extraction"}
                continue
            validate_run(
                root, run, model=model, expected_contexts=contexts, input_roots=input_roots
            )
            if not (folder / "manifest.json").exists():
                readiness[model] = {"status": "pending_aggregation"}
                continue
            report, saved, status = validate_aggregate(
                root,
                folder,
                model,
                selected=item,
                expected_contexts=contexts,
                input_roots=input_roots,
            )
            accepted[model] = (folder, report, saved, status)
            readiness[model] = {
                "status": "verified",
                "run": run.name,
                "aggregate": item["aggregate"],
            }
        except (ValueError, KeyError, FileNotFoundError) as exc:
            readiness[model] = {"status": "invalid", "reason": str(exc)}
    return accepted, readiness


def merge_selected(root, selection, target, *, available_only=False):
    import pandas as pd

    root = Path(root)
    accepted, readiness = selected_aggregates(root, selection)
    if not accepted or (not available_only and len(accepted) != len(selection["models"])):
        raise ValueError("Selected outputs are not ready: " + json.dumps(readiness))
    geometry = {r[1]["catchments_sha256"] for r in accepted.values()}
    if len(geometry) != 1:
        raise ValueError("Catchment geometries differ across models")
    expected_contexts = {
        c["context_id"] for c in json.loads((root / selection["contexts"]).read_text())
    }
    coverage, areas, contracts = [], [], {}
    with fresh_output(target) as stage:
        for model, (folder, _report, saved, status) in accepted.items():
            values = pd.read_parquet(folder / (model + ".parquet"))
            if set(values.run) != {(root / selection["models"][model]["run"]).resolve().name}:
                raise ValueError("Aggregate rows differ from selected run")
            if not set(values.context_id) <= expected_contexts:
                raise ValueError("Aggregate has contexts outside selected census")
            if values.duplicated(["context_id", "catchment_gauge"]).any():
                raise ValueError("Duplicate selected context/catchment")
            shutil.copyfile(folder / (model + ".parquet"), stage / (model + ".parquet"))
            for name, frames in [("coverage.parquet", coverage), ("patch_areas.parquet", areas)]:
                frame = pd.read_parquet(folder / name)
                if len(frame):
                    if set(frame.model) != {model} or set(frame.run) != {values.run.iloc[0]}:
                        raise ValueError("Coverage or patch area rows differ from selected run")
                    frames.append(frame)
            contracts[model] = {
                **selection["models"][model],
                "aggregate_manifest_sha256": sha256(folder / "manifest.json"),
                "run_manifest_sha256": sha256(
                    root / selection["models"][model]["run"] / "manifest.json"
                ),
                "status_sha256": sha256(root / selection["models"][model]["run"] / "status.json"),
                "input_policy": saved.get(
                    "input_policy",
                    "independent_product_composites_v1"
                    if model not in {"croma", "olmoearth", "prithvi"}
                    else "native_product_v1",
                ),
                "contexts_total": status["contexts_total"],
                "input_population": saved.get("input_population"),
            }
        for name, frames in [("coverage.parquet", coverage), ("patch_areas.parquet", areas)]:
            pd.concat(frames, ignore_index=True).to_parquet(stage / name, index=False)
        manifest = {
            "schema_version": 2,
            "engineering": False,
            "partial": len(accepted) != len(selection["models"]),
            "readiness": readiness,
            "errors": [],
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "catchments_sha256": geometry.pop(),
            "selection": selection,
            "selected_runs": contracts,
            "contexts_by_model": {m: r[1]["contexts_by_model"][m] for m, r in accepted.items()},
            "outputs_sha256": {p.name: sha256(p) for p in stage.glob("*.parquet")},
        }
        (stage / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def validate_comparison_inputs(
    root, folder, *, engineering=False, selection=None, allow_partial=False
):
    """Verify both current selection and immutable model arrays before scoring."""
    root, folder = Path(root).resolve(), Path(folder).resolve()
    report = json.loads((folder / "manifest.json").read_text())
    if engineering:
        if not report.get("engineering"):
            raise ValueError("Fixture mode requires engineering vectors")
    else:
        if (
            report.get("schema_version") != 2
            or report.get("engineering")
            or (report.get("partial") and not allow_partial)
            or report.get("errors")
        ):
            raise ValueError("Use the validated selected-run merge (script 117)")
        from src.eo_inputs import ROUTES

        validate_selection(root, report["selection"])
        if selection is not None and report["selection"] != selection:
            raise ValueError("Merged output differs from current selected-run map")
        if (
            not report["selected_runs"]
            or not set(report["selected_runs"]) <= set(ROUTES)
            or (not allow_partial and set(report["selected_runs"]) != set(ROUTES))
        ):
            raise ValueError("Selected merge must account for all configured models")
        for model, item in report["selected_runs"].items():
            for relative, digest in [
                (Path(item["aggregate"]) / "manifest.json", item["aggregate_manifest_sha256"]),
                (Path(item["run"]) / "manifest.json", item["run_manifest_sha256"]),
                (Path(item["run"]) / "status.json", item["status_sha256"]),
            ]:
                if sha256(root / relative) != digest:
                    raise ValueError("Selected source changed: " + str(relative))
            validate_run(
                root,
                root / item["run"],
                model=model,
                input_roots=report["selection"].get("input_roots"),
            )
    expected = {"coverage.parquet", "patch_areas.parquet"} | {
        m + ".parquet" for m in report.get("selected_runs", {})
    }
    if not engineering and set(report["outputs_sha256"]) != expected:
        raise ValueError("Incomplete selected model manifest")
    if set(report["outputs_sha256"]) != {p.name for p in folder.glob("*.parquet")}:
        raise ValueError("Untracked or missing representation file")
    for name, digest in report["outputs_sha256"].items():
        if sha256(folder / name) != digest:
            raise ValueError("Changed catchment representation: " + name)
    return report
