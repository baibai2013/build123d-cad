"""
逆运动学 (IK) — 三连杆解析求解 + 双构型对比
输入足端目标 → 解析求解 → build123d 构建两种姿态 → OCP 显示

用法：python 22_ik_single_leg.py
"""
from build123d import *
from ocp_vscode import show
import numpy as np
import math

# ===== 腿参数 (mm) =====
d1 = 55     # 肩偏移
L1 = 100    # 大腿长
L2 = 100    # 小腿长

# ===== 足端目标 (mm) =====
target = (70.7, 55.0, -170.7)  # FK([0,-45,90]) 的结果


# ===== DH FK（用于验证） =====
def dh_matrix(theta, d, a, alpha):
    ct, st = math.cos(theta), math.sin(theta)
    ca, sa = math.cos(alpha), math.sin(alpha)
    return np.array([
        [ct, -st*ca,  st*sa, a*ct],
        [st,  ct*ca, -ct*sa, a*st],
        [0,   sa,     ca,    d   ],
        [0,   0,      0,     1   ]
    ])


def fk_leg(angles_rad, d1=55, L1=100, L2=100):
    """FK: 角度(rad) → 足端位置(mm)"""
    T01 = dh_matrix(angles_rad[0], 0, 0, math.pi/2)
    T12 = dh_matrix(angles_rad[1], d1, L1, 0)
    T23 = dh_matrix(angles_rad[2], 0, L2, 0)
    T = T01 @ T12 @ T23
    return T[:3, 3]


# ===== 三连杆解析 IK =====
def ik_leg(target, d1=55, L1=100, L2=100, knee_sign=1):
    """
    三连杆平面 IK (mm 单位)。
    knee_sign: +1 膝正弯, -1 膝反弯
    返回: (θ1, θ2, θ3) 弧度，或 None
    """
    x, y, z = target

    # hip 侧摆角
    theta1 = math.atan2(y, x)

    # 投影平面距离
    r = math.sqrt(x**2 + y**2) - d1
    s = -z
    D_sq = r**2 + s**2
    D = math.sqrt(D_sq)

    # 可达性检查
    if D > L1 + L2 or D < abs(L1 - L2):
        return None

    # 膝关节角（余弦定理）
    cos_t3 = (D_sq - L1**2 - L2**2) / (2 * L1 * L2)
    cos_t3 = max(-1.0, min(1.0, cos_t3))
    theta3 = knee_sign * math.acos(cos_t3)

    # 肩俯仰角
    phi = math.atan2(s, r)
    psi = math.atan2(L2 * math.sin(theta3), L1 + L2 * math.cos(theta3))
    theta2 = phi - psi

    return (theta1, theta2, theta3)


# ===== 求解两种构型 =====
print("=" * 60)
print(f"目标: ({target[0]:.1f}, {target[1]:.1f}, {target[2]:.1f}) mm")
print(f"参数: d1={d1} L1={L1} L2={L2} mm")
print("-" * 60)

configs = []
for knee_sign, name in [(+1, "膝正弯 (knee+)"), (-1, "膝反弯 (knee-)")]:
    result = ik_leg(target, d1, L1, L2, knee_sign)
    if result is None:
        print(f"  {name}: 不可达")
        continue

    t1, t2, t3 = result
    print(f"  {name}: θ1={math.degrees(t1):+.1f}° "
          f"θ2={math.degrees(t2):+.1f}° θ3={math.degrees(t3):+.1f}°")

    # FK 验证
    foot = fk_leg([t1, t2, t3], d1, L1, L2)
    error = np.linalg.norm(np.array(foot) - np.array(target))
    print(f"         FK验证: ({foot[0]:+.2f}, {foot[1]:+.2f}, {foot[2]:+.2f}) "
          f"误差={error:.4f}mm")

    configs.append((name, [t1, t2, t3]))

print("=" * 60)

# ===== build123d 可视化 =====
def build_leg_viz(angles_rad, offset_y=0):
    """构建腿链可视化（关节球 + 骨骼线）"""
    T01 = dh_matrix(angles_rad[0], 0, 0, math.pi/2)
    T12 = dh_matrix(angles_rad[1], d1, L1, 0)
    T23 = dh_matrix(angles_rad[2], 0, L2, 0)

    pts = [
        np.array([0, offset_y, 0]),
        T01[:3, 3] + np.array([0, offset_y, 0]),
        (T01 @ T12)[:3, 3] + np.array([0, offset_y, 0]),
        (T01 @ T12 @ T23)[:3, 3] + np.array([0, offset_y, 0]),
    ]

    spheres = []
    for p in pts:
        spheres.append(Pos(p[0], p[1], p[2]) * Sphere(radius=5))

    return Compound(children=spheres)


# 目标点标记
target_marker = Pos(target[0], target[1], target[2]) * Sphere(radius=8)

# 构建两种构型（Y 方向偏移以便对比）
viz_objects = [target_marker]
viz_names = ["target"]
viz_colors = ["red"]

for i, (name, angles) in enumerate(configs):
    offset_y = i * 150  # 间隔 150mm
    leg_viz = build_leg_viz(angles, offset_y)
    viz_objects.append(leg_viz)
    viz_names.append(name)
    viz_colors.append("steelblue" if i == 0 else "orange")

show(*viz_objects, names=viz_names, colors=viz_colors)

print("\nDone: IK dual configuration visualized in OCP Viewer")
