# tscircuit 端到端造板:完整工作流手册

> 面向使用者的逐步手册(命令以 M0 实测为准,见 `pcb-tscircuit-dev-plan.md` §4.1)。
> 子技能入口:`skills/pcb/SKILL.md`。本文是「怎么一步步把一块板从代码做到嘉立创下单」。

---

## 0. 一次性环境

```bash
curl -fsSL https://bun.sh/install | bash      # bun 运行时(tscircuit 依赖)
bun add -g tscircuit                            # 装 tsci(Rosetta 机务必用 bun 装)
tsci version                                    # 自检
claude mcp add jlcpcb -- npx -y jlcpcb-mcp@0.3.3   # 嘉立创集成(免 key 即可查料/报价)
```

> 板级报价/下单才需要 creds(`JLCPCB_APP_ID/ACCESS_KEY/SECRET_KEY` + `JLCPCB_ENABLE_ORDERS=true`)。
> 本技能默认不接 key:物料报价免 key,板级报价/下单代码就绪但默认 disabled。

---

## 1. 需求澄清

写代码前先定:板型与尺寸、是否异形;电源轨与电压、地;IO(连接器/排针/安装孔);
制造商 = JLCPCB(决定封装与出件)。是否要 SMT 贴片(影响是否出 CPL + 贴片元件确认)。

---

## 2. 起项目 + 选料

```bash
bash skills/pcb/scripts/new_board.sh my-board   # tsci init,生成 index.circuit.tsx
cd my-board
tsci search "ESP32-C3"                            # 搜元件
tsci import C2040                                 # 用嘉立创料号导封装
```

---

## 3. 写电路(`index.circuit.tsx`)

要点:参数顶置;每个元件 `name`+`footprint`+布局 props;`<trace>` 选择器**带 `>`**;
电源/地走命名 net;5+ 元件用 `<group>`+`schematicsection` 分块。

```tsx
const W = "20mm", H = "15mm", R_LIMIT = "330"
export default () => (
  <board width={W} height={H}>
    <led name="LED1" footprint="0603" pcbX={-3} schX={-2} />
    <resistor name="R1" resistance={R_LIMIT} footprint="0402" pcbX={3} schX={2} />
    <trace from="net.VCC" to=".R1 > .pin1" />
    <trace from=".R1 > .pin2" to=".LED1 > .anode" />
    <trace from=".LED1 > .cathode" to="net.GND" />
  </board>
)
```

---

## 4. 校验(check + DRC)

```bash
bash skills/pcb/scripts/check_all.sh index.circuit.tsx
```
- `tsci check netlist/placement/routing`:快速预检(官方 under-dev,失败不致命)。
- `tsci build`:**默认跑 DRC**(netlist/pin-spec/placement/routing 四类),出错 exit 1,
  产 `dist/index/circuit.json`。开发期可 `--ignore-*-drc`,**出件前不带豁免复跑**。

> DRC ≠ DFM:DRC 管「设计自洽」(tscircuit 原生);DFM 管「厂做不做得出」(下一步)。

---

## 5. 预览(出件前必做)

三条路径(详见 `skills/pcb/references/preview-3d.md`):

```bash
tsci dev                 # ① 原生:浏览器 :3020 看 PCB/原理图/3D(交互)
tsci snapshot --3d       #   或出 PNG+SVG 快照
# ② 统一进仓库 viewer(推荐,可分享/快照):
tsci export index.circuit.tsx -f glb -o out/board.glb
bash skills/viewer/scripts/start.sh out/board.glb     # → ?engine=cad
```

实测 3D 快照能正确渲染元件 + 走线 + 板框。M2 会把 RunFrame 直接嵌进 viewer 做统一预览 + BOM/总价面板。

---

## 6. DFM(本地,免 key/免上传)

```bash
python3 skills/pcb/scripts/dfm_check.py dist/index/circuit.json
```
读 circuit.json 几何(线宽/孔径/环宽/铜到边)比对嘉立创标准工艺阈值;输出 PASS/FAIL。
这是出件前第一道闸,**不替代**嘉立创官方审核(`jlcpcb_pcb_get_audit_info`,需 key,权威)。

---

## 7. 一键出件

```bash
bash skills/pcb/scripts/export_fab.sh index.circuit.tsx my-board
```
产出(`output/my-board/electrical/`):
- `fab/my-board-gerbers.zip`(Gerber,zip)
- `fab/my-board-bom.csv` / `-cpl.csv`(从 circuit.json `source_component`/`pcb_component` 派生;
  料号已由 build 自动匹配,如 C25104)
- `3d/my-board.{step,glb}`(step→mechanical,glb→viewer)
- `preview/my-board.{pcb,schematic}.svg`

> 无独立 `bom`/`cpl` 导出格式,均从 circuit.json 派生。

---

## 8. 嘉立创报价 + 下单(经 jlcpcb-mcp)

```bash
# 免 key 物料报价(任意机器):
python3 skills/pcb/scripts/jlc_order.py --component C25104 --qty 100
# 板级报价(需 creds;无则降级开网页):
python3 skills/pcb/scripts/jlc_order.py output/my-board/electrical/fab/my-board-gerbers.zip --layers 2 --qty 5
# 下单(双重 gate:creds + JLCPCB_ENABLE_ORDERS=true + --confirm):
python3 skills/pcb/scripts/jlc_order.py <gerbers.zip> --order --confirm
```

降级纪律:`jlcpcb-mcp` → 直连 API → 开 `https://jlcpcb.com/quote` 网页,**绝不假装成功**;
`quote.json` 标 `quote_source: mcp|api|manual`。详见 `skills/pcb/references/jlcpcb-mcp.md`。

---

## 9. 跨子技能 handoff

- → **viewer**:`3d/*.glb`(?engine=cad)、`preview/*.svg`(?engine=pcb/sch)。
- → **mechanical**:`3d/*.step` + 板框 dxf → 外壳让位/装配间隙。
- ← **electronics-bom**(可选上游):读 `library.json` 喂 `tsci import`。
- → **KiCad 兜底**:`tsci export -f kicad_zip` 交用户在 KiCad 做 GUI 高级布线。

---

## 10. 出件前自验清单

- [ ] `tsci build` exit 0、DRC 干净(不带豁免)
- [ ] `dfm_check.py` PASS
- [ ] 看过 PCB+原理图(已给用户审)
- [ ] gerbers.zip / bom.csv / cpl.csv 齐
- [ ] 下单前有报价 + 用户 `--confirm`(且开关已开)
