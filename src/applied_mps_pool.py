"""Exact adaptive averaging for MPS shapes unsupported by the held runtime.

Only non-divisible adaptive pools cross to CPU. Device copies retain autograd;
there are no parameters, resizing substitutions or checkpoint-key changes.
"""

import torch.nn.functional as F
from torch import nn


class MPSCompatibleAdaptiveAvgPool2d(nn.AdaptiveAvgPool2d):
    def forward(self, x):
        size = self.output_size
        shape = (size, size) if isinstance(size, int) else size
        shape = tuple(x.shape[-2 + i] if v is None else v for i, v in enumerate(shape))
        if x.device.type == "mps" and any(n % o for n, o in zip(x.shape[-2:], shape, strict=True)):
            return F.adaptive_avg_pool2d(x.to("cpu"), self.output_size).to(x.device)
        return super().forward(x)


def install_mps_pooling(module):
    """Replace only parameter-free adaptive average pools; keep state keys."""
    count = 0
    for name, child in module.named_children():
        if isinstance(child, nn.AdaptiveAvgPool2d):
            replacement = MPSCompatibleAdaptiveAvgPool2d(child.output_size)
            replacement.train(child.training)
            setattr(module, name, replacement)
            count += 1
        else:
            count += install_mps_pooling(child)
    return count


def _contiguous_mps_input(module, inputs):
    (x,) = inputs
    return (x.contiguous(),) if x.device.type == "mps" else inputs


def _contiguous_mps_gradient(module, inputs, output):
    if output.device.type == "mps" and output.requires_grad:
        output.register_hook(lambda gradient: gradient.contiguous())


def install_mps_batchnorm_layout(module):
    """Keep BatchNorm inputs/backward gradients contiguous; values unchanged."""
    count = 0
    for child in module.modules():
        if isinstance(child, (nn.BatchNorm2d, nn.SyncBatchNorm)):
            child.register_forward_pre_hook(_contiguous_mps_input)
            child.register_forward_hook(_contiguous_mps_gradient)
            count += 1
    return count
