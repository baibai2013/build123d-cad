"""
工作空间点云 — 遍历角度组合 → FK → 足端点云 → OCP 显示
可视化三连杆腿的可达工作空间。

用法：python 23_workspace_cloud.py
"""
from build123d import *
from ocp_vscode import show
import numpy as np
import math

# ===== 腿参数 (mm) =====
d1 = 55
L1 = 100
L2 = 100

# ===== 角度范围 (度) =====
theta1_range = (-45, 45)    # hip 侧摆
theta2_range = (-90, 0)     # upper 前后
theta3_range = (-30, 120)   # lower 膝关节
steps = 15                  # 每轴采样点数


# ===== DH FK =====
def dh_matrix(theta, d, a, alpha):
    ct, st = math.cos(theta), math.sin(theta)
    ca, sa = math.cos(alpha), math.sin(alpha)
    return np.array([
        [ct, -st*ca,  st*sa, a*ct],
        [st,  ct*ca, -ct*sa, a*st],
        [0,   sa,     ca,    d   ],
        [0,   0,      0,     1   ]
    ])


def fk_foot(t1, t2, t3):
    """FK → 足端位置 (mm)"""
    T = (dh_matrix(t1, 0, 0, math.pi/2)
         @ dh_matrix(t2, d1, L1, 0)
         @ dh_matrix(t3, 0, L2, 0))
    return T[:3, 3]


# ===== 生成点云 =====
print(f"生成工作空间点云: {steps}³ = {steps**3} 点...")

points = []
for t1 in np.linspace(math.radians(theta1_range[0]),
                       math.radians(theta1_range[1]), steps):
    for t2 in np.linspace(math.radians(theta2_range[0]),
                           math.radians(theta2_range[1]), steps):
        for t3 in np.linspace(math.radians(theta3_range[0]),
                               math.radians(theta3_range[1]), steps):
            foot = fk_foot(t1, t2, t3)
            points.append(foot)

cloud = np.array(points)
print(f"点云大小: {cloud.shape[0]} 点")
print(f"X 范围: [{cloud[:,0].min():.1f}, {cloud[:,0].max():.1f}] mm")
print(f"Y 范围: [{cloud[:,1].min():.1f}, {cloud[:,1].max():.1f}] mm")
print(f"Z 范围: [{cloud[:,2].min():.1f}, {cloud[:,2].max():.1f}] mm")

# ===== build123d 可视化 =====
# 用小球表示点云（采样以控制 OCP 渲染性能）
max_display = 500
if len(cloud) > max_display:
    indices = np.random.choice(len(cloud), max_display, replace=False)
    display_pts = cloud[indices]
else:
    display_pts = cloud

print(f"显示 {len(display_pts)} 个点...")

spheres = []
for pt in display_pts:
    spheres.append(Pos(pt[0], pt[1], pt[2]) * Sphere(radius=2))

workspace = Compound(children=spheres)

# 肩关节标记
shoulder = Sphere(radius=8)

# 默认站立姿态（参考）
stand_foot = fk_foot(0, math.radians(-45), math.radians(90))
stand_marker = Pos(stand_foot[0], stand_foot[1], stand_foot[2]) * Sphere(radius=6)

show(workspace, shoulder, stand_marker,
     names=["workspace_cloud", "shoulder", "stand_position"],
     colors=["steelblue", "red", "orange"],
     alphas=[0.3, 1.0, 1.0])

print("\nDone: Workspace cloud visualized in OCP Viewer")
