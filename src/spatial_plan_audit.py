"""Conservative compute identities for planning; no fitting or cache loading."""

import hashlib
import json

FIT_FIELDS = {
    "model_contract_sha256",
    "train_inputs_sha256",
    "train_labels_sha256",
    "validation_contract_sha256",
    "preprocessing_sha256",
    "initial_state_sha256",
    "optimization_policy_sha256",
    "sampling_augmentation_sha256",
    "runtime_numerics_sha256",
    "seed",
}


def fit_identity(job):
    """Hash ALL supplied training fields; evaluation/report identity is separate.

    Hash descriptors include the permitted selection/tuning population. A shared
    fit still needs a separate fit/selection-versus-test leakage check for every
    evaluation. This function certifies identity, not scientific eligibility.
    """
    if set(job) - {"training", "evaluation", "report_id"}:
        raise ValueError("Unknown job fields: put scientific fit settings in training")
    training = job.get("training", {})
    if not isinstance(training, dict) or FIT_FIELDS - set(training):
        raise ValueError("Incomplete explicit training identity")
    if type(training["seed"]) is not int or training["seed"] < 0:
        raise ValueError("Require a nonnegative integer seed")
    for key in FIT_FIELDS - {"seed"}:
        value = training[key]
        if not isinstance(value, str) or len(value) != 64 or any(
            c not in "0123456789abcdef" for c in value
        ):
            raise ValueError("Require pinned SHA256: " + key)
    raw = json.dumps(training, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(raw.encode()).hexdigest()


def source_search_counts(rates, seeds=3, *, expanded_final_population=False):
    """Count single-selection-block fits; source CV folds cost separately."""
    if type(rates) is not int or type(seeds) is not int or min(rates, seeds) < 1:
        raise ValueError("Positive integer candidate and seed counts required")
    extra = seeds if expanded_final_population else 0
    independent = rates * seeds + extra
    shared = rates + (seeds if expanded_final_population else seeds - 1)
    return {
        "independent_search_fits": independent,
        "shared_policy_fits": shared,
        "final_population_changed": expanded_final_population,
    }
