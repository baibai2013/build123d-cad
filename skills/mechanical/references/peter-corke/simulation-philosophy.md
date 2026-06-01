# Peter Corke 运动仿真哲学

> 机器人学教育家 Peter Corke 关于运动学、仿真和「Learn by doing」的思维框架。
> 对标 `dave-cowden/assembly-philosophy.md`（CAD 建模哲学），为运动仿真侧提供专家指导。

---

## 1. 「Learn by doing」— 可执行代码优先

Peter Corke 的核心教学哲学：**每个概念必须有可运行的代码**。

这是他三版教材 *Robotics, Vision and Control* 的立身之本——不是先推公式再写代码，而是先跑代码再理解公式。学生通过修改参数、观察结果来建立直觉，而不是被动阅读推导。

> *"Not your grandmother's toolbox — the Robotics Toolbox reinvented for Python"*
> — Corke & Haviland, ICRA 2021

**对 skill 的指导**：
- 每个 `references/simulation/*.md` 参考文档必须包含可粘贴运行的代码
- 每个 `assets/simulation/*.py` 示例必须独立可运行，不依赖未安装的框架
- 核心逻辑用纯 Python + numpy 实现，专业库（ikpy/roboticstoolbox）作为可选验证

**与 Dave Cowden 的对应**：

| Dave Cowden | Peter Corke |
|-------------|-------------|
| 「像机械师思考」— 代码读起来像加工工艺单 | 「Learn by doing」— 代码跑起来像实验室实验 |
| 每行代码，大声读出来机械师能懂 | 每段代码，粘贴运行后学生能看到结果 |

---

## 2. DH 参数是运动学的通用语言

就像 Dave Cowden 说「STEP 是 CAD 的通用语言」，Peter Corke 的立场是：**DH 参数是描述关节链的通用语言**。

### DH 四参数

| 参数 | 含义 | 类比 |
|------|------|------|
| θ (theta) | 关节转角（旋转关节的变量） | 机械师调节的「角度」 |
| d | 连杆偏移（沿 z 轴平移） | 零件间的「间距」 |
| a | 连杆长度（沿 x 轴平移） | 骨骼的「长度」 |
| α (alpha) | 连杆扭角（绕 x 轴旋转） | 关节轴间的「偏转」 |

### 四足单腿 DH 表（标准参考）

| 关节 | θ | d | a | α |
|------|---|---|---|---|
| hip (θ1) | θ1 | 0 | 0 | π/2 |
| upper_leg (θ2) | θ2 | d1 (肩偏移) | L1 (大腿长) | 0 |
| lower_leg (θ3) | θ3 | 0 | L2 (小腿长) | 0 |

### 代码即 DH 表

roboticstoolbox-python 的设计让代码与 DH 表一一对应：

```python
import roboticstoolbox as rtb
import numpy as np

# DH 表 → 代码（几乎是逐行翻译）
leg = rtb.DHRobot([
    rtb.RevoluteDH(d=0,    a=0,    alpha=np.pi/2),   # hip
    rtb.RevoluteDH(d=0.05, a=0.10, alpha=0),          # upper_leg
    rtb.RevoluteDH(d=0,    a=0.10, alpha=0),          # lower_leg
], name="quadruped_leg")

# FK：输入角度 → 输出末端位姿
T = leg.fkine([0, -np.pi/4, np.pi/2])
print(f"足端位置: {T.t}")  # 齐次变换矩阵的平移分量
```

**原则**：先用 DH 表标准化描述关节链，再谈优化。DH 表是「运动学的 STEP 文件」——标准、可交换、任何工具都能读。

---

## 3. 空间数学三件套：SE(3) / SO(3) / twist

### 核心概念

| 数学对象 | 含义 | Python 表达 | build123d 对应 |
|---------|------|------------|---------------|
| SO(3) | 纯旋转（3×3 正交矩阵） | `SO3.Rz(θ)` | `Rot(0, 0, θ)` |
| SE(3) | 刚体变换（旋转+平移，4×4） | `SE3.Tx(d) * SE3.Rz(θ)` | `Pos(d,0,0) * Rot(0,0,θ)` |
| twist | 速度/微分运动（6维向量） | `robot.jacob0(q)` | — |

