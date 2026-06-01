# build123d 曲面建模参考

## 1. 多截面放样 Loft

将不同平面上的多个截面（草图）连接成光滑实体，适合渐变外形零件。

### API 签名

```python
loft(
    sections: Face | Sketch | Iterable[Vertex | Face | Sketch] | None = None,
    ruled: bool = False,
    clean: bool = True,
    mode: Mode = Mode.ADD,
) -> Part
```

| 参数 | 说明 |
|------|------|
| `sections` | 截面列表（Face/Sketch/Vertex）。省略时使用待处理草图 |
| `ruled` | `True` = 直纹面（线性插值），`False` = 光滑曲面 |
| `clean` | 是否清理多余内部结构 |
| `mode` | 组合模式（ADD / SUBTRACT / INTERSECT） |

### 基础放样：圆到方

```python
from build123d import *

with BuildPart() as transition:
    with BuildSketch(Plane.XY):
        Circle(20)
    with BuildSketch(Plane.XY.offset(40)):
        Rectangle(30, 30)
    loft()

export_step(transition.part, "loft_transition.step")
```

### 多截面放样

```python
from build123d import *

with BuildPart() as multi:
    with BuildSketch(Plane.XY):
        Circle(20)
    with BuildSketch(Plane.XY.offset(20)):
        Rectangle(30, 30)
    with BuildSketch(Plane.XY.offset(40)):
        Circle(15)
    loft()

export_step(multi.part, "loft_multi.step")
```

### 收尖放样（Vertex 端点）

截面列表的首/尾可以用 `Vertex` 替代，实现收尖效果（如子弹头、锥形过渡）：

```python
from build123d import *

with BuildPart() as bullet:
    with BuildSketch(Plane.XY):
        Circle(15)
    with BuildSketch(Plane.XY.offset(30)):
        Circle(12)
    loft(sections=[Vertex(0, 0, 50)])  # 仅尾端收尖
    # 也可写成：loft(sections=[pending_faces..., Vertex(0,0,50)])

export_step(bullet.part, "bullet.step")
```

> **注意**：`Vertex` 只能出现在截面列表的第一个或最后一个位置（或两端都用）。

### ruled=True：直纹面

```python
from build123d import *

with BuildPart() as ruled_loft:
    with BuildSketch(Plane.XY):
        Circle(20)
    with BuildSketch(Plane.XY.offset(40)):
        Rectangle(30, 30)
    loft(ruled=True)  # 线性插值，棱角分明

export_step(ruled_loft.part, "loft_ruled.step")
```

### 截面兼容性要点

| 情况 | 结果 |
|------|------|
| 截面边数相同（如两个圆） | 最佳，自然过渡 |
| 截面边数不同（圆 → 方） | 可行，内核自动匹配 |
| 截面面积差异过大 | 可能出现自相交，需加中间截面 |
| 截面不平行 | 支持，但过渡可能不直观 |

---

## 2. 扫掠 Sweep 高级用法

沿路径推扫截面，生成管道、弯管、异形通道等。

### API 签名

```python
sweep(
    sections=None,
    path=None,
    multisection: bool = False,
    is_frenet: bool = False,
    transition: Transition = Transition.TRANSFORMED,
    normal: VectorLike | None = None,
    binormal: Edge | Wire | None = None,
    clean: bool = True,
    mode: Mode = Mode.ADD,
) -> Part | Sketch
```

| 参数 | 说明 |
|------|------|
| `sections` | 截面（Edge/Wire/Face）。省略时使用待处理截面 |
| `path` | 扫掠路径（Curve/Edge/Wire） |
| `multisection` | `True` = 沿路径放置多个截面（渐变扫掠） |
| `is_frenet` | `True` = 使用 Frenet 标架（路径法向量随曲率变化） |
| `transition` | 路径不连续处理：`RIGHT`（直角）/ `ROUND`（圆弧）/ `TRANSFORMED`（变换） |
| `normal` | 固定截面法向量方向 |
| `binormal` | 引导曲线控制截面旋转 |

### 基础扫掠：弯管

