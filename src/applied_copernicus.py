"""Published Copernicus-FM radar-change spatial head, using real MMCV ops.

No substituted backbone/head and no stub compiled operators. Author intensity
statistics (including asymmetric post-event std) are preserved explicitly.
"""

import sys
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (
    ROOT
    / "data/raw/limburg_dynamic_model_weights/code/copernicus_fm/Copernicus-Bench/src/foundation_models"
)
WEIGHT = (
    ROOT
    / "data/raw/limburg_dynamic_model_weights/models/copernicus_fm/CopernicusFM_ViT_base_varlang_e100.pth"
)


def normalize_radar(raw):
    raw = np.asarray(raw, dtype=np.float32)
    if raw.shape[-3] != 4:
        raise ValueError("Expected pre VV,VH then post VV,VH")
    valid = np.all(np.isfinite(raw) & (raw != 0), axis=-3)
    x = (
        np.clip(raw, 0, 0.15) - np.array([0.0981, 0.0253, 0.0981, 0.0253])[:, None, None]
    ) / np.array([0.0430, 0.0174, 0.0981, 0.0253])[:, None, None]
    x[:, ~valid] = 0
    return x.astype(np.float32), valid


class CopernicusRadarChange(nn.Module):
    def __init__(self):
        super().__init__()
        sys.path.insert(0, str(SOURCE))
        sys.path.insert(0, str(SOURCE.parent))
        # Vendor import sets a global seed. Restore the caller's stream so
        # the first LR candidate does not get a different head initialization.
        rng_state = torch.random.get_rng_state()
        from CopernicusFM.models_dwv_seg import vit_base_patch16

        torch.random.set_rng_state(rng_state)
        from mmseg.models.decode_heads import FCNHead, UPerHead
        from mmseg.models.necks import Feature2Pyramid

        # The held release renamed this asset; the benchmark constructor still
        # requests the old filename from a now-404 URL. Alias the SAME held
        # dictionary, whose five required keys were checked, without editing
        # vendor Python or inserting replacement embeddings.
        language = WEIGHT.parent / "varname_embed/varname_embed_llama3.2_1B.pt"
        expected = SOURCE / "CopernicusFM/var_embed_llama3.2_1B.pt"
        if not expected.exists():
            expected.symlink_to(language)
        if expected.resolve() != language.resolve():
            raise ValueError("Conflicting legacy language-asset alias")
        self.encoder = vit_base_patch16()
        state = torch.load(WEIGHT, map_location="cpu", weights_only=False)
        state = state.get("model", state)
        msg = self.encoder.load_state_dict(state, strict=False)
        if msg.missing_keys:
            raise ValueError(f"Missing pretrained parameters: {msg.missing_keys}")
        self.load_report = dict(missing=msg.missing_keys, unexpected=msg.unexpected_keys)
        self.encoder.requires_grad_(False)
        self.neck = Feature2Pyramid(embed_dim=768, rescales=[4, 2, 1, 0.5])
        norm = dict(type="SyncBN", requires_grad=True)
        self.decoder = UPerHead(
            in_channels=[768] * 4,
            in_index=[0, 1, 2, 3],
            pool_scales=(1, 2, 3, 6),
            channels=512,
            dropout_ratio=0.1,
            num_classes=3,
            norm_cfg=norm,
            align_corners=False,
        )
        self.aux_head = FCNHead(
            in_channels=768,
            in_index=2,
            channels=256,
            num_convs=1,
            concat_input=False,
            dropout_ratio=0.1,
            num_classes=3,
            norm_cfg=norm,
            align_corners=False,
        )

        from applied_mps_pool import install_mps_batchnorm_layout, install_mps_pooling

        for head in [self.decoder, self.aux_head]:
            install_mps_pooling(head)
            install_mps_batchnorm_layout(head)

    def frozen_features(self, x, metadata):
        # The author's Fourier coordinates use float64, unsupported by MPS.
        # Preserve those calculations on CPU; only frozen results cross devices.
        self.encoder.to("cpu")
        self.encoder.eval()
        x, metadata = x.to("cpu"), metadata.to("cpu")
        with torch.no_grad():
            pre = self.encoder(
                x[:, :2], metadata[:, 0], None, [50000000] * 2, [1e9] * 2, None, "spectral", 16
            )
            post = self.encoder(
                x[:, 2:], metadata[:, 1], None, [50000000] * 2, [1e9] * 2, None, "spectral", 16
            )
        return [b - a for a, b in zip(pre, post, strict=True)]

    def forward_features(self, features):
        device = next(self.neck.parameters()).device
        features = self.neck([f.to(device) for f in features])
        return tuple(
            F.interpolate(head(features), size=(224, 224), mode="bilinear", align_corners=False)
            for head in [self.decoder, self.aux_head]
        )

    def forward(self, x, metadata):
        if x.shape[-2:] != (224, 224):
            raise ValueError("Published radar-change task uses224px inputs")
        return self.forward_features(self.frozen_features(x, metadata))


def change_loss(outputs, labels):
    if not (labels != 3).any():
        return None
    return F.cross_entropy(outputs[0], labels, ignore_index=3) + 0.4 * F.cross_entropy(
        outputs[1], labels, ignore_index=3
    )
