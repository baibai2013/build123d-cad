# build123d Joints 系统参考

## 概述

build123d 的 Joints（关节）系统用于定义零件之间的运动约束关系，实现装配体建模。

**核心设计理念：**

- **无约束求解器** — 不同于传统 CAD（SolidWorks、Fusion 360）的约束求解方式，build123d 的关节系统是纯 Python 编排模型。你在代码中显式指定每个关节的参数值（角度、位移），而非让求解器推导。
- **父子连接** — 每个 Joint 附着在一个 `to_part`（父零件）上，通过 `connect_to()` 方法将另一个关节（子零件上的）连接过来。连接时子零件会被重新定位。
- **自由度（DOF）驱动** — 5 种关节类型分别提供 0~3 个自由度，connect_to 时传入对应数量的参数来确定子零件的位姿。

**基本工作流：**

```python
from build123d import *

# 1. 创建零件
base = Box(100, 100, 10)
arm = Box(10, 10, 50)

# 2. 在零件上定义关节
j1 = RigidJoint("mount", to_part=base, joint_location=Location((50, 0, 5)))
j2 = RevoluteJoint("pivot", to_part=arm, axis=Axis.Z)

# 3. 连接
j1.connect_to(j2, angle=45)

# 4. 此时 arm 已被移动到正确位置
```

---

## 5 种关节类型

### 1. RigidJoint — 固定连接（0 DOF）

将两个零件刚性固定在一起，无任何运动自由度。

**构造函数：**

```python
RigidJoint(
    label: str,                              # 关节标签名
    to_part: Solid | Compound | None = None, # 附着的零件
    joint_location: Location | None = None,  # 关节在零件上的位置/朝向
)
```

**参数说明：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `label` | `str` | 关节唯一标签，用于在 `part.joints` 字典中检索 |
| `to_part` | `Solid \| Compound \| None` | 关节附着的零件。在 BuildPart 上下文中可省略（自动绑定） |
| `joint_location` | `Location \| None` | 关节坐标系在零件局部坐标中的位置与朝向。`None` 时为零件原点 |

**属性：**

| 属性 | 类型 | 说明 |
|------|------|------|
| `symbol` | `Compound` | 关节的可视化符号（用于调试渲染） |
| `relative_location` | `Location` | 关节相对于零件的位置 |

**connect_to 方法：**

```python
# RigidJoint 可以连接以下类型：
rigid_joint.connect_to(other: RigidJoint)                           # 0 个运动参数
rigid_joint.connect_to(other: RevoluteJoint, angle: float = 0)      # 1 个：旋转角度
rigid_joint.connect_to(other: LinearJoint, position: float = 0)     # 1 个：滑动位置
rigid_joint.connect_to(other: CylindricalJoint,                     # 2 个：位置+角度
                       position: float = 0, angle: float = 0)
rigid_joint.connect_to(other: BallJoint, angles: RotationLike = None) # 3 个：三轴旋转
```

**典型用途：** 螺栓固定、胶粘、焊接等不可动连接；也常作为运动链的"锚点"（基座关节）。

---

### 2. RevoluteJoint — 旋转铰链（1 DOF）

零件绕单一轴旋转，类似门铰链或机械臂的关节。

**构造函数：**

```python
RevoluteJoint(
    label: str,                              # 关节标签名
    to_part: Solid | Compound | None = None, # 附着的零件
    axis: Axis = Axis.Z,                     # 旋转轴
    angle_reference: VectorLike | None = None, # 角度零点参考方向
    angular_range: tuple[float, float] = (0, 360), # 允许旋转范围（度）
)
```

**参数说明：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `label` | `str` | 关节唯一标签 |
| `to_part` | `Solid \| Compound \| None` | 附着零件 |
| `axis` | `Axis` | 旋转轴，定义旋转中心点和方向。默认 `Axis.Z` |
| `angle_reference` | `VectorLike \| None` | 角度测量的零点参考方向（垂直于旋转轴的向量） |
| `angular_range` | `tuple[float, float]` | 旋转角度的最小值和最大值（单位：度） |

**属性：**

| 属性 | 类型 | 说明 |
|------|------|------|
| `angular_range` | `tuple[float, float]` | 允许的角度范围 |
| `relative_axis` | `Axis` | 关节旋转轴（相对于零件） |
| `angle` | `float` | 当前旋转角度 |
| `symbol` | `Compound` | 可视化符号 |

