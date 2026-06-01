---
name: electronics-bom
description: 电子 BOM 全链路 — 元件型号→封装→3D→报价 多源查询(JLCPCB/LCSC/Octopart/SnapEDA)。当前为 P3 占位
owner: hardware
status: WIP
phase: P0-stub
since: 2026-06-02
---

# electronics-bom 子技能(P3 占位)

> **当前状态:WIP**。与 [pcb](../pcb/SKILL.md) 同期启动(P3,Gate 3 通过后)。
> P0 阶段父级路由命中应回答「电子域 P3 启动,见 share/06」。

## 触发场景(关键词)

父级 SKILL.md 路由命中本技能的关键词(与 [父级路由表](../../SKILL.md) 第 61 行同步):

- 「元件型号 / 封装 / 选型 / BOM」
- 「JLCPCB / LCSC / Octopart / SnapEDA / UltraLibrarian」
- 「symbol / footprint / 3D 模型 找一下」
- 「替代料 / 库存 / 询价」

不命中场景:
- 「PCB / 原理图 / Gerber」 → `pcb`
- 「机械标准件 STEP」 → `parts-catalog`(电子料归本 skill,机械标准件归 parts-catalog,见 [06 §6.3](../../../share/build123d-cad改造/06-电子域扩展-pcb-eda-drc.md#63-是否需要专门的electrical-bom与mechanical-bom拆分))

## P3 路线图

落地任务挂在 [06 §3 P3-3](../../../share/build123d-cad改造/06-电子域扩展-pcb-eda-drc.md#3-p3-路线图落地任务卡):

| # | 任务 | 工作量 | 验收 |
|---|---|---|---|
| P3-3 | 元件库接入 | 3d | 输入型号 → 出 symbol+footprint+3D 三件套 |

数据源优先级(详见 [06 §4.4](../../../share/build123d-cad改造/06-电子域扩展-pcb-eda-drc.md#44-元件库--bom-数据源)):

| 优先级 | 数据源 | 用途 | 推荐档位 |
|---|---|---|---|
| 1 | **JLCPCB Basic Library** | 700 颗常用料,免上机费 | ★★★★★ 首选 |
| 2 | **JLCPCB Extended** | 30k 颗扩展料,$3 上机费 | ★★★★ |
| 3 | **LCSC**(立创商城) | 中国最大分销 | ★★★★ |
| 4 | **Octopart** | 全球分销聚合,跨厂比价 | ★★★ 兜底 |
| - | **SnapEDA / UltraLibrarian** | 建库源(symbol+footprint+3D) | ★★★★ |
| - | **Digi-Key** | 高端料 | ★★ 偶发 |

策略:**JLCPCB 优先 → Octopart 兜底**两段式查询。

## 计划能力清单(P3 启动后填)

P0 占位条目,P3 起膨胀(模板见 [06 §2.6a.2](../../../share/build123d-cad改造/06-电子域扩展-pcb-eda-drc.md#26a2-skillselectronics-bomskillmd-膨胀模板p3-起)):

- [ ] `scripts/lookup.py` — `python lookup.py <part_no>` → JSON {symbol, footprint, 3d_step, price, stock, datasheet, alternates[]}
- [ ] `scripts/bom_lookup.py` — 批量查 BOM CSV
- [ ] `scripts/sync_jlcpcb.sh` — 季度同步 JLCPCB Basic 全量
- [ ] `scripts/sources/{jlcpcb,lcsc,octopart,snapeda,ultralibrarian}.py` — 各数据源适配器

## 与其他 skill 的接口(handoff,P3 起)

- **被 pcb skill 反向调**:`pcb/scripts/sch_from_skidl.py` 通过 subprocess 调 `lookup.py` 查料
  → JSON 输出到 stdout(命令行隔离,符合 [08 §1](../../shared/handoff-protocols.md) 子技能零互引用红线)
- **API key 走环境变量**:`EDA_LCSC_API_KEY` / `EDA_OCTOPART_API_KEY`,**不进 git**
- **本地缓存**:`scripts/library_cache/`(.gitignore,size 控制 < 200MB)

## 输出物(P3 起)

落 `output/<task>/electrical/library/`(符合 [08 §2.0](../../shared/handoff-protocols.md)):

- `<part_no>.kicad_sym`(symbol)
- `<part_no>.pretty/<part_no>.kicad_mod`(footprint)
- `<part_no>.step`(3D)
- stdout JSON(给 agent / pcb skill 消费)

## 不做什么

- ❌ 元件选型推荐(那是工程师决策,本 skill 只查不荐)
- ❌ 采购下单(查询 ≠ 交易)
- ❌ 机械标准件 BOM(归 [parts-catalog](../parts-catalog/SKILL.md))
- ❌ 整机装配 BOM(归项目层,不是 skill 层)

## 参考资料

- JLCPCB SMT Parts: https://jlcpcb.com/parts
- SnapEDA API: https://www.snapeda.com/api/
- Octopart API: https://octopart.com/api/v4
- 选型材料: `share/build123d-cad改造/06-电子域扩展-pcb-eda-drc.md` §4.4
