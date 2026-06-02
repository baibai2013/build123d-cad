# 仿真领域(Simulation)

> 场景:URDF 加载、关节控制、力反馈、刚体动力学、步态可视化、MPC/LQR、强化学习。
> 核心原则:**先用 PyBullet 跑通端到端,严肃动力学走 Drake,GPU 大规模学习走 Isaac Lab**。

---

## 候选源(7 个,P1-3 落定)

### 1. Bullet3 / PyBullet examples ★★★★★

- **URL**:https://github.com/bulletphysics/bullet3/tree/master/examples/pybullet
- **价值**:URDF 加载 + 关节控制 + 力反馈完整样例,工业首选轻量物理仿真
- **借鉴点**:
  - `loadURDF` 标准用法 → `references/simulation/pybullet-quickstart.md` 已对接
  - `setJointMotorControlArray` 关节控制
  - 步态调试:固定 base + 单腿 IK 验证
- **stack**:C++ + Python
- **license**:zlib
- **license_status**:pending(zlib 极宽松,几乎无限制)
- **retrieved_at**:2026-06-02
- **借鉴注意**:zlib 不强制署名,但仍建议在文件头标来源

### 2. Drake examples ★★★★

- **URL**:https://github.com/RobotLocomotion/drake/tree/master/examples
- **价值**:严肃刚体动力学 + MPC + LQR 教科书代码
- **借鉴点**:
  - `examples/quadruped/` 四足动力学参考
  - 当 PyBullet 精度不足(扭矩控制 / 反馈线性化)时升级到 Drake
- **stack**:C++ (Python binding 可用)
- **license**:BSD-3-Clause
- **license_status**:pending
- **retrieved_at**:2026-06-02
- **借鉴注意**:本项目主仿真平台仍是 PyBullet,Drake 作为备份学术参考

### 3. Gazebo (gz-sim) demos ★★★★

- **URL**:https://github.com/gazebosim/gz-sim/tree/main/examples
- **价值**:完整 SDF 世界 + 传感器 + ROS2 桥
- **借鉴点**:
  - SDF 世界文件结构 → P1 `skills/sdf/` 子技能直接抄
  - 传感器(IMU / 相机 / lidar)挂载语法
  - ROS2 plugin 接入
- **stack**:C++ + SDF + ROS2
- **license**:Apache 2.0
- **license_status**:pending
- **retrieved_at**:2026-06-02
- **借鉴注意**:与 `skills/sdf/` 子技能强联动(P1-1 algorithm 落)

### 4. MuJoCo Menagerie ★★★★

- **URL**:https://github.com/google-deepmind/mujoco_menagerie
- **价值**:DeepMind 维护的 MJCF 模型库,含多种四足机器狗(Spot / Unitree A1 / ANYmal)
- **借鉴点**:
  - 同体型四足 MJCF 描述 → 我们出 URDF 后对照
  - 关节惯量 / 阻尼默认值参考
- **stack**:XML(MJCF)
- **license**:Apache 2.0(代码)+ 各模型条款不同
- **license_status**:pending(每个模型 LICENSE 单独读,Spot 等可能 vendor 限制)
- **retrieved_at**:2026-06-02
- **借鉴注意**:**逐模型读 LICENSE**,Boston Dynamics Spot / Unitree 等供应商可能保留闭源条款

### 5. PyBullet Quickstart Guide(官方教程)★★★★★

- **URL**:https://github.com/bulletphysics/bullet3/blob/master/docs/pybullet_quickstart_guide/PyBulletQuickstartGuide.md.html
- **价值**:官方教程,本仓 simulation playbook 直接对接
- **借鉴点**:
  - `references/simulation/pybullet-quickstart.md` 已浓缩
  - 复杂场景查阅原文档
- **stack**:Python + 文档
- **license**:zlib(同 Bullet3)
- **license_status**:pending
- **retrieved_at**:2026-06-02

### 6. robotics-toolbox-python(Peter Corke)★★★★

- **URL**:https://github.com/petercorke/robotics-toolbox-python
- **价值**:DH 参数 / 运动学 / Jacobian / 路径规划 教科书代码,与 Peter Corke 仿真哲学一脉相承
- **借鉴点**:
  - DH 参数标准用法 → `references/simulation/forward-kinematics.md` 对接
  - 工作空间可视化(`workspace_cloud`)
  - Jacobian 数值求解(精度对照参考)
- **stack**:Python(numpy)
- **license**:LGPL-3.0
- **license_status**:pending(**LGPL 注意:调用 OK,fork 改 toolbox 本身要回馈**)
- **retrieved_at**:2026-06-02
- **借鉴注意**:**红线 #2** —— LGPL 调用没问题,fork 修改 Toolbox 本身要 LGPL 公开

### 7. Isaac Lab ★★★

- **URL**:https://github.com/isaac-sim/IsaacLab
- **价值**:NVIDIA 高保真仿真(GPU 物理),适合大规模 RL 训练
- **借鉴点**:
  - P3 后做强化学习训练步态时考虑
  - GPU 加速并行仿真(数千个 env)
- **stack**:Python + NVIDIA Isaac Sim
- **license**:BSD-3-Clause + NVIDIA EULA
- **license_status**:pending(**EULA 商用条款另议**)
- **retrieved_at**:2026-06-02
- **借鉴注意**:**红线 #4** —— NVIDIA EULA 商用条款限制,P3 评估时 hardware 团队 + 法务复核

---

## 借鉴流程

```
按场景选择 →
├─ 端到端跑通 demo:Bullet3 / PyBullet quickstart
├─ 严肃动力学/控制理论:Drake
├─ ROS2 + SDF 世界:Gazebo gz-sim
├─ MJCF 模型库:MuJoCo Menagerie
├─ DH/Jacobian 教科书:robotics-toolbox-python
└─ 大规模 RL 训练(P3+):Isaac Lab
```

---

## 与子技能联动

| 候选 | 关联子技能 | 关联点 |
|---|---|---|
| Bullet3 | `skills/urdf/` | URDF → pybullet.loadURDF 链路(M2 demo) |
| Gazebo | `skills/sdf/` | SDF 世界 → gz-sim 加载 |
| MuJoCo Menagerie | `skills/urdf/` | MJCF ↔ URDF 互转参考 |
| robotics-toolbox-python | `references/simulation/` + `peter-corke-perspective` skill | DH/IK 教学 |

---

## 典型场景

| 场景 | 推荐候选 |
|---|---|
| 第一个跑步态 demo | PyBullet + Bullet3 examples |
| 验证 IK 解析正确 | robotics-toolbox-python(numpy 直接验证) |
| ROS2 联合仿真 | Gazebo gz-sim + Champ |
| 高保真训练步态(P3+)| Isaac Lab |
| 学术参考 / 论文复现 | Drake + MuJoCo Menagerie |

---

## 待补充(P1+)

- **Genesis**(Stanford 新发布的物理引擎)— 关注度高,license/性能 P1 复评
- **MyoSuite**(DeepMind 肌肉骨骼仿真)— 仿生方向参考
- **Webots**(Cyberbotics)— 学术常用,license CC-BY-NC,商用受限
