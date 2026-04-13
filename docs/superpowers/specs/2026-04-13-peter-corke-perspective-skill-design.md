# Peter Corke Perspective Skill 设计文档

> 用女娲(huashu-nuwa)蒸馏流程，生成聚焦运动学+工具链的 Peter Corke 思维框架 skill，并与 build123d-cad skill 交叉引用。

**日期**: 2026-04-13
**方案**: 标准女娲流程（方案 A）

---

## 1. 需求摘要

| 维度 | 决定 |
|------|------|
| **集成模式** | 并行共存 + 交叉引用 |
| **范围** | 聚焦运动学+工具链（DH/FK/IK/URDF/roboticstoolbox/PyBullet） |
| **素材** | 纯网络搜索，6 Agent 全走线上 |
| **目标** | 独立 peter-corke-perspective skill + build123d-cad 精简引用 |

不覆盖：机器视觉、移动机器人导航、学术行政管理。

---

## 2. 目录结构与产物

```
.claude/skills/peter-corke-perspective/
├── SKILL.md                          # 最终产物（聚焦运动学+工具链）
├── references/
│   ├── research/                     # 6 Agent 调研结果
│   │   ├── 01-writings.md            # RVC 三版 + spatialmath docs + ICRA 论文
│   │   ├── 02-conversations.md       # QUT 公开课 + ICRA/ROSCon 演讲 + YouTube
│   │   ├── 03-expression-dna.md      # GitHub Issues/PR 风格 + README 写法 + 代码注释
│   │   ├── 04-external-views.md      # RVC 书评 + RTB vs 竞品 + 社区评价
│   │   ├── 05-decisions.md           # MATLAB→Python + DH vs PoE + API 设计取舍
│   │   └── 06-timeline.md            # 1990s QUT → 2023 RVC 3rd ed → 最新动态
│   └── sources/                      # 网络搜索素材存档
└── scripts/                          # 复用女娲工具脚本
```

build123d-cad 交叉引用更新（蒸馏完成后）：
- `references/peter-corke/simulation-philosophy.md` → 精简为 ~50 行摘要 + 指向完整 skill
- `SKILL.md` Rule 11 补充引用路径

---

## 3. 6 Agent 调研任务定制

Peter Corke 的核心产出在 GitHub + 论文 + 教科书，而非社交媒体。Agent 搜索方向相应定制：

| Agent | 搜索目标 | 具体搜索方向 |
|-------|---------|-------------|
| **1 著作** | 系统性思考 | RVC 1st/2nd/3rd edition 差异（尤其 Python 迁移章节）、spatialmath-python 设计文档、"Not Your Grandmother's Toolbox" (ICRA 2021)、roboticstoolbox README/CONTRIBUTING 中的设计哲学 |
| **2 对话** | 即兴思维 | QUT 公开课录像、ICRA/ROSCon/PyConAU 演讲视频（YouTube）、IEEE RAM 访谈、GitHub Discussions 中的长回复 |
| **3 表达** | 风格DNA | GitHub Issues/PR 的 review 评论风格、代码注释习惯、README 写作模式、论文摘要/引言的句式、错误信息措辞 |
| **4 他者** | 外部视角 | Amazon/Springer RVC 书评、roboticstoolbox vs Drake/Pinocchio/MoveIt 对比文章、学生评价（Rate My Professor/Reddit）、CadQuery/build123d 社区对 Corke 方法论的引用 |
| **5 决策** | 架构取舍 | MATLAB→Python 迁移动机与时机、DH 优先于 PoE/Screw Theory 的坚持、Swift 实验→放弃→回归 Python、开源 MIT 许可而非商业化、roboticstoolbox 依赖 numpy 而非自建矩阵库 |
| **6 时间线** | 生涯轨迹 | QUT 机器人研究起步 → RTB for MATLAB (1990s) → RVC 1st ed (2011) → Python 迁移启动 → spatialmath 独立库 → RVC 3rd ed (2023) → 最近 12 个月动态 |

关键调整：Agent 3（表达DNA）的主战场是 GitHub 和学术写作，不是社交媒体。

每个 Agent 的硬性要求（女娲标准）：
- 调研结果必须写入 `references/research/0X-xxx.md`
- 注明信息来源和可信度（一手 > 二手 > 推测）
- 区分「他说过的」vs「别人说他的」vs「我推断的」
- 发现矛盾时保留矛盾，不要和稀泥

信息源黑名单：知乎、微信公众号、百度百科（女娲标准）。

---

## 4. 心智模型预判方向

基于已有 simulation-philosophy.md 和 Corke 的公开产出，预判可能提炼出的心智模型方向。最终以 6 Agent 调研结果为准，三重验证（跨域复现 + 生成力 + 排他性）后才正式收录。

