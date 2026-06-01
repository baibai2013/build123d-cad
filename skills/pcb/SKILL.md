# pcb — PCB / EDA 设计（WIP，P3）

> 占位子技能。启动条件：用户给出第一个 PCB 项目时。

## 路线图（P3）
- KiCad 集成：skidl / kicad-python / kibot
- DRC 自动化：KiBot 报告
- 与 viewer 联动：`kicad-cli pcb export gltf` → GLB 走 viewer cad 引擎；Gerber 走 tracespace
- 与 mechanical 联动：外壳 ⇄ PCB 边框（DXF/STEP 互导，见 shared/handoff-protocols.md）

## 现状
未实现。references/ scripts/ 为空占位。
