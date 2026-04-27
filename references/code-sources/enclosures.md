# 外壳领域（Enclosures）

> 场景：电子产品外壳、PCB 盒子、卡扣壳体、散热孔、分体式壳体、防水壳。
> 核心原则：**PCB 开孔 + 螺丝柱先查 data-sources，卡扣/抽壳结构先翻社区**。

---

## 主力 repo

### 1. `gumyr/build123d` (Apache-2.0) ★★★★★

`examples/` 目录外壳类示例：
- 简单盒体 + 抽壳 + 盖板
- 螺丝柱（boss）配 热压铜螺母
- 分体外壳（body + lid）用 Joint 装配

### 2. `CadQuery/cadquery-contrib` (MIT) ★★★★☆

**社区外壳精品**多在此：
- `examples/` 下有 parametric enclosure 范本
- 常见的"开发板配壳"思路：从 PCB 尺寸反推壳体

借鉴时走 `cadquery-to-build123d.md` 翻译。

---

## 核心技巧

### 1. 从 PCB 尺寸反推壳体
```python
from build123d import *

# PCB 参数（从 Gerber / 铭牌）
pcb_l, pcb_w, pcb_h = 50, 30, 1.6
comp_h = 8      # 元器件最高高度
hole_positions = [(-20,-10), (20,-10), (-20,10), (20,10)]
hole_r = 1.25   # M2.5 安装孔

# 壳体参数
clearance = 1.0           # PCB 到壳壁间隙
wall_t = 2.0              # 壁厚
lid_h = 2.0               # 盖板厚

# 外壳内腔
inner_l = pcb_l + 2 * clearance
inner_w = pcb_w + 2 * clearance
inner_h = comp_h + 2       # 元器件上空余

# 建模
with BuildPart() as case:
    Box(inner_l + 2*wall_t, inner_w + 2*wall_t, inner_h + wall_t)
    # 抽壳：开顶面
    top_face = case.faces().sort_by(Axis.Z)[-1]
    offset(amount=-wall_t, openings=top_face)
    # 螺丝柱（从底升起）
    for x, y in hole_positions:
        with Locations((x, y, -inner_h/2 + wall_t)):
            Cylinder(radius=2.5, height=comp_h/2, mode=Mode.ADD)
            Hole(radius=hole_r, depth=comp_h/2)

# 配套盖板独立建模...
```

### 2. 卡扣结构（Snap-fit）

**原则**：
- 主体壁开内凹槽
- 盖板侧有外凸扣
- 插入方向留 1~2 mm 导入斜面
- FDM 打印时柔性方向与层纹平行，避免分层处断裂

**详见**：`references/parts/patterns.md` 里的卡扣模板 + 社区 `cadquery-contrib` 里的 snap-fit 例子

### 3. 散热孔阵列

用 `GridLocations`：
```python
with BuildPart() as case:
    Box(60, 40, 30)
    top = case.faces().sort_by(Axis.Z)[-1]
    with BuildSketch(top):
        with GridLocations(8, 8, 5, 3):
            Circle(2)       # ⌀4mm 散热孔
    extrude(amount=-wall_t, mode=Mode.SUBTRACT)
```

### 4. PCB 螺丝柱：配热压铜螺母

M3 常用 OD4.2 × L5 铜螺母：
```bash
python3 $SKILL/scripts/research/spec_lookup.py M3
# → threaded_insert.predrill_hole_d: 4.0 mm（热压过程铜会微张开）
```

螺丝柱外径建议 ≥ 5.5 mm（壁厚 0.75 mm 以上）。

### 5. 分体外壳装配

用 `Compound` + `RigidJoint`：
```python
body_joint = RigidJoint("lid_mount", body,
                         joint_location=Location((0, 0, inner_h/2), (0, 0, 0)))
lid_joint  = RigidJoint("body_mount", lid,
                         joint_location=Location((0, 0, -lid_h/2), (180, 0, 0)))
body_joint.connect_to(lid_joint)
```

---

## 3D 打印工艺约束（快速提醒）

| 特征 | FDM 推荐 | SLA 推荐 |
|------|---------|---------|
| 壁厚最小 | 1.6 mm | 1.0 mm |
| 配合间隙 | +0.2~0.3 mm/侧 | +0.1 mm/侧 |
| 螺丝柱外径 | ≥ 5.5 mm（M3） | ≥ 4.5 mm |
| 卡扣凸起 | ≥ 0.8 mm（配合深度） | ≥ 0.5 mm |

详见 `references/process/3d-printing.md`。

---

## 已收录的代码片段

（随 `experience/code-patterns/enclosures/` 累积）

- 暂无

---

## WebSearch prompt 模板

```
"build123d" enclosure snap-fit filename:*.py
site:github.com/CadQuery/cadquery-contrib enclosure
"cadquery" parametric case example
"build123d" OR "cadquery" PCB mount box
```

---

## 相关本地资源

- `references/assembly/mounting-experience.md` — PCB 安装 / 舵机安装 / 电池仓实战
- `references/process/3d-printing.md` — 壁厚 / 悬臂 / 公差 / 多材料
