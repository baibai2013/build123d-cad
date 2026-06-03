# pcb 引擎前端 bundle vendoring

本引擎渲染依赖两个**纯前端**库,按项目红线(00 §6「viewer 不 npm install,dist 预构建」)
**vendoring 进本目录**,不走 npm install:

| bundle | 库 | 用途 | 体积(约) |
|---|---|---|---|
| `kicanvas.js` | [KiCanvas](https://github.com/theacodes/kicanvas) | WebGL 直渲 `.kicad_pcb` / `.kicad_sch`(零导出) | ~1.5 MB(单 ESM) |
| `tracespace.js` | [@tracespace/view](https://github.com/tracespace/tracespace) | 渲 Gerber/gerbers.zip → 分层 SVG | ~0.5 MB |

## 拉取

```bash
bash vendor_assets.sh
```

脚本用 curl 从 CDN/release 拉预构建产物落到本目录,**不联网时本引擎降级**为
「bundle 未 vendoring」提示页(index.html 的 vendorMissing),不报错。

## 落地后「ready」提升

vendoring 完成且端到端验证(P3-9)通过后,把 `index.html` + `vendor/` 提升到
`engines/pcb/dist/index.html`,父 server(server.mjs §124)即把 pcb 引擎识别为
**ready**(非 stub),viewer 健康表 engines.pcb 转 ready。

## 注意

- KiCanvas 注册 `<kicanvas-embed>` web component,`src` 指向父 server 的
  `/files/<board>.kicad_pcb?dir=<dir>` 代理通道(后缀白名单已含 `.kicad_pcb`)。
- tracespace 的具体 render API 随 vendored 版本,落地时按其 ESM 导出对齐
  index.html 的 `mount2D()`。
- 两个库均 MIT/Apache,vendoring 时保留各自 LICENSE 头。
