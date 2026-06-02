"""L2 export_sdf.py 行为测试(world.yaml + URDF → SDF)。"""
from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

pytest.importorskip("jsonschema")
pytest.importorskip("yaml")

import export_sdf  # noqa: E402  (conftest 已把 scripts/ 加进 sys.path)


def test_export_world_with_urdf(example_world: Path, sample_urdf: Path, out_dir: Path) -> None:
    report = export_sdf.export(example_world, out_dir, urdf=sample_urdf)
    assert report.output_world.exists()
    assert report.output_model is not None and report.output_model.exists()
    assert report.model_link_count == 3
    assert report.model_joint_count == 2
    assert report.sensors_injected == 2  # imu + camera

    world = ET.fromstring(report.output_world.read_text())
    assert world.tag == "sdf"
    assert world.get("version") == "1.12"
    w = world.find("world")
    assert w is not None and w.get("name") == "dog_playground"
    assert w.find("physics") is not None
    assert w.find("gravity") is not None
    assert w.find("include/uri").text == "model://dog_left_front_leg"
    # ground_plane model 注入
    assert any(m.get("name") == "ground_plane" for m in w.findall("model"))


def test_model_sdf_structure_and_poses(example_world: Path, sample_urdf: Path, out_dir: Path) -> None:
    report = export_sdf.export(example_world, out_dir, urdf=sample_urdf)
    model = ET.fromstring(report.output_model.read_text()).find("model")
    links = {l.get("name"): l for l in model.findall("link")}
    assert set(links) == {"base_link", "fl_hip", "fl_thigh"}

    # 绝对位姿应是关节 origin 的累乘:fl_thigh = (0.1,0.05,0) ∘ (0,0,-0.02)
    pose = links["fl_thigh"].find("pose").text.split()
    xyz = [float(v) for v in pose[:3]]
    assert xyz == pytest.approx([0.1, 0.05, -0.02], abs=1e-9)

    # joint 轴/限位透传
    j = next(j for j in model.findall("joint") if j.get("name") == "fl_hip_joint")
    assert j.get("type") == "revolute"
    assert j.find("axis/xyz").text == "0 0 1"
    assert float(j.find("axis/limit/lower").text) == pytest.approx(-1.57)


def test_sensors_injected_on_right_links(example_world: Path, sample_urdf: Path, out_dir: Path) -> None:
    report = export_sdf.export(example_world, out_dir, urdf=sample_urdf)
    model = ET.fromstring(report.output_model.read_text()).find("model")
    by_link = {l.get("name"): l for l in model.findall("link")}
    assert by_link["base_link"].find("sensor").get("type") == "imu"
    cam = by_link["fl_thigh"].find("sensor")
    assert cam.get("type") == "camera"
    assert cam.find("camera/image/width").text == "640"
    # 没挂 sensor 的 link 不应凭空多出 sensor
    assert by_link["fl_hip"].find("sensor") is None


def test_gz_unavailable_writes_error_marker(example_world: Path, sample_urdf: Path, out_dir: Path) -> None:
    """本机无 gz → fallback 自写转换器 + _errors/sdf.json 标 gz_unavailable(R3)。"""
    if export_sdf.gz_available():
        pytest.skip("本机装了 gz,走高保真路径,无 fallback marker")
    report = export_sdf.export(example_world, out_dir, urdf=sample_urdf)
    assert report.gz_used is False
    marker = out_dir / "_errors" / "sdf.json"
    assert marker.exists()
    payload = json.loads(marker.read_text())
    assert payload["gz_unavailable"] is True
    assert set(["link", "joint", "inertial", "visual", "collision"]) <= set(payload["covered_tags"])


def test_world_only_no_urdf(example_world: Path, out_dir: Path) -> None:
    """不给 --urdf:只出 world.sdf(含 include 引用),不出 model.sdf。"""
    report = export_sdf.export(example_world, out_dir, urdf=None)
    assert report.output_world.exists()
    assert report.output_model is None
    assert report.model_link_count == 0


def test_sensor_on_missing_link_rejected(sample_urdf: Path, out_dir: Path) -> None:
    """sensor 挂到 model 不存在的 link → 强不变量报错。"""
    import yaml as _yaml
    bad = out_dir / "bad.world.yaml"
    bad.write_text(_yaml.safe_dump({
        "schema_version": 1, "world_name": "w",
        "ground": {"type": "plane"},
        "include_models": [{"uri": "model://dog_left_front_leg", "name": "i"}],
        "sensors": [{"link": "no_such_link", "name": "s", "type": "imu"}],
    }))
    with pytest.raises(export_sdf.ExportSdfError, match="不存在的 link"):
        export_sdf.export(bad, out_dir / "o2", urdf=sample_urdf)


def test_empty_world_rejected(out_dir: Path) -> None:
    import yaml as _yaml
    bad = out_dir / "empty.world.yaml"
    bad.write_text(_yaml.safe_dump({"schema_version": 1, "world_name": "w"}))
    with pytest.raises(export_sdf.ExportSdfError, match="空世界"):
        export_sdf.export(bad, out_dir / "o3", urdf=None)
