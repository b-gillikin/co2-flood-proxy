"""Do not turn the expected output-layer omission into a blanket partial load."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

torch = pytest.importorskip("torch")
SPEC = importlib.util.spec_from_file_location(
    "eo_load", Path(__file__).parents[1] / "environments/eo-screen/check_load.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_default_output_norm_is_nonaffine_layernorm_equivalent():
    norm = torch.nn.LayerNorm(4, eps=1e-6)
    model = SimpleNamespace(fc_norm=norm)
    mismatch = SimpleNamespace(missing_keys=["fc_norm.weight", "fc_norm.bias"], unexpected_keys=[])
    MODULE.validate_copernicus_output_norm(model, mismatch)
    x = torch.tensor([[1.0, 3.0, 5.0, 8.0]])
    assert torch.equal(norm(x), torch.nn.functional.layer_norm(x, (4,), eps=1e-6))
    with torch.no_grad():
        norm.weight[0] = 2.0
    with pytest.raises(ValueError, match="scale"):
        MODULE.validate_copernicus_output_norm(model, mismatch)


@pytest.mark.parametrize(
    "extra_missing,unexpected", [(["blocks.0.norm1.weight"], []), ([], ["wrong_key"])]
)
def test_unexpected_missing_or_extra_weights_still_fail(extra_missing, unexpected):
    model = SimpleNamespace(fc_norm=torch.nn.LayerNorm(4, eps=1e-6))
    mismatch = SimpleNamespace(
        missing_keys=["fc_norm.weight", "fc_norm.bias"] + extra_missing, unexpected_keys=unexpected
    )
    with pytest.raises(ValueError):
        MODULE.validate_copernicus_output_norm(model, mismatch)
