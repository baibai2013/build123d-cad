# 装配模式参考

> 8 种装配模式 + 决策树，从单体零件到大型装配的完整路径。

---

## 1. Compound + Label + children — 基础装配

最简单的装配方式：把多个零件组合成一个 Compound，用 `label` 命名。

```python
from build123d import *

box = Box(10, 10, 10)
box.label = "base"
cyl = Cylinder(5, 20)
cyl.label = "column"

assembly = Compound(children=[box, Pos(0, 0, 15) * cyl])
assembly.label = "assembly"
export_step(assembly, "assembly.step")
```

**要点**：
- `label` 是 STEP 文件中的零件名，也是 OCP Viewer 树中的节点名
- `children` 列表中的形状可以先做 Location 变换再传入
- 导出的 STEP 文件保留装配层级

---

## 2. Joint 驱动装配 — connect_to 自动定位

用关节语义描述装配关系，`connect_to` 自动计算零件位置。

```python
from build123d import *
from ocp_vscode import show

base = Box(50, 50, 10)
base.label = "base"
RigidJoint("top", base, Location((0, 0, 5)))

arm = Box(10, 10, 40)
arm.label = "arm"
RigidJoint("bottom", arm, Location((0, 0, -20)))

base.joints["top"].connect_to(arm.joints["bottom"])
show(base, arm)
```

**关节类型一览**：

| 关节类型 | 自由度 | 典型用途 |
|----------|--------|---------|
| `RigidJoint` | 0 | 螺丝固定、焊接 |
| `RevoluteJoint` | 1（旋转） | 铰链、舵机关节 |
| `LinearJoint` | 1（平移） | 滑轨、升降台 |
| `CylindricalJoint` | 2（旋转+平移） | 液压缸 |
| `BallJoint` | 3（三轴旋转） | 万向节 |

**RevoluteJoint 示例**：

```python
from build123d import *
from ocp_vscode import show

upper = Box(10, 10, 40)
upper.label = "upper_leg"
RevoluteJoint("knee", upper, Location((0, 0, -20)),
              axis=Axis.Y, angular_range=(-90, 0))

lower = Box(10, 10, 35)
lower.label = "lower_leg"
RigidJoint("top", lower, Location((0, 0, 17.5)))

upper.joints["knee"].connect_to(lower.joints["top"])
show(upper, lower)
```

---

## 3. Location 算术 — Pos * Rot * Shape 链式变换

直接用 Location 运算组合零件位置，不依赖关节系统。

```python
from build123d import *

base = Box(80, 60, 5)
base.label = "base"

# 四角立柱
pillar = Cylinder(3, 30)
pillar.label = "pillar"

pillars = []
for x, y in [(-30, -20), (30, -20), (-30, 20), (30, 20)]:
    p = Pos(x, y, 17.5) * pillar
    pillars.append(p)

# 顶板旋转 45 度放置
top = Pos(0, 0, 35) * Rot(0, 0, 45) * Box(50, 50, 3)
top.label = "top_plate"

assembly = Compound(children=[base] + pillars + [top])
assembly.label = "frame"
export_step(assembly, "frame.step")
```

**变换顺序规则**：
- `Pos(x, y, z) * Rot(rx, ry, rz) * Shape` — 先旋转后平移（最常用）
- `Rot(rx, ry, rz) * Pos(x, y, z) * Shape` — 先平移后旋转（绕原点旋转）
- 多次变换从右到左依次作用

---

## 4. 浅拷贝批量装配 — copy.copy() 节省内存

当装配体包含大量相同零件时，用浅拷贝避免几何数据重复。

```python
import copy
from build123d import *

# 建模一个复杂零件
with BuildPart() as bolt:
    Cylinder(2, 10)
    with BuildSketch(bolt.faces().sort_by(Axis.Z)[-1]):
        RegularPolygon(4, 6)
    extrude(amount=3)
bolt_shape = bolt.part
bolt_shape.label = "bolt"

# 浅拷贝 100 个（共享底层几何）
positions = [(x * 15, y * 15, 0) for x in range(10) for y in range(10)]
copies = []
for i, (x, y, z) in enumerate(positions):
    c = copy.copy(bolt_shape)
    c.label = f"bolt_{i}"
    copies.append(Pos(x, y, z) * c)

assembly = Compound(children=copies)
assembly.label = "bolt_array"
export_step(assembly, "bolt_array.step")
```

**内存对比**：

| 方式 | 100 个零件内存 |
|------|---------------|
| 每次重新建模 | ~51 MB |
| `copy.copy()` | ~550 KB |

**注意**：`copy.copy()` 是浅拷贝，修改副本几何会影响所有副本。如需独立修改，用 `copy.deepcopy()`。

---

## 5. 碰撞检测 — do_children_intersect()

装配后检查零件是否有干涉。

```python
from build123d import *

box1 = Pos(-4, 0, 0) * Box(10, 10, 10)
box1.label = "part_a"
box2 = Pos(4, 0, 0) * Box(10, 10, 10)
box2.label = "part_b"

assembly = Compound(children=[box1, box2])

# 检查所有子体是否有交叉
has_interference = assembly.do_children_intersect()
print(f"干涉检测: {'有干涉!' if has_interference else '无干涉'}")

# 输出: 干涉检测: 有干涉!（两个盒子重叠了 2mm）
```

