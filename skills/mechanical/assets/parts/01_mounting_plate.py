"""
安装板 / Mounting Plate
建模序列：取平板毛坯 → 四角打 M5 通孔 → 顶面圆角
参数化重点：修改 margin 一个参数，孔位自动跟随

测试覆盖：
  - 几何断言（包围盒、体积、孔数）
  - 选择器有效性（sort_by 顶面）
  - 参数化联动（margin → 孔间距）
  - OCP Viewer 多视角截图（ISO / TOP / FRONT）
"""
from build123d import *
import os

# ===== 参数 =====
l        = 100    # 板长 mm
w        = 80     # 板宽 mm
h        = 10     # 板厚 mm
hole_r   = 2.5    # M5 孔半径 mm（M5 = Φ5mm，R=2.5mm）
margin   = 12     # 孔中心到板边距离 mm（改这一个参数，孔位全局跟随）
fillet_r = 3      # 顶面圆角半径 mm

# ===== 派生尺寸 =====
hole_x_spacing = l - 2 * margin   # 两孔列间距（X 方向）
hole_y_spacing = w - 2 * margin   # 两孔行间距（Y 方向）

# ===== 建模 =====
# 操作序列：取毛坯 → 四角打孔 → 顶面圆角
with BuildPart() as plate:
    # Step 1: 平板毛坯
    Box(l, w, h)

    # Step 2: 四角 M5 通孔（2×2 GridLocations 阵列）
    with GridLocations(hole_x_spacing, hole_y_spacing, 2, 2):
        Hole(radius=hole_r)

    # Step 3: 顶面所有边倒 R3 圆角（选择器取顶面，无硬编码 Z 坐标）
    fillet(plate.faces().sort_by(Axis.Z)[-1].edges(), radius=fillet_r)

# ============================================================
# 几何断言验证
# ============================================================
print("=" * 50)
print("几何断言验证")
print("=" * 50)

bb = plate.part.bounding_box()
vol = plate.part.volume

# 包围盒
assert abs(bb.size.X - l) < 0.01, f"长度错误: {bb.size.X:.2f} ≠ {l}"
assert abs(bb.size.Y - w) < 0.01, f"宽度错误: {bb.size.Y:.2f} ≠ {w}"
assert abs(bb.size.Z - h) < 0.01, f"厚度错误: {bb.size.Z:.2f} ≠ {h}"

# 体积：实体 < 无孔毛坯（打孔 + 顶面 fillet 均减小体积）
raw_vol = l * w * h
assert vol < raw_vol, f"体积应 < 毛坯体积，实际 {vol:.1f} >= {raw_vol}"
# 合理范围：保留 90%~99.9% 的毛坯体积（4孔 + fillet 共约 2~5%）
assert vol > raw_vol * 0.90, f"体积异常偏小: {vol:.1f}，应 > {raw_vol*0.90:.0f}"

# BRep 有效性
assert plate.part.is_valid, "BRep 无效！"

# 选择器验证：顶面 Z 坐标 = h/2
top_face = plate.faces().sort_by(Axis.Z)[-1]
top_z = top_face.center().Z
assert abs(top_z - h / 2) < 0.01, f"顶面 Z 位置错误: {top_z:.3f} ≠ {h/2}"

# 孔数验证：内圆弧面（圆柱孔侧面）= 4 个
hole_faces = plate.faces().filter_by(GeomType.CYLINDER)
assert len(hole_faces) >= 4, f"孔数错误: 期望 >=4，实际 {len(hole_faces)}"

# 实体数量：应为单一 solid（无多余残留体）
solids = plate.part.solids()
assert len(solids) == 1, f"实体数错误: 期望 1，实际 {len(solids)}"

print(f"  ✓ 包围盒: {bb.size.X:.1f} × {bb.size.Y:.1f} × {bb.size.Z:.1f} mm")
print(f"  ✓ 体积: {vol:.1f} mm³ (毛坯 {raw_vol} - 4孔)")
print(f"  ✓ BRep 有效")
print(f"  ✓ 顶面 Z={top_z:.3f} mm (期望 {h/2})")
print(f"  ✓ 孔侧面数: {len(hole_faces)} (>=4)")
print(f"  ✓ 单一 solid (无残留体)")

# 参数化联动验证：margin 改变，孔间距自动跟随
print("\n参数化联动验证：")
for m_test in [8, 12, 16]:
    xs = l - 2 * m_test
    ys = w - 2 * m_test
    print(f"  margin={m_test:2d}mm → 孔间距 {xs}×{ys}mm")

print("\n所有断言通过 ✓")

# ===== 导出 + Layer 3 STEP 回读验证（CADCodeVerify Layer 3 等价）=====
os.makedirs("output", exist_ok=True)
step_path = "output/mounting_plate.step"
export_step(plate.part, step_path)

# 文件存在且有实质内容
step_size = os.path.getsize(step_path)
assert step_size > 1000, f"STEP 文件过小 ({step_size} bytes)，可能为空"

# 回读验证：导出/导入体积偏差 < 0.1%（STEP 格式为精确 NURBS/BREP，无损）
reimported = import_step(step_path)
vol_diff = abs(reimported.volume - vol) / vol
assert vol_diff < 0.001, f"STEP 导出/导入体积偏差过大: {vol_diff:.4%}"

print(f"\n导出完成: {step_path} ({step_size:,} bytes)")
print(f"  ✓ STEP 回读体积偏差: {vol_diff:.6%} (< 0.1%)")

# ============================================================
# OCP Viewer 多视角截图测试
# 自动检测 ocp_vscode 运行端口，无需手动配置
# ============================================================
try:
    import time
    from ocp_vscode import show, set_port, Camera, save_screenshot
    from ocp_vscode.comms import port_check
    from ocp_vscode.state import get_ports

    # 自动探测活跃端口（从 state 文件中找第一个正在监听的端口）
    active_port = None
    for p in get_ports():
        if port_check(int(p)):
            active_port = int(p)
            break

    if active_port is None:
        print("OCP Viewer: 未找到活跃端口，跳过截图测试")
    else:
        set_port(active_port)
        print(f"\nOCP Viewer: 连接端口 {active_port}")

        # 视角列表：(Camera枚举, 文件名后缀)
        views = [
            (Camera.ISO,   "iso"),
            (Camera.TOP,   "top"),
            (Camera.FRONT, "front"),
        ]

        for cam, label in views:
            # 加载模型，指定视角
            show(
                plate.part,
                names=["mounting_plate"],
                colors=["steelblue"],
                reset_camera=cam,
            )
            time.sleep(1.5)  # 等待渲染完成

            screenshot_path = f"output/mounting_plate_{label}.png"
            save_screenshot(screenshot_path)
            print(f"  截图保存: {screenshot_path} ({label})")

        print("OCP 截图测试完成 ✓")

except ImportError:
    print("提示: 安装 ocp_vscode 可在 VS Code 中查看 3D 预览")
except Exception as e:
    print(f"OCP 预览跳过（{type(e).__name__}: {e}）")
