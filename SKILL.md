---
name: build123d-cad
description: |
  硬件设计 Super Skill。一个父技能内含 22 个子技能（mechanical / viewer / urdf /
  srdf / sdf / simulation / gcode / sendcutsend / parts-catalog / bambu-labs / pcb / electronics-bom /
  requirements-verification / actuator-sizing / pcb-mechanical-reliability / circuit-simulation /
  gait-optimization / motion-control / fea / wear-fatigue / mujoco-simulation / robot-dog-digital-twin），
  覆盖机械建模 → 网页预览 → 机器人描述 → 动力学仿真 → 制造出工 → 电子域全链路。
  触发词：build123d、CAD建模、做一个零件、参数化设计、装配、URDF、机器人描述、
  MoveIt、Gazebo、SDF、动力学仿真、pybullet、跌落测试、步态仿真、headless sim、站得稳吗、
  切片、3D打印、激光切割、SendCutSend、Bambu、找现成零件、
  STEP、网页预览、分享链接、PCB、tscircuit、代码写PCB、Gerber、嘉立创、JLCPCB、下单打板、电子BOM、
  需求合同、验证矩阵、执行器选型、扭矩裕量、热裕量、PCB刚度、PCB挠曲、连接器受力、
  电源预算、电路保护、热风险、步态优化、行走算法、IK、FK、运动控制、轨迹生成、FEA、结构强度、刚度、磨损、疲劳、轴承寿命、维护周期、MuJoCo、MJCF、高保真动力学、数字孪生、虚拟样机、机械狗验证、
  设计评分、实体样机 gate。
  父级只做路由，详细能力在 skills/<name>/SKILL.md。
---

# build123d-cad — 硬件设计 Super Skill

> 一次安装、模块化的硬件设计技能集合。父级只做路由，详细能力在各子技能。
>
> 「像机械师思考，而不是像程序员思考。」 — Dave Cowden

---

## AI 执行准入序列（每次会话第一件事）

1. 读本父 SKILL.md 的「子技能集合」表 + 「路由规则」。
2. 按需求关键词匹配子技能（命中多个 → 主子技能优先，其余走 handoff）。
3. **`Read skills/<name>/SKILL.md`** 后再开始答题；不要凭父级触发词推测子技能内部流程。
4. 子技能 SKILL.md 引用的 Playbook / references 由子技能自行加载，父级不展开。
5. 跨子技能流程由父级显式编排，实施落到子技能；不让子技能直接互相 import。
6. **禁止**：跳过对应子技能 SKILL.md 直接读其 references/ 拼流程；父级 SKILL.md 内嵌
   实现细节；子技能之间 `from skills.<other>.references...` 互引（CI 红线）。

---

## 子技能集合（22 个）

