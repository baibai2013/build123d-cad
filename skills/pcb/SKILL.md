---
name: pcb
description: |
  build123d-cad 的板级电气设计子技能。用 tscircuit(React/TypeScript 写电路)
  端到端造板:写 TSX → check → web 预览(PCB+原理图+3D)→ 出件(Gerber/BOM/CPL)
  → 嘉立创(JLCPCB)报价 + 一键 API 下单。
  触发词:PCB、原理图、tscircuit、代码写PCB、TSX、React写板子、Gerber、出件、
  嘉立创、JLCPCB、下单打板、PCB 3D、EDA、电路板、BOM 报价。
  本子技能不做:机械外壳建模(→ mechanical)、元件选型/curated 料库(→ electronics-bom)、
  通用网页预览基建(→ viewer)。
owner: hardware
status: active
tech: tscircuit
since: 2026-06-05
supersedes: KiCad-cli + skidl(已归档到 legacy-kicad/,见 README)
---

# pcb · tscircuit 端到端造板

板级电气设计入口。**一把 `tsci` CLI 打通 authoring → check → export → 下单**,
代码即电路,真正闭环(旧 KiCad/skidl 路线断在 GUI layout,见 `legacy-kicad/`)。

> 一句话:mechanical 管"外壳画对",pcb 管"板子写对 + 造得出 + 发得了嘉立创"。
>
> 详尽流程文档在仓库 **`docs/pcb-tscircuit-workflow.md`**(选型/逐步详解/示例),本 SKILL 只给执行骨架。

---

## AI 执行准入序列

1. 收到 PCB / 电路板 / tscircuit / 打板 类需求 → 先读本 SKILL.md「6 步主流程」。
2. 写代码前,语法/CLI 拿不准 → 读 `references/syntax-elements.md` / `cli-cheatsheet.md`,
   **不要凭印象编 JSX props 或 CLI flag**(tscircuit 元素/属性大小写敏感)。
3. references/ 是查询表,不当 Playbook 全量读。
4. 跨子技能走 `../../shared/handoff-protocols.md` 文件接口,不互调函数、不互引 references。
5. 触及真实下单/生产数据的步骤标 `gate: true`,等用户显式 `--confirm`。

---

## 6 步主流程

```
[1] 需求澄清      板型尺寸 / 电源轨(电压) / IO 接口(连接器·排针·安装孔) / 制造商=JLCPCB
        ▼
[2] 起项目+选料   new_board.sh <name>(tsci init;入口文件 index.circuit.tsx)
                  tsci search "<关键词>" → tsci import <jlcpcb部件号|author/pkg>(从嘉立创导封装)
        ▼
[3] 写 TSX        index.circuit.tsx 默认导出函数返回 JSX:<board> 内放元件 + 布局 props + <trace> 连接
                  5+ 元件用 <group> / schematicsection 分组(原理图可读性最关键的一步)
        ▼
[4] check + DRC   check_all.sh: tsci check netlist/placement/routing(预检,官方 under-dev)
                  → tsci build(默认跑 DRC,权威);exit 0 且 DRC 干净才算稳
                  开发期可 --ignore-*-drc,出件前必须不带豁免复跑
        ▼
[5] web 预览      tsci dev(:3020,PCB+原理图+3D)/ tsci snapshot --3d(出 PNG+SVG 快照)
                  或 export glb → viewer ?engine=cad(统一预览,见 preview-3d.md)
        ▼
[6] DFM→出件→报价 dfm_check.py(读 circuit.json 本地 DFM,gate)→ export_fab.sh(一键:
                  gerbers/step/glb/svg + 从 circuit.json 派生 BOM/CPL)
                  → jlc_order.py 经 jlcpcb-mcp 报价(免 key 物料 + 需 key 板级)
                  → [gate] --order --confirm 一键下单嘉立创
```

每步脚本见下「脚本索引」,参数读脚本顶部 docstring,不要凭名字猜。

---

## builtin 元素速查(常用,全表见 references/syntax-elements.md)

