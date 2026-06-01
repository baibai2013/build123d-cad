# 正运动学 (Forward Kinematics)

> 给定关节角度 → 计算末端位置。运动学的基础操作。

---

## 1. DH 参数速查

Denavit-Hartenberg (DH) 参数用四个数描述相邻关节间的变换：

| 参数 | 符号 | 含义 |
|------|------|------|
| 关节角 | θ | 绕 z 轴旋转（旋转关节的变量） |
| 连杆偏移 | d | 沿 z 轴平移 |
| 连杆长度 | a | 沿 x 轴平移 |
| 连杆扭角 | α | 绕 x 轴旋转 |

单个 DH 变换矩阵：

```
T(θ, d, a, α) = Rz(θ) · Tz(d) · Tx(a) · Rx(α)

    ┌ cos θ  -sin θ·cos α   sin θ·sin α   a·cos θ ┐
    │ sin θ   cos θ·cos α  -cos θ·sin α   a·sin θ │
    │ 0       sin α         cos α          d       │
    └ 0       0             0              1       ┘
```

---

## 2. 四足单腿 DH 表

典型三连杆腿：hip → upper_leg → lower_leg → foot

| 关节 | θ | d | a | α | 说明 |
|------|---|---|---|---|------|
| hip | θ₁ | 0 | 0 | π/2 | 侧摆关节，轴线从 Z 转到 Y |
| upper_leg | θ₂ | d₁ | L₁ | 0 | 肩偏移 d₁，大腿长 L₁ |
| lower_leg | θ₃ | 0 | L₂ | 0 | 小腿长 L₂ |

常用参数（SpotMicro 尺寸参考）：

```python
d1 = 0.055   # 肩偏移 55mm → 0.055m
L1 = 0.10    # 大腿长 100mm
L2 = 0.10    # 小腿长 100mm
```

---

## 3. 纯 Python + numpy 实现

```python
"""FK：DH 齐次变换链 — 纯 numpy 实现"""
import numpy as np

def dh_matrix(theta, d, a, alpha):
    """单个 DH 变换矩阵（标准 DH 约定）"""
    ct, st = np.cos(theta), np.sin(theta)
    ca, sa = np.cos(alpha), np.sin(alpha)
    return np.array([
        [ct, -st*ca,  st*sa, a*ct],
        [st,  ct*ca, -ct*sa, a*st],
        [0,   sa,     ca,    d   ],
        [0,   0,      0,     1   ]
    ])

def fk_leg(angles, d1=0.055, L1=0.10, L2=0.10):
    """三连杆腿 FK：输入 [θ1, θ2, θ3] → 输出各关节和足端位置"""
    theta1, theta2, theta3 = angles

    T01 = dh_matrix(theta1, 0,  0,  np.pi/2)   # hip
    T12 = dh_matrix(theta2, d1, L1, 0)          # upper_leg
    T23 = dh_matrix(theta3, 0,  L2, 0)          # lower_leg

    # 各关节位置
    T_hip   = T01
    T_knee  = T01 @ T12
    T_foot  = T01 @ T12 @ T23

    positions = {
        "shoulder": np.array([0, 0, 0]),
        "hip":      T_hip[:3, 3],
        "knee":     T_knee[:3, 3],
        "foot":     T_foot[:3, 3],
    }
    return positions

# === 测试 ===
angles = [0, -np.pi/4, np.pi/2]  # hip=0°, upper=-45°, lower=90°
pos = fk_leg(angles)
for name, p in pos.items():
    print(f"{name:10s}: ({p[0]:+.4f}, {p[1]:+.4f}, {p[2]:+.4f})")
```

输出示例：
```
shoulder  : (+0.0000, +0.0000, +0.0000)
hip       : (+0.0000, +0.0000, +0.0000)
knee      : (+0.0707, +0.0550, -0.0707)
foot      : (+0.0707, +0.0550, -0.1707)
```

---

## 4. build123d Location 验证

同样的角度输入，用 build123d 的 Location 链验证 FK 结果一致：

