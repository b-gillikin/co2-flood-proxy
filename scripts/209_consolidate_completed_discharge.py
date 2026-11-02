"""Consolidate all ten completed, model-specific discharge experiments.

Reads frozen reviews; no fitting, re-selection or favorable-case filtering.
"""

import argparse
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=False)
    base = ROOT / "results/limburg_individual_experiments_v1"
    q = json.loads((base / "queue/progress.json").read_text())
    if q["status"] != "completed" or any(v["status"] != "completed" for v in q["tasks"].values()):
        raise ValueError("Primary queue incomplete")
    design = json.loads(
        (ROOT / "config/limburg_individual_encoder_experiments_v1.json").read_text()
    )
    models = [
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
    ]
    hashes = {}
    records = []
    cases = []
    audits = []
    for model in models:
        for directory in sorted((base / "scores").glob(model + "__*")):
            review = directory / "review"
            if not review.exists():
                continue
            audit = json.loads((review / "audit.json").read_text())
            if audit["status"] != "passed" or audit["census_rows"] != 15392:
                raise ValueError("Review did not pass complete census")
            audits.append(dict(job=directory.name, **audit))
            for name in [
                "audit.json",
                "paired-effects.csv",
                "illustrative-cases.csv",
                "results-note.txt",
            ]:
                path = review / name
                hashes[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
            with (review / "paired-effects.csv").open() as f:
                for row in csv.DictReader(f):
                    if row["support"] == "pipeline_with_fallback" and row["reference"] in [
                        "raw_correction",
                        "ablation_correction",
                    ]:
                        records.append(dict(job=directory.name, **row))
            with (review / "illustrative-cases.csv").open() as f:
                for row in csv.DictReader(f):
                    cases.append(dict(job=directory.name, **row))
    selected = []
    for r in records:
        if (
            r["group"] == "whole_network"
            and r["stratum"] == "high_water"
            and r["scenario"] == "local_q_absent"
            and "__ablation" not in r["job"]
        ):
            selected.append(r)
    if {r["model"] for r in selected} != set(models):
        raise ValueError("Incomplete ten-model primary synthesis")
    result = dict(
        status="completed_readout",
        primary_model_count=10,
        experiment_designs=design["experiments"],
        generator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        reviewed_jobs=len(audits),
        primary_local_q_absent_high_water=selected,
        all_declared_effects=records,
        source_hashes=hashes,
        review_audits=audits,
        interpretation="Exploratory model-specific tests, not a common-input model leaderboard. Negative MAE differences favor encoder. Repeated assessments are not independent storms. Country strata describe this network, not national FEWS. Zero flood contrasts often mean the same fallback was selected; they do not prove intrinsic encoder equivalence.",
        scope=design["shared"]["target"],
    )
    (a.output / "readout.json").write_text(json.dumps(result, indent=2) + "\n")
    with (a.output / "effects.csv").open("w") as f:
        w = csv.DictWriter(f, fieldnames=list(records[0]))
        w.writeheader()
        w.writerows(records)
    # Existing selected diagnostic cases are preserved with their selection rule;
    # do not present them as a random sample or test them as independent floods.
    fields = sorted(set().union(*(r.keys() for r in cases)))
    with (a.output / "diagnostic-cases.csv").open("w") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(cases)
    lines = [
        "# Completed discharge experiments —2 November2026",
        "",
        "Internal interpretation aid; Brian writes dissertation prose.",
        "",
        "All ten model-specific experiments and declared configuration comparisons are complete. These results concern next24h discharge correction. Spatial mapping tests are a separate task; their results cannot be inferred here.",
        "",
        "| Model | Local-Q-absent high-water MAE difference (mm/h) | Whole-year interval | Assessments / storms |",
        "|---|---:|---:|---:|",
    ]
    for r in selected:
        lines.append(
            f"| {r['model']} | {float(r['estimate']):.6g} | [{float(r['lower']):.6g}, {float(r['upper']):.6g}] | {r['assessments']} / {r['storms']} |"
        )
    lines += [
        "",
        "DOFA uses held-watercourse transfer; its rich-basin regime aliases local-Q absence. Other experiments use same-gauge annual heads. See readout.json for every model-specific design.",
        "",
        "Negative differences favor the encoder increment over its matched raw-input correction. Assessments, sites, source years and feature support differ between model-specific tests; do not rank these point estimates as an encoder tournament.",
        "",
        "Read effects.csv for every scenario, country, gauge, watercourse and flood stratum; read diagnostic-cases.csv for the previously selected helped/harmed cases. Uncertainty is the existing999 shared whole-year bootstrap conditional on fitted procedures. Nonfinite draws and undefined strata remain in the tables. No multiplicity-adjusted superiority claim.",
        "",
        "Presto and Galileo complete the earlier partial evidence: neither establishes broad discharge benefit. Presto has some high-water improvements but mixed all-flow effects; Galileo is worse overall when all discharge is absent. The documented-flood evidence is sparse and often falls back identically. Consult support-specific contrasts before attributing differences to the encoder.",
        "",
        "The applied mapping branch tests spatial outputs, label efficiency, cost and local reference agreement. Its justification is the distinct task, not an expectation that a more favorable result must appear.",
    ]
    (a.output / "readout.md").write_text("\n".join(lines) + "\n")
    print(json.dumps(dict(status=result["status"], models=10, reviewed_jobs=len(audits))))


if __name__ == "__main__":
    main()
