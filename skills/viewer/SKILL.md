---
name: viewer
description: 多引擎网页预览(STEP/STL/GLB/URDF/G-code/DXF 实跑;PCB/SCH/SIM 占位 P3)。一句话起 server,后缀决定引擎。
---

# viewer — 多引擎网页预览

一句话起 server,后缀决定引擎。CAD 实跑(Three.js),PCB / SCH / SIM 占位待 P3 落地。

## 用法

```bash
bash skills/viewer/scripts/start.sh /abs/path/to/<file> [workspace_root]
# stdout 唯一一行: http://127.0.0.1:<port>/?engine=<cad|pcb|sch|sim>&dir=...&file=...
```

```python
from web_preview import start
url = start("/abs/path/to/hip_bracket.step")  # 拿 URL 直接打开
```

## 后缀路由表(33 后缀 / 21 条目权威表见 `scripts/backend/router.mjs`)

| 后缀 | 引擎 | 状态 |
|---|---|---|
| `.step .stp .brep .stl .glb .gltf .3mf` | cad | ready |
| `.iges .igs .obj` | cad | P1 |
| `.fcstd` | cad | P3(需 FreeCAD CLI) |
| `.urdf .srdf .sdf` | cad | ready |
| `.gcode .nc` | cad | ready(toolpath ribbon) |
| `.dxf` | cad | ready(2D) |
| `.png .jpg .jpeg .webp` | cad | ready(inline `<img>`) |
| `.kicad_pcb .gbr .ger .drl .gtl .gbl` | pcb | stub(P3) |
| `.kicad_sch .sch .svg` | sch | stub(P3) |
| `.csv .mp4 .webm` | sim | stub(P3) |
| `.json` | ambiguous | 需 `?engine=sim` 显式透传(否则 server 回 409) |

扩支持新格式 = `scripts/backend/router.mjs` 加一行 + `scripts/engines/<name>/` 放静态文件。

## URL 协议(对外稳定接口)

```
http://127.0.0.1:<port>/?engine=<cad|pcb|sch|sim>&dir=<abs-dir>&file=<rel-file>
```

完整字段约束 + 安全规则见 `references/url-protocol.md`。跨子技能改动须在 `shared/dependencies.md` 同步。

## 启动行为

- 默认端口 4178(沿用 cad-viewer);冲突时跳 4188-4197,共 20 候选。
- 复用判定:GET `/__cad/server` → `app="build123d-cad/viewer"` + `serverApiVersion>=2` + `workspaceRoot` 一致 + `git` 一致。
- shutdown:默认 `--shutdown-after 12h`,每请求重置;`POST /__cad/shutdown` 优雅关停(仅 127.0.0.1)。
- 仅监听 127.0.0.1,不绑公网。

## 退出码(start.sh)

`0` 成功 / `2` 后缀不支持或参数错 / `3` 文件不存在 / `4` 端口分配失败

## 安全约束

- `?dir` 必须在 `--workspace-root` 内,否则 403
- `?file` 防 `..` 穿越,否则 403
- 文件代理白名单:路由表所有后缀 + `.json/.yaml/.yml`,其它 415

## 测试

```bash
cd skills/viewer && pytest tests/ -v
```

CI 必跑(无浏览器,~9s):`test_routing` / `test_url_assembly` / `test_placeholders`
本地必跑(起 server):`test_start` / `test_server_reuse` / `test_cad_engine`
P3 待落地:`test_{pcb,sch,sim}_engine.py`(skip)

## 子页面索引

- `references/url-protocol.md` — URL 协议字段约束 + 安全
- `references/routing.md` — 路由表(扩展核心)
- `references/server-reuse.md` — 端口/pid/git/workspace 复用规则
- `references/cad-engine.md` — Three.js + 各 loader 集成
- `references/headless-fallback.md` — P1:Web → OCP → VTK 降级链
- `references/viewer-features.md` `moveit2-server.md` — 复刻 cad-viewer 细节
- `references/pcb-engine.md` `sch-engine.md` `sim-engine.md` — P3 路线

## 不集成

- 实时 ROS 数据流 / PCB 编辑器 / FEA 应力云图 / 公网部署 / 用户权限
- 详见 `docs/superpowers/specs/03-viewer.md` §13
