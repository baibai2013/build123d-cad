"""
质量属性分析 / Mass Properties Analysis
用途：计算零件的质量、惯性矩、质心位置
用法：python mass_properties.py part.step [material]
"""
import sys
from build123d import *

# 材料密度库 (g/mm³)
MATERIALS = {
    "PLA":       1.24e-3,
    "ABS":       1.04e-3,
    "PETG":      1.27e-3,
    "Nylon":     1.01e-3,
    "TPU":       1.21e-3,
    "Resin":     1.15e-3,
    "Al6061":    2.70e-3,
    "Steel":     7.85e-3,
    "Brass":     8.50e-3,
    "Copper":    8.96e-3,
    "Titanium":  4.50e-3,
    "Wood_PLA":  1.15e-3,
    "Carbon_PLA": 1.30e-3,
}


def analyze_mass(step_file: str, material: str = "PLA"):
    """分析 STEP 文件的质量属性"""
    print("=" * 50)
    print(f"质量属性分析: {step_file}")
    print("=" * 50)

    # 导入
    part = import_step(step_file)

    # 基本几何
    bb = part.bounding_box()
    volume = part.volume
    print(f"\n几何属性:")
    print(f"  包围盒: {bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f} mm")
    print(f"  体积: {volume:.2f} mm³ ({volume / 1000:.2f} cm³)")

    # 质量
    if material not in MATERIALS:
        print(f"\n⚠️ 未知材料 '{material}'，可选: {', '.join(MATERIALS.keys())}")
        density = float(material) if material.replace('.', '').isdigit() else None
        if density is None:
            return
        print(f"  使用自定义密度: {density} g/mm³")
    else:
        density = MATERIALS[material]

    mass_g = volume * density
    mass_kg = mass_g / 1000

    print(f"\n质量属性 ({material}, ρ={density * 1e3:.2f} g/cm³):")
    print(f"  质量: {mass_g:.2f} g ({mass_kg:.4f} kg)")

    # 惯性矩（包围盒近似）
    Lx, Ly, Lz = bb.size.X, bb.size.Y, bb.size.Z
    Ixx = mass_kg * (Ly**2 + Lz**2) / 12
    Iyy = mass_kg * (Lx**2 + Lz**2) / 12
    Izz = mass_kg * (Lx**2 + Ly**2) / 12

    print(f"\n惯性矩（包围盒近似, kg·mm²）:")
    print(f"  Ixx: {Ixx:.4f}")
    print(f"  Iyy: {Iyy:.4f}")
    print(f"  Izz: {Izz:.4f}")

    # 质心（包围盒中心近似）
    cx = (bb.min.X + bb.max.X) / 2
    cy = (bb.min.Y + bb.max.Y) / 2
    cz = (bb.min.Z + bb.max.Z) / 2
    print(f"\n质心（包围盒中心近似）:")
    print(f"  ({cx:.2f}, {cy:.2f}, {cz:.2f}) mm")

    # 填充率
    bb_volume = Lx * Ly * Lz
    fill_ratio = volume / bb_volume if bb_volume > 0 else 0
    print(f"\n填充率: {fill_ratio:.1%}")
    if fill_ratio < 0.3:
        print("  → 薄壁/空心结构")
    elif fill_ratio < 0.7:
        print("  → 中等密度结构")
    else:
        print("  → 实心结构")

    print("=" * 50)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python mass_properties.py part.step [material]")
        print(f"可选材料: {', '.join(MATERIALS.keys())}")
        sys.exit(1)

    step_file = sys.argv[1]
    material = sys.argv[2] if len(sys.argv) > 2 else "PLA"
    analyze_mass(step_file, material)
