"""Publisher scale/date conventions and missing-data behavior, without weights."""

from datetime import datetime
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from src.eo_encoder_corrections import (
    SATMAE_MEAN,
    SATMAE_STD,
    croma_input,
    install,
    pixel_months,
    satmae_input,
)


def test_satmae_publisher_quantization_and_missing_neutral_value():
    values = np.broadcast_to(SATMAE_MEAN[:, None, None], (10, 2, 3)).copy()
    values[:, 0, 0] -= 3 * SATMAE_STD
    values[:, 0, 2] += 3 * SATMAE_STD
    valid = np.ones((2, 3), bool)
    valid[1, 1] = False
    values[:, 1, 1] = np.nan
    x = satmae_input(values, valid)
    assert np.isfinite(x).all() and x.dtype == np.float32
    np.testing.assert_array_equal(x[:, 0, 0], 0)
    np.testing.assert_array_equal(x[:, 0, 2], 1)
    np.testing.assert_allclose(x[:, 0, 1], 127 / 255)
    np.testing.assert_allclose(x[:, 1, 1], 127 / 255)


def test_croma_scale_and_masked_outlier_do_not_change_observed_stretch():
    values = np.stack([np.arange(64), np.arange(64) * 2 - 30]).reshape(2, 8, 8).astype("float32")
    valid = np.ones((8, 8), bool)
    valid[0, 0] = False
    first = croma_input(values, valid)
    values[:, 0, 0] = 1e20
    second = croma_input(values, valid)
    np.testing.assert_array_equal(first, second)
    assert first.min() >= 0 and first.max() <= 1
    np.testing.assert_allclose(first[:, 0, 0], 127 / 255)
    with pytest.raises(ValueError, match="constant"):
        croma_input(np.ones_like(values), valid)


def test_pixel_months_respect_dates_including_missing_slots_and_year_boundary():
    frames = []
    for dates, valid in [
        (["2020-12-31", "2021-01-01"], [True, True]),
        (["NaT", "2021-02-01"], [False, True]),
    ]:
        days = np.array(dates, dtype="datetime64[D]").astype(float).reshape(1, 2)
        frames.append({"valid": np.array([valid]), "days": days})
    np.testing.assert_array_equal(pixel_months(frames, np.ones((1, 2), bool)), [[11, 0], [0, 1]])
    frames[1]["valid"][0, 0] = True
    with pytest.raises(ValueError, match="acquisition day"):
        pixel_months(frames, np.ones((1, 2), bool))


@pytest.mark.parametrize("count", [1, 4, 12])
def test_anysat_supplies_one_based_dates_for_all_declared_sequence_lengths(count):
    captured = []

    class Model:
        def __call__(self, data, **kwargs):
            captured.append(data)
            return torch.ones(1, 768)

    class Encoder:
        def forward(self, patch):
            raise AssertionError("Historical AnySat branch should not be called")

    module = SimpleNamespace(Encoder=Encoder, tensor=lambda a: torch.tensor(a).float())
    install(module)
    frames = [
        {
            "values": np.full((10, 2, 2), 1000, dtype="float32"),
            "valid": np.ones((2, 2), bool),
            "metadata": {"representative_date": f"2020-{month:02d}-01T00:00:00+00:00"},
        }
        for month in range(1, count + 1)
    ]
    encoder = Encoder()
    encoder.name = "anysat"
    encoder.model = Model()
    encoder.forward({**frames[0], "frames": frames})
    dates = [datetime(2020, m, 1).timetuple().tm_yday for m in range(1, count + 1)]
    assert captured[0]["s2_dates"].tolist() == [dates]
    assert captured[0]["s2"].shape == (1, count, 10, 2, 2)


def test_install_is_idempotent_and_unchanged_routes_delegate():
    class Encoder:
        def forward(self, patch):
            return patch["marker"]

    module = SimpleNamespace(Encoder=Encoder)
    install(module)
    first = Encoder.forward
    install(module)
    assert first is Encoder.forward
    encoder = Encoder()
    encoder.name = "galileo"
    encoder.model = None
    assert encoder.forward({"values": None, "valid": None, "marker": 123}) == 123
