# kicad-cli 速查(KiCad 9.x)

> pcb 子技能只用 `kicad-cli`(命令行稳定),不碰 IPC Python API(见 kicad-9-ipc-status.md)。
> 本表是 `scripts/export_fab.sh` 等脚本调用的命令底层;手动 debug 时直接照抄。

定位(脚本 `find_kicad_cli` / `pcb_common.which_kicad_cli` 的候选):
- macOS:`/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli`
- Linux/PATH:`kicad-cli`
- 版本确认:`kicad-cli version`(应 ≥ 9.0)

## PCB 出件

| 目的 | 命令 | 产物 |
|---|---|---|
| Gerber | `kicad-cli pcb export gerbers --output <dir>/ <board>.kicad_pcb` | 各层 .gbr |
| 钻孔 | `kicad-cli pcb export drill --output <dir>/ <board>.kicad_pcb` | .drl |
| STEP(含元件 3D) | `kicad-cli pcb export step --output <out>.step <board>.kicad_pcb` | .step |
| glTF/glb(给 viewer) | `kicad-cli pcb export glb --output <out>.glb <board>.kicad_pcb` | .glb |
| 贴片坐标 | `kicad-cli pcb export pos --format csv --units mm --output <out>-pos.csv <board>.kicad_pcb` | -pos.csv |
| 板框 DXF(给 mechanical) | `kicad-cli pcb export dxf --layers "Edge.Cuts" --output <dir>/ <board>.kicad_pcb` | .dxf |
| DRC(归 drc 子技能) | `kicad-cli pcb drc --output <out>.json --format json <board>.kicad_pcb` | drc.json |

## 原理图

| 目的 | 命令 | 产物 |
|---|---|---|
| BOM | `kicad-cli sch export bom --output <out>-bom.csv <board>.kicad_sch` | -bom.csv |
| 网表 | `kicad-cli sch export netlist --output <out>.net <board>.kicad_sch` | .net |
| ERC(归 drc) | `kicad-cli sch erc --output <out>.json --format json <board>.kicad_sch` | erc.json |
| PDF | `kicad-cli sch export pdf --output <out>.pdf <board>.kicad_sch` | .pdf |
| SVG(给 viewer sch 引擎) | `kicad-cli sch export svg --output <dir>/ <board>.kicad_sch` | .svg |

## 注意

- `gerbers` / `drill` / `dxf` 的 `--output` 收的是**目录**(末尾带 `/`),按层命名;
  其余多数收**文件路径**。export_fab.sh 据此把 Gerber 先导到临时目录再打包 zip。
- `export glb` 是 KiCad 9.0 新增;旧版用 `export step` 退路(viewer 仍可走 cad 引擎看 STEP→需先转,或直接 KiCanvas 渲 .kicad_pcb)。
- 所有命令不需要 GUI / X11,headless 可跑,适合 CI。
- 出件不跑 DRC/ERC —— 那是 `drc` 子技能职责(`run_drc.sh` 显式触发)。
