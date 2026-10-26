"""Undefined normalization is encoder non-support, not a fabricated observation."""

import numpy as np

from src.eo_croma_supported_inputs import usable_support


def test_one_observed_pixel_is_explicitly_unsupported():
    values = np.zeros((2, 2, 2), dtype=np.float32)
    valid = np.array([[True, False], [False, False]])
    supported, counts = usable_support(values, valid, size=2)
    assert not supported.any()
    assert counts["one_pixel_patches"] == 1
    assert counts["unsupported_observed_pixels"] == 1
    assert valid.sum() == 1


def test_constant_channel_is_unsupported():
    values = np.ones((2, 2, 2), dtype=np.float32)
    valid = np.ones((2, 2), dtype=bool)
    supported, counts = usable_support(values, valid, size=2)
    assert not supported.any()
    assert counts["constant_channel_patches"] == 1


def test_supported_neighbour_is_retained_without_mutation():
    values = np.array(
        [[[1, 2, 5, 5], [3, 4, 5, 5]], [[2, 4, 6, 6], [6, 8, 6, 6]]], dtype=np.float32
    )
    original = values.copy()
    valid = np.ones((2, 4), dtype=bool)
    supported, counts = usable_support(values, valid, size=2)
    assert supported[:, :2].all()
    assert not supported[:, 2:].any()
    assert counts["unsupported_observed_pixels"] == 4
    np.testing.assert_array_equal(values, original)


def test_versioned_wrapper_imports_declared_policies():
    import importlib.util
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "scripts/133_extract_supported_croma.py"
    spec = importlib.util.spec_from_file_location("croma_supported_wrapper", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.SUPPORT_POLICY == "croma_sample_sd_defined_per_native_patch_v1"
