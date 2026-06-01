"""
卡扣 / Snap-Fit Clip
用途：塑料壳体卡扣，3D打印柔性连接
复杂度：★★★☆☆（扫掠 + 薄壁件）
注意：打印方向：Z轴朝上，卡爪在顶端。建议 PETG 或 TPU 材料。
"""
from build123d import *
import math

# ===== Parameters / 参数 =====
body_l      = 20    # 卡扣臂长度 mm
body_w      = 8     # 宽度 mm
body_t      = 1.5   # 臂厚度 mm（决定弹性，越薄越灵活）
hook_h      = 2.5   # 钩爪高度 mm
hook_angle  = 45    # 钩爪倒角角度（°），越小越容易插入
base_l      = 12    # 底座长度 mm
base_h      = 4     # 底座厚度 mm
mount_r     = 1.5   # 安装孔半径（M3）mm
clearance   = 0.3   # 配合间隙（单边）mm

# ===== Modeling / 建模 =====
with BuildPart() as clip:
    # 底座
    Box(base_l, body_w, base_h)
    # 弹性臂
    with BuildSketch(clip.faces().sort_by(Axis.Z)[-1]):
        with Locations(Pos((body_l / 2 - base_l / 2), 0)):
            Rectangle(body_l, body_w)
    extrude(amount=body_l)

    # 掏空底座（减重，保留安装凸缘）
    inner_face = clip.faces().sort_by(Axis.Z)[0]
    wall = 1.5
    with BuildSketch(inner_face):
        Rectangle(base_l - wall * 2, body_w - wall * 2)
    extrude(amount=base_h - wall, mode=Mode.SUBTRACT)

    # 钩爪（在臂端部切出倒角）
    arm_top = clip.faces().sort_by(Axis.Z)[-1]
    hook_face = clip.faces().filter_by(Axis.X).sort_by(Axis.X)[-1]  # 臂端面
    with BuildSketch(hook_face):
        # 梯形截面的钩爪
        hook_pts = [
            (0, 0),
            (0, body_t * 2),
            (hook_h, body_t * 2),
            (hook_h * (1 - 1 / (1 + 1 / math.tan(math.radians(hook_angle)))), 0),
        ]
        with BuildLine():
            Polyline(*hook_pts, close=True)
        make_face()
    extrude(amount=-body_w, mode=Mode.SUBTRACT)

    # 安装孔（底座两侧）
    with Locations(Pos(-base_l / 4, 0), Pos(base_l / 4, 0)):
        Hole(radius=mount_r)

    # 臂根部圆角（防止应力集中）
    fillet(
        clip.edges().sort_by(Axis.Z).group_by(Axis.Z)[len(clip.edges().sort_by(Axis.Z).group_by(Axis.Z)) // 2],
        radius=0.5
    )

# ===== Validation / 验证 =====
assert clip.part is not None, "part is None / part 为空"
assert clip.part.is_valid,    "BRep invalid / BRep 无效"

bb = clip.part.bounding_box()
print(f"总尺寸: {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm")
print(f"臂厚: {body_t}mm（材料 PETG 推荐 1.2-2.0mm）")
print(f"体积: {clip.part.volume:.1f} mm³")

# ===== Export / 导出 =====
export_step(clip.part, "12_snap_fit_clip.step")
