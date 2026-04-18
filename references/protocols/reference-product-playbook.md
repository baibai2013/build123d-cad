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

---

## R1~R5 Step 总表

| Step | 必须产出 | 允许跳过？ | 下一步分叉 |
|---|---|---|---|
| R1 识别 + 搜索计划 | `references/<slug>/search_plan.md` | 否 | → R2 |
| R2 执行搜集 | `references/<slug>/raw_specs.md` + `images/*` | 否 | 有 `model.step` → R3/R2.7；无 → R2.5 |
| R2.5 无 STEP 反推 | `references/<slug>/clean/*_scale.json` + `measurements.csv` | 仅 R2 已产出 `model.step` 时可 skip | → R2.7 |
| R2.7 参考图现实对齐 | `references/<slug>/clean/*_cropped.png` + `part_face_mapping.yaml` | 否（Layer 2 必做）；仅 "有 STEP + 不做视觉对比" 可 skip | → R3 |
| R3 生成 params.md | `references/<slug>/params.md`（含 ★ 置信度） | 否 | → R3.5 |
| R3.5 生成 contract.yaml | `tests/<test>/contract.yaml` | 否 | → R4 |
| R4 建模 | `tests/<test>/<part>.py` + OCP 自动预览 | 否 | → R5 |
| R5 收尾提示 | 回复中输出"完成汇总"块 | 否 | （终态） |

**术语**：
- `<slug>` = 产品短名（kebab-case），如 `redmi-k80-pro`
- `<test>` = 测试目录名，如 `14-xiaomi-k70-case`
- `<part>` = 部件脚本名，如 `xiaomi_k70_case`

---

## Step R1 — 识别 + 生成搜索计划

**前置**：
- [x] 用户需求中明确提到一个具体产品型号

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
- [x] references/<slug>/search_plan.md  (4 来源，待用户确认)
下一步：等用户确认 → Step R2
```

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
- [x] references/<slug>/clean/official_01_back_scale.json   (mm_per_px=0.26)
- [x] references/<slug>/clean/official_01_back_cropped.png
- [x] references/<slug>/measurements.csv                     (3 条：摄像头中心/主相机/电源键)
下一步：Step R2.7
```

**参考**：`references/reference-product/reverse-engineering.md`（5 种手段 A~E 的应用边界）