### 关键洞察：build123d Location = SE(3)

build123d 的 `Location` 本质上就是一个 SE(3) 变换矩阵。这意味着：

```python
# 方法 A：numpy 矩阵链（数学验证）
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

T = dh_matrix(0, 0, 0, np.pi/2) @ dh_matrix(-np.pi/4, 0.05, 0.10, 0) @ dh_matrix(np.pi/2, 0, 0.10, 0)
foot_pos = T[:3, 3]

# 方法 B：build123d Location 链（CAD 验证）
from build123d import Pos, Rot, Location
loc = Pos(0,0,0) * Rot(0,0,0) * ...  # 对应的 Location 链
```

两种方法的结果必须一致——这就是「数学验证 + CAD 验证」的双重保障。

---

## 4. 正向思维 vs 逆向思维

### FK（正运动学）：关节角度 → 末端位置

- **唯一解**：给定一组关节角度，末端位置有且只有一个
- **计算简单**：矩阵连乘 T = T01 × T12 × T23
- **用途**：验证、可视化、动画

### IK（逆运动学）：末端目标 → 关节角度

- **多解/无解**：一个目标可能对应多种姿态，或根本不可达
- **计算复杂**：解析法需要几何推导，数值法需要迭代优化
- **用途**：步态控制、轨迹规划

### 策略选择

| 场景 | 方法 | 理由 |
|------|------|------|
| 三连杆（四足单腿） | 解析法 | 闭合形式，快速精确，约 30 行 Python |
| 六轴机械臂 | 解析法（Pieper 条件） | 满足条件时有闭合解 |
| 通用/冗余链 | 数值法（scipy/ikpy） | Jacobian 伪逆或优化 |
| 实时控制 | 专业框架（MoveIt/Pinocchio） | 需要避障、动力学 |

**Peter Corke 的原则**：解析解优先，因为它快、精确、可理解。数值法是兜底方案。

**与 Cowden 的类比**：
- IK 捕获的是「脚要到哪里」的设计意图 → 类似 Cowden 的选择器
- FK 只是「关节转了多少」的几何快照 → 类似 Cowden 反对的硬编码坐标

---

## 5. 分层验证架构

Peter Corke 的教学强调逐层验证，从数学正确性到物理合理性。

### 三层验证

| 层级 | 验证内容 | 工具 | 通过标准 |
|------|---------|------|---------|
| Layer 1: 数学验证 | FK→IK→FK 往返 | numpy/math | 误差 < 0.01mm |
| Layer 2: 可视化验证 | 姿态是否合理 | OCP show() / matplotlib | 人眼检查无穿模 |
| Layer 3: 物理验证 | 仿真中是否稳定 | PyBullet / MuJoCo | 不摔倒、不抖动 |

### 类比 CAD 验证

这与 `references/verify/cadcodeverify.md` 的三层架构完全对应：

| CAD 验证（Cowden） | 运动验证（Corke） |
|-------------------|------------------|
| BRep 有效性检查 | FK→IK→FK 数学一致性 |
| OCP 视觉检查 | 姿态可视化检查 |
| 制造约束验证 | 物理仿真验证 |

---

## 6. 诚实边界

仿照 Dave Cowden 的「说还不行，不说不可能」原则，明确 skill 在运动仿真方面的能力边界。

### 能力范围表

| 能力 | skill 提供 | 超出范围 → 推荐工具 |
|------|-----------|-------------------|
| 三连杆解析 IK | ✅ 纯 Python 实现 | — |
| 6-DOF 数值 IK | ✅ ikpy/scipy 参考代码 | 实时控制 → MoveIt / Pinocchio |
| 步态关键帧生成 | ✅ 贝塞尔轨迹 + IK | 自适应步态 → RL (legged_gym) |
| URDF 导出 | ✅ build123d→URDF 脚本 | 复杂机构 → onshape-to-robot |
| PyBullet 预览 | ✅ 加载 + 基本关节控制 | 高保真仿真 → MuJoCo / Isaac Sim |
| 动力学分析 | ❌ 不提供 | Pinocchio / Drake |
| 实时控制 | ❌ 不提供 | ROS2 / microROS |
| 强化学习步态 | ❌ 不提供 | legged_gym / walk-these-ways |

