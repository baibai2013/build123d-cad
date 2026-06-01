# 齿轮领域（Gears）

> **第一原则**：**永远先看 `gumyr/bd_warehouse`**，它是 build123d 官方齿轮库——比自己造轮子省 90% 代码。

---

## 主力 repo

### 1. `gumyr/bd_warehouse` (Apache-2.0) ★★★★★

build123d 官方扩展，含齿轮模块：

```python
from bd_warehouse.gear import InvoluteGear, HelicalGear, BevelGear, RackGear

# 渐开线直齿轮
gear = InvoluteGear(
    module_size=1.0,        # 模数
    tooth_count=20,          # 齿数
    pressure_angle=20,       # 压力角
    root_fillet=0.2,         # 齿根圆角
    face_width=5.0,          # 齿宽
)
# gear 已是 build123d Part 对象，直接 show() 或 export_step()

# 斜齿轮
helical = HelicalGear(module_size=1.0, tooth_count=30, helix_angle=15)

# 锥齿轮
bevel = BevelGear(module_size=1.0, tooth_count=20, face_width=5.0,
                  pitch_cone_angle=45)

# 齿条
rack = RackGear(module_size=1.0, tooth_count=15)
```

**安装**：`pip install bd_warehouse`

**何时用**：
- 标准渐开线齿轮
- 斜齿 / 行星 / 锥齿 / 齿条
- 需要标准模数 + 齿数参数化

**何时不用**：
- 特种齿形（摆线齿轮、余弦齿等）— bd_warehouse 不支持
- 需要自定义齿廓曲线 — 走下面的社区参考

---

## Fallback：`CadQuery/cadquery-contrib` (MIT) ★★★☆☆

社区齿轮示例在 `examples/` 目录，风格偏教学：

**典型用法**：
- `examples/gears.py`（或类似文件）— 手写渐开线齿廓
- 可借鉴：齿廓数学公式、参数化范围
- 翻译：CadQuery → build123d，走 `cadquery-to-build123d.md`

**License**：MIT，借鉴注明来源即可。

---

## 核心技巧（齿轮建模心法）

### 1. 用 bd_warehouse 就别自己算渐开线
bd_warehouse 的 `InvoluteGear` 已正确实现齿廓，不要重复造轮子。

### 2. 若必须自己画齿廓：用"根实体 + 逐齿融合"
**⚠️ 陷阱**：一次性把 20 齿拉伸为 300 点多边形 → OCP Viewer 三角化失败（face ignored）。

正确做法见 `references/parts/surface-modeling.md` 或 `SKILL.md §大型非凸多边形面`：
```python
# ✅ 根圆柱 + 逐齿 Algebra Mode 融合
gear = Cylinder(radius=root_r, height=face_width)
for i in range(teeth):
    pts = tooth_profile_2d(i)   # 单齿 ~15 点
    # ...每齿一个 extrude，合并进 gear
```

### 3. 齿轮啮合：中心距 = (m × (z1 + z2)) / 2
模数 m、齿数 z1/z2，标准安装中心距 = m(z1+z2)/2。
装配时用：
```python
gear1 = InvoluteGear(module_size=1.0, tooth_count=20)
gear2 = InvoluteGear(module_size=1.0, tooth_count=40)
center_distance = 1.0 * (20 + 40) / 2   # 30mm
gear2_placed = Pos(center_distance, 0, 0) * gear2
```

### 4. 齿轮与轴配合：用 data-sources 查键槽 / 轴径
```bash
python3 $SKILL/scripts/research/spec_lookup.py 608ZZ   # 如轴用 608 轴承
```

---

## 已收录的代码片段

（本节随 `experience/code-patterns/gears/` 累积而更新）

- 暂无（用到时在 S4/R5 写入经验）

---

## WebSearch prompt 模板

```
site:github.com/gumyr/bd_warehouse gear
site:github.com/CadQuery/cadquery-contrib gear
"build123d" OR "bd_warehouse" involute gear example
```

---

## 已知的不该借鉴对象

- **渐开线 YouTube 教程博文**：多为 OpenSCAD / JavaScript 实现，翻译成本高且 License 不清。优先 bd_warehouse。
- **随意的 GitHub gist**：未标 License 时**禁止借鉴**（见 README §License 纪律）。
