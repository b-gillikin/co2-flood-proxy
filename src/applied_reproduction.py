"""Isolated reproduction helpers; completed production adapters stay unchanged."""

import torch


def unpack_patch_logits(logits, patch_size, classes=2):
    b, h, w, channels = logits.shape
    if channels != classes * patch_size**2:
        raise ValueError("Readout dimension does not match patch size")
    return (
        logits.reshape(b, h, w, classes, patch_size, patch_size)
        .permute(0, 3, 1, 4, 2, 5)
        .reshape(b, classes, h * patch_size, w * patch_size)
    )


def covering_windows(height, width, size=224):
    if min(height, width) < size or size < 1:
        raise ValueError("Windows require a positive size within the image")

    def starts(length):
        return sorted(set(range(0, length - size + 1, size)) | {length - size})

    return [(y, x, y + size, x + size) for y in starts(height) for x in starts(width)]


def galileo_tokens(model, radar, months, patch_size):
    """Use the held encoder with explicit supported granularity and masks."""
    b, _, h, w = radar.shape
    if patch_size not in {4, 8} or h % patch_size or w % patch_size:
        raise ValueError("This controlled check supports aligned patch sizes 4/8")
    api = model.api
    zeros, ones = radar.new_zeros, radar.new_ones
    x = zeros((b, h, w, 1, len(api.SPACE_TIME_BANDS)))
    ids = [api.SPACE_TIME_BANDS.index(v) for v in ["VV", "VH"]]
    x[:, :, :, 0, ids] = radar.permute(0, 2, 3, 1)
    s1 = [i for i, k in enumerate(api.SPACE_TIME_BANDS_GROUPS_IDX) if "S1" in k]
    mask = ones((b, h, w, 1, len(api.SPACE_TIME_BANDS_GROUPS_IDX)))
    mask[..., s1] = 0
    model.encoder.eval()
    with torch.no_grad():
        out = model.encoder(
            x,
            zeros((b, h, w, len(api.SPACE_BANDS))),
            zeros((b, 1, len(api.TIME_BANDS))),
            zeros((b, len(api.STATIC_BANDS))),
            mask,
            ones((b, h, w, len(api.SPACE_BAND_GROUPS_IDX))),
            ones((b, 1, len(api.TIME_BAND_GROUPS_IDX))),
            ones((b, len(api.STATIC_BAND_GROUPS_IDX))),
            months.reshape(b, 1).long(),
            patch_size=patch_size,
            input_resolution_m=10,
            add_layernorm_on_exit=True,
        )
    return out[0][:, :, :, :, s1, :].mean(dim=(3, 4))