**connect_to 方法：**

```python
# RevoluteJoint 只能连接 RigidJoint
revolute_joint.connect_to(other: RigidJoint, angle: float = 0)
```

> **注意：** RevoluteJoint 作为"被连接方"（作为 connect_to 的参数）时，可以被 RigidJoint 或 LinearJoint 连接。

**典型用途：** 门铰链、机械臂关节、四足机器人的髋关节/膝关节/踝关节。

**示例：**

```python
# 带角度限制的膝关节
knee = RevoluteJoint(
    "knee",
    to_part=upper_leg,
    axis=Axis((0, 0, -leg_len/2), (1, 0, 0)),  # 在腿底端，绕 X 轴转
    angular_range=(-120, 0),                     # 只能向后弯曲
)
```

---

### 3. LinearJoint — 直线滑动（1 DOF）

零件沿单一轴线性移动，类似抽屉滑轨。

**构造函数：**

```python
LinearJoint(
    label: str,                              # 关节标签名
    to_part: Solid | Compound | None = None, # 附着的零件
    axis: Axis = Axis.Z,                     # 滑动轴
    linear_range: tuple[float, float] = (0, inf), # 滑动范围
)
```

**参数说明：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `label` | `str` | 关节唯一标签 |
| `to_part` | `Solid \| Compound \| None` | 附着零件 |
| `axis` | `Axis` | 滑动方向轴。`Axis` 的 `position` 定义滑动起点，`direction` 定义滑动方向 |
| `linear_range` | `tuple[float, float]` | 滑动距离的最小值和最大值 |

**属性：**

| 属性 | 类型 | 说明 |
|------|------|------|
| `linear_range` | `tuple[float, float]` | 允许的滑动范围 |
| `relative_axis` | `Axis` | 关节滑动轴（相对于零件） |
| `position` | `float` | 当前滑动位置 |
| `symbol` | `Compound` | 可视化符号 |

**connect_to 方法：**

```python
# LinearJoint 可以连接 RigidJoint 和 RevoluteJoint
linear_joint.connect_to(other: RigidJoint, position: float = 0)
linear_joint.connect_to(other: RevoluteJoint, position: float = 0, angle: float = 0)
```

**典型用途：** 抽屉滑轨、线性导轨、活塞、升降平台。

---

### 4. CylindricalJoint — 旋转+滑动（2 DOF）

零件同时可以绕轴旋转和沿轴移动，类似螺丝在螺纹孔中的运动。

**构造函数：**

```python
CylindricalJoint(
    label: str,                              # 关节标签名
    to_part: Solid | Compound | None = None, # 附着的零件
    axis: Axis = Axis.Z,                     # 运动轴（旋转+滑动共用）
    angle_reference: VectorLike | None = None, # 角度零点参考方向
    linear_range: tuple[float, float] = (0, inf),  # 滑动范围
    angular_range: tuple[float, float] = (0, 360),  # 旋转范围（度）
)
```

**参数说明：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `label` | `str` | 关节唯一标签 |
| `to_part` | `Solid \| Compound \| None` | 附着零件 |
| `axis` | `Axis` | 旋转和滑动共用的轴 |
| `angle_reference` | `VectorLike \| None` | 角度零点参考方向 |
| `linear_range` | `tuple[float, float]` | 滑动范围 |
| `angular_range` | `tuple[float, float]` | 旋转角度范围（度） |

**属性：**

| 属性 | 类型 | 说明 |
|------|------|------|
| `angular_range` | `tuple[float, float]` | 角度范围 |
| `linear_range` | `tuple[float, float]` | 滑动范围 |
| `relative_axis` | `Axis` | 关节轴（相对于零件） |
| `angle` | `float` | 当前角度 |
| `position` | `float` | 当前位置 |
| `symbol` | `Compound` | 可视化符号 |

**connect_to 方法：**

```python
# CylindricalJoint 只能连接 RigidJoint
cylindrical_joint.connect_to(other: RigidJoint, position: float = 0, angle: float = 0)
```

**典型用途：** 螺纹连接、旋转伸缩杆、丝杆螺母机构。

---

### 5. BallJoint — 万向球铰（3 DOF）

零件可以绕三个轴自由旋转（类似万向节 / 人体肩关节）。

