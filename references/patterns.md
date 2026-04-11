# build123d 典型建模模式

## 1. 基础板 + 安装孔阵列

```python
from build123d import *

# 参数定义（所有尺寸放顶部）
plate_l, plate_w, plate_h = 80, 60, 6
hole_radius = 2.5
hole_x_spacing, hole_y_spacing = 20, 20
hole_x_count, hole_y_count = 3, 2

with BuildPart() as mount_plate:
    Box(plate_l, plate_w, plate_h)
    with GridLocations(hole_x_spacing, hole_y_spacing, hole_x_count, hole_y_count):
        Hole(radius=hole_radius)
    fillet(mount_plate.faces().sort_by(Axis.Z)[-1].edges(), radius=3)

export_step(mount_plate.part, "mount_plate.step")
```

---

## 2. 法兰盘 + 均布螺栓孔

```python
from build123d import *

flange_radius = 40
flange_height = 8
bolt_circle_radius = 30
bolt_radius = 4
bolt_count = 6
center_hole_radius = 15

with BuildPart() as flange:
    Cylinder(radius=flange_radius, height=flange_height)
    Hole(radius=center_hole_radius)
    with PolarLocations(radius=bolt_circle_radius, count=bolt_count):
        Hole(radius=bolt_radius)
    fillet(flange.faces().sort_by(Axis.Z)[-1].edges().filter_by(GeomType.CIRCLE), radius=1)

export_step(flange.part, "flange.step")
```

---

## 3. 凸台（Boss）

```python
from build123d import *

base_l, base_w, base_h = 50, 50, 5
boss_radius = 12
boss_height = 15

with BuildPart() as part:
    Box(base_l, base_w, base_h)
    with BuildSketch(part.faces().sort_by(Axis.Z)[-1]):
        Circle(boss_radius)
    extrude(amount=boss_height)
    fillet(part.edges().filter_by(Axis.Z), radius=2)

export_step(part, "boss_part.step")
```

---

## 4. 旋转体（轴对称零件）

```python
from build123d import *

with BuildPart() as shaft:
    with BuildSketch(Plane.XZ):
        with BuildLine():
            # 轮廓线（右侧，绕Z轴旋转）
            Polyline((5,0), (5,20), (8,20), (8,30), (6,30), (6,50), (0,50))
            Line((0,50), (0,0))
        make_face()
    revolve(axis=Axis.Z)

export_step(shaft, "shaft.step")
```

---

## 5. 拉伸切除（口袋/槽）

```python
from build123d import *

length, width, height = 60, 40, 20
pocket_l, pocket_w, pocket_depth = 40, 25, 12

with BuildPart() as pocket_part:
    Box(length, width, height)
    with BuildSketch(pocket_part.faces().sort_by(Axis.Z)[-1]):
        Rectangle(pocket_l, pocket_w)
    extrude(amount=-pocket_depth, mode=Mode.SUBTRACT)

export_step(pocket_part, "pocket.step")
```

---

## 6. 管道/扫掠路径

```python
from build123d import *

with BuildPart() as pipe:
    # 路径
    with BuildLine() as path:
        Line((0,0,0), (0,0,50))
        RadiusArc((0,0,50), (50,0,50), radius=30)
        Line((50,0,50), (50,0,0))
    # 截面（在路径起点的法平面上）
    with BuildSketch(Plane((0,0,0), (0,1,0))):
        Circle(5)
        Circle(4, mode=Mode.SUBTRACT)  # 空心管
    sweep(path=path.wires()[0])

export_step(pipe, "pipe.step")
```

---

## 7. 抽壳（薄壁件）

```python
from build123d import *

outer_l, outer_w, outer_h = 60, 40, 30
wall_thickness = 3

with BuildPart() as box_shell:
    Box(outer_l, outer_w, outer_h)
    shell(box_shell.faces().sort_by(Axis.Z)[-1], thickness=-wall_thickness)

export_step(box_shell, "shell_box.step")
```

---

## 8. L 形支架

```python
from build123d import *

# 参数
base_l, base_w, thickness = 60, 40, 6
rib_h = 40
fillet_r = 2

with BuildPart() as bracket:
    # 底板
    Box(base_l, base_w, thickness)
    # 竖板（在底板后边缘拉伸）
    with BuildSketch(bracket.faces().sort_by(Axis.Z)[-1]):
        with Locations(Pos(0, base_w/2 - thickness/2, 0)):
            Rectangle(base_l, thickness)
    extrude(amount=rib_h)
    # 所有竖边圆角
    fillet(bracket.edges().filter_by(Axis.Z), radius=fillet_r)

export_step(bracket, "bracket.step")
```

---

## 9. 沉头孔 / 内六角螺栓孔

```python
from build123d import *

plate_l, plate_w, plate_h = 80, 60, 10

with BuildPart() as cbore_plate:
    Box(plate_l, plate_w, plate_h)
    with GridLocations(30, 20, 2, 2):
        CounterBoreHole(
            radius=3,               # M6 通孔
            counter_bore_radius=5.5,  # 沉孔半径
            counter_bore_depth=6      # 沉孔深度
        )

export_step(cbore_plate, "cbore_plate.step")
```

---

## 10. 代数模式 — 快速组合

