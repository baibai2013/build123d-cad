# 子技能串接协议 (handoff-protocols)

子技能之间**不直接函数调用、不互引 references**，只通过**文件标准接口**交换。统一工作区：`output/<task>/`。

## 标准产物约定

| 产出方 | 产物 | 路径约定 |
|---|---|---|
| mechanical | 零件/装配 | `output/<task>/<part>.step`（+ `.stl`/`.glb` 可选 sidecar） |
| urdf | 机器人描述 | `output/<task>/<robot>.urdf` + `output/<task>/meshes/` |
| srdf | MoveIt 语义 | `output/<task>/<robot>.srdf`（交互式生成额外产整包 `<robot>_moveit_config/`） |
| sdf | Gazebo 世界 | sibling `<model>.sdf`（或 `-o` 指定）；world 走 `output/<task>/world.sdf` + `model.sdf` |
| viewer | 预览 URL | stdout 返回 `http://127.0.0.1:<port>/?engine=<e>&dir=&file=`；headless 走 sidecar `_viewer/{preview.url,snapshot.png,tier_meta.json}` 或 `<stem>.preview.png` / `<stem>.dimensions.json`（P1-5 三档降级，见 03 §10） |
| gcode | 切片报告 | `output/<task>/<part>.slice.json` |
| sendcutsend | 报价/DXF | `output/<task>/<part>.dxf` + `quote.json` |
| parts-catalog | 现成件 | L1 返回模块路径 + 实例化参数（不下 STEP）；L2+ 落盘 `output/<task>/parts/<id>.step` |
| pcb | PCB 出件/3D/预览 | `output/<task>/electrical/`：`fab/<board>-gerbers.zip`(+`-bom.csv`/`-cpl.csv`)、`3d/<board>.{step,glb}`、`preview/<board>.{pcb,schematic}.svg`、`<board>.circuit.json` + `<board>.bom.json`(viewer engine=tscircuit 统一预览,bom 经 jlcpcb-mcp 免key定价)、`<board>.quote.json` |
| electronics-bom | 电子 BOM 选型报告 | `<project>/reports/`：`electronics_bom.json` + `availability_report.json` + `selection_rationale.md`;`<project>/electrical/library/selected_parts.json` |
| simulation | 动力学仿真记录 | `output/<task>/simulation/`：`<robot>.results.json`(时序+汇总+checks) + `<robot>.trajectory.json`(cad 引擎 3D 回放格式) + `frames/*.png`(+ `manifest.json`) + `<robot>.sim.mp4`(有 imageio/cv2 才出) + `_verify/{static.png,settled.png,checklist.txt}` |
| requirements-verification | 需求合同与验证矩阵 | `<project>/`：`requirements.yaml` + `verification_matrix.yaml` + `architecture.yaml` + `risk_register.md`;校验报告 `<project>/reports/requirements_validation.{json,md}` |
| actuator-sizing | 执行器裕量报告 | `<project>/reports/`：`torque_margin.json` + `actuator_spec.yaml` + `actuator_sizing_report.md` |
| pcb-mechanical-reliability | PCB 结构可靠性报告 | `<project>/reports/`：`pcb_fit.json` + `pcb_reliability_report.json` + `connector_clearance.json` + `pcb_mechanical_report.md` |
| circuit-simulation | 电路/电源/热风险报告 | `<project>/reports/`：`circuit_check.json` + `power_budget.json` + `thermal_report.json` + `protection_checklist.md` + `circuit_simulation_report.md` |
| gait-optimization | 步态评分与参数建议 | `<project>/reports/`：`gait_score.json` + `best_gait_params.yaml` + `failed_candidates.json` + `trajectory.json` + `gait_optimization_report.md` |
| motion-control | IK 与轨迹控制产物 | `<project>/reports/`：`ik_report.json` + `motion_control_report.json` + `motion_control_report.md`;`<project>/control/`：`ik_solution.json` + `trajectory.json` + `controller_params.yaml` |
| firmware | 固件 dry-run 合同与安全报告 | `<project>/reports/`：`firmware_report.json` + `firmware_test_report.json`;`<project>/firmware/`：`project_manifest.json` + `can_frames.md` + `calibration.json` |
| mujoco-simulation | MuJoCo 场景验证报告 | `<project>/reports/`：`mujoco_result.json` + `mujoco_validation_report.md`;`<project>/simulation/mujoco/results/*.sim_result.json` + `trajectories/*.trajectory.json` |
| fea | 结构 FEA 门禁报告 | `<project>/reports/`：`fea_report.json` + `static_case_report.json` + `fea_checklist.md` |
| wear-fatigue | 磨损/疲劳/维护周期报告 | `<project>/reports/`：`wear_report.json` + `fatigue_report.json` + `maintenance_interval.md` + `wear_fatigue_report.md` |
| robot-dog-digital-twin | 实体样机前编排报告 | `<project>/reports/`：`artifacts.collected.json` + `design_score.json` + `gate_report.json` + `gate_report.md` + `failure_report.md` + `next_iteration_plan.md` |

## 常见 handoff 链路

