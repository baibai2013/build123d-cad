#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L2 适配层: joints.yaml + STEP → URDF + meshes/.

用法
----
python skills/urdf/scripts/export_urdf.py <joints.yaml> [-o output_dir/] [--no-l1]

行为
----
1. 读 joints.yaml
2. 用 shared/schemas/joints.schema.json 强校验(jsonschema)
3. 跑「强不变量」检查(单根 / 无环 / parent·child 在 links / axis 非零 / limit 一致)
4. 写 `<output_dir>/<robot>_gen_urdf.py`:内嵌 `gen_urdf()`,返回 ET.Element
5. 调 L1 CLI(`python -m urdf <gen_src>.py -o robot.urdf`)做最后校验+写 URDF
   - `--no-l1` 时跳过 L1,直接由 L2 写 URDF(仅给单元测试 fallback 用)
6. 若 mesh 字段存在且 STEP 在场,优先 build123d/trimesh 把 STEP→STL 落 meshes/;
   缺依赖时跳过(visual/collision 不写 mesh,仅 inertial-only),WARN 不报错
7. 报告:link/joint 数 / inertial fallback link / mesh 状态 / L1 校验结果

设计要点见 share/build123d-cad改造/04 §8(字段全集) / §9(mount_points 映射)。
"""
from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
import warnings
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET

REPO_ROOT = Path(__file__).resolve().parents[3]  # ~/.agents/skills/build123d-cad
SHARED_SCHEMAS = REPO_ROOT / "shared" / "schemas"
SCHEMA_PATH = SHARED_SCHEMAS / "joints.schema.json"


class ExportUrdfError(RuntimeError):
    pass


@dataclass
class ExportReport:
    robot: str
    output_urdf: Path
    link_count: int
    joint_count: int
    inertial_fallback_links: list[str]
    mesh_warnings: list[str]
    l1_passed: bool
    l1_log: str

    def as_text(self) -> str:
        lines = [
            f"robot: {self.robot}",
            f"links: {self.link_count}  joints: {self.joint_count}",
            f"output: {self.output_urdf}",
            f"inertial-fallback links: {', '.join(self.inertial_fallback_links) or '(none)'}",
            f"mesh warnings: {len(self.mesh_warnings)}",
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
        raise ExportUrdfError("missing dependency: pip install pyyaml") from exc
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def validate_schema(data: dict[str, Any], *, schema_path: Path = SCHEMA_PATH) -> None:
    try:
        import jsonschema
    except ImportError as exc:  # pragma: no cover
        raise ExportUrdfError("missing dependency: pip install jsonschema") from exc
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(data)


# ---------------------------------------------------------------------------
# 2. 强不变量(超出 JSON Schema)
# ---------------------------------------------------------------------------
def check_invariants(data: dict[str, Any]) -> None:
    link_names = [link["name"] for link in data["links"]]
    if len(set(link_names)) != len(link_names):
        raise ExportUrdfError("links[].name not unique")
    joint_names = [j["name"] for j in data["joints"]]
    if len(set(joint_names)) != len(joint_names):
        raise ExportUrdfError("joints[].name not unique")

    link_set = set(link_names)
    parents: dict[str, str] = {}
    for joint in data["joints"]:
        for side in ("parent", "child"):
            if joint[side] not in link_set:
                raise ExportUrdfError(f"joint {joint['name']}.{side}={joint[side]!r} not in links[]")
        if joint["child"] in parents:
            raise ExportUrdfError(f"link {joint['child']} has multiple parents")
        parents[joint["child"]] = joint["parent"]
        if joint.get("type") in {"revolute", "prismatic", "continuous"}:
            axis = joint.get("axis") or [0, 0, 0]
            mag = sum(a * a for a in axis)
            if mag <= 1e-9:
                raise ExportUrdfError(f"joint {joint['name']} axis is zero")
        limit = joint.get("limit")
        if limit and limit["lower"] >= limit["upper"]:
            raise ExportUrdfError(f"joint {joint['name']} limit lower >= upper")

    roots = [name for name in link_names if name not in parents]
    if len(roots) != 1:
        raise ExportUrdfError(f"expected exactly 1 root link, got {len(roots)}: {roots}")
    if len(data["joints"]) != len(link_names) - 1:
        raise ExportUrdfError(
            f"link/joint count mismatch: {len(link_names)} links vs {len(data['joints'])} joints "
            f"(expected joints = links - 1 for tree topology)"
        )

    # 无环检查: 从 root 出发 BFS 必须能覆盖所有 link
    children: dict[str, list[str]] = defaultdict(list)
    for joint in data["joints"]:
        children[joint["parent"]].append(joint["child"])
    seen = set()
    stack = [roots[0]]
    while stack:
        node = stack.pop()
        if node in seen:
            raise ExportUrdfError(f"cycle detected at link {node}")
        seen.add(node)
        stack.extend(children.get(node, []))
    if seen != link_set:
        raise ExportUrdfError(f"links not connected from root: missing {link_set - seen}")


# ---------------------------------------------------------------------------
# 3. URDF XML 构建
# ---------------------------------------------------------------------------
INERTIAL_FALLBACK = {
    "mass": 1.0,
    "origin": {"xyz": [0, 0, 0], "rpy": [0, 0, 0]},
    "inertia": {"ixx": 0.001, "iyy": 0.001, "izz": 0.001,
                "ixy": 0, "ixz": 0, "iyz": 0},
}


def _fmt_vec(values: list[float]) -> str:
    return " ".join(f"{v:g}" for v in values)


def _origin_elem(origin: dict[str, Any]) -> ET.Element:
    e = ET.Element("origin")
    e.set("xyz", _fmt_vec(origin["xyz"]))
    e.set("rpy", _fmt_vec(origin["rpy"]))
    return e


def _build_inertial(inertial: dict[str, Any]) -> ET.Element:
    e = ET.Element("inertial")
    e.append(_origin_elem(inertial["origin"]))
    mass = ET.SubElement(e, "mass")
    mass.set("value", f"{inertial['mass']:g}")
    inertia = ET.SubElement(e, "inertia")
    for key in ("ixx", "ixy", "ixz", "iyy", "iyz", "izz"):
        inertia.set(key, f"{inertial['inertia'][key]:g}")
    return e


def _build_visual_or_collision(tag: str, link: dict[str, Any], data: dict[str, Any], *, scale: str) -> ET.Element | None:
    mesh_field = link.get("mesh")
    if not mesh_field:
        return None
    elem = ET.Element(tag)
    elem.append(_origin_elem({"xyz": [0, 0, 0], "rpy": [0, 0, 0]}))
    geometry = ET.SubElement(elem, "geometry")
    mesh = ET.SubElement(geometry, "mesh")
    if data.get("mesh_uri_style") == "package":
        pkg = data["package_name"]
        mesh.set("filename", f"package://{pkg}/meshes/{link['name']}.stl")
    else:
        mesh.set("filename", f"meshes/{link['name']}.stl")
    mesh.set("scale", scale)
    return elem


def _build_collision_primitive(link: dict[str, Any]) -> ET.Element | None:
    prim = link.get("collision_primitive")
    if not prim:
        return None
    coll = ET.Element("collision")
    coll.append(_origin_elem(prim["origin"]))
    geom = ET.SubElement(coll, "geometry")
    if prim["type"] == "box":
        ET.SubElement(geom, "box").set("size", _fmt_vec(prim["size"]))
    elif prim["type"] == "cylinder":
        cyl = ET.SubElement(geom, "cylinder")
        cyl.set("radius", f"{prim['radius']:g}")
        cyl.set("length", f"{prim['length']:g}")
    elif prim["type"] == "sphere":
        ET.SubElement(geom, "sphere").set("radius", f"{prim['radius']:g}")
    return coll


def build_urdf(data: dict[str, Any]) -> tuple[ET.Element, list[str]]:
    fallback_links: list[str] = []
    mesh_units = data.get("mesh_units", "mm")
    scale = "0.001 0.001 0.001" if mesh_units == "mm" else "1 1 1"

    robot = ET.Element("robot", {"name": data["robot"]})
    fallback_comment = (
        "INERTIAL-FALLBACK: links missing inertial use 1kg + 0.001*I diagonal. "
        "See share/build123d-cad改造/04 §7.3."
    )

    for link in data["links"]:
        link_elem = ET.SubElement(robot, "link", {"name": link["name"]})
        inertial = link.get("inertial")
        if inertial is None:
            fallback_links.append(link["name"])
            inertial = INERTIAL_FALLBACK
        link_elem.append(_build_inertial(inertial))

        visual = _build_visual_or_collision("visual", link, data, scale=scale)
        if visual is not None:
            link_elem.append(visual)
        coll_mode = link.get("collision", "same_as_visual")
        if coll_mode == "primitive":
            cp = _build_collision_primitive(link)
            if cp is not None:
                link_elem.append(cp)
        else:
            coll = _build_visual_or_collision("collision", link, data, scale=scale)
            if coll is not None:
                link_elem.append(coll)

    if fallback_links and len(fallback_links) < len(data["links"]):
        robot.insert(0, ET.Comment(f" {fallback_comment} fallbacks: {', '.join(fallback_links)} "))
    elif fallback_links:
        raise ExportUrdfError(
            "every link missing inertial → URDF refused. See 04 §7.3 (tech_lead 决议)."
        )

    for joint in data["joints"]:
        j = ET.SubElement(robot, "joint", {"name": joint["name"], "type": joint["type"]})
        ET.SubElement(j, "parent").set("link", joint["parent"])
        ET.SubElement(j, "child").set("link", joint["child"])
        j.append(_origin_elem(joint["origin"]))
        if joint.get("axis") is not None:
            ET.SubElement(j, "axis").set("xyz", _fmt_vec(joint["axis"]))
        limit = joint.get("limit")
        if limit and joint["type"] != "continuous":
            le = ET.SubElement(j, "limit")
            le.set("lower", f"{limit['lower']:g}")
            le.set("upper", f"{limit['upper']:g}")
            le.set("effort", f"{limit.get('effort', 0):g}")
            le.set("velocity", f"{limit.get('velocity', 0):g}")
        dynamics = joint.get("dynamics")
        if dynamics:
            de = ET.SubElement(j, "dynamics")
            for key in ("damping", "friction"):
                if key in dynamics:
                    de.set(key, f"{dynamics[key]:g}")
        mimic = joint.get("mimic")
        if mimic:
            me = ET.SubElement(j, "mimic")
            me.set("joint", mimic["joint"])
            if "multiplier" in mimic:
                me.set("multiplier", f"{mimic['multiplier']:g}")
            if "offset" in mimic:
                me.set("offset", f"{mimic['offset']:g}")

    return robot, fallback_links


# ---------------------------------------------------------------------------
# 4. mesh STEP→STL(可选,缺依赖跳过)
# ---------------------------------------------------------------------------
def export_meshes(data: dict[str, Any], *, source_dir: Path, meshes_dir: Path) -> list[str]:
    warnings_: list[str] = []
    meshes_dir.mkdir(parents=True, exist_ok=True)

    converter = _pick_mesh_converter()
    for link in data["links"]:
        mesh = link.get("mesh")
        if not mesh:
            continue
        step_path = (source_dir / mesh).resolve()
        if not step_path.exists():
            warnings_.append(f"link={link['name']} mesh path does not exist: {step_path}")
            continue
        out_stl = meshes_dir / f"{link['name']}.stl"
        if step_path.suffix.lower() == ".stl":
            shutil.copyfile(step_path, out_stl)
            continue
        if converter is None:
            warnings_.append(f"link={link['name']} STEP→STL skipped (no build123d/trimesh available)")
            continue
        try:
            converter(step_path, out_stl)
        except Exception as exc:  # pragma: no cover
            warnings_.append(f"link={link['name']} STEP→STL failed: {exc}")
    return warnings_


def _pick_mesh_converter():
    try:  # build123d preferred(与 mechanical 通道一致)
        import build123d  # noqa: F401

        from build123d import import_step, export_stl  # type: ignore

        def convert_b123d(step_path: Path, out_stl: Path) -> None:
            shape = import_step(str(step_path))
            export_stl(shape, str(out_stl))

        return convert_b123d
    except Exception:
        pass
    try:  # trimesh fallback
        import trimesh  # type: ignore

        def convert_trimesh(step_path: Path, out_stl: Path) -> None:
            mesh = trimesh.load_mesh(str(step_path))
            mesh.export(str(out_stl))

        return convert_trimesh
    except Exception:
        return None


# ---------------------------------------------------------------------------
# 5. 写 gen_urdf 源 + 调 L1 CLI
# ---------------------------------------------------------------------------
GEN_URDF_TEMPLATE = '''\
"""Auto-generated by export_urdf.py (L2 → L1 passthrough). Do not hand-edit."""
from __future__ import annotations

import xml.etree.ElementTree as ET


URDF_XML = {urdf_xml!r}


def gen_urdf() -> ET.Element:
    return ET.fromstring(URDF_XML)
'''


def write_gen_urdf_source(robot_elem: ET.Element, *, dest: Path) -> Path:
    ET.indent(robot_elem, space="  ")
    xml_str = ET.tostring(robot_elem, encoding="unicode", short_empty_elements=True)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(GEN_URDF_TEMPLATE.format(urdf_xml=xml_str), encoding="utf-8")
    return dest


def write_urdf_direct(robot_elem: ET.Element, *, dest: Path) -> Path:
    ET.indent(robot_elem, space="  ")
    body = ET.tostring(robot_elem, encoding="unicode", short_empty_elements=True)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(f'<?xml version="1.0"?>\n{body}\n', encoding="utf-8")
    return dest


def run_l1(gen_src: Path, *, output_urdf: Path) -> tuple[bool, str]:
    scripts_dir = REPO_ROOT / "skills" / "urdf" / "scripts"
    cmd = [sys.executable, "-m", "urdf", str(gen_src), "-o", str(output_urdf)]
    try:
        proc = subprocess.run(
            cmd, cwd=str(scripts_dir),
            capture_output=True, text=True, check=False, timeout=60,
        )
    except Exception as exc:  # pragma: no cover
        return False, f"L1 invocation failed: {exc}"
    log = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode == 0 and output_urdf.exists(), log.strip()


# ---------------------------------------------------------------------------
# 6. CLI
# ---------------------------------------------------------------------------
def export(joints_yaml: Path, output_dir: Path, *, no_l1: bool = False) -> ExportReport:
    data = load_yaml(joints_yaml)
    validate_schema(data)
    check_invariants(data)

    output_dir.mkdir(parents=True, exist_ok=True)
    meshes_dir = output_dir / "meshes"
    mesh_warnings = export_meshes(data, source_dir=joints_yaml.parent, meshes_dir=meshes_dir)

    robot_elem, fallback_links = build_urdf(data)
    output_urdf = output_dir / "robot.urdf"

    l1_passed = False
    l1_log = "skipped"
    if no_l1:
        write_urdf_direct(robot_elem, dest=output_urdf)
    else:
        gen_src = output_dir / f"{data['robot']}_gen_urdf.py"
        write_gen_urdf_source(robot_elem, dest=gen_src)
        l1_passed, l1_log = run_l1(gen_src, output_urdf=output_urdf)
        if not l1_passed:
            warnings.warn(f"L1 CLI failed, fallback to direct write. log={l1_log}")
            write_urdf_direct(robot_elem, dest=output_urdf)

    return ExportReport(
        robot=data["robot"],
        output_urdf=output_urdf,
        link_count=len(data["links"]),
        joint_count=len(data["joints"]),
        inertial_fallback_links=fallback_links,
        mesh_warnings=mesh_warnings,
        l1_passed=l1_passed,
        l1_log=l1_log,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="export_urdf",
        description="L2: joints.yaml + STEP → URDF + meshes/. See 04 §8.",
    )
    parser.add_argument("joints_yaml", type=Path)
    parser.add_argument("-o", "--output", type=Path, default=Path.cwd() / "out_urdf")
    parser.add_argument("--no-l1", action="store_true",
                        help="skip L1 CLI passthrough (用于 unit test fallback)")
    args = parser.parse_args(argv)
    report = export(args.joints_yaml.resolve(), args.output.resolve(), no_l1=args.no_l1)
    print(report.as_text())
    if report.mesh_warnings:
        print("\nmesh warnings:")
        for w in report.mesh_warnings:
            print(f"  - {w}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
