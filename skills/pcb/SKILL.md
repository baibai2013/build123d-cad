---
name: pcb
description: PCB 板级电气设计 — KiCad 9.x CLI 集成 / skidl 脚本化原理图 / 一键出件
owner: hardware
status: scaffolded            # 脚本骨架已落地;真出件需装 KiCad 9.x + Gate 3 给真实项目
phase: P3
since: 2026-06-03
---

# pcb 子技能

板级电气设计**入口**:生成 KiCad 工程文件、命令行驱动一键出件。
职责正交三件事不越界:DRC/ERC → `drc`;元件查料/选型 → `electronics-bom`;3D 渲染 → `viewer`。

> **落地状态(2026-06-03)**:scripts 骨架已实现(`new_project.py` 无需 KiCad 即可跑;
> 其余 kicad-cli/skidl 包装在工具缺失时 **fail-loud 给安装提示**,不静默)。
> 真出件需 sysadmin 装 KiCad 9.x + Gate 3 给出首个真实 PCB 项目。

## 触发场景(关键词)

父级 SKILL.md 路由命中本技能(与 [父级路由表](../../SKILL.md) 同步):
- 「PCB / 原理图 / Gerber / 出件 / kicad / 板子 / EDA」
- 「skidl / kicad-cli / 板框 DXF / 多层板 / 走线」

不命中场景(走别的 skill):
- 「DRC / ERC / 制造检查」 → `drc`(P3 同期建)
- 「元件型号 / 封装 / JLCPCB / 找料」 → `electronics-bom`
- 「PCB 3D 预览」 → `viewer`(本技能出 STEP/glTF,viewer 渲)

## 能力清单

| 能力 | 入口 | 输出 | 依赖 |
|---|---|---|---|
| 起空白 KiCad 工程 | `scripts/new_project.py <name>` | `.kicad_pro/.kicad_pcb/.kicad_sch` 三件套 | 无(纯模板,可跑) |
| skidl → 原理图网表 | `scripts/sch_from_skidl.py <design.py>` | `.net`(KiCad import 变 `.kicad_sch`) | skidl |
| 一把出 fab | `scripts/export_fab.sh <board>.kicad_pcb` | gerbers.zip + STEP + glb + pos + bom | kicad-cli |
| 仅出 STEP(给机械) | `scripts/pcb_to_step.sh <board>` | `<board>.step` | kicad-cli |
| 仅出板框 DXF | `scripts/pcb_to_dxf.sh <board>` | `<board>.dxf`(Edge.Cuts) | kicad-cli |
| 批量改既有工程 | `scripts/batch_edit.py <board> --rule rules.yaml` | 改后工程(默认 dry-run) | kicad-skip |

工具栈(06 §4 选型,无异议):主链 **KiCad 9.x `kicad-cli`**(命令行稳定,
**不碰 IPC API** 见 `references/kicad-9-ipc-status.md`);原理图 **skidl**(新建)+
**kicad-skip**(改既有);出件 kicad-cli(快 check)+ KiBot(release,归 `drc`)。

## 输出物

全落 `output/<task>/electrical/`(08 §2.0):
- 工程三件套 `<board>.{kicad_pro,kicad_pcb,kicad_sch}`
- `fab/<board>-gerbers.zip`(Gerber + 钻孔)
- `fab/<board>.step`(给 mechanical 装配)/ `fab/<board>.glb`(给 viewer 3D)
- `fab/<board>.dxf`(板框,给 mechanical 挖孔)
- `fab/<board>-pos.csv` / `fab/<board>-bom.csv`(贴片厂)

## 与其他 skill 的接口(handoff)

- **→ mechanical**:`fab/<board>.dxf`(板框,build123d 读做外壳让位)+ `<board>.step`(装配间隙验证)
- **→ viewer**:`<board>.glb`(engine=cad 3D)/ `.kicad_pcb`(engine=pcb,KiCanvas 直渲)
- **→ drc**:出件后由用户/agent 显式调 `drc/run_drc.sh`,pcb **不**自动跑(职责分离)
- **← electronics-bom(文件接口,非互引用)**:`sch_from_skidl.py --library library.json`
  读 electronics-bom 落盘的 `output/<task>/electrical/library/library.json`(料→封装)。
  **不** subprocess 反向调 `lookup.py` —— 那会违反 [08 §1](../../shared/handoff-protocols.md) 零互引用红线。
  由 agent/父 SKILL 编排:先调 electronics-bom 出 library.json,再跑本技能。
  (解了 06 §3.3a.2 标注的全项目唯一一处红线冲突。)

## viewer 预览页签(P3-6/P3-7,与本技能同期落地)

viewer 路由已就位(`scripts/backend/router.mjs`:`.kicad_pcb`/`.gbr*`→engine=pcb,
`.kicad_sch`/`.svg`→engine=sch,`.glb`→engine=cad),无需改路由,只换占位页:
- **engine=pcb**:`tracespace` 渲 gerbers 2D(图层开关)+ **KiCanvas** 直渲 `.kicad_pcb` 3D;
  pcb skill 出的 `.glb` 走 cad 引擎看带元件精细 3D。2D/3D 页签切换。
- **engine=sch**:KiCanvas 渲 `.kicad_sch`。
- 依赖纯前端(tracespace / KiCanvas 单 ESM bundle),**预构建 vendoring** 进 `engines/`,
  不 npm install(00 §6 红线)。详见 viewer skill `engines/pcb/`。

## 不做什么

- ❌ 自动布线(KiCad 自带 Freerouting)
- ❌ 高速 SI/PI 仿真(超范围,留 P4+)
- ❌ 实时编辑器(viewer 只预览,编辑走 KiCad GUI)
- ❌ DRC/ERC(归 `drc`)

## 参考资料

- `references/kicad-cli-cheatsheet.md` — kicad-cli 全命令速查
- `references/skidl-quickstart.md` — skidl 写第一份原理图 + 料库文件接口
- `references/kicad-9-ipc-status.md` — 为什么只用 CLI 不用 IPC API
- 选型材料:`share/build123d-cad改造/06-电子域扩展-pcb-eda-drc.md` §3.3a.1 / §4
