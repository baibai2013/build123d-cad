"""
打印导出工具 / 3D Print Export Utility
用途：导出 STL/3MF 并自动设置合适的精度参数
用法：python print_export.py part.step [format] [quality]
"""
import sys
import os
from build123d import *

# 导出参数预设
QUALITY_PRESETS = {
    "draft": {
        "linear_tolerance": 0.2,
        "angular_tolerance": 1.0,
        "desc": "草稿（FDM 0.3mm 层高）"
    },
    "standard": {
        "linear_tolerance": 0.1,
        "angular_tolerance": 0.5,
        "desc": "标准（FDM 0.2mm 层高）"
    },
    "fine": {
        "linear_tolerance": 0.05,
        "angular_tolerance": 0.2,
        "desc": "精细（FDM 0.1mm 层高）"
    },
    "sla": {
        "linear_tolerance": 0.01,
        "angular_tolerance": 0.1,
        "desc": "SLA 树脂打印"
    },
}


def print_export(step_file: str, fmt: str = "stl", quality: str = "standard"):
    """导出零件为打印格式"""
    print("=" * 50)
    print(f"打印导出: {step_file}")
    print("=" * 50)

    # 导入
    part = import_step(step_file)
    bb = part.bounding_box()
    print(f"尺寸: {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm")
    print(f"体积: {part.volume:.1f} mm³")

    # 质量预设
    if quality not in QUALITY_PRESETS:
        print(f"⚠️ 未知质量预设 '{quality}'，可选: {', '.join(QUALITY_PRESETS.keys())}")
        return

    preset = QUALITY_PRESETS[quality]
    print(f"精度: {preset['desc']}")
    print(f"  linear_tolerance: {preset['linear_tolerance']}")
    print(f"  angular_tolerance: {preset['angular_tolerance']}")

    # 导出
    base_name = os.path.splitext(step_file)[0]

    if fmt == "stl":
        output = f"{base_name}.stl"
        export_stl(part, output,
                   linear_tolerance=preset["linear_tolerance"],
                   angular_tolerance=preset["angular_tolerance"])
    elif fmt == "3mf":
        output = f"{base_name}.3mf"
        export_3mf(part, output)
    else:
        print(f"⚠️ 未知格式 '{fmt}'，支持: stl, 3mf")
        return

    file_size = os.path.getsize(output)
    print(f"\n✅ 导出: {output}")
    print(f"   文件大小: {file_size:,} bytes ({file_size/1024:.1f} KB)")

    # 打印建议
    max_dim = max(bb.size.X, bb.size.Y, bb.size.Z)
    print(f"\n打印建议:")
    print(f"  最大尺寸: {max_dim:.1f} mm")
    if max_dim > 220:
        print("  ⚠️ 超过常见 FDM 打印床（220mm），考虑分件打印")
    if part.volume < 100:
        print("  ⚠️ 零件很小，注意精细特征是否可打印")

    print("=" * 50)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python print_export.py part.step [stl|3mf] [draft|standard|fine|sla]")
        sys.exit(1)

    step_file = sys.argv[1]
    fmt = sys.argv[2] if len(sys.argv) > 2 else "stl"
    quality = sys.argv[3] if len(sys.argv) > 3 else "standard"
    print_export(step_file, fmt, quality)
