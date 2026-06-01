# 单部件流程 Playbook（Single-Part Protocol）

> **何时进入此 Playbook**：用户需求是 1 个独立实体，无装配关系。
> 入口由 `SKILL.md` 的"流程路由"表触发。

---

## 执行契约（进入此 Playbook 后对本次对话强制生效）

1. 每个 Step 完成后，**必须在当次回复里输出"产出报告"块**。
2. 产出报告里每一条必须是 `[x]`（已产出）或 `[skip] reason=...`（显式跳过）。
3. **没写产出报告的 Step 视为未完成**，禁止进入下一步。
4. **跳步必须声明理由**，静默跳过视为违规。
5. **Artifact 是硬约束**——用户接管某步也不例外。
6. 遇本步 artifact 缺失：回到本步补产，禁止写 `[x]` 骗过。
7. **每个 Step 产出报告第一行必须是 Quote-back**。
   格式：引自 single-part-playbook.md §Step S<n> / <小标题>："<原文一行>"
   缺 Quote-back、引错 Step、原文捏造 = 违规，必须回补。
8. **每个确认门必须遵守 SKILL.md §确认门执行契约**（halt 前三项自检 + `[halt-for-user]` 硬字段 + 同轮不得推进）；违规 = FM-1。

---

## S1~S4 Step 总表

| Step | 必须产出 | 允许跳过？ | 下一步分叉 |
|---|---|---|---|
| S1 需求分析 | 需求分析表 + 参考问询 | 否 | → S1.5 |
| S1.5 标准件候选清单 | `parts_candidates.md` + `standard_parts_resolved.md` + 确认门 ✋ | 纯造型件 `[skip]` | → S2 |
| S2 几何对齐（默认含 3 视图草图） | concept_sketch.png（自动打开）或用户 skip 声明 | 用户明说"跳过草图" | → S2.5 |
| S2.5 代码库巡查 | `code_borrowings.md` + 确认门 ✋ | cheatsheet 已覆盖时 `[skip]` | → S3 |
| S3 建模实现 | `<part>.py` + OCP 自动预览 + 3 变体对比（若用户启用变体） | 否 | → S4 |
| S4 导出 + 工艺提示 | `<part>.step`/`.stl` + 工艺约束清单 | 否 | （终态） |

---

## Step S1 — 需求分析

**前置**：
- [x] 用户需求进入，SKILL.md 路由判定为单部件

**本步产出**：
- 需求分析表（4 要素：几何 / 关键尺寸 / 操作序列 / 导出格式 / 用途）
- 参考资料问询（"是否有参考图、参考链接或参考描述？"）
- 形态评估结论（命中的形态主观词列举 + S2 路径判定：走方案 F / 走方案 A）

**命令模板**：

收到需求后识别：

| 要素 | 问题 | 示例 |
|------|------|------|
| **几何形状** | 基本形状是什么？ | 圆柱、长方体、旋转体 |
| **关键尺寸** | 哪些已给出？哪些缺失？ | 长×宽×高，孔径，壁厚 |
| **操作序列** | 机械师会按什么顺序加工？ | 先车外圆 → 再打孔 → 再切键槽 |
| **导出格式** | STEP / STL / BREP？ | 默认 STEP |
| **用途** | 3D打印？CNC？激光切割？ | 影响公差和格式选择 |

**缺失关键尺寸时**：先询问，不要自行假设关键参数（如螺纹规格、配合尺寸）。
非关键尺寸（如圆角半径）可给合理默认值并标注。

**需求分析结束前必须询问**：

```
在开始建模之前，请问你是否有参考图、参考链接或参考描述？
（有的话发给我，我会根据参考来建模并标注符合度）
```

**形态评估**（决定 S2 分支：方案 F vs 方案 A）

检测需求文本是否含形态主观词（完整词表见 SKILL.md §方案 F：AIGC 概念图 → 参数化设计图 / 触发词）：

