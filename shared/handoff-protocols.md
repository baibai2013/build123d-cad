# 子技能串接协议 (handoff-protocols)

子技能之间**不直接函数调用、不互引 references**，只通过**文件标准接口**交换。统一工作区：`output/<task>/`。

## 标准产物约定

| 产出方 | 产物 | 路径约定 |
|---|---|---|
| mechanical | 零件/装配 | `output/<task>/<part>.step`（+ `.stl`/`.glb` 可选 sidecar） |
| urdf | 机器人描述 | `output/<task>/<robot>.urdf` + `output/<task>/meshes/` |
| viewer | 预览 URL | stdout 返回 `http://127.0.0.1:<port>/?engine=<e>&dir=&file=` |
| gcode | 切片报告 | `output/<task>/<part>.slice.json` |
| sendcutsend | 报价/DXF | `output/<task>/<part>.dxf` + `quote.json` |

## 常见 4 条 handoff

1. **机械 → viewer**：mechanical 出 `*.step` → `viewer.start(step_path)` → 返回 URL。
2. **机械 → urdf**：mechanical 出多零件 STEP + 关节意图 → urdf 读取生成 `*.urdf` + meshes。
3. **机械 → 制造预检**：STEP → gcode(FDM 预检) / sendcutsend(钣金报价)。
4. **urdf → viewer**：`*.urdf` → viewer cad 引擎(urdf-loader + 关节滑块)。

## 规则

- 产物路径由调用方传入，被调方不臆造路径。
- 被调方只读约定后缀；不认识的后缀返回明确错误，不静默吞。
- 跨子技能流程由父级 `SKILL.md` 编排顺序，子技能只管自己那一段。
