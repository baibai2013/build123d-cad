# 参考物建模协议 Playbook（Reference-Product Playbook）

> **何时进入此 Playbook**：用户需求中出现已存在的具体产品型号（手机/开发板/舵机/传感器…）。
> 入口由 `SKILL.md` 的"参考物建模流程"路由段触发。

---

## 执行契约（进入此 Playbook 后对本次对话强制生效）

1. 每个 Step 完成后，**必须在当次回复里输出"产出报告"块**——列出本步 artifact 的 `[x]`（已产出）或 `[skip] reason=...`（显式跳过）。
2. **没写产出报告的 Step 视为未完成**，禁止进入下一步。
3. **跳步必须声明理由**，格式 `[skip] <step-id> reason=<具体理由>`。静默略过视为违规。
4. **Artifact 是硬约束**——用户接管某步也不例外（例如用户直接给 contract，AI 仍必须把内容落盘到约定路径）。
5. 遇到本步 artifact 缺失：回到本步补产，禁止写 `[x]` 骗过。发现上游缺失：在回复里明写 "回补 Step Rx" 并执行，禁止下行。
6. **R1 开始前必须查 `experience/`，R5 结束前必须输出 Experience Draft**（状态用 `[hit]`/`[partial]`/`[miss]`/`[skip]`/`[saved]`，详见 R1 / R5 Step 定义）。
7. **每个 Step 产出报告第一行必须是 Quote-back**。
   格式：引自 reference-product-playbook.md §Step R<n> / <小标题>："<原文一行>"
   缺 Quote-back、引错 Step、原文与文件不符 = 违规，必须回补 Read + 重出报告。

---

## R1~R5 Step 总表

| Step | 必须产出 | 允许跳过？ | 经验交互 | 下一步分叉 |
|---|---|---|---|---|
| R1 识别 + 搜索计划 | `references/<slug>/search_plan.md` | 否 | **读** `experience/`（`[hit]`/`[partial]`/`[miss]` 必报） | → R2 |
| R2 执行搜集 | `references/<slug>/raw_specs.md` + `images/*` | 否 | — | 有 `model.step` → R3/R2.7；无 → R2.5 |
| R2.5 无 STEP 反推 | `references/<slug>/clean/*_scale.json` + `measurements.csv` | 仅 R2 已产出 `model.step` 时可 skip | — | → R2.7 |
| R2.7 参考图现实对齐 | `references/<slug>/clean/*_cropped.png` + `part_face_mapping.yaml` | 否（Layer 2 必做）；仅 "有 STEP + 不做视觉对比" 可 skip | — | → R3 |
| R3 生成 params.md | `references/<slug>/params.md`（含 ★ 置信度） | 否 | 参考命中经验的参数星级，可上调本次置信度 | → R3.5 |
| R3.5 生成 contract.yaml | `tests/<test>/contract.yaml` | 否 | — | → R4 |
| R4 建模 | `tests/<test>/<part>.py` + OCP 自动预览 | 否 | 若命中经验有"复用片段"，优先引用 | → R5 |
| R5 收尾提示 | 回复中输出"完成汇总"块 + Experience Draft | 否 | **写** Experience Draft → 用户 review → 落盘（或 `[skip]`） | （终态） |

**术语**：
- `<slug>` = 产品短名（kebab-case），如 `redmi-k80-pro`
- `<test>` = 测试目录名，如 `14-xiaomi-k70-case`
- `<part>` = 部件脚本名，如 `xiaomi_k70_case`

---

## Step R1 — 识别 + 生成搜索计划

**前置**：
- [x] 用户需求中明确提到一个具体产品型号

**前置检索（进 R1 第一件事，写 `search_plan.md` 之前必须完成）**：

1. 从需求抽 `<slug>`（kebab-case 产品短名）和 `<category>`（Appendix A 白名单里最接近的一个）
2. 精确匹配：`glob experience/*/<slug>.md` → 命中则完整读入，把"关键参数"/"踩过的坑"/"复用片段"三节注入 R1 上下文
3. 未精确命中 → 同类匹配：`glob experience/<category>/*.md` → 挑 `confidence >= 3` 且 `tags` 最接近的 ≤2 条完整读入
4. 都没命中 → 正常走 R1，不加载任何经验