- 视觉风格类：科技感、极简、工业风、复古、仿 XX 风格、高级感
- 形态特征类：流畅、仿生、异形、流线型、有机、雕塑感、灵动、柔和曲面
- 产品门类类：潮玩、角品、ID 产品、手办、艺术摆件、概念设计

**任一词命中** → S2 走方案 F（AIGC 生成概念图 → Gate F1 选图 → 视觉解读 → 3 视图 + 参数合同表 → Gate F2 确认 → 建模）
**未命中** → S2 走方案 A（AI 自画 3 视图 ASCII，沿原流程）

**引 SKILL.md §方案 F / 触发词**：任一主观词命中 → 走方案 F；未命中走方案 A。

**AI 回报契约**：

```
Step S1 产出报告
引自 single-part-playbook.md §Step S1 / 本步产出：
  "需求分析表（4 要素：几何 / 关键尺寸 / 操作序列 / 导出格式 / 用途）"
- [x] 需求分析表已输出（见上方）
- [x] 已询问参考资料
- [x] 形态评估结论：<命中词列举 或"未命中">，S2 走 <方案 F / 方案 A>
下一步：Step S1.5（标准件候选推断，等用户回复参考资料后触发）
```

---

## Step S1.5 — 标准件候选清单（Standard-Parts Inference）

> **目的**：用户说"做一个 XXX"时，AI **先推断**需求里隐含的标准件（螺丝/轴承/舵机/热压铜螺母/弹簧/垫片等），列出候选清单让用户**确认/调整**，再批量查 `data-sources/`。
> 解决 S1「用户表达」与 data-sources「型号参数」之间的意图断层。

**前置**：
- [x] S1 需求分析完成
- [x] 用户已回复参考资料（或明确说"无"）

**本步产出**：
- `tests/<test>/parts_candidates.md`（候选清单表格）
- `tests/<test>/standard_parts_resolved.md`（批量 `spec_lookup` 结果 + 未命中的 websearch_prompts）
- `[halt-for-user]` 硬字段通过

**命令模板**：

```bash
SKILL=/Users/liyijiang/.agents/skills/build123d-cad
TEST=tests/<test-dir>
mkdir -p $TEST
```

**推断 + 写候选清单**（AI 依据 S1 的需求分析结果推断）：

````markdown
## 标准件候选清单

| # | 候选型号 | 数量 | 置信度 | 用途 | data-sources 状态 |
|---|---------|-----|-------|------|------------------|
| 1 | SG90    | 2   | ●●●   | 左右腿髋关节驱动 | ✓ servos.yaml:SG90 |
| 2 | M2 ISO 4762 | 8 | ●●●● | 舵机耳朵螺丝（每台 SG90 需 4 枚）| ✓ fasteners.yaml:M2_ISO4762 |
| 3 | 608ZZ   | 2   | ●●○   | 膝关节旋转支撑 | ✓ bearings.yaml:608ZZ |
| 4 | 3D 打印结构件 | - | - | 骨架（本次建模主体，无标准件参数）| — |

> 置信度：●●●●●=需求明确指定，●●●●=通用方案强推荐，●●●=合理推断，●●○=备选，●○○=冷门可能
````

**halt 交互**：

```
[halt-for-user] ✋ 请确认标准件清单：
  回 "OK" / "删 #3" / "改 #2 数量=6" / "加 M3×2 电池仓盖" / "换 #1 为 MG996R"
```

> 发 `[halt-for-user]` 前必过 SKILL.md §确认门执行契约 的三项自检。

**用户确认后的批量 lookup**：

```bash
SKILL=/Users/liyijiang/.agents/skills/build123d-cad
TEST=tests/<test-dir>
{
  echo "# 标准件参数解析 (standard_parts_resolved)"
  echo ""
  for p in SG90 M2 608ZZ; do   # 用户确认后的最终清单
    echo "## === $p ==="
    python3 $SKILL/scripts/research/spec_lookup.py "$p"
    echo ""
  done
} > $TEST/standard_parts_resolved.md
```

