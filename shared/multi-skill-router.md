# 父级路由依据 (multi-skill-router)

父 `SKILL.md` 两层路由的判据。父级**不读**子技能完整内容，只按关键词分派，再 `Read skills/<name>/SKILL.md`。

## 关键词 → 子技能

> 状态：✅ 已落地可用 / 🟡 占位待开张。

| 子技能 | 触发关键词 | 状态 |
|---|---|---|
| mechanical | CAD、建模、装配、零件、外壳、支架、齿轮、反求、仿真(FK/IK/步态)、STEP/STL | ✅ 根基 |
| viewer | 预览、网页查看、分享链接、headless、看一下模型/PCB/原理图/波形 | ✅ P0 |
| urdf | URDF、机器人描述、link/joint、导出 ROS | ✅ P0 |
| srdf | MoveIt、规划组、planning group、碰撞矩阵、自碰撞 | ✅ P1 |
| sdf | Gazebo、SDF、仿真世界 | ✅ P1 |
| gcode | 切片、FDM、G-code 预检、打印时间估算、悬垂/overhang | ✅ P1 |
| sendcutsend | 激光切割、钣金、报价、SendCutSend、DXF 展开、折弯 | ✅ P1 |
| parts-catalog | 找现成零件、在线 STEP、标准件下载、轴承/螺丝/舵机型号 | ✅ P0 |
| simulation | 动力学仿真、pybullet、跌落/站稳测试、步态仿真、headless sim、会不会翻、关节限位、接触力 | ✅ P1 |
| bambu-labs | Bambu 打印机、上传打印、AMS | 🟡 P2 |
| pcb | PCB、原理图、tscircuit、代码写PCB、TSX、Gerber、出件、嘉立创、JLCPCB、下单打板、PCB 3D、DFM、EDA | ✅ P1(tscircuit) |
| electronics-bom (WIP) | 电子 BOM、元件选型、JLCPCB/Octopart | 🟡 P3 占位 |
| requirements-verification | 需求合同、requirements.yaml、verification_matrix.yaml、验证矩阵、gate 阈值、risk register、需求冻结 | ✅ P0 合同 |
| actuator-sizing | 执行器选型、电机扭矩、关节扭矩、减速器、速度裕量、热裕量、torque_margin、actuator_spec、机械狗电机够不够 | ✅ P0 执行器 |
| pcb-mechanical-reliability | PCB刚度、PCB挠曲、PCB硬度、支撑柱、固定孔、连接器受力、线束弯折、PCB装配间隙、pcb_fit、pcb_reliability_report | ✅ P0 PCB 结构 |
| circuit-simulation | 电路合理性、电源预算、电流峰值、保护电路、急停、欠压、TVS、保险丝、MOSFET热、驱动器热、thermal_report、power_budget、circuit_check | ✅ P0 电路 |
| gait-optimization | 步态优化、行走算法、trot、walk、gait_score、best_gait_params、foot slip、body roll、body pitch、cost of transport、会不会摔 | ✅ P0 步态 |
| fea | FEA、有限元、结构强度、刚度、变形、位移、安全系数、应力、模态、跌落冲击、fea_report、会不会断 | ✅ P1 结构 |
| wear-fatigue | 磨损、疲劳、轴承寿命、齿轮寿命、足垫磨耗、关节限位撞击、螺丝松动、线束弯折、夹线风险、连接器松脱、维护周期、wear_report、fatigue_report | ✅ P1 寿命 |
| robot-dog-digital-twin | 数字孪生、虚拟样机、机械狗验证、实体样机 gate、design_score、failure_report、多域验证、设计迭代 | ✅ P0 编排 |

## 路由规则

1. 收到需求 → 按上表关键词匹配子技能（可命中多个 → 主子技能优先，其余走 handoff）。
2. `Read skills/<name>/SKILL.md` 后再开始答题；不要凭记忆。
3. 跨子技能数据交换走 `shared/handoff-protocols.md`，不直接互引 references。
4. 跨子技能流程（机械→viewer→urdf）由父级编排，实施落到各子技能。

## 多命中消歧

- "做个外壳并预览" → mechanical(主) + viewer(handoff)
- "把这个机器人导成 URDF 并看关节" → urdf(主) + viewer(handoff)
- "找个 608 轴承装进去" → parts-catalog(主) + mechanical(handoff)
- "给这个机器人配 MoveIt 规划组 / 自碰撞矩阵" → urdf(前置) + srdf(主)
- "放进 Gazebo 仿真世界跑一下" → urdf(前置) + sdf(主)
- "这机器人站得稳吗 / 丢进物理引擎跑一下 / 跑个步态看会不会翻" → urdf(前置) + simulation(主, headless 跑 + 判稳)
- "给这只机械狗定义需求合同 / 验证矩阵 / G0 输入" → requirements-verification(主,产 requirements.yaml + verification_matrix.yaml)
- "这套机械狗电机/减速器扭矩够不够 / 热裕量够吗" → actuator-sizing(主,产 actuator_spec.yaml + torque_margin.json)
- "这块 PCB 在机身里刚度/支撑/连接器空间合理吗" → pcb-mechanical-reliability(主,产 pcb_fit.json + pcb_reliability_report.json)
- "这套电路/电源预算/保护/热风险合理吗" → circuit-simulation(主,产 circuit_check.json + power_budget.json + thermal_report.json)
- "这个步态/行走算法会不会摔 / 下一版步态参数怎么改" → gait-optimization(主,产 gait_score.json + best_gait_params.yaml)
- "这个腿/机身强度够吗 / 变形大不大 / 要不要 FEA" → fea(主,产 fea_report.json + static_case_report.json)
- "这些齿轮/轴承/足垫/线束/连接器多久会磨坏 / 维护周期多长" → wear-fatigue(主,产 wear_report.json + fatigue_report.json + maintenance_interval.md)
- "这个机械狗虚拟样机能不能进入实体样机 / 给我 design_score 和 failure_report" → robot-dog-digital-twin(主,读 artifact 跑 gate)
- 关键词"仿真"按意图分:解析 FK/IK → mechanical;丢进物理引擎跑判稳 → simulation;出 Gazebo 世界 → sdf
- "这件能 3D 打印吗 / 估下打印时间" → mechanical(前置 STEP) + gcode(主)
- "这块钣金激光切多少钱" → mechanical(前置 STEP) + sendcutsend(主)
- "用代码写块板子并发嘉立创打样" → pcb(主,tscircuit 端到端) + viewer(预览 handoff)