**过期提醒**：命中条目 frontmatter 的 `last_updated` 距今 > 90 天时，状态降级为 `[partial]` 并在产出报告里显式提醒「⚠ 经验写于 X 天前，建议核实」。

**命中对 `search_plan.md` 内容的影响**：
- 「已知参数」节直接填经验里的数，**每条带来源注释**（形如 `（来自 experience/phone-case/redmi-k80-pro.md）`）
- 「预期坑」节把经验「踩过的坑」原样贴进去（带来源）
- 用户确认 `search_plan.md` 时若当场说「这次重测 X」→ AI 在本次 params.md 里记，**不改经验文件**；R5 时再决定是否回写经验

**R1 产出报告里必须显式上报检索结果**，用以下状态之一（不允许静默加载）：
- `[hit] experience/<category>/<slug>.md` — 精确命中
- `[partial] experience/<category>/*.md` — 同类命中若干条，列出路径
- `[miss] experience/<category>/*` — 全无
- `[skip] reason=<用户明说不查/敏感项目>` — 显式跳过

**本步产出（必须全部存在才允许进入下一步）**：
- `references/<slug>/search_plan.md`（列出 3~4 个待查来源 + 预期获取的资料类型）

**命令模板**：
```bash
SLUG=<kebab-case-product-name>
mkdir -p references/$SLUG
cat > references/$SLUG/search_plan.md <<'EOF'
# 搜索计划：<产品名>

## 目标
- 获取产品尺寸（长/宽/厚 + 关键特征位置）
- 获取官方产品图（至少正面 + 背面）
- 尝试获取 STEP 模型

## 搜索来源
1. 官网规格页 — <品牌官网 URL>
2. GSMArena / 电商规格 — <URL>
3. GrabCAD / Printables — STEP 模型搜索
4. iFixit / B 站拆解视频（兜底）
EOF
```

**AI 回报契约（完成后必须在回复里输出）**：
```
Step R1 产出报告
引自 reference-product-playbook.md §Step R1 / 本步产出：
  "references/<slug>/search_plan.md（列出 3~4 个待查来源 + 预期获取的资料类型）"
- [x] references/<slug>/search_plan.md              (4 来源，待用户确认)
- [hit] experience/phone-case/redmi-k80-pro.md     (精确命中，预加载 10 参数 + 4 坑)
- [miss] experience/phone-case/*                    (无其它同类条目)
下一步：等用户确认 → Step R2
```

（示例为「精确命中」场景；无命中时写 `[miss]`，同类命中时写 `[partial]`。）

**确认门 ✋** 用户确认后进入 R2。

---

## Step R2 — 执行搜集

**前置**：
- [x] `references/<slug>/search_plan.md` 已写入并经用户确认

**本步产出（必须全部存在才允许进入下一步）**：
- `references/<slug>/raw_specs.md`（官网/电商文本规格，含尺寸关键数字）
- `references/<slug>/images/*.{jpg,png}`（至少 1 张产品图，建议正+背+侧各 1）
- （可选）`references/<slug>/model.step`（GrabCAD / 官网下载到的 3D 模型）

**命令模板**：
```bash
SLUG=<your-slug>
mkdir -p references/$SLUG/images

# 1) 抓取官网规格文本 → raw_specs.md（用 WebFetch 或 curl，精炼后写入）
# references/$SLUG/raw_specs.md 内容建议包含：
#   - 产品全名 + 发布年份
#   - 三围尺寸（长/宽/厚）
#   - 重量
#   - 摄像头/按键/接口位置（文字描述）

# 2) 下载官方图
curl -sL <img-url-1> -o references/$SLUG/images/official_01_front.jpg
curl -sL <img-url-2> -o references/$SLUG/images/official_02_back.jpg

# 3) 若 GrabCAD/官网有 STEP：
curl -sL <step-url> -o references/$SLUG/model.step
```