**未命中分叉**：
- 若 `standard_parts_resolved.md` 中出现 `[spec-miss]` → 在文件末尾追加 `## 待 WebSearch` 节，把脚本回落的 `websearch_prompts` 列出来
- 下一 Step（S2 或 S3）开始前 AI 应执行这些 WebSearch 补齐参数

**纯造型件跳过语法**：

```markdown
## 标准件候选清单
[skip] reason=纯造型件（花瓶/雕塑/手办/潮玩等），无标准件需求
```

skip 后直接过 halt 进 S2，**无 lookup**，**无 WebSearch**。

**AI 回报契约**（完成后必须在回复里输出）：

```
Step S1.5 产出报告
引自 single-part-playbook.md §Step S1.5 / 本步产出：
  "tests/<test>/parts_candidates.md（候选清单表格）"
- [x] tests/<test>/parts_candidates.md               (3 候选，全部 data-sources 命中)
- [x] tests/<test>/standard_parts_resolved.md       (SG90+M2+608ZZ lookup 结果)
- [halt-for-user] ✋ 请确认标准件清单，回 "OK" / 修订指令
下一步：等用户确认 → Step S2
```

（纯造型件场景示例：）
```
Step S1.5 产出报告
- [skip] parts_candidates.md reason=纯造型件（八角花瓶），无标准件需求
- [skip] standard_parts_resolved.md reason=同上
下一步：直接进 Step S2
```

**halt 通过 → 更新 parts_candidates.md**：
- 用户回 "OK" → 原表格保持，标注 `## 确认状态：已通过`
- 用户修订 → AI 修改对应行后重出回报 + 重发 halt（同轮不得推进，见 SKILL.md §确认门执行契约）

---

## Step S2 — 几何对齐（默认含 3 视图草图，方案 A 默认触发）

**前置**：
- [x] S1.5 标准件候选已确认（含 `[skip] 纯造型件` 通过）

**本步产出**：
- `concept_sketch.png`（自动保存并打开），或 `[skip] reason=用户说"跳过草图"`

**命令模板**：

> **核心目的**：在建 3D 模型之前，确认 AI 理解的形状和用户脑子里的形状是同一个东西。
> **原则**：**方案 A（3视图草图）默认自动执行**，无需用户开口。用户说「跳过草图」/「直接建模」才跳过。其余4种方案（B/C/D/E）仍需用户主动触发。

### 方案 A：3视图草图（默认自动执行）

**默认触发**：收到任何建模需求后，在建模策略之前自动生成。
**跳过触发词**：「跳过草图」「不需要草图」「直接建模」「skip sketch」

用 Matplotlib 生成正视图 / 侧视图 / 俯视图 PNG，保存后**自动打开**让用户直接看到：

````python
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import subprocess, sys, os

fig, axes = plt.subplots(1, 3, figsize=(14, 5))
fig.suptitle("Concept Sketch / 概念草图", fontsize=13, fontweight='bold')

for ax, title in zip(axes, ["Front View / 正视图", "Side View / 侧视图", "Top View / 俯视图"]):
    ax.set_title(title, fontsize=10)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.axhline(0, color='lightgray', linewidth=0.8, linestyle='--')
    ax.axvline(0, color='lightgray', linewidth=0.8, linestyle='--')
    ax.set_xlabel('mm')
    ax.set_ylabel('mm')

# ── 根据部件形状在对应 ax 绘制轮廓 + 尺寸标注 ──
# 正视图：主轮廓 + 总长×总高尺寸线 / Front: main outline + overall dimensions
axes[0].add_patch(patches.Rectangle((-20, -25), 40, 50,
                  fill=False, edgecolor='black', linewidth=1.5))
axes[0].annotate('', xy=(22, -25), xytext=(22, 25),
                 arrowprops=dict(arrowstyle='<->', color='red', lw=1.2))
