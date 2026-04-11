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
