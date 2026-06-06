# PCB 预览 / 3D:三条路径

> 目标:统一预览(viewer),但 tscircuit 自身也能快看。按场景选路。

## 路径对照

| 路径 | 命令 | 看什么 | 何时用 |
|---|---|---|---|
| **① tscircuit 原生** | `tsci dev`(:3020)/ `tsci snapshot --3d` | PCB / 原理图 / 3D(交互或快照 PNG+SVG) | 写代码时快速迭代、出审图快照 |
| **② glb → viewer cad** | `export -f glb` → `viewer/start.sh <glb>` | 3D(Three.js GLTFLoader,已 ready) | 统一进仓库预览 / 分享链接 / headless 快照 |
| **③ gerber/kicad_pcb → viewer pcb** | `export -f gerbers`/`kicad_pcb` → viewer `?engine=pcb` | 2D Gerber(tracespace)/ 3D(KiCanvas) | viewer engine=pcb 落地后(P3 scaffolded) |

## ① tscircuit 原生(最快)

```bash
tsci dev                  # 浏览器 :3020,PCB/原理图/3D 页签
tsci snapshot --3d        # 出 __snapshots__/*-{pcb.snap.svg,schematic.snap.svg,3d.snap.png}
```
实测 3D 快照能正确渲染元件 + 走线 + 板框。

## ② glb → 仓库 viewer engine=cad(统一预览,推荐)

```bash
tsci export index.circuit.tsx -f glb -o output/<task>/electrical/3d/<board>.glb
bash ../viewer/scripts/start.sh output/<task>/electrical/3d/<board>.glb
# stdout: http://127.0.0.1:<port>/?engine=cad&dir=...&file=<board>.glb
```
- `.glb` 实测可导(M0 出 30KB),viewer `engine=cad` 已 ready(GLTFLoader)。
- headless 快照走 viewer 的 `web_preview.py --snapshot`(接 cad-vision-verify 做视觉验证)。

## ③ gerber/kicad_pcb → viewer engine=pcb(P3 scaffolded)

viewer 的 pcb 引擎骨架已就位(tracespace 渲 Gerber 2D + KiCanvas 渲 .kicad_pcb 3D),
但 bundle 未 vendoring。落地后:
```bash
tsci export ... -f gerbers -o .../fab/<board>-gerbers.zip   # → viewer ?engine=pcb(2D)
tsci export ... -f kicad_pcb -o .../<board>.kicad_pcb        # → viewer ?engine=pcb(KiCanvas 3D)
```

## 统一预览(M2/M3 已落地 ✅,推荐主路径)

viewer 新引擎 **`engine=tscircuit`**(React 直引 `@tscircuit/runframe`,单文件 bundle vendored
进 `engines/tscircuit/dist/`):PCB/原理图/3D 三页 + 自建 BOM/总价面板。

```bash
# export_fab.sh 已自动产出 <board>.circuit.json + <board>.bom.json;直接:
bash ../viewer/scripts/start.sh output/<task>/electrical/<board>.circuit.json
# → http://127.0.0.1:<port>/?engine=tscircuit&dir=...&file=<board>.circuit.json
```
- `.circuit.json` 经 router 自动路由到 `engine=tscircuit`(排在 `.json` ambiguous 之前)。
- BOM 面板读同目录 `<board>.bom.json`(`bom_price.py` 免key定价);无则只显 BOM 不显价。
- 验证用 **playwright headless**(headless chromium 开 `--use-angle=swiftshader` 出 WebGL)。
- 实现细节见 `viewer/scripts/engines/tscircuit/viewer-src/README.md`。
