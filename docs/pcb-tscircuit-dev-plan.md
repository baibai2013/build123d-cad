# PCB 子技能开发方案(tscircuit 端到端造板)

> 状态:**需求/方案讨论中,尚未开发**。本文先定**技术选型**与**开发安排**,
> 评审通过后再落代码。落地后本文转为「设计依据」存档。
>
> 关联:子技能 `skills/pcb/`、复用 `skills/viewer/`、可选上游 `skills/electronics-bom/`。

---

## 1. 背景与目标

把 build123d-cad 的 `pcb` 子技能从旧 **KiCad-cli + skidl** 占位(已归档 `skills/pcb/legacy-kicad/`)
重写为 **tscircuit** 端到端造板。核心目标:

**写 TSX 电路代码 → 统一 web 预览(PCB+原理图+3D+BOM+总价)→ 嘉立创(JLCPCB)报价 → 一键 API 下单。**

为什么弃 KiCad/skidl:`legacy-kicad/references/skidl-quickstart.md` 已暴露硬伤——
skidl 只能出网表 `.net`,**没有 CLI 把它变带布局的板**,layout 必须回 KiCad GUI 手工,
**不是代码端到端**。tscircuit 用一把 `tsci` 从 TSX 直接出带布局的板 + Gerber,真正闭环,
且底座是 React/TS(LLM 训练集最大),最适合「AI 写整块板」。

---

## 2. 技术选型

### 2.1 选型对照(核心库)

| 维度 | **tscircuit(选)** | KiCad+skidl(旧) | atopile |
|---|---|---|---|
| 语法底座 | React/TS(LLM 语料最大) | Python DSL(skidl 小众) | 自研 `.ato`(语料最小) |
| 代码端到端 | ✅ TSX→带布局板→Gerber | ❌ 断在 GUI layout | ✅(约束求解) |
| AI 友好 | ✅ 官方 AI 套件 + llms.txt | 一般 | 弱 |
| 出件 | `tsci export -f gerbers/step/glb/svg/kicad_*` | kicad-cli | KiCad 原生 |
| 可嵌入预览 | ✅ `@tscircuit/runframe` | KiCanvas/tracespace | KiCad GUI |
| 前景/势头 | ✅ 迭代极猛、registry 生态 | 成熟但 GUI 依赖 | YC 系、专业向 |

### 2.2 各环节技术栈(均已核实,不编)

| 环节 | 选型 | 关键事实 |
|---|---|---|
| 电路 authoring | **tscircuit** `tsci` CLI | `init/search/import/check/build/dev/export` |
| 校验 | `tsci check netlist→schematic-placement→placement` | 出件前必过 |
| 出件 | `tsci export -f gerbers/step/glb/gltf/pcb-svg/schematic-svg/kicad_zip` | 已核实格式表 |
| BOM/CPL | export / `tsci dev` fabrication 面板 | 子命令实现期对实时文档校准 |
| **统一预览** | **`@tscircuit/runframe` 嵌入仓库 viewer** | React 组件 或 `runframe.tscircuit.com/iframe.html` + postMessage |
| **BOM+总价面板** | **自建**(runframe 不带) | circuit.json 元件 + `jlcpcb-mcp` 报价(见 §2.3) |
| **JLCPCB 集成层** | **`jlcpcb-mcp` MCP server**(首选)+ 直连 API 兜底 | 查元件/报价/库存**免 key**;板级报价+下单需 key,见 §2.3 |

### 2.3 JLCPCB 集成层:`jlcpcb-mcp` MCP server(关键选型)

不裸手接 JLCPCB REST API,而是用现成 MCP server **`jlcpcb-mcp`**(Eyalm321,
npm `jlcpcb-mcp` v0.3.3,GitHub `Eyalm321/jlcpcb-mcp`)作首选集成层,直连 API 作兜底。

**它暴露的工具(已核实)**:

| 用途 | MCP 工具 | 要 key |
|---|---|---|
| 查元件 / 报价 / 库存 / datasheet | `jlcpcb_search_components` `jlcpcb_get_component_pricing` `jlcpcb_get_component_details` `jlcpcb_get_component_stock` `jlcpcb_get_datasheet_url` | ❌ 免 key |
| 官方权威元件库(LCSC code) | `jlcpcb_official_get_component_detail` `jlcpcb_official_component_library` | ✅ |
| 板级报价 | `jlcpcb_pcb_upload_gerber` → `jlcpcb_pcb_calculate_price`(只报价) | ✅ |
| 一键下单 | `jlcpcb_pcb_create_order` ⚠️(真付费,默认禁用) | ✅ + `JLCPCB_ENABLE_ORDERS=true` |
| 订单状态/进度 | `jlcpcb_pcb_get_order_detail` `jlcpcb_pcb_get_wip_process` `jlcpcb_pcb_get_audit_info` | ✅ |

- **数据源**:本地 SQLite(`yaqwsx/jlcparts` 快照,成熟社区库)+ LCSC 实时(`wmsc.lcsc.com`)
  + 官方 `open.jlcpcb.com`(配 creds 时)。
- **安装**:`claude mcp add jlcpcb -- npx -y jlcpcb-mcp`(stdio;首次构建本地 DB 数分钟)。
- **凭据(仅板级报价/下单需要)**:`JLCPCB_APP_ID` / `JLCPCB_ACCESS_KEY` / `JLCPCB_SECRET_KEY`;
  下单还需 `JLCPCB_ENABLE_ORDERS=true`——**与本技能「下单是 gate」哲学天然一致**。

**收益**:
- **元件查询 + BOM 报价 + 总价 = 免 key 即可做**(M3 不卡 key)。
- 板级报价 + 真实下单走 MCP 工具,不再手写 REST 客户端(M4 大幅简化)。

**风险与兜底**:`jlcpcb-mcp` 很新(单作者、刚发布、1 star),可能不稳/接口变动。
故定为**首选集成层**,脚本侧保留**直连 `api.jlcpcb.com` 的兜底路径**;MCP 不可用时降级,
仍遵守无 key→fail-loud→开网页 的纪律。

> 备选 MCP(均更弱,不选):`@jlcpcb/mcp`(l3wi,偏 sourcing+KiCad 转换)、
> `jlcpcb-mcp-parts-finder`(仅搜索)、`lcsc-mcp-server-node`。

### 2.4 统一预览方案(回应「viewer 统一/嵌入 tscircuit」)

**单一入口 = 仓库 `viewer`,内嵌 tscircuit RunFrame,再加自建 BOM/价格面板。**

```
仓库 viewer(唯一预览入口)
└── 新引擎 engine=tscircuit(或扩 engine=pcb)
    ├── RunFrame(iframe / React)  → PCB · 原理图 · 3D 三页(tscircuit 原生)
    └── 自建 BOM 面板             → 元器件清单(来自 circuit.json)
                                   + 每行单价/库存(jlcpcb-mcp,免 key)
                                   + 合计总价 + 「下载 BOM CSV」按钮
```

- runframe 只给 PCB/原理图/3D;**BOM 表与总价它没有**,故 BOM 面板自建,与 runframe 并排成页签。
- 总价 = 物料合计(`jlcpcb-mcp` 免 key 报价)+ 板费(板级报价,需 key),在面板顶部显示;
  无 key 时只显示物料合计 + 板费「待报价」。
- 嵌入方式 = **React 直引 `<RunFrame />`**(已定,便于自定义 BOM 面板与总价)。
  遵守 viewer「不 `npm install` 进 engines」红线的方式:**离线把 runframe + BOM 面板
  预构建成 bundle,再 vendoring 进 `engines/tscircuit/`**(与现有 engine=cad 的 13MB
  Vite SPA 同款做法)——既能 React 直引自定义,又不在 engines 跑 install。

### 2.5 已定决策(2026-06-05)

| # | 决策 | 含义 |
|---|---|---|
| 1 | **API key:有,但现在不接** | M0–M3(免 key 段)全做;M4 把报价/下单**代码路径写完但默认 disabled**(`JLCPCB_ENABLE_ORDERS` 不开、不填 creds),真实连接等你说接再开。CI/日常跑都走免 key + 降级。 |
| 2 | **SMT 贴片:必做** | M5 从「可选」升为**必做**。BOM 面板要带贴片元件状态(Basic/Extended、库存、是否可贴);出件含 **BOM + CPL**;下单走嘉立创 SMT 装配流程。 |
| 3 | **预览嵌入:React 直引** | `<RunFrame />` 直引,便于自定义 BOM/总价面板;离线预构建 bundle 进 `engines/tscircuit/` 守住 viewer 红线(见 §2.4)。 |

