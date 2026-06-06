# 嘉立创(JLCPCB)对接:`jlcpcb-mcp` — 实测 0.3.3

> 首选集成层 = MCP server **`jlcpcb-mcp`**(Eyalm321,npm `jlcpcb-mcp`);直连 `api.jlcpcb.com` 作兜底。
> 数据源:本地 SQLite(`yaqwsx/jlcparts` 快照)+ LCSC 实时(`wmsc.lcsc.com`)+ 官方 `open.jlcpcb.com`(配 key 时)。
> 工具名/字段对实时为准,**不编**。

## 安装

```bash
claude mcp add jlcpcb -- npx -y jlcpcb-mcp@0.3.3   # 锁版本;stdio;首次构建本地 DB 数分钟
```

## 凭据(只有板级报价/下单/官方库需要)

| 环境变量 | 用途 |
|---|---|
| `JLCPCB_APP_ID` / `JLCPCB_ACCESS_KEY` / `JLCPCB_SECRET_KEY` | 官方 API 鉴权 |
| `JLCPCB_ENABLE_ORDERS=true` | **下单总开关**(不开则 create_order 禁用) |

> 元件查询/报价/库存/datasheet **免 key**。本技能默认不接 key(决策①),报价/下单代码就绪但默认 disabled。

## 28 个工具(实测列出)

**免 key — 目录 + 实时数据**
- `jlcpcb_search_components` 关键词/参数搜,带实时库存/价格,Basic 优先
- `jlcpcb_get_component_details` 单件全量(规格/库存/价格档/datasheet/图)
- `jlcpcb_get_component_stock` 实时库存
- `jlcpcb_get_component_pricing` 阶梯价(USD)— **实测 C25104 返回 100+ $0.0011 …**
- `jlcpcb_get_datasheet_url` / `jlcpcb_list_categories` / `jlcpcb_database_status` / `jlcpcb_refresh_database`

**需 key — 官方库**
- `jlcpcb_official_get_component_detail`(LCSC code 权威)/ `jlcpcb_official_component_library`
  / `jlcpcb_official_private_library` / `jlcpcb_official_component_feed`

**需 key — PCB / 钢网**
- `jlcpcb_pcb_upload_gerber`(→ fileKey)/ `jlcpcb_pcb_calculate_price`(报价,不下单)
- `jlcpcb_pcb_get_audit_info`(**官方工程审核 = DFM 权威**)/ `jlcpcb_pcb_get_order_detail` / `jlcpcb_pcb_get_wip_process`
- `jlcpcb_pcb_upload_blind_via_hole_img` / `jlcpcb_pcb_impedance_template_list` / `jlcpcb_pcb_stencil_price_config`
- ⚠️ `jlcpcb_pcb_create_order` — **真付费下单,默认禁用**(需 `JLCPCB_ENABLE_ORDERS=true`)

**需 key — 3D 打印(本技能不用)**:`jlcpcb_tdp_*`(upload/analysis/price/order…)

## 本技能用法分层

| 阶段 | 工具 | key | gate |
|---|---|---|---|
| BOM 物料报价/总价 | `search_components` / `get_component_pricing` / `get_component_details` | ❌ | — |
| 板级报价 | `upload_gerber` → `calculate_price` | ✅ | — |
| DFM 官方审核 | `get_audit_info` | ✅ | — |
| 下单 | `create_order` | ✅ | `ENABLE_ORDERS=true` + `--confirm` |

## 降级纪律(三级,绝不假装成功)

`jlcpcb-mcp`(首选)→ 直连 `api.jlcpcb.com`(兜底)→ 打开 `https://jlcpcb.com/quote` 上传页(最后)。
每级失败如实报,`quote.json` 标 `quote_source: mcp | api | manual`。