**实际应用**：
- 装配定位后自动验证无碰撞
- 检查运动包络线（把关节极限位置都检查一遍）
- 导出前做最终干涉检查

---

## 6. 打印排版 — pack() 函数

把多个零件自动排列到打印平台上。

```python
from build123d import *

# 建模多个零件
parts = [
    Box(20, 30, 5),
    Cylinder(10, 5),
    Box(15, 15, 5),
    Cylinder(8, 5),
]

# 自动排版（间距 5mm）
packed = pack(parts, padding=5)

# packed 是一个 Compound，零件已自动平铺排列
export_step(packed, "print_layout.step")
export_stl(packed, "print_layout.stl")
```

**参数说明**：

| 参数 | 含义 | 默认值 |
|------|------|--------|
| `padding` | 零件间距 (mm) | 1 |

**提示**：`pack()` 基于 2D 包围盒排列，不考虑高度。适合同一批次打印的零件排版。

---

## 7. show_topology() — 查看装配层级

打印装配体的拓扑树结构，用于调试。

```python
from build123d import *

box = Box(10, 10, 10)
box.label = "base"
cyl = Cylinder(5, 20)
cyl.label = "column"

assembly = Compound(children=[box, Pos(0, 0, 15) * cyl])
assembly.label = "assembly"

# 打印拓扑层级
assembly.show_topology()
```

输出示例：
```
Compound        assembly
├── Solid       base
└── Solid       column
```

**用途**：
- 确认 `label` 正确赋值
- 确认零件层级关系
- 排查 `export_step` 后零件丢失的问题

---

## 8. 大型装配管理 — 30+ 件组织策略

### 子装配分层

```python
from build123d import *

# ===== 层级 1：子装配 =====
# 底座子装配
base_plate = Box(100, 100, 5)
base_plate.label = "base_plate"
standoff = Cylinder(3, 15)
standoffs = []
for x, y in [(-40, -40), (40, -40), (-40, 40), (40, 40)]:
    s = Pos(x, y, 10) * standoff
    standoffs.append(s)
base_asm = Compound(children=[base_plate] + standoffs)
base_asm.label = "base_assembly"

# 电机子装配
motor_body = Cylinder(15, 30)
motor_body.label = "motor_body"
shaft = Cylinder(3, 10)
shaft.label = "shaft"
motor_asm = Compound(children=[motor_body, Pos(0, 0, 20) * shaft])
motor_asm.label = "motor_assembly"

# ===== 层级 2：总装配 =====
total = Compound(children=[
    base_asm,
    Pos(0, 0, 25) * motor_asm,
])
total.label = "total_assembly"
export_step(total, "total_assembly.step")
```

### 命名规范

| 前缀 | 含义 | 示例 |
|------|------|------|
| `asm_` | 子装配 | `asm_drivetrain` |
| `prt_` | 单个零件 | `prt_bearing` |
| `std_` | 标准件 | `std_m3_bolt` |
| `ref_` | 参考几何 | `ref_datum_plane` |

### 文件组织

```
project/
├── parts/
│   ├── base_plate.py
│   ├── motor_mount.py
│   └── shaft_coupler.py
├── assemblies/
│   ├── base_assembly.py      # 导入 parts/
│   ├── drivetrain_assembly.py
│   └── total_assembly.py     # 导入 assemblies/
└── exports/
    ├── *.step
    └── *.stl
```

---

## 决策树：选择装配模式

```
你有几个零件？
│
├── 1 个 → 不需要装配，直接 BuildPart 建模
│
├── 2-5 个（简单多体）
│   ├── 零件间有运动关系？
│   │   ├── 是 → Joints + connect_to
│   │   └── 否 → Compound + Label + Pos 变换
│   └── 需要碰撞检测？
│       └── 是 → 加 do_children_intersect()
│
├── 5-20 个（关节装配）
│   ├── 有铰链/旋转关系 → RevoluteJoint + connect_to
│   ├── 有大量相同零件 → copy.copy() + Compound
│   └── 需要动画预览 → Joints + Animation
│
└── 20+ 个（大型装配）
    ├── 按功能分组 → 子装配层级（2-3 层）
    ├── 标准件批量 → copy.copy() + 命名规范
    ├── 打印排版 → pack() 自动排列
    └── 定期检查 → show_topology() + do_children_intersect()
```

---

## 常见陷阱

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| STEP 中零件无名称 | 忘记设置 `label` | 每个零件必须 `.label = "xxx"` |
| 零件位置错误 | 变换顺序搞反 | 记住：从右到左，先旋转后平移 |
| 内存爆炸 | 重复建模相同零件 | 用 `copy.copy()` 浅拷贝 |
| 导出后零件丢失 | 没放入 `children` | 用 `show_topology()` 检查 |
| 关节定位不对 | Joint Location 参数有误 | 在零件坐标系中确认关节位置 |