```python
from build123d import *

path = Edge.make_circle(40, start_angle=0, end_angle=90)
with BuildPart() as elbow:
    with BuildSketch(Plane(path @ 0, z_dir=path % 0)):
        Circle(15)
        Circle(13, mode=Mode.SUBTRACT)
    sweep(path=path)

export_step(elbow.part, "pipe_elbow.step")
```

**关键技巧**：`path @ 0` 返回路径起点位置，`path % 0` 返回起点切线方向。截面必须位于路径起点的法平面上。

### 复合路径扫掠

```python
from build123d import *

with BuildPart() as pipe:
    with BuildLine() as path:
        Line((0, 0, 0), (0, 0, 50))
        RadiusArc((0, 0, 50), (50, 0, 50), radius=30)
        Line((50, 0, 50), (50, 0, 0))
    with BuildSketch(Plane(path.wires()[0] @ 0, z_dir=path.wires()[0] % 0)):
        Circle(5)
        Circle(4, mode=Mode.SUBTRACT)
    sweep(path=path.wires()[0])

export_step(pipe.part, "pipe_compound.step")
```

### Frenet 标架 vs 固定法向

| 模式 | 用法 | 效果 |
|------|------|------|
| 默认（`is_frenet=False`） | `sweep(path=path)` | 截面朝向沿路径保持"最小扭转" |
| Frenet 标架 | `sweep(path=path, is_frenet=True)` | 截面跟随路径曲率旋转，S 弯处可能翻转 |
| 固定法向 | `sweep(path=path, normal=(0,0,1))` | 截面 Z 方向固定朝上，适合水平路径 |
| 引导曲线 | `sweep(path=path, binormal=guide)` | 用另一条曲线控制截面旋转 |

### 多截面扫掠（渐变截面）

沿路径放置多个不同截面，实现截面渐变效果：

```python
from build123d import *

path = Edge.make_line((0, 0, 0), (0, 0, 60))

# 截面必须位于路径上的不同位置
sec1 = Circle(20)                        # 在起点（大圆）
sec2 = Pos(0, 0, 60) * Rectangle(10, 10) # 在终点（小方形）

with BuildPart() as tapered:
    sweep(sections=[sec1, sec2], path=path, multisection=True)

export_step(tapered.part, "sweep_multi.step")
```

> **注意**：`multisection=True` 时截面需分布在路径上（通过位置对齐），内核自动在截面间插值。

### Transition 选项

控制路径在非连续点（如直线转弯处）的过渡方式：

```python
# 直角过渡（棱角分明）
sweep(path=path, transition=Transition.RIGHT)

# 圆弧过渡（平滑圆角）
sweep(path=path, transition=Transition.ROUND)

# 变换过渡（默认，综合处理）
sweep(path=path, transition=Transition.TRANSFORMED)
```

---

## 3. NURBS 曲面

build123d 提供多种从曲线/点阵创建自由曲面的方法。

### 3.1 曲线创建

#### Bezier 曲线

```python
from build123d import *

# Algebra Mode —— Edge 工厂方法
bezier = Edge.make_bezier(
    (0, 0, 0), (10, 20, 0), (30, 20, 0), (40, 0, 0)
)

# BuildLine 上下文 —— Bezier 对象
with BuildLine() as line:
    Bezier((0, 0, 0), (10, 20, 0), (30, 20, 0), (40, 0, 0))
```

#### B-Spline 曲线

```python
from build123d import *

# Algebra Mode
spline = Edge.make_spline(
    points=[(0, 0, 0), (10, 10, 5), (20, 0, 10), (30, 10, 15)],
    tangents=[(0, 1, 0), (0, 1, 0)],  # 起止切线方向（可选）
)

# BuildLine 上下文
with BuildLine() as line:
    Spline(
        (0, 0, 0), (10, 10, 5), (20, 0, 10), (30, 10, 15),
        tangents=[(0, 1, 0), (0, 1, 0)],
    )
```

#### 带权重的有理 Bezier 曲线

