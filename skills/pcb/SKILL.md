---
name: pcb
description: PCB 板级电气设计 — KiCad 9.x CLI 集成 / skidl 脚本化原理图 / 一键出件。当前为 P3 占位
owner: hardware
status: WIP
phase: P0-stub
since: 2026-06-02
---

# pcb 子技能(P3 占位)

> **当前状态:WIP**。触发条件 = 用户给出第一个 PCB 项目 + Gate 3 通过。
> P0 阶段不要调用本子技能,父级路由命中应回答「电子域 P3 启动,见
> `share/build123d-cad改造/06-电子域扩展-pcb-eda-drc.md`」。

## 触发场景(关键词)

父级 SKILL.md 路由命中本技能的关键词(与 [父级路由表](../../SKILL.md) 第 60 行同步):

- 「PCB / 原理图 / Gerber / 出件 / kicad / 板子 / EDA」
- 「skidl / kicad-cli / 板框 DXF」
- 「板级电气 / 多层板 / 走线」

不命中场景(走别的 skill):
- 「DRC / ERC / 制造检查」 → 未来的 `drc` skill(P3 启动同期建)
- 「元件型号 / 封装 / JLCPCB / 找料」 → `electronics-bom`
- 「PCB 3D 预览」 → `viewer`(本技能负责出 STEP/glTF,不做渲染)

## P3 路线图

落地任务详见 [06 §3 P3 路线图](../../../share/build123d-cad改造/06-电子域扩展-pcb-eda-drc.md#3-p3-路线图落地任务卡):

| # | 任务 | 工作量 | 验收 |
|---|---|---|---|
| P3-1 | KiCad CLI 任务模式 | 2d | 一条命令 `.kicad_pcb` → Gerber+STEP+3D |
| P3-2 | skidl 脚本化原理图 | 2d | Python → `.net` → KiCad import |
| P3-4 | DRC/ERC 自动化(KiBot) | 1d | YAML 一键出 DRC PDF |
| P3-5 | 机械 ⇄ PCB 边框互导 | 1d | DXF 双向跑通 |
| P3-6 | viewer/pcb 引擎对接 | 2d | 浏览器开 `.kicad_pcb` 看 3D + Gerber |

主工具链选型(详见 [06 §4](../../../share/build123d-cad改造/06-电子域扩展-pcb-eda-drc.md#4-kicad-工具链选型预研gate-3-决策材料)):

| 决策项 | 推荐 | 理由(一句) |
|---|---|---|
| EDA 主工具 | **KiCad 9.x** | GPL + CLI 完整 + S-expression 文本(git 友好) |
| 原理图脚本化 | **skidl + kicad-skip** | Pythonic + 与 build123d 风格一致 |
| DRC / 出件 | **KiBot + kicad-cli** | 单测用 cli,release 用 KiBot |
| 3D 模型源 | **packages3D + SnapEDA** | 主流料齐 + 自动下载 |
| 机械⇄PCB | **DXF + STEP** | KiCad/build123d 双向直读 |

## 计划能力清单(P3 启动后填)

P3-1 起本节膨胀为完整的 scripts / tests / 输出物表(见 [06 §3.3a.1](../../../share/build123d-cad改造/06-电子域扩展-pcb-eda-drc.md#33a1-skillspcb--板级电气设计入口))。

P0 阶段保留下面占位条目,P3 启动时由 hardware 替换为真实命令:

- [ ] `scripts/new_project.py` — 起空白 KiCad 工程骨架(P3-1)
- [ ] `scripts/sch_from_skidl.py` — skidl Python → 原理图(P3-2)
- [ ] `scripts/export_fab.sh` — 一把出 Gerber+STEP+glTF+Pos+BOM(P3-1)
- [ ] `scripts/pcb_to_step.sh` / `pcb_to_dxf.sh` — 给 mechanical 用(P3-5)
- [ ] `scripts/batch_edit.py` — kicad-skip 批量改既有工程(P3-2)

## 与其他 skill 的接口(handoff,P3 起)

- **本技能 → mechanical**:`output/<task>/electrical/fab/<board>.dxf`(板框)+ `<board>.step`
- **本技能 → viewer**:`<board>.glb` 或 `.kicad_pcb` → engine=cad / engine=pcb
- **本技能 → drc**(P3 新增):产出 `.kicad_pcb` 后由 drc skill 跑规则
- **本技能 ← electronics-bom**:`sch_from_skidl.py` 通过 subprocess 调 `electronics-bom/scripts/lookup.py` 查料(命令行隔离,详见 [06 §3.3a.2](../../../share/build123d-cad改造/06-电子域扩展-pcb-eda-drc.md#33a2-skillselectronics-bom--元件库管理原-44-数据源策略的实现))

## 不做什么

- ❌ 自动布线(KiCad 自带 Freerouting 已可用)
- ❌ 高速 SI/PI 仿真(超出本 super skill 范围,留 P4+)
- ❌ 实时编辑器(viewer 只预览,编辑走 KiCad GUI)
- ❌ DRC / ERC(归 drc skill,职责分离)

## 参考资料

- KiCad CLI: https://docs.kicad.org/9.0/en/cli/cli.html
- skidl: https://github.com/devbisme/skidl
- kicad-skip: https://github.com/psychogenic/kicad-skip
- KiBot: https://github.com/INTI-CMNB/KiBot
- 选型材料: `share/build123d-cad改造/06-电子域扩展-pcb-eda-drc.md`
