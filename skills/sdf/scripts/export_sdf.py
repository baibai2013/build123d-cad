#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L2 适配层: world.yaml + URDF → SDF(Gazebo 仿真世界)+ model.sdf.

用法
----
python skills/sdf/scripts/export_sdf.py <world.yaml> [--urdf robot.urdf] \
       [-o output_dir/] [--gz-check auto|required|never] [--no-l1]

行为(对应 04 §11.3 流程)
------------------------
1. 读 world.yaml,用 shared/schemas/world.schema.json 强校验(jsonschema)
2. 跑强不变量(world_name 合法 / include 与 sensor.link 自洽 / 至少一个内容块)
3. 若给了 --urdf:把 URDF → model SDF
   - `gz` 在 PATH:走 `gz sdf -p robot.urdf` 高保真转换(官方,语义保真)
   - `gz` 缺失:走自写转换器 fallback(只覆盖 link/joint/inertial/visual/collision 5 个 tag,
     sensor/plugin 缺省)+ WARN + 写 `_errors/sdf.json` 标 gz_unavailable=true(R3)
   - 把 world.yaml 的 sensors 注入 model 对应 link
4. 组 world SDF:注入 physics / gravity / light / include(model)/ ground_plane / plugins
5. 写 `<world>_gen_sdf.py` 内嵌 gen_sdf() → 调 L1 CLI(`python -m sdf` + `--gz-check`)
   做 bundled validation + 可选 gz sdf --check + 元数据落盘;`--no-l1` 时直写
6. 报告:model link/joint 数 / gz 是否可用 / 注入 sensor 数 / L1 校验结果

设计要点见 share/build123d-cad改造/04 §11(SDF 规格)/ §13 R3(gz-tools 风险)。
本子技能 P1 只过结构校验 + gz sdf --check(若装);真跑 Gazebo 仿真留 P2(本机无 ROS)。
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET

REPO_ROOT = Path(__file__).resolve().parents[3]  # ~/.agents/skills/build123d-cad
SCRIPTS_DIR = Path(__file__).resolve().parent     # skills/sdf/scripts
SHARED_SCHEMAS = REPO_ROOT / "shared" / "schemas"
WORLD_SCHEMA_PATH = SHARED_SCHEMAS / "world.schema.json"
SHARED_CADPY_SRC = REPO_ROOT / "shared" / "python" / "cadpy_metadata" / "src"

# 让本进程能 import L1(scripts/sdf)与 shared cadpy_metadata(R5:复用 shared,不 vendor)
for _p in (str(SCRIPTS_DIR), str(SHARED_CADPY_SRC)):
    if _p not in sys.path:
        sys.path.insert(0, _p)


class ExportSdfError(RuntimeError):
    pass


@dataclass
class ExportReport:
    world_name: str
    output_world: Path
    output_model: Path | None
    model_link_count: int
    model_joint_count: int
    gz_available: bool
    gz_used: bool
    sensors_injected: int
    l1_passed: bool
    l1_log: str
    warnings: list[str] = field(default_factory=list)

    def as_text(self) -> str:
        lines = [
            f"world: {self.world_name}",
            f"output world: {self.output_world}",
            f"output model: {self.output_model or '(none — world-only, no --urdf)'}",
            f"model links: {self.model_link_count}  joints: {self.model_joint_count}",
            f"gz-tools: {'available' if self.gz_available else 'UNAVAILABLE (fallback self-converter)'}",
            f"URDF→SDF path: {'gz sdf -p' if self.gz_used else 'self-converter (5-tag, lossy)' if self.output_model else '(n/a)'}",
            f"sensors injected: {self.sensors_injected}",
            f"L1 CLI: {'passed' if self.l1_passed else 'skipped/failed'}",
        ]
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# 1. yaml 读 + JSON Schema 校验
# ---------------------------------------------------------------------------
def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # PyYAML
    except ImportError as exc:  # pragma: no cover
        raise ExportSdfError("missing dependency: pip install pyyaml") from exc
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def validate_schema(data: dict[str, Any], *, schema_path: Path = WORLD_SCHEMA_PATH) -> None:
    try:
        import jsonschema
    except ImportError as exc:  # pragma: no cover
        raise ExportSdfError("missing dependency: pip install jsonschema") from exc
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(data)


