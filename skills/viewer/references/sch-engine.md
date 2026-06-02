# P3 · sch engine

> 目录就位但未实现。Gate 3 通过后落地。

## 选型

| 后缀 | 工具 | License | 集成方式 |
|---|---|---|---|
| `.kicad_sch .sch` | KiCanvas | MIT | 纯 web,单 ES module,`<kicanvas-embed src="/files/...">` |
| `.svg`(原理图导出) | 原生 `<img>` | — | `<img src="/files/...">` + 缩放 |

## 实现路线图

1. `engines/sch/` 引入 KiCanvas 静态产物
2. `index.html` 单页面:解析 `?file=`,根据后缀分支(`.kicad_sch` 走 KiCanvas;`.svg` 走 `<img>`)
3. `tests/test_sch_engine.py` 去 skip
