"""
06-pipe-elbow — Pipe Elbow / 弯管接头
Tests / 测试:
  Edge.make_circle arc path     — 90° sweep path / 90° 弯管路径
  hollow section sweep          — solid outer + subtract inner / 空心截面扫掠
  Plane from path tangent       — Plane(path @ t, z_dir=path % t) / 路径切线构造平面
  connection hubs at both ends  — larger OD collar for pipe joining / 两端连接口（大径管箍）

Design intent (Dave Cowden style) / 设计意图:
  Define 90° arc path -> sweep solid circle -> subtract smaller circle (hollow) ->
  add connection hub collars at both ends for real-world pipe joining
  定义 90° 弧线路径 -> 扫掠实心圆 -> 减去内圆（空心管壁）->
  两端各加一段大径连接口（用于与直管对接）
"""

from build123d import *
import os, math

# ===== Parameters / 参数 =====
bend_r     = 40    # bend centerline radius mm / 弯曲中心线半径 mm
bend_angle = 90    # bend angle degrees / 弯管角度 °

outer_r    = 15    # pipe outer radius mm / 管道外径半径 mm
wall_t     = 2     # wall thickness mm / 壁厚 mm
inner_r    = outer_r - wall_t   # pipe inner radius mm / 管道内径半径 mm  = 13 mm

hub_extra  = 3     # hub OD extra vs pipe OD mm / 连接口外径相比管外径的增量 mm
hub_r      = outer_r + hub_extra  # connection hub outer radius mm / 连接口外径 mm  = 18 mm
hub_len    = 8     # hub length mm / 连接口长度 mm

output_dir = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(output_dir, exist_ok=True)
step_path  = os.path.join(output_dir, "pipe_elbow.step")

# ===== Modeling / 建模 =====

# Step 1: 90° arc path in the XZ plane, centerline radius = bend_r
# 步骤1：XZ 平面内 90° 弧线路径，中心线半径 = bend_r
# Arc center at origin, from (bend_r, 0, 0) sweeping toward (0, 0, bend_r)
# 弧心在原点，从 (bend_r, 0, 0) 向 (0, 0, bend_r) 方向扫过
path = Edge.make_circle(
    radius=bend_r,
    plane=Plane.XZ,          # arc lies in the XZ plane / 弧线在 XZ 平面内
    start_angle=0,
    end_angle=bend_angle,
)

# Step 2: sweep cross-section — solid outer tube
# 步骤2：扫掠截面 — 实心外管
# Plane at path start: origin = path @ 0 (point), z_dir = path % 0 (tangent)
# 路径起始平面：原点 = 路径起点，法向 = 路径起点切线方向
start_plane = Plane(origin=path @ 0, z_dir=path % 0)

with BuildPart() as elbow:
    with BuildSketch(start_plane):
        Circle(outer_r)
    sweep(path=path)

    # Step 3: subtract inner bore to create hollow pipe wall
    # 步骤3：减去内孔，得到空心管壁
    with BuildSketch(start_plane):
        Circle(inner_r)
    sweep(path=path, mode=Mode.SUBTRACT)

    # Step 4: connection hub at start end — larger OD collar for pipe joining
    # 步骤4：起始端连接口 — 大径管箍，用于与直管对接
    # start_plane normal = tangent INTO elbow, so extrude(-hub_len) goes outward
    # start_plane 法向 = 指向弯管内侧的切线方向，所以 extrude(-hub_len) 向外延伸
    with BuildSketch(start_plane):
        Circle(hub_r)
        Circle(inner_r, mode=Mode.SUBTRACT)
    extrude(amount=-hub_len)

    # Step 5: connection hub at end — path @ 1 = parametric end point of arc
    # 步骤5：末端连接口 — path @ 1 = 弧线参数化终点（t=1 对应 90° 末端）
    end_plane = Plane(origin=path @ 1, z_dir=path % 1)
    with BuildSketch(end_plane):
        Circle(hub_r)
        Circle(inner_r, mode=Mode.SUBTRACT)
    extrude(amount=hub_len)

# ===== Validation Layer 1 + 2 / 验证 =====
assert elbow.part is not None, "part is None / part 为空"
assert elbow.part.is_valid,    "BRep invalid / BRep 无效"

vol = elbow.part.volume
bb  = elbow.part.bounding_box()
print(f"Bounding box / 包围盒: {bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f} mm")
print(f"Volume / 体积: {vol:.2f} mm³")

# Bounding box: hubs extend beyond the arc endpoints, so span > bend_r + outer_r
# 包围盒：连接口向外延伸，X/Z 跨度超过 bend_r + outer_r
expected_span = bend_r + hub_r   # 58 mm with hubs / 含连接口的预期跨度
assert bb.size.X > bend_r,    f"X span too small / X 跨度过小: {bb.size.X:.2f}"
assert bb.size.Z > bend_r,    f"Z span too small / Z 跨度过小: {bb.size.Z:.2f}"
assert bb.size.X < expected_span + 10, f"X span too large / X 跨度过大: {bb.size.X:.2f}"

# Volume: hollow annular section swept along 90° arc + 2 connection hubs
# 体积：空心圆环截面沿 90° 弧线扫掠 + 两端连接口材料
annular_area = math.pi * (outer_r**2 - inner_r**2)    # pipe wall cross-section / 管壁截面面积
arc_len      = 2 * math.pi * bend_r * (bend_angle / 360)  # arc length / 弧长
hub_area     = math.pi * (hub_r**2 - inner_r**2)      # hub cross-section / 连接口截面面积
approx_vol   = annular_area * arc_len + 2 * hub_area * hub_len
# Allow ±15% tolerance for bend geometry effects / 允许 ±15% 宽容度（弯管几何效应）
assert approx_vol * 0.85 < vol < approx_vol * 1.15, \
    f"volume out of range / 体积超范围: {vol:.2f}, expected ~{approx_vol:.2f}"

# Exactly one solid / 只有一个 solid
assert len(elbow.part.solids()) == 1, "expected exactly one solid / 应只有一个 solid"

print("✅ Layer 1+2 passed / 通过")

# ===== Validation Layer 3: STEP re-import / STEP 重导入 =====
export_step(elbow.part, step_path)
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
            show(elbow.part, names=["pipe_elbow"], reset_camera=cam)
            time.sleep(0.8)
            save_screenshot(os.path.join(output_dir, f"pipe_elbow_{label}.png"))
            print(f"Screenshot saved / 截图已保存: pipe_elbow_{label}.png")
        print(f"OCP Viewer: preview opened on port {active_port} / 已在端口 {active_port} 打开预览 ✓")
    else:
        print("OCP Viewer: no running Viewer detected / 未检测到运行中的 Viewer")
except Exception as e:
    print(f"OCP preview skipped / 预览跳过: {e}")

print("\n✅ 06-pipe-elbow all tests passed / 全部测试通过")
