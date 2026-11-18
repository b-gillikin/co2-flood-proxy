"""Memory-mapped tensor inputs and deterministic, worker-independent augmentation.

Image/target values are unchanged. Random rotation/flip assignments reproduce
legacy seed+epoch draw order, independent of batching/prefetch worker count.
"""

import json
import multiprocessing as mp
import random
from functools import lru_cache
from pathlib import Path

import numpy as np
import torch
from torch.nn import functional as F
from torch.utils.data import Dataset

from applied_evaluation import CompleteBatches


@lru_cache(maxsize=32)
def feature_map(path):
    return np.load(path, mmap_mode="r", allow_pickle=False)


class EpochBatches(CompleteBatches):
    def __init__(self, size, batch_size, seed, epoch):
        super().__init__(size, batch_size, seed)
        self.epoch = epoch

    def __iter__(self):
        return iter(CompleteBatches(self.size, self.batch_size, self.seed + self.epoch.value))


class CachedChips(Dataset):
    def __init__(self, rows, task, cache, feature_cache=None, augment=False, seed=42):
        self.task = task
        self.cache = Path(cache)
        self.feature_cache = Path(feature_cache) if feature_cache else None
        index = json.loads((self.cache / "index.json").read_text())
        if index["status"] != "complete":
            raise ValueError("Tensor cache incomplete")
        lookup = {r["chip"]: r for r in index["rows"]}
        self.records = [lookup[str(chip)] for chip in rows.chip]
        self.parts = 64 if task == "galileo" else 1
        self.augment = augment and task not in {"galileo", "copernicus"}
        self.seed = seed
        self.epoch = mp.get_context("spawn").Value("i", 0)
        self.maps = None
        self.augmentation_epoch = None
        self.augmentations = {}

    def __len__(self):
        return len(self.records) * self.parts

    def __getstate__(self):
        d = self.__dict__.copy()
        d["maps"] = None
        return d

    def set_epoch(self, epoch):
        self.epoch.value = epoch

    def _refresh(self):
        if self.maps is None:
            self.maps = {
                k: np.load(self.cache / f"{k}.npy", mmap_mode="r", allow_pickle=False)
                for k in ["x", "y"]
            }
        epoch = self.epoch.value
        if self.augmentation_epoch != epoch:
            if self.augment:
                order = (
                    [0]
                    if len(self) == 1
                    else [
                        i
                        for b in CompleteBatches(len(self), max(2, len(self)), self.seed + epoch)
                        for i in b
                    ]
                )
                rng = random.Random(self.seed + epoch)
                self.augmentations = {i: (rng.randrange(4), rng.random() < 0.5) for i in order}
            else:
                self.augmentations = {}
            self.augmentation_epoch = epoch

    def __getitem__(self, index):
        self._refresh()
        row = self.records[index // self.parts]
        position = row["position"]
        part = index % self.parts
        y = self.maps["y"][position]
        raw = self.maps["x"][position]
        k, flip = self.augmentations.get(index, (0, False))
        if self.augment:
            y = np.rot90(y, k)
            raw = np.rot90(raw, k, axes=(-2, -1))
            if flip:
                y = y[..., ::-1]
                raw = raw[..., ::-1]
        if self.parts > 1:
            top, left = (part // 8) * 64, (part % 8) * 64
            y = y[top : top + 64, left : left + 64]
            raw = raw[:, top : top + 64, left : left + 64]
        item = dict(
            y=torch.from_numpy(y.astype(np.int64)), chip=row["chip"], event=row["event"], part=part
        )
        for key in ["temporal", "location", "metadata"]:
            if key in row:
                item[key] = torch.tensor(row[key], dtype=torch.float32)
        if "month" in row:
            item["month"] = row["month"]
        if self.feature_cache:
            feature = feature_map(str(self.feature_cache / f"{row['chip']}.npy"))
            if self.task == "galileo":
                feature = feature[part]
            if self.task == "terramind":
                feature = feature[k + 4 * int(flip)]
            item.update(x=torch.empty(0), features=torch.from_numpy(feature.copy()))
        else:
            x = torch.from_numpy(raw.copy())
            if self.task == "prithvi":
                x = F.interpolate(x[None], size=(224, 224), mode="bilinear", align_corners=False)[0]
            item["x"] = x
        item["loss_y"] = (
            F.interpolate(item["y"][None, None].float(), size=(224, 224), mode="nearest")[
                0, 0
            ].long()
            if self.task == "prithvi"
            else item["y"]
        )
        item["valid_label_pixels"] = int((item["loss_y"] >= 0).sum())
        return item


def cached_terramind_forward(model, features):
    """Same PixelWiseModel path, skipping only the frozen encoder forward."""
    from terratorch.models.pixel_wise_model import center_crop

    selected = list(features.unbind(1))
    layers = [selected[0]] * 12
    for i, tensor in zip([2, 5, 8, 11], selected, strict=True):
        layers[i] = tensor
    stages = model.neck(layers, image_size=(512, 512))
    mask = model.head(model.decoder([f.clone() for f in stages]))
    if model.rescale and mask.shape[-2:] != (512, 512):
        mask = F.interpolate(mask, size=(512, 512), mode="bilinear")
    return center_crop(
        model._check_for_single_channel_and_squeeze(mask), model.image_size_out or (512, 512)
    )


def fast_loss(outputs, y, task, learner):
    """Caller already checked CPU label support; avoid a per-step GPU sync."""
    if task == "copernicus" and learner == "native":
        target = torch.where(y < 0, 3, y)
        return F.cross_entropy(outputs[0], target, ignore_index=3) + 0.4 * F.cross_entropy(
            outputs[1], target, ignore_index=3
        )
    if task == "terramind":
        import segmentation_models_pytorch as smp

        return smp.losses.DiceLoss("multiclass", ignore_index=-1)(outputs.float(), y)
    return F.cross_entropy(outputs, y, ignore_index=-1)


class UnscaledSteps:
    """Old/new PyTorch-compatible FP32 path; no AMP state or skipped updates."""

    def scale(self, loss):
        return loss

    def step(self, optimizer):
        return optimizer.step()

    def update(self):
        pass

    def get_scale(self):
        return 1.0


def make_scaler(torch_module, device, precision):
    if precision != "float16":
        return UnscaledSteps()
    if not hasattr(torch_module.amp, "GradScaler"):
        raise RuntimeError("This runtime lacks GradScaler; use FP32 or a compatible runtime")
    return torch_module.amp.GradScaler(device, enabled=True, init_scale=1024)
