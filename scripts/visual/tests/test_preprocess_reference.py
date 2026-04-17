"""Unit tests for preprocess_reference.
preprocess_reference 的单元测试。
"""
import json
import tempfile
import unittest
from pathlib import Path

from scripts.visual.preprocess_reference import preprocess


FIXTURES = Path(__file__).parent / "fixtures"


class TestPreprocess(unittest.TestCase):
    def test_crop_matches_bbox(self) -> None:
        meta = json.loads((FIXTURES / "fixtures_meta.json").read_text())
        bbox = meta["front_bbox_px"]
        with tempfile.TemporaryDirectory() as tmp:
            out = preprocess(
                image_path=FIXTURES / "synthetic_phone_front.png",
                bbox=tuple(bbox),
                physical_length_mm=meta["phone_length_mm"],
                physical_axis="height",
                output_dir=Path(tmp),
            )
            cropped = out["cropped_path"]
            self.assertTrue(cropped.exists(), "cropped image must be written")
            from PIL import Image
            img = Image.open(cropped)
            self.assertEqual(img.size, (bbox[2], bbox[3]))

    def test_scale_json_mm_per_px(self) -> None:
        meta = json.loads((FIXTURES / "fixtures_meta.json").read_text())
        bbox = meta["front_bbox_px"]
        expected_mm_per_px = 1.0 / meta["px_per_mm"]
        with tempfile.TemporaryDirectory() as tmp:
            out = preprocess(
                image_path=FIXTURES / "synthetic_phone_front.png",
                bbox=tuple(bbox),
                physical_length_mm=meta["phone_length_mm"],
                physical_axis="height",
                output_dir=Path(tmp),
            )
            scale = json.loads(out["scale_path"].read_text())
            self.assertAlmostEqual(scale["mm_per_px"], expected_mm_per_px, places=4)
            self.assertEqual(scale["physical_axis"], "height")

    def test_bbox_json_round_trip(self) -> None:
        meta = json.loads((FIXTURES / "fixtures_meta.json").read_text())
        bbox = meta["front_bbox_px"]
        with tempfile.TemporaryDirectory() as tmp:
            out = preprocess(
                image_path=FIXTURES / "synthetic_phone_front.png",
                bbox=tuple(bbox),
                physical_length_mm=meta["phone_length_mm"],
                physical_axis="height",
                output_dir=Path(tmp),
            )
            bj = json.loads(out["bbox_path"].read_text())
            self.assertEqual(bj["bbox_xywh"], list(bbox))

    def test_invalid_bbox_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                preprocess(
                    image_path=FIXTURES / "synthetic_phone_front.png",
                    bbox=(10, 10, 10000, 10000),
                    physical_length_mm=160.0,
                    physical_axis="height",
                    output_dir=Path(tmp),
                )


if __name__ == "__main__":
    unittest.main()