**AI 回报契约**（三种典型场景）：

场景 1：无 STEP
```
Step R2 产出报告
引自 reference-product-playbook.md §Step R2 / 本步产出：
  "references/<slug>/raw_specs.md（官网/电商文本规格，含尺寸关键数字）"
- [x] references/<slug>/raw_specs.md   (官网 + GSMArena 规格合并)
- [x] references/<slug>/images/        (3 张：正/背/侧)
- [skip] references/<slug>/model.step  (reason: GrabCAD 无收录)
下一步：Step R2.5（model.step 缺失 → 反推）
```

场景 2：有 STEP + 不做 Layer 2
```
Step R2 产出报告
- [x] references/<slug>/raw_specs.md
- [x] references/<slug>/images/
- [x] references/<slug>/model.step     (来源：GrabCAD)
下一步：Step R3（有 STEP + 不做视觉对比，[skip] R2.5 reason=已有 model.step，[skip] R2.7 reason=不做 Layer 2 视觉对比）
```

场景 3：有 STEP + 要做 Layer 2
```
Step R2 产出报告
- [x] references/<slug>/raw_specs.md
- [x] references/<slug>/images/
- [x] references/<slug>/model.step
下一步：Step R2.7（[skip] R2.5 reason=已有 model.step，但 R2.7 必做以支持 Layer 2）
```

**分叉判定**：R2 结束时 AI 必须向用户确认"本次是否需要 Layer 2 视觉对比"。
- 需要 + 无 STEP → R2.5 → R2.7 → R3
- 需要 + 有 STEP → R2.7 → R3（skip R2.5）
- 不需要 + 有 STEP → R3（skip R2.5 + R2.7）
- 不需要 + 无 STEP → R2.5（仍需反推尺寸） → R3（skip R2.7）

---

## Step R2.5 — 无 STEP 时反推尺寸

**前置**：
- [x] Step R2 已产出 `references/<slug>/images/`
- [x] `references/<slug>/model.step` 不存在

**本步产出（必须全部存在才允许进入下一步）**：
- `references/<slug>/clean/<stem>_scale.json`（每张要测量的图 × 1）
- `references/<slug>/clean/<stem>_cropped.png`（同上）
- `references/<slug>/measurements.csv`（≥ 1 条关键特征测量值）

**命令模板**：
```bash
SKILL=/Users/liyijiang/.agents/skills/build123d-cad
SLUG=<your-slug>
STEM=official_01_back   # 对每张要测量的图都跑一次

# 1) 获取 bbox（首次：用 matplotlib ginput 手动标定左上+右下）
python3 -c "
from PIL import Image; import matplotlib.pyplot as plt
img = Image.open('references/$SLUG/images/$STEM.jpg')
plt.imshow(img); pts = plt.ginput(2)
x0,y0 = map(int, pts[0]); x1,y1 = map(int, pts[1])
print(f'--bbox {x0},{y0},{x1-x0},{y1-y0}')
"

# 2) 预处理：裁边 + 建 scale
python3 $SKILL/scripts/visual/preprocess_reference.py \
  references/$SLUG/images/$STEM.jpg \
  --bbox "<paste-from-step-1>" \
  --physical-length "<真实物理长度，如 162.2mm>" \
  --physical-axis <height 或 width> \
  --output-dir references/$SLUG/clean/

# 3) 像素测量关键点（原点 = 部件中心）
python3 $SKILL/scripts/visual/pixel_measure.py \
  references/$SLUG/clean/${STEM}_cropped.png \
  --scale references/$SLUG/clean/${STEM}_scale.json \
  --points "<x1,y1;x2,y2;x3,y3>" \
  --origin center \
  --output references/$SLUG/measurements.csv
```

**AI 回报契约**：
```
Step R2.5 产出报告
引自 reference-product-playbook.md §Step R2.5 / 本步产出：
  "references/<slug>/measurements.csv（≥ 1 条关键特征测量值）"
- [x] references/<slug>/clean/official_01_back_scale.json   (mm_per_px=0.26)
- [x] references/<slug>/clean/official_01_back_cropped.png
- [x] references/<slug>/measurements.csv                     (3 条：摄像头中心/主相机/电源键)
下一步：Step R2.7
```

