"""
安装板 / Mounting Plate
用途：通用安装支架底板，3D打印或CNC加工均可
复杂度：★☆☆☆☆（入门级）
"""
from build123d import *

# ===== 参数 =====
plate_length = 80       # 板长 mm
plate_width  = 60       # 板宽 mm
plate_height = 6        # 板厚 mm
corner_r     = 5        # 四角圆角半径 mm
hole_radius  = 2.5      # 安装孔半径（M5 通孔）
hole_x_sp    = 60       # 孔在 X 方向的间距 mm
hole_y_sp    = 40       # 孔在 Y 方向的间距 mm
hole_x_n     = 2        # X 方向孔数
hole_y_n     = 2        # Y 方向孔数

# ===== 建模 =====
with BuildPart() as plate:
    Box(plate_length, plate_width, plate_height)
    # 四角圆角（顶面边缘）
    fillet(
        plate.faces().sort_by(Axis.Z)[-1].edges(),
        radius=corner_r
    )
    # 安装孔阵列
    with GridLocations(hole_x_sp, hole_y_sp, hole_x_n, hole_y_n):
        Hole(radius=hole_radius)

# ===== 验证 =====
bb = plate.part.bounding_box()
print(f"尺寸: {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm")
print(f"体积: {plate.part.volume:.1f} mm³")

# ===== 导出 =====
export_step(plate.part, "01_mounting_plate.step")
