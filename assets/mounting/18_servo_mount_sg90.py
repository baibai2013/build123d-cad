"""
SG90 舵机安装座 / SG90 Servo Mount
用途：微型舵机固定座，适用于机械猫关节
难度：★★★

技法：Box + Shell 内腔 + 耳朵槽 + 出线口
"""
from build123d import *

# ===== SG90 舵机尺寸 =====
servo_l = 22.8            # 舵机体长
servo_w = 12.2            # 舵机体宽
servo_h = 22.7            # 舵机体高
ear_total_w = 32.2        # 含耳朵总宽
ear_h = 2.5               # 耳朵厚度
ear_z = 15.5              # 耳朵距底部
shaft_offset_y = 6.1      # 输出轴偏心距

# ===== 安装座设计参数 =====
gap = 0.3                 # FDM 装配间隙（每侧）
wall = 2.5                # 壁厚
screw_r = 1.1             # M2 自攻螺丝孔半径
cable_slot_w = 4          # 出线槽宽
cable_slot_h = 3          # 出线槽高

# ===== 计算 =====
cavity_l = servo_l + 2 * gap
cavity_w = servo_w + 2 * gap
cavity_h = servo_h + gap
ear_slot_w = ear_total_w + 2 * gap
outer_l = cavity_l + 2 * wall
outer_w = cavity_w + 2 * wall
outer_h = cavity_h + wall

# ===== 建模 =====
with BuildPart() as mount:
    # 外壳
    Box(outer_l, outer_w, outer_h)

    # 主腔体（舵机嵌入）
    top = mount.faces().sort_by(Axis.Z)[-1]
    with BuildSketch(top):
        Rectangle(cavity_l, cavity_w)
    extrude(amount=-cavity_h, mode=Mode.SUBTRACT)

    # 耳朵卡槽（顶部加宽区域）
    with BuildSketch(top):
        Rectangle(ear_slot_w, cavity_w)
    extrude(amount=-ear_h, mode=Mode.SUBTRACT)

    # 输出轴通孔（侧面）
    shaft_face = mount.faces().sort_by(Axis.Y)[-1]
    with BuildSketch(shaft_face):
        with Locations((0, outer_h / 2 - (servo_h - ear_z))):
            Circle(4)     # 输出轴通孔
    extrude(amount=-wall - 1, mode=Mode.SUBTRACT)

    # 底部出线口
    back_face = mount.faces().sort_by(Axis.X)[0]
    with BuildSketch(back_face):
        with Locations((0, -outer_h / 4)):
            Rectangle(cable_slot_w, cable_slot_h)
    extrude(amount=-wall - 1, mode=Mode.SUBTRACT)

    # 安装螺丝孔（四角）
    bottom = mount.faces().sort_by(Axis.Z)[0]
    with BuildSketch(bottom):
        margin = 3
        with Locations(
            (outer_l / 2 - margin, outer_w / 2 - margin),
            (-outer_l / 2 + margin, outer_w / 2 - margin),
            (outer_l / 2 - margin, -outer_w / 2 + margin),
            (-outer_l / 2 + margin, -outer_w / 2 + margin),
        ):
            Circle(screw_r)
    extrude(amount=wall + 2, mode=Mode.SUBTRACT)

    # 顶部边缘倒角
    top_edges = mount.faces().sort_by(Axis.Z)[-1].edges()
    chamfer(top_edges, length=0.5)

# ===== 验证 =====
bb = mount.part.bounding_box()
print(f"安装座尺寸: {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm")
print(f"舵机腔体: {cavity_l:.1f} x {cavity_w:.1f} x {cavity_h:.1f} mm")
print(f"装配间隙: {gap}mm (FDM)")

# ===== 导出 =====
export_step(mount.part, "servo_mount_sg90.step")

# ===== OCP 预览 =====
# from ocp_vscode import show
# show(mount, deviation=0.05)
