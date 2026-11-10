import sys
import unittest
from pathlib import Path

import numpy as np
import torch
from einops import rearrange

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from applied_reproduction import covering_windows, unpack_patch_logits


class ReproductionTests(unittest.TestCase):
    def test_readout_matches_author_axes_at_both_granularities(self):
        for p in [4, 8]:
            grid = 64 // p
            x = torch.arange(2 * grid * grid * 2 * p * p).reshape(2, grid, grid, 2 * p * p)
            expected = rearrange(
                x.reshape(2, grid * grid, 2 * p * p),
                "b (h w) (c i j) -> b c (h i) (w j)",
                h=grid,
                w=grid,
                c=2,
                i=p,
                j=p,
            )
            torch.testing.assert_close(unpack_patch_logits(x, p), expected)

    def test_mismatched_head_is_rejected(self):
        with self.assertRaises(ValueError):
            unpack_patch_logits(torch.zeros(1, 8, 8, 128), 4)

    def test_window_cover_reconstructs_nondivisible_scene(self):
        image = np.arange(512 * 511).reshape(512, 511)
        reconstructed = np.zeros_like(image)
        cover = np.zeros_like(image)
        for top, left, bottom, right in covering_windows(*image.shape):
            reconstructed[top:bottom, left:right] = image[top:bottom, left:right]
            cover[top:bottom, left:right] += 1
        self.assertTrue((cover > 0).all())
        np.testing.assert_array_equal(reconstructed, image)

    def test_invalid_window_is_rejected(self):
        with self.assertRaises(ValueError):
            covering_windows(100, 512)


if __name__ == "__main__":
    unittest.main()