**参考**：`references/reference-product/reverse-engineering.md`（5 种手段 A~E 的应用边界）

---

## Step R2.7 — 参考图现实对齐检查

**前置**：
- [x] Step R2 已产出 `references/<slug>/images/`
- [x] 本次要做 Layer 2 视觉对比（若不做视觉对比 + 有 STEP，可 skip）

**本步产出（必须全部存在才允许进入下一步）**：
- `references/<slug>/clean/<stem>_cropped.png`（每张要进 Layer 2 的参考图，若 R2.5 已跑过可复用）
- `references/<slug>/clean/<stem>_scale.json`（同上）
- `references/<slug>/part_face_mapping.yaml`（语义面 → OCP Camera 枚举映射）

**命令模板**：
```bash
SKILL=/Users/liyijiang/.agents/skills/build123d-cad
SLUG=<your-slug>

# 1) 预处理每张要进 Layer 2 的参考图（若 R2.5 已跑过同图可跳过）
python3 $SKILL/scripts/visual/preprocess_reference.py \
  references/$SLUG/images/official_02_front.jpg \
  --bbox "<x,y,w,h>" --physical-length "<162.2mm>" --physical-axis height \
  --output-dir references/$SLUG/clean/

# 2) 基于模板写 part_face_mapping.yaml
cp $SKILL/references/verify/part-face-mapping-template.yaml \
   references/$SLUG/part_face_mapping.yaml
# 编辑内容：
#   - part: <产品 slug>
#   - coordinate_system.screen_normal: -Y (屏幕朝下) / +Y / ...
#   - face_mapping: FRONT/BACK/LEFT/RIGHT/TOP/BOTTOM 各映射到 Camera 枚举
#   - face_labels: 每面一句中文描述
# 实战参考：tests/14-xiaomi-k70-case/part_face_mapping.yaml
```

**AI 回报契约**：
```
Step R2.7 产出报告
引自 reference-product-playbook.md §Step R2.7 / 本步产出：
  "references/<slug>/part_face_mapping.yaml（语义面 → OCP Camera 枚举映射）"
- [x] references/<slug>/clean/official_02_front_cropped.png
- [x] references/<slug>/clean/official_02_front_scale.json
- [x] references/<slug>/part_face_mapping.yaml            (6 face mappings，coord: screen -Y)
下一步：Step R3
```

**参考**：
- `references/verify/reference-image-preprocessing.md`（预处理 6 节规范）
- `references/verify/part-face-mapping-template.yaml`（模板）
- `references/verify/edge-comparison.md`（下游 Layer 2 阈值）

**特别提示**：
- 只要本次要做 Layer 2 视觉对比，R2.7 就必做——哪怕 R2 有 STEP。
- `part_face_mapping.yaml` 是 `multi_view_screenshot.py --face-mapping` 的强制输入。

---

## Step R3 — 生成 params.md（建模直接输入）

**前置**：
- [x] Step R2（raw_specs.md 提供官方尺寸）
- [x] Step R2.7 已产出（若做 Layer 2）或 Step R2 已产出 `model.step`

**本步产出（必须全部存在才允许进入下一步）**：
- `references/<slug>/params.md`，结构必须包含：
  - `## 数据来源` 段（列出每个来源 + 置信度 ★）
  - `## 产品尺寸（建模直接使用）` 表（参数/数值/来源/置信度四列）
  - `## 配件建模参数建议` 表（壁厚/配合间隙/开孔余量 等工艺参数）

