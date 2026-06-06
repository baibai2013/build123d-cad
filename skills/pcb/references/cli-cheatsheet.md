# tscircuit CLI(`tsci`)速查 — 实测 0.0.1829

> 权威:https://docs.tscircuit.com/command-line。本表标「实测」者为 M0 在本机验证过的真实行为。
> 工具缺失时本技能脚本 fail-loud,不静默。

## 安装(实测:依赖 bun)

```bash
# tsci 来自 tscircuit 包(bin=tsci/tscircuit),且运行时依赖 bun
curl -fsSL https://bun.sh/install | bash      # 先装 bun
bun add -g tscircuit                            # 装 tsci(Rosetta 机必须用 bun 装,否则 @resvg 原生库架构不匹配)
tsci version                                    # 自检
tsci doctor                                     # 环境诊断
```

> ⚠️ 用 `npm i -g tscircuit` 在 Apple Silicon + Rosetta 下会报 `Cannot find module @resvg/resvg-js-darwin-arm64`。用 bun 装可避开。

## 项目生命周期(实测)

| 命令 | 用途 | 备注 |
|---|---|---|
| `tsci init [dir] -y` | 起新项目 | **入口文件 `index.circuit.tsx`**(不是 index.tsx);`--no-install` 跳依赖 |
| `tsci dev [file]` | 本地预览 server | :3020,PCB/原理图/3D 页签 |
| `tsci build [file]` | 编译 | 输出 **`dist/<entry>/circuit.json`**;**默认跑 DRC**;`--pcb-png <f>` 出图 |
| `tsci check` | 分阶段预检 | 子命令 `netlist`/`placement`/`routing`;**官方标 under-development**,当辅助 |
| `tsci snapshot [--3d]` | 出快照 | `__snapshots__/*-pcb.snap.svg` + `-schematic.snap.svg` + `-3d.snap.png`;`-u` 更新 |
| `tsci export -f <fmt> -o <out>` | 导出 | 见下 |
| `tsci transpile` | TSX→JS | — |

## 元件 / 包(实测命令存在)

| 命令 | 用途 |
|---|---|
| `tsci search <query...>` | 搜 footprint/CAD模型/包 |
| `tsci add <packageSpec>` | 装组件包 |
| `tsci import <query...>` | 从 JLCPCB / registry 导入(嘉立创料号可直接导) |
| `tsci clone <pkg>` / `tsci install` | 克隆 / 装依赖 |
| `tsci push` | 发布到 registry(**仅用户显式要求时**) |
| `tsci login` / `auth` | 登录(`autorouter="auto-cloud"` 云布线需要) |

## DRC(实测:`tsci build` 默认跑,可分类豁免)

```bash
tsci build index.circuit.tsx          # 默认跑 DRC;出错 exit 1
# 开发期可分类豁免(出件前必须不带豁免复跑):
#   --ignore-netlist-drc  --ignore-pin-specification-drc
#   --ignore-placement-drc(布局重叠)  --ignore-routing-drc(未布通/间距)
#   --ignore-errors  --ignore-warnings
```

`tsci check netlist|placement|routing` 是快速预检,但官方标 under-dev → **以 build 的 DRC 为权威**。

## export 格式表(`tsci export -f <fmt>`,实测全可出)

| fmt | 产物 | 下游 |
|---|---|---|
| `gerbers` | Gerber 出件(**zip 实测**) | 嘉立创/PCBWay 上传 |
| `step` | STEP 3D 模型 | mechanical 装配 / viewer |
| `glb` / `gltf` | glTF 3D | viewer `?engine=cad`(已 ready) |
| `pcb-svg` / `schematic-svg` / `assembly-svg` | 2D SVG | viewer / 文档 / 审图 |
| `specctra-dsn` / `srj` | 布线问题格式 | Freerouting / 自定义布线 |
| `kicad_pcb` / `kicad_zip` / `kicad-library` | KiCad 文件/工程/库 | KiCad GUI 兜底 |
| `readable-netlist` / `circuit-json`(默认 json) | 网表 / circuit.json | AI/人审 / 程序化 |

> **无独立 `bom` / `cpl` 格式**(实测 export 列表里没有)→ BOM/CPL 从 circuit.json 的
> `source_component` 派生(build 已自动配嘉立创料号),或走 `tsci dev` fabrication 面板。
