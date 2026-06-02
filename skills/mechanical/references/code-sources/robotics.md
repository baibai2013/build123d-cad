# 机器人领域(Robotics)

> 场景:四足机器狗、机械臂、关节控制、IK、步态、URDF/SDF 描述、ROS2 栈。
> 核心原则:**机器狗整机几何先抄 stanford-pupper / mini-pupper;关节模组抄 ODRI;控制器思路抄 MIT Cheetah**。

---

## 候选源(6 个,P1-3 落定)

> 每条:URL / 价值 / 借鉴点 / license / license_status / retrieved_at。
> `license_status` 当前一律标 `pending` —— 由 cad-scraper agent 拉 LICENSE 文件复核后改 `verified` + 补 `commit_hash`。

### 1. stanford-pupper v3 ★★★★★

- **URL**:https://github.com/Nate711/StanfordQuadruped
- **价值**:同体型四足机器狗参考。腿部几何 + IK 解析(8 关节 / 4 腿)+ 三角步态 + 完整开源(STEP + 控制 + 硬件文档)
- **借鉴点**:
  - 腿部 link 长度比例(coxa / femur / tibia)→ 我们机器狗腿部尺寸初值
  - `pupper.py` 里 IK 解析公式可直接翻成 numpy(Apache 2.0 兼容)
  - 步态表(stance/swing 切换时序)→ 写进 `references/simulation/gait-planning.md` 时复用
- **stack**:Python + STM32
- **license**:MIT
- **license_status**:pending(cad-scraper 待复核 LICENSE 文件)
- **retrieved_at**:2026-06-02
- **借鉴注意**:整体结构布局参考即可,逐零件抄要在文件头标注 `# 参考: Nate711/StanfordQuadruped@<hash> (MIT)`

### 2. mini-pupper(MangDang)★★★★☆

- **URL**:https://github.com/mangdangroboticsclub/mini_pupper_2
- **价值**:商业小型四足机器狗,完整 ROS2 栈 + URDF + RPi 主控,装配尺寸成熟
- **借鉴点**:
  - URDF 描述完整,与本项目 P0-4 urdf 子技能 schema 对照
  - 机械文档(STEP + DXF)是 mini-pupper v2 公开件
  - launch 文件结构 → 后续 P3 ROS2 集成时参考
- **stack**:Python + ROS2
- **license**:Apache 2.0(代码)+ CC-BY-SA 4.0(机械文档)
- **license_status**:pending(机械文档 SA 传染需逐文件确认)
- **retrieved_at**:2026-06-02
- **借鉴注意**:**机械 STEP / DXF 抄了 → 衍生件必须 CC-BY-SA 公开**(红线 #3)。代码部分 Apache 2.0 与本仓兼容。

### 3. MIT Cheetah-Software ★★★★

- **URL**:https://github.com/mit-biomimetics/Cheetah-Software
- **价值**:MPC + WBC 控制器祖宗,工业级四足控制参考
- **借鉴点**:
  - 关节扭矩等级 / 电机选型(对照 MIT Cheetah 3 / Mini Cheetah 的 12 关节布局)
  - `Controllers/MPC/` 里 MPC 的代价函数构造(本项目 P3+ 控制时参考思路,不直接抄 C++)
- **stack**:C++ (Lcm)
- **license**:MIT
- **license_status**:pending
- **retrieved_at**:2026-06-02
- **借鉴注意**:hardware 部分(`hardware/` 目录)license 单独读,可能与代码不一致

### 4. open-dynamic-robot-initiative · Solo12 actuator hardware ★★★★

- **URL**:https://github.com/open-dynamic-robot-initiative/open_robot_actuator_hardware
- **价值**:开源关节模组(BLDC + planetary)全套机械文档(STEP + DXF + BOM)
- **借鉴点**:
  - 关节模组装配几何 → 我们自研关节直接 fork
  - BOM 标准件清单(M3 螺丝、608 轴承)→ 我们 BOM 对照
  - 减速比 + 力矩输出曲线 → 选电机时参考
- **stack**:机械(STEP/DXF)+ ODrive 控制
- **license**:CC-BY-SA 4.0
- **license_status**:pending(SA 传染必须复核)
- **retrieved_at**:2026-06-02
- **借鉴注意**:**抄机械件 → 衍生关节模组必须 CC-BY-SA 公开**(红线 #3)。若想保留闭源,只引用尺寸数字,不复制原 STEP。

### 5. Champ(quadruped framework)★★★

- **URL**:https://github.com/chvmp/champ
- **价值**:ROS2 通用四足栈,只要给 URDF 即可跑步态(适配多种四足机器狗)
- **借鉴点**:
  - 后续 P3 我们机器狗出 URDF 后,直接用 Champ 跑出第一个步态 demo
  - 步态参数 YAML 模板(stride / 频率 / 摆腿高度)
- **stack**:C++ + ROS2
- **license**:BSD-3-Clause
- **license_status**:pending
- **retrieved_at**:2026-06-02
- **借鉴注意**:BSD 兼容,可直接调用,不需 fork

### 6. ODrive 官方 examples ★★★

- **URL**:https://github.com/odriverobotics/ODrive/tree/master/docs/examples
- **价值**:BLDC FOC 接线 + 调参 + 编码器对零标准流程
- **借鉴点**:
  - 关节驱动开发时 motor calibration 流程
  - Python API 调用模板
- **stack**:Python(odrive 包)
- **license**:MIT
- **license_status**:pending
- **retrieved_at**:2026-06-02

---

## 借鉴流程

1. 走 Playbook 「代码库巡查」子步骤(§S2.5 / P2.0 / R4.0)
2. `python3 scripts/research/code_lookup.py robotics` 命中本文件
3. 按候选 ★ 优先级选 1~2 个仓库,read 借鉴点列出的具体文件
4. 借鉴时在生成代码文件头加注:
   ```python
   # 参考: <repo>@<commit> <path>#L<start>-<end> (<license>)
   # 例:Nate711/StanfordQuadruped@a1b2c3d pupper.py#L120-180 (MIT)
   ```
5. 若 `license_status: pending` → 先停手,跑 cad-scraper 复核 → 通过后再借鉴
6. 衍生件落到 `~/work/robot-dog/domains/mechanical/output/<task>/`,不在 skill 仓堆

---

## 与其他资源的分工

| 类型 | 路径 | 例子 |
|---|---|---|
| 整机参考 | 本文件 | stanford-pupper / mini-pupper / MIT Cheetah |
| 关节模组 | 本文件 §4 ODRI Solo12 | 自研关节抄机械件(注意 SA 传染) |
| 控制思路 | 本文件 §3 MIT Cheetah | 控制策略文献参考(C++ 代码不直接搬) |
| 步态算法 | `simulation.md` | Bullet3 / Champ 跑步态 |
| 机器人描述 | `skills/urdf/` 子技能 | URDF/SRDF/SDF 生成 |

---

## 待补充(P1+)

- **mini_pupper_v3**:发布后补充
- **Unitree A1/B1 开源仿真件**:Unitree SDK + URDF
- **Boston Dynamics Spot**:hardware 闭源,只能从论文借步态思路