| 子 skill | 触发场景关键词（部分匹配即触发） | 路径 | 优先级 |
|---|---|---|---|
| mechanical      | 建模 / 装配 / 反求 / 零件 / part / assembly / 仿真 / FK / IK / 步态 | skills/mechanical/SKILL.md      | P0 根基 |
| viewer          | 预览 / 网页查看 / 分享链接 / headless / 看一下模型/PCB/原理图       | skills/viewer/SKILL.md          | P0 |
| urdf            | URDF / 机器人描述 / robot description / link / joint / .urdf      | skills/urdf/SKILL.md            | P0 |
| parts-catalog   | 找现成件 / 标准件 / STEP 下载 / McMaster / 608 轴承 / M3 螺丝     | skills/parts-catalog/SKILL.md   | P0 |
| srdf            | MoveIt / 规划组 / planning group / collision matrix              | skills/srdf/SKILL.md            | P1 |
| sdf             | Gazebo / 仿真世界 / sim world / .sdf                             | skills/sdf/SKILL.md             | P1 |
| simulation      | 动力学仿真 / pybullet / 跌落测试 / 站得稳吗 / 步态仿真 / headless sim / 会不会翻 / 关节限位 | skills/simulation/SKILL.md | P1 ✅ |
| gcode           | 切片 / FDM / G-code 预检 / 打印估时 / 支撑 / overhang             | skills/gcode/SKILL.md           | P1 |
| sendcutsend     | 激光切割 / 钣金 / DXF 报价 / kerf / SendCutSend                  | skills/sendcutsend/SKILL.md     | P1 |
| bambu-labs      | Bambu / 打印机 / 上传打印 / AMS / send to printer                | skills/bambu-labs/SKILL.md      | P2 |
| pcb             | PCB / 原理图 / tscircuit / 代码写PCB / TSX / Gerber / 出件 / 嘉立创 / JLCPCB / 下单打板 / PCB 3D / DFM / EDA | skills/pcb/SKILL.md | P1 ✅ tscircuit |
| electronics-bom | 电子 BOM / 元件库 / MCU / 电机驱动 / 编码器 / 电源器件 / JLCPCB / Octopart / 元件型号 | skills/electronics-bom/SKILL.md | P1 ✅ BOM |
| requirements-verification | 需求合同 / requirements.yaml / verification_matrix.yaml / 验证矩阵 / gate 阈值 / risk register | skills/requirements-verification/SKILL.md | P0 ✅ 合同 |
| actuator-sizing | 执行器选型 / 电机扭矩 / 关节扭矩裕量 / 减速器 / 速度裕量 / 热裕量 / actuator_spec / torque_margin | skills/actuator-sizing/SKILL.md | P0 ✅ 执行器 |
| pcb-mechanical-reliability | PCB 刚度 / 挠曲 / 支撑柱 / 固定孔 / 连接器受力 / 线束弯折 / PCB 装配间隙 / pcb_fit | skills/pcb-mechanical-reliability/SKILL.md | P0 ✅ PCB 结构 |
| circuit-simulation | 电路合理性 / 电源预算 / 电流峰值 / 保护电路 / 急停 / 欠压 / TVS / 热风险 / circuit_check / power_budget | skills/circuit-simulation/SKILL.md | P0 ✅ 电路 |
| gait-optimization | 步态优化 / 行走算法 / trot / gait_score / foot slip / body roll / body pitch / cost of transport / best_gait_params | skills/gait-optimization/SKILL.md | P0 ✅ 步态 |
| motion-control | IK / FK / 逆运动学 / gait generator / trot trajectory / controller_params / trajectory.json / 运动控制 | skills/motion-control/SKILL.md | P1 ✅ 控制 |
| fea | FEA / 有限元 / 结构强度 / 刚度 / 变形 / 安全系数 / 应力 / 模态 / 跌落冲击 / fea_report | skills/fea/SKILL.md | P1 ✅ 结构 |
| wear-fatigue | 磨损 / 疲劳 / 轴承寿命 / 齿轮寿命 / 足垫磨耗 / 线束弯折 / 连接器松脱 / maintenance_interval | skills/wear-fatigue/SKILL.md | P1 ✅ 寿命 |
| mujoco-simulation | MuJoCo / MJCF / 高保真动力学 / 接触摩擦 / slope / step obstacle / push disturbance / mujoco_result | skills/mujoco-simulation/SKILL.md | P1 ✅ MuJoCo |
| robot-dog-digital-twin | 数字孪生 / 虚拟样机 / 机械狗验证 / 设计评分 / failure report / 实体样机 gate / 多域验证 | skills/robot-dog-digital-twin/SKILL.md | P0 ✅ 编排 |

> 关键词权威映射在 `shared/multi-skill-router.md`；本表是其精简映像，改动需双向同步。

---

## 路由规则

1. 收到需求 → 按上表关键词匹配子技能；命中多个 → 主子技能优先，其余走 handoff。
2. 先 `Read skills/<name>/SKILL.md` 再开始答题；不读子技能 references/ 全量（防 token 爆）。
3. 子技能间数据交换走 `shared/handoff-protocols.md` 文件接口，不做函数调用，不互引 references。
4. 跨子技能流程由父级编排，实施落到子技能；父级只路由，不实现。
5. 关键词模糊或冲突 → 反问消歧，不要赌。

---

## 多命中消歧示例

- 「做个外壳并预览」 → mechanical（主） + viewer（handoff：STEP → URL）
- 「把这个机器人导成 URDF 并看关节」 → urdf（主） + viewer（handoff：URDF → urdf-loader）
- 「找个 608 轴承装进去」 → parts-catalog（主） + mechanical（handoff：合并入装配）
- 「这个支架能激光切吗，多少钱」 → mechanical（出 DXF） + sendcutsend（报价）
- 「这个件 3D 打印能不能打出来」 → mechanical（已有 STEP） + gcode（FDM 切片预检）
- 「用代码写块板子并发嘉立创」 → pcb（主，tscircuit 端到端） + viewer（预览 handoff）
- 「PCB 外壳一起做」 → pcb（电气） + mechanical（外壳） + viewer（双引擎并显）
- 「这机器人站得稳吗 / 丢进物理引擎跑一下 / 跑个步态看会不会翻」 → urdf（前置 URDF） + simulation（主，headless 跑 + 判稳）
- 「给这只机械狗定需求合同 / 验证矩阵」 → requirements-verification（主，产 requirements.yaml + verification_matrix.yaml）
- 「这套机械狗电机/减速器扭矩够不够 / 热裕量够吗」 → actuator-sizing（主，产 actuator_spec.yaml + torque_margin.json）
- 「这块 PCB 在机身里硬度/刚度够吗 / 支撑柱和连接器合理吗」 → pcb-mechanical-reliability（主，产 pcb_fit.json）
- 「这套电路/电源预算/保护/热风险合理吗」 → circuit-simulation（主，产 circuit_check.json + power_budget.json）
- 「这个步态/行走算法会不会摔 / foot slip 高不高 / 下一版步态参数怎么改」 → gait-optimization（主，产 gait_score.json）
- 「生成 IK 解 / trot 轨迹 / controller_params 给仿真或固件」 → motion-control（主，产 trajectory.json + controller_params.yaml）
- 「这个腿/机身强度够吗 / 变形大不大 / 要不要 FEA」 → fea（主，产 fea_report.json）
- 「齿轮/轴承/足垫/线束会不会很快磨坏 / 维护周期多长」 → wear-fatigue（主，产 wear_report.json + fatigue_report.json）
- 「用 MuJoCo/MJCF 跑斜坡、台阶、推扰、接触摩擦验证」 → mujoco-simulation（主，产 mujoco_result.json）
- 「这个机械狗虚拟样机能不能进实体」 → robot-dog-digital-twin（主，读各域 artifact → gate/score/failure_report）
- 关键词「仿真」按意图分：解析 FK/IK → mechanical；丢进物理引擎跑判稳 → simulation；出 Gazebo 世界 → sdf

