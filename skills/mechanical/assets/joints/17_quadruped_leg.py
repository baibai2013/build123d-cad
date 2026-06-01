"""
四足腿部关节链 / Quadruped Leg Joint Chain
用途：机械猫腿部 — 髋→膝→踝→足 串联 RevoluteJoint
难度：★★★★

技法：RevoluteJoint 链 + connect_to 自动定位 + 关节可视化
"""
from build123d import *

# ===== 腿部参数 =====
upper_leg_l = 50          # 大腿长 mm
upper_leg_w = 12          # 大腿宽 mm
upper_leg_t = 8           # 大腿厚 mm
lower_leg_l = 45          # 小腿长 mm
lower_leg_w = 10
lower_leg_t = 6
foot_l = 20               # 足部长
foot_w = 15
foot_t = 4

# ===== 髋关节挂载块 =====
with BuildPart() as hip_mount:
    Box(20, 20, 15)
    # 髋关节：绕 Y 轴旋转（前后摆腿）
    RigidJoint("hip_fixed", hip_mount,
               Location((0, 0, -7.5)))   # 底面中心

hip_mount.part.label = "hip_mount"

# ===== 大腿 =====
with BuildPart() as upper_leg:
    Box(upper_leg_w, upper_leg_t, upper_leg_l)
    # 顶部关节（连接髋关节）
    RevoluteJoint("hip_joint", upper_leg,
                  axis=Axis((0, 0, upper_leg_l / 2), (0, 1, 0)),
                  angular_range=(-45, 45))
    # 底部关节（连接膝关节）
    RigidJoint("knee_fixed", upper_leg,
               Location((0, 0, -upper_leg_l / 2)))

upper_leg.part.label = "upper_leg"

# ===== 小腿 =====
with BuildPart() as lower_leg:
    Box(lower_leg_w, lower_leg_t, lower_leg_l)
    # 顶部关节（连接膝关节）
    RevoluteJoint("knee_joint", lower_leg,
                  axis=Axis((0, 0, lower_leg_l / 2), (0, 1, 0)),
                  angular_range=(-90, 0))   # 膝关节只向后弯
    # 底部关节（连接踝关节）
    RigidJoint("ankle_fixed", lower_leg,
               Location((0, 0, -lower_leg_l / 2)))

lower_leg.part.label = "lower_leg"

# ===== 足部 =====
with BuildPart() as foot:
    Box(foot_l, foot_w, foot_t)
    # 顶部关节（连接踝关节）
    RevoluteJoint("ankle_joint", foot,
                  axis=Axis((0, 0, foot_t / 2), (0, 1, 0)),
                  angular_range=(-30, 30))

foot.part.label = "foot"

# ===== 装配关节链 =====
# 髋 → 大腿
hip_mount.part.joints["hip_fixed"].connect_to(
    upper_leg.part.joints["hip_joint"], angle=15)    # 前倾 15°

# 膝 → 小腿
upper_leg.part.joints["knee_fixed"].connect_to(
    lower_leg.part.joints["knee_joint"], angle=-30)  # 后弯 30°

# 踝 → 足部
lower_leg.part.joints["ankle_fixed"].connect_to(
    foot.part.joints["ankle_joint"], angle=15)       # 足部微调

# ===== 组装 =====
leg_assembly = Compound(children=[
    hip_mount.part, upper_leg.part, lower_leg.part, foot.part
])
leg_assembly.label = "quadruped_leg"

# ===== 导出 =====
export_step(leg_assembly, "quadruped_leg.step")

# ===== 验证 =====
bb = leg_assembly.bounding_box()
print(f"腿部装配尺寸: {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm")
print(f"关节链: hip(±45°) → knee(-90°~0°) → ankle(±30°)")

# ===== OCP 预览 =====
# from ocp_vscode import show
# show(hip_mount.part, upper_leg.part, lower_leg.part, foot.part,
#      names=["hip_mount", "upper_leg", "lower_leg", "foot"],
#      colors=["gray", "steelblue", "steelblue", "orange"],
#      render_joints=True)
