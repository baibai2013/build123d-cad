"""
PCB 壳体 / PCB Enclosure with Standoffs
用途：电子项目壳体，含 PCB 固定柱和接插件开口
难度：★★★

技法：Shell + 固定柱 + USB-C 开口 + 通风口
"""
from build123d import *

# ===== PCB 参数 =====
pcb_l, pcb_w, pcb_h = 50, 30, 1.6
comp_h = 10                              # 元器件最高高度
hole_positions = [                        # PCB 安装孔 (x, y)
    (-20, -10), (20, -10),
    (-20, 10),  (20, 10),
]
standoff_r = 2.5                          # 固定柱外径
screw_r = 1.25                            # M2.5 螺丝孔

# ===== 壳体参数 =====
clearance = 1.5                           # PCB 到壁间隙
wall = 2.0
standoff_h = 5                            # 固定柱高度
lid_h = 3                                 # 盖板高度

# ===== 计算 =====
inner_l = pcb_l + 2 * clearance
inner_w = pcb_w + 2 * clearance
inner_h = standoff_h + pcb_h + comp_h + clearance
outer_l = inner_l + 2 * wall
outer_w = inner_w + 2 * wall
outer_h = inner_h + wall

# ===== 盒体 =====
with BuildPart() as body:
    Box(outer_l, outer_w, outer_h)
    # 抽壳（顶面开口）
    top = body.faces().sort_by(Axis.Z)[-1]
    shell(top, thickness=-wall)

    # PCB 固定柱
    bottom_inner = body.faces().sort_by(Axis.Z)[0]
    with BuildSketch(bottom_inner):
        with Locations(*hole_positions):
            Circle(standoff_r)
    extrude(amount=standoff_h)

    # 固定柱螺纹孔
    with Locations(*[(x, y, 0) for x, y in hole_positions]):
        Hole(radius=screw_r, depth=standoff_h + wall)

    # USB-C 开口（前面板）
    front = body.faces().sort_by(Axis.X)[-1]
    usb_z = wall + standoff_h + pcb_h / 2      # USB 口中心高度
    with BuildSketch(front):
        with Locations((0, usb_z - outer_h / 2)):
            Rectangle(10, 4)                     # USB-C: 9.5×3.5 + 间隙
    extrude(amount=-wall - 1, mode=Mode.SUBTRACT)

    # 底部通风口
    bottom = body.faces().sort_by(Axis.Z)[0]
    with BuildSketch(bottom):
        with GridLocations(5, 0, 6, 1):
            Rectangle(1.5, inner_w * 0.6)
    extrude(amount=wall + 1, mode=Mode.SUBTRACT)

# ===== 盖板 =====
with BuildPart() as lid:
    # 盖板主体
    Box(outer_l, outer_w, lid_h)
    # 嵌入唇边
    lip_gap = 0.3                # FDM 间隙
    with BuildSketch(lid.faces().sort_by(Axis.Z)[0]):
        Rectangle(inner_l - lip_gap * 2, inner_w - lip_gap * 2)
    extrude(amount=-2)           # 唇边深度 2mm

# ===== 验证 =====
bb_body = body.part.bounding_box()
bb_lid = lid.part.bounding_box()
print(f"盒体: {bb_body.size.X:.1f} x {bb_body.size.Y:.1f} x {bb_body.size.Z:.1f} mm")
print(f"盖板: {bb_lid.size.X:.1f} x {bb_lid.size.Y:.1f} x {bb_lid.size.Z:.1f} mm")
print(f"PCB 空间: {inner_l:.1f} x {inner_w:.1f} x {inner_h:.1f} mm")

# ===== 导出 =====
export_step(body.part, "pcb_enclosure_body.step")
export_step(lid.part, "pcb_enclosure_lid.step")

# ===== OCP 预览 =====
# from ocp_vscode import show
# assembled_lid = Pos(0, 0, outer_h / 2 + lid_h / 2) * lid.part
# show(body.part, assembled_lid,
#      names=["body", "lid"],
#      colors=["steelblue", "orange"])
