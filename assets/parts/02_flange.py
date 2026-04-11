"""
法兰盘 / Flange
用途：管道法兰、轴端法兰、电机安装法兰
复杂度：★★☆☆☆
"""
from build123d import *

# ===== 参数 =====
flange_r     = 40       # 法兰外径半径 mm
flange_h     = 10       # 法兰厚度 mm
center_r     = 15       # 中心通孔半径 mm
pcd_r        = 28       # 螺栓孔分布圆半径（PCD/2）mm
bolt_r       = 4        # 螺栓孔半径（M8 通孔）mm
bolt_n       = 6        # 螺栓孔数量
boss_r       = 20       # 中心凸台半径 mm
boss_h       = 8        # 中心凸台高度 mm
fillet_r     = 1.5      # 边缘圆角 mm

# ===== 建模 =====
with BuildPart() as flange:
    # 主体圆盘
    Cylinder(radius=flange_r, height=flange_h)
    # 中心凸台
    with BuildSketch(flange.faces().sort_by(Axis.Z)[-1]):
        Circle(boss_r)
    extrude(amount=boss_h)
    # 中心通孔
    Hole(radius=center_r)
    # 均布螺栓孔
    with PolarLocations(radius=pcd_r, count=bolt_n):
        Hole(radius=bolt_r)
    # 顶面圆弧边圆角
    fillet(
        flange.edges().filter_by(GeomType.CIRCLE).sort_by(SortBy.RADIUS)[-1],
        radius=fillet_r
    )

# ===== 验证 =====
bb = flange.part.bounding_box()
print(f"尺寸: Ø{bb.size.X:.1f} x H{bb.size.Z:.1f} mm")
print(f"体积: {flange.part.volume:.1f} mm³")

# ===== 导出 =====
export_step(flange.part, "02_flange.step")
