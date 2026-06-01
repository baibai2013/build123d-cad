# 边缘对比判定阈值 / Edge Comparison Thresholds

> 这些是 **几何对齐视角** 的阈值（配合 `scripts/visual/visual_compare.py`）。
> AI Vision 模式的阈值见 cad-vision-verify skill 文档。

## 1. 判定表（第一版，test 13 N=1 样本）

| 指标 | 通过 ✅ | 警告 ⚠️ | 失败 ❌ |
|---|---|---|---|
| 边缘 IoU（二值化 Canny 后） | ≥ 0.85 | 0.70 ~ 0.85 | < 0.70 |
| Bounding box 尺寸偏差 | ≤ 2 % | 2 % ~ 5 % | > 5 % |
| 关键特征位置偏差 | ≤ 2 mm | 2 ~ 5 mm | > 5 mm |
| 灰度差 heatmap 平均值 | ≤ 15 | 15 ~ 30 | > 30 |

注：阈值为建议值，test 14/15 积累更多案例后应复核。

## 2. Canny 参数

- `low=50, high=150`，高斯模糊 `sigma=1.0`（实测可行于 test 13）
- **不调** Canny 参数去"抢救"失败的对比——如果 IoU 低，回源头修模型

## 3. 失败诊断路径

| 症状 | 回到哪一步 |
|---|---|
| 尺寸整体错 | Step R3 参数合同（params.md） |
| 特征位置错 | Step R3.5 合同校验（contract.yaml） |
| 比例错 | Step R2 资料来源（三视图尺寸核对） |
| 视图名对不上 | `part_face_mapping.yaml` |
| 参考图歪/畸变 | Step R2.7 参考图预处理 |

## 4. 不适用场景

- 透视强烈的 3/4 角度实拍 → 走 AI Vision（cad-vision-verify skill）
- 参考图有遮挡、阴影、反光 → IoU 会虚低，以人眼判断为准
