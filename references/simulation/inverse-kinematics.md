# 逆运动学 (Inverse Kinematics)

> 给定末端目标位置 → 求解关节角度。步态控制的核心。

---

## 1. 解析法：三连杆平面 IK

四足单腿是典型的三连杆结构（hip + upper + lower），存在闭合形式解析解。

### 几何推导

已知：
- 足端目标 `(x, y, z)`（相对于肩关节原点）
- 肩偏移 `d1`、大腿长 `L1`、小腿长 `L2`

求解：`θ1` (hip)、`θ2` (upper)、`θ3` (lower)

```
步骤 1：求 θ1（hip 侧摆角）
    θ1 = atan2(y, x)
    （将脚投影到 xz 平面）

步骤 2：计算投影平面内的距离
    r = sqrt(x² + y²) - d1    （扣除肩偏移后的水平距离）
    s = -z                      （垂直距离，注意 z 轴方向）
    D = sqrt(r² + s²)           （肩到脚的直线距离）

步骤 3：求 θ3（lower 膝关节角）— 余弦定理
    cos_θ3 = (D² - L1² - L2²) / (2·L1·L2)
    θ3 = ±acos(cos_θ3)         （两解：膝正弯/反弯）

步骤 4：求 θ2（upper 肩俯仰角）— 几何法
    φ = atan2(s, r)
    ψ = atan2(L2·sin(θ3), L1 + L2·cos(θ3))
    θ2 = φ - ψ
```

### 纯 Python 实现

```python
"""三连杆解析 IK — 纯 math 实现"""
import math

def ik_leg(target, d1=0.055, L1=0.10, L2=0.10, knee_sign=1):
    """
    三连杆平面 IK。
    target: (x, y, z) 足端目标，m 单位
    knee_sign: +1 = 膝正弯（默认），-1 = 膝反弯
    返回: (theta1, theta2, theta3) 弧度，或 None（不可达）
    """
    x, y, z = target

    # Step 1: hip 侧摆角
    theta1 = math.atan2(y, x)

    # Step 2: 投影平面距离
    r = math.sqrt(x**2 + y**2) - d1
    s = -z
    D_sq = r**2 + s**2
    D = math.sqrt(D_sq)

    # 可达性检查
    if D > L1 + L2 or D < abs(L1 - L2):
        return None  # 不可达

    # Step 3: 膝关节角（余弦定理）
    cos_theta3 = (D_sq - L1**2 - L2**2) / (2 * L1 * L2)
    cos_theta3 = max(-1.0, min(1.0, cos_theta3))  # 数值安全
    theta3 = knee_sign * math.acos(cos_theta3)

    # Step 4: 肩俯仰角
    phi = math.atan2(s, r)
    psi = math.atan2(L2 * math.sin(theta3), L1 + L2 * math.cos(theta3))
    theta2 = phi - psi

    return (theta1, theta2, theta3)

# === 测试 ===
target = (0.07, 0.055, -0.17)  # FK 结果的逆问题
result = ik_leg(target)
if result:
    t1, t2, t3 = result
    print(f"θ1={math.degrees(t1):.1f}° θ2={math.degrees(t2):.1f}° θ3={math.degrees(t3):.1f}°")
```

### FK→IK→FK 往返验证

```python
"""验证：FK(IK(target)) ≈ target"""
import numpy as np

# 正向：给定角度 → 足端
from forward_kinematics import fk_leg
original_angles = [0, -np.pi/4, np.pi/2]
pos = fk_leg(original_angles)
target = pos["foot"]

# 逆向：足端 → 角度
result = ik_leg(tuple(target))
print(f"原始角度: {[f'{np.degrees(a):.1f}°' for a in original_angles]}")
print(f"IK 结果:  {[f'{np.degrees(a):.1f}°' for a in result]}")

# 再正向验证
pos2 = fk_leg(list(result))
error = np.linalg.norm(pos2["foot"] - target)
print(f"往返误差: {error:.6f} m")  # 应 < 0.0001
assert error < 0.001, f"往返误差过大: {error}"
```

---

## 2. 数值 IK（通用方法）

当关节链超过三连杆，或有特殊约束时，需要数值方法。

### 方法 A：scipy 优化

```python
"""数值 IK — scipy.optimize"""
import numpy as np
from scipy.optimize import minimize

def ik_numerical(target, fk_func, q0=None, n_joints=3):
    """
    数值 IK：最小化 ||FK(q) - target||²
    target: (x, y, z) 目标位置
    fk_func: FK 函数，输入角度数组 → 返回 dict 含 "foot" 键
    q0: 初始猜测（None = 零位）
    """
    if q0 is None:
        q0 = np.zeros(n_joints)
    target = np.array(target)

    def cost(q):
        pos = fk_func(q)
        return np.sum((pos["foot"] - target) ** 2)

    result = minimize(cost, q0, method="L-BFGS-B",
                      bounds=[(-np.pi, np.pi)] * n_joints)

    if result.fun < 1e-8:
        return result.x
    return None  # 未收敛
```

### 方法 B：ikpy 库

```python
"""数值 IK — ikpy 库"""
# pip install ikpy
import ikpy.chain
import numpy as np

# 从 URDF 加载链
chain = ikpy.chain.Chain.from_urdf_file(
    "quadruped.urdf",
    base_elements=["base_link"],
    active_links_mask=[False, True, True, True, False]  # 只激活 3 个关节
)

# IK 求解
target_position = [0.07, 0.055, -0.17]
angles = chain.inverse_kinematics(target_position)
print(f"IK 结果: {np.degrees(angles[1:4])}")  # 跳过 base 和 end

# 验证
fk_result = chain.forward_kinematics(angles)
print(f"FK 验证: {fk_result[:3, 3]}")
```

