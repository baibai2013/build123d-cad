# tscircuit engine 构建源(预构建 → vendoring)

viewer 的 `engine=tscircuit`:React 直引 `@tscircuit/runframe` 的 `CircuitJsonPreview`
(PCB/原理图/3D 三页)+ 自建 BOM/总价面板(读 `<board>.bom.json` sidecar)。
**离线预构建成单文件 `dist/index.html`(JS/CSS 全内联)再 vendoring**,守 viewer
「engines 不 npm install」红线(同 cad 引擎做法)。

## 重新构建(改了 src 后)

```bash
cd <临时构建目录>            # 不在 engines/ 内 install
cp -r viewer-src/* .
bun install                  # 装 react/runframe/vite 等(见 package.json + runframe 的外部依赖)
bunx --bun vite build        # 必须 --bun:Rosetta 机用 node 跑会原生库架构不匹配
cp dist/index.html <repo>/skills/viewer/scripts/engines/tscircuit/dist/index.html
```

> runframe dist 未自带依赖,需补装 @radix-ui/* + 一批 @tscircuit/* + circuit-json-to-bom-csv 等;
> 完整清单见构建日志「Rollup failed to resolve」逐个补,或参考 dev-plan §4.1 spike 记录。
> Vite 固定 5.x(8.x 的 rolldown / 5.x 的 rollup 原生绑定在 Rosetta 下都需 `--bun` 运行时)。

## 运行期约定

- 页面读 URL `?dir=&file=`,经父 server `/files/<file>?dir=` 取 `circuit.json`。
- BOM 面板读同目录 sidecar `<file 去 .circuit.json>.bom.json`(由 `pcb/scripts/bom_price.py` 生成)。
- 单文件:无独立 asset 请求,不经 cad backend 反代。
