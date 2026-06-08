# 子技能依赖关系 (dependencies)

谁依赖谁。改动被多方依赖的子技能（viewer 尤甚）时，需跑相关方的 smoke test。

## 依赖图

```
mechanical ──STEP──▶ viewer        (机械产物预览)
mechanical ──STEP──▶ urdf          (转机器人描述)
mechanical ──STEP──▶ gcode         (FDM 切片预检)
mechanical ──STEP/DXF─▶ sendcutsend (钣金报价)
urdf       ──URDF──▶ viewer        (关节可视化)
urdf       ─────────▶ srdf         (MoveIt 规划组基于 URDF)
urdf       ─────────▶ sdf          (Gazebo 世界引用 URDF)
urdf       ──URDF──▶ simulation    (无头动力学跑 + 自验稳定性)
sdf        ──SDF───▶ simulation    (loadSDF 跑世界/模型)
simulation ──trajectory.json──▶ viewer (cad 引擎 3D 回放:URDF + ?trajectory= 时间轴)
simulation ──results.json─────▶ viewer (engine=sim 数据面板:曲线 + 判稳徽章)
parts-catalog ─STEP─▶ mechanical   (现成件并入装配)
pcb        ──circuit.json+bom.json──▶ viewer(engine=tscircuit 统一预览:PCB/原理图/3D + BOM/总价)
pcb        ──glb/svg──▶ viewer      (engine=cad/pcb/sch 单产物预览)
pcb        ──step/dxf─▶ mechanical  (外壳让位/装配间隙)
electronics-bom ─library.json─▶ pcb (选料喂 tsci import,可选上游)
requirements-verification ─requirements.yaml+verification_matrix.yaml─▶ robot-dog-digital-twin (G0/G1 合同输入)
requirements-verification ─requirements.yaml+architecture.yaml─▶ actuator-sizing (执行器扭矩/速度/热裕量输入)
actuator-sizing ─torque_margin.json+actuator_spec.yaml─▶ robot-dog-digital-twin (G2/G3 执行器 blocker 输入)
pcb+mechanical ─pcb_mechanical.yaml/metadata─▶ pcb-mechanical-reliability (PCB 支撑/挠曲/连接器检查)
pcb-mechanical-reliability ─pcb_fit.json+pcb_reliability_report.json─▶ robot-dog-digital-twin (G2/G3 PCB 结构 blocker 输入)
pcb/electronics-bom ─circuit_requirements.yaml/metadata─▶ circuit-simulation (电源预算/保护/热风险检查)
circuit-simulation ─circuit_check.json+power_budget.json+thermal_report.json─▶ robot-dog-digital-twin (G2/G3 电路 blocker 输入)
simulation/actuator-sizing ─gait_validation.yaml/metrics─▶ gait-optimization (步态评分/参数建议)
gait-optimization ─gait_score.json+best_gait_params.yaml─▶ robot-dog-digital-twin (G3 步态 blocker 输入)
urdf/mechanical ─kinematic metadata+motion_plan.yaml─▶ motion-control (IK/步态轨迹生成)
motion-control ─trajectory.json+controller_params.yaml─▶ simulation/mujoco-simulation/firmware (轨迹与控制参数输入)
motion-control ─ik_report.json+motion_control_report.json─▶ robot-dog-digital-twin (G3/P1 控制 blocker 输入)
mujoco-simulation ─mujoco_result.json+*.sim_result.json─▶ gait-optimization (高保真场景指标,后续替换 metadata gait 输入)
mujoco-simulation ─mujoco_result.json+*.sim_result.json─▶ robot-dog-digital-twin (G3/P1 动力学 blocker 输入)
mechanical ─fea_cases.yaml/STEP metadata─▶ fea (结构强度/刚度/模态检查)
fea ─fea_report.json+static_case_report.json─▶ robot-dog-digital-twin (G3/P1 结构 blocker 输入)
mechanical/simulation/gait-optimization ─wear_inputs.yaml/loads─▶ wear-fatigue (齿轮/轴承/足垫/线束/连接器寿命检查)
wear-fatigue ─wear_report.json+fatigue_report.json+maintenance_interval.md─▶ robot-dog-digital-twin (G3/P1 寿命 blocker 输入)
mechanical/pcb/simulation/actuator-sizing/pcb-mechanical-reliability/circuit-simulation/gait-optimization/motion-control/mujoco-simulation/fea/wear-fatigue ─reports─▶ robot-dog-digital-twin (实体前 gate + design_score + failure_report)
robot-dog-digital-twin ─next_iteration_plan.md─▶ mechanical/pcb/simulation (参数迭代建议,不直接 import)
```

## 被依赖度（改动需谨慎）

