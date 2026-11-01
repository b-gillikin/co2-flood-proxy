"""Conventional four-downsampling U-Net comparator, alongside the compact control."""

import torch
from torch import nn
from torch.nn import functional as F


class StandardUNet(nn.Module):
    def __init__(self, channels, classes):
        super().__init__()

        def block(a, b):
            return nn.Sequential(
                nn.Conv2d(a, b, 3, padding=1),
                nn.GroupNorm(8, b),
                nn.ReLU(),
                nn.Conv2d(b, b, 3, padding=1),
                nn.GroupNorm(8, b),
                nn.ReLU(),
            )

        self.encoders = nn.ModuleList(
            [block(channels, 32), block(32, 64), block(64, 128), block(128, 256), block(256, 512)]
        )
        self.decoders = nn.ModuleList(
            [block(768, 256), block(384, 128), block(192, 64), block(96, 32)]
        )
        self.head = nn.Conv2d(32, classes, 1)

    def forward(self, x):
        skips = []
        for layer in self.encoders:
            if skips:
                x = F.max_pool2d(x, 2)
            x = layer(x)
            skips.append(x)
        for layer, skip in zip(self.decoders, reversed(skips[:-1]), strict=True):
            x = F.interpolate(x, size=skip.shape[-2:], mode="bilinear", align_corners=False)
            x = layer(torch.cat([x, skip], dim=1))
        return self.head(x)
