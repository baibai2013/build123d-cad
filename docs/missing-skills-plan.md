# 缺失子技能规划方案(机器狗「虚拟验证→实体样机」全链路补全)

> 状态:**P0 孵化中**。`robot-dog-digital-twin`、`requirements-verification`
> 与 `actuator-sizing`、`pcb-mechanical-reliability`、`circuit-simulation`、
> `gait-optimization`、`motion-control`、`fea`、`wear-fatigue`、`mujoco-simulation` MVP 已落地;
> 其余条目仍是缺口分析与子技能规划,
> 后续逐个按 `docs/adding-new-subskill.md` 流程立项。
>
> 关联:现有 12 子技能(见 `SKILL.md`)、架构红线(见本文 §2)、handoff 约定(`shared/handoff-protocols.md`)。

---

## 0. 目标修正:先做实体前数字孪生闭环

本规划的核心目标不是"把 CAD 放进 3D 场景里看",而是建立一套机械狗**实体制造前**
的虚拟验证闭环:

```text
需求指标
  -> 虚拟样机
  -> 机械 / PCB / 电路 / 控制 / 步态 / 装配 / 制造 多域验证
  -> design_score + failure_report + next_iteration_plan
  -> 参数迭代
  -> gate 通过后再允许实体样机
```

第一版不追求完整工业数字孪生,先让系统能回答 3 个问题:

1. 这个机械狗设计现在能不能进入实体样机?
2. 不能的话,阻塞原因是什么?
3. 下一版应该改哪些参数?

定位上建议分两层:

| 层 | 定位 | 说明 |
|---|---|---|
| `build123d-cad` | 硬件设计工具箱 | 提供 CAD / PCB / URDF / SDF / viewer / PyBullet smoke / 制造预检等底层能力 |
| `robot-dog-digital-twin` | 机械狗数字孪生编排层 | 短期先放在 `build123d-cad` 下孵化;读取需求和各域 artifact,跑 gate,评分,归因,给下一轮参数建议 |

也就是说,短期不要把完整数字孪生总控塞进 `mechanical` 或 `simulation`,也不要让父
`build123d-cad` 变成项目管理器。`robot-dog-digital-twin` 可以先作为 `build123d-cad`
下的编排子域 / 子技能孵化,但必须保持"只编排、只读 artifact、不替代底层子技能"的边界;
闭环成熟后再评审是否拆成独立 super skill 或独立仓库。

---

## 1. 背景:一只机器狗从 0 到能跑,要走完哪些环节

把全流程拆成 6 大阶段,贯穿 机械 / 电子 / 嵌入式 / 控制 / 系统 五条线:

```
①需求定义 → ②机械设计 → ③电子设计 → ④嵌入式/固件 → ⑤运动控制+仿真 → ⑥制造装配+整机调试
```

当前 skill 覆盖度对照:

| 阶段 | 环节 | 现有子技能 | 覆盖 |
|---|---|---|---|
| ① 需求/总体 | 形态/自由度/负载/续航/成本目标 | —— | ❌ 无 |
| ② 机械 | 参数化建模 / 装配 / 标准件 / 减重 | `mechanical` `parts-catalog` | ✅ 强 |
| ② 机械验证 | 受力 / 疲劳 / 模态(FEA) | `fea` | ✅ MVP |
| ② 机械可靠性 | 磨损 / 轴承寿命 / 齿轮寿命 / 足垫磨耗 / 线束弯折 | `wear-fatigue` | ✅ MVP |
| ③ 电子 | 原理图 / PCB / BOM / 出件下单 | `pcb` `electronics-bom`(占位) | 🟡 板能造,选型弱 |
| ③ PCB 机械可靠性 | PCB 刚度 / 挠曲 / 固定孔应力 / 连接器受力 / 机身干涉 | `pcb-mechanical-reliability` | ✅ MVP |
| ③ 电路验证 | 电源预算 / 电流峰值 / 保护电路 / 热风险 / SPICE 粗验 | `circuit-simulation` | ✅ MVP |
| ④ **固件** | MCU 驱动 / FOC 电机环 / 总线协议 / 标定 | —— | ❌ **完全空白** |
| ⑤ 描述 | URDF / SRDF / SDF | `urdf` `srdf` `sdf` | ✅ 强 |
| ⑤ 仿真 | 动力学 / 步态 / 稳定性 | `simulation`(pybullet MVP) | 🟡 未到真步态 |
| ⑤ 运控算法 | FK/IK / 步态生成 / 平衡 / MPC | `mechanical`(仅"指引") | ❌ 无可执行实现 |
| ⑥ 制造 | 3D 打印 / 钣金激光 / 切片 | `gcode` `sendcutsend` `bambu-labs` | ✅ 强 |
| ⑥ 整机调试 | 标定 / 上电测试 / 数据回采 | —— | ❌ 无 |

**结论:当前 skill 把「画得对 + 造得出 + 仿真里动得对」三段闭环做到相当成熟,
但在「仿真模型 ↔ 真实会动的硬件」之间有一道断崖 —— 固件/嵌入式/实时控制层。**

对"先虚拟验证再做实体"这个目标,还额外缺 4 类能力:

- **需求合同与验证矩阵**:把"什么叫设计够好"量化成 gate 和阈值。
- **多域验证 artifact**:机械、PCB、电路、磨损、动力学、步态都要输出机器可读报告。
- **失败归因与参数建议**:不仅告诉用户失败,还要说明应改腿长、电池位置、PCB 固定点、步态参数等哪一类参数。
- **迭代评分**:每一版设计都能比较上一版是否变好,但最终放行由 gate 决定,不是由分数单独决定。

---

## 2. 关键前提:断崖是架构红线主动划的,不是漏掉

父 `SKILL.md` 与 `shared/multi-skill-router.md` 明确写了红线:

> ❌ 不涉及固件/嵌入式/控制层(机器人描述只是描述,控制靠 ROS/MuJoCo/Gazebo 下游)

所以"固件缺失"目前**是有意的边界**。真正要拍板的不是"怎么补固件",而是:

> **要不要打破这条红线,让 skill 从「数字孪生」延伸到「真实控制」?**

本文改为按阶段推进:

- **P0(虚拟闭环)**:需求合同 + artifact schema + orchestrator + 执行器/PCB/电路/步态的最小规则验证。
- **P1(验证加深)**:FEA、磨损疲劳、MuJoCo、真步态优化,把粗规则逐步替换成可信仿真/求解。
- **P2(真实控制)**:固件、sim2real、整机 bring-up。只有当前两阶段跑通后才评审是否打破红线。

> 本文 §5 给出跨域依赖关系;§6 按 P0/P1/P2 给优先级排序。

---

## 2.1 实体前虚拟验证域

数字孪生闭环应拆成 6 个虚拟验证域。每个域都要有输入、验证方法、机器可读输出和
blocker 判定,不能只产自然语言总结。

