# Peter Corke Perspective Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Use the huashu-nuwa (女娲) distillation pipeline to create a peter-corke-perspective skill focused on kinematics + toolchain, then cross-reference it with the existing build123d-cad skill.

**Architecture:** Standard 女娲 6-phase process: create skill directory → 6 parallel research agents → research review → synthesis → build SKILL.md → quality validation → dual-agent refinement → build123d-cad cross-reference update. Peter Corke's primary information sources are GitHub repos, academic publications, and textbooks rather than social media.

**Tech Stack:** Claude Code Agent tool (subagents), WebSearch, huashu-nuwa SKILL.md process, huashu-nuwa skill-template.md, huashu-nuwa extraction-framework.md

**Design Spec:** `docs/superpowers/specs/2026-04-13-peter-corke-perspective-skill-design.md`

---

## File Structure

### New files (peter-corke-perspective skill)

| File | Responsibility |
|------|---------------|
| `.claude/skills/peter-corke-perspective/SKILL.md` | Final distilled skill — mental models, heuristics, expression DNA, agentic protocol |
| `.claude/skills/peter-corke-perspective/references/research/01-writings.md` | Agent 1 output: RVC editions, spatialmath docs, ICRA papers |
| `.claude/skills/peter-corke-perspective/references/research/02-conversations.md` | Agent 2 output: QUT lectures, ICRA/ROSCon talks, YouTube, GitHub Discussions |
| `.claude/skills/peter-corke-perspective/references/research/03-expression-dna.md` | Agent 3 output: GitHub Issues/PR style, README patterns, code comments, paper prose |
| `.claude/skills/peter-corke-perspective/references/research/04-external-views.md` | Agent 4 output: RVC book reviews, RTB vs competitors, student/community evaluations |
| `.claude/skills/peter-corke-perspective/references/research/05-decisions.md` | Agent 5 output: MATLAB→Python, DH vs PoE, Swift experiment, open-source licensing |
| `.claude/skills/peter-corke-perspective/references/research/06-timeline.md` | Agent 6 output: 1990s QUT → RTB MATLAB → RVC editions → Python migration → latest |

### Modified files (build123d-cad cross-reference)

| File | Change |
|------|--------|
| `references/peter-corke/simulation-philosophy.md` | Trim 273→~50 lines, add pointer to full skill |
| `SKILL.md` (line 36, Rule 11) | Add mention of peter-corke-perspective skill for deep kinematics analysis |

---

## Task 1: Create Skill Directory Structure

**Files:**
- Create: `.claude/skills/peter-corke-perspective/references/research/` (directory)
- Create: `.claude/skills/peter-corke-perspective/references/sources/` (directory)

- [ ] **Step 1: Create the full directory tree**

Run:
```bash
mkdir -p /c/Users/Administrator/.claude/skills/peter-corke-perspective/references/research
mkdir -p /c/Users/Administrator/.claude/skills/peter-corke-perspective/references/sources
mkdir -p /c/Users/Administrator/.claude/skills/peter-corke-perspective/scripts
```

- [ ] **Step 2: Verify directory exists**

Run:
```bash
ls -R /c/Users/Administrator/.claude/skills/peter-corke-perspective/
```

Expected: Three subdirectories visible (references/research, references/sources, scripts).

- [ ] **Step 3: Commit**

```bash
cd /c/Users/Administrator/.agents/skills/build123d-cad
git add -A
git commit -m "chore: create peter-corke-perspective skill directory structure"
```

---

## Tasks 2-7: Six Parallel Research Agents (Phase 1)

> **IMPORTANT:** Tasks 2 through 7 are **independent** and MUST be run in parallel (6 concurrent subagents). Do NOT run them sequentially. Use the Agent tool with 6 parallel calls in a single message.

## Task 2: Agent 1 — Writings Research (著作与系统思考)

**Files:**
- Create: `.claude/skills/peter-corke-perspective/references/research/01-writings.md`

- [ ] **Step 1: Spawn Agent 1 with the following prompt**

Spawn a subagent (Agent tool) with this prompt:

