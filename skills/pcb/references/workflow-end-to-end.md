# tscircuit 端到端造板:完整闭环 + 自验清单

> 6 步主流程的可操作展开,每步给命令 + 通过判据。命令均以 M0 实测为准。
> 详尽叙述见仓库 `docs/pcb-tscircuit-workflow.md`。

## 工作区约定

```
output/<task>/electrical/
├── index.circuit.tsx / package.json   # tscircuit 项目(入口名固定 index.circuit.tsx)
├── dist/index/circuit.json            # tsci build 产物(单一事实源)
├── fab/   <board>-gerbers.zip  <board>-bom.csv  <board>-cpl.csv
├── 3d/    <board>.step  <board>.glb
├── preview/ <board>.pcb.svg  <board>.schematic.svg
└── <board>.quote.json                 # 嘉立创报价/下单回执
```

## 步骤

### [1] 需求澄清(写代码前先问清)
板型+尺寸(`<board width height>`)、异形(`<cutout>`)、电源轨与电压、地、
IO(连接器/排针/安装孔 `<hole>`/`<platedhole>`)、制造商=JLCPCB。

### [2] 起项目 + 选料
```bash
bash scripts/new_board.sh <board>     # tsci init,生成 index.circuit.tsx
tsci search "ESP32-C3"                  # 搜
tsci import C2040                        # 用嘉立创料号导封装
```
判据:`index.circuit.tsx` 生成,需要的封装可用。

### [3] 写 TSX
- 顶部定义参数(尺寸/阻值/电压)。
- `<board>` 内放元件:`name` + `footprint` + 布局 props(`pcbX/pcbY`、`schX/schY`)。
- `<trace from=".R1 > .pin1" to="net.VCC" />` 连接(**选择器带 `>`**),电源/地走 `net.VCC`/`net.GND`。
- 5+ 元件用 `<group>` + `schematicsection` 分块。

### [4] check + DRC
```bash
bash scripts/check_all.sh index.circuit.tsx
# = tsci check netlist/placement/routing(预检,under-dev)→ tsci build(默认跑 DRC,权威)
```
判据:`tsci build` **exit 0** 且 DRC 干净(出件前不带 `--ignore-*-drc` 复跑)。

### [5] web 预览(出件前必做)
```bash
tsci dev                                 # :3020 交互看 PCB+原理图+3D
tsci snapshot --3d                        # 或出 PNG+SVG 快照(无需起 server)
# 统一进仓库 viewer:
bash scripts/export_fab.sh index.circuit.tsx <task>
bash ../viewer/scripts/start.sh output/<task>/electrical/3d/<board>.glb   # ?engine=cad
```
判据:PCB 布局 + 原理图肉眼合理,给用户审。三路径见 `preview-3d.md`。

### [6] DFM → 出件 → 报价 → 下单
```bash
# 6a 本地 DFM(免 key/免上传,读 circuit.json):
python scripts/dfm_check.py output/<task>/electrical/dist/index/circuit.json
# 6b 一键出件:
bash scripts/export_fab.sh index.circuit.tsx <task>     # gerbers/step/glb/svg + 派生 BOM/CPL
# 6c 报价(免 key 物料 + 需 key 板级,经 jlcpcb-mcp):
python scripts/jlc_order.py output/<task>/electrical/fab/<board>-gerbers.zip --layers 2 --qty 5
# 6d 下单(gate,需 key + 开关 + 确认):
python scripts/jlc_order.py <...> --order --confirm
```
判据:DFM 过;`quote.json` 有价(`quote_source: mcp`)或正确降级(`manual` + 开网页);
下单仅在 `--confirm`(且 `JLCPCB_ENABLE_ORDERS=true`)时发生。

## 出件前自验清单

- [ ] `tsci build` exit 0,DRC 干净(不带豁免)
- [ ] 本地 `dfm_check.py` 通过(线宽/间距/孔/铜到边)
- [ ] 第 5 步至少看过一次 PCB+原理图(已给用户审)
- [ ] gerbers.zip 出齐;BOM/CPL 从 circuit.json 派生(料号已自动匹配)
- [ ] 下单前已拿到报价且用户 `--confirm`

## 常见坑

- trace 选择器漏 `>`(写成 `.R1 .pin1`)→ 连接不成立。
- 元素/属性大小写敏感,编造 props 会静默失效 → 查 `syntax-elements.md`。
- 以为有 `bom`/`cpl` 导出格式 → 没有,从 circuit.json `source_component` 派生。
- 无 JLC key 还硬报板级价 → 必须 fail-loud 降级,不假装成功(物料价免 key)。