**模板**：
```markdown
# 参数表：<产品名> 配件建模参考

## 数据来源
- 官网：<url>  ★★★★★
- GSMArena：<url>  ★★★★
- STEP 模型：GrabCAD <url>  ★★★★★（如有）
- 反推测量：references/<slug>/measurements.csv  ★★★★

## 产品尺寸（建模直接使用）
| 参数 | 数值 | 来源 | 置信度 |
|------|------|------|--------|
| 长度 | 162.2mm | 官网 | ★★★★★ |
| 宽度 | 74.9mm | 官网 | ★★★★★ |
| 厚度 | 8.9mm | GSMArena | ★★★★ |
| 摄像头模组 | 38×38mm | 反推（手段 B） | ★★★★ |
| 摄像头凸起高度 | ~2mm | 特征比例推断（手段 D） | ★★ |

## 配件建模参数建议
| 参数 | 推荐值 | 说明 |
|------|--------|------|
| 壁厚 | 1.2mm | FDM 打印最小可靠壁厚 |
| 配合间隙（单侧） | +0.3mm | 确保装入顺畅 |
| 开孔余量（单侧） | +0.5mm | 防止遮挡关键接口 |
```

**置信度约定**（与 `references/reference-product/photo-annotation.md` 同步）：
- ★★★★★ 官网参数 / 规格书 / STEP 实测
- ★★★★ 三视图反推（手段 B）/ 已知基准测量（手段 C）
- ★★★ 拆机视频截帧反推（手段 E）
- ★★ 特征比例推断（手段 D）— 下游必须标记"待验证"
- ★ 未确认 / 待用户实测

**AI 回报契约**：
```
Step R3 产出报告
引自 reference-product-playbook.md §Step R3 / 本步产出：
  "references/<slug>/params.md，结构必须包含：## 数据来源 段 / ## 产品尺寸（建模直接使用）表 / ## 配件建模参数建议 表"
- [x] references/<slug>/params.md  (8 行尺寸表：5 项 ★★★★★ / 2 项 ★★★★ / 1 项 ★★)
下一步：等用户确认 → Step R3.5
```

**确认门 ✋** 用户确认后进入 R3.5。

---

## Step R3.5 — 生成 Layer 0 参数合同（contract.yaml）

**前置**：
- [x] Step R3 `params.md` 已用户确认

**本步产出（必须全部存在才允许进入下一步）**：
- `tests/<test>/contract.yaml`，结构必须包含：`meta` / `features` / `param_map`

**模板**：
```yaml
meta:
  product: "<产品名>"
  body_ref: {L: 162.2, W: 74.9, T: 8.9}

features:
  - name: camera_module
    type: rounded_rect
    face: back
    dims: {w: 38.0, h: 38.0, r: 8.0}
    pos: {cx: -13.0, cy: 55.0}
    constraints:
      - {type: on_face, value: back, locks: [Z]}
      - {type: edge_dist, ref: top, value: 26.4, tol: 2.0, locks: [Y]}
      - {type: edge_dist, ref: left, value: 24.9, tol: 2.0, locks: [X]}

param_map:
  camera_module.pos.cx: CAMERA_CX
  camera_module.pos.cy: CAMERA_CY
```

**要求**：
- 每个 feature 至少 3 条 constraints（覆盖 X / Y / Z 三轴）
- `_ratios` 归一化比例字段可选，但一旦填写须与绝对值一致

**静态检查**：
```bash
python3 /Users/liyijiang/.agents/skills/build123d-cad/scripts/validate/contract_verify.py \
  --contract tests/<test>/contract.yaml --check-only
```
期望：exit code 0 + "contract complete and consistent"。

**AI 回报契约**：
```
Step R3.5 产出报告
引自 reference-product-playbook.md §Step R3.5 / 本步产出：
  "tests/<test>/contract.yaml，结构必须包含：meta / features / param_map"
- [x] tests/<test>/contract.yaml           (3 features, 9 constraints, 静态检查通过)
下一步：等用户确认 → Step R4
```

**参考**：`references/verify/layer0-contract.md`

**确认门 ✋** 用户确认合同无误后进入 R4。

---

## Step R4 — 进入标准建模流程

**前置**：
- [x] Step R3.5 `contract.yaml` 已用户确认

**本步产出（必须全部存在才允许进入下一步）**：
- `tests/<test>/<part>.py`（建模脚本，末尾带 OCP 自动预览块）
- OCP Viewer 实际打开并显示模型（可用截图或 `get_ports()` 的输出作为证据）