| 子技能 | 被依赖方 | 改动影响面 |
|---|---|---|
| **viewer** | mechanical / urdf / pcb / simulation（所有要预览的） | 高——改 router/server 跑全量 viewer 测试 |
| **mechanical** | viewer / urdf / gcode / sendcutsend | 高——是产物源头 |
| requirements-verification | robot-dog-digital-twin | 中——改合同 schema 需跑自身和 digital-twin G0 测试 |
| actuator-sizing | robot-dog-digital-twin | 中——改 `torque_margin.json`/`actuator_spec.yaml` 字段需跑自身和 digital-twin gate 测试 |
| pcb-mechanical-reliability | robot-dog-digital-twin / mechanical / pcb | 中——改 `pcb_fit.json`/`pcb_reliability_report.json` 字段需跑自身和 digital-twin gate 测试 |
| circuit-simulation | robot-dog-digital-twin / pcb / electronics-bom | 中——改 `circuit_check.json`/`power_budget.json`/`thermal_report.json` 字段需跑自身和 digital-twin gate 测试 |
| gait-optimization | robot-dog-digital-twin / simulation / actuator-sizing | 中——改 `gait_score.json`/`best_gait_params.yaml` 字段需跑自身和 digital-twin gate 测试 |
| motion-control | simulation / mujoco-simulation / firmware / robot-dog-digital-twin | 中——改 `trajectory.json`/`controller_params.yaml`/`ik_report.json` 字段需跑自身和仿真相关测试 |
| mujoco-simulation | robot-dog-digital-twin / gait-optimization / simulation | 中——改 `mujoco_result.json`/`*.sim_result.json` 字段需跑自身和 digital-twin/gait 相关测试 |
| fea | robot-dog-digital-twin / mechanical | 中——改 `fea_report.json`/`static_case_report.json` 字段需跑自身和 digital-twin gate 测试 |
| wear-fatigue | robot-dog-digital-twin / mechanical / simulation / gait-optimization | 中——改 `wear_report.json`/`fatigue_report.json`/`maintenance_interval.md` 字段需跑自身和 digital-twin gate 测试 |
| robot-dog-digital-twin | 作为编排层读取 mechanical / pcb / simulation / control / manufacturing 报告 | 中——改 gate/score 需跑自身测试 |
| urdf | srdf / sdf / viewer | 中 |
| parts-catalog | mechanical | 低 |

## 独立（无下游）

`bambu-labs`、`gcode`、`sendcutsend`、`srdf`、`sdf` 为链路末端，改动只需自测。
（`simulation` 消费 urdf/sdf 产物，下游产 `trajectory.json`/`results.json` 给 viewer 做 3D 回放/数据面板。）
`robot-dog-digital-twin` 是编排层,只读各域 artifact,不作为底层工具被直接 import。
`requirements-verification` 是合同输入层,产物被 digital-twin 编排层读取。
`actuator-sizing` 是执行器校核层,产物被 digital-twin 编排层读取。
`pcb-mechanical-reliability` 是 PCB 结构可靠性校核层,产物被 digital-twin 编排层读取。
`circuit-simulation` 是电路/电源/热风险校核层,产物被 digital-twin 编排层读取。
`gait-optimization` 是步态评分与参数建议层,产物被 digital-twin 编排层读取。
`motion-control` 是 IK/步态轨迹与控制参数生成层,产物被 simulation/MuJoCo/firmware/digital-twin 读取。
`mujoco-simulation` 是高保真动力学场景校核层,产物被 gait/digital-twin 编排层读取。
`fea` 是结构强度/刚度/模态校核层,产物被 digital-twin 编排层读取。
`wear-fatigue` 是磨损/疲劳/维护周期校核层,产物被 digital-twin 编排层读取。

## 高扇入接口登记

### viewer URL 协议(P0-3 fullstack 2026-06-02 落地)

所有上游(mechanical / urdf / gcode / sendcutsend)只产文件路径,**不直接拼 URL**;
URL 拼装由 `skills/viewer/scripts/start.sh` / `web_preview.py` 统一生成。

```
http://127.0.0.1:<port>/?engine=<cad|pcb|sch|sim>&dir=<abs-dir>&file=<rel-file>
```

- 字段规约:见 `skills/viewer/references/url-protocol.md`
- 健康协议:`GET /__cad/server` → `app="build123d-cad/viewer" + serverApiVersion=2`
- 退出码契约:`0/2/3/4` 见 url-protocol.md §退出码

**改动须知**:viewer URL 协议 / `serverApiVersion` / `engines` 枚举 / `engineImpl` 字段任一改动,
必须在本节升级版本号 + @全员 + 跑各上游 smoke。当前版本 `serverApiVersion=2`(2026-06-02)。

### 后续登记(占位)

- joints schema(P0-4 algorithm,4 + 8)
- output 路径约定(P0-6 tech_lead,§7)
- mechanical→urdf/gcode handoff(P0-2 mechanical,见 02 §X)
