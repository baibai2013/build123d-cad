# PyBullet 快速入门

> 加载 URDF → 地面 → 关节控制 → 步态仿真

---

## 1. 安装

```bash
pip install pybullet
```

---

## 2. 最小可运行示例

```python
"""PyBullet 最小示例：加载 URDF + 地面 + GUI"""
import pybullet as p
import pybullet_data
import time

# 启动仿真
physics_client = p.connect(p.GUI)  # p.DIRECT 无 GUI
p.setAdditionalSearchPath(pybullet_data.getDataPath())
p.setGravity(0, 0, -9.81)

# 加载地面
plane_id = p.loadURDF("plane.urdf")

# 加载机器人
robot_id = p.loadURDF(
    "quadruped.urdf",           # 你的 URDF 文件
    basePosition=[0, 0, 0.2],   # 初始位置（抬高避免穿地）
    useFixedBase=False           # False = 自由浮动
)

# 打印关节信息
n_joints = p.getNumJoints(robot_id)
for i in range(n_joints):
    info = p.getJointInfo(robot_id, i)
    print(f"Joint {i}: {info[1].decode()} type={info[2]} "
          f"lower={info[8]:.2f} upper={info[9]:.2f}")

# 仿真循环
for _ in range(10000):
    p.stepSimulation()
    time.sleep(1/240)

p.disconnect()
```

---

## 3. 关节控制三种模式

### POSITION_CONTROL — 角度伺服（最常用）

```python
# 将关节 0 移动到目标角度 -0.5 rad
p.setJointMotorControl2(
    robot_id,
    jointIndex=0,
    controlMode=p.POSITION_CONTROL,
    targetPosition=-0.5,        # 目标角度 (rad)
    force=5.0                   # 最大力矩 (Nm)
)
```

对应真实世界的**舵机控制**：给定目标角度，内置 PD 控制器自动跟踪。

### VELOCITY_CONTROL — 速度控制

```python
p.setJointMotorControl2(
    robot_id,
    jointIndex=0,
    controlMode=p.VELOCITY_CONTROL,
    targetVelocity=1.0,         # 目标角速度 (rad/s)
    force=5.0
)
```

### TORQUE_CONTROL — 力矩控制（高级）

```python
# 先禁用默认电机
p.setJointMotorControl2(robot_id, 0, p.VELOCITY_CONTROL, force=0)

# 直接施加力矩
p.setJointMotorControl2(
    robot_id,
    jointIndex=0,
    controlMode=p.TORQUE_CONTROL,
    force=2.0                   # 力矩 (Nm)
)
```

需要自己实现 PD 控制器，适合动力学研究。

---

## 4. 步态仿真循环

```python
"""完整四足步态仿真"""
import pybullet as p
import pybullet_data
import numpy as np
import time

# === 初始化 ===
client = p.connect(p.GUI)
p.setAdditionalSearchPath(pybullet_data.getDataPath())
p.setGravity(0, 0, -9.81)
p.setTimeStep(1/240)

plane = p.loadURDF("plane.urdf")
robot = p.loadURDF("quadruped.urdf", [0, 0, 0.2], useFixedBase=False)

# === 获取关节映射 ===
joint_map = {}
for i in range(p.getNumJoints(robot)):
    info = p.getJointInfo(robot, i)
    joint_map[info[1].decode()] = i

# === 步态生成器（从 gait-planning.md 导入） ===
# from gait_generator import GaitGenerator
# gait = GaitGenerator(gait_type="trot", period=0.8)

# === 仿真循环 ===
dt = 1/240
t = 0
max_force = 5.0

for step in range(24000):  # 100 秒
    # 步态 → 各腿关节角度
    # angles = gait.step(t)

    # 示例：固定站立姿态
    stand_angles = {
        "LF_hip": 0, "LF_upper": -0.5, "LF_lower": 1.0,
        "RF_hip": 0, "RF_upper": -0.5, "RF_lower": 1.0,
        "LR_hip": 0, "LR_upper": -0.5, "LR_lower": 1.0,
        "RR_hip": 0, "RR_upper": -0.5, "RR_lower": 1.0,
    }

    for jname, angle in stand_angles.items():
        if jname in joint_map:
            p.setJointMotorControl2(
                robot, joint_map[jname],
                p.POSITION_CONTROL,
                targetPosition=angle,
                force=max_force
            )

    p.stepSimulation()
    t += dt

    if step % 240 == 0:  # 每秒打印一次
        pos, orn = p.getBasePositionAndOrientation(robot)
        print(f"t={t:.1f}s  pos=({pos[0]:.3f}, {pos[1]:.3f}, {pos[2]:.3f})")

p.disconnect()
```