仍开放:SMT 元件「确认/替换」交互的深度(一期可先只读展示 + 标风险,不做在线替换)。

---

## 3. 架构与解耦

`pcb` **单一内聚**(tscircuit 一把 CLI 打通 authoring→export→order,不拆多子技能,避免互引红线)。
对外只走**文件接口 handoff**:

| 关系 | 对象 | 接口 |
|---|---|---|
| 软 handoff(预览) | `viewer` | glb/svg/circuit.json → engine=tscircuit |
| 可选上游(选料) | `electronics-bom` | 读它落盘 `library.json` 喂 `tsci import` |
| 下游(外壳) | `mechanical` | step/板框 dxf → 外壳让位 |
| 兜底(GUI 布线) | KiCad(非子技能) | `tsci export -f kicad_zip` |

**硬依赖 = 无**:pcb 用 tscircuit + JLCPCB API 即可独立跑全链路。
**报价职责线**:物料级单价=Components API;板级报价+下单=PCB API(gate)。

---

## 3.5 工作流总览(端到端主流 + 分流点)

### 主流(从需求到拿到板)

```
 需求(板型/电源/IO/SMT)
        │
        ▼
 [tscircuit 写板]  index.tsx  ──tsci──▶  circuit.json   ← 代码即电路
        │                                   │
        ▼                                   │(同一份 circuit.json 供给下游,单一事实源)
 [check 预检] tsci check netlist / placement / routing(快速,官方标 under-dev)
        │
        ▼
 [布线 routing]  自动(local / auto-cloud)│ 自定义 algorithmFn(SimpleRouteJson)
        │         │ 或 export specctra-dsn → Freerouting 外部布线 → 回灌
        ▼
 [build + DRC]  tsci build(默认跑 DRC:netlist/pin-spec/placement/routing 四类)
        │        → circuit.json(含走线 + DRC 错误对象);出错 exit 1
        │
        ▼
 [统一预览 = 仓库 viewer · engine=tscircuit]  ◀── React 直引 RunFrame
        ├── PCB / 原理图 / 3D   (RunFrame 原生)
        ├── BOM 面板(自建)     元器件清单 + 单价/库存 + 合计总价 + 下载CSV
        │                         └─ 数据来自 jlcpcb-mcp(免 key)
        └── [预览验证] viewer 快照 → cad-vision-verify 视觉核对(对不对/缺件/丝印)
        │
        ▼
 [DFM 检测 · GATE]  tscircuit DRC + 嘉立创 DFM 规则 + jlcpcb-mcp 工程审核(audit_info)
        │            └─ 不过 → 回 [写板] 修;过 → 才允许出件/下单
        ▼
 [一键导出 export_fab]  一条命令出齐:gerbers.zip + BOM.csv + CPL.csv + step + glb + svg
        │
        ▼
 [嘉立创 报价/下单]  经 jlcpcb-mcp
        ├─ 板级报价  upload_gerber → calculate_price
        ├─ SMT 装配  BOM + CPL → 装配报价
        └─ [GATE] create_order ⚠️  ← 默认 disabled(决策①),--confirm + 开关才真发
        │
        ▼
 订单 / 网页降级
```

### 分流点(4 处「岔路」)

1. **免 key 流 ┃ 需 key 流**
   - 免 key:写板 / check / 预览 / **元件查询·BOM·总价(物料)** —— 全程不要凭据,日常&CI 都走这条。
   - 需 key:**板级报价 + 真实下单 + SMT 装配下单** —— 代码就绪但默认 disabled(决策①)。
2. **裸板 ┃ SMT 贴片**(决策②两条都做)
   - 裸板:只 gerbers → 板级报价/下单。
   - SMT:额外 BOM + CPL + 贴片元件状态(Basic/Extended·库存·可贴性)→ 装配报价/下单。
3. **集成层三级降级**:`jlcpcb-mcp`(首选)→ 直连 `api.jlcpcb.com`(兜底)→ 打开网页上传(最后),
   每级都不假装成功,失败如实报。
