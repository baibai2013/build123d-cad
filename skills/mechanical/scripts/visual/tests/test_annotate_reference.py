"""Unit tests for annotate_reference.
annotate_reference 的单元测试。
"""
import json
import tempfile
import unittest
from pathlib import Path

from scripts.visual.annotate_reference import annotate


FIXTURES = Path(__file__).parent / "fixtures"


SAMPLE_ANNOTATIONS = {
    "scale": {"pixels": 800, "mm": 160.0},
    "origin": [227, 470],
    "features": [
        {"name": "camera", "center_px": [227, 80], "size_mm": [20, 20], "confidence": 5, "color": "blue"},
        {"name": "button", "center_px": [415, 300], "size_mm": [6, 20], "confidence": 3, "color": "red"},
    ],
}


class TestAnnotate(unittest.TestCase):
    def test_produces_output_png(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ann_path = Path(tmp) / "ann.json"
            ann_path.write_text(json.dumps(SAMPLE_ANNOTATIONS))
            out = annotate(
                image_path=FIXTURES / "synthetic_phone_front.png",
                annotations_path=ann_path,
                output_path=Path(tmp) / "annotated.png",
            )
            self.assertTrue(out.exists())

    def test_rejects_invalid_confidence(self) -> None:
        bad = {**SAMPLE_ANNOTATIONS, "features": [
            {"name": "x", "center_px": [10, 10], "size_mm": [1, 1], "confidence": 99, "color": "red"}
        ]}
        with tempfile.TemporaryDirectory() as tmp:
            ann_path = Path(tmp) / "ann.json"
            ann_path.write_text(json.dumps(bad))
            with self.assertRaises(ValueError):
                annotate(
                    image_path=FIXTURES / "synthetic_phone_front.png",
                    annotations_path=ann_path,
                    output_path=Path(tmp) / "annotated.png",
                )


if __name__ == "__main__":
    unittest.main()
