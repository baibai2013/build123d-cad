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
