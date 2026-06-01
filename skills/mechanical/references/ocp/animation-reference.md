# Animation API 参考

> OCP CAD Viewer 动画系统完整 API，含轨道类型、GIF 导出、多关节协调模板。

---

## 基本用法

```python
from ocp_vscode import show, Animation

# 1. 先 show() 显示零件
show(body, lid,
     names=["body", "lid"],
     colors=["steelblue", "orange"])

# 2. 创建动画
animation = Animation()

# 3. 添加轨道
animation.add_track("/Group/lid", "tz", [0, 2, 4], [0, 30, 30])

# 4. 播放
animation.animate(1)

# 5. 可选：导出 GIF
animation.save_as_gif("output.gif")
```

---

## 1. Animation() 构造函数

```python
animation = Animation()
```

创建一个空的动画对象。

> **注意**：旧版本有 `Animation(assembly=...)` 参数，已废弃。当前版本不需要传入任何参数。

---

## 2. add_track() — 添加动画轨道

```python
animation.add_track(path, action, times, values)
```

### 参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `path` | str | 目标对象路径，格式 `"/Group/name"` |
| `action` | str | 变换类型（见下表） |
| `times` | list[float] | 关键帧时间点列表（秒） |
| `values` | list | 关键帧值列表，长度必须与 `times` 一致 |

### action 类型

| action | 含义 | values 格式 | 示例 |
|--------|------|------------|------|
| `"t"` | 位置（三轴） | `[[x,y,z], ...]` | `[[0,0,0], [0,0,30]]` |
| `"tx"` | X 轴平移 | `[float, ...]` | `[0, 20]` |
| `"ty"` | Y 轴平移 | `[float, ...]` | `[0, 15]` |
| `"tz"` | Z 轴平移 | `[float, ...]` | `[0, 30]` |
| `"rx"` | 绕 X 轴旋转 | `[degrees, ...]` | `[0, 90]` |
| `"ry"` | 绕 Y 轴旋转 | `[degrees, ...]` | `[0, 45]` |
| `"rz"` | 绕 Z 轴旋转 | `[degrees, ...]` | `[0, 180]` |
| `"q"` | 四元数旋转 | `[[x,y,z,w], ...]` | `[[0,0,0,1], [0,0,0.707,0.707]]` |

### 使用 "t" vs "tx"/"ty"/"tz"

```python
# 方式一：用 "t" 一次性指定三轴位移
animation.add_track("/Group/lid", "t",
    [0, 2, 4],
    [[0,0,0], [0,0,30], [0,0,30]])

# 方式二：用 "tz" 只指定 Z 轴（更简洁）
animation.add_track("/Group/lid", "tz",
    [0, 2, 4],
    [0, 30, 30])
```

- 单轴运动用 `"tx"/"ty"/"tz"` 更简洁
- 多轴联动必须用 `"t"` 向量格式

### 旋转示例

```python
# 绕 Z 轴转 360 度
animation.add_track("/Group/turntable", "rz",
    [0, 4],
    [0, 360])

# 绕 Y 轴摆动
animation.add_track("/Group/arm", "ry",
    [0, 1, 2, 3, 4],
    [0, 30, 0, -30, 0])
```

### animate_joints 参数

```python
animation.add_track(path, action, times, values, animate_joints=False)
```

当 `animate_joints=True` 时，使用 build123d Joint 系统自动解算运动。默认 `False`，直接指定变换值。

---

## 3. animate() — 播放动画

```python
animation.animate(speed=1)
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `speed` | float | 1 | 播放速度倍率（2=两倍速，0.5=半速） |

动画在 OCP CAD Viewer 中自动循环播放。

---

## 4. set_relative_time() — 跳转到指定时间

```python
animation.set_relative_time(0.5)  # 跳到动画中间
```

| 参数 | 类型 | 范围 | 说明 |
|------|------|------|------|
| `fraction` | float | 0.0 ~ 1.0 | 动画进度比例 |

**用途**：
- 跳到特定帧截图
- 调试关键帧位置
- 交互式控制动画

```python
# 跳到爆炸态截图
animation.set_relative_time(0.25)  # 假设 25% 处是完全展开