axes[0].text(25, 0, '50mm', color='red', fontsize=8, va='center')
axes[0].annotate('', xy=(-20, -28), xytext=(20, -28),
                 arrowprops=dict(arrowstyle='<->', color='blue', lw=1.2))
axes[0].text(0, -32, '40mm', color='blue', fontsize=8, ha='center')

# 侧视图：壁厚 / Side: wall thickness
# 俯视图：孔位 / Top: hole pattern
# （根据实际部件几何填充各视图内容）

plt.tight_layout()

# ===== 保存 + 自动打开 =====
sketch_path = os.path.join(output_dir, "concept_sketch.png")
plt.savefig(sketch_path, dpi=130, bbox_inches='tight')
plt.close()

# 自动用系统查看器打开（macOS: open, Windows: start, Linux: xdg-open）
if sys.platform == "darwin":
    subprocess.Popen(["open", sketch_path])
elif sys.platform == "win32":
    os.startfile(sketch_path)
else:
    subprocess.Popen(["xdg-open", sketch_path])

print(f"概念草图已生成并打开 / Concept sketch opened: {sketch_path}")
````

AI **同时输出文字说明**，标注每个视图的几何意图：

```
## 概念草图说明

正视图：主轮廓 + 中心线，总长×总高，关键台阶位置
侧视图：截面形状，壁厚/圆角/槽深
俯视图：孔位分布，PCD/间距/阵列

图已自动打开，请确认形状是否符合预期？
[ ✅ 确认，进入建模 ] 或 [ ❌ 第N视图不对：___ ]
```

> 发 [halt-for-user] 前必过 SKILL.md §确认门执行契约 的三项自检。

**确认门 ✋** 用户确认草图正确后，才进入建模策略。

```
[halt-for-user] ✋ 确认 3 视图草图形状符合预期，回 "OK" 进建模 / 或指出哪视图需修改
```

### 方案 B：OCP 快速原型（Bounding Box Proxy）

**触发词**：「先看比例」「先预览比例」「占位块」「proxy」「先看看大概」
用 `Box` / `Cylinder` 代替真实部件，在 OCP 中展示3D比例和装配位置。
**最适合**：多部件装配，先对齐整体比例再逐部件精建。

### 方案 C：关键截面草图（Profile Sketch）

**触发词**：「画截面」「截面轮廓」「旋转轮廓」「profile」「扫掠截面」「revolve截面」
专为 **Revolve / Sweep** 零件——用 Matplotlib 画2D截面轮廓，用户确认截面后再建实体。
**最适合**：阶梯轴、弯管、有机外壳等旋转体和扫掠件。

### 方案 D：参考图标注

**触发词**：「解读一下图」「标注图」「图里xxx是什么」「你怎么理解这张图的」「有参考图」
用户提供参考图时，AI 用纯文字标注自己对图的解读，让用户纠错。
**最适合**：用户有参考图、AI 可能看错局部细节时，零代码开销。

### 方案 E：参数约束表

**触发词**：「先确认参数」「列出参数」「参数合同」「先列尺寸」「把参数给我看看」
建模前列出所有关键参数，用户逐行确认，形成「参数合同」。
**最适合**：有精度要求的配合件、尺寸需要精确匹配时。

### 5种方案选择速查

| 方案 | 对齐的是什么 | 生成开销 | 最适合场景 |
|------|------------|---------|-----------|
| A 3视图草图 | 整体形状 | 中（Matplotlib） | 复杂单体，无参考图 |
| B OCP快速原型 | 3D比例+装配位置 | 快（build123d） | 多部件装配 |
| C 关键截面草图 | 截面轮廓 | 中（Matplotlib） | Revolve / Sweep 件 |
| D 参考图标注 | AI对图的理解 | 极快（纯文字） | 有参考图时 |
| E 参数约束表 | 关键尺寸数值 | 极快（表格） | 精度配合件 |

