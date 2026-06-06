# KiCad 9.x IPC API 稳定度跟踪(防 P3-1/P3-2 用错栈)

> 结论先行(06 §4.1.4 风险点):**pcb 子技能 P3 落地只用 `kicad-cli`(命令行)**,
> **不用 KiCad 9.x 的 IPC Python API**。本文记录为什么,以及何时可重新评估。

## 为什么现在不用 IPC API

KiCad 9.x 正处于插件/脚本 API 的重构期:
- 旧 `pcbnew` SWIG Python 绑定**正在被弃用**,新的 **IPC API**(基于 gRPC,需 KiCad
  后台进程在跑)还在迭代,9.0/9.1 之间签名仍可能变。
- IPC API 需要启动 KiCad 进程做后台服务,headless/CI 部署成本高,与本 super skill
  「命令行 + 无 GUI 依赖」的调性不符。
- `kicad-cli` 是**稳定的命令行契约**,9.x 全程可用,headless 原生支持,正是我们要的。

## 三栈分工(当前 P3 落地用栈)

| 需求 | 用什么 | 为什么不用 IPC |
|---|---|---|
| 出件(Gerber/STEP/glTF/BOM/DXF) | `kicad-cli`(`export_fab.sh` 等) | CLI 稳定、headless、零后台进程 |
| 从零写原理图 | skidl(`sch_from_skidl.py`) | 纯 Python DSL,不碰 KiCad 内核 |
| 批量改既有工程 | kicad-skip(`batch_edit.py`) | 解析 S-expression,不启动 KiCad |
| 走 GUI 插件流程 | (暂缓)kicad-python IPC | 重构期不稳,见下「重评条件」 |

## 重新评估条件(预计 2026 Q4)

满足以下**全部**再考虑引入 IPC API:
- KiCad 9.x IPC API 文档标 stable(非 experimental),且两个 minor 版本签名未变;
- 出现 `kicad-cli` / skidl / kicad-skip 三者都覆盖不了的需求(如交互式插件、实时 DRC 高亮);
- headless 起 KiCad 后台服务的部署成本被验证可接受(CI 镜像 + 资源)。

任意一条不满足则继续三栈,不开 IPC 这个口子(与 §4.1.3 EasyEDA 退路条款同样的纪律)。

## 参考

- KiCad CLI 文档:https://docs.kicad.org/9.0/en/cli/cli.html
- IPC API(跟踪用,勿据此实装):https://dev-docs.kicad.org/en/apis-and-binding/ipc-api/
- 选型决议:`share/build123d-cad改造/06-电子域扩展-pcb-eda-drc.md` §4.1.4 / §4.2