4. **跨子技能分流(解耦)**:同一份 `circuit.json`/产物按用途分到不同子技能——
   预览→`viewer`、外壳让位→`mechanical`、选料→`electronics-bom`、GUI 高级布线→KiCad 兜底。
   pcb 只管电气,产物走文件接口,不互引(见 §3)。

### 流 ↔ 开发阶段映射

`写板+check`=M1 · `统一预览`=M2 · `BOM/总价面板`=M3 · `板级报价/下单`=M4 · `SMT 装配`=M5 · `布线`=M6。

## 3.6 进阶能力(DFM / 一键导出 / 预览验证 / 布线 / 嘉立创 3D)

| 能力 | 机制(均已核实落点,不编) | 落到 |
|---|---|---|
| **布线算法** | tscircuit 自动布线(local / `autorouter="auto-cloud"` 需登录)│ 自定义 `algorithmFn`(吃 `SimpleRouteJson` 返回 `GenericLocalAutorouter`)│ `tsci export -f specctra-dsn` → 外部 Freerouting → 回灌 | **M6** |
| **DRC 验证(布局/走线)** | **tscircuit 原生**:`tsci build` 默认跑 DRC(netlist / pin-spec / **placement=布局重叠** / **routing=未布通·间距**),出错 exit 1;`tsci check` 快速预检;`<drccheck>` 写自定义规则 | **M1 起** |
| **DFM 检测(gate)** | tscircuit **无**原生 DFM → ① 嘉立创 DFM 规则本地 checklist(最小线宽/孔径/环宽/铜到边/拼板)② `jlcpcb-mcp.jlcpcb_pcb_get_audit_info` 官方工程审核 | **M1 起**(出件前 gate) |
| **一键导出** | `export_fab.sh <entry>` 一条命令出齐 gerbers.zip + BOM.csv + CPL.csv + step + glb + pcb/sch-svg → `output/<task>/electrical/` | **M1** |
| **预览验证** | viewer 快照(`web_preview.py --snapshot`)→ `cad-vision-verify`(渲染图交视觉模型核对:元件齐不齐/极性/丝印/板框)→ 出报告 | **M2**(接现有技能) |
| **嘉立创 3D 预览器** | 本地 RunFrame 3D 快看;上传后 `jlcpcb-mcp.upload_gerber` 拿 fileKey → 嘉立创报价页**官方 3D/Gerber 预览**做权威核对(deep-link 给用户,不强嵌) | **M4**(随报价) |

**两道 GATE 串起质量闭环**:`DFM 检测`(出件前,必过)+ `下单确认`(--confirm,默认 disabled)。
DFM 不过 → 回写板修;预览/视觉验证不过 → 同样回修。**不过不出件、不过不下单。**

### 3.7 验证分层:DRC(tscircuit 原生)vs DFM(嘉立创)— 不要混

回应「tscircuit 的 DFM 和 PCB 布局走线验证」:tscircuit 自己做的是 **DRC**(设计规则,
电气/几何),**不做 DFM**(可制造性)。两层职责必须分清:

| 层 | 管什么 | 谁做 | 具体 |
|---|---|---|---|
| **DRC(布局/走线)** | 设计自洽:网表对、引脚对、**元件不重叠(placement)**、**线连通且不撞(routing)** | **tscircuit 原生** | `tsci build` 默认跑,四类 DRC + exit 1;`tsci check` 预检(under-dev,当辅助);`<drccheck>` 自定义规则 |
| **DFM(可制造性)** | 这家厂**做不做得出**:最小线宽/间距、最小孔径/环宽、铜到板边、阻焊/字符、拼板 | **嘉立创层**(tscircuit 没有) | 本地按嘉立创工艺参数做 DFM checklist + `jlcpcb-mcp` 工程审核 `audit_info` |

要点:
- **布局走线验证 = tscircuit DRC**(placement-drc + routing-drc),是出件前第一道闸。
- **DFM ≠ DRC**:DRC 过了不代表厂能做(线太细/孔太小厂做不出)→ 必须再过嘉立创 DFM。
- `tsci check` 官方标 under-development → **以 `tsci build` 的 DRC 为权威**,`check` 仅快速预检。
- DRC 警告开发期可暂忽略(`--ignore-*-drc`),但**出件前必须复跑且不带豁免**,确保干净。

**DFM 两档执行方式(CLI vs 必须导出)**:

| 档位 | 跑法 | 导出/上传 | key | 权威性 |
|---|---|---|---|---|
| 本地 DFM checklist | 纯 CLI,读 `circuit.json` 几何(线宽/间距/孔径/环宽/铜到边)比对嘉立创工艺参数 | ❌ 免导出(build 完读 json) | ❌ 免 key | 自维护规则,兜底 |
| 嘉立创官方审核 | `jlcpcb-mcp.upload_gerber → get_audit_info`(可 CLI 程序化驱动) | ✅ **必须导出 Gerber + 上传** | ✅ 需 key | 厂方权威 |

- **DFM 可以 CLI 化**:本地 checklist 离线/免 key,`tsci build` 后直接读 circuit.json 即可查。
- **官方权威 DFM 绕不开「导出 + 上传」**:MCP 只是程序化驱动它,本质仍需先出件上传。
- **闭环**:平时迭代跑本地 checklist(免网络/key);**下单前**导出上传走官方审核拿权威结论。

## 4. 开发安排(分阶段,每阶段独立可验收)

> 原则:先打通最小闭环(裸板),预览与下单逐层加;每阶段留 fail-loud,不堆半成品。

| 阶段 | 内容 | 产物 | 验收 |
|---|---|---|---|
| **M0 技术验证 spike** ✅ **已完成 2026-06-05** | 见下「M0 验证结论」 | `/tmp/pcb-spike/led-demo` | 全部达成 ✅ |
| **M1 子技能骨架 + 裸板闭环 + DFM/一键导出** | 重写 `pcb` SKILL/references;脚本 `new_board.sh`/`check_all.sh`/**`export_fab.sh`(一键导出)**/`dfm_check`(tscircuit DRC + 嘉立创 DFM checklist,出件前 gate);tests(结构+fail-loud);大文档 `docs/pcb-tscircuit-workflow.md` | `skills/pcb/` 完整 | `pytest` 全绿;一键出件三件齐;DFM 不过能拦下 |
| **M2 统一预览(React 直引 RunFrame)** ✅ **完成 2026-06-06** | viewer 加 `engine=tscircuit`:React 直引 RunFrame 单文件 bundle(`engines/tscircuit/dist/`),PCB/原理图/3D 三页;`.circuit.json` 自动路由;router/start/health 测试同步 | viewer engine | ✅ playwright headless:三页签 + 渲染 9/9 |
| **M3 BOM + 总价面板** ✅ **完成 2026-06-06** | `bom_price.py`(免 key jlcpcb-mcp)→ `<board>.bom.json` sidecar;BOM 面板读它显元器件清单 + 库存 + 单价 + **物料合计总价** + 下载 CSV | BOM 面板 + `bom.json`/`bom.csv` | ✅ 预览里 LED1/R1 料号+价、物料总价 $0.023、CSV 下载(**无 key**) |
| **M4 嘉立创报价+下单(代码就绪/默认 disabled)** | 经 `jlcpcb-mcp`:`upload_gerber`+`calculate_price` 板级报价 → gate `create_order`;**按决策①默认不开 `JLCPCB_ENABLE_ORDERS`、不填 creds**,代码路径写全但不真连;MCP 不可用→直连 API 兜底;无 key→降级网页 | 报价/下单封装 + `quote.json` | 免 key:正确降级且不假装;开关一开即可真连(留好接口) |
| **M5 SMT 贴片(必做)** | BOM 面板带贴片元件状态(Basic/Extended·库存·可贴性);出件含 **BOM + CPL**;下单走嘉立创 SMT 装配链路 | 贴片 BOM+CPL + 装配下单封装 | BOM 面板显示贴片状态;CPL 正确;装配报价跑通(默认 disabled) |
| **M6 布线算法** | 自动布线(local / auto-cloud)默认开;自定义 `algorithmFn`(SimpleRouteJson)接口;`export specctra-dsn` ↔ Freerouting 外部布线回灌 | 布线封装 + DSN 出入口 | minimal 板自动布通;DSN 能导出/回灌 |

依赖:M2 依赖 M1;M3 依赖 M2 + `jlcpcb-mcp`(免 key);M4/M5 报价/下单代码就绪但默认 disabled(决策①);M5 依赖 M3/M4;M6 可与 M2+ 并行(布线影响出件质量,建议 M3 前接上)。
前置:`claude mcp add jlcpcb -- npx -y jlcpcb-mcp@0.3.3`(M3 起需要,锁版本)。

