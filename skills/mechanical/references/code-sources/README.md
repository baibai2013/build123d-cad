# 代码源目录（Code Sources）

> **用途**：建模前先翻社区代码，借鉴成熟实现，紧跟时代。
> 解决"AI 凭训练数据写过时代码 / 写社区已有成熟实现的轮子"问题。

---

## 一句话原则

> **借鉴 > 原创**。零件级实现紧跟社区；组合设计才留创意。

---

## 目录组织

```
references/code-sources/
├── README.md                  # 本文件（规范 + 借鉴原则 + License）
├── catalog.yaml               # 5 主力代码库白名单 + 6 领域映射 + WebSearch prompts
├── cadquery-to-build123d.md   # ★ CadQuery → build123d 翻译核心规则
├── gears.md                   # 齿轮领域（已建）
├── surfaces.md                # 曲面/有机（已建）
├── enclosures.md              # 外壳/卡扣（已建）
└── robotics.md / fixtures.md / simulation.md  # 按需扩充
```

---

## 查询方式

```bash
SKILL=/Users/liyijiang/.agents/skills/build123d-cad

# 按领域
python3 $SKILL/scripts/research/code_lookup.py gears
python3 $SKILL/scripts/research/code_lookup.py surfaces

# 按关键词（跨领域模糊搜）
python3 $SKILL/scripts/research/code_lookup.py "involute curve"

# 直接输出 WebSearch prompt 供粘贴
python3 $SKILL/scripts/research/code_lookup.py gears --websearch

# 管理
python3 $SKILL/scripts/research/code_lookup.py --list-domains
python3 $SKILL/scripts/research/code_lookup.py --cache-status
python3 $SKILL/scripts/research/code_lookup.py gears --fresh  # 强制重搜
```

---

## 工作流（在 Playbook 里怎么用）

三个 Playbook 都有"代码库巡查"子步骤：

| Playbook | 子步骤 | 触发 |
|----------|-------|------|
| single-part | Step S2.5 | 几何对齐后、建模前 |
| multi-part  | Phase P2 Step 2.0 | 每个部件 Pn 建模前 |
| reference-product | Step R4.0 | 进 R4 建模前 |

**标准流程**：
1. AI 识别本次涉及的领域关键词（最多 2 个）
2. 跑 `code_lookup.py <domain>` → 得 repos + prompts
3. cache miss → AI 跑 WebSearch → 整理"借鉴候选表"
4. `[halt-for-user]` 让用户选借鉴项
5. 用户确认 → 下一 Step 代码里明确引用来源

---

## 主力代码库（5 个，`catalog.yaml` 详述）

| # | Repo | License | 用途 |
|---|------|---------|------|
| 1 | gumyr/build123d | Apache-2.0 | 原作者主库，examples/ + tests/ 权威 |
| 2 | gumyr/bd_warehouse | Apache-2.0 | 官方扩展：齿轮/螺纹/紧固件 |
| 3 | CadQuery/cadquery | Apache-2.0 | 翻译源（~80% 机械翻译） |
| 4 | CadQuery/cadquery-contrib | MIT | 社区示例：齿轮/外壳/教程 |
| 5 | jmwright/cadquery-stubs | Apache-2.0 | CadQuery API 类型参考 |

扩充时修改 `catalog.yaml` 的 `core_repos:` 节。

---

## 6 个主领域

1. **gears** — 齿轮 / 渐开线 / 斜齿 / 行星齿轮
2. **surfaces** — Loft / Sweep / NURBS / 有机曲面
3. **enclosures** — 外壳 / 卡扣 / 抽壳 / 散热孔
4. **robotics** — 机械臂 / 腿 / 步态 / URDF（doc 待建）
5. **fixtures** — 夹具 / 支架 / 定位销（doc 待建）
6. **simulation** — PyBullet / 运动仿真（doc 待建）

每个领域在 `catalog.yaml` 的 `domains:` 节下有对应入口。

---

## License 纪律

借鉴前**必须**核对 License（`catalog.yaml` 已标注 repo License，新增 repo 时要填）：

| 类别 | License | 规则 |
|------|---------|------|
| 🟢 安全 | MIT / BSD / Apache-2.0 / Unlicense / CC0 | 注明来源 repo + commit 即可借鉴 |
| 🟡 谨慎 | GPL / AGPL / LGPL | **默认禁用**（传染性）。除非项目本就 GPL，且用户显式确认 |
| 🔴 禁用 | 未标 License / 商业 / 自定义 | 禁止借鉴。让用户联系原作者或完全自写 |

**引用格式**（借鉴代码后在 .py 里写）：

```python
# 参考：gumyr/bd_warehouse@a1b2c3d gears.py#L45-89 (Apache-2.0)
from bd_warehouse.gear import InvoluteGear
```

---

## Cache 机制

查询结果缓存在 `experience/code-patterns/_cache/<domain>/<keyword>.md`：

- **有效期**：7 天
- **命中行为**：脚本直接返回 cached prompt，不提示 AI 搜索
- **过期/未命中**：脚本给 fresh prompts，AI 跑 WebSearch 后把摘要回写进 cache
- **强制刷新**：`--fresh` 标志

---

## 与其他资源的分工

| 资源 | 负责 | 例子 |
|------|------|------|
| `references/parts/cheatsheet.md` | build123d **基础 API**（已封装） | `Hole(radius=r)`、`fillet(edges, r)` |
| `references/parts/patterns.md` | **10 种典型建模模式** | 安装板、法兰、旋转体、抽壳 |
| `references/code-sources/` | **社区代码借鉴清单 + 领域路径** | 齿轮用 bd_warehouse、外壳抄 cadquery-contrib |
| `experience/code-patterns/` | **学过的组合用法 / 领域实现** | 本项目采纳的渐开线齿廓片段 |

**判断边界**：
- build123d 内置 API 能搞定 → cheatsheet/patterns
- 需要翻社区才知道怎么写 → code-sources + WebSearch
- 已借鉴过的精华片段（需复用） → code-patterns 累积

---

## 贡献规则

新增条目时：

1. **catalog.yaml 里 repo 必须带完整 `license:` 字段**——缺了默认 blocked
2. **confidence ≤ 2 的 repo 不加**——维护压力过大
3. **新增领域 .md 文件**：同时在 catalog.yaml `domains:` 注册 + 在 README 的"6 个主领域"表更新
4. **实际用过的代码片段**：沉淀到 `experience/code-patterns/<domain>/<slug>.md`，frontmatter 带 `source` / `license` / `last_verified`
