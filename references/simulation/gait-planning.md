# 步态规划 (Gait Planning)

> 时间 t → 各腿相位 → 足端轨迹 → IK → 关节角度 → 执行

---

## 1. 四种基本步态

四足机器人的步态由**各腿相位偏移**和**占空比**定义。

| 步态 | LF | RF | LR | RR | 占空比 | 特点 |
|------|----|----|----|----|--------|------|
| 爬行 crawl | 0° | 90° | 180° | 270° | 75% | 最慢最稳，始终 3 脚着地 |
| 小跑 trot | 0° | 180° | 180° | 0° | 50% | 对角同步，中速 |
| 踱步 pace | 0° | 180° | 0° | 180° | 50% | 同侧同步，易侧倾 |
| 弹跳 bound | 0° | 0° | 180° | 180° | 30% | 前后对交替，最快 |

- **相位**：各腿在一个步态周期内的时间偏移（0°=周期起点，180°=半周期）
- **占空比**：支撑相占周期的比例（75%=脚在地面的时间占 75%）

### 步态选择

```python
GAITS = {
    "crawl": {"phases": [0, 0.25, 0.5, 0.75], "duty": 0.75},
    "trot":  {"phases": [0, 0.5,  0.5, 0],    "duty": 0.50},
    "pace":  {"phases": [0, 0.5,  0,   0.5],  "duty": 0.50},
    "bound": {"phases": [0, 0,    0.5, 0.5],  "duty": 0.30},
}
```

---

## 2. 贝塞尔曲线足端轨迹（MIT 11 点法）

来源：MIT Biomimetic Robotics Lab，`moribots/spot_mini_mini` 的标准实现。

### 摆动相（swing）：抬脚→前伸→落地

用 11 个贝塞尔控制点定义一条平滑的空中轨迹：

```python
"""11 点贝塞尔摆动轨迹"""
import numpy as np
from scipy.special import comb

def bernstein(n, k, t):
    """伯恩斯坦基函数"""
    return comb(n, k) * t**k * (1 - t)**(n - k)

def bezier_swing(t_phase, stride, clearance):
    """
    摆动相贝塞尔轨迹。
    t_phase: 0→1 摆动相进度
    stride: 步幅 (m)
    clearance: 抬脚高度 (m)
    返回: (dx, dz) 相对于中心的位移
    """
    # 11 个控制点（归一化坐标）
    # X 方向：从 -stride/2 到 +stride/2
    cx = np.array([
        -0.5, -0.5, -0.25, -0.10, 0.0, 0.0,
        0.0, 0.10, 0.25, 0.5, 0.5
    ]) * stride

    # Z 方向：中间抬高
    cz = np.array([
        0, 0, 0.6, 0.9, 1.0, 1.0,
        1.0, 0.9, 0.6, 0, 0
    ]) * clearance

    n = len(cx) - 1
    x = sum(bernstein(n, k, t_phase) * cx[k] for k in range(n + 1))
    z = sum(bernstein(n, k, t_phase) * cz[k] for k in range(n + 1))

    return x, z

def stance_phase(t_phase, stride):
    """
    支撑相：脚在地面线性后移。
    t_phase: 0→1 支撑相进度
    返回: (dx, dz)
    """
    x = stride * (0.5 - t_phase)  # 从 +stride/2 线性移到 -stride/2
    z = 0  # 贴地
    return x, z
```

### 完整单腿轨迹

```python
def foot_trajectory(t, period, phase_offset, stride, clearance,
                    duty_factor=0.5, ground_z=-0.17):
    """
    单腿完整轨迹。
    t: 当前时间 (s)
    period: 步态周期 (s)
    phase_offset: 该腿的相位偏移 (0~1)
    ground_z: 站立时足端 z 坐标 (m)
    返回: (x, y, z) 足端目标位置
    """
    # 当前相位（0~1 循环）
    phase = ((t / period) + phase_offset) % 1.0

    if phase < duty_factor:
        # 支撑相
        t_stance = phase / duty_factor
        dx, dz = stance_phase(t_stance, stride)
    else:
        # 摆动相
        t_swing = (phase - duty_factor) / (1 - duty_factor)
        dx, dz = bezier_swing(t_swing, stride, clearance)

    return (dx, 0, ground_z + dz)
```

---

## 3. 步态生成器架构

```
┌──────────┐     ┌──────────────┐     ┌──────────┐     ┌──────────┐
│ 时间 t   │ ──▶ │ 步态调度器    │ ──▶ │ IK 求解  │ ──▶ │ 执行     │
│          │     │ (相位+轨迹)   │     │          │     │          │
└──────────┘     └──────────────┘     └──────────┘     └──────────┘
                  各腿 foot_target      各腿 angles      OCP Animation
                  (x, y, z)             (θ1, θ2, θ3)     / PyBullet
```