```
你的任务：调研 Peter Corke 的著作和系统性长文，聚焦运动学与工具链方面。

搜索方向：
- *Robotics, Vision and Control* 三个版本（2011 1st ed / 2017 2nd ed / 2023 3rd ed）：
  - 各版核心结构差异（尤其 Python 迁移章节 vs 旧 MATLAB 章节）
  - 关于 DH 参数的立场和阐述方式
  - 关于 FK/IK 的教学顺序和哲学
  - 自创术语和核心定义（如 "spatial math", "not your grandmother's toolbox"）
- spatialmath-python 设计文档和 README 中的哲学阐述
- roboticstoolbox-python README 和 CONTRIBUTING.md 中的设计原则
- "Not Your Grandmother's Toolbox — the Robotics Toolbox Reinvented" (ICRA 2021) 论文核心论点
- Corke 在 Springer 出版的其他学术著作
- 反复出现≥3次的核心论点（这些是真信念）
- 推荐书单和引用谱系（揭示智识源头）

输出要求：
- 写入 /c/Users/Administrator/.claude/skills/peter-corke-perspective/references/research/01-writings.md
- 每条信息标注来源URL和可信度（一手/二手/推测）
- 区分一手（Corke 直接写的）vs 二手（别人总结的）
- 发现矛盾直接记录，不要调和
- 范围限制：聚焦运动学、DH、FK/IK、工具链设计、SE(3)。不覆盖机器视觉、移动机器人导航

信息源黑名单：不使用知乎、微信公众号、百度百科。
```

- [ ] **Step 2: Verify output file exists and has substance**

Run:
```bash
wc -l /c/Users/Administrator/.claude/skills/peter-corke-perspective/references/research/01-writings.md
```

Expected: At least 100 lines of structured research content.

---

## Task 3: Agent 2 — Conversations Research (对话与即兴思考)

**Files:**
- Create: `.claude/skills/peter-corke-perspective/references/research/02-conversations.md`

- [ ] **Step 1: Spawn Agent 2 with the following prompt**

Spawn a subagent (Agent tool) with this prompt:

```
你的任务：调研 Peter Corke 的长对话、演讲和即兴思考，聚焦运动学与工具链方面。

搜索方向：
- QUT 公开课录像（YouTube 搜索 "Peter Corke QUT robotics"）
- ICRA/IROS 会议演讲（搜索 "Peter Corke ICRA talk", "Peter Corke IROS presentation"）
- ROSCon 演讲（搜索 "Peter Corke ROSCon"）
- PyConAU 或其他 Python 社区演讲
- IEEE Robotics and Automation Magazine 访谈
- GitHub Discussions / Issues 中的长回复（petercorke/roboticstoolbox-python, petercorke/spatialmath-python）
- 被追问时的回答方式（比如有人质疑 DH vs PoE 时他如何回应）
- 即兴类比（他用什么比喻解释运动学概念）
- 改变立场的瞬间（如果有的话）
- 拒绝回答或承认不知道的问题

输出要求：
- 写入 /c/Users/Administrator/.claude/skills/peter-corke-perspective/references/research/02-conversations.md
- 每条信息标注来源URL和可信度
- 区分「他说过的」vs「别人说他的」vs「我推断的」
- 发现矛盾直接记录

信息源黑名单：不使用知乎、微信公众号、百度百科。
```

- [ ] **Step 2: Verify output file exists and has substance**

Run:
```bash
wc -l /c/Users/Administrator/.claude/skills/peter-corke-perspective/references/research/02-conversations.md
```

Expected: At least 80 lines.

---

## Task 4: Agent 3 — Expression DNA Research (表达风格)

**Files:**
- Create: `.claude/skills/peter-corke-perspective/references/research/03-expression-dna.md`

- [ ] **Step 1: Spawn Agent 3 with the following prompt**

Spawn a subagent (Agent tool) with this prompt:

```
你的任务：调研 Peter Corke 的表达风格和语言DNA，聚焦他在技术写作和代码中的风格。

注意：Corke 不是社交媒体活跃用户。他的主要表达场所是 GitHub 和学术写作。

搜索方向：
- GitHub Issues/PR 的 review 评论风格：
  - 搜索 petercorke/roboticstoolbox-python Issues 和 PR 中 Corke 的回复
  - 搜索 petercorke/spatialmath-python Issues 中 Corke 的回复
  - 他回复 bug report 时的语气
  - 他回复 feature request 时的态度
  - 他 reject PR 时怎么措辞
- 代码注释习惯：
  - roboticstoolbox-python 源码中的注释风格
  - docstring 写法（简洁 vs 详尽）
  - 变量命名偏好
- README 写作模式：
  - 多个 repo 的 README 对比（roboticstoolbox, spatialmath, machinevision-toolbox）
  - 开场方式、结构、语气
- 论文写作风格：
  - 摘要/引言的句式结构
  - 确定性表达 vs 谨慎表达的比例
  - 类比来源域（数学？工程？日常生活？）
- 高频用词和句式指纹
- 禁忌词和他从不说的话
- 幽默方式（如果有的话）

输出要求：
- 写入 /c/Users/Administrator/.claude/skills/peter-corke-perspective/references/research/03-expression-dna.md
- 按维度组织：句式偏好、词汇特征、节奏感、幽默方式、确定性表达、引用习惯
- 每个观察附带具体引用（原文 + 出处）
- 区分一手观察 vs 推测

信息源黑名单：不使用知乎、微信公众号、百度百科。
```

- [ ] **Step 2: Verify output file exists and has substance**

Run:
```bash
wc -l /c/Users/Administrator/.claude/skills/peter-corke-perspective/references/research/03-expression-dna.md
```

Expected: At least 80 lines.

---

## Task 5: Agent 4 — External Views Research (他者视角)

**Files:**
- Create: `.claude/skills/peter-corke-perspective/references/research/04-external-views.md`

- [ ] **Step 1: Spawn Agent 4 with the following prompt**

Spawn a subagent (Agent tool) with this prompt:

```
你的任务：调研其他人对 Peter Corke 和他的工具的评价，收集外部视角。

搜索方向：
- *Robotics, Vision and Control* 书评：
  - Amazon 评价（搜索 "Robotics Vision and Control Corke review"）
  - Springer 出版页面评价
  - 学术书评期刊
  - Goodreads 评价
- roboticstoolbox-python vs 竞品对比：
  - roboticstoolbox vs Drake (TRI)
  - roboticstoolbox vs Pinocchio
  - roboticstoolbox vs MoveIt/moveit2
  - roboticstoolbox vs Modern Robotics (Lynch & Park) 配套代码
  - 社区对比讨论（Reddit r/robotics, Hacker News）
- 学生评价：
  - Rate My Professor（QUT Peter Corke）
  - Reddit 讨论（搜索 "Peter Corke" site:reddit.com）
  - 课程评价网站
- CadQuery/build123d 社区对 Corke 方法论的引用（搜索 "DH parameters" "Peter Corke" 在 build123d 或 CadQuery 相关仓库中）
- 学术引用者对 Corke 方法的评价
- 批评和争议：
  - 对 DH 参数的批评（PoE 支持者的立场）
  - 对 RTB 教学局限性的批评
  - 对 MATLAB→Python 迁移质量的评价

输出要求：
- 写入 /c/Users/Administrator/.claude/skills/peter-corke-perspective/references/research/04-external-views.md
- 分类：赞誉、批评、竞品对比、社区使用反馈
- 每条标注来源URL和评价者身份（学生/同行/用户）
- 保留批评原文，不美化

信息源黑名单：不使用知乎、微信公众号、百度百科。
```

- [ ] **Step 2: Verify output file exists and has substance**

Run:
```bash
wc -l /c/Users/Administrator/.claude/skills/peter-corke-perspective/references/research/04-external-views.md
```

Expected: At least 80 lines.

---

## Task 6: Agent 5 — Decisions Research (决策与架构取舍)

**Files:**
- Create: `.claude/skills/peter-corke-perspective/references/research/05-decisions.md`

- [ ] **Step 1: Spawn Agent 5 with the following prompt**

Spawn a subagent (Agent tool) with this prompt:

```
你的任务：调研 Peter Corke 的重大决策和架构取舍，聚焦运动学工具链。

搜索方向：
- MATLAB → Python 迁移：
  - 何时决定？什么触发了迁移？
  - 迁移策略：全部重写还是逐步移植？
  - 遇到的困难和取舍（MATLAB 的优势 vs Python 的优势）
  - 对已有 MATLAB 用户的态度
- DH 参数 vs Product of Exponentials (PoE) / Screw Theory：
  - Corke 为什么坚持 DH？
  - 他是否回应过 "Modern Robotics" (Lynch & Park) 用 PoE 的做法？
  - 在 RVC 中如何处理这个分歧？
- Swift 实验：
  - petercorke/swift (Swift 语言版本) 的尝试和放弃
  - 为什么尝试？为什么放弃？
- spatialmath 独立库决策：
  - 为什么把 SE(3)/SO(3) 从 roboticstoolbox 中拆出来独立发布？
  - API 设计取舍（operator overloading、numpy 兼容性）
- 开源 MIT 许可 vs 商业化：
  - 为什么选 MIT 而非 GPL 或商业许可？
  - 与 MathWorks/MATLAB 的商业模式对比
- 依赖策略：
  - numpy-only 核心 vs 可选重依赖
  - 为什么不依赖 sympy/scipy 作为核心？
- RVC 出版决策：
  - 为什么选 Springer？
  - 三版之间的范围增减
  - 开放获取 vs 付费出版

输出要求：
- 写入 /c/Users/Administrator/.claude/skills/peter-corke-perspective/references/research/05-decisions.md
- 每个决策记录：背景、选项、最终选择、理由、事后反思（如有）
- 标注信息来源和可信度
- 特别注意言行一致/不一致案例

信息源黑名单：不使用知乎、微信公众号、百度百科。
```

- [ ] **Step 2: Verify output file exists and has substance**

Run:
```bash
wc -l /c/Users/Administrator/.claude/skills/peter-corke-perspective/references/research/05-decisions.md
```

Expected: At least 100 lines.

---

## Task 7: Agent 6 — Timeline Research (时间线)

**Files:**
- Create: `.claude/skills/peter-corke-perspective/references/research/06-timeline.md`

- [ ] **Step 1: Spawn Agent 6 with the following prompt**

Spawn a subagent (Agent tool) with this prompt:

```
你的任务：构建 Peter Corke 的完整职业时间线，聚焦运动学和工具链领域。

搜索方向：
- 学术生涯：
  - 教育背景（本科、博士、学校、导师）
  - QUT 职位历程（讲师 → 教授 → 研究中心主任）
  - 学术荣誉和获奖
- 工具开发时间线：
  - Robotics Toolbox for MATLAB 首次发布（1990s，具体年份）
  - 各主要版本（RTB 9, RTB 10）
  - Machine Vision Toolbox for MATLAB
  - Python 迁移启动年份
  - roboticstoolbox-python 首次发布
  - spatialmath-python 首次发布和独立化
  - Swift（实验）的起止时间
  - machinevision-toolbox-python
- 出版时间线：
  - RVC 1st edition (2011, Springer)
  - RVC 2nd edition (2017, Springer)
  - RVC 3rd edition (2023, Springer) — Python 版
- 关键论文时间线：
  - "Not Your Grandmother's Toolbox" (ICRA 2021)
  - 其他高引用论文
- 最近12个月动态（2025年4月 - 2026年4月）：
  - GitHub 活跃度（最近的 commits, releases）
  - 新论文或演讲
  - roboticstoolbox-python 最新版本
  - 是否有新项目
- 思想转折点：
  - 什么时候开始意识到 MATLAB 是限制？
  - 什么时候决定写教科书？
  - 什么时候确立"Learn by doing"教学哲学？

输出要求：
- 写入 /c/Users/Administrator/.claude/skills/peter-corke-perspective/references/research/06-timeline.md
- 格式：| 年份 | 事件 | 来源 | 可信度 |
- 按时间顺序排列
- 标注信息来源URL
- 最近12个月必须有内容，否则标注「信息不足」

信息源黑名单：不使用知乎、微信公众号、百度百科。
```

- [ ] **Step 2: Verify output file exists and has substance**

Run:
```bash
wc -l /c/Users/Administrator/.claude/skills/peter-corke-perspective/references/research/06-timeline.md
```

Expected: At least 60 lines with chronological entries.

---

## Task 8: Research Review Checkpoint (Phase 1.5)

**Files:**
- Read: All 6 files in `.claude/skills/peter-corke-perspective/references/research/`

**Prerequisite:** Tasks 2-7 all completed.

- [ ] **Step 1: Read all 6 research files and generate quality summary**