| 类别 | 元素 |
|---|---|
| 容器 | `<board>` `<subcircuit>` `<group>` `<footprint>` `<schematicsection>` |
| 无源 | `<resistor>` `<capacitor>` `<inductor>` `<diode>` `<led>` `<crystal>` `<fuse>` |
| 有源/IC | `<chip>` `<mosfet>` `<transistor>` `<opamp>` |
| 连接 | `<connector>`(`standard="usb_c"`)`<pinheader>` `<jumper>` `<net>` `<netlabel>` `<trace>` |
| PCB 图元 | `<via>` `<platedhole>` `<hole>` `<smtpad>` `<silkscreentext>` `<copperpour>` `<cutout>` |

布局 props:PCB 用 `pcbX / pcbY / pcbRotation / layer`;原理图用 `schX / schY / schRotation`。
连接用 `<trace from=".R1 > .pin1" to="net.VCC" />`(**选择器带 `>`**),电源/地走命名 net:`net.VCC` `net.GND`。

```tsx
// 文件名固定 index.circuit.tsx(tsci init 生成)
export default () => (
  <board width="20mm" height="15mm">
    <led name="LED1" footprint="0603" pcbX={-3} schX={-2} />
    <resistor name="R1" resistance="330" footprint="0402" pcbX={3} schX={2} />
    <trace from="net.VCC" to=".R1 > .pin1" />
    <trace from=".R1 > .pin2" to=".LED1 > .anode" />
    <trace from=".LED1 > .cathode" to="net.GND" />
  </board>
)
```

---

## CLI + export 速查(全表见 references/cli-cheatsheet.md)

| 命令 | 用途 |
|---|---|
| `tsci init [dir] -y` / `tsci dev` | 起项目(入口 index.circuit.tsx)/ 浏览器预览(:3020) |
| `tsci search` / `tsci add` / `tsci import` | 搜元件 / 装 registry 包 / 从 JLCPCB·registry 导入 |
| `tsci check`(子命令 `netlist`/`placement`/`routing`) | 分阶段预检(官方标 under-dev,当辅助) |
| `tsci build [file] [--pcb-png f]` | 编译 → `dist/<entry>/circuit.json`,**默认跑 DRC** |
| `tsci snapshot --3d` | 出 PCB/原理图 SVG + 3D PNG 快照 |
| `tsci export -f <fmt> -o <out>` | 导出(见下) |

`export -f` 格式(实测):`gerbers`(出件 **zip**)、`step`/`glb`/`gltf`(3D,给 mechanical/viewer)、
`pcb-svg`/`schematic-svg`/`assembly-svg`(2D)、`specctra-dsn`/`srj`(布线)、`kicad_pcb`/`kicad_zip`(KiCad 兜底)、
`readable-netlist`/`circuit-json`。**无独立 bom/cpl 格式** → 从 circuit.json 的 `source_component`
派生(build 已自动配嘉立创料号,如 C25104)。

> **工具前置**:`tsci` 来自 **`tscircuit`** 包(bin=tsci)且**依赖 bun 运行时**;缺失时脚本 fail-loud
> 给提示(`bun add -g tscircuit`;Rosetta 机须用 bun 装否则原生库架构不匹配),不静默。
> 这是本技能的运行依赖,非 viewer vendoring 红线范畴。

---

## 嘉立创(JLCPCB):报价 + 下单(经 jlcpcb-mcp)

首选 MCP server **`jlcpcb-mcp`**(免大量手写 REST),直连 `api.jlcpcb.com` 作兜底:

- **免 key**:查元件/报价/库存/datasheet(`jlcpcb_search_components` `jlcpcb_get_component_pricing`
  `jlcpcb_get_component_details` …)→ 喂 BOM + 总价(物料部分)。**实测 C25104 返回阶梯价。**
- **需 key**(`JLCPCB_APP_ID` / `JLCPCB_ACCESS_KEY` / `JLCPCB_SECRET_KEY`):板级报价
  `jlcpcb_pcb_upload_gerber`→`jlcpcb_pcb_calculate_price`;官方工程审核 `jlcpcb_pcb_get_audit_info`(DFM 权威)。
- **下单是 gate**:`jlcpcb_pcb_create_order` 默认禁用,需 `JLCPCB_ENABLE_ORDERS=true` + `--confirm` 才真发。
- 安装:`claude mcp add jlcpcb -- npx -y jlcpcb-mcp@0.3.3`。无 key / MCP 不可用 → 降级开
  `https://jlcpcb.com/quote` 上传页,**绝不假装报价/下单成功**。
- 工具名/字段对实时为准,**不编**;详见 `references/jlcpcb-mcp.md`。

---

## 脚本索引(scripts/)

