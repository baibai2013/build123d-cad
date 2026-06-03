---
name: build123d-cad-sendcutsend
description: |
  build123d-cad 的钣金/激光出工子技能。把 mechanical 出的 STEP 转成
  SendCutSend 合规 DXF,做 DFM 自检,出估价区间,必要时调 SendCutSend
  公开报价(API 或网站表单 fallback)。
  触发词:激光切割、钣金、DXF、SendCutSend、kerf、折弯、bend relief、
  攻丝、anodize、水刀、laser cut、sheet metal。
  本子技能不做:3D 建模本身(→ mechanical)、3D 打印切片(→ gcode)、
  网页预览(→ viewer)。
---

# build123d-cad · sendcutsend 子技能

把 build123d 钣金件落到 SendCutSend 这家平台:**STEP → DXF → DFM 自检 → 估价**。

> 一句话定位:mechanical 管"画对",sendcutsend 管"做得出 + 做得起"。
>
> 设计端永远导**名义尺寸**,不做 kerf 预补偿(SendCutSend 自己 CAM 端补)。

---

## AI 执行准入序列

1. 收到"激光切"/"钣金"/"DXF 报价"类需求 → 先确认 STEP 文件存在(由 mechanical 上游产出)。
2. 读本 SKILL.md(本文件)的"5 步主流程",**不要**直接读 references/ 拼。
3. references/ 仅作为脚本规则查询表,不当 Playbook 用。
4. 跨子技能流程通过 `../../shared/handoff-protocols.md` 走文件接口,不互调函数。

---

## 5 步主流程

```
mechanical 出 STEP (sheet_metal=True)
        │
        ▼
[1] step_to_dxf.py        — 投影 XY + 标 BEND 层
        │
        ▼
[2] dfm_check()           — 跑 DFM checklist(quote_estimator.py)
        │
        ├─ 失败 → 标注问题 → handoff 回 mechanical
        │
        └─ 通过 ▼
[3] estimate_price()      — 本地表估价区间
        │
        ▼
[4] quote_api()           — 真实下单价(API/网站表单 fallback)
        │
        ▼
[5] viewer handoff        — DXF 预览链接给 CEO 审
```

每一步的脚本都在 `scripts/` 下,见下表。

---

## 工艺能力矩阵(速查)

| 工艺 | 适用范围 | 详表 |
|---|---|---|
| 激光切割 | 金属 0.5~6 mm,亚克力/木 1~12 mm | `references/material-thickness-price.md` §1 |
| 折弯 | 板厚 ≤6 mm,长度 ≤48 in | `references/dfm-rules-laser-bend.md` §4 |
| 攻丝 | M2~M12 / #2-56~1/2-13 | `references/dfm-rules-laser-bend.md` §5 |
| 沉头/锪孔 | 82°/90°/100° | `references/dfm-rules-laser-bend.md` §6 |
| 表面处理 | 拉丝/喷砂/阳极/粉末/镀锌/钝化 | `references/dfm-rules-laser-bend.md` §7 |
| 水刀 | ≤25 mm 任意材料 | `references/material-thickness-price.md` §1 |

---

## 材料矩阵(机器狗常用三选)

| 材料 | 厚度档(mm) | 用途 | 价格区间(USD/in²) |
|---|---|---|---|
| 2024-T3 铝 | 0.5~3.2 | 力臂、电机背板、承力件 | 0.06 ~ 0.32 |
| 5052-H32 铝 | 0.5~6.4 | **外壳钣金、整流罩(首选)** | 0.05 ~ 0.50 |
| 304 不锈钢 | 0.5~6.4 | 户外关节件、流体接触 | 0.10 ~ 1.30 |

完整厚度档 + 工艺可行性 + 单价见 `references/material-thickness-price.md`。

---

## DFM 五条铁律(违反必退单)

1. **kerf 不预补偿**(DXF 始终导名义尺寸)
2. **最小孔径** ≥ 1.0×t(软金属) / 1.2×t(不锈钢)
3. **折弯距孔距离** ≥ 2.5×t + 内 R(DFM 退单 No.1)
4. **折弯凸缘高度** ≥ 4×t + R + die_w/2(典型 1.6mm 板 ≥10mm)
5. **折弯线必须放 `BEND` 图层 + DASHED 线型**(SendCutSend 自动识别)

