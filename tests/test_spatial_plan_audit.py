"""Prevent unsafe reuse and understated source-refit counts."""

import pytest

from src.spatial_plan_audit import FIT_FIELDS, fit_identity, source_search_counts


def job():
    return {
        "training": {k: 42 if k == "seed" else "a" * 64 for k in FIT_FIELDS},
        "evaluation": {"test": "event-A"},
        "report_id": "water",
    }


def test_new_evaluation_can_share_an_identical_fit():
    a, b = job(), job()
    b["evaluation"] = {"test": "event-B", "reference": "another-reference"}
    b["report_id"] = "flood-change"
    assert fit_identity(a) == fit_identity(b)


@pytest.mark.parametrize("key", sorted(FIT_FIELDS))
def test_every_training_or_selection_change_prevents_reuse(key):
    a, b = job(), job()
    b["training"][key] = 1729 if key == "seed" else "b" * 64
    assert fit_identity(a) != fit_identity(b)


def test_future_training_fields_are_hashed_and_unknown_root_fields_rejected():
    a, b = job(), job()
    b["training"]["transductive_target_images"] = ["target-B"]
    assert fit_identity(a) != fit_identity(b)
    a["new_model_setting"] = "untracked"
    with pytest.raises(ValueError):
        fit_identity(a)


def test_incomplete_identity_cannot_authorize_reuse():
    a = job()
    del a["training"]["train_labels_sha256"]
    with pytest.raises(ValueError):
        fit_identity(a)


def test_changed_final_population_costs_all_refit_seeds():
    assert source_search_counts(3)["shared_policy_fits"] == 5
    assert source_search_counts(3, expanded_final_population=True) == {
        "independent_search_fits": 12,
        "shared_policy_fits": 6,
        "final_population_changed": True,
    }
    assert source_search_counts(16, expanded_final_population=True)["shared_policy_fits"] == 19