---

## 5. 传感器读取

### 关节状态

```python
# 读取关节角度、角速度、力矩
state = p.getJointState(robot, joint_index)
position = state[0]     # 当前角度 (rad)
velocity = state[1]     # 当前角速度 (rad/s)
reaction  = state[2]    # 反作用力 (Fx,Fy,Fz,Mx,My,Mz)
torque   = state[3]     # 施加的力矩 (Nm)
```

### 基座状态（IMU 替代）

```python
pos, orn = p.getBasePositionAndOrientation(robot)
lin_vel, ang_vel = p.getBaseVelocity(robot)
euler = p.getEulerFromQuaternion(orn)  # (roll, pitch, yaw)
```

### 接触力

```python
contacts = p.getContactPoints(bodyA=robot, bodyB=plane)
for c in contacts:
    contact_normal = c[7]     # 法向量
    normal_force = c[9]       # 法向力
    link_index = c[3]         # 哪个 link 接触了
```

---

## 6. 调试技巧

### 足端轨迹可视化

```python
prev_foot_pos = {}

def draw_foot_trail(robot, foot_link_index, leg_name, color):
    """在 PyBullet 中画足端轨迹线"""
    state = p.getLinkState(robot, foot_link_index)
    pos = state[0]

    if leg_name in prev_foot_pos:
        p.addUserDebugLine(
            prev_foot_pos[leg_name], pos,
            lineColorRGB=color,
            lineWidth=2,
            lifeTime=3.0  # 3 秒后消失
        )
    prev_foot_pos[leg_name] = pos
```

### 实时参数滑块

```python
# 创建 GUI 滑块
stride_id = p.addUserDebugParameter("stride", 0.01, 0.10, 0.04)
clearance_id = p.addUserDebugParameter("clearance", 0.01, 0.05, 0.03)
period_id = p.addUserDebugParameter("period", 0.3, 2.0, 0.8)

# 在循环中读取
stride = p.readUserDebugParameter(stride_id)
clearance = p.readUserDebugParameter(clearance_id)
period = p.readUserDebugParameter(period_id)
```

### 相机控制

```python
# 设置相机位置
p.resetDebugVisualizerCamera(
    cameraDistance=0.5,
    cameraYaw=45,
    cameraPitch=-30,
    cameraTargetPosition=[0, 0, 0.1]
)

# 跟随机器人
pos, _ = p.getBasePositionAndOrientation(robot)
p.resetDebugVisualizerCamera(0.5, 45, -30, pos)
```

---

## 7. MuJoCo 对比简述

| 特性 | PyBullet | MuJoCo |
|------|---------|--------|
| 安装 | `pip install pybullet` | `pip install mujoco` |
| 格式 | URDF | MJCF（更丰富） |
| 接触模型 | 硬接触 | 软接触（更真实） |
| 速度 | 中 | 快（GPU 加速） |
| 可视化 | 内置 OpenGL GUI | 内置 viewer / mujoco.viewer |
| 适合 | 原型验证、教学 | 研究、RL 训练 |
| 许可证 | zlib | Apache 2.0（2022 年免费） |

### MuJoCo 最小示例

```python
"""MuJoCo 最小示例"""
import mujoco
import mujoco.viewer

# 从 XML 加载（MJCF 格式）
model = mujoco.MjModel.from_xml_path("robot.xml")
data = mujoco.MjData(model)

# 可视化
with mujoco.viewer.launch_passive(model, data) as viewer:
    while viewer.is_running():
        mujoco.mj_step(model, data)
        viewer.sync()
```

> MuJoCo 也支持加载 URDF（通过 `mujoco.MjModel.from_xml_string` + URDF→MJCF 转换）。

---

## 8. 推荐工作流

```
1. build123d 建模 → STEP 文件
2. URDF 导出 → robot.urdf + meshes/
3. yourdfpy 验证 → 可视化检查
4. PyBullet 加载 → 基本站立测试
5. 步态生成器接入 → 行走仿真
6. 参数调优 → GUI 滑块实时调节
7. (可选) MuJoCo 高保真验证
```
