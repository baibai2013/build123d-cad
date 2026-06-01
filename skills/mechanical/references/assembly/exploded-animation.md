# 爆炸动画参考

> 从静态装配到动态爆炸动画的完整流程，含顺序拆解、多关节运动、GIF 导出。

---

## 1. 静态装配预览 — show() 多色显示

最基础的装配可视化：用 `show()` 把多个零件分色显示。

```python
from build123d import *
from ocp_vscode import show

body = import_step("enclosure_box.step")
lid = import_step("enclosure_lid.step")

# 盖子定位到盒体顶面
lid_z = 20 + 1.5  # outer_h/2 + lid_thick/2
assembled_lid = Pos(0, 0, lid_z) * lid

# 分色显示
show(body, assembled_lid,
     names=["body", "lid"],
     colors=["steelblue", "orange"])
```

**要点**：
- `names` 列表与传入的零件一一对应
- `colors` 支持 CSS 颜色名或 `(r, g, b)` 元组
- `names` 决定了后续动画中 `add_track` 的路径名

---

## 2. 静态爆炸图 — Pos 偏移

不需要动画时，直接用 Pos 偏移生成爆炸图。

```python
from build123d import *

body = import_step("enclosure_box.step")
lid = import_step("enclosure_lid.step")

explode_dist = 30  # 爆炸总距离 mm
half = explode_dist / 2

# 各零件向外移动
exp_body = Pos(0, 0, -half) * body
exp_lid = Pos(0, 0, 20 + 1.5 + half) * lid

exploded = Compound(children=[exp_body, exp_lid])
export_step(exploded, "enclosure_exploded.step")
```

**适用场景**：生成技术文档插图、不需要交互式预览。

---

## 3. 动画爆炸 — 经验证的 16s 循环

OCP CAD Viewer 动画：炸开 2s -> 停留 10s -> 合拢 2s -> 停留 2s。

```python
from build123d import *
from ocp_vscode import show, Animation

body = import_step("enclosure_box.step")
lid = import_step("enclosure_lid.step")

# 装配定位
lid_z = 20 + 1.5
assembled_lid = Pos(0, 0, lid_z) * lid

# 爆炸参数（默认值，实战验证）
explode_dist = 30    # 爆炸总距离 mm
half = explode_dist / 2

# 显示装配态（动画起点）
show(body, assembled_lid,
     names=["body", "lid"],
     colors=["steelblue", "orange"])

# 时间轴：炸开2s → 停留10s → 合拢2s → 停留2s（16s循环）
t = [0, 2, 12, 14, 16]

animation = Animation()
animation.add_track("/Group/body", "t", t,
                    [[0,0,0], [0,0,-half], [0,0,-half], [0,0,0], [0,0,0]])
animation.add_track("/Group/lid",  "t", t,
                    [[0,0,0], [0,0,half],  [0,0,half],  [0,0,0], [0,0,0]])
animation.animate(1)  # speed=1 正常速度
```

### 默认参数说明

| 参数 | 值 | 说明 |
|------|-----|------|
| `explode_dist` | 30mm | 适合 50-100mm 尺寸零件 |
| 时间轴 `t` | `[0, 2, 12, 14, 16]` | 16s 循环，展开态停留最长 |
| `animate(1)` | speed=1 | 正常速度播放 |
| 路径前缀 | `/Group/` | OCP Viewer 默认的根节点 |
| 颜色 | steelblue + orange | 高对比度、工程感 |

### 路径格式

- `/Group/name` — `name` 对应 `show()` 中 `names` 参数
- 查看所有可用路径：`animation.paths`

---

## 4. 顺序拆解动画 — 错开时间轴

多个零件按拆卸顺序依次弹出，视觉更清晰。

