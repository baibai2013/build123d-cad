"""
L 形支架 / L-Bracket
用途：结构支撑、角支架、电子设备安装
复杂度：★★☆☆☆
"""
from build123d import *

# ===== 参数 =====
base_l       = 60       # 底板长度 mm
base_w       = 40       # 底板宽度 mm
rib_h        = 50       # 竖板高度 mm
thickness    = 5        # 板厚 mm
hole_r       = 2.5      # 安装孔半径 mm（M5）
fillet_r     = 3        # 外角圆角 mm
inner_fillet = 5        # 内角圆角（根部加强）mm
base_holes   = [        # 底板安装孔位置 [(x, y), ...]
    (-20, -10), (20, -10),
    (-20,  10), (20,  10)
]
rib_holes    = [        # 竖板安装孔位置（X, Z offset from rib center）
    (-15, 15), (15, 15),
    (-15, 35), (15, 35)
]

# ===== 建模 =====
with BuildPart() as bracket:
    # 底板
    Box(base_l, base_w, thickness)

    # 竖板：从底板后边缘向上拉伸
    with BuildSketch(bracket.faces().sort_by(Axis.Z)[-1]):
        with Locations(Pos(0, base_w / 2 - thickness / 2)):
            Rectangle(base_l, thickness)
    extrude(amount=rib_h)

    # 内角加强圆角（底板与竖板交界）
    inner_edges = (
        bracket.edges()
        .filter_by(Axis.X)
        .filter_by(lambda e: abs(e.center().Z - thickness) < 0.1)
    )
    fillet(inner_edges, radius=inner_fillet)

    # 外部竖边圆角
    fillet(bracket.edges().filter_by(Axis.Z), radius=fillet_r)

    # 底板安装孔
    with Locations(*[Pos(x, y, 0) for x, y in base_holes]):
        Hole(radius=hole_r)

    # 竖板安装孔（在竖板前面）
    rib_front = bracket.faces().filter_by(Axis.Y).sort_by(Axis.Y)[0]
    with BuildSketch(rib_front):
        with Locations(*[Pos(x, z) for x, z in rib_holes]):
            Circle(hole_r)
    extrude(amount=-thickness, mode=Mode.SUBTRACT)

# ===== 验证 =====
bb = bracket.part.bounding_box()
print(f"尺寸: {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm")
print(f"体积: {bracket.part.volume:.1f} mm³")

# ===== 导出 =====
export_step(bracket.part, "03_l_bracket.step")
