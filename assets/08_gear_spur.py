"""
直齿圆柱齿轮 / Spur Gear
用途：传动机构，参数化齿轮生成（简化渐开线）
复杂度：★★★★★（数学参数化建模）
参考：ISO 1328 标准，标准模数齿轮

注意：此版本使用"近似渐开线"（梯形逼近）。
      工业级精确渐开线需配合 cadquery-gear 或 build123d-contrib 插件。

⚠️ 已知渲染问题（2026-04）：
   此文件将全部轮廓（~300点非凸多边形）一次性拉伸，
   OCP CAD Viewer（Three.js）无法三角化顶底面，输出 "face ignored"，
   导致 3D 视图中顶底面透明。STEP 几何本身完全正确。
   ✅ 修复版请用 08_gear_spur_v2.py（根圆柱 + 逐齿 Algebra Mode 融合）
"""
from build123d import *
import math

# ===== 参数 =====
module      = 2        # 模数 m
teeth       = 20       # 齿数 z
face_width  = 12       # 齿宽 mm
shaft_r     = 4        # 中心轴孔半径 mm
keyway_w    = 2.0      # 键槽宽 mm（0 = 无键槽）
pressure_a  = 20       # 压力角 °（标准 20°）

# ===== 计算基本参数 =====
pitch_r     = module * teeth / 2              # 分度圆半径
addendum_r  = pitch_r + module                # 齿顶圆半径
dedendum_r  = pitch_r - 1.25 * module        # 齿根圆半径
base_r      = pitch_r * math.cos(math.radians(pressure_a))  # 基圆半径

print(f"分度圆直径: {2*pitch_r:.1f}mm")
print(f"齿顶圆直径: {2*addendum_r:.1f}mm")
print(f"齿根圆直径: {2*dedendum_r:.1f}mm")

# ===== 建模（近似渐开线齿轮）=====
def tooth_profile_pts(pitch_r, addendum_r, dedendum_r, base_r, n_teeth, tooth_idx):
    """生成单个轮齿的近似轮廓点（以分度圆为基准）"""
    pitch_angle   = 2 * math.pi / n_teeth
    half_tooth_a  = math.pi / (2 * n_teeth)  # 分度圆上半齿厚角

    pts = []
    # 左齿根 → 左渐开线 → 齿顶 → 右渐开线 → 右齿根
    steps = 8
    for i in range(steps + 1):
        t = i / steps
        # 渐开线参数（从基圆展开）
        inv_angle = math.sqrt(max(0, (addendum_r / base_r) ** 2 - 1)) * t
        r = base_r * math.sqrt(1 + inv_angle ** 2)
        r = min(r, addendum_r)
        theta = pitch_angle * tooth_idx + half_tooth_a - inv_angle + math.atan(inv_angle)
        pts.append((r * math.cos(theta), r * math.sin(theta)))

    # 右侧（镜像）
    for i in range(steps, -1, -1):
        t = i / steps
        inv_angle = math.sqrt(max(0, (addendum_r / base_r) ** 2 - 1)) * t
        r = base_r * math.sqrt(1 + inv_angle ** 2)
        r = min(r, addendum_r)
        theta = pitch_angle * tooth_idx - half_tooth_a + inv_angle - math.atan(inv_angle)
        pts.append((r * math.cos(theta), r * math.sin(theta)))

    return pts

# 合并所有轮齿轮廓点
all_pts = []
for i in range(teeth):
    t_pts = tooth_profile_pts(pitch_r, addendum_r, dedendum_r, base_r, teeth, i)
    # 添加齿根过渡圆弧近似点
    pitch_angle = 2 * math.pi / teeth
    r_root = dedendum_r
    a_start = pitch_angle * i - math.pi / teeth
    all_pts.extend(t_pts)
    # 齿槽底部
    a_root = pitch_angle * i + math.pi / teeth
    all_pts.append((r_root * math.cos(a_root), r_root * math.sin(a_root)))

with BuildPart() as gear:
    with BuildSketch(Plane.XY):
        with BuildLine():
            Polyline(*all_pts, close=True)
        make_face()
    extrude(amount=face_width)

    # 中心轴孔
    Hole(radius=shaft_r)

    # 键槽
    if keyway_w > 0:
        keyway_depth = shaft_r + 1.2  # 键槽深度（轴孔半径 + 键高）
        top_face = gear.faces().sort_by(Axis.Z)[-1]
        with BuildSketch(top_face):
            with Locations(Pos(0, shaft_r + keyway_w / 4)):
                Rectangle(keyway_w, keyway_w * 1.2)
        extrude(amount=-face_width, mode=Mode.SUBTRACT)

    # 两端面倒角
    top_edges = gear.faces().sort_by(Axis.Z)[-1].edges().filter_by(GeomType.CIRCLE)
    bot_edges = gear.faces().sort_by(Axis.Z)[0].edges().filter_by(GeomType.CIRCLE)
    chamfer(list(top_edges) + list(bot_edges), length=0.5)

# ===== 导出 =====
export_step(gear.part, "08_gear_spur.step")
