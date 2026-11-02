"""The same adaptive-average bins, evaluated as separable on-device matrices.

PyTorch's supported CPU/divisible MPS cases retain their original operator.
Only unsupported MPS non-divisible shapes use floor/ceil average-bin weights.
There are no learned parameters, resolution changes or checkpoint-key changes.
"""

import math
from functools import lru_cache

import torch
from torch import nn
from torch.nn import functional as F


@lru_cache(maxsize=64)
def weights(length, output, device):
    matrix = torch.zeros(output, length, dtype=torch.float32)
    for i in range(output):
        left = math.floor(i * length / output)
        right = math.ceil((i + 1) * length / output)
        matrix[i, left:right] = 1 / (right - left)
    return matrix.to(device)


class OnDeviceAdaptiveAvgPool2d(nn.AdaptiveAvgPool2d):
    def forward(self, x):
        size = self.output_size
        shape = (size, size) if isinstance(size, int) else size
        h, w = x.shape[-2:]
        oh, ow = (h if shape[0] is None else shape[0]), (w if shape[1] is None else shape[1])
        if x.device.type != "mps" or (h % oh == 0 and w % ow == 0):
            return F.adaptive_avg_pool2d(x, size)
        # Retain full-precision accumulation even under mixed-precision heads.
        with torch.autocast("mps", enabled=False):
            result = torch.matmul(weights(h, oh, str(x.device)), x.float())
            result = torch.matmul(result, weights(w, ow, str(x.device)).T)
        return result.to(x.dtype)


def install_on_device_pools(model):
    count = 0
    for name, child in model.named_children():
        if isinstance(child, nn.AdaptiveAvgPool2d):
            replacement = OnDeviceAdaptiveAvgPool2d(child.output_size)
            replacement.train(child.training)
            setattr(model, name, replacement)
            count += 1
        else:
            count += install_on_device_pools(child)
    return count