| 验证域 | 要验证什么 | 典型方法 | 最小输出 |
|---|---|---|---|
| 机械结构 | 强度、刚度、机身/腿部变形、装配干涉、跌落冲击 | CAD 质量属性、碰撞检查、FEA、跌落工况 | `mechanical_report.json`、`fea_report.json`、`collision_report.json` |
| PCB 机械可靠性 | PCB 刚度、挠曲、固定孔应力、支撑柱布局、连接器受力、外壳干涉 | PCB STEP + 机身 STEP 装配检查、简化板挠曲/支撑点规则、连接器载荷规则 | `pcb_fit.json`、`pcb_reliability_report.json` |
| 磨损寿命 | 齿轮、轴承、连杆、足垫、关节间隙、线束弯折、连接器松脱 | 载荷谱 + 运动轨迹 + 材料/标准件参数 + 经验寿命模型 | `wear_report.json`、`fatigue_report.json`、`maintenance_interval.md` |
| 电路合理性 | ERC/DRC、电源裕量、电流峰值、保护电路、热风险、EMI 初筛 | tscircuit/EDA 检查、电源预算、SPICE 粗验、热估算 | `circuit_check.json`、`power_budget.json`、`thermal_report.json` |
| 机器人动力学 | 站立、跌落、翻倒、关节限位、扭矩需求、地面接触、重心合理性 | PyBullet smoke、MuJoCo 高保真场景、扰动测试 | `sim_result.json`、`torque_margin.json`、`trajectory.json` |
| 行走算法 | FK/IK、步态稳定性、斜坡/小障碍、足端打滑、body roll/pitch、能耗 | IK 单测、步态参数搜索、仿真日志评分 | `gait_score.json`、`controller_params.yaml`、`next_gait_params.yaml` |

术语上,"PCB 的硬度"在工程报告里建议拆成:

```text
PCB 刚度 / 挠曲 / 固定孔应力 / 支撑柱布局 / 连接器局部受力 / 焊点应力风险
```

这样后续可以逐步从规则检查升级到真实结构仿真,而不改变上层 artifact 名称。

---

## 2.2 实体样机前 gate

数字孪生不能只"跑了一堆报告",必须有清晰 gate。建议第一版使用:

| Gate | 名称 | 放行条件 |
|---|---|---|
| G0 | `requirements_ready` | `requirements.yaml` 和 `verification_matrix.yaml` 完整,关键目标有数值阈值 |
| G1 | `virtual_architecture_ready` | 架构方案、质量预算、功耗预算、执行器初选、PCB/电池/关节布局存在 |
| G2 | `digital_prototype_ready` | CAD/PCB/URDF 或 MJCF/仿真场景齐全,能被 viewer 和 simulation 读取 |
| G3 | `multi_domain_validation_passed` | 机械、PCB、电路、动力学、步态最小验证均无 blocker |
| G4 | `iteration_score_passed` | `design_score.total >= 85`,且关键域分数不低于各自底线 |
| G5 | `physical_prototype_allowed` | G0-G4 全通过,制造包齐全,仍需人工确认后进入实体制造 |

规则:

- 任一 blocker 未清除,不得进入实体样机。
- `design_score` 只用于版本排序和优化方向;是否放行由 gate 决定。
- 真实下单、打印、烧录、上电、电机转动都必须是显式确认动作,不能由数字孪生自动执行。
- 第一版 gate 可以只覆盖简化机械狗;后续逐步把简化规则替换成高保真验证。

---

## 3. 缺失子技能规划(逐个定边界 / 工具链 / handoff)

每个子技能遵守现有架构原则:**自治**(独立 SKILL.md + tests)、**零互引用**、
**文件标准接口**(走 `output/<task>/` 路径约定,不做函数调用)。

### 3.0 `digital-twin-orchestrator` — 数字孪生总控(先在本仓库孵化)

**落地状态(2026-06-06)**:已以 `skills/robot-dog-digital-twin/` MVP 落地,包含
artifact 收集、G0-G5 gate、设计评分、failure report、next iteration plan、示例和 pytest。

**定位**:读取需求、artifact 和各域验证报告,运行 G0-G5 gate,生成 `design_score`、
`failure_report` 和下一轮参数建议。它不直接画 CAD、不直接写 PCB、不直接控制仿真器。

**建议边界**:

| 模块 | 内容 |
|---|---|
| 需求读取 | 读取 `requirements.yaml`、`verification_matrix.yaml`、`architecture.yaml` |
| artifact 收集 | 收集 mechanical / electrical / simulation / control / manufacturing 下的报告 |
| gate runner | 按 G0-G5 输出 `gate_report.json` / `gate_report.md` |
| 评分 | 确定性规则优先,输出 `design_score.json` |
| 失败归因 | 汇总 blocker、风险、缺失 artifact,输出 `failure_report.md` |
| 下一版建议 | 生成 `next_iteration_plan.md`,说明应改哪些参数及理由 |

**关键原则**:

- 不 import 其他子技能代码,只读文件 artifact。
- 不直接替代 `mechanical`、`pcb`、`simulation` 等技能。
- 不凭感觉允许实体制造,必须看 gate。
- 建议先作为 `build123d-cad` 下的 `robot-dog-digital-twin` 编排层起步;成熟后再评审是否独立。

**最小输出**:

```text
reports/digital_twin/
  gate_report.json
  gate_report.md
  design_score.json
  failure_report.md
  next_iteration_plan.md
```

**建议仓内落点**:

```text
skills/robot-dog-digital-twin/
  SKILL.md
  README.md
  references/
    workflow.md
    gates.md
    scoring.md
    failure-taxonomy.md
    quadruped-mvp.md
  scripts/
    collect_artifacts.py
    run_gate.py
    score_design.py
    propose_next_iteration.py
  tests/
  examples/
    quadruped_mvp/
```

---

### 3.0.1 `requirements-verification` — 需求合同与验证矩阵

**落地状态(2026-06-06)**:已以 `skills/requirements-verification/` MVP 落地,包含
合同模板生成、stdlib-only 校验器、示例 `quadruped_mvp/`、validation report 和 pytest。

**定位**:把"比较好的机械狗版本"转成可验证合同。没有需求合同,后续评分会变成主观判断。

**边界(做什么)**:

- 定义目标:质量、负载、速度、续航、尺寸、坡度、成本、安全温度、电流上限。
- 定义验证矩阵:每个目标由哪个域验证、阈值是多少、是否 blocker。
- 定义风险登记:哪些目标暂时只能粗验,哪些必须实体测试。
- 定义版本冻结规则:什么时候允许进入 G5。

**产物**:

```text
requirements.yaml
verification_matrix.yaml
risk_register.md
architecture.yaml
```

**示例指标**:

```yaml
dynamics:
  stand_stable_seconds:
    limit_min: 30
    source: simulation
  flat_walk_no_fall:
    required: true
    source: gait_simulation
  max_joint_torque_margin_pct:
    limit_min: 20
    source: actuator_sizing
```

---

### 3.0.2 `actuator-sizing` — 执行器选型与扭矩/速度/热裕量

**落地状态(2026-06-08)**:已以 `skills/actuator-sizing/` MVP 落地,包含
需求/架构读取、简化 hip/knee/ankle 扭矩估算、速度裕量、连续扭矩热裕量、blocker 输出、
示例 `quadruped_mvp/` 和 pytest。第一版是确定性早期 gate,不替代 MuJoCo 或实机测量。

**定位**:机械狗成败最核心的早期验证之一。腿长、体重、步态速度、减速比、关节限位都要
先过执行器裕量检查,否则后面 CAD 再漂亮也走不起来。

**边界(做什么)**:

- 按质量、腿长、目标速度、步态和坡度估算 hip/knee/ankle 峰值扭矩。
- 检查连续扭矩、峰值扭矩、速度、减速比、热裕量。
- 输出每个关节的 margin 和 blocker。
- 给机械/步态参数修改建议,如缩短 stride、调整腿长、降低 body height、换电机或减速器。

**产物**:

```text
actuator_spec.yaml
torque_margin.json
actuator_sizing_report.md
```

**后续增强**:

- 增加真实候选执行器列表和减速器效率曲线。
- 从 `simulation` / `gait-optimization` 读取载荷谱,替换当前简化动态系数。
- 引入电机热时间常数、降额曲线和电池电压下限。
- 输出面向 `robot-dog-digital-twin` 的下一轮参数建议,如降低速度、缩短步幅或调整腿长。

