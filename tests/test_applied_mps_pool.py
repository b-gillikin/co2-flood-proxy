"""Output, gradient and serialization equivalence for the local MPS workaround."""

import numpy as np
import pytest
import torch
from torch import nn

from applied_mps_pool import MPSCompatibleAdaptiveAvgPool2d, install_mps_pooling


@pytest.mark.parametrize(
    "shape,size", [((14, 14), 3), ((14, 14), 6), ((7, 7), 2), ((14, 14), 1), ((14, 14), (None, 3))]
)
@pytest.mark.parametrize("device", ["cpu", "mps"])
def test_exact_pool_outputs_and_input_gradients(shape, size, device):
    if device == "mps" and not torch.backends.mps.is_available():
        pytest.skip("MPS unavailable")
    np.random.seed(42)
    torch.manual_seed(42)
    cpu = torch.randn(2, 4, *shape, requires_grad=True)
    x = cpu.detach().to(device).requires_grad_(True)
    expected = nn.AdaptiveAvgPool2d(size)(cpu)
    actual = MPSCompatibleAdaptiveAvgPool2d(size)(x)
    weights = torch.randn_like(expected)
    (expected * weights).sum().backward()
    (actual * weights.to(device)).sum().backward()
    torch.testing.assert_close(actual.cpu(), expected, rtol=1e-5, atol=1e-6)
    torch.testing.assert_close(x.grad.cpu(), cpu.grad, rtol=1e-5, atol=1e-6)


def test_replacement_preserves_checkpoint_and_optimizer_parameters():
    model = nn.Sequential(nn.Conv2d(4, 8, 1), nn.Sequential(nn.AdaptiveAvgPool2d(3)))
    before = {k: v.clone() for k, v in model.state_dict().items()}
    params = [id(p) for p in model.parameters()]
    assert install_mps_pooling(model) == 1
    assert isinstance(model[1][0], MPSCompatibleAdaptiveAvgPool2d)
    assert params == [id(p) for p in model.parameters()]
    assert before.keys() == model.state_dict().keys()
    for name, value in before.items():
        torch.testing.assert_close(value, model.state_dict()[name])


@pytest.mark.parametrize("device", ["cpu", "mps"])
def test_batchnorm_layout_retains_values_parameter_gradients_and_running_stats(device):
    from applied_mps_pool import install_mps_batchnorm_layout

    if device == "mps" and not torch.backends.mps.is_available():
        pytest.skip("MPS unavailable")
    torch.manual_seed(42)
    expected = nn.BatchNorm2d(4)
    actual = nn.BatchNorm2d(4).to(device)
    actual.load_state_dict(expected.state_dict())
    assert install_mps_batchnorm_layout(actual) == 1
    x = torch.randn(2, 4, 14, 14).transpose(-1, -2).requires_grad_(True)
    y = x.detach().to(device).requires_grad_(True)
    a = expected(x)
    b = actual(y)
    gradient = torch.randn_like(a).transpose(-1, -2)
    a.backward(gradient)
    b.backward(gradient.to(device))
    torch.testing.assert_close(a, b.cpu(), rtol=1e-4, atol=1e-5)
    torch.testing.assert_close(x.grad, y.grad.cpu(), rtol=1e-4, atol=1e-5)
    for n, p in expected.named_parameters():
        torch.testing.assert_close(
            p.grad, dict(actual.named_parameters())[n].grad.cpu(), rtol=1e-4, atol=1e-5
        )
    for n, v in expected.state_dict().items():
        torch.testing.assert_close(v, actual.state_dict()[n].cpu(), rtol=1e-4, atol=1e-5)
