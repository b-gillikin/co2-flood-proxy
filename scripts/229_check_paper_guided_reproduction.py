"""Training-only diagnostics, not author-score reproduction or test evaluation.

No fitting/reading of validation/test labels. No production files overwritten.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument("--run", action="store_true")
    p.add_argument(
        "--output", type=Path, default=ROOT / "results/paper-guided-recovery-v1/diagnostics"
    )
    a = p.parse_args()
    if not a.run:
        print(
            "Training-only: Galileo patch8 parity, patch4 shape/readout, probe learnability; Prithvi label-resolution roundtrip. No test scoring."
        )
        return
    import numpy as np
    import torch
    from einops import rearrange
    from torch.nn import functional as F

    from applied_reproduction import covering_windows, galileo_tokens, unpack_patch_logits
    from applied_spatial_models import GalileoRadar

    torch.set_num_threads(2)
    torch.manual_seed(42)
    a.output.mkdir(parents=True, exist_ok=False)
    planpath = ROOT / "results/applied_study_v5/ready-v2/execution-plan.json"
    plan = json.loads(planpath.read_text())
    job = next(
        j
        for j in plan["jobs"]
        if j["task"] == "galileo"
        and j["learner"] == "native"
        and j["budget"] == 1
        and j["seed"] == 42
    )
    mp = ROOT / job["output"] / "manifest.json"
    manifest = json.loads(mp.read_text())
    cache = Path(manifest["arguments"]["tensor_cache"])
    idx = json.loads((cache / "index.json").read_text())
    train = set(manifest["partitions"]["train"])
    assert not train.intersection(manifest["partitions"]["test"])
    x = np.load(cache / "x.npy", mmap_mode="r")
    y = np.load(cache / "y.npy", mmap_mode="r")
    selected = []
    for row in sorted(idx["rows"], key=lambda r: r["chip"]):
        if row["chip"] not in train:
            continue
        for part in range(64):
            top, left = (part // 8) * 64, (part % 8) * 64
            label = y[row["position"], top : top + 64, left : left + 64]
            if int((label == 1).sum()) >= 16 and int((label == 0).sum()) >= 16:
                selected.append((row, part, top, left))
                break
        if len(selected) == 2:
            break
    if len(selected) != 2:
        raise ValueError("No two eligible training fixtures")
    radar = torch.from_numpy(
        np.stack(
            [x[r["position"], :, top : top + 64, left : left + 64] for r, _, top, left in selected]
        ).copy()
    )
    labels = torch.from_numpy(
        np.stack(
            [y[r["position"], top : top + 64, left : left + 64] for r, _, top, left in selected]
        ).astype("int64")
    )
    months = torch.tensor([r["month"] for r, _, _, _ in selected])
    model = GalileoRadar().eval()
    production = model.features(radar, months)
    tokens8 = galileo_tokens(model, radar, months, 8)
    torch.testing.assert_close(tokens8, production, rtol=0, atol=0)
    cache_values = torch.from_numpy(
        np.stack(
            [
                np.load(
                    Path(manifest["arguments"]["feature_cache"]) / (r["chip"] + ".npy"),
                    mmap_mode="r",
                )[part]
                for r, part, _, _ in selected
            ]
        ).copy()
    )
    delta = float((cache_values - tokens8).abs().max())
    checks = {}
    for patch in [8, 4]:
        tokens = galileo_tokens(model, radar, months, patch)
        torch.manual_seed(42)
        head = torch.nn.Linear(tokens.shape[-1], 2 * patch * patch)
        opt = torch.optim.AdamW(head.parameters(), lr=0.01)

        def prediction(head=head, tokens=tokens, patch=patch):
            return unpack_patch_logits(head(tokens), patch)

        before = float(F.cross_entropy(prediction(), labels, ignore_index=-1).detach())
        for _ in range(400):
            opt.zero_grad()
            loss = F.cross_entropy(prediction(), labels, ignore_index=-1)
            loss.backward()
            opt.step()
        logits = head(tokens).detach()
        author = rearrange(
            logits.reshape(2, -1, 2 * patch * patch),
            "b (h w) (c i j) -> b c (h i) (w j)",
            h=64 // patch,
            w=64 // patch,
            c=2,
            i=patch,
            j=patch,
        )
        torch.testing.assert_close(author, unpack_patch_logits(logits, patch), rtol=0, atol=0)
        checks[str(patch)] = {
            "tokens_shape": list(tokens.shape),
            "initial_training_ce": before,
            "final_training_ce": float(
                F.cross_entropy(prediction(), labels, ignore_index=-1).detach()
            ),
            "optimizer_steps": 400,
            "readout_matches_author_rearrangement": True,
        }
    # All source-grid labels are training labels from the same named fixture.
    pj = next(
        j
        for j in plan["jobs"]
        if j["task"] == "prithvi"
        and j["learner"] == "native"
        and j["fold"] == job["fold"]
        and j["budget"] == 1
        and j["seed"] == 42
    )
    pmp = ROOT / pj["output"] / "manifest.json"
    pm = json.loads(pmp.read_text())
    pc = Path(pm["arguments"]["tensor_cache"])
    pi = json.loads((pc / "index.json").read_text())
    plook = {r["chip"]: r for r in pi["rows"]}
    py = np.load(pc / "y.npy", mmap_mode="r")
    detail = []
    for row, _, _, _ in selected:
        assert row["chip"] in pm["partitions"]["train"]
        label = torch.from_numpy(py[plook[row["chip"]]["position"]].astype("int64"))
        small = F.interpolate(label[None, None].float(), size=(224, 224), mode="nearest")
        restored = F.interpolate(small, size=label.shape, mode="nearest")[0, 0].long()
        valid = (label >= 0) & (restored >= 0)
        wet = label == 1
        cover = np.zeros(tuple(label.shape), dtype=np.uint8)
        for top, left, bottom, right in covering_windows(*label.shape):
            cover[top:bottom, left:right] += 1
        detail.append(
            {
                "chip": row["chip"],
                "source_positive_pixels": int(wet.sum()),
                "source_label_sha256": hashlib.sha256(label.numpy().tobytes()).hexdigest(),
                "resize_roundtrip_positive_to_nonwater_pixels": int(
                    (wet & valid & (restored != 1)).sum()
                ),
                "resize_roundtrip_nonwater_to_positive_pixels": int(
                    ((label == 0) & valid & (restored == 1)).sum()
                ),
                "lost_valid_support_pixels": int(((label >= 0) & (restored < 0)).sum()),
                "all_pixels_covered_by_224_windows": bool(cover.min() > 0),
                "windows": len(covering_windows(*label.shape)),
            }
        )
    sources = [
        planpath,
        mp,
        pmp,
        pc / "index.json",
        cache / "index.json",
        ROOT / "src/applied_reproduction.py",
        Path(__file__),
        ROOT / "src/applied_spatial_models.py",
    ]
    out = {
        "status": "engineering_checks_complete",
        "selection": "First two sorted TRAIN chips with at least16 water and16 nonwater pixels in a64px patch; selected for plumbing, not representative accuracy",
        "fixtures": [{"chip": r["chip"], "part": part} for r, part, _, _ in selected],
        "galileo_patch8_production_exact": True,
        "radar_fixture_sha256": hashlib.sha256(radar.numpy().tobytes()).hexdigest(),
        "radar_label_fixture_sha256": hashlib.sha256(labels.numpy().tobytes()).hexdigest(),
        "galileo_cached_patch8_max_abs_delta": delta,
        "galileo_probe_checks": checks,
        "spatial_label_roundtrip": detail,
        "interpretation": "Training fixture diagnostic only. No author accuracy reproduced, no validation/test read, no flood-performance or patch-size superiority claim. Label roundtrip is resampling information loss, not model error.",
        "source_hashes": {
            str(q.relative_to(ROOT)): hashlib.sha256(q.read_bytes()).hexdigest() for q in sources
        },
    }
    (a.output / "checks.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