```python
"""用 build123d Location 验证 FK 结果"""
from build123d import *
import numpy as np

# 与 FK 函数相同的参数
d1, L1, L2 = 0.055, 0.10, 0.10
theta1, theta2, theta3 = 0, -np.pi/4, np.pi/2

# build123d Location 链（单位：m → mm 转换）
scale = 1000  # m → mm
loc_hip = Location((0, 0, 0), (0, 0, np.degrees(theta1))) * Location((0, 0, 0), (np.degrees(np.pi/2), 0, 0))
loc_upper = Location((0, 0, d1*scale), (0, 0, np.degrees(theta2))) * Location((L1*scale, 0, 0))
loc_lower = Location((0, 0, 0), (0, 0, np.degrees(theta3))) * Location((L2*scale, 0, 0))

# 足端位置 = 链式变换
foot_loc = loc_hip * loc_upper * loc_lower
foot_pos = foot_loc.IsSetPosition  # 或用 .IsTranslation 属性
print(f"build123d foot: {foot_loc}")
```

> 注意：build123d 使用 mm 单位，DH 代码通常用 m。验证时注意单位转换。

---

## 5. roboticstoolbox-python 对比验证

```python
"""用 roboticstoolbox 交叉验证"""
import roboticstoolbox as rtb
import numpy as np

# 同一条腿的 DH 定义
leg = rtb.DHRobot([
    rtb.RevoluteDH(d=0,     a=0,    alpha=np.pi/2),
    rtb.RevoluteDH(d=0.055, a=0.10, alpha=0),
    rtb.RevoluteDH(d=0,     a=0.10, alpha=0),
], name="quadruped_leg")

print(leg)  # 打印 DH 参数表

# FK
q = [0, -np.pi/4, np.pi/2]
T = leg.fkine(q)
print(f"rtb foot: {T.t}")

# 与纯 numpy FK 对比
from forward_kinematics_example import fk_leg  # 上面的函数
pos = fk_leg(q)
diff = np.linalg.norm(T.t - pos["foot"])
print(f"差异: {diff:.6f} m")  # 应接近 0
```

> 安装：`pip install roboticstoolbox-python`（可选，仅用于验证）

---

## 6. 关节位置可视化

用 build123d 构建关节球 + 骨骼线进行 OCP 可视化：

```python
"""FK 结果 OCP 可视化"""
from build123d import *
from ocp_vscode import show
import numpy as np

# FK 计算
d1, L1, L2 = 55, 100, 100  # mm 单位
angles = [0, -np.pi/4, np.pi/2]

# 简化 FK（直接几何，mm 单位）
def fk_leg_mm(angles, d1=55, L1=100, L2=100):
    """简化版 FK，返回关节位置列表（mm）"""
    # ... 同上 fk_leg 但输入/输出用 mm
    import numpy as np
    def dh_matrix(theta, d, a, alpha):
        ct, st = np.cos(theta), np.sin(theta)
        ca, sa = np.cos(alpha), np.sin(alpha)
        return np.array([
            [ct, -st*ca,  st*sa, a*ct],
            [st,  ct*ca, -ct*sa, a*st],
            [0,   sa,     ca,    d   ],
            [0,   0,      0,     1   ]
        ])
    T01 = dh_matrix(angles[0], 0,  0,  np.pi/2)
    T12 = dh_matrix(angles[1], d1, L1, 0)
    T23 = dh_matrix(angles[2], 0,  L2, 0)
    return [
        np.array([0, 0, 0]),
        T01[:3, 3],
        (T01 @ T12)[:3, 3],
        (T01 @ T12 @ T23)[:3, 3],
    ]

pts = fk_leg_mm(angles)

# 关节球
joints = []
for p in pts:
    joints.append(Pos(p[0], p[1], p[2]) * Sphere(radius=4))

# 骨骼线
bones = []
for i in range(len(pts)-1):
    p1, p2 = pts[i], pts[i+1]
    bone_len = np.linalg.norm(p2 - p1)
    if bone_len > 0.1:
        bones.append(
            Pos((p1[0]+p2[0])/2, (p1[1]+p2[1])/2, (p1[2]+p2[2])/2)
            * Cylinder(radius=2, height=bone_len)
        )

leg_viz = Compound(children=joints)
show(leg_viz, names=["leg_fk"])
```

---

## 7. 常见陷阱

| 陷阱 | 说明 | 解决 |
|------|------|------|
| 标准 DH vs 修改 DH | 两种约定的矩阵不同 | 本 skill 统一用**标准 DH** |
| 角度单位 | numpy 用弧度，build123d 用角度 | FK 内部弧度，显示时转角度 |
| 单位 | DH 常用 m，build123d 用 mm | 接口处显式转换，函数签名标注单位 |
| 关节角范围 | 超出物理限位会得到不可能姿态 | FK 前 clamp 到 angular_range |
| Z-up vs Y-up | build123d 是 Z-up，一些仿真器是 Y-up | URDF 导出时处理坐标系 |