### 方法 C：Jacobian 伪逆迭代

```python
"""数值 IK — Jacobian 伪逆法"""
import numpy as np

def ik_jacobian(target, fk_func, jacob_func, q0=None,
                n_joints=3, max_iter=100, tol=1e-6):
    """
    Jacobian 伪逆 IK。
    jacob_func: 返回 3×n Jacobian 矩阵
    """
    q = np.zeros(n_joints) if q0 is None else np.array(q0)
    target = np.array(target)

    for i in range(max_iter):
        pos = fk_func(q)["foot"]
        error = target - pos

        if np.linalg.norm(error) < tol:
            return q

        J = jacob_func(q)              # 3×n Jacobian
        J_pinv = np.linalg.pinv(J)     # n×3 伪逆
        dq = J_pinv @ error
        q = q + 0.5 * dq               # 步长 0.5 避免振荡

    return None  # 未收敛

def numerical_jacobian(fk_func, q, delta=1e-6):
    """数值差分 Jacobian"""
    n = len(q)
    pos0 = fk_func(q)["foot"]
    J = np.zeros((3, n))
    for i in range(n):
        dq = np.zeros(n)
        dq[i] = delta
        pos1 = fk_func(q + dq)["foot"]
        J[:, i] = (pos1 - pos0) / delta
    return J
```

---

## 3. 工作空间分析

通过遍历角度网格，计算所有可达足端位置，形成工作空间点云。

```python
"""工作空间点云生成"""
import numpy as np

def workspace_cloud(d1=0.055, L1=0.10, L2=0.10,
                    theta1_range=(-45, 45),
                    theta2_range=(-90, 0),
                    theta3_range=(-30, 120),
                    steps=20):
    """
    遍历角度组合 → 足端点云
    返回: (N, 3) numpy 数组
    """
    from forward_kinematics import fk_leg

    points = []
    for t1 in np.linspace(*np.radians(theta1_range), steps):
        for t2 in np.linspace(*np.radians(theta2_range), steps):
            for t3 in np.linspace(*np.radians(theta3_range), steps):
                pos = fk_leg([t1, t2, t3], d1, L1, L2)
                points.append(pos["foot"])

    return np.array(points)

# 生成点云
cloud = workspace_cloud(steps=15)  # 15³ = 3375 点
print(f"点云大小: {cloud.shape}")
print(f"X 范围: [{cloud[:,0].min():.3f}, {cloud[:,0].max():.3f}]")
print(f"Y 范围: [{cloud[:,1].min():.3f}, {cloud[:,1].max():.3f}]")
print(f"Z 范围: [{cloud[:,2].min():.3f}, {cloud[:,2].max():.3f}]")
```

### 可达性判断

```python
from scipy.spatial import ConvexHull

hull = ConvexHull(cloud)
# 检查目标是否在凸包内（简化判断）
def is_reachable(target, hull_points):
    """粗略判断：目标是否在工作空间凸包内"""
    from scipy.spatial import Delaunay
    hull = Delaunay(hull_points)
    return hull.find_simplex(target) >= 0
```

---

## 4. 多解与奇异性

### 双解构型

三连杆 IK 通常有两个解（`knee_sign = ±1`）：

```python
# 膝正弯（常用，类似人类蹲姿）
result_pos = ik_leg(target, knee_sign=+1)

# 膝反弯（反关节，类似鸟腿）
result_neg = ik_leg(target, knee_sign=-1)
```

选择策略：
- **默认膝正弯**（`knee_sign=+1`）— 适合大多数四足
- 根据当前姿态选最近解 — 避免动画跳变
- 检查角度限位 — 超出 `angular_range` 的解丢弃

### 奇异位置

| 奇异类型 | 条件 | 现象 |
|---------|------|------|
| 完全伸直 | D = L1 + L2 | Jacobian 秩亏，数值法不收敛 |
| 完全折叠 | D = |L1 - L2| | 同上 |
| hip 奇异 | x = y = 0 | θ1 不定 |

处理策略：
```python
# 在奇异附近添加扰动
if abs(D - (L1 + L2)) < 1e-6:
    D = L1 + L2 - 1e-4  # 微缩，避免奇异
```

---

## 5. IK 库对比

| 库 | 安装 | 方法 | 适合场景 | 速度 |
|---|------|------|---------|------|
| 纯 Python (math) | 无需安装 | 解析法 | 三连杆四足腿 | 最快 |
| ikpy | `pip install ikpy` | 数值法（BFGS） | 快速原型，URDF 解析 | 中 |
| roboticstoolbox | `pip install roboticstoolbox-python` | 解析+数值 | 教学，DH 标准 | 中 |
| Pinocchio | `pip install pin` | 数值法+动力学 | 研究级，实时控制 | 快 |
| PyBullet | `pip install pybullet` | `calculateInverseKinematics` | 仿真内 IK | 快 |

**推荐路径**：
1. 先用纯 Python 解析法（三连杆够用）
2. 需要 URDF 集成时用 ikpy
3. 需要教学验证时用 roboticstoolbox
4. 需要实时控制时用 Pinocchio
