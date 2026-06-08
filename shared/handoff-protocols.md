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
| simulation | 动力学仿真记录 | `output/<task>/simulation/`：`<robot>.results.json`(时序+汇总+checks) + `<robot>.trajectory.json`(cad 引擎 3D 回放格式) + `frames/*.png`(+ `manifest.json`) + `<robot>.sim.mp4`(有 imageio/cv2 才出) + `_verify/{static.png,settled.png,checklist.txt}` |
| requirements-verification | 需求合同与验证矩阵 | `<project>/`：`requirements.yaml` + `verification_matrix.yaml` + `architecture.yaml` + `risk_register.md`;校验报告 `<project>/reports/requirements_validation.{json,md}` |
| actuator-sizing | 执行器裕量报告 | `<project>/reports/`：`torque_margin.json` + `actuator_spec.yaml` + `actuator_sizing_report.md` |
| pcb-mechanical-reliability | PCB 结构可靠性报告 | `<project>/reports/`：`pcb_fit.json` + `pcb_reliability_report.json` + `connector_clearance.json` + `pcb_mechanical_report.md` |
| circuit-simulation | 电路/电源/热风险报告 | `<project>/reports/`：`circuit_check.json` + `power_budget.json` + `thermal_report.json` + `protection_checklist.md` + `circuit_simulation_report.md` |
| gait-optimization | 步态评分与参数建议 | `<project>/reports/`：`gait_score.json` + `best_gait_params.yaml` + `failed_candidates.json` + `trajectory.json` + `gait_optimization_report.md` |
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
11. **requirements-verification → robot-dog-digital-twin**：`requirements.yaml` + `verification_matrix.yaml` + `architecture.yaml` + `risk_register.md` → G0/G1 合同输入。
12. **requirements-verification → actuator-sizing**：`requirements.yaml` + `architecture.yaml` + 可选 `actuator_candidate.yaml` → `reports/torque_margin.json` + `reports/actuator_spec.yaml`。
13. **actuator-sizing → robot-dog-digital-twin**：`reports/torque_margin.json` + `reports/actuator_spec.yaml` → G2/G3 执行器 blocker 与设计评分输入。
14. **pcb/mechanical → pcb-mechanical-reliability**：PCB 板尺寸/板厚/连接器/支撑柱/机身间隙 metadata → `reports/pcb_fit.json` + `reports/pcb_reliability_report.json`。
15. **pcb-mechanical-reliability → robot-dog-digital-twin**：`reports/pcb_fit.json` + `reports/pcb_reliability_report.json` → G2/G3 PCB 结构 blocker 与设计评分输入。
16. **pcb/electronics-bom → circuit-simulation**：电源轨/电机驱动/保护/热 metadata → `reports/circuit_check.json` + `reports/power_budget.json` + `reports/thermal_report.json`。
17. **circuit-simulation → robot-dog-digital-twin**：`reports/circuit_check.json` + `reports/power_budget.json` + `reports/thermal_report.json` → G2/G3 电路 blocker 与设计评分输入。
18. **simulation/actuator-sizing → gait-optimization**：步态参数/仿真结果/扭矩裕量 metadata → `reports/gait_score.json` + `reports/best_gait_params.yaml`。
19. **gait-optimization → robot-dog-digital-twin**：`reports/gait_score.json` + `reports/best_gait_params.yaml` → G3 步态 blocker 与设计评分输入。
20. **多域报告 → robot-dog-digital-twin**：`requirements.yaml` + `verification_matrix.yaml` + `artifacts.json` + 各域报告 → `reports/design_score.json` + `reports/failure_report.md` + `reports/next_iteration_plan.md`。

## 规则

- 产物路径由调用方传入，被调方不臆造路径。
- 被调方只读约定后缀；不认识的后缀返回明确错误，不静默吞。
- 跨子技能流程由父级 `SKILL.md` 编排顺序，子技能只管自己那一段。
