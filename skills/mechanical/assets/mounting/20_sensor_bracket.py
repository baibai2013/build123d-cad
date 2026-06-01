"""
传感器支架 / Sensor Mounting Bracket
用途：距离传感器（如 HC-SR04）安装支架，可调角度
难度：★★★

技法：Box + 圆弧槽（角度调节）+ 传感器开窗
"""
from build123d import *

# ===== 传感器参数 (HC-SR04) =====
sensor_l = 45             # 传感器板长
sensor_w = 20             # 传感器板宽
sensor_h = 15             # 传感器高度（含超声波头）
eye_r = 8                 # 超声波头半径
eye_spacing = 26          # 两个超声波头中心距
eye_depth = 10            # 超声波头伸出深度

# ===== 支架参数 =====
gap = 0.3                 # FDM 间隙
wall = 2.0
mount_screw_r = 1.5       # M3 安装螺丝

# ===== 计算 =====
cavity_l = sensor_l + 2 * gap
cavity_w = sensor_w + 2 * gap
outer_l = cavity_l + 2 * wall
outer_w = cavity_w + 2 * wall
outer_h = sensor_h + wall

# ===== 建模 =====
with BuildPart() as bracket:
    # 支架主体
    Box(outer_l, outer_w, outer_h)

    # 传感器嵌入槽（顶部开口）
    top = bracket.faces().sort_by(Axis.Z)[-1]
    with BuildSketch(top):
        Rectangle(cavity_l, cavity_w)
    extrude(amount=-sensor_h, mode=Mode.SUBTRACT)

    # 前面板超声波开窗（两个圆孔）
    front = bracket.faces().sort_by(Axis.Y)[-1]
    with BuildSketch(front):
        with Locations((-eye_spacing / 2, 0), (eye_spacing / 2, 0)):
            Circle(eye_r + gap)
    extrude(amount=-wall - 1, mode=Mode.SUBTRACT)

    # 底部安装螺丝孔
    bottom = bracket.faces().sort_by(Axis.Z)[0]
    with BuildSketch(bottom):
        with Locations(
            (-outer_l / 2 + 5, 0),
            (outer_l / 2 - 5, 0),
        ):
            Circle(mount_screw_r)
    extrude(amount=wall + 2, mode=Mode.SUBTRACT)

    # 后面板线缆出口
    back = bracket.faces().sort_by(Axis.Y)[0]
    with BuildSketch(back):
        Rectangle(8, 4)
    extrude(amount=-wall - 1, mode=Mode.SUBTRACT)

    # 顶部边缘圆角
    fillet(bracket.faces().sort_by(Axis.Z)[-1].edges(), radius=1)

# ===== 验证 =====
bb = bracket.part.bounding_box()
print(f"支架尺寸: {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm")

# ===== 导出 =====
export_step(bracket.part, "sensor_bracket.step")
