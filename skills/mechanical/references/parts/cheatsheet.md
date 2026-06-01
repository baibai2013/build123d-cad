# build123d API Cheat Sheet

## 安装

```bash
pip install build123d
pip install ocp_vscode  # VS Code 实时预览
```

## 必写的导入

```python
from build123d import *
```

---

## 两种建模范式

### Builder Mode（推荐，LLM 幻觉率更低）

```python
with BuildPart() as part:
    Box(10, 10, 5)
    Cylinder(radius=3, height=6, mode=Mode.SUBTRACT)
    fillet(part.edges().filter_by(Axis.Z), radius=0.5)
```

三个 Builder 上下文：
- `BuildPart()` — 3D 实体
- `BuildSketch()` — 2D 草图
- `BuildLine()` — 线/线框

### Algebra Mode（运算符组合）

```python
box = Box(10, 10, 5)
cyl = Cylinder(radius=3, height=6)
result = box - cyl        # 差集
result2 = box + cyl       # 并集
result3 = box & cyl       # 交集
```

---

## Mode 参数（Builder Mode 专用）

| Mode | 含义 |
|------|------|
| `Mode.ADD`（默认） | 加入上下文 |
| `Mode.SUBTRACT` | 从上下文减去 |
| `Mode.INTERSECT` | 与上下文求交 |
| `Mode.PRIVATE` | 创建但不加入 |
| `Mode.REPLACE` | 替换上下文 |

---

## 3D 形状

```python
Box(length, width, height)
Cylinder(radius, height)
Cone(bottom_radius, top_radius, height)
Sphere(radius)
Torus(major_radius, minor_radius)
Wedge(xsize, ysize, zsize, xmin, zmin, xmax, zmax)
```

## 2D 形状（在 BuildSketch 内使用）

```python
Circle(radius)
Rectangle(width, height)
RectangularArray(x_spacing, y_spacing, x_count, y_count)  # 矩形阵列草图
Polygon(n_sides, radius)
Ellipse(x_radius, y_radius)
RegularPolygon(radius, side_count)
SlottedHole(length, radius)
```

---

## 操作

```python
# 拉伸
extrude(amount=10)
extrude(amount=10, taper=5)      # 带拔模角
extrude(amount=10, both=True)    # 双向拉伸
extrude(amount=-5, mode=Mode.SUBTRACT)  # 向下切除

# 旋转
revolve(axis=Axis.Z)             # 绕Z轴旋转360°
revolve(revolution_arc=90, axis=Axis.Z)  # 旋转90°

# 扫掠
sweep(path=path_wire)

# 放样
loft([sketch1, sketch2, sketch3])

# 抽壳
shell(part.faces().sort_by(Axis.Z)[-1], thickness=-2)  # 顶面开口，壁厚2mm

# 圆角
fillet(edges, radius=2)

# 倒角
chamfer(edges, length=1)
chamfer(edges, length=1, length2=2)  # 非对称倒角

# 孔（直通）
Hole(radius=3)
Hole(radius=3, depth=10)         # 盲孔

# 沉孔
CounterBoreHole(radius=3, counter_bore_radius=5, counter_bore_depth=3)

# 锥孔
CounterSinkHole(radius=3, counter_sink_radius=5, counter_sink_angle=82)
```

---

## 拓扑选择器（核心！）

```python
# 访问
part.vertices()
part.edges()
part.faces()
part.wires()
part.solids()

# filter_by — 过滤
part.edges().filter_by(Axis.Z)              # 平行于Z轴的边（竖边）
part.edges().filter_by(Axis.X)              # 平行于X轴的边
part.faces().filter_by(Axis.Z)              # 法向量平行Z轴的面（顶/底面）
part.edges().filter_by(GeomType.CIRCLE)     # 圆弧边
part.edges().filter_by(GeomType.LINE)       # 直线边
part.faces().filter_by(GeomType.CYLINDER)   # 柱面
part.edges().filter_by(lambda e: e.length > 5)  # 长度>5的边

# sort_by — 排序（返回列表，用[-1]取最后/最大）
part.faces().sort_by(Axis.Z)[-1]            # 最高面（顶面）
part.faces().sort_by(Axis.Z)[0]             # 最低面（底面）
part.edges().sort_by(SortBy.LENGTH)[-1]     # 最长边
part.faces().sort_by(SortBy.AREA)[-1]       # 最大面
part.edges().sort_by(SortBy.RADIUS)[-1]     # 最大圆弧半径

# group_by — 分组
part.edges().group_by(Axis.Z)[-1]           # 最高一组边

# 链式调用
part.faces().sort_by(Axis.Z)[-1].edges()    # 顶面的所有边
part.faces().sort_by(Axis.Z)[-1].edges().filter_by(Axis.X)  # 顶面的X向边
```

---

## 位置与阵列

```python
# 基本位置
Pos(x, y, z)                    # 平移
Rot(x_deg, y_deg, z_deg)        # 旋转
Location((x,y,z))               # 位置
Plane.XY.offset(10)             # 偏移平面

# 阵列 — 在 with 块内自动复制所有子形状
with GridLocations(x_spacing=20, y_spacing=20, x_count=3, y_count=3):
    Cylinder(radius=3, height=5)

with PolarLocations(radius=20, count=6):
    Hole(radius=3)

with HexLocations(apothem=10, x_count=3, y_count=3):
    Cylinder(radius=4, height=5)

with Locations((0,0,0), (10,0,0), (20,0,0)):
    Hole(radius=2)
```

---

## 平面（在哪个面上建模）

```python
Plane.XY                         # 默认
Plane.XZ
Plane.YZ
Plane.XY.offset(10)             # Z=10 处的平面

# 在零件的特定面上建模（最常用）
with BuildSketch(part.faces().sort_by(Axis.Z)[-1]):  # 顶面
    Circle(5)
extrude(amount=5)
```

---

## 导出

```python
export_step(part.part, "output.step")                            # ⚠️ 注意：传 .part，不是 BuildPart 上下文
export_step(part.part, "output.step", precision_mode=PrecisionMode.GREATEST)

export_stl(part.part, "output.stl")
export_stl(part.part, "output.stl", linear_tolerance=0.001, angular_tolerance=0.1)

export_brep(part.part, "output.brep")    # OCC 原生，无损
export_dxf(sketch.sketch, "output.dxf") # 2D，激光切割（传 .sketch）
export_3mf(part.part, "output.3mf")     # 3D打印制造格式
export_gltf(part.part, "output.gltf")   # 可视化

# Algebra Mode 下直接传对象（不需要 .part）
box = Box(10, 10, 10)
export_step(box, "output.step")          # Algebra Mode：直接传形状对象
```

---

## 导入

```python
import_step("input.step")
import_brep("input.brep")
import_svg("input.svg")
```

---

## 常见错误预防

| 错误写法（幻觉） | 正确写法 |
|---------------|---------|
| `part.top_face()` | `part.faces().sort_by(Axis.Z)[-1]` |
| `part.bottom_face()` | `part.faces().sort_by(Axis.Z)[0]` |
| `Box(10, 10, 10).fillet(1)` | `fillet(box.edges(), radius=1)` |
| `Hole(radius=3, through=True)` | `Hole(radius=3)` （无 through 参数） |
| `extrude(sketch, 10)` | `extrude(amount=10)` （Builder Mode 内不传 sketch） |
| `part.add(box)` | `mode=Mode.ADD`（默认）|
| `part.subtract(cyl)` | `mode=Mode.SUBTRACT` 或 `-` 运算符 |
| `export_step(part, "f.step")` | `export_step(part.part, "f.step")` （传 .part 属性）|
