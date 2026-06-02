# shared/ 跨子技能接口变更登记

> 本文是 shared/ 改动的「PR-level」登记表。规则见 `share/build123d-cad改造/08-shared跨子技能协议.md` §8。
> 任何 PR 修改 `shared/handoff-protocols.md` / `shared/multi-skill-router.md` / `shared/dependencies.md` / `shared/schemas/` / `shared/python/` 必须新增一行,否则 CI block。

| 日期 | 变更 | 影响子技能 | Owner | 备注 |
|---|---|---|---|---|
| 2026-06-02 | 初版 handoff/router/dependencies 协议草案 | 全员 | tech_lead | P0-1 骨架同期 |
| 2026-06-02 | `joints.schema.json` v1 落 shared/schemas/ | mechanical · urdf · srdf · testing | algorithm + tech_lead | examples/ 含单腿样例 |
| 2026-06-02 | `cadpy_metadata` 抽到 shared/python/ | urdf · srdf · sdf | tech_lead | 应 04 §8 R4 |
| 2026-06-02 | viewer URL schema `?engine=&dir=&file=` 锁定 | viewer · 所有上游 | fullstack + tech_lead | 与 03 §4 同步 |
| 2026-06-02 | 标准 task 目录结构 + `_errors/` 错误传播约定 | 全员 | tech_lead | 见 08 §2.0 / §2.3 |
| 2026-06-02 | 命名约定 v1(`fl/fr/rl/rr` + `hip/thigh/shank/foot`) | mechanical · urdf · srdf | tech_lead | 见 08 §2.2 |
| 2026-06-02 | **P0-7 tests 骨架 + 命名约定**:每子技能 `tests/{conftest.py, test_smoke.py}` 统一模板;父根 `pytest.ini` 锁 `--import-mode=importlib`;markers `smoke / slow / p1 / p3 / requires_node / requires_build123d` | 全员 | testing | 影响所有未来子技能新增的 tests/ 入口;CI 调度按 `-m smoke` 跑 PR 必跑子集 |
| 2026-06-02 | **P0-9 benchmarks 套件就位**:`skills/mechanical/benchmarks/{run_all,compare_golden,bench_def,models/,prompts/,golden.json}`;fast 子集 #1/#2/#3 < 1 s,full 10 题 < 1 s;golden 由 BRepCheck_Analyzer + STEP reimport 双校验 | mechanical · testing | testing | golden 当前 `_meta.frozen_by` 待 Dave 复核签字;enclosure_box / impeller solid_count != 1 已记入复核单 |
| 2026-06-02 | **P1-4 evals/ 模板落盘**:`evals/bench-mechanical-{pr,nightly}.yaml` + README;PR 触发 fast block-merge,nightly cron full 黄通知 | testing | testing | 落公司 CI evals gate `build123d-cad-bench-{pr,nightly}` |
| 2026-06-02 | **P0-3 viewer 多引擎容器实施完成** — ① router 升 21 条目 / 33 后缀(新增 `.brep/.iges/.igs/.obj/.gltf/.fcstd/.png/.jpg/.jpeg/.webp` 进 cad 引擎 + `.json → 'ambiguous'` 哨兵,server 见 ambiguous 时回 409 + 提示需 `?engine=` 透传);② 父 server.mjs 改为反向代理:cad backend 作为内部子进程(127.0.0.1:5178+ 动态分配),父 server 自管 `/__cad/server` `/__cad/shutdown` `/files/*` 安全边界 + stub engines 拦截,其余 `/__cad/*` / `/assets/*` / `/<chunk>.js` 透传给 cad 子进程,SPA 期望的 `/__cad/catalog` 已 curl 实测返回 entries;③ pcb/sch/sim stub 占位 HTML 实测渲染 OK;④ tests 75 passed / 4 skipped(P1-5 + P3 任务跳过) | viewer · 所有上游(mechanical / urdf / gcode / sendcutsend / parts-catalog) | fullstack | M2 端到端验收第二条 ready(`bash start.sh <step> <ws>` → URL → 浏览器 3D);headless chrome 无 GPU 不渲染 WebGL,真 3D 渲染需用户本机浏览器自验 |

## 登记规则

- 任何修改 shared/ 的 PR 必须新增一行,内容含日期 / 变更 / 影响子技能 / Owner / 备注
- 破坏性变更(改字段名/类型/枚举值)需 @tech_lead 评审通过 + 用 ⚠️ 标记
- CI 在 `git diff shared/` 命中时,要求 `git diff shared/CHANGELOG.md` 也命中,否则 block
