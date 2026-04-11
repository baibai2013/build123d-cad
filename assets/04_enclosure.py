"""
矩形外壳（抽壳）/ Rectangular Enclosure (Shell)
用途：电子设备外壳、3D打印盒体
复杂度：★★★☆☆
"""
from build123d import *

# ===== 参数 =====
outer_l      = 100      # 外部长度 mm
outer_w      = 70       # 外部宽度 mm
outer_h      = 40       # 外部高度 mm
wall_t       = 2.5      # 壁厚 mm
corner_r     = 4        # 外角圆角 mm
lid_gap      = 0.3      # 盖子配合间隙 mm（单边）
boss_r       = 3.5      # 内部固定柱半径（螺纹嵌件用）mm
boss_h_ratio = 0.6      # 固定柱高度占内高比例
screw_r      = 1.5      # 螺丝孔半径 mm（M3）

# ===== 建模 =====
with BuildPart() as box:
    # 主体
    Box(outer_l, outer_w, outer_h)
    # 外角圆角
    fillet(box.edges().filter_by(Axis.Z), radius=corner_r)
    # 顶面开口抽壳
    shell(box.faces().sort_by(Axis.Z)[-1], thickness=-wall_t)

    # 四角固定柱（内部）
    inner_l = outer_l - 2 * wall_t
    inner_w = outer_w - 2 * wall_t
    boss_h  = (outer_h - wall_t) * boss_h_ratio
    boss_offsets = [
        Pos( inner_l/2 - boss_r - 2, inner_w/2 - boss_r - 2),
        Pos(-inner_l/2 + boss_r + 2, inner_w/2 - boss_r - 2),
        Pos( inner_l/2 - boss_r - 2,-inner_w/2 + boss_r + 2),
        Pos(-inner_l/2 + boss_r + 2,-inner_w/2 + boss_r + 2),
    ]
    bottom_face = box.faces().sort_by(Axis.Z)[0]
    with BuildSketch(bottom_face):
        with Locations(*boss_offsets):
            Circle(boss_r)
    extrude(amount=boss_h)

    # 固定柱中心孔（嵌件孔）
    with Locations(*[Pos(p.position.X, p.position.Y, 0) for p in boss_offsets]):
        Hole(radius=screw_r, depth=boss_h)

# ===== 验证 =====
bb = box.part.bounding_box()
print(f"外尺寸: {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm")
print(f"壁厚: {wall_t} mm，内尺寸: {outer_l-2*wall_t:.1f} x {outer_w-2*wall_t:.1f} x {outer_h-wall_t:.1f} mm")
print(f"体积: {box.part.volume:.1f} mm³")

# ===== 导出 =====
export_step(box.part, "04_enclosure.step")
