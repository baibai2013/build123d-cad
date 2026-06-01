"""
05-stepped-shaft — Stepped Shaft / 阶梯轴
Tests / 测试:
  BuildSketch(Plane.XZ) + revolve  — multi-step profile rotation / 多段阶梯轮廓旋转体
  Mode.SUBTRACT extrude            — keyway slot cut / 键槽切割
  chamfer                          — end chamfers / 两端倒角

Design intent (Dave Cowden style) / 设计意图:
  Draw half-profile on XZ plane -> revolve 360° -> cut axial keyway from top -> chamfer both ends
  在 XZ 平面画半截面轮廓 -> 旋转 360° -> 从顶面沿轴向切键槽 -> 两端倒角
"""

from build123d import *
import os, math as _math

# ===== Parameters / 参数 =====
# Shaft segments (from one end to other) / 轴段（从一端到另一端）
# Segment: (radius mm, length mm)
segments = [
    (6,  15),   # end journal / 端轴颈    φ12 x 15mm
    (8,  25),   # mid journal / 中间轴颈  φ16 x 25mm
    (10, 40),   # main body   / 主轴段    φ20 x 40mm
    (8,  25),   # mid journal / 中间轴颈  φ16 x 25mm
    (6,  15),   # end journal / 端轴颈    φ12 x 15mm
]
total_length = sum(s[1] for s in segments)  # 120 mm

# Derive main-body index and Z-center (works for asymmetric shafts too)
# 推算主轴段索引和 Z 中心（对非对称轴也适用）
main_idx      = max(range(len(segments)), key=lambda i: segments[i][0])
main_r        = segments[main_idx][0]                              # 10 mm
main_body_len = segments[main_idx][1]                              # 40 mm
z_main_start  = -total_length / 2 + sum(s[1] for s in segments[:main_idx])
z_main_center = z_main_start + main_body_len / 2                   # 0 mm (symmetric)

# Keyway on main body / 主轴段键槽
key_width  = 6                        # keyway width mm / 键槽宽度 mm
key_depth  = 3                        # keyway depth mm / 键槽深度 mm
key_length = main_body_len * 0.75     # 75% of main body length / 主轴段长度的 75%  → 30 mm
key_angle  = 0                        # keyway angular position, degrees around shaft Z axis
                                      # 键槽角度，绕轴 Z 轴旋转（0=顶面 +Y, 90=右侧 +X, 180=底面 -Y）

chamfer_len = 0.5   # end chamfer length mm / 端面倒角长度 mm

output_dir = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(output_dir, exist_ok=True)
step_path  = os.path.join(output_dir, "stepped_shaft.step")

# ===== Modeling / 建模 =====
with BuildPart() as shaft:

    # Step 1: half-profile polyline on XZ plane, revolve around Z axis
    # 步骤1：XZ 平面半截面折线，绕 Z 轴旋转
    with BuildSketch(Plane.XZ):
        pts = []
        z = -total_length / 2          # start at left end / 从左端开始
        pts.append((0, z))             # left end center / 左端中心
        for r, l in segments:
            pts.append((r, z))
            z += l
            pts.append((r, z))
        pts.append((0, z))             # right end center / 右端中心
        with BuildLine():
            Polyline(*pts)
        make_face()
    revolve(axis=Axis.Z)

    # Step 2: axial keyway at key_angle around shaft Z axis
    # 步骤2：绕轴 Z 轴旋转 key_angle 角度的轴向键槽
    #
    # Plane is built analytically so key_angle drives the cut position:
    #   origin  = (r·sin θ, r·cos θ, 0)   — point on shaft surface at angle θ
    #   x_dir   = (cos θ, −sin θ, 0)       — tangential direction (keyway width)
    #   z_dir   = (0, 0, 1)                — axial direction (keyway length)
    #   extrude = −key_depth (inward along plane normal / 沿法向向内切)
    # 平面解析构造，key_angle 驱动键槽方位：
    #   原点 = 轴表面对应角度处，X 方向 = 切向（槽宽），Z 方向 = 轴向（槽长）
    # Plane geometry derived from Plane.XZ.offset(r) at θ=0:
    #   origin = (r·sin θ, −r·cos θ, 0)   — shaft surface at angle θ
    #   x_dir  = (cos θ,   sin θ,    0)   — tangential (keyway width direction)
    #   z_dir  = (sin θ,  −cos θ,    0)   — outward normal (= z_dir of Plane at θ=0)
    #   y_dir  = (0, 0, −1) [implied]     — axial but flipped; Rectangle height goes in −Z
    # extrude(−depth) cuts in the inward radial direction / extrude(-depth) 沿径向向内切
    #
    # 平面几何由 Plane.XZ.offset(r) 在 θ=0 时推导：
    #   origin = (r·sin θ, −r·cos θ, 0)  法向 = 径向外向，extrude(-depth) 沿径向向内
    _a = _math.radians(key_angle)
    keyway_plane = Plane(
        origin = Vector( main_r * _math.sin(_a), -main_r * _math.cos(_a), 0),
        x_dir  = Vector( _math.cos(_a),           _math.sin(_a),           0),
        z_dir  = Vector( _math.sin(_a),           -_math.cos(_a),          0),  # outward normal
    )
    with BuildSketch(keyway_plane):
        with Locations((0, -z_main_center)):  # y_dir=-Z so negate; centers on main body / y_dir=-Z 取负，对中主轴段
            Rectangle(key_width, key_length)
    extrude(amount=-key_depth, mode=Mode.SUBTRACT)   # cut inward / 向内切入

    # Step 3: chamfer both end faces / 步骤3：两端倒角
    end_edges = shaft.edges().filter_by(GeomType.CIRCLE).sort_by(Axis.Z)
    chamfer(end_edges[0],  length=chamfer_len)   # left end / 左端
    chamfer(end_edges[-1], length=chamfer_len)   # right end / 右端