### 四足步态生成器

```python
"""四足步态生成器"""
import numpy as np

class GaitGenerator:
    def __init__(self, gait_type="trot", period=1.0,
                 stride=0.04, clearance=0.03,
                 d1=0.055, L1=0.10, L2=0.10,
                 body_width=0.10, body_length=0.16,
                 ground_z=-0.17):
        gait = GAITS[gait_type]
        self.phases = gait["phases"]
        self.duty = gait["duty"]
        self.period = period
        self.stride = stride
        self.clearance = clearance
        self.ground_z = ground_z

        # 腿名称和肩关节偏移
        self.legs = {
            "LF": np.array([ body_length/2,  body_width/2, 0]),
            "RF": np.array([ body_length/2, -body_width/2, 0]),
            "LR": np.array([-body_length/2,  body_width/2, 0]),
            "RR": np.array([-body_length/2, -body_width/2, 0]),
        }

        # IK 参数
        self.d1, self.L1, self.L2 = d1, L1, L2

    def step(self, t):
        """
        给定时间 t → 各腿关节角度
        返回: dict[leg_name] → (θ1, θ2, θ3)
        """
        from inverse_kinematics import ik_leg

        result = {}
        for i, (name, offset) in enumerate(self.legs.items()):
            # 足端轨迹（相对于肩关节）
            target = foot_trajectory(
                t, self.period, self.phases[i],
                self.stride, self.clearance,
                self.duty, self.ground_z
            )

            # IK 求解
            angles = ik_leg(target, self.d1, self.L1, self.L2)
            if angles is None:
                angles = (0, -np.pi/4, np.pi/2)  # 默认站立姿态
            result[name] = angles

        return result
```

---

## 4. 步态 → OCP 动画

将关节角度序列转换为 OCP `Animation` 轨道：

```python
"""步态 → OCP Animation"""
from ocp_vscode import show, Animation
import numpy as np

# 生成关节角度时间序列
gait = GaitGenerator(gait_type="trot", period=1.0)
fps = 30
duration = 2.0  # 2 个周期
n_frames = int(duration * fps)
dt = 1.0 / fps

# 收集轨迹
tracks = {leg: {"rz": []} for leg in gait.legs}
time_keys = [i * dt for i in range(n_frames + 1)]

for i in range(n_frames + 1):
    t = i * dt
    angles = gait.step(t)
    for leg_name, (t1, t2, t3) in angles.items():
        tracks[leg_name]["rz"].append(np.degrees(t2))  # 只取主关节角度示例

# 构建 Animation
animation = Animation()
for leg_name in gait.legs:
    path = f"/Group/{leg_name}_upper"
    animation.add_track(path, "rz", time_keys,
                       [[0, 0, v] for v in tracks[leg_name]["rz"]])
animation.animate(speed=1)
```

---

## 5. 步态 → PyBullet

```python
"""步态 → PyBullet 控制循环"""
import pybullet as p
import time

# 假设已加载 URDF（见 pybullet-quickstart.md）
# robot = p.loadURDF("quadruped.urdf", ...)

gait = GaitGenerator(gait_type="trot")
dt = 1/240  # PyBullet 默认时间步

t = 0
while True:
    angles = gait.step(t)

    for leg_name, (t1, t2, t3) in angles.items():
        # 映射到 PyBullet 关节 ID（需要根据 URDF 定义）
        joint_ids = get_leg_joint_ids(robot, leg_name)
        for jid, angle in zip(joint_ids, [t1, t2, t3]):
            p.setJointMotorControl2(
                robot, jid,
                p.POSITION_CONTROL,
                targetPosition=angle,
                force=1.0
            )

    p.stepSimulation()
    t += dt
    time.sleep(dt)
```

---

## 6. 步态参数调节

| 参数 | 范围 | 效果 |
|------|------|------|
| period | 0.3~2.0s | 越小步频越快 |
| stride | 0.02~0.08m | 越大步幅越长 |
| clearance | 0.01~0.05m | 越大抬脚越高 |
| duty_factor | 0.3~0.8 | 越大支撑时间越长（越稳） |
| ground_z | -0.12~-0.20m | 站立高度（腿伸展程度） |

### 调节策略

1. **先慢后快**：从 crawl（period=2.0, duty=0.75）开始验证
2. **先低后高**：clearance 从 0.01 开始，逐步增加
3. **先短后长**：stride 从 0.02 开始
4. **PyBullet 实测**：参数调好后在仿真中验证稳定性

---

## 7. 参考实现

| 项目 | 文件 | 特点 |
|------|------|------|
| spot_mini_mini | `bezier_gait.py` | MIT 11 点贝塞尔标准实现 |
| StanfordQuadruped | `pupper/GaitPlanner.py` | 教学级，代码清晰 |
| spotMicro | `Kinematics/` | PyBullet 集成完整 |
