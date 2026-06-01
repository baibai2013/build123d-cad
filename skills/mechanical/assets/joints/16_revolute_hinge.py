"""
RevoluteJoint 铰链装配 / Revolute Joint Hinge Assembly
用途：演示 RevoluteJoint 关节系统的基本用法
难度：★★★

技法：RevoluteJoint + connect_to + render_joints
"""
from build123d import *

# ===== 参数 =====
leaf_l, leaf_w, leaf_t = 40, 25, 3    # 铰链叶片
pin_r = 2                              # 铰链销半径
pin_h = 12                             # 铰链销高度
barrel_r = 4                           # 铰链圆筒半径
barrel_h = 5                           # 铰链圆筒高度

# ===== 叶片 A（固定端） =====
with BuildPart() as leaf_a:
    Box(leaf_l, leaf_w, leaf_t)
    # 铰链圆筒
    with BuildSketch(Plane.XZ.offset(leaf_w / 2)):
        Circle(barrel_r)
    extrude(amount=barrel_h)
    # 销孔
    with Locations((0, leaf_w / 2 + barrel_h / 2, leaf_t / 2)):
        Hole(radius=pin_r, depth=barrel_h + 2)

    # 定义关节：固定端
    RigidJoint("hinge_fixed", leaf_a,
               Location((0, leaf_w / 2 + barrel_h / 2, leaf_t / 2)))

leaf_a.part.label = "leaf_a"

# ===== 叶片 B（活动端） =====
with BuildPart() as leaf_b:
    Box(leaf_l, leaf_w, leaf_t)
    # 铰链圆筒
    with BuildSketch(Plane.XZ.offset(-leaf_w / 2)):
        Circle(barrel_r)
    extrude(amount=-barrel_h)
    # 销孔
    with Locations((0, -leaf_w / 2 - barrel_h / 2, leaf_t / 2)):
        Hole(radius=pin_r, depth=barrel_h + 2)

    # 定义关节：旋转端
    RevoluteJoint("hinge_rotate", leaf_b,
                  axis=Axis((0, -leaf_w / 2 - barrel_h / 2, leaf_t / 2),
                            (0, 1, 0)),
                  angular_range=(-120, 120))

leaf_b.part.label = "leaf_b"

# ===== 装配 =====
# connect_to 自动定位 leaf_b
leaf_a.part.joints["hinge_fixed"].connect_to(
    leaf_b.part.joints["hinge_rotate"],
    angle=45    # 打开 45°
)

# ===== 导出 =====
assembly = Compound(children=[leaf_a.part, leaf_b.part])
assembly.label = "hinge_assembly"
export_step(assembly, "revolute_hinge.step")

print(f"铰链装配完成，打开角度: 45°")
print(f"关节范围: {leaf_b.part.joints['hinge_rotate'].angular_range}")

# ===== OCP 预览 =====
# from ocp_vscode import show
# show(leaf_a.part, leaf_b.part,
#      names=["leaf_a", "leaf_b"],
#      colors=["steelblue", "orange"],
#      render_joints=True)