# 逐帧检查
for f in [0, 0.1, 0.2, 0.3, 0.4, 0.5]:
    animation.set_relative_time(f)
    # 在 Viewer 中观察每一帧
```

---

## 5. save_as_gif() — 导出 GIF

```python
animation.save_as_gif(
    output,          # str: 输出文件路径
    fps=25,          # int: 帧率
    loops=0,         # int: 循环次数
    endpoint=False,  # bool: 是否包含末帧
    bg_color="white",# str: 背景颜色
    pause=0.02       # float: 截图间隔
)
```

### 参数详解

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `output` | str | (必填) | 输出 GIF 文件路径 |
| `fps` | int | 25 | 帧率，只用精确值 |
| `loops` | int | 0 | 0=无限循环，N=播放 N 次后停止 |
| `endpoint` | bool | False | True 时包含最后一帧（循环动画设 False 避免重复帧） |
| `bg_color` | str | "white" | 背景色，支持 CSS 颜色名 |
| `pause` | float | 0.02 | 每帧截图的间隔秒数（过小可能截图不全） |

### fps 精确值表

GIF 格式以厘秒（centiseconds，1/100 秒）为单位存储帧间隔。只有 100 能整除的 fps 值才精确：

| fps | 帧间隔 | 厘秒 | 16s 动画帧数 | 说明 |
|-----|--------|------|-------------|------|
| 10 | 100ms | 10 | 160 | 文件最小 |
| 20 | 50ms | 5 | 320 | 平衡之选 |
| **25** | **40ms** | **4** | **400** | **推荐默认** |
| 50 | 20ms | 2 | 800 | 高质量 |
| 100 | 10ms | 1 | 1600 | 最流畅，文件大 |

**不推荐的值**：fps=15（6.67cs 近似为 7cs=14.3fps）、fps=24（4.17cs 近似为 4cs=25fps）、fps=30（3.33cs 近似为 3cs=33fps）。

### 完整 GIF 导出示例

```python
from build123d import *
from ocp_vscode import show, Animation

body = import_step("body.step")
lid  = import_step("lid.step")

show(body, Pos(0, 0, 22) * lid,
     names=["body", "lid"],
     colors=["steelblue", "orange"])

animation = Animation()
t = [0, 2, 12, 14, 16]
animation.add_track("/Group/body", "tz", t, [0, -15, -15, 0, 0])
animation.add_track("/Group/lid",  "tz", t, [0, 15, 15, 0, 0])
animation.animate(1)

# 导出 GIF
animation.save_as_gif(
    "exploded.gif",
    fps=25,        # 流畅且文件适中
    loops=0,       # 无限循环
    bg_color="white"
)
```

---

## 6. paths 属性 — 查看可用路径

```python
animation = Animation()
print(animation.paths)
```

`animation.paths` 返回所有可用的动画路径列表，在 `show()` 之后才有值。

**路径格式规则**：

| show() 参数 | 对应路径 |
|-------------|---------|
| `names=["body"]` | `/Group/body` |
| `names=["lid"]` | `/Group/lid` |
| `names=["bolt_0"]` | `/Group/bolt_0` |

- 根节点固定为 `/Group/`
- 名称与 `show()` 的 `names` 参数一一对应
- 如果没设 `names`，使用变量名或自动编号

**调试技巧**：

```python
show(body, lid, names=["body", "lid"])
animation = Animation()
print("可用路径:", animation.paths)
# 输出: 可用路径: ['/Group/body', '/Group/lid']
```

---

## 7. 多关节协调动画模板

### 四足步态 — 对角步态

左前 + 右后同步，右前 + 左后同步，相位差 180 度。

```python
from ocp_vscode import Animation

animation = Animation()

# 一个步态周期 2 秒
t = [0, 0.5, 1.0, 1.5, 2.0]

# ===== 左前腿（A 相） =====
animation.add_track("/Group/leg_fl_upper", "ry", t,
                    [0, 25, 0, -25, 0])   # 大腿前后摆
animation.add_track("/Group/leg_fl_lower", "ry", t,
                    [0, -35, 0, 10, 0])   # 小腿屈伸

