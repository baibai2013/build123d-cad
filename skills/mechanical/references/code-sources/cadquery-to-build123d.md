# CadQuery → build123d 翻译规则

> **为什么要翻译**：GitHub 上 CadQuery 代码数量是 build123d 的 2~3 倍，很多齿轮/曲面/装配的成熟例子只有 CadQuery 版。
> **好消息**：build123d 作者 Roger Maitland 就是 CadQuery 前核心维护者，两者**底层都是 OpenCASCADE**，API 对应度 ~80%。
> **使用建议**：找到对应 CadQuery 代码 → 对照本文件规则机械翻译 → OCP 验证几何等价。

---

## 总体差异（先理解哲学）

| 方面 | CadQuery | build123d |
|------|---------|-----------|
| **DSL 风格** | 链式调用（Fluent API）：`.extrude().fillet().hole()` | Builder 模式（context manager）：`with BuildPart():` + 语句 |
| **当前对象** | 隐式栈（`.faces(">Z").workplane().rect(10,10)`） | 显式上下文（`with BuildSketch(face)`） |
| **选择器** | 字符串 DSL：`.faces(">Z")`、`.edges("|Z")` | Python 选择器：`part.faces().sort_by(Axis.Z)[-1]` |
| **装配** | `cq.Assembly()` | `Compound(children=[...])` + Joints |
| **约束求解** | 无原生约束 | 无原生约束（同哲学） |
| **模式并存** | 单一 Fluent | **Builder + Algebra** 两模式 |

**关键洞察**：build123d 是 CadQuery 的"Pythonic 版"，把隐式栈换成了显式作用域。

---

## API 映射表（高频先）

### 1️⃣ 几何创建

| CadQuery | build123d | 注意 |
|----------|-----------|------|
| `cq.Workplane("XY")` | `with BuildPart():` | context manager 必须 |
| `cq.Workplane("XY").box(l, w, h)` | `with BuildPart(): Box(l, w, h)` | Box 是顶级类 |
| `cq.Workplane().circle(r)` | `with BuildSketch(): Circle(r)` | 草图独立上下文 |
| `cq.Sketch()` | `with BuildSketch():` | 同上 |
| `cq.Workplane().rect(w, h)` | `with BuildSketch(): Rectangle(w, h)` | Rectangle 替代 rect |
| `cq.Workplane().polygon(6, 10)` | `with BuildSketch(): RegularPolygon(5, side_count=6)` | 参数顺序差异：build123d 先半径后边数 |

### 2️⃣ 操作

| CadQuery | build123d | 注意 |
|----------|-----------|------|
| `.extrude(10)` | `extrude(amount=10)` | **参数名必填**；build123d 拒绝位置参 |
| `.extrude(-5, combine="s")` | `extrude(amount=-5, mode=Mode.SUBTRACT)` | Mode.SUBTRACT 替代字符串 |
| `.cutBlind(10)` | `extrude(amount=-10, mode=Mode.SUBTRACT)` | 统一语义 |
| `.revolve(angle, axis)` | `revolve(axis=Axis.Z, revolution_arc=angle)` | 参数名+默认 360° |
| `.sweep(path)` | `sweep(path=path)` | 参数名必填 |
| `.loft(combine=True)` | `loft()` | Builder 内自动合并 |
| `.shell(t)` | `offset(amount=-t, openings=<face>)` | **⚠️ shell() 未导出！** 用 offset |
| `.fillet(r)` | `fillet(edges, radius=r)` | 需先选 edges |
| `.chamfer(d)` | `chamfer(edges, length=d)` | 同上 |

### 3️⃣ 孔

| CadQuery | build123d | 注意 |
|----------|-----------|------|
| `.hole(d)` | `Hole(radius=d/2)` | build123d 用**半径**，CadQuery 用直径 |
| `.cboreHole(d, cd, ch)` | `CounterBoreHole(radius=d/2, counter_bore_radius=cd/2, counter_bore_depth=ch)` | 参数全量命名 |
| `.cskHole(d, cd, angle)` | `CounterSinkHole(radius=d/2, counter_sink_radius=cd/2, counter_sink_angle=angle)` | 同上 |

### 4️⃣ 选择器（重点，最容易踩坑）

