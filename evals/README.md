# evals/ — agent-eval 任务模板

落地于 P1-4(目标 2026-06-15)。

| 任务 | 触发 | 套件 | 总耗时上限 | 失败处理 | gate id |
|---|---|---|---|---|---|
| `bench-mechanical-pr.yaml` | PR 命中 mechanical/shared/python/SKILL.md | fast(#1/#2/#3) | 120 s | block merge(PR 红) | `build123d-cad-bench-pr` |
| `bench-mechanical-nightly.yaml` | 02:30 cron + push to main + dispatch | full(#1~#10) | 600 s | 黄 + 通知 #待审批 + 24h SLA | `build123d-cad-bench-nightly` |

完整字段说明见 `share/build123d-cad改造/07-测试与验证基建.md` §7。

## 本地复现

```bash
# fast(< 60 s)
~/work/build123d-parts-lib/.venv/bin/python -m skills.mechanical.benchmarks.run_all --suite fast
~/work/build123d-parts-lib/.venv/bin/python -m skills.mechanical.benchmarks.compare_golden --suite fast

# full(< 10 min)
~/work/build123d-parts-lib/.venv/bin/python -m skills.mechanical.benchmarks.run_all --suite full
~/work/build123d-parts-lib/.venv/bin/python -m skills.mechanical.benchmarks.compare_golden --suite full

# 用 agent-eval 直接跑(等价 CI)
agent-eval run evals/bench-mechanical-pr.yaml
agent-eval run evals/bench-mechanical-nightly.yaml
```

## golden 基线

- 文件:`skills/mechanical/benchmarks/golden.json`
- 当前 `_meta.frozen_by` = `<待 Dave 签字>`(P0-9 自动种子)
- 改动必须 `@tech_lead + @mechanical(Dave)` 双签;CI 不允许 `--emit-golden`
