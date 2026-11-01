"""Model-specific native spatial tasks. Imported only by a named task worker.

No pooling into catchment vectors, no modification of the running environments,
and no implicit downloads. New decoders are explicitly untrained until fitted.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import torch
from torch import nn

ROOT = Path(__file__).resolve().parents[1]
HELD = ROOT / "data/raw/limburg_dynamic_model_weights"


def module_at(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def terramind():
    from terratorch.models.encoder_decoder_factory import EncoderDecoderFactory

    model = EncoderDecoderFactory().build_model(
        task="segmentation",
        backbone="terramind_v1_tiny",
        backbone_pretrained=False,
        backbone_modalities=["S2L1C", "S1GRD"],
        backbone_merge_method="mean",
        necks=[
            dict(name="SelectIndices", indices=[2, 5, 8, 11]),
            dict(name="ReshapeTokensToImage", remove_cls_token=False),
            dict(name="LearnedInterpolateToPyramidal"),
        ],
        decoder="UNetDecoder",
        decoder_channels=[256, 128, 64, 32],
        head_dropout=0.1,
        num_classes=2,
    )
    state = torch.load(
        HELD / "models/terramind/TerraMind_v1_tiny.pt", map_location="cpu", weights_only=True
    )
    # The published checkpoint includes other modalities/decoder components.
    # Every key required by this encoder must nevertheless be present.
    model.encoder.load_state_dict({k: state[k] for k in model.encoder.state_dict()}, strict=True)
    model.freeze_encoder()
    return model


def prithvi():
    from terratorch.models.backbones.prithvi_vit import PRETRAINED_BANDS, checkpoint_filter_fn_vit
    from terratorch.models.encoder_decoder_factory import EncoderDecoderFactory

    model = EncoderDecoderFactory().build_model(
        task="segmentation",
        backbone="prithvi_eo_v2_tiny_tl",
        backbone_pretrained=False,
        backbone_num_frames=1,
        backbone_bands=PRETRAINED_BANDS,
        decoder="UperNetDecoder",
        decoder_channels=256,
        necks=[
            dict(name="SelectIndices", indices=[2, 5, 8, 11]),
            dict(name="ReshapeTokensToImage"),
            dict(name="InterpolateToPyramidal"),
        ],
        num_classes=2,
        head_dropout=0.1,
        rescale=True,
    )
    state = torch.load(
        HELD / "models/prithvi/Prithvi_EO_V2_tiny_TL.pt", map_location="cpu", weights_only=True
    )
    filtered = checkpoint_filter_fn_vit(state, model.encoder, PRETRAINED_BANDS, PRETRAINED_BANDS)
    model.encoder.load_state_dict(filtered, strict=True)
    # Unlike frozen TerraMind/Galileo, the author Prithvi task fine-tunes the
    # backbone. This is an explicit Tiny adaptation, not encoder-only LP.
    return model


class GalileoRadar(nn.Module):
    """Nano + published token-to-8x8-pixel linear segmentation readout."""

    def __init__(self):
        super().__init__()
        source = HELD / "code/galileo/single_file_galileo.py"
        self.api = module_at("applied_native_galileo", source)
        weights = HELD / "models/galileo/models/nano"
        cfg = json.loads((weights / "config.json").read_text())
        self.encoder = self.api.Encoder(**cfg["model"]["encoder"])
        state = torch.load(weights / "encoder.pt", map_location="cpu", weights_only=True)
        self.encoder.load_state_dict(
            {k.replace(".backbone", ""): v for k, v in state.items()}, strict=True
        )
        self.encoder.requires_grad_(False)
        self.probe = nn.Linear(cfg["model"]["encoder"]["embedding_size"], 2 * 8 * 8)
        self.patch_size = 8

    def features(self, radar, months):
        b, _, h, w = radar.shape
        if h != 64 or w != 64:
            raise ValueError("Native Galileo task requires 64px subpatches")
        api = self.api

        def zeros(*shape):
            return radar.new_zeros(shape)

        def ones(*shape):
            return radar.new_ones(shape)

        x = zeros(b, h, w, 1, len(api.SPACE_TIME_BANDS))
        ids = [api.SPACE_TIME_BANDS.index(v) for v in ["VV", "VH"]]
        x[:, :, :, 0, ids] = radar.permute(0, 2, 3, 1)
        mask = ones(b, h, w, 1, len(api.SPACE_TIME_BANDS_GROUPS_IDX))
        s1 = [i for i, key in enumerate(api.SPACE_TIME_BANDS_GROUPS_IDX) if "S1" in key]
        mask[..., s1] = 0
        self.encoder.eval()
        with torch.no_grad():
            out = self.encoder(
                x,
                zeros(b, h, w, len(api.SPACE_BANDS)),
                zeros(b, 1, len(api.TIME_BANDS)),
                zeros(b, len(api.STATIC_BANDS)),
                mask,
                ones(b, h, w, len(api.SPACE_BAND_GROUPS_IDX)),
                ones(b, 1, len(api.TIME_BAND_GROUPS_IDX)),
                ones(b, len(api.STATIC_BAND_GROUPS_IDX)),
                months.reshape(b, 1).long(),
                patch_size=8,
                input_resolution_m=10,
                add_layernorm_on_exit=True,
            )
            tokens = out[0][:, :, :, :, s1, :].mean(dim=(3, 4))
        return tokens

    def forward(self, radar, months):
        b = radar.shape[0]
        logits = self.probe(self.features(radar, months))
        return logits.reshape(b, 8, 8, 2, 8, 8).permute(0, 3, 1, 4, 2, 5).reshape(b, 2, 64, 64)


class GalileoSpatialProbe(nn.Module):
    """The same native linear readout operating on cached frozen tokens."""

    def __init__(self):
        super().__init__()
        self.probe = nn.Linear(128, 128)

    def forward(self, tokens):
        b = tokens.shape[0]
        logits = self.probe(tokens)
        return logits.reshape(b, 8, 8, 2, 8, 8).permute(0, 3, 1, 4, 2, 5).reshape(b, 2, 64, 64)


class CompactUNet(nn.Module):
    """Small same-input learned comparator; no pretrained external features."""

    def __init__(self, channels):
        super().__init__()

        def block(a, b):
            return nn.Sequential(
                nn.Conv2d(a, b, 3, padding=1),
                nn.GroupNorm(4, b),
                nn.GELU(),
                nn.Conv2d(b, b, 3, padding=1),
                nn.GroupNorm(4, b),
                nn.GELU(),
            )

        self.down = block(channels, 16)
        self.bottom = block(16, 32)
        self.up = block(48, 16)
        self.head = nn.Conv2d(16, 2, 1)

    def forward(self, x):
        skip = self.down(x)
        y = self.bottom(torch.nn.functional.avg_pool2d(skip, 2))
        y = torch.nn.functional.interpolate(
            y, size=skip.shape[-2:], mode="bilinear", align_corners=False
        )
        return self.head(self.up(torch.cat([skip, y], dim=1)))
