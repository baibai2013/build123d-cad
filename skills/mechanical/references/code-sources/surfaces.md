# 曲面领域（Surfaces）

> 场景：Loft 多截面放样、Sweep 扭转扫掠、NURBS 有机外壳、流线型造型。
> 核心原则：**先翻 `gumyr/build123d/examples/`**，那里有作者亲手写的 Loft/Sweep 范式。

---

## 主力 repo

### 1. `gumyr/build123d` (Apache-2.0) ★★★★★

`examples/` 目录含多个曲面示范：
- Loft 多截面（常见于瓶身、电吹风外壳）
- Sweep 路径扫掠（管件、缎带扭转）
- Shell / offset 抽壳
- Fillet / Chamfer 曲面过渡

**典型调用**：

```python
from build123d import *

# 多截面 Loft
with BuildPart() as body:
    with BuildSketch(Plane.XY):
        Circle(20)
    with BuildSketch(Plane.XY.offset(50)):
        Rectangle(30, 20)
    loft()

# Sweep 扭转扫掠（is_frenet 关键）
path = Edge.make_helix(pitch=240, height=60, radius=40)
start_plane = Plane(origin=path @ 0, z_dir=path % 0)
with BuildPart() as ribbon:
    with BuildSketch(start_plane):
        Rectangle(30, 5)
    sweep(path=path, is_frenet=True)   # Frenet 框架驱动自然扭转
```

---

### 2. `CadQuery/cadquery` (Apache-2.0) ★★★★☆

有机形体参考多（瓶体、艺术品），API 差异需过 `cadquery-to-build123d.md`。

**常见 CadQuery 曲面构造**：
- `.loft()` → build123d `loft()`（相同）
- `.sweep()` → `sweep()`（参数名必填）
- `.shell(t)` → **注意用 `offset(amount=-t, openings=<face>)`**（shell() 未导出）

---

### 3. `CadQuery/cadquery-contrib` (MIT) ★★★☆☆

社区曲面示例（瓶身、扭转把手等）。`examples/` + `tutorials/` 可直接运行。

---

## 核心技巧

### 1. Loft 三截面：曲率平滑
```python
with BuildPart() as bottle:
    with BuildSketch(Plane.XY): Circle(20)
    with BuildSketch(Plane.XY.offset(30)): Circle(25)      # 腰部略粗
    with BuildSketch(Plane.XY.offset(60)): Rectangle(18, 18)  # 瓶口方形
    loft()
```
- 截面数 ≥ 3 才能控制曲率；2 截面可能得到线性过渡
- 截面拓扑一致（Circle→Circle OK，Circle→Rectangle 可能出怪形）

### 2. Sweep 扭转：is_frenet=True
路径曲率大时截面跟随扭转。螺旋路径 + 矩形截面 → 天然莫比乌斯感。

### 3. Shell 陷阱（高频踩坑）
```python
# ❌ shell(face, thickness=-t)  # shell() 在 build123d 未导出！
# ✅ offset(amount=-t, openings=face)   # 正确做法
```

### 4. NURBS 面光顺检查
`references/parts/surface-modeling.md` 有 G1/G2 连续性讨论和斑马纹检查方法。

### 5. 曲面建模验证
```python
# 导出后用 visual verification 对比
# scripts/validate/validate_part.py 自动验证 BRep + 体积 + STEP 精度
```

---

## 易混点

### Plane.XZ.offset(10) 的 z_dir
- `Plane.XZ.offset(10)` → origin=(0, -10, 0), **z_dir=(0, -1, 0)**（法向向内）
- 新手常以为 z_dir 是"朝上"，实际是法向
- 见 `cadquery-to-build123d.md §易混点`

### Sweep 路径切线
- `path @ 0` = 起点坐标
- `path % 0` = 起点切线向量
- `Plane(origin=path @ 0, z_dir=path % 0)` 标准写法（切线 = 截面法向）

---

## 已收录的代码片段

（随 `experience/code-patterns/surfaces/` 累积）

- 暂无

---

## WebSearch prompt 模板

```
site:github.com/gumyr/build123d loft sweep filename:*.py
site:github.com/gumyr/build123d path:examples surface
"build123d" NURBS surface example
"cadquery" organic shape lofted
```

---

## 相关本地资源

- `references/parts/surface-modeling.md` — 曲面连续性 / 斑马纹 / 多截面陷阱（700+ 行深度）
- `SKILL.md §大型非凸多边形面` — OCP 三角化失败的通用解法
