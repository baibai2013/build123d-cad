"""
阶梯轴 / Stepped Shaft
用途：传动轴、电机轴，旋转体建模范例
复杂度：★★★☆☆（旋转体 + 键槽）
"""
from build123d import *

# ===== 参数 =====
# 各段 [直径(半径), 长度]
segments = [
    (6,  15),   # 端部小轴（轴承配合）
    (8,  10),   # 过渡段
    (12, 40),   # 主轴段
    (8,  10),   # 过渡段
    (6,  15),   # 另一端小轴
]
keyway_w    = 3.0   # 键槽宽度 mm
keyway_d    = 1.8   # 键槽深度 mm
keyway_l    = 25    # 键槽长度 mm（位于主轴段中央）
chamfer_l   = 0.5   # 端部倒角 mm

# ===== 建模（旋转体方式）=====
# 计算各段累计 Z 位置
z_positions = []
z = 0
for r, l in segments:
    z_positions.append((r, z, z + l))
    z += l
total_l = z

with BuildPart() as shaft:
    # 用旋转体生成阶梯轴
    with BuildSketch(Plane.XZ):
        pts = [(0, 0)]
        z_cur = 0
        for r, l in segments:
            pts.append((r / 2, z_cur))        # 台阶起点
            pts.append((r / 2, z_cur + l))    # 台阶终点
            z_cur += l
        pts.append((0, z_cur))
        with BuildLine():
            Polyline(*pts)
            Line(pts[-1], pts[0])
        make_face()
    revolve(axis=Axis.Z)

    # 两端倒角
    bottom_edge = shaft.edges().sort_by(Axis.Z)[0]
    top_edge    = shaft.edges().sort_by(Axis.Z)[-1]
    chamfer([bottom_edge, top_edge], length=chamfer_l)

    # 键槽（在主轴段顶部切除）
    main_r = segments[2][0] / 2
    main_z_start = sum(s[1] for s in segments[:2])
    main_z_center = main_z_start + segments[2][1] / 2
    keyway_plane = Plane(
        origin=(0, main_r, main_z_center),
        x_dir=(1, 0, 0),
        z_dir=(0, 0, 1)
    )
    with BuildSketch(keyway_plane):
        Rectangle(keyway_w, keyway_l)
    extrude(amount=-(keyway_d + main_r), mode=Mode.SUBTRACT)

# ===== 验证 =====
bb = shaft.part.bounding_box()
print(f"轴总长: {bb.size.Z:.1f} mm，最大直径: {bb.size.X:.1f} mm")
print(f"体积: {shaft.part.volume:.1f} mm³")

# ===== 导出 =====
export_step(shaft.part, "05_shaft.step")