**路由**：
- 单个配件 → 走 `SKILL.md` "单部件简化流程（Single-Part Protocol）" Step 1~4（含 3 变体 OCP 对比）
- 多部件 → 走 `SKILL.md` "多部件 4 阶段流程（Multi-Part Protocol）" Phase 1~4

**建模完成后自动触发 Layer 1/2 验证链**：

```bash
SKILL=/Users/liyijiang/.agents/skills/build123d-cad

# Layer 1 合同运行时验证
python3 $SKILL/scripts/validate/contract_verify.py \
  --contract tests/<test>/contract.yaml \
  --params tests/<test>/params.json

# Layer 2 视觉对比（需要 R2.7 产出的 part_face_mapping.yaml）
python3 $SKILL/scripts/visual/multi_view_screenshot.py \
  tests/<test>/<part>.step \
  --mode ortho \
  --face-mapping references/<slug>/part_face_mapping.yaml

python3 $SKILL/scripts/visual/visual_compare.py \
  output/<part>_FRONT.png references/<slug>/clean/official_front_cropped.png \
  --reference-scale references/<slug>/clean/official_front_scale.json \
  --rendered-scale auto \
  --mode edge_overlay \
  --output output/compare_front.png
```

**AI 回报契约**：
```
Step R4 产出报告
引自 reference-product-playbook.md §Step R4 / 本步产出：
  "tests/<test>/<part>.py（建模脚本，末尾带 OCP 自动预览块）"
- [x] tests/<test>/<part>.py              (Layer 1 pass)
- [x] OCP Viewer 预览已打开               (端口 3939)
- [x] Layer 2 edge_overlay: IoU=0.87     (≥0.85 阈值，pass)
下一步：Step R5
```

**Layer 2 失败反馈**：若 IoU < 0.85，按 `references/verify/feedback-diagnosis.md` 分根因回退：
- 根因 A（数据源错）→ 回补 R2/R3
- 根因 B（合同错）→ 回 R3.5 改 contract.yaml
- 根因 C（代码错）→ 修改建模代码
- 修复上限：L1×3 + L2×2 + 跨层×2 = 总计 ≤ 5 轮

**参考**：
- Layer 1：`references/verify/layer1-verification.md`
- Layer 2：`references/verify/layer2-visual.md` + `references/verify/edge-comparison.md`
- 反馈闭环：`references/verify/feedback-diagnosis.md`

---

## Step R5 — 收尾提示

**前置**：
- [x] Step R4 建模完成且 Layer 1 / Layer 2 通过（或已按反馈闭环修复完成）

**本步产出**：

1. **完成汇总块**（当次回复里的一段文字，不落盘）——Layer 0/1/2 状态 + 置信度统计 + 后续建议
2. **Experience Draft 块**（当次回复里的一段文字）——按下方模板自动起草，供用户 review
3. **用户 review 决策落盘**：
   - 用户说「保存」/「ok」/「yes」→ 落盘 `experience/<category>/<slug>.md`，回报 `[saved]`
   - 用户提增删改 → AI 更新 draft 重输出，再等确认
   - 用户说「不保存」/「skip」→ 回报 `[skip] experience reason=...`，不写盘
4. **落盘行为**：
   - 新条目 → `Write` 工具直接写
   - 已存在（精确 slug 命中，R1 `[hit]` 过的情况）→ 读旧文件 → diff 呈现 → 用户选：
     - `merge`（默认推荐）：参数按 slug+name 去重（新值覆盖，`confidence` 取高）；"踩过的坑"和"复用片段"一律 **append 不去重**
     - `overwrite`：整文件覆盖
     - `keep-old`：不动旧文件

**关键规则**：draft 和 saved/skip 必须都在回报里显式上报；**未经用户 review 不得自动写盘**。

**完成汇总块模板**：