```python
from build123d import *
from ocp_vscode import show, Animation

body = import_step("body.step")
pcb  = import_step("pcb.step")
lid  = import_step("lid.step")

# 螺栓组（4个）
bolt = import_step("bolt.step")
bolt_positions = [(-25, -15, 22), (25, -15, 22), (-25, 15, 22), (25, 15, 22)]
bolts = [Pos(*p) * bolt for p in bolt_positions]

# 显示装配态
show(body, pcb, lid, *bolts,
     names=["body", "pcb", "lid", "bolt_0", "bolt_1", "bolt_2", "bolt_3"],
     colors=["steelblue", "steelblue", "orange",
             "gray", "gray", "gray", "gray"])

animation = Animation()

# 顺序拆解：螺栓先出 → 盖子再出 → PCB 最后出
#            时间轴设计：每组错开 2 秒
# 时间点：   0s    2s    4s    6s    8s   (总 8s 拆完)

# 螺栓：0-2s 上升
t_bolts = [0, 2, 8]
for i in range(4):
    animation.add_track(f"/Group/bolt_{i}", "tz", t_bolts,
                        [0, 30, 30])

# 盖子：2-4s 上升（螺栓拆完后）
t_lid = [0, 2, 4, 8]
animation.add_track("/Group/lid", "tz", t_lid,
                    [0, 0, 25, 25])

# PCB：4-6s 上升（盖子拆完后）
t_pcb = [0, 4, 6, 8]
animation.add_track("/Group/pcb", "tz", t_pcb,
                    [0, 0, 20, 20])

animation.animate(1)
```

### 时间轴设计模板

5 个部件的错开时间轴：

```python
# 每组错开 2 秒，总时长 = 部件数 × 2 + 停留时间
t_bolts = [0, 2, 2, 2, 2]     # 螺栓 0-2s 上升，然后保持
t_lid   = [0, 0, 2, 4, 4]     # 盖子 2-4s 上升
t_pcb   = [0, 0, 0, 4, 6]     # PCB 4-6s 上升
```

**设计要点**：
- 拆卸顺序与实际操作一致：先拆外层（螺栓）→ 再拆中层（盖子）→ 最后拆内层（PCB）
- 每组之间留 0.5-1s 间隔，视觉上有节奏感
- 最后一帧保持爆炸态，便于截图

---

## 5. 多关节运动动画 — RevoluteJoint 角度映射

不是爆炸动画，而是关节运动动画（如机器人行走）。

```python
from build123d import *
from ocp_vscode import show, Animation

# 建模（简化的腿部）
body = Box(40, 20, 10)
body.label = "body"

upper_leg = Box(8, 8, 30)
upper_leg.label = "upper_leg"
lower_leg = Box(6, 6, 25)
lower_leg.label = "lower_leg"

# 定位
pos_upper = Pos(0, 0, -20) * upper_leg
pos_lower = Pos(0, 0, -42.5) * lower_leg

# 显示
show(body, pos_upper, pos_lower,
     names=["body", "upper_leg", "lower_leg"],
     colors=["steelblue", "orange", "orange"])

# 关节运动动画
animation = Animation()

# 大腿绕 Y 轴摆动：前后各 30 度
animation.add_track("/Group/upper_leg", "ry",
                    [0, 1, 2, 3, 4],
                    [0, 30, 0, -30, 0])

# 小腿绕 Y 轴弯曲：膝关节屈伸
animation.add_track("/Group/lower_leg", "ry",
                    [0, 1, 2, 3, 4],
                    [0, -45, 0, 45, 0])

animation.animate(1)
```

### 四足步态模板

```python
# 对角步态：左前+右后同步，右前+左后同步
# 一个周期 2 秒
t = [0, 0.5, 1.0, 1.5, 2.0]

# 左前腿
animation.add_track("/Group/leg_fl_upper", "ry", t, [0, 25, 0, -25, 0])
animation.add_track("/Group/leg_fl_lower", "ry", t, [0, -35, 0, 10, 0])

# 右后腿（与左前同步）
animation.add_track("/Group/leg_br_upper", "ry", t, [0, 25, 0, -25, 0])
animation.add_track("/Group/leg_br_lower", "ry", t, [0, -35, 0, 10, 0])

# 右前腿（反相）
animation.add_track("/Group/leg_fr_upper", "ry", t, [0, -25, 0, 25, 0])
animation.add_track("/Group/leg_fr_lower", "ry", t, [0, 10, 0, -35, 0])

# 左后腿（与右前同步）
animation.add_track("/Group/leg_bl_upper", "ry", t, [0, -25, 0, 25, 0])
animation.add_track("/Group/leg_bl_lower", "ry", t, [0, 10, 0, -35, 0])
```

### action 类型与旋转轴对应

| action | 含义 | 单位 | 典型用途 |
|--------|------|------|---------|
| `"rx"` | 绕 X 轴旋转 | 度 | 俯仰（侧面关节） |
| `"ry"` | 绕 Y 轴旋转 | 度 | 俯仰（正面关节） |
| `"rz"` | 绕 Z 轴旋转 | 度 | 偏航（转盘） |

