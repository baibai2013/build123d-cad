# 参考图标注规范 / Photo Annotation Convention

> 工具：`scripts/visual/annotate_reference.py`

## 1. 颜色约定

| 颜色 | 含义 | 典型 confidence |
|---|---|---|
| 🔵 蓝 | 官方参数（官网 / 规格书） | 5 |
| 🔴 红 | 反推尺寸（手段 B/C/E） | 4 |
| 🟠 橙 | 拆解/视频截帧反推 | 3 |
| 🟡 黄 | 特征比例推断（手段 D） | 2 |
| ⚫ 灰 | 未确认 / 待用户测量 | 1 |

`annotate_reference.py` 的 `confidence` 字段是 1~5，脚本按这个自动上色；`color` 字段可以手动覆盖。

## 2. annotations.json 格式

```json
{
  "scale": {"pixels": 1080, "mm": 162.0},
  "origin": [540, 820],
  "features": [
    {
      "name": "camera_module",
      "center_px": [320, 150],
      "size_mm": [38, 38],
      "confidence": 4,
      "color": "red"
    },
    {
      "name": "power_button",
      "center_px": [1000, 500],
      "size_mm": [6, 20],
      "confidence": 5
    }
  ]
}
```

## 3. 产出文件命名

- `{face}_annotated.png`（face ∈ front/back/side/top/bottom）
- 放到 `references/{product}/annotated/` 目录
- 原图保留在 `references/{product}/images/`

## 4. 标注流程

1. 跑 `preprocess_reference.py` 拿到 cropped 图 + scale.json
2. 用 Preview / matplotlib ginput 在原图或 cropped 图上点关键特征，记录像素坐标
3. 写 annotations.json（scale/origin/features）
4. 跑 `annotate_reference.py`
5. 肉眼检查输出，置信度低的特征加入 `params.md` 的"待确认"列表

## 5. 案例

见 `/Users/liyijiang/work/build123d-cad-skill-test/tests/13-redmi-k80-pro/output/photo_annotated.png` 和 `side_annotated.png`（test 13 实战产出）。