```markdown
## 完成汇总

### 验证状态
- Layer 0（合同静态检查）：✅
- Layer 1（合同运行时验证）：✅
- Layer 2（视觉对比）：✅ IoU=0.87

### 置信度分布
- 尺寸 ★★★★★：5 项
- 尺寸 ★★★★：2 项
- 尺寸 ★★：1 项（摄像头凸起高度，建议用户实测后回填）

### 参考资料归档
- `references/<slug>/` 已完成使命，是否保留？
  - [ 保留 ]（作为设计依据，后续回改参数时复用）
  - [ 删除 ]（本次已落入 `params.md` + `contract.yaml`，原始资料可清）

### 下一步建议
- <Layer 2 IoU 偏低 → 建议回 R2.7 检查 face_mapping>
- <某特征置信度 ≤ ★★ → 建议用户实测后更新 params.md>
- <未出现异常 → 可进入 3D 打印 / CNC 流程>
```

**Experience Draft 模板**（AI 自动起草，填值规则见各字段注释）：

````markdown
## Experience Draft（请 review，确认后保存到 `experience/<category>/<slug>.md`）

```yaml
slug: <kebab-case 产品短名，与 references/<slug>/ 对齐>
category: <Appendix A 白名单里最接近的>
tags: [<3~5 个类别词，从 raw_specs.md 摘屏幕尺寸/芯片/接口等>]
confidence: <本次 params.md 所有 ★ 行的中位数，整数>
last_updated: <今天的 ISO 日期>
related_tests:
  - tests/<test>
source_model: <step / reverse-engineered / mixed>
```

## 关键参数（下次直接用）
<从 references/<slug>/params.md 提 ★ ≥ 3 的行；每行末尾保留来源>

## 踩过的坑
<从本次对话摘：用户纠正节点 / AI 回退节点 / 修了几轮的 Layer 2 偏差 / 单位搞错等>

**若本节为空**，AI 必须显式问用户「本次没发现坑对吗？确认后保存」——避免垃圾经验污染后续检索。

## 下次直接复用（copy-paste 片段）
<从 tests/<test>/<part>.py 提前 ~20 行关键尺寸常量声明段，封装成 code block>

## 未解决 / 待验证（可选）
<本次置信度 ★ ≤ 2 的尺寸 / Layer 2 未覆盖的特征 / 用户承诺回测的条目>
````

**AI 回报契约**：
```
Step R5 产出报告
引自 reference-product-playbook.md §Step R5 / 本步产出：
  "完成汇总块（当次回复里的一段文字，不落盘）——Layer 0/1/2 状态 + 置信度统计 + 后续建议"
- [x] 完成汇总块已输出（上方）
- [x] Experience Draft 已输出（上方），等用户 review
- [ ] experience/<category>/<slug>.md    (等用户确认后补 [saved] 或 [skip])
- [ask] references/<slug>/ 保留 or 删除？
参考物建模协议 R1~R5 完成（经验落盘待用户 review）。
```

---

## 常见失败模式（test 13 / 14 沉淀）

### FM-1：bbox 越界
**现象**：`preprocess_reference.py` 报 `bbox out of image range`
**根因**：误以为图是竖版（height 主轴），实际是横版（width 主轴）；或直接复用他图的 bbox 数字
**诊断**：
```bash
python3 -c "from PIL import Image; print(Image.open('<img>').size)"
```
**修复**：根据实际 size 切换 `--physical-axis width` 或 `height` + 重新标 bbox

### FM-2：mm/px 反算
**现象**：测量值数量级异常（单位看起来像 µm 或 km）
**根因**：`--physical-length` 填成了图上像素数，而非真实物理长度
**诊断**：检查 `*_scale.json` 里 `mm_per_px`，合理区间通常是 0.05 ~ 1.0
**修复**：用真实物理长度（如 `162.2mm`）重跑 preprocess

### FM-3：face_mapping 写反
**现象**：Layer 2 每个面都 IoU < 0.3，整体对不上
**根因**：`part_face_mapping.yaml` 的 FRONT/BACK 与 OCP `Camera.FRONT/BACK` 的法线方向搞反
**诊断**：检查 `coordinate_system.screen_normal`，再逐条核对 `face_mapping` 条目
**修复**：参考实战样本 `tests/14-xiaomi-k70-case/part_face_mapping.yaml`，明确"屏幕朝 -Y → FRONT→BACK"的等价关系

