# 激光切割设计规则

> 2D 轮廓提取、切缝补偿、DXF 导出完整流程。

---

## 1. 2D 轮廓提取

```python
from build123d import *

# 方法 1：直接在 BuildSketch 中设计 2D 轮廓
with BuildSketch() as panel:
    Rectangle(200, 150)
    with GridLocations(60, 40, 3, 3):
        Circle(5, mode=Mode.SUBTRACT)    # 阵列孔

export_dxf(panel.sketch, "panel.dxf")

# 方法 2：从 3D 零件截取截面
with BuildPart() as box:
    Box(100, 80, 20)
    Hole(radius=10)

# 在 Z=10 处截取截面
section_plane = Plane.XY.offset(10)
section = box.part.section(section_plane)
export_dxf(section, "box_section.dxf")
```

---

## 2. 切缝补偿

| 激光类型 | 典型切缝宽度 | 补偿量（每侧） |
|---------|------------|--------------|
| CO2 激光 | 0.15-0.25mm | ~0.1mm |
| 光纤激光 | 0.08-0.12mm | ~0.05mm |
| 紫外激光 | 0.03-0.05mm | ~0.02mm |

### 在 build123d 中补偿切缝

```python
from build123d import *

kerf = 0.2            # CO2 激光切缝
half_kerf = kerf / 2

# 外轮廓向外偏移（实际切出尺寸更大）
with BuildSketch() as outer:
    Rectangle(100 + kerf, 80 + kerf)  # 外廓 +kerf

# 内轮廓（孔）向内偏移（实际切出孔更小）
# 或使用 offset()
with BuildSketch() as panel:
    Rectangle(100, 80)
    with Locations((0, 0)):
        Circle(10 - half_kerf, mode=Mode.SUBTRACT)  # 孔径 -补偿

export_dxf(panel.sketch, "panel_compensated.dxf")
```

> **注意**：大多数激光切割机软件（如 LightBurn、RDWorks）内置切缝补偿功能。
> 如果下游软件会处理补偿，则 build123d 导出名义尺寸即可。

---

## 3. 最小特征尺寸

| 约束 | 值 | 说明 |
|------|-----|------|
| 最小孔径 | ≥ 材料厚度 | 薄板: Ø ≥ t |
| 最小间距 | ≥ 材料厚度 | 特征间距 ≥ t |
| 最小凸台宽度 | ≥ 材料厚度 × 0.8 | 窄凸台容易变形 |
| 最小文字 | 字高 ≥ 3mm | 取决于材料和激光功率 |
| 最小圆角 | R ≥ 0.5mm | 尖角会产生过烧 |

---

## 4. 材料对应

| 材料 | 常见厚度 | 适合激光 | 注意事项 |
|------|---------|---------|---------|
| 亚克力（PMMA） | 1-20mm | CO2 | 切口光滑，可抛光 |
| 密度板/木板 | 2-10mm | CO2 | 边缘焦化正常 |
| 碳钢板 | 0.5-20mm | 光纤 | 需氧气辅助 |
| 不锈钢 | 0.5-10mm | 光纤 | 需氮气辅助（无氧化） |
| 铝板 | 0.5-8mm | 光纤 | 反射率高，需高功率 |
| PCB（FR4） | 0.8-1.6mm | 紫外 | 精细切割，无碳化 |

---

## 5. DXF 导出工作流

### 完整流程

```python
from build123d import *

# Step 1: 设计 2D 轮廓
with BuildSketch() as bracket:
    # 外轮廓
    Rectangle(120, 80)
    fillet(bracket.vertices(), radius=5)
    
    # 安装孔
    with GridLocations(90, 50, 2, 2):
        Circle(3.5, mode=Mode.SUBTRACT)  # M6 通孔
    
    # 中心开口
    Rectangle(40, 30, mode=Mode.SUBTRACT)
    
    # 弯折线（用于钣金折弯标记）
    # 弯折线通常用极细线条表示，不切透

# Step 2: 导出 DXF
export_dxf(bracket.sketch, "bracket_laser.dxf")
```

### 从 3D 零件提取激光切割 2D 图

```python
# 板材零件 → 提取中面轮廓
with BuildPart() as plate:
    Box(120, 80, 3)           # 3mm 板材
    with GridLocations(90, 50, 2, 2):
        Hole(radius=3.5)
    fillet(plate.faces().sort_by(Axis.Z)[-1].edges(), radius=5)

# 截取中面
mid_section = plate.part.section(Plane.XY)
export_dxf(mid_section, "plate_laser.dxf")
```

---

## 6. 激光切割检查清单

| 检查项 | 通过标准 |
|--------|---------|
| 轮廓封闭 | 所有切割轮廓必须是封闭曲线 |
| 最小特征 | 孔径 ≥ 板厚，间距 ≥ 板厚 |
| 尖角处理 | 内角 R ≥ 0.5mm |
| 切缝补偿 | 已确认补偿方式（设计端 vs 切割机端） |
| 文件格式 | DXF（AutoCAD 兼容） |
| 单位 | mm（DXF 中确认单位正确） |
