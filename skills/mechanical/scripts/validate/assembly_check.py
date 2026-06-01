"""
装配碰撞检测 / Assembly Collision Detection
用途：检查装配体中零件是否干涉
用法：python assembly_check.py part1.step part2.step [part3.step ...]
"""
import sys
from build123d import *

def check_assembly(step_files: list[str]):
    """检查多个 STEP 文件组成的装配体"""
    print("=" * 50)
    print("装配碰撞检测")
    print("=" * 50)

    # 导入所有零件
    parts = []
    for f in step_files:
        try:
            part = import_step(f)
            part.label = f.replace(".step", "")
            parts.append(part)
            bb = part.bounding_box()
            print(f"✅ {f}: {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm, "
                  f"体积 {part.volume:.1f} mm³")
        except Exception as e:
            print(f"❌ {f}: 导入失败 — {e}")
            return

    if len(parts) < 2:
        print("⚠️ 需要至少 2 个零件才能检查碰撞")
        return

    # 组装
    assembly = Compound(children=parts)

    # 碰撞检测
    print("\n碰撞检测...")
    collisions = assembly.do_children_intersect()

    if collisions:
        print(f"\n❌ 发现 {len(collisions)} 处干涉:")
        for i, pair in enumerate(collisions, 1):
            print(f"  {i}. {pair}")
    else:
        print("\n✅ 无干涉 — 装配通过")

    # 装配体统计
    total_volume = sum(p.volume for p in parts)
    assy_volume = assembly.volume
    overlap = total_volume - assy_volume
    print(f"\n零件总体积: {total_volume:.1f} mm³")
    print(f"装配体积: {assy_volume:.1f} mm³")
    if overlap > 0.1:
        print(f"⚠️ 重叠体积: {overlap:.1f} mm³ ({overlap/total_volume:.1%})")

    print("=" * 50)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python assembly_check.py part1.step part2.step [part3.step ...]")
        sys.exit(1)
    check_assembly(sys.argv[1:])
