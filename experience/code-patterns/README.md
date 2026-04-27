# 代码模式累积（code-patterns）

> 累积从 `references/code-sources/` 搜到的**被采纳**代码片段。
> 下次同领域命中 → 直接复用，零成本。

---

## 目录结构

```
experience/code-patterns/
├── README.md                  # 本文件
├── _cache/                    # code_lookup.py 管理，7 天 TTL
│   └── <domain>/<keyword>.md
├── gears/                     # 领域分类，按需创建
│   └── <pattern-slug>.md
├── surfaces/
├── enclosures/
└── …
```

`_cache/` 与**领域目录**的分工：
- `_cache/` → 脚本自动写（搜索摘要、过期刷新）
- 领域目录 → 人工沉淀（被采纳的精华片段，长期保留）

---

## 何时写入

**R5 / S4 / P4 收尾前**，AI 问用户：
> "本次借鉴了哪些代码？需要沉淀到 `experience/code-patterns/` 吗？"

用户确认 → AI 按下方格式写入。

**禁止写入**的情况：
- License 不安全（GPL / 未标）
- 借鉴成本高、实际没跑通
- 只是博文抄来的数学推导，没有可运行代码

---

## 文件格式

```markdown
---
domain: gears
pattern: involute-profile
source:
  repo: gumyr/bd_warehouse
  commit: a1b2c3d
  file_path: src/bd_warehouse/gear.py
  line_range: L45-L89
license: Apache-2.0
translate_cost: none      # none / low / medium / high
last_verified: 2026-04-27
confidence: 5             # 1~5，跟 data-sources 一致
tags: [involute, spur, bd_warehouse, builtin]
---

# 模式名称

一句话描述。

## 使用场景

- 场景 1
- 场景 2

## 核心代码

```python
# 参考：<source.repo>@<commit> <file>#<line_range> (<license>)
from bd_warehouse.gear import InvoluteGear

gear = InvoluteGear(
    module_size=1.0,
    tooth_count=20,
    pressure_angle=20,
    face_width=5.0,
)
```

## 关键技巧

- 模数 × 齿数 / 2 = 中心距
- `pressure_angle=20` 是 ISO 标准，别改

## 踩过的坑

- 齿数 < 17 时渐开线会自交，需要齿根修正（见 …）

## 用过此模式的项目

- tests/22-gear-reducer/ (2026-04-27)
```

---

## 与其他资源的分工

| 位置 | 负责 | 粒度 |
|------|------|------|
| `references/parts/cheatsheet.md` | build123d **基础 API** 总览 | API 级 |
| `references/parts/patterns.md` | **10 种典型建模模式**（skill 自带） | 模板级 |
| `references/code-sources/<domain>.md` | 领域**外部 repo 清单 + 技巧** | 领域级 |
| `experience/code-patterns/<domain>/` | **本项目采纳过的精华代码片段** | 代码级 |

**判断边界**：
- 第一次用 → `code-sources/` + WebSearch → 落到 `_cache/`
- 确认好用 + 用户同意沉淀 → 写入领域目录（非 _cache）
- 长期沉淀 → 可能升级到 `references/parts/patterns.md`（skill 层面通用）

---

## Cache vs 正式 pattern 文件

| 特性 | `_cache/<domain>/<keyword>.md` | `<domain>/<pattern-slug>.md` |
|------|------------------------------|------------------------------|
| 谁写 | `code_lookup.py` 自动 / AI 写摘要 | AI 和用户共同确认 |
| 保留 | 7 天自动过期 | 永久保留 |
| 内容 | 搜索摘要 + repo 链接 | 完整片段 + 使用经验 |
| 作用 | 快速回忆上次搜到什么 | 精华沉淀，跨项目复用 |

---

## 贡献规则

新增领域目录时：
1. 目录名与 `references/code-sources/catalog.yaml` 的 `domains:` 键一致
2. 首次在某领域沉淀，若本领域在 `references/code-sources/` 下无对应 .md → 建议顺手建 `<domain>.md`
3. frontmatter 必带 `license` + `last_verified`，不合规不收录
