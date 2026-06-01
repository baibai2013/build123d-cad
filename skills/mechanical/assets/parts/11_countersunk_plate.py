"""
沉头孔安装板 / Countersunk Mounting Plate
用途：需要螺钉头低于表面的薄板固定件
复杂度：★★☆☆☆（沉头孔 + 埋头孔）
"""
from build123d import *

# ===== Parameters / 参数 =====
plate_l     = 100   # 板长 mm
plate_w     = 60    # 板宽 mm
plate_h     = 6     # 板厚 mm
corner_r    = 5     # 圆角半径 mm

# M4 内六角沉头螺钉孔（DIN 7991）
cbore_r       = 2.1     # M4 通孔半径
cbore_cb_r    = 4.0     # 沉头座半径（头径 7mm → 半径 3.5，留余量 4）
cbore_cb_d    = 2.5     # 沉头深度 mm（M4 沉头高 2.2mm）

# M4 十字平头螺钉 82° 锥孔
csink_r       = 2.1     # M4 通孔半径
csink_cs_r    = 4.5     # 锥面大端半径
csink_angle   = 82      # 锥角 °（标准 82°）

# 孔位布局
cbore_positions = [(30, 20), (30, -20), (-30, 20), (-30, -20)]   # 沉头孔（四角）
csink_positions = [(0, 20), (0, -20)]                             # 锥孔（中部）

# ===== Modeling / 建模 =====
with BuildPart() as plate:
    Box(plate_l, plate_w, plate_h)
    fillet(plate.edges().filter_by(Axis.Z), radius=corner_r)

    # 沉头孔（内六角圆柱头螺钉）
    with Locations(*[Pos(x, y) for x, y in cbore_positions]):
        CounterBoreHole(
            radius=cbore_r,
            counter_bore_radius=cbore_cb_r,
            counter_bore_depth=cbore_cb_d
        )

    # 埋头锥孔（十字平头螺钉）
    with Locations(*[Pos(x, y) for x, y in csink_positions]):
        CounterSinkHole(
            radius=csink_r,
            counter_sink_radius=csink_cs_r,
            counter_sink_angle=csink_angle
        )

# ===== Validation / 验证 =====
assert plate.part is not None, "part is None / part 为空"
assert plate.part.is_valid,    "BRep invalid / BRep 无效"

bb = plate.part.bounding_box()
print(f"尺寸: {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm")
print(f"体积: {plate.part.volume:.1f} mm³")

# ===== Export / 导出 =====
export_step(plate.part, "11_countersunk_plate.step")
