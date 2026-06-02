"""自写转换器(gz 缺失 fallback)单测:5-tag 覆盖 + SE(3) 位姿累乘 + rpy 复合。"""
from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

import export_sdf  # noqa: E402


MINIMAL_URDF = """<?xml version="1.0"?>
<robot name="chain">
  <link name="base">
    <inertial><origin xyz="0 0 0" rpy="0 0 0"/><mass value="1.0"/>
      <inertia ixx="0.01" iyy="0.01" izz="0.01" ixy="0" ixz="0" iyz="0"/></inertial>
    <visual><origin xyz="0 0 0" rpy="0 0 0"/>
      <geometry><box size="0.1 0.1 0.1"/></geometry></visual>
    <collision><origin xyz="0 0 0" rpy="0 0 0"/>
      <geometry><box size="0.1 0.1 0.1"/></geometry></collision>
  </link>
  <link name="tip">
    <inertial><origin xyz="0 0 0" rpy="0 0 0"/><mass value="0.5"/>
      <inertia ixx="0.001" iyy="0.001" izz="0.001" ixy="0" ixz="0" iyz="0"/></inertial>
    <visual><origin xyz="0 0 0" rpy="0 0 0"/>
      <geometry><mesh filename="meshes/tip.stl" scale="0.001 0.001 0.001"/></geometry></visual>
  </link>
  <joint name="j" type="revolute">
    <parent link="base"/><child link="tip"/>
    <origin xyz="0.2 0 0.1" rpy="0 0 1.5708"/>
    <axis xyz="0 0 1"/>
    <limit lower="-1" upper="1" effort="5" velocity="3"/>
  </joint>
</robot>
"""


def _convert(tmp_path: Path) -> ET.Element:
    urdf = tmp_path / "chain.urdf"
    urdf.write_text(MINIMAL_URDF)
    model = export_sdf._convert_self(urdf, model_name="chain")
    return model


def test_self_converter_five_tags(tmp_path: Path) -> None:
    model = _convert(tmp_path)
    base = next(l for l in model.findall("link") if l.get("name") == "base")
    assert base.find("inertial/mass").text == "1.0"
    assert base.find("visual/geometry/box/size").text == "0.1 0.1 0.1"
    assert base.find("collision/geometry/box/size") is not None
    tip = next(l for l in model.findall("link") if l.get("name") == "tip")
    assert tip.find("visual/geometry/mesh/uri").text == "meshes/tip.stl"
    assert tip.find("visual/geometry/mesh/scale").text == "0.001 0.001 0.001"


def test_self_converter_joint_passthrough(tmp_path: Path) -> None:
    model = _convert(tmp_path)
    j = model.find("joint")
    assert j.get("type") == "revolute"
    assert j.find("parent").text == "base"
    assert j.find("child").text == "tip"
    assert j.find("axis/limit/lower").text == "-1"
    assert j.find("axis/limit/effort").text == "5"


def test_self_converter_absolute_pose_with_rotation(tmp_path: Path) -> None:
    """tip 绝对位姿 = 关节 origin(平移 0.2,0,0.1 + 绕 Z 转 90°)。"""
    model = _convert(tmp_path)
    tip = next(l for l in model.findall("link") if l.get("name") == "tip")
    vals = [float(v) for v in tip.find("pose").text.split()]
    assert vals[:3] == pytest.approx([0.2, 0, 0.1], abs=1e-9)
    assert vals[5] == pytest.approx(1.5708, abs=1e-4)  # yaw 90°


def test_rpy_roundtrip() -> None:
    """rpy → R → rpy 往返一致(非万向锁区)。"""
    for rpy in ([0.1, -0.2, 0.3], [0.0, 0.0, 1.5708], [-0.4, 0.5, -0.6]):
        R = export_sdf._rpy_to_R(*rpy)
        back = export_sdf._R_to_rpy(R)
        assert list(back) == pytest.approx(rpy, abs=1e-9)


def test_floating_joint_downgraded(tmp_path: Path) -> None:
    urdf = tmp_path / "f.urdf"
    urdf.write_text(
        '<?xml version="1.0"?><robot name="r">'
        '<link name="a"/><link name="b"/>'
        '<joint name="j" type="floating"><parent link="a"/><child link="b"/>'
        '<origin xyz="0 0 0" rpy="0 0 0"/></joint></robot>'
    )
    model = export_sdf._convert_self(urdf, model_name="r")
    assert model.find("joint").get("type") == "fixed"  # SDF 无 floating → fixed