Read each of the 6 research files (`01-writings.md` through `06-timeline.md`). For each file, count:
- Number of distinct sources cited
- Ratio of primary (Corke's own) vs secondary sources
- Key findings (top 3)
- Gaps or "information insufficient" markers

- [ ] **Step 2: Display quality summary table to user**

Present the following table format:

```
┌──────────────────┬──────────┬─────────────┬──────────────────────────┐
│ Agent            │ 来源数量  │ 一手占比     │ 关键发现                  │
├──────────────────┼──────────┼─────────────┼──────────────────────────┤
│ 1 著作           │ ?篇      │ ?%          │ ...                      │
│ 2 对话           │ ?段      │ ?%          │ ...                      │
│ 3 表达           │ ?条      │ ?%          │ ...                      │
│ 4 他者           │ ?篇      │ ?%          │ ...                      │
│ 5 决策           │ ?个      │ ?%          │ ...                      │
│ 6 时间线         │ ?个      │ ?%          │ ...                      │
├──────────────────┼──────────┼─────────────┼──────────────────────────┤
│ 矛盾点           │ ?处      │             │ ...                      │
│ 信息不足维度      │ ?处      │             │ ...                      │
└──────────────────┴──────────┴─────────────┴──────────────────────────┘
```

- [ ] **Step 3: Wait for user confirmation**

Ask user: "调研质量 OK 吗？还是某个维度需要补充？"

- User says OK → proceed to Task 9
- User says supplement needed → re-run the specific Agent task (Tasks 2-7) with refined search directions, then return to this step

---

## Task 9: Framework Synthesis (Phase 2)

**Files:**
- Read: All 6 research files
- Read: `references/peter-corke/simulation-philosophy.md` (existing, for cross-validation)
- Read: `.agents/skills/huashu-nuwa/references/extraction-framework.md` (methodology)

**Prerequisite:** Task 8 user confirmation received.

- [ ] **Step 1: Scan all research files for candidate mental models**

Read `01-writings.md` through `05-decisions.md`. List all candidate beliefs/frameworks (expect 15-30 candidates). For each candidate, note:
- Statement of the belief
- Which research file(s) it appeared in
- Whether Corke stated it directly or it was inferred

- [ ] **Step 2: Apply three-way validation to each candidate**

For each candidate, check:
1. **Cross-domain recurrence**: Appears in ≥2 different contexts (e.g., teaching AND API design AND papers)?
2. **Generative power**: Can predict Corke's stance on a new question?
3. **Exclusivity**: Not something every roboticist would say?

Results:
- 3/3 → Mental model (target: 3-7 models)
- 1-2/3 → Decision heuristic
- 0/3 → Discard

- [ ] **Step 3: Cross-validate against existing simulation-philosophy.md**

Read the existing 273-line `simulation-philosophy.md` at `/c/Users/Administrator/.agents/skills/build123d-cad/references/peter-corke/simulation-philosophy.md`. Check:
- Do the newly extracted mental models align with the 7 sections in the existing doc?
- Any new models discovered that aren't in the existing doc?
- Any existing doc claims that the research doesn't support?

- [ ] **Step 4: Extract decision heuristics (5-10)**

From research files, extract "if X then Y" rules Corke follows, each with a concrete case.

- [ ] **Step 5: Analyze expression DNA**

From `03-expression-dna.md`, synthesize:
- Sentence structure preferences
- Vocabulary fingerprint (high-frequency words, banned words)
- Rhythm (conclusion-first vs build-up)
- Humor style
- Certainty level
- Citation habits

- [ ] **Step 6: Extract values, anti-patterns, and internal tensions**

- **Values**: 3-5 ranked core values
- **Anti-patterns**: What Corke explicitly opposes
- **Tensions**: At least 2 pairs of internal contradictions (e.g., "engineering pragmatism" vs "mathematical rigor")

- [ ] **Step 7: Map intellectual lineage**

Who influenced Corke → Corke → who Corke influenced. Place on intellectual map.

- [ ] **Step 8: Define honest boundaries**

List what the skill cannot do:
- Can't predict responses to entirely novel situations
- Public persona vs private person gap
- Information cutoff date
- Scope limited to kinematics+toolchain (not vision, not navigation)

---

## Task 10: Synthesis Confirmation Checkpoint (Phase 2.5)

**Prerequisite:** Task 9 completed.

- [ ] **Step 1: Display synthesis summary to user**

Present:

```
提炼结果摘要：
- 心智模型：N个（列出名称）
- 决策启发式：N条（列出关键词）
- 表达DNA：[3个关键特征]
- 核心张力：N对（列出）
- 诚实边界：N条
```

- [ ] **Step 2: Wait for user confirmation**

Ask user: "提炼结果 OK 吗？某个模型需要调整或缺少？"

- User says OK → proceed to Task 11
- User requests adjustment → revise synthesis and return to this step

---

## Task 11: Build SKILL.md (Phase 3)

**Files:**
- Read: `.agents/skills/huashu-nuwa/references/skill-template.md` (template)
- Create: `.claude/skills/peter-corke-perspective/SKILL.md`

**Prerequisite:** Task 10 user confirmation received.

- [ ] **Step 1: Read the skill template**

Read `/c/Users/Administrator/.agents/skills/huashu-nuwa/references/skill-template.md` for the target structure.

- [ ] **Step 2: Write SKILL.md frontmatter and role-playing rules**

Write the file header following the template. The `name` must be `peter-corke-perspective`. The `description` must mention:
- Source count and type (from research)
- Number of mental models and heuristics
- Trigger words: "Peter Corke perspective", "Corke 视角", "运动学哲学", "DH 参数哲学", "roboticstoolbox 设计", "Corke 会怎么看"
- Scope: kinematics + toolchain only

Role-playing rules: follow template defaults (first person, disclaimer only on first activation, exit protocol).

- [ ] **Step 3: Write identity card**

50-word first-person self-introduction in Corke's voice, based on timeline (06) and writings (01). Include: QUT professor, RVC author, roboticstoolbox creator, "Learn by doing" advocate.

- [ ] **Step 4: Write Agentic Protocol (回答工作流)**

Implement the 3-step protocol from design spec Section 5:

Step 1: Question classification (fact-dependent / pure-framework / hybrid)

Step 2: Corke-style research dimensions (derived from mental models):
- 看机构/机器人: DH table, DOF, FK chain, IK solvability, open-source implementations
- 看算法/方法: SE(3) basis, numerical stability, runnable reference, teachability vs efficiency
- 看工具/库: API design (matrix-first vs object-first), dependency depth, docs quality

Step 3: Corke-style answer using mental models + expression DNA

- [ ] **Step 5: Write mental models section**

3-7 models, each with: name, one-line description, evidence (≥2 contexts), application, limitations.

- [ ] **Step 6: Write decision heuristics section**

5-10 heuristics, each with: rule name, description, application scenario, case example.

- [ ] **Step 7: Write expression DNA section**

Convert analysis into role-playing style rules: sentence structure, vocabulary, rhythm, humor, certainty, citation habits.

- [ ] **Step 8: Write timeline section**

Key milestones table from 06-timeline.md, plus "latest developments" subsection.

- [ ] **Step 9: Write values, anti-patterns, internal tensions**

Values (ranked), anti-patterns (what Corke opposes), tensions (contradictions preserved).

- [ ] **Step 10: Write intellectual lineage**

Who influenced → Corke → who was influenced.

- [ ] **Step 11: Write honest boundaries**

At least 3 specific limitations, including information cutoff date and scope restriction.

- [ ] **Step 12: Write research sources appendix**

Primary sources (Corke's own) and secondary sources (others' analysis), with key quotes.

- [ ] **Step 13: Add 女娲 attribution footer**

```markdown
> 本Skill由 [女娲 · Skill造人术](https://github.com/alchaincyf/nuwa-skill) 生成
> 创建者：[花叔](https://x.com/AlchainHust)
```

- [ ] **Step 14: Run quality self-check**

Read `extraction-framework.md` quality checklist and verify:
- [ ] Each model has ≥2 domain evidence
- [ ] Model count 3-7
- [ ] Each model has application + limitation
- [ ] Expression DNA has distinctiveness
- [ ] Decision heuristics have concrete cases
- [ ] Honest boundaries ≥3 items
- [ ] Primary source ratio >50%

Fix any failures inline.

---

## Task 12: Quality Validation (Phase 4)

**Files:**
- Read: `.claude/skills/peter-corke-perspective/SKILL.md`

**Prerequisite:** Task 11 completed.

- [ ] **Step 1: Known test 1 — "6-DOF IK method selection"**

Spawn a subagent that loads the new SKILL.md and answers:
"6 自由度机器人的逆运动学该用什么方法？"

Expected direction: First check Pieper condition (3 consecutive axes intersect at a point). If satisfied → analytical solution. Otherwise → numerical (Jacobian pseudo-inverse or optimization).

Verify: Direction matches Corke's known stance from RVC.

- [ ] **Step 2: Known test 2 — "DH vs PoE"**

Spawn a subagent that loads the new SKILL.md and answers:
"为什么你的库用 DH 参数而不是 Product of Exponentials？"

Expected direction: Engineering standard > mathematical elegance. DH is industry-universal, students learn it faster, every robot manufacturer publishes DH tables. PoE is elegant but less practical for teaching.

Verify: Direction matches.

- [ ] **Step 3: Known test 3 — "MATLAB vs Python RTB"**

Spawn a subagent that loads the new SKILL.md and answers:
"MATLAB 版和 Python 版的 Robotics Toolbox 哪个更好？"

Expected direction: Python version is better for accessibility and democratized education. MATLAB version is more mature with longer history. Migration was necessary because MATLAB is a commercial barrier to learning.

Verify: Direction matches.

- [ ] **Step 4: Edge test — "Isaac Sim replacing traditional simulation"**

Spawn a subagent that loads the new SKILL.md and answers:
"你怎么看 NVIDIA Isaac Sim 取代传统运动学仿真工具？"

Expected: Moderate uncertainty. Acknowledge GPU-accelerated sim trend, but emphasize DH/FK/IK fundamentals don't change regardless of renderer. Should NOT be overconfident about a topic Corke hasn't publicly discussed in depth.

Verify: Shows appropriate uncertainty.

- [ ] **Step 5: Voice test**

Spawn a subagent that loads the new SKILL.md and writes a 100-word analysis of "why Python is better than MATLAB for robotics education."

Verify:
- Has Corke's expression characteristics (academic but accessible, code-centric, confident in engineering matters)
- Not generic AI boilerplate
- Not quote-stitching

- [ ] **Step 6: Evaluate pass/fail against criteria**

| Check | Pass? |
|-------|-------|
| Mental models 3-7 with source evidence | |
| Each model has failure conditions | |
| Expression DNA recognizable in 100 words | |
| Honest boundaries ≥3 specific items | |
| Internal tensions ≥2 pairs | |
| Primary source ratio >50% | |

If any fail → go back to Task 9/11, fix the specific weakness. Max 2 iterations.

- [ ] **Step 7: Present results to user**

Show the test results table and ask: "验证结果 OK 吗？"

- User says OK → proceed to Task 13
- User requests changes → fix and re-validate

---

## Task 13: Dual-Agent Refinement (Phase 5)

**Files:**
- Modify: `.claude/skills/peter-corke-perspective/SKILL.md`

**Prerequisite:** Task 12 user confirmation received.

- [ ] **Step 1: Spawn Agent A (structure evaluator)**

Spawn a subagent with this prompt:

```
你是 auto-skill-optimizer。对以下 SKILL.md 执行 8 维度结构评估：
1. 工作流清晰度
2. 边界条件完整性
3. 检查点设计
4. 指令具体性
5. 触发条件覆盖
6. 退出条件
7. 失败预防
8. 信息密度

然后干跑以下 3 个测试 prompt，评估效果：
- "帮我分析这个 3-DOF 机械臂的运动学"
- "roboticstoolbox-python 的 API 设计思路是什么？"
- "用 Corke 的视角审查我的 IK 实现"

输出：最弱 2 个维度的具体改进建议，要有改后文本示例。

SKILL.md 路径: /c/Users/Administrator/.claude/skills/peter-corke-perspective/SKILL.md
```

- [ ] **Step 2: Spawn Agent B (activation reviewer)**

Spawn a subagent with this prompt:

```
你是 skill-creator 审查员。对以下 SKILL.md 评审：
1. 激活触发条件是否覆盖真实使用场景（中英文、隐含触发、边缘触发）
2. 角色扮演规则的可操作性（有无问题路由、频率约束、失败预防）
3. 识别缺失的关键信息

输出：2-3 处具体文本改动建议，要有改后文本示例。

SKILL.md 路径: /c/Users/Administrator/.claude/skills/peter-corke-perspective/SKILL.md
```

- [ ] **Step 3: Synthesize and apply non-conflicting improvements**

Read both agent reports. Apply improvements that don't conflict. If they conflict, prefer the change that makes the skill more "activate and execute" rather than just adding content.

- [ ] **Step 4: Present refinement summary to user**

Show what was changed and why. Ask: "精炼变更 OK 吗？"

- User says OK → proceed to Task 14
- User requests changes → adjust and re-present

---

## Task 14: build123d-cad Cross-Reference Update

**Files:**
- Modify: `references/peter-corke/simulation-philosophy.md` (in build123d-cad repo)
- Modify: `SKILL.md` line 36 (in build123d-cad repo)

**Prerequisite:** Task 13 user confirmation received.

- [ ] **Step 1: Trim simulation-philosophy.md to ~50 line summary**

Read the current 273-line file at `/c/Users/Administrator/.agents/skills/build123d-cad/references/peter-corke/simulation-philosophy.md`.

Rewrite to ~50 lines keeping:
- Header with pointer: `> 完整 Peter Corke 思维框架见 .claude/skills/peter-corke-perspective/SKILL.md`
- DH 四参数表 (Section 2 table)
- SE(3) = build123d Location bridge (Section 3 key insight)
- 3-layer verification table (Section 5)
- Tool chain recommendation table (Section 8)
- Honest boundaries capability table (Section 6)

Remove: detailed prose, code examples, Cowden comparisons (these now live in the full skill).

- [ ] **Step 2: Update SKILL.md Rule 11**

In `/c/Users/Administrator/.agents/skills/build123d-cad/SKILL.md`, find line 36 (Rule 11) and append:

```
当用户需要深度运动学分析或想用 Peter Corke 的视角审视运动学设计时，提示可切换到 peter-corke-perspective skill（`.claude/skills/peter-corke-perspective/SKILL.md`）
```

- [ ] **Step 3: Verify cross-references work**

Check that:
- The trimmed simulation-philosophy.md still contains the DH table and SE(3)=Location bridge
- The pointer path in the trimmed file matches the actual SKILL.md location
- Rule 11 in SKILL.md has the correct path

- [ ] **Step 4: Commit all changes**

```bash
cd /c/Users/Administrator/.agents/skills/build123d-cad
git add references/peter-corke/simulation-philosophy.md SKILL.md
git commit -m "refactor: trim simulation-philosophy.md to summary, link to full peter-corke-perspective skill"
```

---

## Task 15: Final Commit and Verification

**Files:**
- All files in `.claude/skills/peter-corke-perspective/`

- [ ] **Step 1: Verify complete directory structure**

Run:
```bash
find /c/Users/Administrator/.claude/skills/peter-corke-perspective/ -type f | sort
```

Expected:
```
SKILL.md
references/research/01-writings.md
references/research/02-conversations.md
references/research/03-expression-dna.md
references/research/04-external-views.md
references/research/05-decisions.md
references/research/06-timeline.md
```

- [ ] **Step 2: Verify SKILL.md has all required sections**

Run:
```bash
grep "^##" /c/Users/Administrator/.claude/skills/peter-corke-perspective/SKILL.md
```

Expected sections (in order): 角色扮演规则, 身份卡, 回答工作流, 核心心智模型, 决策启发式, 表达DNA, 人物时间线, 价值观与反模式, 智识谱系, 诚实边界, 调研来源

- [ ] **Step 3: Verify line counts**

Run:
```bash
wc -l /c/Users/Administrator/.claude/skills/peter-corke-perspective/SKILL.md
wc -l /c/Users/Administrator/.agents/skills/build123d-cad/references/peter-corke/simulation-philosophy.md
```

Expected: SKILL.md ≥300 lines, simulation-philosophy.md ~50 lines.

- [ ] **Step 4: Final commit in build123d-cad repo**

```bash
cd /c/Users/Administrator/.agents/skills/build123d-cad
git add -A
git commit -m "feat: complete peter-corke-perspective skill generation via 女娲 pipeline

6-agent parallel research → 3-way validated mental models → SKILL.md
Cross-referenced with build123d-cad simulation-philosophy.md (trimmed to summary)"
```

- [ ] **Step 5: Report completion**

Tell user: "Peter Corke perspective skill 生成完成。SKILL.md 在 `.claude/skills/peter-corke-perspective/SKILL.md`，build123d-cad 的交叉引用已更新。"