| CadQuery | build123d | 含义 |
|----------|-----------|------|
| `.faces(">Z")` | `part.faces().sort_by(Axis.Z)[-1]` | 顶面（Z 最大） |
| `.faces("<Z")` | `part.faces().sort_by(Axis.Z)[0]` | 底面 |
| `.edges("\|Z")` | `part.edges().filter_by(Axis.Z)` | 所有平行 Z 的边 |
| `.edges(">Z and <X")` | 组合 `sort_by` + `filter_by`（写多行） | 复合选择需分解 |
| `.faces("%CIRCLE")` | `part.faces().filter_by(GeomType.CIRCLE)` | 圆面 |
| `.edges(tag="myedge")` | build123d 无 tag DSL，用保存引用 | 改思路 |

### 5️⃣ 位置与变换

| CadQuery | build123d | 注意 |
|----------|-----------|------|
| `.translate((x,y,z))` | `Pos(x, y, z) * shape` 或 `.move(Location((x,y,z)))` | Algebra Mode 用 `*` |
| `.rotate((0,0,0), (0,0,1), 90)` | `Rot(0, 0, 90) * shape` | 欧拉角直接传 |
| `.asLocation()` | `Location((x,y,z), (rx,ry,rz))` | 构造器直接传 |
| `cq.Plane.named("XY")` | `Plane.XY` | 类属性 |
| `Plane.XY.offset(10)` | `Plane.XY.offset(10)` | 相同 ✓ |

### 6️⃣ 阵列 / 多位置

| CadQuery | build123d | 注意 |
|----------|-----------|------|
| `.rarray(xs, ys, nx, ny)` | `with GridLocations(xs, ys, nx, ny):` | context manager |
| `.polarArray(r, angleStart, angleTotal, count)` | `with PolarLocations(radius=r, count=count):` | 参数简化 |
| `.pushPoints([(x1,y1), (x2,y2)])` | `with Locations((x1,y1), (x2,y2)):` | 可变参 |

### 7️⃣ 布尔

| CadQuery | build123d | 注意 |
|----------|-----------|------|
| `.cut(other)` | `part - other` (Algebra) 或 `mode=Mode.SUBTRACT` | 两种写法 |
| `.union(other)` | `part + other` 或 `mode=Mode.ADD`（默认） | |
| `.intersect(other)` | `part & other` 或 `mode=Mode.INTERSECT` | |

### 8️⃣ 装配

| CadQuery | build123d | 注意 |
|----------|-----------|------|
| `cq.Assembly()` | `Compound(children=[...])` | 用 list 传入 |
| `.add(part, name="x")` | `part.label = "x"` + `Compound([...])` | 命名分离 |
| CadQuery 无 Joint | `RigidJoint / RevoluteJoint / BallJoint` | build123d 有 5 种 Joint |
| `.constrain(...)` | 无约束求解器，手动 `.connect_to()` 编排 | **两库哲学相同：不支持求解器** |

### 9️⃣ 导出

| CadQuery | build123d | 注意 |
|----------|-----------|------|
| `cq.exporters.export(result, "f.step")` | `export_step(part.part, "f.step")` | ⚠️ **传 `.part` 属性** 不是 BuildPart 对象 |
| `cq.exporters.export(..., "f.stl")` | `export_stl(part.part, "f.stl")` | 同上 |
| `cq.exporters.export(..., "f.dxf")` | `export_dxf(sketch.sketch, "f.dxf")` | 2D 导 `.sketch` |

---

## 易混点（5 条）

### 1. `Plane.z_dir` 是平面**法向**，不是草图"朝上"方向
CadQuery 的 `Plane` 直接以名字定位（"XY"/"XZ"/"YZ"）；build123d 的 `Plane(origin, z_dir=...)` 的 z_dir 是法向量。
- `Plane.XZ.offset(10)` 返回 origin=(0,-10,0)、**z_dir=(0,-1,0)**，不是 (0,0,1)
- 新手常以为 z_dir 是"朝上"，实际是法向朝外

### 2. `Location` vs `Rotation` 顺序
`Location((x,y,z), (rx,ry,rz))` — 两个 tuple，第一个是平移、第二个是欧拉角（degrees）。CadQuery 用 `Vector + angle + axis`，build123d 扁平化传参。

### 3. `mode=Mode.SUBTRACT` 是 build123d 独有语义
Builder Mode 里每个操作都有 `mode=` 参数控制合并方式（ADD/SUBTRACT/INTERSECT/REPLACE/PRIVATE）。CadQuery 里用字符串 `"s"`/`"a"`/`"i"`，语义一致但不直译。

### 4. `angular_range` 是**degrees**不是 radians
`RevoluteJoint(angular_range=(-45, 90))` 是度数；不要手工 `math.radians()`。

