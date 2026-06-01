"""
有机曲面外壳 — 多截面放样 / Organic Shell via Multi-Section Loft
用途：机械猫身体外壳等有机造型的基础范例
难度：★★★★

技法：多截面 Loft + Shell 抽壳 + 斑马纹检查
"""
from build123d import *

# ===== 参数 =====
body_length = 120         # 总长 mm
body_width = 60           # 最宽处 mm
body_height = 45          # 最高处 mm
wall_t = 2.5              # 壁厚 mm
n_sections = 5            # 截面数量

# ===== 截面定义（从后到前） =====
# 每个截面：(z_offset, x_radius, y_radius)
sections = [
    (0,                  15, 18),    # 尾部：较小的椭圆
    (body_length * 0.25, 28, 22),    # 后腰：逐渐变宽
    (body_length * 0.50, 30, 22),    # 中部：最宽
    (body_length * 0.75, 25, 20),    # 前胸：收窄
    (body_length,        18, 15),    # 头部连接处：较小
]

# ===== 建模 =====
with BuildPart() as shell:
    # 多截面放样
    for i, (z, rx, ry) in enumerate(sections):
        with BuildSketch(Plane.XY.offset(z)):
            Ellipse(rx, ry)
    loft()

    # 抽壳（底面开口）
    bottom = shell.faces().sort_by(Axis.Z)[0]
    shell_op = shell(bottom, thickness=-wall_t)

# ===== 验证 =====
bb = shell.part.bounding_box()
print(f"尺寸: {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm")
print(f"体积: {shell.part.volume:.1f} mm³")

# ===== 导出 =====
export_step(shell.part, "organic_shell.step")

# ===== OCP 预览（含斑马纹曲面检查） =====
# from ocp_vscode import show
# show(shell, zebra_count=12, zebra_direction=0)
