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
| simulation | 动力学仿真记录 | `output/<task>/simulation/`：`<robot>.results.json`(时序+汇总+checks) + `frames/*.png`(+ `manifest.json`) + `<robot>.sim.mp4`(有 imageio/cv2 才出) + `_verify/{static.png,settled.png,checklist.txt}` |

## 常见 handoff 链路

1. **机械 → viewer**：mechanical 出 `*.step` → `viewer.start(step_path)` → 返回 URL。
2. **机械 → urdf**：mechanical 出多零件 STEP + 关节意图 → urdf 读取生成 `*.urdf` + meshes。
3. **机械 → 制造预检**：STEP → gcode(FDM 预检) / sendcutsend(钣金报价)。
4. **urdf → viewer**：`*.urdf` → viewer cad 引擎(urdf-loader + 关节滑块)。
5. **urdf → srdf**：`*.urdf` → srdf 静态推导自碰撞矩阵 + 规划组 → `*.srdf`。
6. **urdf → sdf**：`*.urdf` + `world.yaml` → sdf 转换 → `world.sdf` + `model.sdf`（Gazebo）。
7. **parts-catalog → mechanical**：找到现成件 → L1 模块路径直接装配 / L2+ STEP `import_step()` 并入。
8. **urdf → simulation**：`*.urdf` + `meshes/` → pybullet headless 跑(base 目录进 search path 解析相对 mesh) → `simulation/<robot>.results.json` + 关键帧/截图。
9. **sdf → simulation**：`world.sdf`/`model.sdf` → `loadSDF`(取 `ids[0]`,世界自带地面不叠 plane) → 同上产物。

## 规则

- 产物路径由调用方传入，被调方不臆造路径。
- 被调方只读约定后缀；不认识的后缀返回明确错误，不静默吞。
- 跨子技能流程由父级 `SKILL.md` 编排顺序，子技能只管自己那一段。
