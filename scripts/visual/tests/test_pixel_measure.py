"""Unit tests for pixel_measure batch mode.
pixel_measure batch 模式的单元测试。
"""
import json
import tempfile
import unittest
from pathlib import Path

from scripts.visual.pixel_measure import measure_points


FIXTURES = Path(__file__).parent / "fixtures"


class TestPixelMeasure(unittest.TestCase):
    def setUp(self) -> None:
        self.meta = json.loads((FIXTURES / "fixtures_meta.json").read_text())
        self.mm_per_px = 1.0 / self.meta["px_per_mm"]

    def test_origin_at_bbox_center_gives_zero(self) -> None:
        bbox = self.meta["front_bbox_px"]
        cx = bbox[0] + bbox[2] // 2
        cy = bbox[1] + bbox[3] // 2
        results = measure_points(
            points_px=[(cx, cy)],
            mm_per_px=self.mm_per_px,
            origin_px=(cx, cy),
        )
        self.assertAlmostEqual(results[0]["x_mm"], 0.0, places=4)
        self.assertAlmostEqual(results[0]["y_mm"], 0.0, places=4)

    def test_camera_position_in_mm(self) -> None:
        bbox = self.meta["front_bbox_px"]
        origin = (bbox[0] + bbox[2] // 2, bbox[1] + bbox[3] // 2)
        cam_px = tuple(self.meta["front_camera_center_px"])
        results = measure_points(
            points_px=[cam_px],
            mm_per_px=self.mm_per_px,
            origin_px=origin,
        )
        self.assertAlmostEqual(results[0]["x_mm"], 0.0, delta=0.5)
        self.assertLess(results[0]["y_mm"], 0)

    def test_y_axis_sign_convention_flag(self) -> None:
        results_image = measure_points(
            points_px=[(100, 200)],
            mm_per_px=0.5,
            origin_px=(50, 50),
            y_axis_up=False,
        )
        results_math = measure_points(
            points_px=[(100, 200)],
            mm_per_px=0.5,
            origin_px=(50, 50),
            y_axis_up=True,
        )
        self.assertAlmostEqual(results_image[0]["y_mm"], 75.0, places=4)
        self.assertAlmostEqual(results_math[0]["y_mm"], -75.0, places=4)


if __name__ == "__main__":
    unittest.main()