```python
from build123d import *

# 权重越大，曲线越靠近该控制点
rational_bezier = Edge.make_bezier(
    (0, 0, 0), (20, 30, 0), (40, 0, 0),
    weights=[1.0, 2.0, 1.0],  # 中间点权重大 → 曲线更弯
)
```

### 3.2 从曲线创建曲面

#### Face.make_surface_from_curves —— 直纹曲面

从两条曲线创建连接曲面（ruled surface）：

```python
from build123d import *

curve1 = Edge.make_spline([(0, 0, 0), (20, 10, 0), (40, 0, 0)])
curve2 = Edge.make_spline([(0, 0, 30), (20, -10, 30), (40, 0, 30)])

face = Face.make_surface_from_curves(curve1, curve2)

# 增厚为实体
solid = extrude(face, amount=2)
export_step(solid, "ruled_surface.step")
```

#### Face.make_surface —— 边界曲面

用封闭线框定义曲面边界，可选内部点控制形状：

```python
from build123d import *

# 四条边围成封闭轮廓
e1 = Edge.make_line((0, 0, 0), (40, 0, 0))
e2 = Edge.make_spline([(40, 0, 0), (40, 20, 10), (40, 40, 0)])
e3 = Edge.make_line((40, 40, 0), (0, 40, 0))
e4 = Edge.make_spline([(0, 40, 0), (0, 20, 10), (0, 0, 0)])

wire = Wire([e1, e2, e3, e4])
face = Face.make_surface(
    exterior=wire,
    surface_points=[(20, 20, 15)],  # 中间隆起
)
```

#### Face.make_bezier_surface —— Bezier 曲面

用二维控制点阵列定义 Bezier 曲面片：

```python
from build123d import *

# 4x4 控制点网格
points = [
    [(0,  0,  0), (10, 0,  5),  (20, 0,  5),  (30, 0,  0)],
    [(0,  10, 5), (10, 10, 15), (20, 10, 15), (30, 10, 5)],
    [(0,  20, 5), (10, 20, 15), (20, 20, 15), (30, 20, 5)],
    [(0,  30, 0), (10, 30, 5),  (20, 30, 5),  (30, 30, 0)],
]

face = Face.make_bezier_surface(points)
```

#### Face.make_surface_from_array_of_points —— 拟合曲面

通过二维点阵拟合 B-Spline 曲面（适合逆向工程/扫描数据）：

```python
from build123d import *
import math

# 生成波浪形点阵（模拟扫描数据）
points = []
for v in range(10):
    row = []
    for u in range(10):
        x = u * 5
        y = v * 5
        z = 5 * math.sin(x / 10) * math.cos(y / 10)
        row.append((x, y, z))
    points.append(row)

face = Face.make_surface_from_array_of_points(
    points,
    tol=0.01,
    smoothing=(1.0, 1.0, 1.0),  # 平滑权重
    min_deg=1,
    max_deg=6,
)
```

#### Face.make_gordon_surface —— Gordon 曲面

由交叉的轮廓曲线（profiles）和引导曲线（guides）网格构建曲面，精确插值所有输入曲线：

```python
from build123d import *

# 轮廓线（U 方向）
p1 = Edge.make_spline([(0, 0, 0), (15, 0, 10), (30, 0, 0)])
p2 = Edge.make_spline([(0, 20, 0), (15, 20, 15), (30, 20, 0)])
p3 = Edge.make_spline([(0, 40, 0), (15, 40, 10), (30, 40, 0)])

# 引导线（V 方向）—— 两端必须落在轮廓线上
g1 = Edge.make_spline([(0, 0, 0), (0, 20, 0), (0, 40, 0)])
g2 = Edge.make_spline([(15, 0, 10), (15, 20, 15), (15, 40, 10)])
g3 = Edge.make_spline([(30, 0, 0), (30, 20, 0), (30, 40, 0)])

face = Face.make_gordon_surface(
    profiles=[p1, p2, p3],
    guides=[g1, g2, g3],
)
```