---

## 角色规则（7 条核心，详细在子技能 SKILL.md）

1. **代码优先**：直接给可执行代码，不长篇解释；用户已给方向（"按这个方案"/"继续"）→
   立即执行，不重新评估利弊。
2. **参数化**：所有尺寸用变量定义在文件顶部，修改一处全局生效。
3. **设计意图优先**：用选择器（`sort_by` / `filter_by`）定位特征，不硬编码坐标。
4. **不编造 API**：基础 API 必须在子技能 references 中收录；建模前强制巡查
   `references/code-sources/` 同领域成熟实现，标明来源 + License。
5. **STEP 优先**：CNC / 激光 / 装配配合件一律 STEP；3D 打印再考虑 STL。
6. **必须导出**：每段代码末尾包含 `export_step()` 或用户指定格式的导出。
7. **跨子技能时主动 handoff**：检测到产物可被下游消费（STEP→viewer/urdf/gcode）时，
   主动提示并按 `shared/handoff-protocols.md` 串接。

> 子技能私有的更细规则（OCP 预览强制、装配爆炸提示、subagent 模型分派等）在
> `skills/mechanical/SKILL.md` 等子技能 SKILL.md 内展开，父级不重复。

---

## 跨子技能标准 handoff（常见 4 条）

| # | 链路 | 文件接口 |
|---|---|---|
| 1 | mechanical → viewer | `output/<task>/<part>.step` → `viewer.start(step)` 返回 URL |
| 2 | mechanical → urdf | 多零件 STEP + `output/<task>/joints.yaml` → `*.urdf` + `meshes/` |
| 3 | mechanical → 制造预检 | STEP → `gcode`（FDM）/ DXF → `sendcutsend`（钣金报价） |
| 4 | urdf → viewer | `*.urdf` → viewer cad 引擎（urdf-loader + 关节滑块） |

> 完整路径约定与 schema 见 `shared/handoff-protocols.md` 与
> `share/build123d-cad改造/08-shared跨子技能协议.md` §2。

---

## 输出工作区约定

- 所有子技能产物落到**项目工作区**：`~/work/<project>/domains/<x>/output/<task>/`
- super skill 内**不放** `output/`（防污染 skill 目录，见 08 §6 决议）
- 子技能脚本不要 `Path("output/...")` 自拼，走 `shared/python/handoff/output_paths`

---

## 加新子技能

见 `docs/adding-new-subskill.md` 9 步流程。改动 3 处共享配置：父 SKILL 路由表、
`shared/multi-skill-router.md`、`shared/dependencies.md`（必要时再加 handoff 条目）。

---

## 评审与变更流程

| 变更类型 | 流程 |
|---|---|
| 父 SKILL 路由 / 骨架原则变更 | 改 `share/build123d-cad改造/00-总览与目标架构.md` → Gate 1/Gate 3 评审 |
| 跨技能接口变更（handoff 路径 / schema / URL 协议） | 改 `shared/<对应文件>.md` → 在 `shared/CHANGELOG.md` 登记 → @ 受影响 Owner |
| 单子技能内实现变更 | 子技能 Owner 自决，跑 `pytest skills/<name>/tests/` 通过即可 |

破坏性变更（改字段名/类型/枚举）必须 @tech_lead 评审，CHANGELOG 用 ⚠️ 标记。

---

## 不做什么

- ❌ 不在父 SKILL.md 内嵌实现 / 详细代码 / Playbook 全文
- ❌ 不让子技能之间直接 import 或读对方 references/
- ❌ 不在 super skill 内放 `output/`（落项目工作区）
- ❌ 不用 git submodule（子技能是目录，monorepo 一次安装）
- ❌ 不改 skill 名（暂留 `build123d-cad`，多域成熟再议）

---

## 参考文档

- 总览与目标架构：`share/build123d-cad改造/00-总览与目标架构.md`
- 跨子技能协议：`shared/handoff-protocols.md` / `multi-skill-router.md` / `dependencies.md`
- 加新子技能：`docs/adding-new-subskill.md`
- 架构说明：`docs/architecture.md`