---

### 3.1 `firmware` — 嵌入式/电机控制固件(P2,最大断崖)

**定位**:把 `pcb` 造出来的驱动板/主控板"装上能跑的代码"。从 MCU 工程脚手架到电机闭环。

**边界(做什么)**:

| 模块 | 内容 |
|---|---|
| MCU 工程脚手架 | STM32(CubeMX/HAL)、ESP-IDF 工程生成;引脚分配/时钟树由 `pcb` BOM+netlist 喂入 |
| 电机控制 | BLDC FOC 电流环 / 位置-速度-力矩三环;参考 [SimpleFOC](https://simplefoc.com)、ODrive、moteus 思路 |
| 编码器接口 | SPI(AS5047P 类)/ ABZ / 磁编码器读取与偏置标定 |
| 总线协议 | CAN-FD / EtherCAT 帧格式定义 + 收发代码 + 状态机(对齐 `pcb` 的连接器/收发器选型) |
| 关节标定 | 零位标定、磁编码器偏置、calibration hash 生成与持久化 |
| 实时性 | 控制环周期(250 Hz~1 kHz)、jerk 限幅、L1/L2/L3 降级状态机 |

**不做什么**:不做高层步态决策(归 `motion-control`);不做布线/选型(归 `pcb`)。

**工具链(待调研核实,先列候选)**:
- 电机控制框架:SimpleFOC(Arduino/PlatformIO,LLM 语料多)/ 裸 HAL FOC
- 构建:PlatformIO CLI(可 headless build + 静态检查) / STM32CubeIDE headless
- 仿真/自验:Renode(MCU 指令级仿真,可 CI 跑固件而无需实体板) / QEMU
- 单元测试:Ceedling(C 单测) / Unity

**handoff(上下游)**:
- 上游 `pcb` → `firmware`:`output/<task>/electrical/` 的 netlist + BOM(MCU 型号/引脚/外设)
- 上游 `mechanical` / `urdf`:关节限位、减速比、零位定义(标定用)
- 下游 `firmware` → `simulation`:导出控制环参数/期望轨迹,做 sim↔real 对比
- 产物:`output/<task>/firmware/` —— 工程目录 + `*.elf`/`*.bin` + `can-frames.md` + `calibration.json`

**风险**:固件强依赖具体硬件,headless 可验证性差 → 用 Renode/QEMU + 单测把"能编译+逻辑对"
闭环,实体烧录/上电明确标为 gate(类似 `bambu-labs` 的 `--execute --confirm`)。

---

### 3.2 `motion-control` — 运动控制算法(可执行版)

**落地状态(2026-06-08)**:已以 `skills/motion-control/` MVP 落地,包含 `motion_plan.yaml`
metadata 输入、2-link 平面腿 IK、关节限位/可达性 blocker、trot/walk/bound 相位轨迹生成、
`trajectory.json`、`controller_params.yaml`、示例 `quadruped_mvp/` 和 pytest。第一版是可执行
IK/轨迹文件合同,不替代 3D 全身运动学、MPC/WBC、状态估计或实时固件控制。

**定位**:把 `mechanical` 里只有"指引"的运动学/步态,做成**能跑的库**,在 `simulation` 里验证,
再下发给 `firmware` 执行。填补 `simulation` 现在"相位正弦 MVP"到"真步态"的距离。

**边界(做什么)**:
- FK/IK 可执行库:闭式解 + 数值解(DLS)+ 奇异规避;输出 `< Nμs` 求解时间基准
- 步态生成器:trot / walk / bound;相位机 + Bezier 摆动轨迹 + 落足点规划
- 平衡控制:质心轨迹规划;VMC / WBC / MPC(按复杂度分阶段)
- 地形适应:落足点调整(进阶,可后置)

**工具链(候选)**:
- 运动学:Pinocchio(C++/Python,工业级动力学库) / 自写闭式解(腿这种低 DOF 够用)
- 仿真验证:复用 `simulation` 的 pybullet,后续可加 MuJoCo
- 参考:Peter Corke Robotics Toolbox(`mechanical/references/peter-corke/` 已有哲学,这里做实现)

**handoff**:
- 上游 `urdf`(运动学链)+ `simulation`(动力学验证环境)
- 下游 `firmware`(把期望关节角/力矩轨迹下发)、`simulation`(回放验证)
- 产物:`output/<task>/motion/` —— `ik.py`/`gait.py` + `trajectory.json`(对齐 simulation 已有格式)

**与现状的关系**:`simulation` 的 `gait` 模式应改为**消费** `motion-control` 的轨迹,
而非自己内嵌正弦驱动 → 两者解耦,各管"算"与"验"。

**后续增强**:

- 从 `urdf` / `architecture.yaml` 自动生成 link length、joint limits 和足端默认目标。
- 增加 3D hip ab/adduction、Jacobian/DLS IK、奇异规避和轨迹平滑。
- 让 `simulation` / `mujoco-simulation` 直接消费 `control/trajectory.json`。
- 增加 VMC/WBC/MPC 或 terrain-adaptive foot placement 作为后续 controller 层。

---

### 3.3 `fea` — 结构有限元验证(P1,结构验证加深)

**落地状态(2026-06-08)**:已以 `skills/fea/` MVP 落地,包含 `fea_cases.yaml`
metadata 输入、应力/安全系数/位移/模态频率/跌落冲击规则检查、示例 `quadruped_mvp/`
和 pytest。第一版先建立稳定 artifact 和 gate,不替代真实求解器、网格收敛或实体载荷测试。

**定位**:给 `mechanical` 的几何做应力/疲劳/模态分析。机器狗腿是**动态冲击载荷件**,
没 FEA 等于盲减重。补上后减重才有依据。

**边界(做什么)**:
- 静力学:应力/应变/安全系数(SF)
- 模态分析:固有频率(避开步态激励频率)
- 疲劳:动态循环载荷下的寿命估算(进阶)
- 工况:落地冲击、最大扭矩、自重

**工具链(候选,均可 headless)**:
- 求解器:CalculiX(开源,Abaqus 语法,CLI 友好) / FEniCS(Python,适合脚本化)
- 网格:Gmsh(STEP→mesh) / FreeCAD FEM workbench headless
- 前处理:从 `mechanical` 的 STEP 直接吃,材料库对齐 `parts-catalog`(7075/PETG 等)

**handoff**:
- 上游 `mechanical`:`output/<task>/*.step` + 载荷工况定义
- 下游回 `mechanical`:减重/加厚建议(闭环迭代)
- 产物:`output/<task>/fea/` —— `report.json`(SF/频率/位移)+ 云图 PNG + checklist

**后续增强**:

- 从 `mechanical` 的 STEP 和材料 metadata 自动生成 `fea_cases.yaml`。
- 接入 Gmsh 生成网格,再接 CalculiX 或 FreeCAD FEM headless 求解。
- 增加网格收敛、云图 PNG 和多工况报告。
- 将 `wear-fatigue` 的载荷谱接入疲劳寿命评估。

---

### 3.3.1 `wear-fatigue` — 磨损/疲劳/维护周期估算

**落地状态(2026-06-08)**:已以 `skills/wear-fatigue/` MVP 落地,包含 `wear_inputs.yaml`
metadata 输入、齿轮接触应力/寿命、轴承 L10、足垫磨耗、关节限位撞击、螺丝松动、线束弯折/
夹线、连接器插拔寿命/振动锁/拉力释放规则检查、示例 `quadruped_mvp/` 和 pytest。第一版是
确定性早期寿命 gate,不替代真实耐久测试、供应商寿命曲线、接触磨损模型或疲劳试验。

**定位**:回答"这个结构会不会很快磨坏"。磨损不能只靠静态 CAD,需要读取运动轨迹、
接触力、材料和标准件参数。

**边界(做什么)**:

| 部位 | 验证内容 |
|---|---|
| 齿轮/减速器 | 接触应力、齿面速度、润滑假设、材料、寿命估算 |
| 轴承 | 径向/轴向载荷、L10 寿命、转速、安装误差 |
| 足垫 | 地面摩擦、冲击、磨耗、可替换设计 |
| 关节外壳 | 限位撞击、螺丝松动、冲击载荷 |
| 线束 | 最小弯折半径、运动包络、磨擦、夹线风险 |
| 连接器 | 插拔寿命、振动松脱、拉力释放 |

**handoff**:

- 上游 `mechanical` / `urdf`:几何、关节限位、材料、标准件。
- 上游 `simulation` / `gait`:轨迹、接触力、载荷谱。
- 下游 `digital-twin-orchestrator`:寿命 blocker 和维护建议。
- 产物:`wear_report.json`、`fatigue_report.json`、`maintenance_interval.md`、`wear_fatigue_report.md`。

**后续增强**:

- 从 `simulation` / `gait-optimization` 的真实轨迹和接触力自动生成 `wear_inputs.yaml`。
- 接入标准件/供应商轴承、减速器和连接器寿命曲线。
- 引入载荷谱累计损伤、足垫材料磨耗模型和线束弯折循环寿命。
- 将维护周期 blocker 纳入 `robot-dog-digital-twin` 的 G3/G5 放行规则。

---

### 3.3.2 `pcb-mechanical-reliability` — PCB 结构可靠性

**落地状态(2026-06-08)**:已以 `skills/pcb-mechanical-reliability/` MVP 落地,包含
`pcb_mechanical.yaml` metadata 输入、板厚/支撑柱/固定孔/装配间隙检查、简化 PCB 挠曲估算、
连接器支撑/线束弯折/拉力释放规则、示例 `quadruped_mvp/` 和 pytest。第一版是规则检查,
不替代 PCB STEP 装配检查、FEA 或实体振动/跌落测试。

**定位**:机械狗的 PCB 不只是"电路板能画出来",还要在机身里扛得住振动、跌落、连接器插拔
和线束拉力。这里验证用户关心的"PCB 硬度/刚度/是否合理"。

**边界(做什么)**:

- PCB STEP 放入机身,检查板边、连接器、电池、电机线束、外壳和关节运动包络干涉。
- 检查安装孔、支撑柱数量与位置、连接器附近是否有支撑。
- 粗估 PCB 挠曲和固定孔局部应力风险。
- 检查连接器朝向、插拔空间、线束弯折半径、拉力释放。
- 输出 blocker:如连接器顶外壳、XT30 附近无支撑、板子跨度过大、孔边距不足。

**handoff**:

- 上游 `pcb`:board STEP、连接器位置、BOM、板厚。
- 上游 `mechanical`:机身 STEP、支撑柱、螺丝孔、电池/电机空间。
- 下游 `mechanical`:支撑柱/让位/固定点修改建议。
- 产物:`pcb_fit.json`、`pcb_reliability_report.json`、`connector_clearance.json`。

**后续增强**:

- 从 `pcb` 的 board STEP / connector metadata 自动生成 `pcb_mechanical.yaml`。
- 从 `mechanical` 的机身 STEP / 支撑柱 / 电池仓自动生成间隙和支撑输入。
- 引入真实板材叠层、FR4 弹性模量、螺丝预紧和跌落载荷谱。
- 升级为 PCB STEP + 机身 STEP 的装配干涉检查。

---

### 3.3.3 `circuit-simulation` / `power-thermal` — 电路与电源热合理性

**落地状态(2026-06-08)**:已以 `skills/circuit-simulation/` MVP 落地,包含
`circuit_requirements.yaml` metadata 输入、ERC/DRC 状态收集、电池/保险丝/电源轨/电机驱动电流
预算、急停/欠压/TVS/反接/大电容保护检查、简化器件温升估算、示例 `quadruped_mvp/`
和 pytest。第一版是规则检查,不替代完整 SPICE、EMI/信号完整性、真实热测试或实体上电。

**定位**:回答"电路是否合理"。第一版不必完整 SPICE 全电路,先把机械狗最容易出问题的
电源、电机驱动、电流峰值、保护和热风险做成可验规则。

**边界(做什么)**:

- ERC/DRC 结果收集和 blocker 化。
- 电源轨预算:电池电压、峰值电流、DC-DC 裕量、LDO 热耗散。
- 电机驱动峰值电流和连续电流检查。
- 欠压、反接、保险丝、急停、TVS、续流路径等保护检查。
- MOSFET/驱动芯片/电源器件热风险估算。
- 对高风险网段做 SPICE 或简化 transient 预检(后续扩展)。

**产物**:

```text
circuit_check.json
power_budget.json
thermal_report.json
protection_checklist.md
```

**后续增强**:

- 从 `pcb` 的 `circuit.json` / BOM 自动生成 `circuit_requirements.yaml`。
- 从 `electronics-bom` 获取器件电流、功耗、封装和热阻参数。
- 对高风险电源轨接入 SPICE transient 粗验。
- 增加电机再生、电池内阻、线束压降、MOSFET SOA 和保险丝熔断曲线。

---

### 3.4 `electronics-bom` — 电子选型上游(填满现有占位)

**定位**:现在是 P3 占位。填满后给 `pcb` 的 `tsci import` 喂 curated 料库,
解决"选哪颗 MCU/驱动/编码器"靠临场判断的问题。

**边界(做什么)**:
- curated 料库:按"机器人常用"分类的 MCU / 电机驱动 / 编码器 / 传感器 / 电源
- 选型决策表:性能/价格/库存/封装 多维对照(类似 robot 项目里 DEC-01~07 的产物形态)
- JLCPCB/LCSC 接入:复用 `pcb` 已选的 `jlcpcb-mcp`(查料/库存/报价免 key)
- 功耗/成本预算:喂给系统层(§3.5)

**handoff**:
- 下游 `pcb`(选型结果 → `tsci import` 封装)、`firmware`(MCU/外设确定)
- 产物:`output/<task>/bom/` —— `bom.json` + `selection-rationale.md`

**注**:这是**已有占位的填充**,不是新建,成本最低。

---

### 3.4.1 `mujoco-simulation` — 高保真腿足动力学

**落地状态(2026-06-08)**:已以 `skills/mujoco-simulation/` MVP 落地,包含
`mujoco_scenarios.yaml` metadata 输入、stand/walk_flat/slope/drop 等场景门禁、姿态/打滑/
扭矩裕量/接触穿透/能耗规则检查、MJCF 示例、`mujoco_result.json`、每场景 `*.sim_result.json`
和 pytest。第一版是 MuJoCo 文件合同与 deterministic metadata backend,不声称已经运行真实
MuJoCo 求解器;后续可在不改上层 artifact 的前提下替换成真实 `mujoco` Python backend。

**定位**:PyBullet 继续做 CI smoke,MuJoCo 用于认真迭代步态、接触、摩擦、执行器和地形扰动。

**为什么需要**:

- 腿足机器人对接触模型敏感,PyBullet 适合快速发现穿地、爆炸、翻倒等粗问题。
- MuJoCo 更适合大量参数搜索、执行器建模、摩擦地形、步态控制迭代。
- 后续 `gait-optimization` 可以在 MuJoCo 中批量跑候选参数。

**边界(做什么)**:

- URDF/SDF → MJCF 或直接读取 MJCF。
- 场景:stand、walk_flat、slope、step_obstacle、drop、push_disturbance。
- 输出稳定性、接触、关节扭矩、能耗、轨迹、失败时刻。

**产物**:

```text
simulation/mujoco/
  robot.xml
  scenarios/*.yaml
  results/*.sim_result.json
  trajectories/*.trajectory.json
reports/
  mujoco_result.json
  mujoco_validation_report.md
```

**后续增强**:

- 接入真实 `mujoco` Python backend,读取 `simulation/mujoco/robot.xml`。
- 从 `urdf`/`sdf` 转换或同步生成 MJCF。
- 输出真实接触力、穿透、关节力矩、能耗和轨迹。
- 将 `mujoco_result.json` 接入 `gait-optimization` 的真实评分输入。

---

### 3.4.2 `gait-optimization` — 步态参数搜索与评分

**落地状态(2026-06-08)**:已以 `skills/gait-optimization/` MVP 落地,包含
`gait_validation.yaml` metadata 输入、IK/相位/站立/慢走/roll/pitch/打滑/扭矩裕量/速度/能耗
确定性评分、候选步态参数选择、示例 `quadruped_mvp/` 和 pytest。第一版是规则评分和参数建议,
不替代 MuJoCo、MPC、强化学习或实体行走测试。

**定位**:回答"行走算法是否合理"。不是看模型能不能动,而是按分级场景量化稳定性、速度、
足端打滑、body roll/pitch、扭矩裕量和能耗。

**验证等级**:

| Level | 验证项 |
|---|---|
| L0 | 单腿 IK 正确 |
| L1 | 四腿空中摆动轨迹正确 |
| L2 | 平地站立 30 秒不倒 |
| L3 | 平地慢走不倒 |
| L4 | 斜坡行走 |
| L5 | 小台阶 |
| L6 | 外力推扰恢复 |
| L7 | 不同摩擦地面 |
| L8 | 低电量/电机降额下仍安全 |

**评分指标**:

```yaml
gait_validation:
  no_fall: true
  max_body_roll_deg: 8
  max_body_pitch_deg: 8
  foot_slip_ratio_max: 0.12
  joint_torque_margin_pct_min: 20
  average_speed_mps_min: 0.5
  cost_of_transport_max: 2.5
```

**产物**:

```text
gait_score.json
best_gait_params.yaml
failed_candidates.json
trajectory.json
```

**后续增强**:

- 从 `simulation` 的真实 `sim_result.json` / `trajectory.json` 自动生成 `gait_validation.yaml`。
- 从 `actuator-sizing` 读取 `torque_margin.json`,替换手写扭矩裕量。
- 增加 slope、step obstacle、push disturbance、friction variation 场景。
- 接入 MuJoCo 批量参数搜索,把当前候选评分升级为真实仿真搜索。

---

### 3.5 `system` — 需求/系统工程层(顶层规划,可选但价值高)

**定位**:现在每个子技能都很能干,但缺一个把它们串成"一只完整狗"的顶层入口。

**边界(做什么)**:
- 总体设计:形态、自由度方案、负载/续航/成本目标
- 预算分解:功耗预算、质量预算、成本模型(下发给各域当约束)
- 架构选型:电气架构(集中 vs 分布式总线)、自由度配置
- 需求→子技能任务分解 + handoff 编排

**工具链**:主要是文档/表格驱动(YAML 规格 + 决策记录),轻代码。

**handoff**:它是**最上游**,产物是约束规格,下发给 mechanical/electronics-bom/firmware/motion-control。
- 产物:`output/<task>/system/` —— `requirements.yaml` + `budgets.yaml` + `architecture.md`

**注**:与 super skill"父级只路由"哲学略有张力 —— 它不是路由,是"规划编排"。
当前建议不要把这层塞进父 `SKILL.md` 主流程,而是放到本仓库 `robot-dog-digital-twin`
子域中孵化,以文件 artifact 调用既有子技能。

---

### 3.6 `integration` — 整机集成与上电调试(够不到,先不做)

**定位**:bring-up checklist、HIL(硬件在环)、实物数据回采对比仿真。

**现实**:属于"有了实体硬件之后"的环节,headless/CI 几乎无法覆盖,强依赖实物。
**建议**:**暂不立项**,等 P2 的 `firmware` 落地、有真实板子后再议。可先在 `firmware`/`simulation`
里以"sim↔real 对比"的 handoff 占位。

---

## 4. 添加缺失 skill 后的目录结构规划

短期仍按现有 monorepo 方式扩展:所有新增能力先放在 `build123d-cad/skills/` 下,
每个子技能保持 `SKILL.md + README.md + references/ + scripts/ + tests/` 骨架。
`robot-dog-digital-twin` 是编排子技能,负责串联各域;其他新增 skill 是可独立测试的域验证器。

### 4.1 目标目录树

```text
build123d-cad/
├── SKILL.md
├── README.md
├── docs/
│   ├── adding-new-subskill.md
│   ├── architecture.md
│   ├── missing-skills-plan.md
│   └── robot-dog-digital-twin/
│       ├── architecture.md
│       ├── gate-policy.md
│       ├── artifact-contracts.md
│       └── mvp-roadmap.md
├── evals/
│   ├── bench-digital-twin-mvp.yaml
│   ├── bench-gait-optimization.yaml
│   └── bench-pcb-reliability.yaml
├── shared/
│   ├── handoff-protocols.md
│   ├── multi-skill-router.md
│   ├── dependencies.md
│   ├── schemas/
│   │   ├── requirements.schema.json
│   │   ├── verification_matrix.schema.json
│   │   ├── design_artifacts.schema.json
│   │   ├── actuator_spec.schema.json
│   │   ├── mass_properties.schema.json
│   │   ├── pcb_fit.schema.json
│   │   ├── circuit_check.schema.json
│   │   ├── power_budget.schema.json
│   │   ├── sim_scenario.schema.json
│   │   ├── sim_result.schema.json
│   │   ├── gait_score.schema.json
│   │   └── design_score.schema.json
│   └── python/
│       └── digital_twin_artifacts/
│           ├── README.md
│           └── src/digital_twin_artifacts/
│               ├── __init__.py
│               ├── paths.py
│               ├── load.py
│               └── validate.py
├── skills/
│   ├── mechanical/
│   ├── pcb/
│   ├── viewer/
│   ├── urdf/
│   ├── sdf/
│   ├── srdf/
│   ├── simulation/
│   ├── gcode/
│   ├── sendcutsend/
│   ├── bambu-labs/
│   ├── parts-catalog/
│   ├── electronics-bom/                  # 现有占位,后续填实
│   ├── robot-dog-digital-twin/           # P0:总控编排
│   ├── requirements-verification/        # P0:需求合同与验证矩阵
│   ├── actuator-sizing/                  # P0:执行器扭矩/速度/热裕量
│   ├── pcb-mechanical-reliability/       # P0:PCB 刚度/挠曲/固定/连接器风险
│   ├── circuit-simulation/               # P0:电路、电源、保护、热粗估
│   ├── gait-optimization/                # P0/P1:步态参数评分与搜索
│   ├── fea/                              # P1:结构强度/刚度/模态/跌落
│   ├── wear-fatigue/                     # P1:磨损、疲劳、维护周期
│   ├── mujoco-simulation/                # P1:高保真腿足动力学
│   ├── motion-control/                   # P1:FK/IK/步态库/控制参数
│   ├── firmware/                         # P2:固件/电机控制/总线/标定
│   ├── sim2real-calibration/             # P2:实机数据回灌仿真参数
│   └── integration/                      # P2:bring-up/HIL/整机调试
└── tests/
    ├── test_skeleton.py
    ├── test_e2e_design_to_print.py
    └── test_robot_dog_digital_twin_e2e.py
```

### 4.2 `robot-dog-digital-twin` 子技能内部结构

```text
skills/robot-dog-digital-twin/
├── SKILL.md
├── README.md
├── references/
│   ├── workflow.md
│   ├── gates.md
│   ├── scoring.md
│   ├── failure-taxonomy.md
│   ├── artifact-layout.md
│   ├── iteration-loop.md
│   └── quadruped-mvp.md
├── scripts/
│   ├── init_project.py
│   ├── collect_artifacts.py
│   ├── run_gate.py
│   ├── score_design.py
│   ├── propose_next_iteration.py
│   └── render_failure_report.py
├── tests/
│   ├── conftest.py
│   ├── test_smoke.py
│   ├── test_collect_artifacts.py
│   ├── test_gate_rules.py
│   ├── test_score_design.py
│   └── test_failure_report.py
└── examples/
    └── quadruped_mvp/
        ├── requirements.yaml
        ├── verification_matrix.yaml
        ├── architecture.yaml
        ├── artifacts.json
        ├── mechanical/
        │   ├── body.step
        │   ├── leg.step
        │   ├── mass_properties.json
        │   └── collision_report.json
        ├── electrical/
        │   ├── board.circuit.json
        │   ├── board.bom.json
        │   ├── pcb_fit.json
        │   ├── circuit_check.json
        │   └── power_budget.json
        ├── simulation/
        │   ├── robot.urdf
        │   ├── robot.xml
        │   ├── scenarios/
        │   │   ├── stand.yaml
        │   │   ├── flat_walk.yaml
        │   │   ├── slope.yaml
        │   │   └── drop.yaml
        │   └── results/
        │       ├── stand.sim_result.json
        │       └── flat_walk.sim_result.json
        ├── control/
        │   ├── gait_params.yaml
        │   └── gait_score.json
        └── reports/
            ├── design_score.json
            ├── gate_report.json
            ├── failure_report.md
            └── next_iteration_plan.md
```

### 4.3 各新增子技能标准骨架

除 `robot-dog-digital-twin` 外,其他新增子技能统一用这个骨架,避免每个域长得不一样:

```text
skills/<skill-name>/
├── SKILL.md
├── README.md
├── references/
│   ├── workflow.md
│   ├── input-contract.md
│   ├── output-contract.md
│   ├── validation.md
│   └── examples.md
├── scripts/
│   ├── run_check.py
│   ├── collect_inputs.py
│   └── write_report.py
└── tests/
    ├── conftest.py
    ├── test_smoke.py
    ├── test_contracts.py
    └── test_run_check.py
```

各域的文件命名可以专门化:

| 子技能 | 关键脚本 | 关键 references | 关键输出 |
|---|---|---|---|
| `requirements-verification` | `validate_requirements.py`、`validate_matrix.py` | `requirements-fields.md`、`gate-thresholds.md` | `requirements_report.json` |
| `actuator-sizing` | `estimate_torque.py`、`select_actuator.py` | `torque-model.md`、`thermal-margin.md` | `torque_margin.json`、`actuator_spec.yaml` |
| `pcb-mechanical-reliability` | `check_pcb_fit.py`、`estimate_board_flex.py` | `standoff-rules.md`、`connector-loads.md` | `pcb_fit.json`、`pcb_reliability_report.json` |
| `circuit-simulation` | `check_power_budget.py`、`check_protection.py` | `power-rails.md`、`thermal-rules.md` | `circuit_check.json`、`power_budget.json` |
| `gait-optimization` | `score_gait.py`、`search_params.py` | `gait-levels.md`、`stability-metrics.md` | `gait_score.json`、`best_gait_params.yaml` |
| `fea` | `run_static_case.py`、`summarize_fea.py` | `load-cases.md`、`materials.md` | `fea_report.json` |
| `wear-fatigue` | `estimate_wear.py`、`estimate_fatigue.py` | `wear-models.md`、`bearing-life.md` | `wear_report.json`、`maintenance_interval.md` |
| `mujoco-simulation` | `run_scenarios.py`、`summarize_results.py` | `scenarios.md`、`backend-plan.md` | `mujoco_result.json`、`*.sim_result.json` |
| `motion-control` | `solve_ik.py`、`generate_gait.py` | `ik-model.md`、`gait-contract.md` | `trajectory.json`、`controller_params.yaml` |
| `firmware` | `generate_project.py`、`run_firmware_tests.py` | `mcu-targets.md`、`can-protocol.md` | `firmware_report.json`、`calibration.json` |

### 4.4 分阶段落盘顺序

不要一次性建满所有目录。推荐按阶段落盘:

| 阶段 | 新增/填实目录 | 验收 |
|---|---|---|
| P0-1 | `skills/robot-dog-digital-twin/`、`shared/schemas/{requirements,verification_matrix,design_score}.schema.json` | quadruped MVP 能生成 `gate_report` 和 `design_score` |
| P0-2 | `skills/requirements-verification/`、`skills/actuator-sizing/` | ✅ requirements 和 torque margin 已能独立跑 smoke |
| P0-3 | `skills/pcb-mechanical-reliability/`、`skills/circuit-simulation/` | ✅ PCB fit 和电源预算已能产 blocker |
| P0-4 | `skills/gait-optimization/` | ✅ 平地站立/慢走指标已能评分 |
| P1-1 | `skills/fea/`、`skills/wear-fatigue/` | ✅ FEA 与磨损疲劳 MVP 均已能产 blocker |
| P1-2 | `skills/mujoco-simulation/` | ✅ MuJoCo 场景合同与 metadata backend 已能产动力学 blocker |
| P1-3 | `skills/motion-control/` | ✅ IK 与相位步态轨迹 MVP 已能产 blocker 和 trajectory |
| P1-4 | `skills/mujoco-simulation/` real backend | 真实 MuJoCo 求解器接入 |
| P2 | `skills/firmware/`、`skills/sim2real-calibration/`、`skills/integration/` | 真实控制和实物闭环进入人工 gate |

### 4.5 模块间上下文清理纪律

每完成一个模块或子技能后,先清理上下文再进入下一个模块。这里的"完成"至少包括:

```text
1. 子技能骨架/脚本/测试/文档完成
2. 对应 smoke 或 focused tests 跑过
3. 产物、失败点、剩余风险写成简短交接摘要
4. 下一模块需要的接口和 artifact 路径确认
```

然后再做一次上下文压缩或手动交接,只保留下一模块真正需要的信息:

```text
保留:
  - 当前模块已完成什么
  - 输出 artifact 名称和路径
  - 已验证的命令
  - 未解决 blocker
  - 下一模块输入契约

丢弃:
  - 已经读过但下一模块不用的长文档
  - 中间推理细节
  - 临时方案分支
  - 已经废弃的目录/命名设想
```

执行顺序建议:

```text
实现一个子 skill
  -> 跑该子 skill 测试
  -> 写 module handoff note
  -> 压缩/清理上下文
  -> 读取下一个子 skill 的 SKILL.md / references
  -> 再开始下一个模块
```

这样可以避免在 `robot-dog-digital-twin` 这种多域项目里,前一个模块的细节污染后一个模块。

### 4.6 子技能测试红线

延续现有仓库惯例:每个子技能目录下都应有自己的 `tests/` 文件夹。新增或填实的子技能
必须保持同样结构,并至少有一个可运行测试。测试不通过时,不得进入下一个模块,必须回到
当前子技能继续修改,直到测试通过或明确记录 blocker。

最低要求:

```text
skills/<skill-name>/tests/
  conftest.py
  test_smoke.py
```

现有子技能已经基本按这个模式组织:

```text
skills/mechanical/tests/
skills/pcb/tests/
skills/viewer/tests/
skills/urdf/tests/
skills/sdf/tests/
skills/simulation/tests/
...
```

新增的 `robot-dog-digital-twin`、`actuator-sizing`、`pcb-mechanical-reliability` 等也必须遵守
相同约定,不要把测试集中塞到父级 `tests/`。

`test_smoke.py` 至少验证:

```text
1. SKILL.md 存在且非空
2. README.md 存在
3. references/ scripts/ tests/ 标准目录存在
4. SKILL.md 行数不过长
```

一旦子技能有脚本,还要增加 focused tests:

```text
scripts/run_check.py              -> test_run_check.py
scripts/score_design.py           -> test_score_design.py
scripts/run_gate.py               -> test_gate_rules.py
scripts/check_pcb_fit.py          -> test_check_pcb_fit.py
scripts/estimate_torque.py        -> test_estimate_torque.py
```

执行纪律:

```text
新增/修改一个子 skill
  -> 先跑 pytest skills/<skill-name>/tests/
  -> 如果失败,回到当前子 skill 修复
  -> 再跑同一组测试
  -> 通过后写 module handoff note
  -> 清理/压缩上下文
  -> 才能进入下一个子 skill
```

父级集成测试只在子技能自测通过后再跑:

```text
pytest tests/test_robot_dog_digital_twin_e2e.py
```

允许暂时跳过的测试必须显式标记原因,不能静默跳过:

```text
@pytest.mark.skip(reason="requires mujoco; P1 not installed in CI yet")
```

测试失败处理规则:

| 情况 | 处理 |
|---|---|
| smoke 失败 | 子技能骨架不合格,立即修 |
| contract/schema 失败 | artifact 接口不稳定,立即修 |
| 脚本 focused test 失败 | 回到脚本实现,修到通过 |
| 外部依赖缺失 | 用 `importorskip` 或显式 skip reason,并保留 dry-run 测试 |
| 真实硬件/下单/烧录相关 | 不进自动测试,只保留 dry-run 和人工 gate |

### 4.7 输出目录边界

仓库内只放**技能代码、schema、文档、测试 fixture 和 MVP 示例**。真实项目输出仍然不能写进
super skill 根目录,应放到项目工作区:

```text
~/work/<project>/domains/robot-dog-digital-twin/output/<iteration>/
  requirements/
  mechanical/
  electrical/
  simulation/
  control/
  reports/
```

这样既能在 `build123d-cad` 内孵化数字孪生能力,又不会把用户真实设计产物污染到 skill 仓库。

---

## 5. 子技能依赖关系

```
requirements-verification / system(robot-dog-digital-twin 子域)
              │ requirements / budgets / verification_matrix
              ▼
   ┌──────────────────────── robot-dog-digital-twin orchestrator ────────────────────────┐
   │                    gate / score / failure_report / next_iteration                    │
   └──────────────────────────────────────────────────────────────────────────────────────┘
              │
   ┌──────────┼──────────────┬──────────────┬──────────────┬─────────────────────┐
   ▼          ▼              ▼              ▼              ▼                     ▼
mechanical  electronics-bom  actuator-sizing  pcb           motion-control        manufacturing
   │          │              │              │              │                     │
   │STEP      │选型          │torque margin  │circuit/STEP  │trajectory            │slice/quote
   ▼          ▼              │              ▼              ▼                     ▼
  fea        pcb ────────────┘       pcb-mechanical   simulation(PyBullet)       gcode/sendcutsend
   │减重建议   │netlist/BOM              │fit/reliability     │smoke result
   │          ▼                         ▼                   ▼
   │     circuit-simulation / power-thermal        mujoco-simulation
   │          │                         ▲                   │
   ▼          ▼                         │                   ▼
mechanical ◄ wear-fatigue ◄──────── simulation / gait ── gait-optimization
   │
   ▼
urdf / sdf / viewer
```

依赖原则:

- `digital-twin-orchestrator` 只读 artifact,不 import 任何子技能代码。
- `requirements-verification` 是最上游合同层,所有验证域都以它的阈值为准。
- `simulation` 保持轻量 PyBullet smoke;`mujoco-simulation` 用于严肃步态/接触/扰动验证。
- `wear-fatigue` 需要 `mechanical` 的材料/标准件和 `simulation/gait` 的载荷谱。
- `pcb-mechanical-reliability` 同时消费 `pcb` 的板级 3D 和 `mechanical` 的机身装配。
- `gait-optimization` 产出的轨迹和参数回灌 `motion-control` / `simulation`。

---

## 6. 优先级排序(数字孪生优先)

### P0:先跑通虚拟样机闭环

| 序 | 子技能 | 理由 | 成本 |
|---|---|---|---|
| 1 | `requirements-verification` | 没有需求合同和验证矩阵,后续评分/gate 都会主观化 | 低 |
| 2 | `digital-twin-orchestrator` | 先把 artifact 收集、gate、score、failure_report 跑通 | 中 |
| 3 | `actuator-sizing` | 机械狗成败核心是扭矩/速度/热裕量,应早于精细 CAD 迭代 | 中 |
| 4 | `pcb-mechanical-reliability` | 直接覆盖用户关心的 PCB 刚度/挠曲/支撑/连接器风险 | 中 |
| 5 | `circuit-simulation` / `power-thermal` | 先做电源预算、保护、电流峰值、热风险,不一开始追求完整 SPICE | 中 |
| 6 | `gait-optimization` | 让"行走算法合理"变成可评分场景,先接 PyBullet,再接 MuJoCo | 中高 |

### P1:把虚拟验证做深

| 序 | 子技能 | 理由 | 成本 |
|---|---|---|---|
| 1 | `fea` | 把结构强度/刚度/跌落从规则检查升级到求解器 | 中 |
| 2 | `wear-fatigue` | 评估齿轮、轴承、足垫、线束、连接器寿命和维护间隔 | 中高 |
| 3 | `mujoco-simulation` | 高保真接触/摩擦/执行器/地形扰动,支撑大量步态参数搜索 | 中高 |
| 4 | `motion-control` | 将 IK/步态库做成可执行实现,供 simulation/MuJoCo/firmware 消费 | 中高 |
| 5 | `electronics-bom` | 填满现有占位,给 pcb/circuit/firmware 的选型提供依据 | 低 |

### P2:跨到真实控制和实体闭环

| 序 | 子技能 | 理由 | 成本 |
|---|---|---|---|
| 1 | `firmware` | 最大断崖,跨过它才谈真实可动;但必须先有虚拟验证和 dry-run 保护 | 高 |
| 2 | `sim2real-calibration`(后续) | 将实机数据回灌仿真参数,减少仿真和真实差距 | 高 |
| 3 | `integration` | Bring-up / HIL / 实物数据回采,必须等真实硬件出现后再做 | 高 |

> `system` / orchestrator 层先放在 `build123d-cad` 的 `robot-dog-digital-twin` 子域中孵化,
> 但不要让父 `SKILL.md` 从"路由器"变成"项目经理"。

---

## 7. 落地节奏建议(分阶段,每阶段独立可验收)

- **Gate A(先做,无争议)**:需求合同 + artifact schema + digital-twin orchestrator skeleton。
  目标是先能读一个简化机械狗项目,输出 gate、score、failure_report。
- **Gate B(虚拟验证 MVP)**:接入 actuator-sizing、PCB fit、电路/电源预算、PyBullet stand/flat_walk/drop。
  目标是能判断"是否允许实体样机",并给下一轮参数建议。
- **Gate C(提高真实性)**:加入 FEA、wear-fatigue、MuJoCo、gait-optimization。
  目标是把粗规则逐步替换成更可信的仿真/求解结果。
- **Gate D(战略决策)**:`firmware` / sim2real / integration。**必须先决定是否打破红线**。
  若做,先用 Renode/QEMU/单测把"能编译+逻辑对"闭环,实体烧录/上电/电机转动设为人工 gate。

每个子技能立项时走 `docs/adding-new-subskill.md`:建目录骨架 → 改父 `SKILL.md` 路由 →
改 `shared/multi-skill-router.md` + `shared/dependencies.md` + `shared/handoff-protocols.md`。

---

## 8. MVP 验收样例: `skills/robot-dog-digital-twin/examples/quadruped_mvp`

第一版必须有真实例子,否则容易变成漂亮文档。建议先在本仓库的
`skills/robot-dog-digital-twin/examples/quadruped_mvp/` 下放一个最小样例:

```text
skills/robot-dog-digital-twin/examples/quadruped_mvp/
  requirements.yaml
  verification_matrix.yaml
  architecture.yaml
  artifacts.json
  mechanical/
    body.step
    leg.step
    mass_properties.json
    collision_report.json
  electrical/
    board.circuit.json
    board.bom.json
    pcb_fit.json
    circuit_check.json
    power_budget.json
  simulation/
    robot.urdf
    robot.xml                 # 可选:MuJoCo MJCF
    scenarios/
      stand.yaml
      flat_walk.yaml
      slope.yaml
      drop.yaml
    results/
      stand.sim_result.json
      flat_walk.sim_result.json
  control/
    gait_params.yaml
    gait_score.json
  reports/
    design_score.json
    failure_report.md
    next_iteration_plan.md
```

MVP 可以用简化机械狗:

```text
body = box
leg = 3-link simplified leg
pcb = rectangle board with connectors
battery = mass block
simulation = simplified URDF
gait = trot phase table
```

最低可跑命令应类似:

```bash
python skills/robot-dog-digital-twin/scripts/collect_artifacts.py skills/robot-dog-digital-twin/examples/quadruped_mvp
python skills/robot-dog-digital-twin/scripts/score_design.py skills/robot-dog-digital-twin/examples/quadruped_mvp
python skills/robot-dog-digital-twin/scripts/run_gate.py skills/robot-dog-digital-twin/examples/quadruped_mvp --gate G3
python skills/robot-dog-digital-twin/scripts/propose_next_iteration.py skills/robot-dog-digital-twin/examples/quadruped_mvp
```

期望输出:

```json
{
  "version": "quadruped_mvp_v0",
  "total_score": 68,
  "prototype_allowed": false,
  "blockers": [
    "flat_walk_no_fall failed",
    "front_knee torque margin below threshold",
    "pcb connector clearance below 2mm"
  ],
  "next_actions": [
    "move battery 20mm backward",
    "reduce trot stride from 60mm to 42mm",
    "add PCB standoff near power connector"
  ]
}
```

---

## 9. 统一 artifact / schema 建议

数字孪生必须靠统一数据结构,不能靠自然语言临时拼接。建议最小 schema:

```text
shared/schemas/
  requirements.schema.json
  verification_matrix.schema.json
  design_artifacts.schema.json
  actuator_spec.schema.json
  mass_properties.schema.json
  pcb_fit.schema.json
  circuit_check.schema.json
  sim_scenario.schema.json
  sim_result.schema.json
  gait_score.schema.json
  design_score.schema.json
```

MVP 先做 5 个:

```text
requirements.schema.json
verification_matrix.schema.json
pcb_fit.schema.json
sim_result.schema.json
design_score.schema.json
```

`requirements.yaml` 示例:

```yaml
version: "1.0"
robot:
  name: quadruped_mvp
  type: quadruped
  dof: 12

targets:
  mass_kg: 5.0
  payload_kg: 0.5
  runtime_min: 30
  flat_walk_speed_mps: 0.5
  max_slope_deg: 8
  max_body_width_mm: 180
  max_body_length_mm: 280

constraints:
  manufacturing:
    primary: fdm_3d_print
    material: petg
  electronics:
    battery_voltage_nominal: 24
    max_current_a: 30
  safety:
    require_emergency_stop: true
    max_surface_temp_c: 65
```

`design_score.json` 第一版权重:

```yaml
weights:
  mechanical: 20
  pcb_reliability: 15
  electrical: 20
  dynamics: 20
  gait: 15
  manufacturability: 10
```

评分规则必须确定性优先:

- 机械:无干涉、质量低于目标、重心合理、结构报告无 blocker。
- PCB:连接器 clearance 合格、支撑柱合理、板挠曲风险低、固定孔无 blocker。
- 电气:ERC/DRC 通过、电源裕量 >= 20%、热风险可接受、保护电路齐全。
- 动力学:站立 30 秒、跌落不爆炸、关节限位正常、扭矩裕量 >= 20%。
- 步态:平地不倒、roll/pitch 合格、足端打滑低、速度达到目标。

---

## 10. 第一版不要做什么

这些先不要碰,否则会卡死在工具链和真实性细节里:

```text
不要一开始做完整 FEA 自动化
不要一开始追求真实磨损寿命
不要一开始做强化学习
不要一开始接真实采购下单
不要一开始做完整 ROS2 产品栈
不要一开始做高精度热仿真
不要一开始自动烧录/上电/让电机转动
```

第一版只要把"虚拟样机是否允许实体制造"跑成可复现闭环,后续再把各域检查从规则逐步升级。

---

## 11. 红线与风险

- **红线决策前置**:`firmware`/`motion-control` 的实体执行(烧录、上电、电机转动)必须
  默认 dry-run + 显式 `--confirm`,对齐 `bambu-labs` 的安全哲学。绝不假装成功。
- **可验证性**:固件/控制强依赖硬件 → 优先选**可 headless 仿真**的工具(Renode/QEMU/pybullet),
  把"无实体也能验逻辑"作为选型硬指标,否则违背 skill 的离线/CI 可复现纪律。
- **不过度扩张**:`system`/`integration` 与"父级只路由"哲学有张力,**不轻易拉进 skill**,
  优先留给调用方编排框架。
- **解耦**:`motion-control` 落地后,`simulation` 的内嵌 gait 要退化为"消费轨迹",
  避免两处各写一套步态。
- **sim2real 差距**:数字孪生不能替代实体测试,只能把第一次实体样机从盲做变成有依据的工程验证件。
- **评分误用**:分数高不等于可以做实体;只要存在 blocker,gate 必须失败。

---

## 12. 待评审决策点

1. `robot-dog-digital-twin` 是否先放在 `build123d-cad` 下孵化?当前建议:是。
2. 闭环成熟后是否再拆成独立 super skill / 独立仓库?当前建议:成熟后再评审。
3. MVP 是否先用 PyBullet smoke,等闭环跑通后再加 MuJoCo?当前建议:是。
4. `pcb-mechanical-reliability` 第一版是规则检查还是直接接 FEA?当前建议:先规则检查。
5. `circuit-simulation` 第一版是否只做电源预算/保护/热粗估?当前建议:是,不追求完整 SPICE。
6. **是否打破"不碰固件"红线?** 当前建议:先不打破,等 G0-G4 闭环跑通后再评审。
7. `fea` 求解器选 CalculiX 还是 FEniCS?(CI 友好度 + LLM 语料)
8. `motion-control` 运动学选 Pinocchio 还是自写闭式解?(腿低 DOF 可能自写更轻)
9. `firmware` 电机框架选 SimpleFOC 还是裸 HAL?(语料 vs 性能)