### 表达方式

```
❌ "这个 skill 不能做运动仿真"
✅ "skill 提供 FK/IK/步态的 Python 参考实现和 PyBullet 预览。
    生产级实时控制需要 ROS2，自适应步态需要强化学习框架。
    参见 references/simulation/ 了解衔接方式。"
```

---

## 7. Peter Corke 与 Dave Cowden 的哲学交汇

### 共同点

1. **Python 生态即超能力**：Cowden 选 Python 而非 DSL，Corke 从 MATLAB 迁移到 Python
2. **开源工具链**：Cowden 选 OCC 不选 Parasolid（免费），Corke 选 Python 不选 MATLAB（免费）
3. **实用主义 > 完美主义**：Cowden 说 "Favor progress over correctness"，Corke 说先跑起来再优化
4. **代码即文档**：Cowden 的 API 读起来像加工步骤，Corke 的 API 读起来像 DH 参数表

### 分工

```
Dave Cowden                           Peter Corke
「零件长什么样」                        「零件怎么动」
build123d → 几何真相源                  roboticstoolbox → 运动真相源
(geometry ground truth)                (kinematics ground truth)

         ┌──────────────────────────┐
         │   build123d Compound     │
         │   (Joint + Location)     │
         │                          │
         │   Cowden: 关节定义        │
         │   Corke: 运动学计算      │
         └──────────────────────────┘
                    │
                    ▼
         ┌──────────────────────────┐
         │   URDF                   │
         │   (几何 + 运动 → 统一)    │
         └──────────────────────────┘
                    │
              ┌─────┴─────┐
              ▼           ▼
         PyBullet     ROS/MoveIt
         (预览)        (生产)
```

### 交接点

build123d 的 `Joint` 系统是两位大师哲学的交汇处：
- **Cowden 视角**：Joint 是装配定位工具，`connect_to()` 计算一次性位置
- **Corke 视角**：Joint 定义了 DH 参数，是运动学链的基础

当用户从「零件建模」走向「让零件动起来」时，就是从 Cowden 领域走向 Corke 领域的时刻。

---

## 8. 推荐工具链

| 阶段 | 工具 | 安装 |
|------|------|------|
| 运动学原型 | numpy + math（纯 Python） | 内置 |
| 教学级验证 | roboticstoolbox-python | `pip install roboticstoolbox-python` |
| 快速 IK 原型 | ikpy | `pip install ikpy` |
| URDF 读写 | yourdfpy | `pip install yourdfpy` |
| 物理仿真 | PyBullet | `pip install pybullet` |
| 研究级动力学 | Pinocchio | `pip install pin` |
| 高保真仿真 | MuJoCo | `pip install mujoco` |

**核心依赖**只有 numpy——其余都是可选验证工具。这遵循 Corke 的原则：用最简单的工具先跑通，再用专业工具验证。

---

## 参考来源

| 来源 | 类型 |
|------|------|
| Peter Corke, *Robotics, Vision and Control* (3rd ed., 2023, Springer) | 教材 — DH/FK/IK 标准 |
| Corke & Haviland, "Not your grandmother's toolbox" (ICRA 2021) | 论文 — 工具设计哲学 |
| `petercorke/roboticstoolbox-python` GitHub | 开源库 — API 设计参考 |
| `petercorke/spatialmath-python` GitHub | 开源库 — SE(3)/SO(3) 实现 |
| `moribots/spot_mini_mini` GitHub (MIT License) | 四足 IK + 贝塞尔步态实现 |
| `stanfordroboticsclub/StanfordQuadruped` GitHub | 教学级四足步态 |
| `mike4192/spotMicro` GitHub | PyBullet 四足仿真 |
