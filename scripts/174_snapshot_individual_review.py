"""Snapshot audited completed jobs without fitting or changing the live queue.

Event examples are deliberately post-hoc extremes among positive-EO predictions,
not independent validation or selected evidence of general skill.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "results/limburg_individual_experiments_v1"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    tables, modes, examples, ablations, receipts = [], [], [], [], {}
    for path in sorted((SOURCE / "scores").glob("*/review/audit.json")):
        job = path.parent.parent
        audit = json.loads(path.read_text())
        manifest = json.loads((job / "manifest.json").read_text())
        assert audit["status"] == "passed"
        assert audit["source_manifest_sha256"] == digest(job / "manifest.json")
        for name, expected in manifest["outputs"].items():
            assert digest(job / name) == expected, (job.name, name)
        for name, expected in manifest["source_hashes"].items():
            assert digest(ROOT / name) == expected, name
        for name in ["audit.json", "paired-effects.csv", "case-effects.parquet"]:
            p = path.parent / name
            receipts[str(p.relative_to(ROOT))] = digest(p)
        table = pd.read_csv(path.parent / "paired-effects.csv")
        if job.name.endswith("__ablation"):
            ablations.append(table[table.group.isin(["whole_network", "country_NL", "country_DE"])])
            continue
        tables.append(table[table.reference.isin(["raw_correction", "conventional_mean"])
                            & table.group.isin(["whole_network", "country_NL", "country_DE"])])
        meta = pd.read_parquet(path.parent / "case-effects.parquet")
        cases = pd.read_parquet(job / "cases.parquet")
        assert meta.assessment_id.tolist() == cases.assessment_id.tolist()
        assert meta.index.equals(pd.RangeIndex(len(meta)))
        eligible = meta.raw_available & meta.encoder_available & meta.outcome_valid
        for country, subset in [("whole_network", meta), *meta.groupby("country")]:
            for mode, count in subset.encoder_prediction_mode.value_counts().items():
                modes.append(dict(job=job.name, country=country, mode=mode, assessments=int(count)))
        if manifest["scenario"] != "local_q_absent":
            continue
        delta = "encoder_correction_minus_raw_correction"
        # Stable, explicit selection; no reranking by observed peak or flood label.
        selected = meta[eligible & meta.encoder_prediction_mode.eq("encoder_correction")]
        with np.load(job / "predictions.npz") as arrays:
            for country, subset in selected.groupby("country"):
                for direction, ascending in [("improvement", True), ("deterioration", False)]:
                    ordered = subset.sort_values([delta, "assessment_id"], ascending=[ascending, True])
                    if ordered.empty:
                        continue
                    i = ordered.index[0]
                    row = meta.loc[i]
                    if (ascending and row[delta] >= 0) or (not ascending and row[delta] <= 0):
                        continue
                    observed = arrays["observed"][i]
                    np.testing.assert_allclose(
                        np.abs(arrays["encoder_correction"][i] - observed).mean()
                        - np.abs(arrays["raw_correction"][i] - observed).mean(),
                        row[delta], rtol=1e-10, atol=1e-12,
                    )
                    factor = float(row.area_km2) / 3.6
                    record = dict(
                        model=manifest["model"], country=country, direction=direction,
                        assessment_id=row.assessment_id, storm_id=row.storm_id,
                        station=row.station, issue_utc=str(row.issue_utc),
                        verification_clean=bool(row.verification_clean),
                        documented_flood=bool(row.documented_flood_overlap),
                        delta_mae_m3s=float(row[delta]) * factor,
                        observed_peak_m3s=float(observed.max()) * factor,
                        observed_peak_h=int(observed.argmax()) + 1,
                    )
                    for name in ["conventional_mean", "raw_correction", "encoder_correction"]:
                        prediction = arrays[name][i]
                        record[name + "_mae_m3s"] = float(np.abs(prediction - observed).mean()) * factor
                        record[name + "_peak_m3s"] = float(prediction.max()) * factor
                        record[name + "_peak_h"] = int(prediction.argmax()) + 1
                    examples.append(record)
    assert tables, "No audited jobs available"
    pd.concat(tables, ignore_index=True).to_csv(args.output / "effects.csv", index=False)
    if ablations:
        pd.concat(ablations, ignore_index=True).to_csv(args.output / "configuration-effects.csv", index=False)
    pd.DataFrame(modes).to_csv(args.output / "prediction-modes.csv", index=False)
    pd.DataFrame(examples).to_csv(args.output / "event-examples.csv", index=False)
    (args.output / "manifest.json").write_text(json.dumps(dict(
        status="partial_snapshot_not_final_ten_model_result",
        created_utc=datetime.now(timezone.utc).isoformat(),
        script_sha256=digest(Path(__file__)), source_hashes=receipts,
        models=sorted({t.model.iloc[0] for t in tables}),
        jobs=len(tables), configuration_comparisons=len(ablations),
        selection="Local-Q absence; largest signed change per model/country among positive-EO predictions; post-hoc examples",
        outputs={p.name: digest(p) for p in args.output.glob("*.csv")},
    ), indent=2) + "\n")


if __name__ == "__main__":
    main()