> **可组合**：多部件设计推荐 B（整体比例）+ D（参考图理解）+ E（参数锁定）三连。

**AI 回报契约**：

```
Step S2 产出报告
引自 single-part-playbook.md §Step S2 / 本步产出：
  "concept_sketch.png（自动保存并打开）"
- [x] concept_sketch.png  (已自动打开查看)
下一步：Step S3
```

**跳过声明**：若用户说"跳过草图"/"直接建模"：

```
Step S2 产出报告
引自 single-part-playbook.md §Step S2 / 本步产出：
  "concept_sketch.png（自动保存并打开）"
- [skip] concept_sketch.png  (reason: 用户说"跳过草图")
下一步：Step S3
```

---

## Step S2.5 — 代码库巡查（Code Sources Lookup）

> **目的**：建模前先翻社区代码，避免"闭门造车写呆板代码"。GitHub 上有成熟实现就借鉴，组合设计才留创意。
> 解决"AI 凭训练数据写过时代码 / 重复造轮子"的问题。

**前置**：
- [x] S2 几何对齐完成（草图或 skip 声明）

**本步产出**：
- `tests/<test>/code_borrowings.md`（借鉴候选表 + 用户确认后的最终借鉴清单）
- `[halt-for-user]` 硬字段通过

**命令模板**：

```bash
SKILL=/Users/liyijiang/.agents/skills/build123d-cad
TEST=tests/<test-dir>

# 1) AI 根据 S1 需求分析，识别本次涉及的领域关键词（最多 2 个）
#    示例：渐开线齿轮 → gears；流线型外壳 → surfaces + enclosures

# 2) 查领域：
python3 $SKILL/scripts/research/code_lookup.py gears
# 若 cache 命中 → 复用上次摘要
# 若 cache miss → 脚本输出 repos + websearch_prompts，AI 执行 WebSearch

# 3) AI 把脚本 + WebSearch 结果汇总为"借鉴候选表"，写入 code_borrowings.md
```

**候选清单格式**：

````markdown
## 借鉴候选（S2.5）

| # | 来源 | 核心技巧 | 翻译成本 | License | 推荐度 |
|---|------|---------|---------|---------|-------|
| 1 | gumyr/bd_warehouse@<commit> src/bd_warehouse/gear.py#L45-89 | InvoluteGear 一键调用 | 零 | Apache-2.0 ✓ | ●●● |
| 2 | CadQuery/cadquery-contrib@<commit> examples/gears.py#L20-60 | 变位齿轮手写齿廓 | 低 | MIT ✓ | ●●○ |
| 3 | blog.example.com/xxx | 渐开线数学推导 | 中 | 未标 ✗ | ●○○ 仅理论参考，不抄代码 |

推荐度：●●●=首选、●●○=备选、●○○=理论参考（不借代码）
````

**halt 交互**：

```
[halt-for-user] ✋ 是否借鉴？
  回 "借 #1" / "借 #1+#2" / "跳过（自写）" / "全跳"
```

> 发 `[halt-for-user]` 前必过 SKILL.md §确认门执行契约 的三项自检。

**用户确认后，S3 建模时明确引用**：

```python
# 参考：gumyr/bd_warehouse@a1b2c3d src/bd_warehouse/gear.py#L45-89 (Apache-2.0)
from bd_warehouse.gear import InvoluteGear
```

**skip 语法**（简单零件、cheatsheet 已覆盖）：

```markdown
## 借鉴候选（S2.5）
[skip] reason=cheatsheet + patterns 已完全覆盖（Box + Hole + fillet，无冷门操作）
```

**cache 未命中时的 fallback**：若 WebSearch 无结果 → AI 明写"本次无社区参考，走原创" → 不阻塞流程。

