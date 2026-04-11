"""
散热片 / Heat Sink
用途：功率器件散热，阵列翅片建模
复杂度：★★★☆☆（矩形阵列 + 拉伸切除）
"""
from build123d import *

# ===== 参数 =====
base_l      = 80    # 底板长度 mm
base_w      = 60    # 底板宽度 mm
base_h      = 4     # 底板厚度 mm
fin_h       = 25    # 翅片高度 mm
fin_t       = 2     # 翅片厚度 mm
fin_gap     = 4     # 翅片间距（净空）mm
fin_count   = 8     # 翅片数量
mount_r     = 2.5   # 安装孔半径（M5）mm
mount_inset = 6     # 安装孔距角距离 mm
chamfer_l   = 0.8   # 翅片顶端倒角 mm

# ===== 建模 =====
with BuildPart() as sink:
    # 底板
    Box(base_l, base_w, base_h)

    # 翅片（在底板顶面上拉伸矩形阵列）
    top_face = sink.faces().sort_by(Axis.Z)[-1]
    fin_pitch = fin_t + fin_gap
    total_fin_w = fin_count * fin_t + (fin_count - 1) * fin_gap
    fin_x_start = -total_fin_w / 2 + fin_t / 2

    fin_positions = [
        Pos(fin_x_start + i * fin_pitch, 0)
        for i in range(fin_count)
    ]

    with BuildSketch(top_face):
        with Locations(*fin_positions):
            Rectangle(fin_t, base_w)
    extrude(amount=fin_h)

    # 翅片顶端倒角（改善散热和外观）
    top_fin_edges = (
        sink.faces().sort_by(Axis.Z)[-1].edges()
        .filter_by(Axis.Y)
    )
    chamfer(top_fin_edges, length=chamfer_l)

    # 四角安装孔
    mount_offsets = [
        Pos( base_l/2 - mount_inset,  base_w/2 - mount_inset),
        Pos(-base_l/2 + mount_inset,  base_w/2 - mount_inset),
        Pos( base_l/2 - mount_inset, -base_w/2 + mount_inset),
        Pos(-base_l/2 + mount_inset, -base_w/2 + mount_inset),
    ]
    bottom_face = sink.faces().sort_by(Axis.Z)[0]
    with BuildSketch(bottom_face):
        with Locations(*mount_offsets):
            Circle(mount_r)
    extrude(amount=base_h, mode=Mode.SUBTRACT)

# ===== 验证 =====
bb = sink.part.bounding_box()
print(f"尺寸: {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm")
print(f"翅片数: {fin_count}，间距: {fin_gap}mm")
print(f"体积: {sink.part.volume:.1f} mm³")

# ===== 导出 =====
export_step(sink.part, "10_heat_sink.step")