### FM-4：R2.7 偷懒跳过
**现象**：AI 有 STEP 模型就直接跳 R3，后续 Layer 2 失败时才发现缺 `part_face_mapping.yaml`
**根因**：错误等同"有 STEP = R2.7 可跳"，忽略"做 Layer 2 就必做 R2.7"
**诊断**：在 R2 产出报告里必须显式答复"本次是否做 Layer 2"
**修复**：是 → R2.7 必做（只跳 R2.5）；否 → skip R2.7 + reason

### FM-5：置信度伪造
**现象**：params.md 里反推尺寸被标 ★★★★★
**根因**：AI 为了让验证通过，把低置信度尺寸标高
**诊断**：交叉检查 params.md "数据来源"段：若来自"反推/拆机/推断"，置信度不得 ≥ ★★★★
**修复**：如实填写置信度。允许 ★★ 尺寸进入下游建模，但 R5 完成汇总里要提醒用户实测

### FM-6：产出报告漏写
**现象**：AI 直接开始做下一步，没有先输出产出报告
**根因**：遗忘"执行契约"第 1 条
**诊断**：用户注意到回复里没有 `Step Rn 产出报告` 块
**修复**：立刻补一条产出报告，回补漏的 artifact，再继续

### FM-7：静默加载经验
**现象**：R1 检索到 `experience/<slug>.md` 但不在产出报告里报 `[hit]`，用户不知道 `search_plan.md` 里哪些参数来自历史记录
**根因**：遗忘契约第 6 条，把"读经验"当作透明过程
**诊断**：检查 R1 产出报告是否含 `[hit]`/`[partial]`/`[miss]`/`[skip]` 四状态之一；检查 `search_plan.md` 的"已知参数"节是否每条带来源注释
**修复**：立刻补一条 `[hit] experience/...`；把来源注释补回 `search_plan.md`；若用户已基于无来源的参数做了决策，回退到 R1 重走

### FM-8：经验污染 R2.7
**现象**：R1 命中经验的「踩过的坑」后，AI 把这些坑当既定事实，跳过 R2.7 视觉对齐
**根因**：把"先验"误当"事实"；经验是历史 offset，不替代本次 Layer 2 验证
**诊断**：R2.7 产出报告缺失但 Layer 2 分叉仍走下去；或 `part_face_mapping.yaml` 未生成
**修复**：强制回 R2.7 补产；在 R1 产出报告里把命中的"坑"标明「本次仍需 Layer 2 验证」

### FM-9：Quote-back 伪造
**现象**：AI 写了 Quote-back 但原文在 Playbook 里 grep 不到
**根因**：AI 没真 Read，凭记忆拼了一句"像 Playbook 的话"
**诊断**：
```bash
grep -F "<被引用的原文>" references/protocols/reference-product-playbook.md
```
**修复**：要求 AI 重新 Read 对应 Step 原文，重出产出报告；多次违规视为必须降级重跑本 Step

---

## Appendix A — category 白名单

AI 在 R1 前置检索时，`<category>` 必须从下面 25 个中取**最接近的一个**，不自造。同类词（如 `手机壳` / `case` / `phone case`）一律映射到白名单词（`phone-case`）。

```
phone-case         servo-mount       enclosure         pcb-holder
heat-sink          bracket           knob              gear
clip               hinge             adapter           mount-plate
standoff           cable-gland       handle            cap
bushing            spacer            fixture           jig
housing            shell             cover             tray
frame
```

**边界情况**：
- 产品介于两类之间（如「舵机外壳」介于 `servo-mount` 和 `enclosure`）→ 以**主结构**决定，外壳占比大 → `enclosure`；安装位占比大 → `servo-mount`
- 白名单里找不到合适的 → 不新增词，临时用 `fixture` 或 `jig` 兜底；**连续 3 个条目都走 fixture 时**，在该 skill 仓提 issue 考虑扩充白名单