**构造函数：**

```python
BallJoint(
    label: str,                              # 关节标签名
    to_part: Solid | Compound | None = None, # 附着的零件
    joint_location: Location | None = None,  # 关节位置
    angular_range: tuple[
        tuple[float, float],   # X 轴旋转范围
        tuple[float, float],   # Y 轴旋转范围
        tuple[float, float],   # Z 轴旋转范围
    ] = ((0, 360), (0, 360), (0, 360)),
    angle_reference: Plane = Plane.XY,       # 角度参考平面
)
```

**参数说明：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `label` | `str` | 关节唯一标签 |
| `to_part` | `Solid \| Compound \| None` | 附着零件 |
| `joint_location` | `Location \| None` | 关节坐标系位置 |
| `angular_range` | 三元组嵌套 | 三个轴各自的旋转范围（度），格式 `((x_min, x_max), (y_min, y_max), (z_min, z_max))` |
| `angle_reference` | `Plane` | 角度测量的参考平面 |

**属性：**

| 属性 | 类型 | 说明 |
|------|------|------|
| `angular_range` | 三元组嵌套 | 三轴角度范围 |
| `symbol` | `Compound` | 可视化符号 |

**connect_to 方法：**

```python
# BallJoint 只能连接 RigidJoint
ball_joint.connect_to(other: RigidJoint, angles: RotationLike = None)
```

> `RotationLike` 可以是 `Rotation(x, y, z)` 对象或 `(x, y, z)` 元组，表示绕三轴的旋转角度。

**典型用途：** 机器人肩关节、头部关节、万向节、球头连杆。

---

## connect_to() 兼容矩阵

下表说明哪些关节对可以互连，以及连接时需要传入的运动参数。

行 = 调用方（`caller.connect_to(other)`），列 = 被连接方（`other`）。

| caller \\ other | RigidJoint | RevoluteJoint | LinearJoint | CylindricalJoint | BallJoint |
|---|---|---|---|---|---|
| **RigidJoint** | ✅ — | ✅ `angle` | ✅ `position` | ✅ `position, angle` | ✅ `angles` |
| **RevoluteJoint** | ✅ `angle` | ❌ | ❌ | ❌ | ❌ |
| **LinearJoint** | ✅ `position` | ✅ `position, angle` | ❌ | ❌ | ❌ |
| **CylindricalJoint** | ✅ `position, angle` | ❌ | ❌ | ❌ | ❌ |
| **BallJoint** | ✅ `angles` | ❌ | ❌ | ❌ | ❌ |

**规律总结：**

- RigidJoint 是"万能适配器"，可以连接任何类型的关节。
- 其他关节类型只能连接 RigidJoint（LinearJoint 额外可连 RevoluteJoint）。
- 运动参数数量 = 两个关节的 DOF 之和。

---

## Builder Mode 集成

在 `BuildPart()` 上下文中创建关节时，可以省略 `to_part` 参数。关节会自动附着到当前 Builder 正在构建的零件上。

```python
with BuildPart() as arm:
    Box(10, 10, 50)
    # 无需写 to_part=arm.part，关节自动绑定
    RevoluteJoint("shoulder", axis=Axis.X)
    RigidJoint("end", joint_location=Location((0, 0, 25)))
```

**自动转移规则：**

- 在 BuildPart 上下文内创建的 Joint 会自动绑定到 `BuildPart.part`。
- 上下文退出后，可通过 `arm.part.joints["shoulder"]` 访问关节。
- 如果显式指定了 `to_part`，则不会自动绑定（以显式指定为准）。

**访问关节：**

```python
# 通过 joints 字典
shoulder = arm.part.joints["shoulder"]

# 遍历所有关节
for name, joint in arm.part.joints.items():
    print(f"{name}: {type(joint).__name__}")
```

---

## 关节可视化

### symbol 属性

每种关节类型都有 `symbol` 属性，返回一个小型 `Compound` 几何体，直观表示关节的位置、轴向和类型：

- **RigidJoint** — 三色坐标轴（XYZ 三色线段）
- **RevoluteJoint** — 旋转轴 + 弧形箭头
- **LinearJoint** — 滑动轴 + 箭头
- **CylindricalJoint** — 旋转弧 + 滑动箭头
- **BallJoint** — 三个旋转弧

### 在 OCP Viewer 中显示关节

