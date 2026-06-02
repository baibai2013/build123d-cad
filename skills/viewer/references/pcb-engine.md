# P3 · pcb engine

> 目录就位但未实现。Gate 3 通过 + 首个 PCB 项目立项后落地。

## 选型(规格 §8 已锁)

| 后缀 | 工具 | License | 集成方式 |
|---|---|---|---|
| `.gbr .ger .drl .gtl .gbl`(Gerber) | tracespace | MIT | 纯 web,放 `engines/pcb/dist/` |
| `.kicad_pcb`(2D) | tracespace | MIT | 同上 |
| `.kicad_pcb`(3D) | `kicad-cli pcb export gltf` → cad engine | KiCad GPL-3(仅命令行调用,不污染) | server 端调命令落 GLB cache,URL 改走 cad |

## 实现路线图

1. 装 KiCad 9+(系统级,通过 `brew install kicad`)
2. `engines/pcb/` 引入 tracespace 静态产物
3. server.mjs 加 `?as_3d=true` 触发 KiCad CLI 转换(写 `/tmp/build123d-cad-viewer/glb-cache/<sha>.glb`)
4. `references/pcb-engine.md` 展开实现细节
5. `tests/test_pcb_engine.py` 去 skip,加端到端

## 不在范围

- ❌ PCB 编辑(只预览)
- ❌ DRC 检查(归 06-电子域 drc 子技能)
