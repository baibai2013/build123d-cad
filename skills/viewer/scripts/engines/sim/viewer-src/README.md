# engine=sim 源码说明

`../dist/index.html` 是 **手写的零依赖单文件**(原生 HTML + Canvas + vanilla JS),
**没有 build 步骤**——直接编辑 `dist/index.html` 即可,不像 tscircuit 引擎需要 vite 打包。

之所以零依赖(不引 plotly / three.js / React):
- 仿真回放只需 **帧 scrubber(`<img>` 切图)+ 简单 line chart(手绘 Canvas)+ checks 徽章**,
  原生足够,曲线是单序列/少量多线,不值得拖一个图表库进来。
- 完全离线 / headless 友好:无 CDN、无 vendored 大库,headless chromium 能真渲(纯 DOM+Canvas,不依赖 GPU/WebGL),
  便于 `verify_urdf.py` 那套 playwright 截图自验。

## 它渲染什么

读 `?dir=&file=`,经父 server 的 `/files/<rel>?dir=` 代理取文件(与 tscircuit 引擎同一 fetch 模式):

- `*.results.json`(主) → 仪表盘:顶栏 meta + 四 checks 徽章;左=帧回放(scrubber + play);
  右=Canvas 曲线(base z / roll·pitch / 关节角 / 接触力)带时间游标;底=summary。
- `*.mp4` / `*.webm` → `<video>`。
- `*.csv` → 简单表格。

帧路径来自 `results.json` 的 `frames[].path`(相对 outdir 的 `frames/frame_NNNN.png`),
按当前 scrub 时间就近取帧。`checks` 为空(run_sim 单跑未自验)时显「未自验」灰徽章,不报错。

产物格式契约见 `skills/simulation/references/output-contract.md`。
