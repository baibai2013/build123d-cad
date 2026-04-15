"""
04-flange — Flange Plate / 法兰盘
Tests / 测试: Cylinder + center hole + PolarLocations bolt hole array + CounterBoreHole

Design intent (Dave Cowden style) / 设计意图:
  Blank disc -> center bore -> polar-arrayed counterbore bolt holes
  毛坯圆盘 -> 中心通孔 -> 极坐标均布沉头螺栓孔
"""

from build123d import *
import os

# ===== Parameters / 参数 =====
outer_r      = 40        # outer radius mm / 外径半径 mm  (outer diameter 80 mm / 外径 80mm)
flange_h     = 8         # flange height mm / 法兰高度 mm
center_r     = 15        # center bore radius mm / 中心通孔半径 mm

bolt_pcd_r   = 30        # bolt hole PCD radius mm / 螺栓孔 PCD 半径 mm  (PCD 60 mm)
bolt_count   = 6         # number of bolt holes / 螺栓孔数量
bolt_r       = 4         # bolt clearance hole radius mm / 螺栓通孔半径 mm  (M8 clearance / M8 通孔)
cbore_r      = 6.5       # counterbore radius mm / 沉头半径 mm  (M8 hex-head socket / M8 内六角螺栓头)
cbore_depth  = 4         # counterbore depth mm / 沉头深度 mm

output_dir = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(output_dir, exist_ok=True)
step_path  = os.path.join(output_dir, "flange.step")

# ===== Modeling / 建模 =====
with BuildPart() as flange:
    # Step 1: blank cylinder (flange body) / 步骤1：毛坯圆柱（法兰盘基体）
    Cylinder(radius=outer_r, height=flange_h)

    # Step 2: center through-bore (main shaft hole) / 步骤2：中心通孔（主轴孔）
    Hole(radius=center_r)

    # Step 3: 6 counterbore bolt holes evenly distributed on PCD / 步骤3：PCD 均布 6 个沉头螺栓孔
    with PolarLocations(radius=bolt_pcd_r, count=bolt_count):
        CounterBoreHole(
            radius=bolt_r,
            counter_bore_radius=cbore_r,
            counter_bore_depth=cbore_depth,
        )

# ===== Validation Layer 1 + 2 / 验证 Layer 1 + 2 =====
assert flange.part is not None, "part is None / part 为空"
assert flange.part.is_valid,    "BRep invalid / BRep 无效"

vol = flange.part.volume
bb  = flange.part.bounding_box()
print(f"Dimensions / 尺寸: {bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f} mm")
print(f"Volume / 体积: {vol:.2f} mm³")

assert bb.size.Z > 0,                           "height is 0 / 高度为 0"
assert abs(bb.size.Z - flange_h) < 0.5,        f"height deviation / 高度偏差: {bb.size.Z:.2f}"
assert abs(bb.size.X - outer_r * 2) < 0.5,     f"outer diameter deviation X / 外径偏差 X: {bb.size.X:.2f}"
assert abs(bb.size.Y - outer_r * 2) < 0.5,     f"outer diameter deviation Y / 外径偏差 Y: {bb.size.Y:.2f}"

# Volume lower bound: full disc minus center bore and 6 counterbore holes (10% tolerance)
# 体积下限：完整圆盘扣掉中心孔 + 6 个沉头孔的估算（10% 宽容度）
import math
raw_vol    = math.pi * outer_r**2 * flange_h                       # full cylinder / 完整圆柱
center_vol = math.pi * center_r**2 * flange_h                      # center bore / 中心孔
bolt_vol   = bolt_count * (math.pi * bolt_r**2 * flange_h          # clearance holes / 通孔
              + math.pi * (cbore_r**2 - bolt_r**2) * cbore_depth)  # extra counterbore / 沉头额外部分
min_vol    = (raw_vol - center_vol - bolt_vol) * 0.9                # 10% margin / 10% 宽容度
assert vol > min_vol, f"volume out of range / 体积异常: {vol:.2f} < {min_vol:.2f}"

# Exactly one solid / 确认有且仅有一个 solid
assert len(flange.part.solids()) == 1, "expected exactly one solid / 应只有一个 solid"

print("✅ Layer 1+2 passed / 通过")

# ===== Validation Layer 3: STEP export + re-import accuracy / STEP 导出 + 重导入精度 =====
export_step(flange.part, step_path)
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

    active_port = next((int(p) for p in get_ports() if port_check(int(p))), None)
    if active_port:
        set_port(active_port)

        views = [
            ("ISO",   Camera.ISO),
            ("TOP",   Camera.TOP),
            ("FRONT", Camera.FRONT),
        ]
        for label, cam in views:
            show(flange.part, names=["flange"], reset_camera=cam)
            import time; time.sleep(0.8)
            save_screenshot(os.path.join(output_dir, f"flange_{label}.png"))
            print(f"Screenshot saved / 截图已保存: flange_{label}.png")

        print(f"OCP Viewer: preview opened on port {active_port} / 已在端口 {active_port} 打开预览 ✓")
    else:
        print("OCP Viewer: no running Viewer detected / 未检测到运行中的 Viewer")
except Exception as e:
    print(f"OCP preview skipped / 预览跳过: {e}")

print("\n✅ 04-flange all tests passed / 全部测试通过")