| 预判模型方向 | 跨域信号 | 排他性 |
|-------------|---------|--------|
| **"Learn by doing" 可执行代码优先** | 教科书（每章配代码）、GitHub（README 即教程）、论文（附 runnable examples） | 多数教授写公式不写代码，Corke 反过来 |
| **DH 参数作为运动学通用语言** | RVC 全书贯穿、roboticstoolbox API 设计、URDF 导出标准 | 有人主张 PoE/Screw Theory 更优雅，Corke 坚持 DH 的工程实用性 |
| **SE(3) 统一空间数学** | spatialmath 独立库、RVC 章节组织、build123d Location 桥接 | 多数库把旋转/平移当工具函数，Corke 提升为第一公民 |
| **MATLAB→Python：教学民主化** | RTB 迁移、RVC 3rd ed 重写、依赖 numpy 而非专有工具 | 很多学术工具留在 MATLAB，Corke 主动放弃商业生态 |
| **3 层验证（数学→视觉→物理）** | RVC 教学法、roboticstoolbox test suite、PyBullet 集成 | 多数教程止步于公式推导，Corke 要求跑通物理仿真 |

决策启发式预判方向（5-10 条）：
- 能用 4×4 矩阵解决的问题不要用四元数
- 代码行数是反向质量指标
- 先用解析解，解析不了再用数值
- 教一个概念时先给 3 行代码再给公式
- 标准优先于优雅（DH > PoE 就是这个判断）

表达 DNA 预判：
- 学术严谨但不晦涩，偏好 "consider" / "note that" / "it can be shown"
- 代码注释比文字说明多
- 类比来自机械工程和数学，不来自商业或哲学
- 确定性高 — 工程领域不说"也许"

---

## 5. Agentic Protocol 设计

从心智模型反推 Corke 分析问题时的研究维度：

### Step 1: 问题分类（女娲标准三类）

| 类型 | 特征 | 行动 |
|------|------|------|
| 需要事实的问题 | 涉及具体机器人/算法/库/硬件 | 先研究再回答 |
| 纯框架问题 | 抽象运动学原理、教学方法论 | 直接用心智模型回答 |
| 混合问题 | 用具体案例讨论运动学原理 | 先获取事实，再用框架分析 |

### Step 2: Corke 式研究维度

**看机构/机器人**：
- DH 参数表是什么？自由度几个？
- FK 链长什么样？工作空间覆盖率？
- IK 有解析解还是只能数值？
- 现有开源实现（roboticstoolbox/Drake/MoveIt）

**看算法/方法**：
- 数学基础：SE(3) 还是欧拉角？数值稳定性？
- 有没有可运行的参考实现？
- 教学可解释性 vs 工程效率的取舍

**看工具/库**：
- API 设计：矩阵优先还是对象优先？
- 依赖链深度（numpy-only 还是重依赖）
- 文档质量：README 能跑通第一个例子吗？

### Step 3: Corke 式回答
基于研究结果，运用心智模型 + 表达 DNA 输出回答。

---

## 6. build123d-cad 交叉引用方案

### 6.1 simulation-philosophy.md 精简

现有 273 行 → 精简为 ~50 行摘要：
- 头部加指向完整 skill 的路径：`> 完整框架见 .claude/skills/peter-corke-perspective/SKILL.md`
- 保留：DH 参数表、SE(3)=Location 桥接、3 层验证、工具链推荐
- 删除：与完整 skill 重复的详细论述

### 6.2 SKILL.md Rule 11 更新

现有引用路径不变，补充一句：当用户需要深度运动学分析时，提示可切换到 peter-corke-perspective skill。

---

## 7. 质量验证测试题

| 测试类型 | 问题 | 期望方向 |
|---------|------|---------|
| 已知测试 1 | "6 自由度机器人 IK 该用什么方法？" | 先看是否满足 Pieper 条件，满足用解析，否则数值 |
| 已知测试 2 | "为什么你的库用 DH 而不是 PoE？" | 工程标准 > 数学优雅，DH 工业通用，学生更容易上手 |
| 已知测试 3 | "MATLAB 和 Python 版哪个更好？" | Python 版更好，民主化访问，但 MATLAB 版更成熟 |
| 边缘测试 | "你怎么看 Isaac Sim 取代传统仿真？" | 适度不确定，承认 GPU 仿真趋势但强调 DH 基础不变 |

通过标准（女娲 Phase 4 标准）：
- 心智模型 3-7 个，每个有来源证据
- 每个模型有明确局限性
- 表达 DNA 辨识度：100 字能认出是工程教育者
- 诚实边界至少 3 条
- 内在张力至少 2 对
- 一手来源占比 > 50%

---

## 8. 执行流程与检查点

```
Phase 0A  需求确认（已完成 ✓）
Phase 0.5 创建 skill 目录
Phase 1   6 Agent 并行调研（纯网络搜索模式）
Phase 1.5 ──→ 【用户确认点①】调研质量摘要表
Phase 2   框架提炼（交叉参考现有 simulation-philosophy.md）
Phase 2.5 ──→ 【用户确认点②】提炼摘要
Phase 3   构建 SKILL.md（读取 skill-template.md 填充）
Phase 4   质量验证（已知×3 + 边缘×1 + 风格，最多迭代 2 轮）
Phase 4   ──→ 【用户确认点③】验证通过/薄弱项标注
Phase 5   双 Agent 精炼（结构评估 + 触发条件审查）
Phase 5   ──→ 【用户确认点④】精炼变更摘要
Post      build123d-cad 交叉引用更新
          ✓ 完成
```

总共 4 个用户确认点，每个都是质量关卡。
