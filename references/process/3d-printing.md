# 3D 打印设计规则

> FDM / SLA 打印的设计约束、公差、配合、导出参数完整参考。

---

## 1. FDM 打印设计约束

| 约束 | 推荐值 | 说明 |
|------|--------|------|
| 最小壁厚 | ≥ 0.8mm（2 线宽） | 低于此值切片软件可能忽略 |
| 悬臂角度 | ≤ 45° | 超过需加支撑 |
| 桥接长度 | ≤ 10mm | 超过会下垂 |
| 最小孔径 | ≥ 2mm | 小于此值可能被填充 |
| 最小特征 | ≥ 0.4mm（1 线宽） | 文字/浮雕最小细节 |
| 层高对齐 | 尺寸为层高整数倍 | 0.2mm 层高 → 高度 10.0/10.2/10.4mm |

### 悬臂与支撑

```python
# 悬臂角度 > 45° 需要支撑
# 设计时优先用倒角代替直角悬臂
chamfer(overhanging_edges, length=overhang_height)  # 45° 倒角消除支撑

# 或使用 fillet 创建自支撑过渡
fillet(overhanging_edges, radius=overhang_height)
```

### 打印方向选择

| 目标 | 推荐打印方向 |
|------|------------|
| 最高强度 | 载荷方向垂直于层线（XY 方向受力） |
| 最少支撑 | 悬臂面朝上 |
| 最佳表面 | 外观面垂直放置 |
| 孔精度 | 孔轴垂直于打印床（Z 方向） |

---

## 2. SLA 打印设计约束

| 约束 | 推荐值 | 说明 |
|------|--------|------|
| 最小壁厚 | ≥ 0.4mm | 薄壁可能破裂 |
| 最小特征 | ≥ 0.2mm | 精细纹理极限 |
| 排液孔 | Ø ≥ 2mm | 空心结构必须开排液孔 |
| 最小间隙 | ≥ 0.15mm | 活动配合件 |
| 支撑接触点 | Ø 0.3-0.5mm | 最小化支撑痕迹 |

---

## 3. 打印公差表

| 工艺 | XY 精度 | Z 精度 | 圆孔精度 |
|------|---------|--------|---------|
| FDM (0.4mm 喷嘴) | ±0.2mm | ±0.1mm (层高) | -0.1~-0.3mm (偏小) |
| FDM (0.2mm 喷嘴) | ±0.1mm | ±0.05mm | -0.05~-0.15mm |
| SLA (标准) | ±0.05mm | ±0.025mm | ±0.05mm |
| SLA (精密) | ±0.025mm | ±0.01mm | ±0.025mm |

---

## 4. 配合设计

### 间隙推荐值

| 配合类型 | FDM 间隙 | SLA 间隙 | 用途 |
|---------|---------|---------|------|
| 间隙配合（松） | 0.3-0.5mm | 0.15-0.25mm | 可拆卸零件 |
| 间隙配合（紧） | 0.15-0.25mm | 0.08-0.15mm | 滑动配合 |
| 过渡配合 | 0.05-0.15mm | 0.03-0.08mm | 定位销 |
| 过盈配合 | -0.05~-0.15mm | -0.02~-0.05mm | 压入固定 |

### 在 build123d 中设计配合

```python
# 轴和孔的配合设计
shaft_r = 5.0            # 名义半径
clearance = 0.2          # FDM 间隙配合

# 轴（名义尺寸）
with BuildPart() as shaft:
    Cylinder(radius=shaft_r, height=20)

# 孔（名义尺寸 + 间隙）
with BuildPart() as housing:
    Box(30, 30, 20)
    Hole(radius=shaft_r + clearance)  # 孔径 = 轴径 + 间隙

export_step(shaft.part, "shaft.step")
export_step(housing.part, "housing.step")
```

---

## 5. 螺纹设计

### 自攻孔尺寸（FDM）

