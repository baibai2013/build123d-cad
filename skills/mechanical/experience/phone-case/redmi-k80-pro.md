---
slug: redmi-k80-pro
category: phone-case
tags: [android, 6.67-inch, triple-camera, xiaomi]
confidence: 4
last_updated: 2026-04-18
related_tests:
  - tests/13-redmi-k80-pro
source_model: reverse-engineered
---

## 关键参数（下次直接用）

- 机身 160.26 × 74.95 × 8.39 mm ★5（多站交叉验证官方尺寸）
- 竖边圆角 R_corner 9.0 mm ★3（图片比例推算）
- 前后 Z 方向边缘圆角 R_edge 1.5 mm ★3
- 后置摄像头模组外环直径 D_cam 34.0 mm ★3（图片比例 ~45% 机身宽）
- 摄像头模组凸起高度 2.5 mm ★3
- 摄像头中心 X: -16.0 mm ★3（从机身中心，负=偏左）
- 摄像头中心 Y: +60.0 mm ★3（从机身中心，正=偏上；距顶边约 20 mm）
- USB-C 口宽 × 高 = 9.0 × 3.2 mm ★3（居中）
- USB-C 圆角 1.6 mm ★3（胶囊形）
- 屏幕尺寸 152.0 × 72.0 mm ★3（6.67″ 20:9 反推）

## 踩过的坑

- 摄像头中心 Y 坐标正负易混淆：**正 = 距机身中心往上偏**，而不是"距顶边距离"。test 13 曾误把 +60 当成距顶边 60mm，导致整个模组位置下移
- 屏幕凹陷深度 0.15 mm 非常小，容易手写成 1.5 mm——check 数量级
- 按键宽度（沿厚度方向 2.5 mm）和按键凸起高度（凸出中框 1.0 mm）是两个维度，不要混淆
- 摄像头模组外环直径由图片比例推算（~45% 机身宽 × 74.95），置信度只有 ★3，新品发布后若拿到 STEP 需要实测覆盖

## 下次直接复用（copy-paste 片段）

```python
# Redmi K80 Pro 机身基本参数（mm）
phone_L, phone_W, phone_T = 160.26, 74.95, 8.39
corner_R, edge_R = 9.0, 1.5

# 后置摄像头模组（圆形"风暴眼"）
cam_module_D = 34.0      # 外环直径
cam_bump_H = 2.5          # 凸起高度
cam_center = (-16.0, 60.0)  # (X, Y) 相对机身中心；负 X=偏左，正 Y=偏上

# 底部开孔
usb_w, usb_h, usb_r = 9.0, 3.2, 1.6  # USB-C 胶囊形
```

## 未解决 / 待验证

- 摄像头模组外环直径 ★3 只有图片比例推算，建议后续用卡尺或 STEP 实测回填到 ★4+
- 三镜头布局 PCD 9.0 mm 未经 Layer 2 验证，仅供参考
