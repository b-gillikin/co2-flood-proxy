import numpy as np
import pytest

from src.eo_token_masks import token_observations


def test_thin_observed_sliver_does_not_become_a_visible_token():
    valid = np.zeros((2, 8, 8), dtype=bool)
    valid[:, 1, :] = True
    assert valid.any()
    assert not token_observations(valid, 4).any()


def test_complete_tokens_and_temporal_missingness_are_preserved():
    valid = np.ones((2, 8, 8), dtype=bool)
    valid[1, 1, 1] = False
    actual = token_observations(valid, 4)
    assert actual[0].all()
    assert not actual[1, :4, :4].any()
    assert actual[1, 4:, :].all()
    assert not (actual & ~valid).any()
    np.testing.assert_array_equal(actual, token_observations(actual, 4))


def test_rejects_unaligned_shapes():
    with pytest.raises(ValueError):
        token_observations(np.ones((7, 8), dtype=bool), 4)
