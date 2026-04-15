"""
07-heat-sink — Pin-Fin Heat Sink / 针状散热片
Tests / 测试:
  Box base + top face selector  — 30×30×3mm base plate / 底板顶面选择器
  GridLocations pin array       — 6×6 square pins, 8mm tall, 2mm wide / 6×6 方形针阵列
  sort_by(Axis.Z) top face      — sketch plane from sorted face / 排序取顶面作草图平面

Design intent (Dave Cowden style) / 设计意图:
  Base plate -> select top face -> grid-locate square pin sketches -> extrude pins upward
  Pin-fin style allows airflow from all four sides (vs plate fins: one direction only)
  底板 -> 选顶面 -> 网格定位方形针草图 -> 向上拉伸针柱
  针状散热片支持四面进风（平板式只能单向进风）
"""

from build123d import *
import os, math

# ===== Parameters / 参数 =====
base_l  = 30     # base plate length mm / 底板长度 mm
base_w  = 30     # base plate width mm / 底板宽度 mm
base_h  = 3      # base plate height mm / 底板高度 mm

pin_nx  = 6      # pin count in X / X 方向针数
pin_ny  = 6      # pin count in Y / Y 方向针数
pin_h   = 8      # pin height mm / 针高度 mm
pin_w   = 2      # pin width (square cross-section) mm / 针宽（正方形截面）mm
margin  = 3      # edge margin mm / 边缘留量 mm
# Spacing between pin centers / 针中心间距
pin_x_spacing = (base_l - 2 * margin) / (pin_nx - 1)   # 4.8 mm
pin_y_spacing = (base_w - 2 * margin) / (pin_ny - 1)   # 4.8 mm

output_dir = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(output_dir, exist_ok=True)
step_path  = os.path.join(output_dir, "heat_sink.step")

# ===== Modeling / 建模 =====
with BuildPart() as sink:

    # Step 1: base plate / 步骤1：底板
    Box(base_l, base_w, base_h)

    # Step 2: select top face as pin sketch plane / 步骤2：选顶面作针草图平面
    top_face = sink.faces().sort_by(Axis.Z)[-1]

    # Step 3: grid-locate square pin sketches on top face, extrude upward
    # 步骤3：在顶面网格定位方形针草图，向上拉伸针柱
    with BuildSketch(top_face):
        with GridLocations(pin_x_spacing, pin_y_spacing, pin_nx, pin_ny):
            Rectangle(pin_w, pin_w)
    extrude(amount=pin_h)

# ===== Validation Layer 1 + 2 / 验证 =====
assert sink.part is not None, "part is None / part 为空"
assert sink.part.is_valid,    "BRep invalid / BRep 无效"

vol = sink.part.volume
bb  = sink.part.bounding_box()
print(f"Bounding box / 包围盒: {bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f} mm")
print(f"Volume / 体积: {vol:.2f} mm³")

# Bounding box checks / 包围盒检查
assert abs(bb.size.X - base_l) < 1.0, \
    f"length deviation / 长度偏差: {bb.size.X:.2f} vs {base_l}"
assert abs(bb.size.Y - base_w) < 1.0, \
    f"width deviation / 宽度偏差: {bb.size.Y:.2f} vs {base_w}"
assert abs(bb.size.Z - (base_h + pin_h)) < 1.0, \
    f"total height deviation / 总高偏差: {bb.size.Z:.2f} vs {base_h + pin_h}"

# Volume: base plate + pin array / 体积：底板 + 针阵列
base_vol = base_l * base_w * base_h
pin_vol  = pin_nx * pin_ny * pin_w * pin_w * pin_h
total_approx = base_vol + pin_vol
# Allow ±5% tolerance / 允许 ±5% 宽容度
assert total_approx * 0.95 < vol < total_approx * 1.05, \
    f"volume out of range / 体积超范围: {vol:.2f}, expected ~{total_approx:.2f}"

assert len(sink.part.solids()) == 1, "expected exactly one solid / 应只有一个 solid"

print("✅ Layer 1+2 passed / 通过")

# ===== Validation Layer 3: STEP re-import / STEP 重导入 =====
export_step(sink.part, step_path)
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
            show(sink.part, names=["heat_sink"], reset_camera=cam)
            time.sleep(0.8)
            save_screenshot(os.path.join(output_dir, f"heat_sink_{label}.png"))
            print(f"Screenshot saved / 截图已保存: heat_sink_{label}.png")
        print(f"OCP Viewer: preview opened on port {active_port} / 已在端口 {active_port} 打开预览 ✓")
    else:
        print("OCP Viewer: no running Viewer detected / 未检测到运行中的 Viewer")
except Exception as e:
    print(f"OCP preview skipped / 预览跳过: {e}")

print("\n✅ 07-heat-sink all tests passed / 全部测试通过")