# ---------------------------------------------------------------------------
# 2. 强不变量(超出 JSON Schema)
# ---------------------------------------------------------------------------
def check_invariants(data: dict[str, Any], *, model_links: set[str] | None = None) -> None:
    content = bool(data.get("include_models")) or bool(data.get("ground"))
    if not content:
        raise ExportSdfError("world 必须至少有一个 include_models 或 ground(否则是空世界)")

    names = [m.get("name") or _model_name_from_uri(m["uri"]) for m in data.get("include_models", [])]
    if len(set(names)) != len(names):
        raise ExportSdfError(f"include_models 实例名重复: {names}")

    if model_links is not None:
        for sensor in data.get("sensors", []):
            if sensor["link"] not in model_links:
                raise ExportSdfError(
                    f"sensor {sensor['name']!r} 挂在不存在的 link {sensor['link']!r};"
                    f" model 现有 link: {sorted(model_links)}"
                )


def _model_name_from_uri(uri: str) -> str:
    return uri.split("://", 1)[-1].strip("/").split("/")[0] if uri else "model"


# ---------------------------------------------------------------------------
# 3. URDF → model SDF
# ---------------------------------------------------------------------------
def gz_available() -> bool:
    import shutil
    return shutil.which("gz") is not None


def convert_urdf_to_model_sdf(
    urdf_path: Path, *, model_name: str
) -> tuple[ET.Element, bool, list[str]]:
    """URDF → SDF <model> 元素。返回 (model_elem, gz_used, warnings)。"""
    if gz_available():
        try:
            return _convert_via_gz(urdf_path, model_name=model_name), True, []
        except Exception as exc:  # pragma: no cover - 本机无 gz
            warns = [f"gz sdf -p 失败,退回自写转换器: {exc}"]
            return _convert_self(urdf_path, model_name=model_name), False, warns
    return (
        _convert_self(urdf_path, model_name=model_name),
        False,
        ["gz 不在 PATH,URDF→SDF 走自写转换器(5-tag,sensor/plugin 缺省;见 04 §13 R3)"],
    )


