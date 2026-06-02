"""L2 export_urdf.py 行为测试."""
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

pytest.importorskip("jsonschema")
pytest.importorskip("yaml")

import export_urdf  # noqa: E402  (after path setup in conftest)


def test_export_single_leg(example_joints: Path, out_dir: Path) -> None:
    report = export_urdf.export(example_joints, out_dir)
    assert report.output_urdf.exists(), "robot.urdf must exist"
    assert report.link_count == 3
    assert report.joint_count == 2
    assert report.inertial_fallback_links == []

    root = ET.fromstring(report.output_urdf.read_text())
    assert root.tag == "robot"
    assert root.get("name") == "dog_left_front_leg"
    assert len(root.findall("link")) == 3
    assert len(root.findall("joint")) == 2


def test_export_no_l1_path_works(example_joints: Path, out_dir: Path) -> None:
    report = export_urdf.export(example_joints, out_dir, no_l1=True)
    assert report.output_urdf.exists()
    assert report.l1_passed is False
    assert "<robot" in report.output_urdf.read_text()


def test_invariants_catch_cycle(out_dir: Path) -> None:
    bad = {
        "schema_version": 1, "robot": "bad",
        "links": [{"name": "a", "inertial": _i()},
                  {"name": "b", "inertial": _i()}],
        "joints": [
            {"name": "j1", "type": "fixed", "parent": "a", "child": "b",
             "origin": _o()},
            {"name": "j2", "type": "fixed", "parent": "b", "child": "a",
             "origin": _o()},
        ],
    }
    with pytest.raises(export_urdf.ExportUrdfError):
        export_urdf.check_invariants(bad)


def test_invariants_axis_zero_rejected() -> None:
    bad = {
        "schema_version": 1, "robot": "bad",
        "links": [{"name": "a", "inertial": _i()},
                  {"name": "b", "inertial": _i()}],
        "joints": [{"name": "j", "type": "revolute", "parent": "a", "child": "b",
                    "origin": _o(), "axis": [0, 0, 0],
                    "limit": {"lower": -1, "upper": 1}}],
    }
    with pytest.raises(export_urdf.ExportUrdfError, match="axis is zero"):
        export_urdf.check_invariants(bad)


def test_invariants_multiple_roots_rejected() -> None:
    bad = {
        "schema_version": 1, "robot": "bad",
        "links": [{"name": "a", "inertial": _i()},
                  {"name": "b", "inertial": _i()},
                  {"name": "c", "inertial": _i()}],
        "joints": [{"name": "j1", "type": "fixed", "parent": "a", "child": "b",
                    "origin": _o()}],
    }
    with pytest.raises(export_urdf.ExportUrdfError):
        export_urdf.check_invariants(bad)


def test_export_inertial_fallback_partial(out_dir: Path) -> None:
    """部分 link 缺 inertial → WARN + 注释,但 URDF 仍写出."""
    import yaml as _yaml
    src = out_dir / "partial.joints.yaml"
    src.write_text(_yaml.safe_dump({
        "schema_version": 1, "robot": "tiny",
        "links": [
            {"name": "a", "inertial": {
                "mass": 1.0,
                "origin": {"xyz": [0, 0, 0], "rpy": [0, 0, 0]},
                "inertia": {"ixx": 0.01, "iyy": 0.01, "izz": 0.01,
                            "ixy": 0, "ixz": 0, "iyz": 0}}},
            {"name": "b"},  # 缺 inertial
        ],
        "joints": [
            {"name": "j", "type": "fixed", "parent": "a", "child": "b",
             "origin": {"xyz": [0, 0, 0], "rpy": [0, 0, 0]}}],
    }))
    report = export_urdf.export(src, out_dir / "out2", no_l1=True)
    assert report.inertial_fallback_links == ["b"]
    text = report.output_urdf.read_text()
    assert "INERTIAL-FALLBACK" in text


# helpers ---------------------------------------------------------------------
def _i() -> dict:
    return {"mass": 1.0,
            "origin": {"xyz": [0, 0, 0], "rpy": [0, 0, 0]},
            "inertia": {"ixx": 0.01, "iyy": 0.01, "izz": 0.01,
                        "ixy": 0, "ixz": 0, "iyz": 0}}


def _o() -> dict:
    return {"xyz": [0, 0, 0], "rpy": [0, 0, 0]}
