"""Unit tests for visual_compare.
visual_compare 的单元测试。
"""
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

from scripts.visual.visual_compare import (
    canny_edges, compose_side_by_side, compose_edge_overlay, compose_diff_heatmap,
    normalize_to_scale,
)


FIXTURES = Path(__file__).parent / "fixtures"


def _identical_pair() -> tuple[Image.Image, Image.Image]:
    img = Image.open(FIXTURES / "synthetic_phone_front.png").convert("RGB")
    return img, img.copy()


class TestVisualCompare(unittest.TestCase):
    def test_canny_returns_binary_mask(self) -> None:
        img, _ = _identical_pair()
        edges = canny_edges(np.array(img.convert("L")))
        self.assertEqual(edges.dtype, np.uint8)
        unique = set(np.unique(edges).tolist())
        self.assertTrue(unique.issubset({0, 255}))

    def test_side_by_side_shape(self) -> None:
        a, b = _identical_pair()
        out = compose_side_by_side(a, b)
        self.assertEqual(out.height, max(a.height, b.height))
        self.assertEqual(out.width, a.width + b.width)

    def test_edge_overlay_identical_has_no_blue_only_pixels(self) -> None:
        a, b = _identical_pair()
        overlay = compose_edge_overlay(a, b)
        arr = np.array(overlay)
        blue_only = (arr[..., 2] > 0) & (arr[..., 0] == 0)
        self.assertEqual(int(blue_only.sum()), 0)

    def test_diff_heatmap_identical_is_zero(self) -> None:
        a, b = _identical_pair()
        heat = compose_diff_heatmap(a, b)
        arr = np.array(heat.convert("L"))
        self.assertLess(float(arr.mean()), 5.0)

    def test_normalize_to_scale_resizes_to_common_mm_per_px(self) -> None:
        a, _ = _identical_pair()
        a_small = a.resize((a.width // 2, a.height // 2))
        na, nb = normalize_to_scale(
            a_small, mm_per_px_a=2.0,
            b=a, mm_per_px_b=1.0,
        )
        self.assertLessEqual(abs(na.width - nb.width), 1)
        self.assertLessEqual(abs(na.height - nb.height), 1)


if __name__ == "__main__":
    unittest.main()