# ===== 右后腿（A 相，与左前同步） =====
animation.add_track("/Group/leg_br_upper", "ry", t,
                    [0, 25, 0, -25, 0])
animation.add_track("/Group/leg_br_lower", "ry", t,
                    [0, -35, 0, 10, 0])

# ===== 右前腿（B 相，反相） =====
animation.add_track("/Group/leg_fr_upper", "ry", t,
                    [0, -25, 0, 25, 0])
animation.add_track("/Group/leg_fr_lower", "ry", t,
                    [0, 10, 0, -35, 0])

# ===== 左后腿（B 相，与右前同步） =====
animation.add_track("/Group/leg_bl_upper", "ry", t,
                    [0, -25, 0, 25, 0])
animation.add_track("/Group/leg_bl_lower", "ry", t,
                    [0, 10, 0, -35, 0])

animation.animate(1)
```

### 步态参数说明

| 参数 | 值 | 说明 |
|------|-----|------|
| 周期 | 2s | 一个完整步态循环 |
| 大腿摆幅 | ±25° | 前后摆动范围 |
| 小腿屈伸 | -35° ~ +10° | 抬腿时屈膝，着地时伸直 |
| 相位差 | 180° | A/B 组反向运动 |

### 机械臂 — 多关节协调

```python
from ocp_vscode import Animation

animation = Animation()

# 3 自由度机械臂：底座旋转 + 大臂俯仰 + 小臂俯仰
t = [0, 2, 4, 6, 8]

# 底座绕 Z 轴旋转
animation.add_track("/Group/base_turret", "rz", t,
                    [0, 45, 45, -45, 0])

# 大臂绕 Y 轴俯仰
animation.add_track("/Group/upper_arm", "ry", t,
                    [0, -30, -60, -30, 0])

# 小臂绕 Y 轴俯仰
animation.add_track("/Group/lower_arm", "ry", t,
                    [0, 20, 40, 20, 0])

animation.animate(1)
```

### 转盘展示 — 简单旋转

```python
from ocp_vscode import Animation

animation = Animation()

# 零件绕 Z 轴匀速旋转一圈
animation.add_track("/Group/part", "rz",
                    [0, 8],
                    [0, 360])

animation.animate(1)
animation.save_as_gif("turntable.gif", fps=25, loops=0)
```

---

## 完整工作流模板

```python
from build123d import *
from ocp_vscode import show, Animation

# ===== 1. 建模或导入零件 =====
body = import_step("body.step")
lid  = import_step("lid.step")

# ===== 2. 装配定位 =====
assembled_lid = Pos(0, 0, 22) * lid

# ===== 3. 显示（设置 names） =====
show(body, assembled_lid,
     names=["body", "lid"],
     colors=["steelblue", "orange"])

# ===== 4. 创建动画 =====
animation = Animation()

# 检查路径
print("可用路径:", animation.paths)

# ===== 5. 添加轨道 =====
explode = 15
t = [0, 2, 12, 14, 16]
animation.add_track("/Group/body", "tz", t, [0, -explode, -explode, 0, 0])
animation.add_track("/Group/lid",  "tz", t, [0, explode, explode, 0, 0])

# ===== 6. 播放 =====
animation.animate(1)

# ===== 7. 导出 GIF =====
animation.save_as_gif("exploded.gif", fps=25, loops=0, bg_color="white")
```

---

## 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| `animation.paths` 为空 | `show()` 未先执行 | 必须先调用 `show()` |
| 路径找不到对象 | `names` 拼写不一致 | 打印 `animation.paths` 确认 |
| 旋转方向反了 | 角度符号搞反 | 正值=逆时针（右手定则） |
| GIF 帧速不对 | fps 非精确值 | 用 10/20/25/50/100 |
| GIF 循环停止 | `loops` 非零 | 设 `loops=0` 无限循环 |
| 动画跳帧 | `times` 和 `values` 长度不匹配 | 确保两个列表等长 |
| 多轨道不同步 | 时间轴不一致 | 所有轨道用同一个 `t` 列表 |
| `animate_joints` 无效 | 零件没有定义 Joint | 需要先在 build123d 中设置关节 |
