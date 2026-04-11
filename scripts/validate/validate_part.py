#!/usr/bin/env python3
"""
validate_part.py — build123d 零件几何验证工具

用法:
    python3 validate_part.py <part_script.py> [--verbose]
    python3 validate_part.py assets/01_mounting_plate.py
    python3 validate_part.py assets/01_mounting_plate.py --verbose

输出:
    - 尺寸（包围盒 X/Y/Z）
    - 体积、面积
    - 几何有效性（IsValid / BRep 检查）
    - 面/边/顶点数量
    - 警告：薄壁、极小特征、非流形几何
"""

import sys
import os
import subprocess
import importlib.util
import tempfile
import argparse
from pathlib import Path


# ───────────────────────── helpers ──────────────────────────

def run_script_capture_part(script_path: Path):
    """
    执行零件脚本，捕获 build123d Part 对象。
    通过注入收集代码实现，不修改原脚本。
    """
    collect_code = f"""
import sys, os
sys.path.insert(0, str({repr(str(script_path.parent))}))

# 执行零件脚本
with open({repr(str(script_path))}) as f:
    src = f.read()

# 覆盖 export_step/export_stl 等函数，避免生成文件
import build123d as _b123
_orig_export_step = _b123.export_step
_orig_export_stl  = getattr(_b123, 'export_stl', None)

_parts = []

def _capture_export(shape, *a, **kw):
    _parts.append(shape)

_b123.export_step = _capture_export
if _orig_export_stl:
    _b123.export_stl = _capture_export

import builtins
_g = dict(__builtins__=builtins.__dict__)
exec(src, _g)

# 恢复
_b123.export_step = _orig_export_step

# 输出结果
if _parts:
    part = _parts[-1]
    bb   = part.bounding_box()
    print(f"BBOX {{bb.size.X:.4f}} {{bb.size.Y:.4f}} {{bb.size.Z:.4f}}")
    print(f"VOLUME {{part.volume:.4f}}")
    try:
        print(f"AREA {{part.area:.4f}}")
    except:
        print("AREA N/A")
    try:
        from OCP.BRep import BRep_Builder
        from OCP.BRepCheck import BRepCheck_Analyzer
        ana = BRepCheck_Analyzer(part.wrapped)
        print(f"VALID {{ana.IsValid()}}")
    except Exception as e:
        print(f"VALID_CHECK_ERROR {{e}}")
    try:
        print(f"FACES {{len(list(part.faces()))}}")
        print(f"EDGES {{len(list(part.edges()))}}")
        print(f"VERTICES {{len(list(part.vertices()))}}")
    except:
        print("TOPO N/A")
else:
    print("NO_PART_FOUND")
"""
    result = subprocess.run(
        [sys.executable, "-c", collect_code],
        capture_output=True, text=True, timeout=120
    )
    return result.stdout, result.stderr


def parse_output(stdout: str) -> dict:
    data = {}
    for line in stdout.splitlines():
        if line.startswith("BBOX "):
            x, y, z = line[5:].split()
            data["bbox"] = (float(x), float(y), float(z))
        elif line.startswith("VOLUME "):
            data["volume"] = float(line[7:])
        elif line.startswith("AREA "):
            v = line[5:].strip()
            data["area"] = float(v) if v != "N/A" else None
        elif line.startswith("VALID "):
            data["valid"] = line[6:].strip().lower() in ("true", "1")
        elif line.startswith("VALID_CHECK_ERROR"):
            data["valid"] = None
        elif line.startswith("FACES "):
            data["faces"] = int(line[6:])
        elif line.startswith("EDGES "):
            data["edges"] = int(line[6:])
        elif line.startswith("VERTICES "):
            data["vertices"] = int(line[9:])
        elif line == "NO_PART_FOUND":
            data["error"] = "脚本中未检测到导出的零件"
    return data


def check_warnings(data: dict) -> list[str]:
    warnings = []
    if "bbox" in data:
        x, y, z = data["bbox"]
        min_dim = min(x, y, z)
        if min_dim < 0.5:
            warnings.append(f"极薄特征: 最小尺寸 {min_dim:.3f}mm（<0.5mm，可能导致打印/加工问题）")
        if max(x, y, z) > 500:
            warnings.append(f"超大零件: 最大尺寸 {max(x,y,z):.1f}mm（>500mm，确认单位是否正确）")
    if data.get("valid") is False:
        warnings.append("BRep 几何无效：可能存在非流形、自相交或开放边界")
    if "volume" in data and data["volume"] < 1:
        warnings.append(f"极小体积: {data['volume']:.4f}mm³（检查单位或建模意图）")
    return warnings


# ───────────────────────── main ──────────────────────────

def main():
    parser = argparse.ArgumentParser(description="build123d 零件几何验证工具")
    parser.add_argument("script", help="要验证的零件脚本路径")
    parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息（含stderr）")
    args = parser.parse_args()

    script = Path(args.script).resolve()
    if not script.exists():
        print(f"错误: 找不到文件 {script}")
        sys.exit(1)

    print(f"\n验证: {script.name}")
    print("=" * 50)

    stdout, stderr = run_script_capture_part(script)

    if args.verbose and stderr.strip():
        print("\n--- 脚本输出/错误 ---")
        print(stderr)
        print("---")

    data = parse_output(stdout)

    if "error" in data:
        print(f"失败: {data['error']}")
        if stderr:
            print("详情:", stderr[:500])
        sys.exit(1)

    if not data:
        print("执行失败，无法获取零件信息")
        if stderr:
            print("错误输出:", stderr[:500])
        sys.exit(1)

    # 打印结果
    if "bbox" in data:
        x, y, z = data["bbox"]
        print(f"包围盒:    {x:.2f} x {y:.2f} x {z:.2f} mm")

    if "volume" in data:
        vol = data["volume"]
        print(f"体积:      {vol:.2f} mm³  ({vol/1000:.4f} cm³)")

    if data.get("area") is not None:
        print(f"表面积:    {data['area']:.2f} mm²")

    if data.get("valid") is not None:
        status = "有效" if data["valid"] else "无效 ⚠"
        print(f"几何有效性: {status}")

    if "faces" in data:
        print(f"拓扑:      {data['faces']} 面 / {data['edges']} 边 / {data['vertices']} 顶点")

    # 警告
    warnings = check_warnings(data)
    if warnings:
        print("\n警告:")
        for w in warnings:
            print(f"  ⚠ {w}")
    else:
        print("\n通过所有检查")

    print()


if __name__ == "__main__":
    main()
