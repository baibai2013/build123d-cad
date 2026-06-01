"""
直齿圆柱齿轮 / Spur Gear
建模策略：根圆柱 + 逐齿 Algebra Mode 融合
"""
from build123d import *  # noqa: F403
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace  # type: ignore[import-untyped]
from OCP.gp import gp_Pln, gp_Pnt, gp_Dir  # type: ignore[import-untyped]
import math

# ===== 参数 =====
module      = 2        # 模数 m
teeth       = 20       # 齿数 z
face_width  = 12       # 齿宽 mm
shaft_r     = 4        # 中心轴孔半径 mm
keyway_w    = 2.0      # 键槽宽 mm（0 = 无）
pressure_a  = 20       # 压力角 °

# ===== 计算 =====
pitch_r    = module * teeth / 2
addendum_r = pitch_r + module
root_r     = pitch_r - 1.25 * module
base_r     = pitch_r * math.cos(math.radians(pressure_a))

pitch_angle = 2 * math.pi / teeth
half_t      = math.pi / (2 * teeth)

print(f"分度圆: {2*pitch_r:.1f}mm  齿顶: {2*addendum_r:.1f}mm  齿根: {2*root_r:.1f}mm")

XY_PLANE = gp_Pln(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1))

def make_face_from_pts(pts_2d):
    wire = Wire.make_polygon([(x, y, 0) for x, y in pts_2d], close=True)
    return Face(BRepBuilderAPI_MakeFace(XY_PLANE, wire.wrapped, True).Face())

def tooth_pts(tooth_idx, steps=8):
    a_i = pitch_angle * tooth_idx
    inv_max = math.sqrt(max(0, (addendum_r / base_r) ** 2 - 1))

    left = []
    for s in range(steps + 1):
        t  = s / steps
        ia = inv_max * t
        r  = base_r * math.sqrt(1 + ia ** 2)
        if r < root_r:
            continue
        r  = min(r, addendum_r)
        th = a_i + half_t - ia + math.atan(ia)
        left.append((r * math.cos(th), r * math.sin(th)))

    right = []
    for s in range(steps, -1, -1):
        t  = s / steps
        ia = inv_max * t
        r  = base_r * math.sqrt(1 + ia ** 2)
        if r < root_r:
            continue
        r  = min(r, addendum_r)
        th = a_i - half_t + ia - math.atan(ia)
        right.append((r * math.cos(th), r * math.sin(th)))

    if not left or not right:
        return None

    th_r = math.atan2(right[-1][1], right[-1][0])
    th_l = math.atan2(left[0][1],  left[0][0])
    if th_l < th_r:
        th_l += 2 * math.pi
    arc_pts = [(root_r * math.cos(th_r + (th_l - th_r) * k / 4),
                root_r * math.sin(th_r + (th_l - th_r) * k / 4))
               for k in range(1, 4)]

    return left + right + arc_pts

# ===== 建模 =====
gear = Cylinder(radius=root_r, height=face_width)

fused = 0
for i in range(teeth):
    pts = tooth_pts(i)
    if pts is None:
        continue
    f = make_face_from_pts(pts)
    with BuildPart() as tooth:
        with BuildSketch(Plane.XY.offset(-face_width / 2)):
            add(f)
        extrude(amount=face_width)
    gear = gear + tooth.part
    fused += 1

print(f"融合齿数: {fused}")

# 中心轴孔
gear = gear - Cylinder(radius=shaft_r, height=face_width)

# 键槽
if keyway_w > 0:
    slot_depth = shaft_r + keyway_w * 1.2
    slot = Box(keyway_w, slot_depth, face_width)
    slot = slot.moved(Location((0, slot_depth / 2, 0)))
    gear = gear - slot

# ===== 验证 =====
bb = gear.bounding_box()
print(f"尺寸: {bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f} mm")
print(f"volume: {gear.volume:.2f} mm3")

# ===== OCP 预览 =====
from ocp_vscode import show
show(gear, names=["spur_gear"])

# ===== 导出 =====
export_step(gear, "output/gear_spur.step")
print("Done: output/gear_spur.step")