```python
from ocp_vscode import show

# 方法 1：渲染时启用关节符号
show(part, render_joints=True)

# 方法 2：手动添加关节符号到场景
joint_symbols = [j.symbol for j in part.joints.values()]
show(part, *joint_symbols)
```

> `render_joints=True` 是调试装配体时最常用的方式，可以直观看到每个关节的位置和方向是否正确。

---

## 运动学链示例 — 四足腿部

四足机器人的一条腿由 4 个零件和 3 个旋转关节组成：

```
body → [hip RevoluteJoint] → upper_leg → [knee RevoluteJoint] → lower_leg → [ankle RevoluteJoint] → foot
```

### 完整代码

```python
from build123d import *

# === 零件尺寸 ===
body_size = (60, 40, 15)
upper_leg_len = 30
lower_leg_len = 25
foot_size = (8, 6, 3)

# === 创建零件并定义关节 ===

# 身体（基座）
with BuildPart() as body:
    Box(*body_size)
    # 右前腿挂载点 — 固定关节作为"锚"
    RigidJoint(
        "hip_rf",
        joint_location=Location(
            (body_size[0]/2, body_size[1]/4, -body_size[2]/2)
        ),
    )

# 大腿
with BuildPart() as upper_leg:
    Box(6, 6, upper_leg_len)
    # 顶部：被身体连接的旋转关节（髋关节）
    RevoluteJoint(
        "hip",
        axis=Axis((0, 0, upper_leg_len/2), (1, 0, 0)),
        angular_range=(-45, 45),
    )
    # 底部：连接小腿的固定关节
    RigidJoint(
        "knee_mount",
        joint_location=Location((0, 0, -upper_leg_len/2)),
    )

# 小腿
with BuildPart() as lower_leg:
    Box(5, 5, lower_leg_len)
    # 顶部：膝关节
    RevoluteJoint(
        "knee",
        axis=Axis((0, 0, lower_leg_len/2), (1, 0, 0)),
        angular_range=(-120, 0),
    )
    # 底部：连接脚掌
    RigidJoint(
        "ankle_mount",
        joint_location=Location((0, 0, -lower_leg_len/2)),
    )

# 脚掌
with BuildPart() as foot:
    Box(*foot_size)
    # 踝关节
    RevoluteJoint(
        "ankle",
        axis=Axis((0, 0, foot_size[2]/2), (1, 0, 0)),
        angular_range=(-30, 30),
    )

# === 驱动运动学链 ===

hip_angle = 20      # 髋关节前摆 20 度
knee_angle = -60     # 膝关节弯曲 60 度
ankle_angle = 15     # 踝关节微调 15 度

# 连接顺序：从基座往末端
body.part.joints["hip_rf"].connect_to(
    upper_leg.part.joints["hip"], angle=hip_angle
)
upper_leg.part.joints["knee_mount"].connect_to(
    lower_leg.part.joints["knee"], angle=knee_angle
)
lower_leg.part.joints["ankle_mount"].connect_to(
    foot.part.joints["ankle"], angle=ankle_angle
)

# === 显示 ===
from ocp_vscode import show
show(
    body.part, upper_leg.part, lower_leg.part, foot.part,
    render_joints=True,
)
```

**运动学链的关键模式：**

1. 父零件端用 **RigidJoint** 标记挂载点。
2. 子零件端用 **RevoluteJoint**（或其他运动关节）定义运动自由度。
3. `RigidJoint.connect_to(RevoluteJoint, angle=...)` 传入角度来驱动姿态。
4. 链式调用：上一个零件的末端 RigidJoint 连接下一个零件的运动关节。

---

## 错误处理

### ValueError — 参数超出范围

当 connect_to 传入的角度或位置超出关节定义的范围时，抛出 `ValueError`：

```python
knee = RevoluteJoint("knee", to_part=leg, angular_range=(-120, 0))
mount = RigidJoint("mount", to_part=body)

# 角度 45 不在 (-120, 0) 范围内 → ValueError
mount.connect_to(knee, angle=45)
# ValueError: angle 45.0 is not in range (-120.0, 0.0)
```

**同理适用于 LinearJoint 和 CylindricalJoint 的线性范围：**

