"""
正运动学 (FK) — 三连杆腿链可视化
输入角度数组 → DH 齐次变换 → 计算各关节和足端位置 → OCP 显示

用法：python 21_fk_leg_chain.py
"""
from build123d import *
from ocp_vscode import show
import numpy as np
import math

# ===== 腿参数 (mm) =====
d1 = 55     # 肩偏移
L1 = 100    # 大腿长
L2 = 100    # 小腿长

# ===== 关节角度 (度) =====
theta1_deg = 0      # hip 侧摆
theta2_deg = -45    # upper 前后摆
theta3_deg = 90     # lower 膝关节

# ===== DH 正运动学 =====
def dh_matrix(theta, d, a, alpha):
    """标准 DH 齐次变换矩阵"""
    ct, st = math.cos(theta), math.sin(theta)
    ca, sa = math.cos(alpha), math.sin(alpha)
    return np.array([
        [ct, -st*ca,  st*sa, a*ct],
        [st,  ct*ca, -ct*sa, a*st],
        [0,   sa,     ca,    d   ],
        [0,   0,      0,     1   ]
    ])


def fk_leg(angles_deg, d1=55, L1=100, L2=100):
    """
    三连杆 FK：输入角度(度) → 各关节位置(mm)
    返回: [(name, [x,y,z]), ...]
    """
    t1 = math.radians(angles_deg[0])
    t2 = math.radians(angles_deg[1])
    t3 = math.radians(angles_deg[2])

    T01 = dh_matrix(t1, 0,  0,  math.pi/2)
    T12 = dh_matrix(t2, d1, L1, 0)
    T23 = dh_matrix(t3, 0,  L2, 0)

    T_hip  = T01
    T_knee = T01 @ T12
    T_foot = T01 @ T12 @ T23

    return [
        ("shoulder", np.array([0.0, 0.0, 0.0])),
        ("hip",      T_hip[:3, 3]),
        ("knee",     T_knee[:3, 3]),
        ("foot",     T_foot[:3, 3]),
    ]


# ===== 计算 =====
angles = [theta1_deg, theta2_deg, theta3_deg]
joints = fk_leg(angles)

print("=" * 50)
print(f"输入角度: θ1={angles[0]}° θ2={angles[1]}° θ3={angles[2]}°")
print(f"腿参数:  d1={d1}mm L1={L1}mm L2={L2}mm")
print("-" * 50)
for name, pos in joints:
    print(f"  {name:10s}: ({pos[0]:+8.2f}, {pos[1]:+8.2f}, {pos[2]:+8.2f}) mm")
print("=" * 50)

# ===== build123d 可视化 =====
# 关节球
joint_spheres = []
joint_colors = ["red", "green", "blue", "orange"]
joint_names = []

for i, (name, pos) in enumerate(joints):
    sphere = Pos(pos[0], pos[1], pos[2]) * Sphere(radius=5)
    joint_spheres.append(sphere)
    joint_names.append(name)

# 骨骼连接线（用细圆柱近似）
bones = []
bone_names = []
for i in range(len(joints) - 1):
    p1 = joints[i][1]
    p2 = joints[i+1][1]
    mid = (p1 + p2) / 2
    length = np.linalg.norm(p2 - p1)

    if length < 0.1:
        continue

    # 构建方向向量
    direction = (p2 - p1) / length

    # 简单骨骼：在中点放一个 Box
    bone = Pos(mid[0], mid[1], mid[2]) * Box(3, 3, length)
    bones.append(bone)
    bone_names.append(f"bone_{joints[i][0]}_{joints[i+1][0]}")

# 足端标记（更大的球）
foot_pos = joints[-1][1]
foot_marker = Pos(foot_pos[0], foot_pos[1], foot_pos[2]) * Sphere(radius=8)

# 坐标轴参考（原点处）
axis_x = Box(50, 1, 1)
axis_y = Pos(0, 25, 0) * Box(1, 50, 1)
axis_z = Pos(0, 0, 25) * Box(1, 1, 50)

# OCP 显示
show(
    *joint_spheres,
    foot_marker,
    axis_x, axis_y, axis_z,
    names=joint_names + ["foot_marker", "X_axis", "Y_axis", "Z_axis"],
    colors=joint_colors + ["red", "red", "green", "blue"],
)

print("\nDone: FK leg chain visualized in OCP Viewer")
