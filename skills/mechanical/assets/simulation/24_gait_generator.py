"""
步态生成器 — 贝塞尔轨迹 + IK → OCP 四足步态动画
实现 trot 对角步态，可视化四腿协调运动。

用法：python 24_gait_generator.py
"""
from build123d import *
from ocp_vscode import show, Animation
import numpy as np
import math

# ===== 腿参数 (mm) =====
d1 = 55
L1 = 100
L2 = 100

# ===== 步态参数 =====
STRIDE = 40        # 步幅 mm
CLEARANCE = 30     # 抬脚高度 mm
PERIOD = 1.0       # 步态周期 s
DUTY = 0.5         # 占空比
GROUND_Z = -170    # 站立高度 mm

# 四腿相位（trot 对角步态）
LEG_PHASES = {
    "LF": 0.0,    # 左前
    "RF": 0.5,    # 右前
    "LR": 0.5,    # 左后
    "RR": 0.0,    # 右后
}

# 四腿肩关节位置（相对于体中心，mm）
BODY_L, BODY_W = 160, 100
LEG_ORIGINS = {
    "LF": np.array([ BODY_L/2,  BODY_W/2, 0]),
    "RF": np.array([ BODY_L/2, -BODY_W/2, 0]),
    "LR": np.array([-BODY_L/2,  BODY_W/2, 0]),
    "RR": np.array([-BODY_L/2, -BODY_W/2, 0]),
}


# ===== 贝塞尔足端轨迹 =====
def bernstein(n, k, t):
    """伯恩斯坦基函数"""
    from math import comb
    return comb(n, k) * t**k * (1 - t)**(n - k)


def bezier_swing(t_phase, stride, clearance):
    """摆动相: 11 点贝塞尔曲线"""
    cx = np.array([-0.5, -0.5, -0.25, -0.10, 0, 0, 0, 0.10, 0.25, 0.5, 0.5]) * stride
    cz = np.array([0, 0, 0.6, 0.9, 1.0, 1.0, 1.0, 0.9, 0.6, 0, 0]) * clearance
    n = len(cx) - 1
    x = sum(bernstein(n, k, t_phase) * cx[k] for k in range(n + 1))
    z = sum(bernstein(n, k, t_phase) * cz[k] for k in range(n + 1))
    return x, z


def foot_trajectory(t, phase_offset):
    """单腿完整轨迹: 支撑相 + 摆动相"""
    phase = ((t / PERIOD) + phase_offset) % 1.0
    if phase < DUTY:
        # 支撑相: 线性后移
        t_stance = phase / DUTY
        dx = STRIDE * (0.5 - t_stance)
        dz = 0
    else:
        # 摆动相: 贝塞尔
        t_swing = (phase - DUTY) / (1 - DUTY)
        dx, dz = bezier_swing(t_swing, STRIDE, CLEARANCE)
    return dx, 0, GROUND_Z + dz


# ===== 三连杆解析 IK (mm) =====
def ik_leg(target_mm, knee_sign=1):
    """解析 IK，返回 (θ1, θ2, θ3) 弧度"""
    x, y, z = target_mm
    theta1 = math.atan2(y, x) if (x != 0 or y != 0) else 0
    r = math.sqrt(x**2 + y**2) - d1
    s = -z
    D_sq = r**2 + s**2
    D = math.sqrt(max(D_sq, 0.01))

    if D > L1 + L2:
        D = L1 + L2 - 0.1
    if D < abs(L1 - L2):
        D = abs(L1 - L2) + 0.1

    cos_t3 = (D**2 - L1**2 - L2**2) / (2 * L1 * L2)
    cos_t3 = max(-1.0, min(1.0, cos_t3))
    theta3 = knee_sign * math.acos(cos_t3)

    phi = math.atan2(s, r)
    psi = math.atan2(L2 * math.sin(theta3), L1 + L2 * math.cos(theta3))
    theta2 = phi - psi

    return (theta1, theta2, theta3)


# ===== 构建四足模型 =====
print("构建四足模型...")

# 身体（简化为长方体）
body = Box(BODY_L, BODY_W, 30)
body.label = "body"

# 各腿组件（简化为圆柱）
legs_parts = {}
for name, origin in LEG_ORIGINS.items():
    upper = Pos(origin[0], origin[1], -L1/2) * Cylinder(radius=5, height=L1)
    upper.label = f"{name}_upper"
    legs_parts[name] = upper

# 装配
all_parts = [body] + list(legs_parts.values())
assembly = Compound(children=all_parts)

# ===== 生成动画轨迹 =====
print("生成 trot 步态动画轨迹...")

fps = 20
duration = 4.0  # 4 秒 = 4 个步态周期
n_frames = int(duration * fps)
dt = 1.0 / fps

# 时间轴
time_keys = [round(i * dt, 3) for i in range(n_frames + 1)]

# 各腿关节角度序列
leg_tracks = {}
for name in LEG_PHASES:
    leg_tracks[name] = {"angles": []}

for i in range(n_frames + 1):
    t = i * dt
    for name, phase in LEG_PHASES.items():
        foot_target = foot_trajectory(t, phase)
        angles = ik_leg(foot_target)
        leg_tracks[name]["angles"].append(angles)

# ===== OCP 显示 + 动画 =====
show(assembly,
     names=["quadruped"],
     colors=["steelblue"])

# 动画：用 upper leg 的 θ2 角度驱动 rz 轨道
animation = Animation()

for name in LEG_PHASES:
    path = f"/Group/quadruped/{name}_upper"
    # 提取 θ2 序列（主要可见的摆动角度）
    rz_values = [math.degrees(a[1]) for a in leg_tracks[name]["angles"]]
    animation.add_track(path, "rz", time_keys,
                       [[0, 0, v] for v in rz_values])

animation.animate(speed=1)

# ===== 打印步态摘要 =====
print("=" * 60)
print(f"步态: trot (对角步态)")
print(f"周期: {PERIOD}s  步幅: {STRIDE}mm  抬脚: {CLEARANCE}mm")
print(f"占空比: {DUTY*100:.0f}%  站立高度: {GROUND_Z}mm")
print(f"动画: {duration}s @ {fps}fps = {n_frames} 帧")
print("-" * 60)
for name, phase in LEG_PHASES.items():
    angles_start = leg_tracks[name]["angles"][0]
    print(f"  {name}: phase={phase:.1f}  "
          f"θ2_range=[{min(math.degrees(a[1]) for a in leg_tracks[name]['angles']):+.1f}°, "
          f"{max(math.degrees(a[1]) for a in leg_tracks[name]['angles']):+.1f}°]")
print("=" * 60)
print("\nDone: Gait animation playing in OCP Viewer")