---

## 6. save_as_gif() — GIF 导出

把动画导出为 GIF 文件，用于文档和 README。

```python
animation.save_as_gif("exploded.gif", fps=25, loops=0, bg_color="white")
```

### 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `output` | str | (必填) | 输出文件路径 |
| `fps` | int | 25 | 帧率，只能用精确值 |
| `loops` | int | 0 | 0=无限循环，N=播放 N 次 |
| `endpoint` | bool | False | 是否包含最后一帧 |
| `bg_color` | str | "white" | 背景色，CSS 颜色名 |
| `pause` | float | 0.02 | 每帧截图间隔（秒） |

### fps 精确值

GIF 以厘秒（centiseconds）存储帧间隔，只有能整除 100 的 fps 值才精确：

| fps | 帧间隔 (cs) | 说明 |
|-----|-------------|------|
| 10 | 10 | 文件小，适合简单展示 |
| 20 | 5 | 平衡质量与文件大小 |
| **25** | **4** | **推荐，流畅且文件适中** |
| 50 | 2 | 高质量，文件较大 |
| 100 | 1 | 最流畅，文件最大 |

其他 fps 值（如 30）会被近似处理，帧速不精确。

### GIF 文件大小优化

- 降低 fps：25 → 10 可减半文件大小
- 缩短动画时长：减少停留时间
- 使用 `gifsicle` 后处理压缩：
  ```bash
  gifsicle -O3 --lossy=80 input.gif -o output.gif
  ```

---

## 7. 多部件时间轴设计指南

5 个以上零件的爆炸动画，需要精心设计视觉节奏。

### 设计原则

1. **由外到内**：先拆外壳 → 再拆中间层 → 最后拆核心件
2. **同类同步**：同种零件（如 4 个螺栓）同时运动
3. **间隔呼吸**：每组动作之间留 0.5-1s 静止段
4. **停留充足**：爆炸态至少停留 3-5s（截图需要）
5. **首尾静止**：动画开头和结尾各留 1-2s 静止

### 8 部件时间轴模板

```
时间轴：0 ──── 2 ── 3 ── 4 ── 5 ── 6 ──────── 14 ── 16
        ↑      ↑    ↑    ↑    ↑    ↑            ↑     ↑
        静止   螺栓  盖子  PCB  散热  风扇         合拢   静止
        起点   弹出  弹出  弹出  弹出  弹出         开始   终点
```

```python
from ocp_vscode import Animation

animation = Animation()

# 总时长 16s，各组依次爆炸
total = 16
groups = {
    "bolts":  {"parts": ["bolt_0","bolt_1","bolt_2","bolt_3"],
               "start": 0, "dur": 2, "axis": "tz", "dist": 40},
    "lid":    {"parts": ["lid"],
               "start": 2, "dur": 1, "axis": "tz", "dist": 30},
    "pcb":    {"parts": ["pcb"],
               "start": 3, "dur": 1, "axis": "tz", "dist": 20},
    "heatsink":{"parts": ["heatsink"],
               "start": 4, "dur": 1, "axis": "tx", "dist": 25},
    "fan":    {"parts": ["fan"],
               "start": 5, "dur": 1, "axis": "tz", "dist": 35},
}

hold_end = 14  # 爆炸态持续到 14s
close_dur = 2  # 合拢用 2s

for name, g in groups.items():
    t0, dur, dist = g["start"], g["dur"], g["dist"]
    t = [0, t0, t0 + dur, hold_end, hold_end + close_dur, total]
    v = [0, 0, dist, dist, 0, 0]
    for part in g["parts"]:
        animation.add_track(f"/Group/{part}", g["axis"], t, v)

animation.animate(1)
```

---

## 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| 动画不播放 | `show()` 未先执行 | 必须先 `show()` 再 `Animation()` |
| 路径找不到 | `names` 与 `add_track` 路径不匹配 | 检查 `animation.paths` |
| GIF 帧速异常 | fps 不是 100 的因数 | 用 10/20/25/50/100 |
| 零件飞走 | `"t"` 轨道值是绝对坐标偏移 | 使用相对偏移量，非绝对位置 |
| 动画不循环 | `animate()` 只播放一次 | OCP Viewer 自动循环，GIF 设 `loops=0` |