### 5. `part.is_valid` 是**属性**不是方法
```python
# ❌ part.is_valid()   → 报错：bool is not callable
# ✅ part.is_valid     → 正确
```

---

## 翻译工作流

收到 CadQuery 代码后：

1. **扫一遍识别操作**：extrude/fillet/hole/选择器 → 对照映射表
2. **逐行改写**：
   - 链式 `.xxx().yyy()` → 拆成 Builder 内多语句
   - 字符串选择器 → Python 选择器
   - 位置参 → 命名参
3. **注意 shell / is_valid / export_step(.part) 三大坑**
4. **OCP 验证几何等价**：分别 export STEP，对比体积与 bounding box；差异 > 0.1% 要定位
5. **不可直译项**（见下方）→ 走原生 build123d 路径

---

## 必须改写而非翻译的项

### CadQuery 的 `makeRuledSurface` / `makeSplineApprox`
build123d 无直接对应。改写策略：
- `makeRuledSurface(edge1, edge2)` → `Face.make_surface_from_curves([edge1, edge2])`（需核对 API）
- `makeSplineApprox(points)` → `Edge.make_spline(points)` + `make_face()`

### CadQuery 的 tagged selectors
```python
.faces(tag="top")   # CadQuery
```
build123d 无 tag DSL。改用**保存引用**：
```python
with BuildPart() as p:
    Box(10, 10, 10)
    top = p.faces().sort_by(Axis.Z)[-1]   # 保存引用
    # 后续使用 top
```

### CadQuery 的 `.sketch().reset()` / `.faces().workplane()`
`reset` 在 build123d 无对应。改用 **显式 `BuildSketch(some_face)`** 重新开上下文：
```python
# CadQuery: .faces(">Z").workplane().circle(5).extrude(3)
# build123d:
top = part.faces().sort_by(Axis.Z)[-1]
with BuildSketch(top):
    Circle(5)
extrude(amount=3)
```

---

## 翻译示例（完整）

### CadQuery 原代码

```python
import cadquery as cq

result = (
    cq.Workplane("XY")
    .box(80, 60, 10)
    .faces(">Z")
    .workplane()
    .pushPoints([(-20, -10), (20, -10), (-20, 10), (20, 10)])
    .hole(5)
    .edges("|Z")
    .fillet(3)
)
cq.exporters.export(result, "plate.step")
```

### build123d 翻译

```python
from build123d import *

with BuildPart() as plate:
    Box(80, 60, 10)
    # 选顶面打孔：保存引用便于后续
    top = plate.faces().sort_by(Axis.Z)[-1]
    with BuildSketch(top):
        with Locations((-20, -10), (20, -10), (-20, 10), (20, 10)):
            Circle(2.5)   # CadQuery hole(5) 是直径，build123d Circle(r) 是半径
    extrude(amount=-10, mode=Mode.SUBTRACT)
    fillet(plate.edges().filter_by(Axis.Z), radius=3)

export_step(plate.part, "plate.step")   # ⚠️ .part 属性
```

**差异点清单**：
- `.box()` → `Box()`
- `.faces(">Z").workplane()` → `BuildSketch(top)`（保存引用）
- `.pushPoints(...)` → `with Locations(...):`
- `.hole(5)` → `Circle(2.5)` + `extrude(mode=Mode.SUBTRACT)`（半径转换 + Mode 显式）
- `.edges("|Z")` → `.edges().filter_by(Axis.Z)`
- `.fillet(3)` → `fillet(edges, radius=3)`
- `exporters.export(result, ...)` → `export_step(plate.part, ...)`（`.part` 属性）

---

## 翻译成本估计

| CadQuery 代码类型 | 翻译成本 | 说明 |
|-----------------|---------|------|
| 纯 Box/Cylinder/hole/fillet | 零 | 1:1 对应，机械翻译 |
| 选择器 + 拉伸 + 切除 | 低 | 查表逐行替换 |
| Loft / Sweep 曲面 | 中 | Builder 上下文要拆分 |
| tag + 复杂选择器 | 中-高 | 需保存引用重构 |
| makeRuledSurface / splineApprox | 高 | 无对应 API，走原生路径 |
| 带约束求解器的装配 | n/a | 两库都不支持求解器 |

---

## 验证翻译正确性

```bash
# 两个版本分别导出 STEP，用 step_info.py 比较
python3 $SKILL/scripts/analysis/step_info.py cq_version.step
python3 $SKILL/scripts/analysis/step_info.py b3d_version.step

# 体积差异 < 0.1% 认为翻译正确
```