| 脚本 | 职责 | 缺工具行为 |
|---|---|---|
| `new_board.sh <name>` | 包 `tsci init` 起项目(入口 index.circuit.tsx) | 无 tsci/bun → 安装提示退出 |
| `check_all.sh [entry]` | `tsci check netlist/placement/routing` + `tsci build`(DRC) | 同上 |
| `dfm_check.py <circuit.json>` | 本地 DFM:读几何(线宽/间距/孔/铜到边)比对嘉立创工艺,免 key/免导出 | 无 json → 提示先 build |
| `export_fab.sh <entry> [task]` | 一键 build + 出 gerbers/step/glb/svg + 派生 BOM/CPL + `<board>.circuit.json`/`.bom.json`(统一预览) → `output/<task>/electrical/` | 同上 |
| `bom_price.py <circuit.json>` | 派生 BOM + jlcpcb-mcp **免key**定价 → `<board>.bom.json`(喂 viewer BOM/总价面板) | MCP 不可用→降级 unpriced |
| `jlc_order.py <gerbers.zip>` | 经 jlcpcb-mcp 报价;`--order --confirm` 下单 | 无 key → fail-loud + 降级开网页 |

---

## handoff(文件接口,不互引)

| 链路 | 产物 → 用途 |
|---|---|
| pcb → **viewer**(统一预览) | `electrical/<board>.circuit.json` → `?engine=tscircuit`(PCB+原理图+3D+BOM/总价,读 `<board>.bom.json` sidecar);单产物 `glb`→`?engine=cad`、`svg`→`?engine=pcb/sch` |
| pcb → **mechanical** | `electrical/3d/<board>.step` + 板框 `.dxf` → build123d 读做外壳让位/装配间隙 |
| pcb ← **electronics-bom**(可选上游) | 读它落盘的 `library.json`(选好的料)喂 `tsci import`;**不** subprocess 反调 |
| pcb → **KiCad 兜底** | 需 GUI 高级手工布线 → `tsci export -f kicad_zip` 交用户在 KiCad 打开(非子技能) |

输出物全落 `output/<task>/electrical/`(沿用 08 §2 约定):
`<board>.circuit.json` / `fab/<board>-gerbers.zip` / `fab/<board>-bom.csv` / `fab/<board>-cpl.csv`
/ `3d/<board>.{step,glb}` / `preview/<board>.{pcb,schematic}.svg` / `<board>.quote.json`。

---

## 角色规则(子技能本地)

1. **代码即电路**:直接给可执行 TSX,参数(尺寸/电压)定义在顶部。
2. **不编 API/props**:JSX 元素属性、CLI flag、JLCPCB 端点一律先查 references/实时文档。
3. **check 才算数**:`tsci build` 的 DRC 干净 + 本地 DFM 过,再谈出件;不靠肉眼。
4. **出件前必预览**:第 5 步至少出一次 PCB+原理图视图(tsci dev 或 svg),给用户审。
5. **下单是 gate**:真实下单/付款必须 `--confirm`;无 key 时降级开网页,不假装成功。
6. **解耦**:选料找 electronics-bom,外壳找 mechanical,预览基建找 viewer,本技能只管电气。

---

## 不做什么

- ❌ 不编 JLCPCB API 端点/字段(对实时文档校准,无 key fail-loud)
- ❌ 不自动真实下单/付款(永远等 `--confirm`)
- ❌ 不做机械外壳建模(→ mechanical)、元件选型 curated 库(→ electronics-bom)
- ❌ 不做高速 SI/PI 仿真(超范围)
- ❌ 不重造 3D 预览基建(复用 viewer engine=cad)

---

## references/

- `cli-cheatsheet.md` — `tsci` 全命令 + `export -f` 格式表
- `syntax-elements.md` — 常用 JSX 元素 + props + net/trace + schematicsection
- `workflow-end-to-end.md` — 需求→出件 完整闭环 + 自验清单
- `jlcpcb-mcp.md` — 嘉立创 jlcpcb-mcp 对接(28 工具/免key报价/板级/审核/下单 gate)
- `preview-3d.md` — PCB 3D 预览三路径(tsci dev / glb→viewer cad / gerber→viewer pcb)

不在 references/ 里的语法/端点不要凭印象写,先查官方文档(docs.tscircuit.com / api.jlcpcb.com)再补表。