1. **机械 → viewer**：mechanical 出 `*.step` → `viewer.start(step_path)` → 返回 URL。
2. **机械 → urdf**：mechanical 出多零件 STEP + 关节意图 → urdf 读取生成 `*.urdf` + meshes。
3. **机械 → 制造预检**：STEP → gcode(FDM 预检) / sendcutsend(钣金报价)。
4. **urdf → viewer**：`*.urdf` → viewer cad 引擎(urdf-loader + 关节滑块)。
5. **urdf → srdf**：`*.urdf` → srdf 静态推导自碰撞矩阵 + 规划组 → `*.srdf`。
6. **urdf → sdf**：`*.urdf` + `world.yaml` → sdf 转换 → `world.sdf` + `model.sdf`（Gazebo）。
7. **parts-catalog → mechanical**：找到现成件 → L1 模块路径直接装配 / L2+ STEP `import_step()` 并入。
8. **urdf → simulation**：`*.urdf` + `meshes/` → pybullet headless 跑(base 目录进 search path 解析相对 mesh) → `simulation/<robot>.results.json` + `<robot>.trajectory.json` + 关键帧/截图。
9. **sdf → simulation**：`world.sdf`/`model.sdf` → `loadSDF`(取 `ids[0]`,世界自带地面不叠 plane) → 同上产物。
10. **simulation → viewer(3D 回放)**：`<robot>.trajectory.json` + 原 `*.urdf` → cad 引擎 `?trajectory=` 时间轴回放(关节随时序动);辅 `results.json → engine=sim` 数据面板。
11. **electronics-bom → pcb/circuit-simulation/firmware**：`reports/electronics_bom.json` + `electrical/library/selected_parts.json` → PCB authoring、电源预算和固件 MCU/外设输入。
12. **requirements-verification → robot-dog-digital-twin**：`requirements.yaml` + `verification_matrix.yaml` + `architecture.yaml` + `risk_register.md` → G0/G1 合同输入。
13. **requirements-verification → actuator-sizing**：`requirements.yaml` + `architecture.yaml` + 可选 `actuator_candidate.yaml` → `reports/torque_margin.json` + `reports/actuator_spec.yaml`。
14. **actuator-sizing → robot-dog-digital-twin**：`reports/torque_margin.json` + `reports/actuator_spec.yaml` → G2/G3 执行器 blocker 与设计评分输入。
15. **pcb/mechanical → pcb-mechanical-reliability**：PCB 板尺寸/板厚/连接器/支撑柱/机身间隙 metadata → `reports/pcb_fit.json` + `reports/pcb_reliability_report.json`。
16. **pcb-mechanical-reliability → robot-dog-digital-twin**：`reports/pcb_fit.json` + `reports/pcb_reliability_report.json` → G2/G3 PCB 结构 blocker 与设计评分输入。
17. **pcb/electronics-bom → circuit-simulation**：电源轨/电机驱动/保护/热 metadata → `reports/circuit_check.json` + `reports/power_budget.json` + `reports/thermal_report.json`。
18. **circuit-simulation → robot-dog-digital-twin**：`reports/circuit_check.json` + `reports/power_budget.json` + `reports/thermal_report.json` → G2/G3 电路 blocker 与设计评分输入。
19. **simulation/actuator-sizing → gait-optimization**：步态参数/仿真结果/扭矩裕量 metadata → `reports/gait_score.json` + `reports/best_gait_params.yaml`。
20. **gait-optimization → robot-dog-digital-twin**：`reports/gait_score.json` + `reports/best_gait_params.yaml` → G3 步态 blocker 与设计评分输入。
21. **urdf/mechanical → motion-control**：腿长、关节限位、足端目标和 gait 参数 → `control/trajectory.json` + `control/controller_params.yaml`。
22. **motion-control → simulation/mujoco-simulation/firmware**：`control/trajectory.json` + `controller_params.yaml` → 动力学验证或固件控制参数输入。
23. **motion-control → robot-dog-digital-twin**：`reports/ik_report.json` + `reports/motion_control_report.json` → G3/P1 控制 blocker 与设计评分输入。
24. **electronics-bom/pcb/motion-control → firmware**：MCU/驱动/编码器候选 + CAN/轨迹/安全 metadata → `reports/firmware_report.json` + `firmware/project_manifest.json`。
25. **firmware → robot-dog-digital-twin**：`reports/firmware_report.json` + `firmware/calibration.json` → G4/G5 bring-up blocker 与实体前安全检查输入。
26. **urdf/mjcf/scenarios → mujoco-simulation**：MJCF/URDF + stand/walk/slope/drop/push 场景 → `reports/mujoco_result.json` + `simulation/mujoco/results/*.sim_result.json`。
27. **mujoco-simulation → gait-optimization**：高保真场景指标/轨迹 → `reports/gait_score.json` 的后续真实输入。
28. **mujoco-simulation → robot-dog-digital-twin**：`reports/mujoco_result.json` → G3/P1 动力学 blocker 与设计评分输入。
29. **mechanical → fea**：结构载荷/材料/初步求解 metadata → `reports/fea_report.json` + `reports/static_case_report.json`。
30. **fea → robot-dog-digital-twin**：`reports/fea_report.json` → G3/P1 结构 blocker 与设计评分输入。
31. **mechanical/simulation/gait → wear-fatigue**：齿轮、轴承、足垫、关节、线束、连接器 metadata + 载荷谱 → `reports/wear_report.json` + `reports/fatigue_report.json`。
32. **wear-fatigue → robot-dog-digital-twin**：`reports/wear_report.json` + `reports/fatigue_report.json` + `reports/maintenance_interval.md` → G3/P1 寿命 blocker 与维护建议输入。
33. **多域报告 → robot-dog-digital-twin**：`requirements.yaml` + `verification_matrix.yaml` + `artifacts.json` + 各域报告 → `reports/design_score.json` + `reports/failure_report.md` + `reports/next_iteration_plan.md`。

## 规则

- 产物路径由调用方传入，被调方不臆造路径。
- 被调方只读约定后缀；不认识的后缀返回明确错误，不静默吞。
- 跨子技能流程由父级 `SKILL.md` 编排顺序，子技能只管自己那一段。