**Gordon 曲面要求**：
- 每条轮廓线必须与每条引导线相交
- 轮廓线两端必须落在引导线上
- 引导线两端必须落在轮廓线上
- 首/尾的轮廓或引导可以用点（`VectorLike`）替代曲线

#### Face.make_surface_patch —— 约束曲面片

支持连续性约束的曲面补片，用于曲面间光滑过渡：

```python
from build123d import *

# 假设已有相邻曲面 existing_face
# 创建边界边
e1 = Edge.make_line((0, 0, 0), (30, 0, 0))
e2 = Edge.make_spline([(30, 0, 0), (30, 15, 10), (30, 30, 0)])
e3 = Edge.make_line((30, 30, 0), (0, 30, 0))

patch = Face.make_surface_patch(
    edge_face_constraints=[
        (e1, existing_face, ContinuityLevel.C1),  # 与已有面 G1 连续
    ],
    edge_constraints=[e2, e3],          # 自由边
    point_constraints=[(15, 15, 8)],    # 控制点
)
```

### 3.3 曲面方法对比

| 方法 | 输入 | 适用场景 |
|------|------|---------|
| `Face.make_surface_from_curves` | 两条边/线框 | 两条边之间的过渡面 |
| `Face.make_surface` | 封闭线框 + 可选内部点 | 边界已知的自由曲面 |
| `Face.make_bezier_surface` | 二维控制点阵列 | 精确控制曲面形状 |
| `Face.make_surface_from_array_of_points` | 二维数据点阵列 | 逆向工程、扫描数据拟合 |
| `Face.make_gordon_surface` | 轮廓+引导曲线网格 | 双向曲线网络插值 |
| `Face.make_surface_patch` | 边+面约束+连续性等级 | 曲面间光滑过渡补片 |

### 3.4 曲面增厚为实体

曲面（Face）是零厚度的，实际使用需增厚为实体：

```python
from build123d import *

# 方法 1：extrude 沿法向增厚
face = Face.make_bezier_surface(points)
solid = extrude(face, amount=2)  # 沿面法向偏移 2mm

# 方法 2：Solid.thicken（偏移曲面）
solid = Solid.thicken(face, depth=2)

# 方法 3：Shell.make_shell 后封闭
# （适合薄壁曲面件）
```

---

## 4. 曲面连续性

在 CAD 中，两个相邻曲面之间的连接质量由连续性等级（Continuity Level）衡量。

### 连续性等级

| 等级 | 名称 | 含义 | 视觉特征 |
|------|------|------|---------|
| **G0** | 位置连续 | 边沿位置吻合，但可以有折角 | 能看到明显的棱线 |
| **G1** | 切线连续 | 接缝处切线方向一致 | 棱线消失，但高光反射有折痕 |
| **G2** | 曲率连续 | 接缝处曲率半径匹配 | 高光反射平滑流过接缝，无折痕 |

### 直观理解

```
G0：两块板对齐放在一起，有明显折角
     ╱╲
    ╱  ╲

G1：两块板边缘相切，看起来连续但"不够顺滑"
     ╱‾‾‾
    ╱

G2：两块板曲率完全匹配，像一整块弯板
     ╭‾‾‾‾
    ╱
```

### build123d 中的连续性控制

build123d 通过 `ContinuityLevel` 枚举控制连续性：

```python
from build123d import *

# 连续性等级枚举
ContinuityLevel.C0  # 位置连续（G0）
ContinuityLevel.C1  # 切线连续（G1）
ContinuityLevel.C2  # 曲率连续（G2）
```

用于 `Face.make_surface_patch` 的边约束：

```python
# G1 连续补片
patch = Face.make_surface_patch(
    edge_face_constraints=[
        (shared_edge, adjacent_face, ContinuityLevel.C1),
    ],
    edge_constraints=[free_edge_1, free_edge_2],
)
```

### fillet 与连续性

`fillet()` 默认生成 G1 连续的过渡面（切线连续圆弧）。对于高品质外观件，可能需要手动构建 G2 连续的过渡曲面。

---

## 5. 曲面质量分析

### OCP CAD Viewer 斑马纹分析