```python
slider = LinearJoint("slider", to_part=rail, linear_range=(0, 100))
mount = RigidJoint("mount", to_part=block)

# 位置 150 超出 (0, 100) → ValueError
mount.connect_to(slider, position=150)
# ValueError: position 150.0 is not in range (0.0, 100.0)
```

### TypeError — 关节类型不兼容

当尝试连接不兼容的关节对时，抛出 `TypeError`：

```python
rev1 = RevoluteJoint("j1", to_part=part_a)
rev2 = RevoluteJoint("j2", to_part=part_b)

# RevoluteJoint 只能连 RigidJoint → TypeError
rev1.connect_to(rev2, angle=0)
# TypeError: RevoluteJoint can only connect to RigidJoint
```

**防御性编程建议：**

```python
def safe_connect(parent_joint, child_joint, **kwargs):
    """带验证的安全连接"""
    try:
        parent_joint.connect_to(child_joint, **kwargs)
    except ValueError as e:
        print(f"参数越界: {e}")
        # 钳位到合法范围
        if hasattr(child_joint, 'angular_range') and 'angle' in kwargs:
            lo, hi = child_joint.angular_range
            kwargs['angle'] = max(lo, min(hi, kwargs['angle']))
            parent_joint.connect_to(child_joint, **kwargs)
    except TypeError as e:
        print(f"类型不匹配: {e}")
        raise
```

---

## 完整代码示例

### 示例 1：简易铰链装配

两个板通过铰链连接，可以开合：

```python
from build123d import *
from ocp_vscode import show

# 底板（固定）
with BuildPart() as base_plate:
    Box(50, 30, 3)
    RigidJoint(
        "hinge_mount",
        joint_location=Location((25, 0, 1.5)),  # 右边缘中点
    )

# 翻盖
with BuildPart() as flap:
    Box(40, 30, 3)
    RevoluteJoint(
        "hinge",
        axis=Axis((-20, 0, 1.5), (0, 1, 0)),   # 左边缘，绕 Y 轴旋转
        angular_range=(0, 135),                   # 0=闭合, 135=最大张开
    )

# 打开到 90 度
base_plate.part.joints["hinge_mount"].connect_to(
    flap.part.joints["hinge"],
    angle=90,
)

show(base_plate.part, flap.part, render_joints=True)
```

### 示例 2：线性滑台

```python
from build123d import *
from ocp_vscode import show

# 导轨
with BuildPart() as rail:
    Box(100, 10, 5)
    LinearJoint(
        "slide",
        axis=Axis((-50, 0, 2.5), (1, 0, 0)),   # 沿 X 轴滑动
        linear_range=(0, 80),                     # 行程 80mm
    )

# 滑块
with BuildPart() as slider:
    Box(15, 12, 8)
    RigidJoint("base", joint_location=Location((0, 0, -4)))

# 滑到中间位置
rail.part.joints["slide"].connect_to(
    slider.part.joints["base"],
    position=40,
)

show(rail.part, slider.part, render_joints=True)
```

### 示例 3：球铰万向头

```python
from build123d import *
from ocp_vscode import show

# 底座
with BuildPart() as pedestal:
    Cylinder(radius=15, height=30)
    RigidJoint(
        "ball_mount",
        joint_location=Location((0, 0, 15)),
    )

# 头部
with BuildPart() as head:
    Sphere(radius=10)
    BallJoint(
        "neck",
        joint_location=Location((0, 0, -10)),
        angular_range=((-30, 30), (-30, 30), (-180, 180)),
    )

# 头部偏转
pedestal.part.joints["ball_mount"].connect_to(
    head.part.joints["neck"],
    angles=Rotation(15, -10, 45),
)

show(pedestal.part, head.part, render_joints=True)
```

---

## 速查表

| 关节类型 | DOF | 运动参数 | 核心场景 |
|----------|-----|----------|----------|
| `RigidJoint` | 0 | — | 固定连接、挂载点 |
| `RevoluteJoint` | 1 | `angle` | 铰链、旋转关节 |
| `LinearJoint` | 1 | `position` | 滑轨、活塞 |
| `CylindricalJoint` | 2 | `position, angle` | 螺纹、旋转伸缩 |
| `BallJoint` | 3 | `angles` | 万向节、肩关节 |

**记忆口诀：** Rigid 固定不动 → Revolute 转一个 → Linear 走一个 → Cylindrical 又转又走 → Ball 三轴全转。
