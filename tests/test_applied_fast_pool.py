"""Prove output/gradient equivalence before replacing CPU transfer pooling."""

import numpy as np
import pytest
import torch
from torch import nn

from applied_fast_pool import OnDeviceAdaptiveAvgPool2d, install_on_device_pools


@pytest.mark.parametrize(
    "shape,size",
    [
        ((7, 7), 2),
        ((14, 14), 3),
        ((14, 14), 6),
        ((7, 9), (3, 4)),
        ((14, 14), 1),
        ((7, 7), (None, 3)),
    ],
)
@pytest.mark.parametrize("device", ["cpu", "mps"])
def test_same_bins_values_and_gradients(shape, size, device):
    if device == "mps" and not torch.backends.mps.is_available():
        pytest.skip("MPS unavailable")
    torch.manual_seed(42)
    np.random.seed(42)
    x = torch.randn(2, 4, *shape, requires_grad=True)
    z = x.detach().to(device).requires_grad_(True)
    y = nn.AdaptiveAvgPool2d(size)(x)
    r = OnDeviceAdaptiveAvgPool2d(size)(z)
    gradient = torch.randn_like(y)
    y.backward(gradient)
    r.backward(gradient.to(device))
    torch.testing.assert_close(r.cpu(), y, atol=2e-6, rtol=1e-5)
    torch.testing.assert_close(z.grad.cpu(), x.grad, atol=2e-6, rtol=1e-5)


def test_no_new_state_or_parameters():
    model = nn.Sequential(nn.AdaptiveAvgPool2d(3), nn.Conv2d(4, 2, 1))
    keys = set(model.state_dict())
    parameters = [id(p) for p in model.parameters()]
    assert install_on_device_pools(model) == 1
    assert keys == set(model.state_dict()) and parameters == [id(p) for p in model.parameters()]
