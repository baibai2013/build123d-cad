"""
弯管接头 / Pipe Elbow
用途：管道系统 90° 弯头，扫掠路径建模范例
复杂度：★★★★☆（sweep 路径 + 法兰端面）
"""
from build123d import *

# ===== 参数 =====
pipe_od      = 22       # 外径 mm
pipe_id      = 18       # 内径（管壁厚 2mm）mm
bend_r       = 30       # 弯曲半径（中心线半径）mm
flange_od    = 32       # 法兰外径 mm
flange_h     = 5        # 法兰厚度 mm
bolt_r       = 3        # 螺栓孔半径 mm
bolt_n       = 4        # 螺栓孔数量
bolt_pcd     = 27       # 螺栓孔分布圆半径 mm

# ===== 建模 =====
with BuildPart() as elbow:
    # 扫掠路径：在 XZ 平面内做 90° 圆弧
    with BuildLine() as path:
        RadiusArc(
            start_point=(0, 0, 0),
            end_point=(bend_r, 0, bend_r),
            radius=bend_r
        )

    # 截面：空心圆管（在路径起点的法向平面）
    start_normal = Plane((0, 0, 0), x_dir=(0, 1, 0), z_dir=(-1, 0, 0))
    with BuildSketch(start_normal):
        Circle(pipe_od / 2)
        Circle(pipe_id / 2, mode=Mode.SUBTRACT)
    sweep(path=path.wires()[0])

    # 入口法兰（底部）
    bottom_face = elbow.faces().sort_by(Axis.Z)[0]
    with BuildSketch(bottom_face):
        Circle(flange_od / 2)
        Circle(pipe_od / 2, mode=Mode.SUBTRACT)  # 法兰环形
    extrude(amount=-flange_h)
    with BuildSketch(elbow.faces().sort_by(Axis.Z)[0]):
        with PolarLocations(radius=bolt_pcd, count=bolt_n):
            Circle(bolt_r)
    extrude(amount=flange_h, mode=Mode.SUBTRACT)

# ===== 验证 =====
bb = elbow.part.bounding_box()
print(f"包围盒: {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm")
print(f"体积: {elbow.part.volume:.1f} mm³")

# ===== 导出 =====
export_step(elbow.part, "07_pipe_elbow.step")
