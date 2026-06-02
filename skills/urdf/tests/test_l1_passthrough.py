"""L1 (earthtojake) CLI 不破: 直接调 source.read_urdf_source 校验自家产物."""
from __future__ import annotations

from pathlib import Path

import pytest


def test_l1_source_module_imports() -> None:
    from urdf import source  # noqa: F401
    assert hasattr(source, "read_urdf_source")
    assert hasattr(source, "URDF_SUFFIX")
    assert source.URDF_SUFFIX == ".urdf"


def test_l1_validates_l2_output(example_joints: Path, out_dir: Path) -> None:
    """L2 produced URDF 必须能被 L1 source 解析+通过 SUPPORTED_JOINT_TYPES 检查."""
    pytest.importorskip("yaml")
    pytest.importorskip("jsonschema")
    import export_urdf
    from urdf import source as l1_source

    report = export_urdf.export(example_joints, out_dir, no_l1=True)
    parsed = l1_source.read_urdf_source(report.output_urdf)
    assert parsed.robot_name == "dog_left_front_leg"
    assert parsed.root_link == "base_link"
    assert len(parsed.links) == 3
    assert len(parsed.joints) == 2
    for j in parsed.joints:
        assert j.joint_type in l1_source.SUPPORTED_JOINT_TYPES