斑马纹（Zebra Stripe）是检验曲面质量的标准工具，通过模拟环境反射条纹来暴露曲面缺陷。

```python
from ocp_vscode import show

# 基本斑马纹分析
show(part, zebra_count=9, zebra_direction=0)
```

| 参数 | 说明 | 推荐值 |
|------|------|--------|
| `zebra_count` | 条纹数量 | 7-12（少 → 粗略检查，多 → 精细检查） |
| `zebra_direction` | 条纹方向角度（度） | 0（水平），90（垂直），多方向交叉检查 |
| `zebra_color_scheme` | 条纹配色 | 默认黑白即可 |
| `zebra_opacity` | 条纹不透明度 | 0.0-1.0，默认 1.0 |

### 如何判读斑马纹

| 条纹表现 | 诊断 | 连续性等级 |
|----------|------|-----------|
| 条纹在接缝处断开/错位 | 曲面不连续 | < G0（间隙） |
| 条纹在接缝处对齐但折角 | 位置连续但不切线连续 | G0 |
| 条纹连续穿过接缝但有"拐点" | 切线连续但曲率不连续 | G1 |
| 条纹平滑流过接缝，无拐点 | 曲率连续 | G2 |

### 多方向检查

单一方向的斑马纹可能遗漏与条纹平行的缺陷，建议多角度检查：

```python
from ocp_vscode import show

# 水平条纹
show(part, zebra_count=9, zebra_direction=0)

# 垂直条纹
show(part, zebra_count=9, zebra_direction=90)

# 45 度条纹
show(part, zebra_count=9, zebra_direction=45)
```

### 常见问题与对策

| 问题 | 斑马纹表现 | 解决方案 |
|------|----------|---------|
| fillet 过渡不顺 | 条纹在圆角边缘折角 | 增大圆角半径，或用手动曲面替代 |
| loft 自相交 | 条纹局部扭曲/翻转 | 增加中间截面，缩小截面差异 |
| 曲面接缝 | 条纹明显断裂 | 用 `make_surface_patch` + `ContinuityLevel.C1/C2` |
| 扫掠扭曲 | 条纹不均匀旋转 | 尝试 `is_frenet=True` 或设定 `normal` |

---

## 6. 实战场景

### 6.1 有机外壳：多截面放样

适用于机械猫身体、手柄、鼠标外壳等有机曲面造型。

```python
from build123d import *

# 参数
body_length = 80

with BuildPart() as organic_shell:
    # 底部截面（宽扁椭圆）
    with BuildSketch(Plane.XY):
        Ellipse(25, 15)

    # 中段截面（较大的圆角矩形）
    with BuildSketch(Plane.XY.offset(body_length * 0.4)):
        RectangleRounded(50, 35, radius=10)

    # 上段截面（稍小的圆角矩形）
    with BuildSketch(Plane.XY.offset(body_length * 0.75)):
        RectangleRounded(40, 28, radius=12)

    # 顶部收尖
    with BuildSketch(Plane.XY.offset(body_length)):
        Ellipse(10, 8)

    loft()

    # 抽壳：从底面开口
    shell(organic_shell.faces().sort_by(Axis.Z)[0], thickness=-2)

export_step(organic_shell.part, "organic_shell.step")
```

**设计要点**：
- 截面数量越多，形状控制越精细（3-5 个截面通常足够）
- 相邻截面形状不宜差异过大，否则过渡不自然
- 使用 `Ellipse` 和 `RectangleRounded` 获得自然的有机感
- 最后 `shell()` 抽壳变为薄壁件

### 6.2 流线型外形：曲线路径扫掠

适用于扶手、栏杆、滑轨等沿曲线路径延伸的零件。

```python
from build123d import *

# 路径：3D 样条曲线
path = Edge.make_spline(
    points=[
        (0, 0, 0),
        (30, 0, 20),
        (60, 20, 30),
        (90, 20, 20),
        (120, 0, 0),
    ],
    tangents=[(1, 0, 1), (1, 0, -1)],  # 起止切线
)

with BuildPart() as streamline:
    with BuildSketch(Plane(path @ 0, z_dir=path % 0)):
        # 截面：圆角矩形（扁平）
        RectangleRounded(20, 8, radius=3)
    sweep(path=path)

export_step(streamline.part, "streamline.step")
```