完整 10 条 checklist + 高频反例见 `references/dfm-rules-laser-bend.md` §8/§9。

---

## 与 mechanical 的 handoff

mechanical 在 STEP 元数据(`<part>.meta.json` sidecar)标:

```json
{
  "sheet_metal": true,
  "thickness_mm": 1.6,
  "material": "AL_5052",
  "bends": [
    {"line_id": "bend_1", "direction": "up", "angle_deg": 90, "radius_mm": 1.6}
  ],
  "finish": "anodize_black"
}
```

父级路由器看到 `sheet_metal=true` → 自动调用本子技能 `scripts/step_to_dxf.py`。

如果 sidecar 缺失:
- 优先反问 mechanical 补齐(关键参数:厚度、材料、折弯方向)
- 不要在 sendcutsend 内推断厚度(STEP bbox 推不准弯角处的真厚度)

---

## 脚本索引

| 脚本 | 职责 |
|---|---|
| `scripts/step_to_dxf.py` | STEP → DXF(投影 XY 平面,BEND 层标记折弯线) |
| `scripts/quote_estimator.py` | DFM 自检 + 本地估价 + 询价 API/表单 fallback |

直接读脚本顶部 docstring 看用法,不要凭名字猜参数。

---

## 询价对接

`quote_estimator.py::quote_api()` 走两级 fallback:

1. **首选** SendCutSend public quote endpoint(若公开)
   `POST https://sendcutsend.com/api/v1/quote` (form-encoded `dxf_file`/`material_sku`/`thickness`/`finish`/`quantity`)
2. **降级**:写 form 提交脚本(playwright/requests)模拟网站上传 → 抓 quote 页价格
3. **再降级**:打开浏览器到 `https://sendcutsend.com/upload` 让 CEO 手动确认

第 1 级 endpoint 公开状态会变化,定期校准;失败时不要假装报价成功,直接降级到第 2/3 级并在结果里注明 `quote_source: form/manual`。

---

## 输出物路径约定

按 `shared/handoff-protocols.md`:

```
output/<task>/
├── <part>.dxf              # SendCutSend 上传文件(已通过 DFM)
├── <part>.quote.json       # 本地估价 + 真实询价(若拿到)
└── <part>.dfm-report.md    # DFM 自检报告(失败时给 mechanical 回环)
```

文件名约定:`<part>_<material>-<thickness>.dxf`,如 `bracket_AL5052-1.6.dxf`。

---

## 验证脚本(端到端)

```bash
# 1. 拿 mechanical 输出的钣金 STEP
STEP=output/sheet-bracket/bracket.step

# 2. 出 DXF
python scripts/step_to_dxf.py "$STEP" \
    --thickness 1.6 --material AL_5052 \
    --out output/sheet-bracket/bracket_AL5052-1.6.dxf

# 3. DFM + 估价
python scripts/quote_estimator.py \
    output/sheet-bracket/bracket_AL5052-1.6.dxf \
    --thickness 1.6 --material AL_5052 \
    --finish anodize_black --quantity 5 \
    --out output/sheet-bracket/bracket.quote.json

# 4. 看 quote.json:price_low / price_high / dfm_pass
cat output/sheet-bracket/bracket.quote.json
```

预期:`dfm_pass: true`、`price_low/high` 落在材料表区间内、`quote_source: local_estimate`(API 未公开时)。

---

## 角色规则(子技能本地)

1. 永远导名义尺寸,不预补 kerf。
2. 折弯线放 `BEND` 图层 + DASHED;cut 几何放 `0` 层(默认)。
3. 估价**仅作设计阶段过滤**,真实下单必走第 4 步询价。
4. DFM 失败 → 写 `dfm-report.md` 回环给 mechanical,不擅自改 STEP。
5. 凡是触及生产数据 / 真实下单的步骤标 `gate: true`,等 CEO 审。

---

## references/

- `material-thickness-price.md` — 工艺能力 + 材料矩阵 + 单价区间
- `dfm-rules-laser-bend.md` — 设计为加工(kerf / 孔径 / 折弯 / 攻丝 / 表面处理 / 自检 checklist)

不在 references/ 里的规则不要凭印象写,先去 sendcutsend.com Design Guidelines 校准再加进表。
