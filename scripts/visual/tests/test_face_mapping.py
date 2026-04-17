"""Unit tests for face_mapping loader.
face_mapping loader 的单元测试。
"""
import tempfile
import unittest
from pathlib import Path

from scripts.visual.face_mapping import load_face_mapping, DEFAULT_MAPPING


YAML_OK = """
part: test_phone
coordinate_system:
  up: "+Z"
  right: "+X"
  screen_normal: "-Y"
face_mapping:
  FRONT: BACK
  BACK: FRONT
  LEFT: LEFT
  RIGHT: RIGHT
  TOP: TOP
  BOTTOM: BOTTOM
"""


class TestFaceMapping(unittest.TestCase):
    def test_load_valid_yaml(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "mapping.yaml"
            p.write_text(YAML_OK)
            mapping = load_face_mapping(p)
            self.assertEqual(mapping.semantic_to_camera("FRONT"), "BACK")
            self.assertEqual(mapping.semantic_to_camera("BACK"), "FRONT")

    def test_default_when_missing(self) -> None:
        mapping = load_face_mapping(None)
        self.assertEqual(mapping.semantic_to_camera("FRONT"), "FRONT")
        self.assertTrue(mapping.is_default)

    def test_unknown_view_raises(self) -> None:
        mapping = load_face_mapping(None)
        with self.assertRaises(KeyError):
            mapping.semantic_to_camera("DIAGONAL")

    def test_invalid_target_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "bad.yaml"
            p.write_text("part: x\nface_mapping:\n  FRONT: WAT\n")
            with self.assertRaises(ValueError):
                load_face_mapping(p)


if __name__ == "__main__":
    unittest.main()