**License 纪律**（`catalog.yaml license_policy`）：
- 🟢 MIT / BSD / Apache-2.0 / Unlicense / CC0 → 注明来源即可借鉴
- 🟡 GPL / AGPL / LGPL → 默认禁用（传染性），除非本项目本就 GPL
- 🔴 未标 License / 商业 → 禁止借鉴

**AI 回报契约**：

```
Step S2.5 产出报告
引自 single-part-playbook.md §Step S2.5 / 本步产出：
  "tests/<test>/code_borrowings.md（借鉴候选表 + 用户确认后的最终借鉴清单）"
- [x] tests/<test>/code_borrowings.md          (3 候选，用户选 #1)
- [spec-hit] cache=gears-default (7 天内复用，age=3d)
- [halt-pass] 用户回 "借 #1"
下一步：Step S3（建模实现，代码里显式引用 bd_warehouse@a1b2c3d）
```

（skip 场景示例：）
```
Step S2.5 产出报告
- [skip] code_borrowings.md reason=cheatsheet + patterns 已覆盖（Box + Hole）
下一步：Step S3（直接建模）
```

---

## Step S3 — 建模实现

**前置**：
- [x] S2.5 代码库巡查完成（借鉴清单 / skip 声明）

**本步产出**：
- `<part>.py`（含 OCP 自动预览块）
- OCP Viewer 实际打开
- 3 变体对比（若用户启用变体讨论）

**命令模板**：

### 选择建模策略

| 情况 | 策略 |
|------|------|
| 简单零件（<5特征） | 直接 Builder Mode |
| 旋转体 | `revolve()` + `BuildSketch(Plane.XZ)` |
| 管道/异形 | `sweep()` + `BuildLine()` 路径 |
| 薄壁件 | `offset(amount=-t, openings=face)` 抽壳 |
| 阵列特征 | `GridLocations` / `PolarLocations` |
| 快速组合 | Algebra Mode（`+`, `-`, `&`） |
| **有机曲面/流线型** | **Loft 多截面放样 + Sweep 扭转**（见 `../references/parts/surface-modeling.md`） |
| **复杂轮廓（齿轮/凸轮）** | **根实体 + 逐特征 Algebra Mode 融合** |

完整代码模板见 `../references/parts/patterns.md`，可运行示例见 `assets/` 目录。

### 生成3个变体 + OCP 并排对比

> **无论单部件还是多部件，建模时必须生成3个变体，OCP 并排展示，用户选定后才导出最终 STEP。**

````python
from build123d import *
from ocp_vscode import show, set_port, Camera
from ocp_vscode.comms import port_check
from ocp_vscode.state import get_ports

# ===== 参数（3个变体共用基础参数，各自差异化一个维度）=====
# V1 保守：尺寸偏小/偏薄，适合轻量化 / conservative: smaller/thinner
# V2 参考：最贴合参考图，标准工艺（推荐）/ reference: closest to spec (recommended)
# V3 加强：关键截面加宽/加厚，承载优先 / reinforced: wider/thicker key sections

def make_v1(): ...   # 保守方案
def make_v2(): ...   # 参考方案（推荐）
def make_v3(): ...   # 加强方案

v1 = make_v1()
v2 = make_v2()
v3 = make_v3()

# 并排偏移：X方向间隔 1.5× 部件最大宽度 / side-by-side offset
offset = max(v1.bounding_box().size.X,
             v2.bounding_box().size.X,
             v3.bounding_box().size.X) * 1.5
v2 = v2.move(Location((offset, 0, 0)))
v3 = v3.move(Location((offset * 2, 0, 0)))

# ===== OCP 并排预览 =====
try:
    active_port = next((int(p) for p in get_ports() if port_check(int(p))), None)
    if active_port:
        set_port(active_port)
        show(v1, v2, v3,
             names=["V1_conservative", "V2_reference", "V3_reinforced"],
             colors=["steelblue", "orange", "green"],
             reset_camera=Camera.ISO)
        print("OCP Viewer: 3变体并排展示 ✓")
    else:
        print("OCP Viewer: 未检测到 Viewer，请启动 OCP CAD Viewer 扩展")
