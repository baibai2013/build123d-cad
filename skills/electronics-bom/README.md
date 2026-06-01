# electronics-bom — 开发者说明

P3 占位子技能,与 [pcb](../pcb/SKILL.md) 同期启动。
落地触发条件 = 用户给出第一个 PCB 项目 + Gate 3 通过。

详见 [SKILL.md](SKILL.md) 与 [share/06 §4.4](../../../share/build123d-cad改造/06-电子域扩展-pcb-eda-drc.md#44-元件库--bom-数据源)。

## 当前状态

| 项 | 状态 |
|---|---|
| SKILL.md(占位 + 触发关键词 + 数据源优先级) | ✅ |
| references/ | 空(P3 起填 source-priority / jlcpcb-csv-format / snapeda-api 等) |
| scripts/ | 空(P3 起填 lookup / bom_lookup / sync_jlcpcb 等) |
| tests/ | placeholder smoke 一条 |
| data/ | 空(P3 起放 jlcpcb-basic-snapshot.csv 历史快照) |

## P3 启动后做什么

按 [06 §3.3a.2](../../../share/build123d-cad改造/06-电子域扩展-pcb-eda-drc.md#33a2-skillselectronics-bom--元件库管理原-44-数据源策略的实现) 拆解:

```
skills/electronics-bom/
├── SKILL.md          # 膨胀到 ≤ 250 行(模板见 06 §2.6a.2)
├── references/
│   ├── source-priority.md
│   ├── jlcpcb-csv-format.md
│   └── snapeda-api.md
├── scripts/
│   ├── lookup.py
│   ├── bom_lookup.py
│   ├── sync_jlcpcb.sh
│   ├── sources/
│   │   ├── jlcpcb.py
│   │   ├── lcsc.py
│   │   ├── octopart.py
│   │   ├── snapeda.py
│   │   └── ultralibrarian.py
│   └── library_cache/  (.gitignore,size 控制 < 200MB)
├── tests/
│   ├── test_lookup_lm358.py        # 集成,需网络
│   ├── test_lookup_fallback.py     # JLCPCB 缺料 → Octopart 兜底
│   └── test_csv_parser.py          # JLCPCB CSV 解析,无网络
└── data/
    └── jlcpcb-basic-snapshot.csv
```

## API key 安全约定

- LCSC / Octopart 等 API key **永远不进 git**
- 走环境变量 `EDA_LCSC_API_KEY` / `EDA_OCTOPART_API_KEY`
- CI 跑用 mock,真实集成测试加 `@pytest.mark.network`

## P0 期间不要做什么

- ❌ 不要写真实 API 调用(等 Gate 3)
- ❌ 不要 commit JLCPCB CSV 全量(P3 起再加,size 大)
- ❌ 不要把 API key 写进任何文件(永远走环境变量)
