# 路由表(扩展核心)

> 后缀 → 引擎 的映射在 `scripts/backend/router.mjs`,**纯函数**,可单测。
> 加新格式 = 加一行 + 在 `engines/<name>/` 放静态文件,不改 server.mjs。

## 当前映射

| 后缀 | 引擎 | 前端实现 | 状态 |
|---|---|---|---|
| `.step .stp .stl .glb .3mf` | cad | Three.js + STEP→GLB sidecar(OCP 转换) | P0 ready |
| `.urdf .srdf .sdf` | cad | urdf-loader-three + 关节滑块 | P0 ready |
| `.gcode .nc` | cad | Three.js toolpath ribbon(着色按速度/层) | P0 ready |
| `.dxf` | cad | flat 2D viewer(dxf-parser + Canvas) | P0 ready |
| `.kicad_pcb` | pcb | tracespace 2D + `kicad-cli pcb export gltf` 走 cad 拿 3D | P3 |
| `.gbr .ger .drl .gtl .gbl` | pcb | tracespace(纯 web Gerber,MIT) | P3 |
| `.kicad_sch .sch` | sch | KiCanvas(MIT,import 内嵌) | P3 |
| `.svg`(原理图导出) | sch | `<img>` 内嵌 + 缩放 | P3 |
| `.csv`(波形/轨迹) | sim | plotly.js / d3 | P3 |
| `.mp4 .webm`(录屏) | sim | HTML5 video | P3 |
| `.json`(URDF 轨迹回放) | sim | Three.js + 关节时间序列 | P3(显式 `?engine=sim` 透传,router 不 sniff JSON) |

## API

```js
// router.mjs
export const ENGINE_ROUTES = [/* ... */];      // 后缀表
export const SUPPORTED_ENGINES = ['cad','pcb','sch','sim'];
export const SUPPORTED_EXTENSIONS = [/* 拍平后所有支持后缀 + .json/.yaml/.yml */];
export function routeByExtension(filePath);    // → engine 名 或 null
export function listSupportedExtensions();     // 拍平的所有后缀(带点前缀)
```

`routeByExtension` 是**纯函数**(零 IO,大小写不敏感),可在 server.mjs / start.sh / 单测里互通。

## 加新格式 6 步

1. `scripts/backend/router.mjs` 在 `ENGINE_ROUTES` 加一行
2. 把前端打包产物落到 `scripts/engines/<name>/dist/`(必须有 `index.html`);占位则放 `scripts/engines/<name>/index.html`
3. 必要时调整 `scripts/backend/server.mjs` 的 `/assets/*` 路由(P0 默认 cad 优先)
4. `tests/test_<name>_engine.py` 把 `pytest.skip` 换成真测试
5. `references/<name>-engine.md` 写选型和集成
6. `shared/dependencies.md` 登记后缀路由变更 + @全员

## 后缀冲突

- `.json` 用于 urdf 配置 ↔ urdf 轨迹时间序列 ↔ 通用配置文件 → router **不 sniff JSON 顶层 schema**;P3 sim 落地时由调用方显式 `?engine=sim` 透传。
- `.svg` 原理图导出走 sch;通用 SVG(图标/插图)不应进 viewer。