**设计要点**：
- 截面必须在路径起点的法平面上（`Plane(path @ 0, z_dir=path % 0)`）
- 用 `Edge.make_spline` 的 `tangents` 参数控制起止方向
- 截面不宜太大（相对路径曲率半径），否则在急弯处自相交

### 6.3 过渡曲面：不同截面的光滑连接

连接两个不同截面的管道过渡段，如方管转圆管。

```python
from build123d import *

# 过渡段
transition_height = 50

with BuildPart() as reducer:
    # 方管入口
    with BuildSketch(Plane.XY):
        Rectangle(40, 40)
        offset(amount=-3)  # 壁厚 3mm 的空心截面

    # 圆管出口
    with BuildSketch(Plane.XY.offset(transition_height)):
        Circle(20)
        Circle(17, mode=Mode.SUBTRACT)  # 壁厚 3mm

    loft()

export_step(reducer.part, "reducer.step")
```

### 6.4 自由曲面外壳：Bezier 曲面 + 增厚

用控制点网格直接定义外壳曲面形状。

```python
from build123d import *

# 控制点网格：中间隆起的壳面
points = [
    [(0,  0,  0), (20, 0,  3),  (40, 0,  3),  (60, 0,  0)],
    [(0,  15, 3), (20, 15, 15), (40, 15, 15), (60, 15, 3)],
    [(0,  30, 3), (20, 30, 15), (40, 30, 15), (60, 30, 3)],
    [(0,  45, 0), (20, 45, 3),  (40, 45, 3),  (60, 45, 0)],
]

face = Face.make_bezier_surface(points)
shell_body = Solid.thicken(face, depth=2)

export_step(shell_body, "bezier_shell.step")
```

### 6.5 曲线网络建模：Gordon 曲面

用交叉曲线网络精确定义复杂曲面（如车身曲面、船体）。

```python
from build123d import *

# U 方向轮廓线（"肋骨"）
rib1 = Edge.make_spline([(0, 0, 0), (0, 15, 12), (0, 30, 0)])
rib2 = Edge.make_spline([(20, 0, 0), (20, 15, 18), (20, 30, 0)])
rib3 = Edge.make_spline([(40, 0, 0), (40, 15, 12), (40, 30, 0)])

# V 方向引导线（"龙骨"）
keel1 = Edge.make_spline([(0, 0, 0), (20, 0, 0), (40, 0, 0)])
keel2 = Edge.make_spline([(0, 15, 12), (20, 15, 18), (40, 15, 12)])
keel3 = Edge.make_spline([(0, 30, 0), (20, 30, 0), (40, 30, 0)])

face = Face.make_gordon_surface(
    profiles=[rib1, rib2, rib3],
    guides=[keel1, keel2, keel3],
)
solid = Solid.thicken(face, depth=2)

export_step(solid, "gordon_hull.step")
```

---

## 附录：曲面建模常见错误

| 错误 | 原因 | 解决方案 |
|------|------|---------|
| `loft()` 生成自相交实体 | 相邻截面差异过大或排列顺序错误 | 增加中间截面；确保截面从低到高排列 |
| `sweep()` 在弯道处扭曲 | 默认法向跟踪不适合路径 | 尝试 `is_frenet=True` 或指定 `normal` |
| `sweep()` 截面位置不对 | 截面不在路径起点法平面上 | 使用 `Plane(path @ 0, z_dir=path % 0)` |
| `make_gordon_surface` 失败 | 曲线不满足交叉要求 | 确保每条 profile 与每条 guide 相交 |
| 曲面增厚失败 | 曲面自身有奇异点或曲率半径小于厚度 | 减小 `depth` 值或简化曲面 |
| `make_surface_patch` 报错 | 边约束不封闭或不兼容 | 检查边的端点是否首尾相连 |