except Exception as e:
    print(f"OCP 预览跳过: {e}")
````

### AI 比对分析（必须输出，参考图优先）

```
## 变体对比分析

| 变体 | 对应参考图位置       | 尺寸符合度 | 建模特点         | 推荐工艺 |
|------|---------------------|-----------|------------------|---------|
| V1   | 图中xxx区域，偏细    | ~85%      | 轻量，腰部偏细   | 3D打印  |
| V2   | 图中xxx区域，最接近  | ~97%      | 标准CNC铝板截面  | CNC     |
| V3   | 图中xxx区域，偏厚    | ~80%      | 端部加宽，略重   | CNC     |

推荐：V2（最贴合参考图，符合工艺约束）

（无参考图时：V2 为行业标准尺寸，V1/V3 为轻量化/加强化方向）
```

### 自动断言（三项全过才可选）

````python
for name, part in [("V1", v1_original), ("V2", v2_original), ("V3", v3_original)]:
    ok = []
    ok.append("✅ BRep有效" if part.is_valid else "❌ BRep无效")
    vol = part.volume
    ok.append("✅ 体积合理" if lower < vol < upper else f"❌ 体积超范围({vol:.0f})")
    export_step(part, f"/tmp/{name}.step")
    ri = import_step(f"/tmp/{name}.step")
    diff = abs(ri.volume - vol) / vol
    ok.append("✅ STEP精度" if diff < 0.001 else f"❌ STEP精度损失({diff:.3%})")
    print(f"{name}: {' '.join(ok)}")
````

### 确认门

> 发 [halt-for-user] 前必过 SKILL.md §确认门执行契约 的三项自检。

```
请选择变体：[ V1 ] [ V2（推荐）] [ V3 ]
或告诉我调整参数，我重新生成。

[halt-for-user] ✋ 选定变体编号（V1/V2/V3），或给调整参数
```

**AI 回报契约**：

```
Step S3 产出报告
引自 single-part-playbook.md §Step S3 / 本步产出：
  "<part>.py（含 OCP 自动预览块）"
- [x] <part>.py
- [x] OCP Viewer 预览已打开
下一步：Step S4
```

---

## Step S4 — 导出 + 工艺提示

**前置**：
- [x] S3 建模完成且 OCP 预览通过

**本步产出**：
- `<part>.step` 或 `<part>.stl`（按用途选格式）
- 工艺约束清单（3D 打印 / CNC / 激光，按用户场景挑一个）

**命令模板**：

用户选定变体后：

1. 导出选定变体的 STEP 文件存档
2. 输出：操作序列说明（3-5行）+ 调参指引
3. 告知用户「已选 Vn，STEP 已导出，OCP 中显示的即为最终版本」

**AI 回报契约**：

```
Step S4 产出报告
引自 single-part-playbook.md §Step S4 / 本步产出：
  "<part>.step 或 <part>.stl + 工艺约束清单"
- [x] <part>.step
- [x] 工艺约束清单（3D 打印：壁厚 1.2mm 最小 / 悬臂 ≤45°）
单部件流程 S1~S4 完成。
```

---

## 常见失败模式

跨 Playbook 通用的 Quote-back 违规见 `protocols/README.md`。以下为单部件流程专属：

### FM-1：越权通过确认门

**诊断**：single-part-playbook §Step S2（草图确认）或 §Step S3/S4（变体选定）的确认门要求 `[halt-for-user]`，AI 同一轮回复里发了 halt 又继续推进（给最终建模代码 / 写导出代码 / 直接进下一 Step）。典型诱因：用户说"直接给代码""不要太啰嗦"导致 AI 跳过 S2 草图 halt。

**修复**：删除 halt 之后的所有推进内容；保留 halt，重出该轮回报；等用户下一轮真实回执（OK / 修改 / 提问）才决定如何进下一 Step。
