"""Exploratory two-window follow-up to the first Limburg lag fit.

This does not replace the protocol's hourly lag estimand. It asks whether the
observed-history diagnostic yields a more stable descriptive association.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.case_crossover import fit_problem, prepare_problem  # noqa: E402

OUT = ROOT / "results/event_study/real_data_v1"
INPUT = OUT / "observed_rainfall_windows_matched_rows.csv"
SEED = 20260929
REPLICATES = 999
NAMES = ["warm_recent", "warm_earlier", "cold_recent", "cold_earlier"]


def design_matrix(frame: pd.DataFrame) -> np.ndarray:
    """Season-specific rainfall totals, scaled per 10 mm within each window."""
    warm = frame.warm.to_numpy(dtype=float)
    recent = frame.rain_1_24_mm.to_numpy(dtype=float) / 10.0
    earlier = frame.rain_25_72_mm.to_numpy(dtype=float) / 10.0
    return np.column_stack(
        [recent * warm, earlier * warm, recent * (1 - warm), earlier * (1 - warm)]
    )


def main() -> None:
    frame = pd.read_csv(INPUT)
    if frame[["rain_1_24_mm", "rain_25_72_mm"]].isna().any().any():
        raise AssertionError("the matched analysis contains incomplete windows")
    design = design_matrix(frame)
    problem = prepare_problem(design, frame.onset, frame.stratum, frame.block)
    fit = fit_problem(problem)
    eta = problem["design"] @ fit["coef"]
    top = np.full(problem["n_strata"], -np.inf)
    np.maximum.at(top, problem["codes"], eta)
    exponent = np.exp(eta - top[problem["codes"]])
    probability = exponent / (problem["operator"] @ exponent)[problem["codes"]]
    informative = frame.groupby("stratum").onset.transform("sum").gt(0)
    fit_rows = frame.loc[informative].copy()
    if len(fit_rows) != len(probability):
        raise AssertionError("diagnostic rows differ from the fitted rows")
    fit_rows["conditional_probability"] = probability
    fit_rows.loc[fit_rows.onset.eq(1)].nsmallest(20, "conditional_probability").to_csv(
        OUT / "observed_window_least_expected_onsets.csv", index=False
    )
    labels = pd.read_csv(OUT / "observed_window_all_blocks.csv").block.to_numpy()
    local_labels = pd.factorize(frame.block.to_numpy())[1]
    if len(local_labels) != problem["n_blocks"]:
        raise AssertionError("bootstrap block indexing differs from prepared problem")
    global_index = {int(block): i for i, block in enumerate(labels)}
    local_to_global = np.array([global_index[int(block)] for block in local_labels])
    rng = np.random.default_rng(SEED)
    draws = np.full((REPLICATES, len(NAMES)), np.nan)
    failures = []
    for i in range(REPLICATES):
        sampled = rng.integers(0, len(labels), len(labels))
        counts = np.bincount(sampled, minlength=len(labels))
        weights = counts[local_to_global[problem["stratum_block"]]].astype(float)
        try:
            draws[i] = fit_problem(problem, weights)["coef"]
            failures.append("")
        except (np.linalg.LinAlgError, RuntimeError, ValueError, FloatingPointError) as error:
            failures.append(f"{type(error).__name__}: {error}")
    table = pd.DataFrame(draws, columns=NAMES)
    table.insert(0, "draw", np.arange(1, REPLICATES + 1))
    table["failure"] = failures
    table.to_csv(OUT / "observed_window_bootstrap.csv", index=False)
    contrast = np.column_stack([draws[:, 0] - draws[:, 2], draws[:, 1] - draws[:, 3]])
    points = list(fit["coef"]) + [fit["coef"][0] - fit["coef"][2], fit["coef"][1] - fit["coef"][3]]
    all_draws = np.column_stack([draws, contrast])
    names = NAMES + ["warm_minus_cold_recent", "warm_minus_cold_earlier"]
    estimates = []
    for name, point, sample in zip(names, points, all_draws.T, strict=True):
        valid = sample[np.isfinite(sample)]
        estimates.append(
            {
                "term": name,
                "log_association_per_10mm": point,
                "bootstrap_lower_95": np.quantile(valid, 0.025) if len(valid) else np.nan,
                "bootstrap_upper_95": np.quantile(valid, 0.975) if len(valid) else np.nan,
                "successful_draws": len(valid),
            }
        )
    pd.DataFrame(estimates).to_csv(OUT / "observed_window_followup_estimates.csv", index=False)
    # Inspect conspicuous calendar blocks without redefining the main sample.
    largest_blocks = frame.loc[frame.onset.eq(1)].groupby("block").size().nlargest(5).index
    block_checks = [202107, *[int(block) for block in largest_blocks]]
    influence = []
    for block in dict.fromkeys(block_checks):
        keep = frame.block.ne(block).to_numpy()
        subset = frame.loc[keep]
        refit = fit_problem(
            prepare_problem(design[keep], subset.onset, subset.stratum, subset.block)
        )
        influence.append(
            {
                "omitted_block": block,
                "onsets_removed": int(frame.loc[~keep, "onset"].sum()),
                "onsets_retained": refit["n_onsets"],
                "warm_minus_cold_recent": refit["coef"][0] - refit["coef"][2],
                "warm_minus_cold_earlier": refit["coef"][1] - refit["coef"][3],
                "dispersion": refit["dispersion"],
            }
        )
    pd.DataFrame(influence).to_csv(OUT / "observed_window_month_influence.csv", index=False)
    manifest = {
        "status": "exploratory_followup_not_original_estimand",
        "input_sha256": hashlib.sha256(INPUT.read_bytes()).hexdigest(),
        "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "seed": SEED,
        "replicates": REPLICATES,
        "failed_draws": sum(bool(failure) for failure in failures),
        "n_rows": fit["n_rows"],
        "n_onsets": fit["n_onsets"],
        "n_strata": fit["n_strata"],
        "n_global_blocks": len(labels),
        "dispersion": fit["dispersion"],
        "log_likelihood": fit["loglik"],
        "onset_probability_minimum": float(probability[problem["onset"] > 0].min()),
    }
    (OUT / "observed_window_followup_run.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(pd.DataFrame(estimates).to_string(index=False, float_format=lambda x: f"{x:.3f}"))
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