def _convert_via_gz(urdf_path: Path, *, model_name: str) -> ET.Element:  # pragma: no cover
    """官方 `gz sdf -p` 转换;解析 stdout 取 <model> 并改名。"""
    import shutil
    proc = subprocess.run(
        [shutil.which("gz"), "sdf", "-p", str(urdf_path)],
        capture_output=True, text=True, check=False, timeout=60,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        raise ExportSdfError(f"gz sdf -p 非零退出: {(proc.stderr or proc.stdout).strip()}")
    sdf_root = ET.fromstring(proc.stdout)
    model = sdf_root.find("model")
    if model is None:
        raise ExportSdfError("gz sdf -p 输出未含 <model>")
    model.set("name", model_name)
    return model


# --- 自写转换器(fallback)----------------------------------------------------
def _convert_self(urdf_path: Path, *, model_name: str) -> ET.Element:
    robot = ET.fromstring(urdf_path.read_text(encoding="utf-8"))
    if robot.tag != "robot":
        raise ExportSdfError(f"{urdf_path} 根不是 <robot>")

    links = {l.get("name"): l for l in robot.findall("link")}
    joints = robot.findall("joint")

    # 构父子关系 + 每个 joint 的 child-in-parent 变换
    parent_of: dict[str, str] = {}
    joint_T: dict[str, tuple[list[list[float]], list[float]]] = {}  # child -> (R, t)
    for j in joints:
        child = j.find("child").get("link")
        parent = j.find("parent").get("link")
        parent_of[child] = parent
        joint_T[child] = _origin_to_Rt(j.find("origin"))

    roots = [name for name in links if name not in parent_of]
    if len(roots) != 1:
        raise ExportSdfError(f"URDF 应恰有 1 个根 link,得到 {roots}")

    # 累乘出每个 link 在 model 系下的绝对位姿(零关节角姿态)
    abs_T = _accumulate_absolute(roots[0], parent_of, joint_T)

    model = ET.Element("model", {"name": model_name})
    for name, link_elem in links.items():
        sdf_link = ET.SubElement(model, "link", {"name": name})
        R, t = abs_T[name]
        ET.SubElement(sdf_link, "pose").text = _pose_text(R, t)
        _emit_inertial(sdf_link, link_elem)
        _emit_geometry_block(sdf_link, link_elem, "visual")
        _emit_geometry_block(sdf_link, link_elem, "collision")

    for j in joints:
        _emit_joint(model, j)
    return model


def _emit_inertial(sdf_link: ET.Element, urdf_link: ET.Element) -> None:
    src = urdf_link.find("inertial")
    if src is None:
        return
    inertial = ET.SubElement(sdf_link, "inertial")
    o = src.find("origin")
    if o is not None:
        R, t = _origin_to_Rt(o)
        ET.SubElement(inertial, "pose").text = _pose_text(R, t)
    mass = src.find("mass")
    if mass is not None:
        ET.SubElement(inertial, "mass").text = mass.get("value", "0")
    iz = src.find("inertia")
    if iz is not None:
        inertia = ET.SubElement(inertial, "inertia")
        for key in ("ixx", "ixy", "ixz", "iyy", "iyz", "izz"):
            ET.SubElement(inertia, key).text = iz.get(key, "0")


def _emit_geometry_block(sdf_link: ET.Element, urdf_link: ET.Element, tag: str) -> None:
    src = urdf_link.find(tag)
    if src is None:
        return
    block = ET.SubElement(sdf_link, tag, {"name": f"{urdf_link.get('name')}_{tag}"})
    o = src.find("origin")
    if o is not None:
        R, t = _origin_to_Rt(o)
        ET.SubElement(block, "pose").text = _pose_text(R, t)
    src_geo = src.find("geometry")
    if src_geo is None:
        return
    geo = ET.SubElement(block, "geometry")
    mesh = src_geo.find("mesh")
    if mesh is not None:
        m = ET.SubElement(geo, "mesh")
        ET.SubElement(m, "uri").text = mesh.get("filename", "")
        if mesh.get("scale"):
            ET.SubElement(m, "scale").text = mesh.get("scale")
        return
    box = src_geo.find("box")
    if box is not None:
        ET.SubElement(ET.SubElement(geo, "box"), "size").text = box.get("size", "1 1 1")
        return
    cyl = src_geo.find("cylinder")
    if cyl is not None:
        c = ET.SubElement(geo, "cylinder")
        ET.SubElement(c, "radius").text = cyl.get("radius", "0.1")
        ET.SubElement(c, "length").text = cyl.get("length", "0.1")
        return
    sph = src_geo.find("sphere")
    if sph is not None:
        ET.SubElement(ET.SubElement(geo, "sphere"), "radius").text = sph.get("radius", "0.1")


def _emit_joint(model: ET.Element, urdf_joint: ET.Element) -> None:
    jtype = urdf_joint.get("type", "fixed")
    if jtype == "floating":  # SDF 无 floating,降级 fixed + 提示
        jtype = "fixed"
    j = ET.SubElement(model, "joint", {"name": urdf_joint.get("name"), "type": jtype})
    ET.SubElement(j, "parent").text = urdf_joint.find("parent").get("link")
    ET.SubElement(j, "child").text = urdf_joint.find("child").get("link")
    urdf_axis = urdf_joint.find("axis")
    if urdf_axis is not None and jtype in {"revolute", "prismatic", "continuous"}:
        axis = ET.SubElement(j, "axis")
        ET.SubElement(axis, "xyz").text = urdf_axis.get("xyz", "0 0 1")
        limit = urdf_joint.find("limit")
        if limit is not None and jtype != "continuous":
            le = ET.SubElement(axis, "limit")
            ET.SubElement(le, "lower").text = limit.get("lower", "0")
            ET.SubElement(le, "upper").text = limit.get("upper", "0")
            if limit.get("effort"):
                ET.SubElement(le, "effort").text = limit.get("effort")
            if limit.get("velocity"):
                ET.SubElement(le, "velocity").text = limit.get("velocity")
        dyn = urdf_joint.find("dynamics")
        if dyn is not None:
            dd = ET.SubElement(axis, "dynamics")
            if dyn.get("damping"):
                ET.SubElement(dd, "damping").text = dyn.get("damping")
            if dyn.get("friction"):
                ET.SubElement(dd, "friction").text = dyn.get("friction")


# --- 小 SE(3) 工具(纯 stdlib,URDF 固定轴 rpy = Rz·Ry·Rx)---------------------
def _origin_to_Rt(origin: ET.Element | None) -> tuple[list[list[float]], list[float]]:
    if origin is None:
        return _identity_R(), [0.0, 0.0, 0.0]
    xyz = [float(v) for v in (origin.get("xyz") or "0 0 0").split()]
    rpy = [float(v) for v in (origin.get("rpy") or "0 0 0").split()]
    return _rpy_to_R(*rpy), xyz


def _identity_R() -> list[list[float]]:
    return [[1.0, 0, 0], [0, 1.0, 0], [0, 0, 1.0]]


def _rpy_to_R(roll: float, pitch: float, yaw: float) -> list[list[float]]:
    cr, sr = math.cos(roll), math.sin(roll)
    cp, sp = math.cos(pitch), math.sin(pitch)
    cy, sy = math.cos(yaw), math.sin(yaw)
    # R = Rz(yaw) @ Ry(pitch) @ Rx(roll)
    return [
        [cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr],
        [sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr],
        [-sp,     cp * sr,                cp * cr],
    ]


def _R_to_rpy(R: list[list[float]]) -> tuple[float, float, float]:
    sy = math.sqrt(R[0][0] ** 2 + R[1][0] ** 2)
    if sy > 1e-9:
        roll = math.atan2(R[2][1], R[2][2])
        pitch = math.atan2(-R[2][0], sy)
        yaw = math.atan2(R[1][0], R[0][0])
    else:  # 万向锁
        roll = math.atan2(-R[1][2], R[1][1])
        pitch = math.atan2(-R[2][0], sy)
        yaw = 0.0
    return roll, pitch, yaw


def _matmul(A: list[list[float]], B: list[list[float]]) -> list[list[float]]:
    return [[sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def _matvec(A: list[list[float]], v: list[float]) -> list[float]:
    return [sum(A[i][k] * v[k] for k in range(3)) for i in range(3)]


def _compose(
    T1: tuple[list[list[float]], list[float]], T2: tuple[list[list[float]], list[float]]
) -> tuple[list[list[float]], list[float]]:
    R1, t1 = T1
    R2, t2 = T2
    return _matmul(R1, R2), [a + b for a, b in zip(_matvec(R1, t2), t1)]


def _accumulate_absolute(
    root: str, parent_of: dict[str, str], joint_T: dict
) -> dict[str, tuple[list[list[float]], list[float]]]:
    abs_T: dict[str, tuple] = {root: (_identity_R(), [0.0, 0.0, 0.0])}

    def resolve(link: str):
        if link in abs_T:
            return abs_T[link]
        parent = parent_of[link]
        abs_T[link] = _compose(resolve(parent), joint_T[link])
        return abs_T[link]

    for link in list(parent_of):
        resolve(link)
    return abs_T


def _g(v: float) -> str:
    """格式化浮点;把 -0.0 归一成 0,避免 SDF 里出现刺眼的 '-0'。"""
    return f"{v + 0.0:g}"


def _pose_text(R: list[list[float]], t: list[float]) -> str:
    r, p, y = _R_to_rpy(R)
    return " ".join(_g(v) for v in (*t, r, p, y))


# ---------------------------------------------------------------------------
# 4. 注入 sensors / 组 world SDF
# ---------------------------------------------------------------------------
def inject_sensors(model: ET.Element, sensors: list[dict[str, Any]]) -> int:
    by_link = {l.get("name"): l for l in model.findall("link")}
    count = 0
    for s in sensors:
        link = by_link.get(s["link"])
        if link is None:
            continue
        sensor = ET.SubElement(link, "sensor", {"name": s["name"], "type": _sdf_sensor_type(s["type"])})
        if s.get("update_rate"):
            ET.SubElement(sensor, "update_rate").text = f"{s['update_rate']:g}"
        if s.get("pose"):
            R, t = _yaml_pose_to_Rt(s["pose"])
            ET.SubElement(sensor, "pose").text = _pose_text(R, t)
        if s["type"] in {"camera", "depth_camera"} and s.get("camera"):
            cam = ET.SubElement(sensor, "camera")
            c = s["camera"]
            if "horizontal_fov" in c:
                ET.SubElement(cam, "horizontal_fov").text = f"{c['horizontal_fov']:g}"
            if "image" in c:
                img = ET.SubElement(cam, "image")
                if "width" in c["image"]:
                    ET.SubElement(img, "width").text = str(c["image"]["width"])
                if "height" in c["image"]:
                    ET.SubElement(img, "height").text = str(c["image"]["height"])
        count += 1
    return count


def _sdf_sensor_type(t: str) -> str:
    return {"depth_camera": "depth_camera", "lidar": "gpu_lidar", "gpu_lidar": "gpu_lidar"}.get(t, t)


def _yaml_pose_to_Rt(pose: dict[str, Any]) -> tuple[list[list[float]], list[float]]:
    xyz = pose.get("xyz", [0, 0, 0])
    rpy = pose.get("rpy", [0, 0, 0])
    return _rpy_to_R(*rpy), list(map(float, xyz))


def build_world_sdf(data: dict[str, Any]) -> ET.Element:
    sdf = ET.Element("sdf", {"version": data.get("sdformat_version", "1.12")})
    world = ET.SubElement(sdf, "world", {"name": data["world_name"]})

    phys = data.get("physics", {})
    pe = ET.SubElement(world, "physics", {"type": phys.get("type", "ode")})
    ET.SubElement(pe, "max_step_size").text = f"{phys.get('max_step_size', 0.001):g}"
    ET.SubElement(pe, "real_time_factor").text = f"{phys.get('real_time_factor', 1.0):g}"
    ET.SubElement(world, "gravity").text = " ".join(f"{v:g}" for v in phys.get("gravity", [0, 0, -9.81]))

    for light in data.get("light", []):
        le = ET.SubElement(world, "light", {"name": light["name"], "type": light["type"]})
        if "direction" in light:
            ET.SubElement(le, "direction").text = " ".join(f"{v:g}" for v in light["direction"])
        ET.SubElement(le, "cast_shadows").text = "true" if light.get("cast_shadows", True) else "false"

    for inc in data.get("include_models", []):
        ie = ET.SubElement(world, "include")
        ET.SubElement(ie, "uri").text = inc["uri"]
        if inc.get("name"):
            ET.SubElement(ie, "name").text = inc["name"]
        if inc.get("static"):
            ET.SubElement(ie, "static").text = "true"
        if inc.get("pose"):
            R, t = _yaml_pose_to_Rt(inc["pose"])
            ET.SubElement(ie, "pose").text = _pose_text(R, t)

    ground = data.get("ground")
    if ground and ground.get("type") == "plane":
        _emit_ground_plane(world, ground)

    for plugin in data.get("plugins", []):
        ET.SubElement(world, "plugin", {"filename": plugin["filename"], "name": plugin["name"]})

    return sdf


def _emit_ground_plane(world: ET.Element, ground: dict[str, Any]) -> None:
    size = ground.get("size", [100, 100])
    friction = ground.get("friction", {})
    gm = ET.SubElement(world, "model", {"name": "ground_plane"})
    ET.SubElement(gm, "static").text = "true"
    link = ET.SubElement(gm, "link", {"name": "link"})
    for tag in ("collision", "visual"):
        block = ET.SubElement(link, tag, {"name": tag})
        geo = ET.SubElement(block, "geometry")
        plane = ET.SubElement(geo, "plane")
        ET.SubElement(plane, "normal").text = "0 0 1"
        ET.SubElement(plane, "size").text = " ".join(f"{v:g}" for v in size)
        if tag == "collision" and friction:
            surf = ET.SubElement(block, "surface")
            fr = ET.SubElement(surf, "friction")
            ode = ET.SubElement(fr, "ode")
            if "mu" in friction:
                ET.SubElement(ode, "mu").text = f"{friction['mu']:g}"
            if "mu2" in friction:
                ET.SubElement(ode, "mu2").text = f"{friction['mu2']:g}"


# ---------------------------------------------------------------------------
# 5. 序列化 + L1 passthrough
# ---------------------------------------------------------------------------
GEN_SDF_TEMPLATE = '''\
"""Auto-generated by export_sdf.py (L2 → L1 passthrough). Do not hand-edit."""
from __future__ import annotations


SDF_XML = {sdf_xml!r}


def gen_sdf() -> str:
    return SDF_XML
'''


def _serialize(elem: ET.Element) -> str:
    ET.indent(elem, space="  ")
    body = ET.tostring(elem, encoding="unicode", short_empty_elements=True)
    return f'<?xml version="1.0"?>\n{body}\n'


def _wrap_model_as_sdf(model: ET.Element, version: str) -> ET.Element:
    sdf = ET.Element("sdf", {"version": version})
    sdf.append(model)
    return sdf


def write_xml(elem: ET.Element, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(_serialize(elem), encoding="utf-8")
    return dest


def validate_in_process(xml_text: str, dest: Path) -> list[str]:
    """用 L1 bundled validation 校验(不依赖 gz);返回 error 文案列表(空=通过)。"""
    try:
        from sdf.validation import validate_sdf_xml
    except Exception as exc:  # pragma: no cover
        return [f"无法加载 L1 validation: {exc}"]
    result = validate_sdf_xml(xml_text, source_path=dest, base_dir=dest.parent)
    return [f.format() for f in result.errors]


def run_l1(gen_src: Path, *, output_sdf: Path, gz_check: str) -> tuple[bool, str]:
    import os
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [str(SHARED_CADPY_SRC), env.get("PYTHONPATH", "")]
    ).rstrip(os.pathsep)
    cmd = [sys.executable, "-m", "sdf", str(gen_src), "-o", str(output_sdf), "--gz-check", gz_check]
    try:
        proc = subprocess.run(
            cmd, cwd=str(SCRIPTS_DIR), env=env,
            capture_output=True, text=True, check=False, timeout=120,
        )
    except Exception as exc:  # pragma: no cover
        return False, f"L1 invocation failed: {exc}"
    log = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode == 0 and output_sdf.exists(), log.strip()


# ---------------------------------------------------------------------------
# 6. 主流程
# ---------------------------------------------------------------------------
def export(
    world_yaml: Path,
    output_dir: Path,
    *,
    urdf: Path | None = None,
    gz_check: str = "auto",
    no_l1: bool = False,
) -> ExportReport:
    data = load_yaml(world_yaml)
    validate_schema(data)
    version = data.get("sdformat_version", "1.12")
    output_dir.mkdir(parents=True, exist_ok=True)
    warns: list[str] = []

    # --- model SDF(可选,给了 --urdf 才转)---
    model_elem: ET.Element | None = None
    output_model: Path | None = None
    model_links: set[str] | None = None
    gz_used = False
    sensors_injected = 0
    model_link_count = model_joint_count = 0

    if urdf is not None:
        if not urdf.exists():
            raise ExportSdfError(f"--urdf 路径不存在: {urdf}")
        model_name = (
            _model_name_from_uri(data["include_models"][0]["uri"])
            if data.get("include_models") else "model"
        )
        model_elem, gz_used, conv_warns = convert_urdf_to_model_sdf(urdf, model_name=model_name)
        warns.extend(conv_warns)
        model_links = {l.get("name") for l in model_elem.findall("link")}
        model_link_count = len(model_links)
        model_joint_count = len(model_elem.findall("joint"))
        sensors_injected = inject_sensors(model_elem, data.get("sensors", []))

    check_invariants(data, model_links=model_links)

    # model.sdf 落盘 + bundled 校验
    if model_elem is not None:
        model_sdf = _wrap_model_as_sdf(model_elem, version)
        output_model = output_dir / "model.sdf"
        model_errors = validate_in_process(_serialize(model_sdf), output_model)
        if model_errors:
            raise ExportSdfError("model SDF 校验失败:\n" + "\n".join(model_errors))
        write_xml(model_sdf, output_model)

    # --- world SDF ---
    world_elem = build_world_sdf(data)
    output_world = output_dir / "world.sdf"
    world_xml = _serialize(world_elem)
    world_errors = validate_in_process(world_xml, output_world)
    if world_errors:
        raise ExportSdfError("world SDF 校验失败:\n" + "\n".join(world_errors))

    l1_passed = False
    l1_log = "skipped"
    if no_l1:
        write_xml(world_elem, output_world)
    else:
        gen_src = output_dir / f"{data['world_name']}_gen_sdf.py"
        gen_src.write_text(GEN_SDF_TEMPLATE.format(sdf_xml=world_xml), encoding="utf-8")
        l1_passed, l1_log = run_l1(gen_src, output_sdf=output_world, gz_check=gz_check)
        if not l1_passed:
            warnings.warn(f"L1 CLI 未通过,退回直写。log={l1_log}")
            write_xml(world_elem, output_world)

    # --- R3:gz 不可用时落 _errors/sdf.json ---
    gz_ok = gz_available()
    if not gz_ok and urdf is not None:
        errors_dir = output_dir / "_errors"
        errors_dir.mkdir(parents=True, exist_ok=True)
        (errors_dir / "sdf.json").write_text(
            json.dumps(
                {
                    "gz_unavailable": True,
                    "fallback_used": "self-converter",
                    "covered_tags": ["link", "joint", "inertial", "visual", "collision"],
                    "dropped": ["sensor/plugin 高保真(仅 yaml 注入的 sensor 进 model)", "frame relative_to 语义"],
                    "remedy": "brew install ignition-tools / apt install libgz-tools2 后重跑可得高保真转换",
                    "ref": "share/build123d-cad改造/04 §11.3 step6 / §13 R3",
                },
                ensure_ascii=False, indent=2,
            ),
            encoding="utf-8",
        )

    return ExportReport(
        world_name=data["world_name"],
        output_world=output_world,
        output_model=output_model,
        model_link_count=model_link_count,
        model_joint_count=model_joint_count,
        gz_available=gz_ok,
        gz_used=gz_used,
        sensors_injected=sensors_injected,
        l1_passed=l1_passed,
        l1_log=l1_log,
        warnings=warns,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="export_sdf",
        description="L2: world.yaml + URDF → SDF(Gazebo world)+ model.sdf. See 04 §11.",
    )
    parser.add_argument("world_yaml", type=Path)
    parser.add_argument("--urdf", type=Path, default=None,
                        help="上游 URDF;给了才做 URDF→SDF model 转换")
    parser.add_argument("-o", "--output", type=Path, default=Path.cwd() / "out_sdf")
    parser.add_argument("--gz-check", choices=("auto", "required", "never"), default="auto")
    parser.add_argument("--no-l1", action="store_true",
                        help="跳过 L1 CLI passthrough(单元测试 fallback)")
    args = parser.parse_args(argv)
    report = export(
        args.world_yaml.resolve(),
        args.output.resolve(),
        urdf=args.urdf.resolve() if args.urdf else None,
        gz_check=args.gz_check,
        no_l1=args.no_l1,
    )
    print(report.as_text())
    if report.warnings:
        print("\nwarnings:")
        for w in report.warnings:
            print(f"  - {w}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