| 螺丝规格 | 自攻孔直径 | 孔深 | 壳体最小壁厚 |
|---------|----------|------|------------|
| M2 | Ø1.6mm | ≥4mm | 2mm |
| M2.5 | Ø2.0mm | ≥5mm | 2.5mm |
| M3 | Ø2.5mm | ≥6mm | 3mm |
| M4 | Ø3.3mm | ≥8mm | 4mm |

### 嵌入螺母预留

```python
# M3 热熔嵌入螺母（常见规格 Ø4.2 × 3mm）
insert_d = 4.2
insert_h = 3.0
press_fit = 0.1          # 过盈量

with BuildPart() as boss:
    Cylinder(radius=insert_d / 2 + 2, height=insert_h + 2)
    # 嵌入孔（顶部稍大便于热熔插入）
    Hole(radius=(insert_d - press_fit) / 2, depth=insert_h)
```

---

## 6. STL/3MF 导出参数

```python
# FDM 打印 — 标准精度
export_stl(part.part, "output.stl",
           linear_tolerance=0.1,     # 0.1mm 弦偏差
           angular_tolerance=0.5)    # 0.5° 角度偏差

# SLA 打印 — 高精度
export_stl(part.part, "output.stl",
           linear_tolerance=0.01,    # 0.01mm 弦偏差
           angular_tolerance=0.1)    # 0.1° 角度偏差

# 3MF 格式（支持颜色、材料信息）
export_3mf(part.part, "output.3mf")
```

| 参数 | FDM 推荐 | SLA 推荐 | 说明 |
|------|---------|---------|------|
| `linear_tolerance` | 0.1 | 0.01 | 弦偏差（mm），越小越精细 |
| `angular_tolerance` | 0.5 | 0.1 | 角度偏差（度） |
| 文件大小 | ~1-5 MB | ~5-50 MB | 精度越高文件越大 |

---

## 7. 多材料策略

| 场景 | 材料组合 | 设计要点 |
|------|---------|---------|
| 柔性足垫 | TPU (Shore 95A) + PLA 骨架 | 接合面用燕尾槽/卡扣 |
| 透明视窗 | 透明 PETG + 不透明 ABS 壳体 | 预留装配槽，间隙 0.2mm |
| 导电触点 | 导电 PLA + 普通 PLA | 独立打印后装配 |
| 减震组件 | TPU 缓冲 + PLA 结构 | 过盈配合压入 |

### 多材料接合面设计

```python
# 燕尾槽接合（TPU 足垫 + PLA 腿部）
dovetail_angle = 60     # 燕尾角度
slot_depth = 2          # 槽深
slot_width = 8          # 槽宽

# PLA 腿部底面：开燕尾槽
with BuildSketch(leg.faces().sort_by(Axis.Z)[0]):
    with BuildLine():
        # 梯形轮廓（燕尾截面）
        Polyline(
            (-slot_width/2, 0),
            (-slot_width/2 + slot_depth * 0.577, slot_depth),
            (slot_width/2 - slot_depth * 0.577, slot_depth),
            (slot_width/2, 0),
            close=True
        )
    make_face()
extrude(amount=10)  # 槽长度

# TPU 足垫：对应的燕尾凸起（尺寸 +0.15mm 间隙）
```

---

## 8. 打印优化检查清单

| 检查项 | 通过标准 |
|--------|---------|
| 最小壁厚 | FDM ≥ 0.8mm, SLA ≥ 0.4mm |
| 悬臂角度 | ≤ 45° 或已加支撑/倒角 |
| 孔径补偿 | 已考虑收缩（FDM 孔径 +0.2mm） |
| 配合间隙 | 已按工艺设置间隙值 |
| 层高对齐 | 关键尺寸为层高整数倍 |
| 排液孔 | SLA 空心件已开排液孔 |
| 导出精度 | linear_tolerance 适合目标工艺 |
| 打印方向 | 已标注推荐打印方向 |