```python
from build123d import *

# 直接用运算符组合
housing = (
    Box(50, 50, 30)
    - Cylinder(radius=15, height=30)                        # 内孔
    - Box(30, 50, 10, align=(Align.CENTER, Align.CENTER, Align.MAX))  # 开口槽
)

# 圆角
result = fillet(housing.edges().filter_by(GeomType.CIRCLE), radius=1)

export_step(result, "housing.step")
```

---

## 11. 直齿圆柱齿轮（根圆柱 + 逐齿 Algebra Mode 融合）

**适用场景**：任何需要多边形轮廓拉伸且轮廓高度非凸的零件（齿轮、凸轮等）

**关键原则**：不要一次性拉伸全部轮廓。用「根实体 + N 个小特征融合」代替「一个大多边形拉伸」，避免 OCP viewer 的 Three.js 三角化器跳过复杂非凸面。

```python
"""
直齿圆柱齿轮 / Spur Gear — 根圆柱 + 逐齿融合（OCP viewer 兼容）
⚠️ 不要用单一 300 点多边形拉伸：OCP viewer 会忽略顶底面（face ignored）
"""
from build123d import *
from OCP.OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
from OCP.OCP.gp import gp_Pln, gp_Pnt, gp_Dir
import math

# ===== 参数 =====
module      = 2        # 模数 m（越大齿越粗）
teeth       = 20       # 齿数 z
face_width  = 12       # 齿宽 mm
shaft_r     = 4        # 轴孔半径 mm
keyway_w    = 2.0      # 键槽宽 mm（0 = 无）
pressure_a  = 20       # 压力角 °（标准 20°）

# ===== 计算 =====
pitch_r    = module * teeth / 2
addendum_r = pitch_r + module
root_r     = pitch_r - 1.25 * module
base_r     = pitch_r * math.cos(math.radians(pressure_a))
pitch_a    = 2 * math.pi / teeth
half_t     = math.pi / (2 * teeth)

XY_PLANE   = gp_Pln(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1))

def make_planar_face(pts_2d):
    """从 2D 点列表创建平面 Face（显式指定 XY 平面）"""
    wire = Wire.make_polygon([(x, y, 0) for x, y in pts_2d], close=True)
    return Face(BRepBuilderAPI_MakeFace(XY_PLANE, wire.wrapped, True).Face())

def tooth_pts(i, steps=8):
    """第 i 个齿的 2D 轮廓（仅齿根圆以上的凸起，约 20 点，近似凸形）"""
    a_i      = pitch_a * i
    inv_max  = math.sqrt(max(0, (addendum_r / base_r) ** 2 - 1))

    left = []
    for s in range(steps + 1):
        ia = inv_max * s / steps
        r  = min(base_r * math.sqrt(1 + ia ** 2), addendum_r)
        if r < root_r:
            continue
        th = a_i + half_t - ia + math.atan(ia)
        left.append((r * math.cos(th), r * math.sin(th)))

    right = []
    for s in range(steps, -1, -1):
        ia = inv_max * s / steps
        r  = min(base_r * math.sqrt(1 + ia ** 2), addendum_r)
        if r < root_r:
            continue
        th = a_i - half_t + ia - math.atan(ia)
        right.append((r * math.cos(th), r * math.sin(th)))

    if not left or not right:
        return None

    # 齿根弧收口（右侧 → 左侧，短弧）
    th_r = math.atan2(right[-1][1], right[-1][0])
    th_l = math.atan2(left[0][1],  left[0][0])
    if th_l < th_r:
        th_l += 2 * math.pi
    arc = [(root_r * math.cos(th_r + (th_l - th_r) * k / 4),
            root_r * math.sin(th_r + (th_l - th_r) * k / 4))
           for k in range(1, 4)]
    return left + right + arc

# ===== 建模：Algebra Mode =====
# Cylinder 以原点为中心（z = -h/2 到 +h/2）
gear = Cylinder(radius=root_r, height=face_width)

for i in range(teeth):
    pts = tooth_pts(i)
    if pts is None:
        continue
    f = make_planar_face(pts)
    with BuildPart() as tooth:
        # ⚠️ 草图偏移 -face_width/2，与 Cylinder 中心对齐（否则高度变 1.5×）
        with BuildSketch(Plane.XY.offset(-face_width / 2)):
            add(f)
        extrude(amount=face_width)
    gear = gear + tooth.part

# 轴孔 + 键槽
gear = gear - Cylinder(radius=shaft_r, height=face_width)
if keyway_w > 0:
    slot_depth = shaft_r + keyway_w * 1.2
    gear = gear - Box(keyway_w, slot_depth, face_width).moved(
        Location((0, slot_depth / 2, 0))
    )

# ===== 验证 =====
bb = gear.bounding_box()
print(f"尺寸: {bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f} mm")
print(f"体积: {gear.volume:.2f} mm³")

# ===== 导出 =====
export_step(gear, "gear_spur.step")
```

**调参指引**

| 变量 | 效果 |
|------|------|
| `module` | 齿的粗细（模数越大，齿越粗，传递力越大） |
| `teeth` | 齿数（越多越接近圆柱，传动比越精细） |
| `face_width` | 齿宽（越宽承载能力越大，一般取 8–15× module） |
| `shaft_r` | 轴孔半径（与配对轴直径一致） |
| `steps` | 渐开线采样点数（越多齿形越精确，6–12 即可） |
