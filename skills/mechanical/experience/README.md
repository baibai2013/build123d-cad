# experience/ — 参考物建模经验缓存

本目录存放用户跑完参考物建模协议 R1~R5 后沉淀的**具体产品**实战笔记，供下次建同型号/同类产品时 R1 预检索复用。

## 与 assets/ 的区别

| 维度 | `assets/` | `experience/` |
|---|---|---|
| 内容 | 可运行的 .py 参考代码（enclosure/servo_mount 等通用模板） | 某个具体产品的实战笔记 |
| 粒度 | 抽象几何范式 | 具体型号 |
| 来源 | skill 作者预置 | 用户跑完 R1~R5 后沉淀 |
| 索引 | 按零件类型（mounting/parts/...） | 按 `<category>/<slug>` |
| 用途 | R4 建模参考 | R1 开始时"上次这型号怎么建的" |

## 目录结构

```
experience/
├── README.md                          （本文件）
├── <category>/                        （来自 Playbook Appendix A 白名单）
│   └── <slug>.md                      （kebab-case 产品短名，对齐 references/<slug>/）
```

## 条目 schema

每个 `.md` 条目使用 YAML frontmatter + 3 节固定 markdown body。完整 schema 见 Playbook `Step R5 — Experience Draft 模板` 节。

frontmatter 字段：
- `slug`：产品短名（kebab-case）
- `category`：Playbook Appendix A 白名单里的一个
- `tags`：3~5 个类别词
- `confidence`：本次 params.md 星级**中位数**（1~5）
- `last_updated`：ISO 日期，形如 `2026-04-18`
- `related_tests`：test 仓路径列表（跨仓引用约定，形如 `tests/13-redmi-k80-pro`）
- `source_model`：`step` / `reverse-engineered` / `mixed`

body 节：
- `## 关键参数（下次直接用）`（必填）
- `## 踩过的坑`（必填；为空时 AI 显式问用户确认）
- `## 下次直接复用（copy-paste 片段）`（必填）
- `## 未解决 / 待验证`（可选）

## ⚠️ 发布风险说明

**experience/ 目录随 skill 仓一起进 git**。如果该仓将来公开发布，以下内容会一并暴露：
- 产品型号名 + 你测过的关键尺寸
- 踩过的坑（可能暗示客户项目 / 未公开产品）
- copy-paste 片段里的命名

**慎写敏感内容**。涉及客户/未公开产品时，建议：
1. 别写进 experience/（本次建模用完即弃）
2. 或用脱敏 slug（如 `customer-phone-A` 而非真实型号）
3. 长期可加 `experience/.private/` 放 `.gitignore`（当前未启用）

## 读写流程

- **读**：Playbook Step R1 前置检索自动做（glob `experience/*/<slug>.md` 精确匹配 → 失败 fallback 到 `experience/<category>/*.md` 同类 ≤2 条）。
- **写**：Playbook Step R5 由 AI 起草 Experience Draft 块，用户 review 后落盘。未经 review 不得自动写盘。