---

## 4.1 M0 验证结论(2026-06-05,已跑通)

在 `/tmp/pcb-spike/led-demo`(LED+330Ω 限流电阻)实测,**整条链路打通**,并修正若干早先假设:

**工具链**:`node 20 + bun 1.3.14 + tsci 0.0.1829`。`tsci` 来自 **`tscircuit`** 包(bin=tsci,
**非** `@tscircuit/cli`),且**依赖 bun 运行时**;Rosetta 机器须**用 bun 装**(`bun add -g tscircuit`)
否则原生库(@resvg)架构不匹配。

**实测事实(权威,纠正草稿)**:
- 入口文件是 **`index.circuit.tsx`**(不是 `index.tsx`)。
- trace 选择器实际写法:**`<trace from=".R1 > .pin1" to=".C1 > .pin1" />`**(带 `>`);电源走 `net.VCC`/`net.GND` 成立。
- `tsci build` **默认输出 `dist/<entry>/circuit.json`**,exit 0;**自动匹配嘉立创料号**
  (电阻→`C25104`、LED→`C965799`,另给备选)并产出结构化 **`supplier_footprint_mismatch_warning`** 元素。
- `tsci export -f` 实测可出:`gerbers`(**zip**)/`glb`/`step`/`pcb-svg`/`schematic-svg`/`readable-netlist`
  + `specctra-dsn`/`srj`/`kicad_*`。**无独立 `bom`/`cpl` 格式** → BOM/CPL 须从 circuit.json 派生或走 dev 面板。
- **本地 DFM 可行**:circuit.json 内 `pcb_trace.width`(实测 0.15mm)、`pcb_smtpad`(尺寸+坐标)、
  `pcb_board`(12×8mm)齐全 → 最小线宽/间距/铜到边可离线校验,免导出免 key。
- **`tsci check`** 子命令仅 `netlist/placement/routing`,官方标 under-dev → 以 `tsci build` 的 DRC 为权威。

**统一预览**:`@tscircuit/runframe` v0.0.2042 存在;iframe host `runframe.tscircuit.com/iframe.html`
返回 **200**(可嵌入)。

**嘉立创 `jlcpcb-mcp@0.3.3`(免 key)实测**:MCP server 正常启动、列出 **28 个工具**;
真实调用 `jlcpcb_get_component_pricing(C25104)` **免 key 返回阶梯价**
(100+ $0.0011 / 1000+ $0.0009 / 3000+ $0.0008 / 50000+ $0.0006,available)。
→ 「circuit.json 自动配料号 → 免 key 报价 → 总价」整链成立。

> spike 工作区保留在 `/tmp/pcb-spike/led-demo`(含 dist/circuit.json + out/ 各格式)供 M1 参考。

## 5. 风险与红线

- **不编 API**:JLCPCB 端点/字段、tscircuit JSX props/CLI flag,一律对实时文档校准;拿不准 fail-loud。
- **下单是 gate**:真实下单/付款必须 `--confirm`;无 key 降级网页,绝不假装成功。
- **viewer 红线**:engines 不 `npm install`,runframe 走 iframe host 或预构建 bundle 进 `engines/`。
- **零互引**:pcb 不 import/subprocess 反调其他子技能,只读它们落盘的文件。
- **API key 缺位**:元件报价免 key(M3 不受影响);板级报价+下单待 key,隔离在 M4,无 key 降级网页。
- **`jlcpcb-mcp` 很新**(单作者、刚发布):定为首选集成层但**保留直连 `api.jlcpcb.com` 兜底**;
  锁定版本(如 `jlcpcb-mcp@0.3.3`)避免 npx 拉到破坏性更新;MCP 工具名/字段以实时为准,不编。

---

## 6. 验收总纲

- `pytest skills/pcb/tests` 全绿;`SKILL.md` ≤250 行,父 `SKILL.md` ≤220 行。
- minimal 板端到端:init→check→build→export→viewer 看 PCB/原理图/3D/BOM/总价→报价(→可选下单)。
- 父/子 SKILL 链接指向本文与 `docs/pcb-tscircuit-workflow.md`。
- 3 处共享配置(父路由表 / multi-skill-router / handoff+dependencies)同步。