# ===== Validation Layer 1 + 2 / 验证 =====
assert shaft.part is not None, "part is None / part 为空"
assert shaft.part.is_valid,    "BRep invalid / BRep 无效"

vol = shaft.part.volume
bb  = shaft.part.bounding_box()
print(f"Dimensions / 尺寸: {bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f} mm")
print(f"Volume / 体积: {vol:.2f} mm³")

assert abs(bb.size.Z - total_length) < 1.0, \
    f"length deviation / 总长偏差: {bb.size.Z:.2f} vs {total_length}"
assert abs(bb.size.X - main_r * 2) < 1.0, \
    f"max diameter deviation / 最大径偏差: {bb.size.X:.2f} vs {main_r*2}"

full_vol = _math.pi * main_r**2 * total_length
assert 0 < vol < full_vol, f"volume out of range / 体积超范围: {vol:.2f}"
assert len(shaft.part.solids()) == 1, "expected exactly one solid / 应只有一个 solid"

print("✅ Layer 1+2 passed / 通过")

# ===== Validation Layer 3: STEP re-import / STEP 重导入 =====
export_step(shaft.part, step_path)
reimported = import_step(step_path)
vol_diff = abs(reimported.volume - vol) / vol
print(f"STEP re-import volume deviation / 重导入体积偏差: {vol_diff:.6%}")
assert vol_diff < 0.001, f"STEP precision loss / 精度损失: {vol_diff:.4%}"
print("✅ Layer 3 passed / 通过")

# ===== OCP preview (three-view screenshots) / OCP 预览（三视角截图）=====
try:
    from ocp_vscode import show, set_port, Camera, save_screenshot
    from ocp_vscode.comms import port_check
    from ocp_vscode.state import get_ports
    import time

    active_port = next((int(p) for p in get_ports() if port_check(int(p))), None)
    if active_port:
        set_port(active_port)
        for label, cam in [("ISO", Camera.ISO), ("TOP", Camera.TOP), ("FRONT", Camera.FRONT)]:
            show(shaft.part, names=["stepped_shaft"], reset_camera=cam)
            time.sleep(0.8)
            save_screenshot(os.path.join(output_dir, f"stepped_shaft_{label}.png"))
            print(f"Screenshot saved / 截图已保存: stepped_shaft_{label}.png")
        print(f"OCP Viewer: preview opened on port {active_port} / 已在端口 {active_port} 打开预览 ✓")
    else:
        print("OCP Viewer: no running Viewer detected / 未检测到运行中的 Viewer")
except Exception as e:
    print(f"OCP preview skipped / 预览跳过: {e}")

print("\n✅ 05-stepped-shaft all tests passed / 全部测试通过")
