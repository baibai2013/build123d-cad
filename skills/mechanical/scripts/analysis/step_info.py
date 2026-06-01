#!/usr/bin/env python3
"""
step_info.py — 读取 STEP 文件并输出详细信息

用法:
    python3 step_info.py <file.step> [--json]

输出:
    - 包围盒尺寸
    - 体积和表面积
    - 拓扑统计（面/边/顶点/实体数量）
    - 几何类型分布（平面/柱面/球面/环面等）
    - 质心位置
    - 可选 JSON 输出（用于脚本集成）
"""

import sys
import argparse
import json
from pathlib import Path


def analyze_step(step_path: Path, as_json: bool = False):
    try:
        from build123d import import_step
        from OCP.BRepGProp import BRepGProp
        from OCP.GProp import GProp_GProps
        from OCP.BRepCheck import BRepCheck_Analyzer
        from OCP.TopAbs import TopAbs_FACE, TopAbs_EDGE, TopAbs_VERTEX, TopAbs_SOLID, TopAbs_SHELL
        from OCP.TopExp import TopExp_Explorer
        from OCP.GeomAbs import GeomAbs_Plane, GeomAbs_Cylinder, GeomAbs_Cone, GeomAbs_Sphere, GeomAbs_Torus
        from OCP.BRep import BRep_Tool
        from OCP.BRepAdaptor import BRepAdaptor_Surface
        from OCP.gp import gp_Pnt
    except ImportError as e:
        print(f"依赖缺失: {e}")
        print("请安装: pip install build123d")
        sys.exit(1)

    shape = import_step(str(step_path))
    wrapped = shape.wrapped

    # 包围盒
    bb = shape.bounding_box()

    # 体积/面积/质心
    vol_props = GProp_GProps()
    BRepGProp.VolumeProperties_s(wrapped, vol_props)
    volume = vol_props.Mass()
    cx, cy, cz = vol_props.CentreOfMass().X(), vol_props.CentreOfMass().Y(), vol_props.CentreOfMass().Z()

    surf_props = GProp_GProps()
    BRepGProp.SurfaceProperties_s(wrapped, surf_props)
    area = surf_props.Mass()

    # 几何有效性
    analyzer = BRepCheck_Analyzer(wrapped)
    is_valid = analyzer.IsValid()

    # 拓扑统计
    def count_topo(shape, topo_type):
        exp = TopExp_Explorer(shape, topo_type)
        count = 0
        while exp.More():
            count += 1
            exp.Next()
        return count

    n_faces    = count_topo(wrapped, TopAbs_FACE)
    n_edges    = count_topo(wrapped, TopAbs_EDGE)
    n_vertices = count_topo(wrapped, TopAbs_VERTEX)
    n_solids   = count_topo(wrapped, TopAbs_SOLID)
    n_shells   = count_topo(wrapped, TopAbs_SHELL)

    # 面几何类型分布
    surface_types = {
        "平面":   0, "柱面": 0, "锥面": 0,
        "球面":   0, "环面": 0, "其他": 0,
    }
    exp = TopExp_Explorer(wrapped, TopAbs_FACE)
    while exp.More():
        face = exp.Current()
        try:
            adaptor = BRepAdaptor_Surface(face)
            st = adaptor.GetType()
            if   st == GeomAbs_Plane:    surface_types["平面"]   += 1
            elif st == GeomAbs_Cylinder: surface_types["柱面"]   += 1
            elif st == GeomAbs_Cone:     surface_types["锥面"]   += 1
            elif st == GeomAbs_Sphere:   surface_types["球面"]   += 1
            elif st == GeomAbs_Torus:    surface_types["环面"]   += 1
            else:                         surface_types["其他"]   += 1
        except:
            surface_types["其他"] += 1
        exp.Next()

    result = {
        "file":     str(step_path),
        "bbox_mm":  {"x": round(bb.size.X, 4), "y": round(bb.size.Y, 4), "z": round(bb.size.Z, 4)},
        "volume_mm3":   round(volume, 4),
        "area_mm2":     round(area, 4),
        "centroid_mm":  {"x": round(cx, 4), "y": round(cy, 4), "z": round(cz, 4)},
        "is_valid":     is_valid,
        "topology": {
            "solids": n_solids, "shells": n_shells,
            "faces": n_faces, "edges": n_edges, "vertices": n_vertices,
        },
        "surface_types": {k: v for k, v in surface_types.items() if v > 0},
    }

    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    # 人类可读输出
    print(f"\n{'=' * 55}")
    print(f"文件:      {step_path.name}")
    print(f"{'=' * 55}")
    print(f"包围盒:    {bb.size.X:.2f} × {bb.size.Y:.2f} × {bb.size.Z:.2f} mm")
    print(f"体积:      {volume:.2f} mm³  ({volume/1000:.4f} cm³)")
    print(f"表面积:    {area:.2f} mm²")
    print(f"质心:      ({cx:.2f}, {cy:.2f}, {cz:.2f})")
    print(f"几何有效:  {'是' if is_valid else '否 ⚠'}")
    print()
    print(f"拓扑统计:")
    print(f"  实体 {n_solids}  壳体 {n_shells}  面 {n_faces}  边 {n_edges}  顶点 {n_vertices}")
    print()
    print(f"面几何类型:")
    for k, v in surface_types.items():
        if v > 0:
            bar = "█" * min(v, 40)
            print(f"  {k:6s} {v:4d}  {bar}")
    print()


def main():
    parser = argparse.ArgumentParser(description="STEP 文件信息查看器")
    parser.add_argument("file", help="STEP 文件路径")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")
    args = parser.parse_args()

    path = Path(args.file).resolve()
    if not path.exists():
        print(f"错误: 找不到文件 {path}")
        sys.exit(1)
    if path.suffix.lower() not in (".step", ".stp"):
        print(f"警告: 文件扩展名不是 .step/.stp，仍尝试解析...")

    analyze_step(path, as_json=args.json)


if __name__ == "__main__":
    main()
