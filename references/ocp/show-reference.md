# show() 完整参数参考

> OCP CAD Viewer 的 `show()` 函数参数分类速查，含常用配置组合。

---

## 基本用法

```python
from ocp_vscode import show

# 最简用法
show(part)

# 多零件 + 命名 + 颜色
show(body, lid,
     names=["body", "lid"],
     colors=["steelblue", "orange"])

# 完整参数示例
show(part,
     names=["my_part"],
     colors=["steelblue"],
     alphas=[0.8],
     deviation=0.1,
     angular_tolerance=0.1,
     default_edgecolor=(0.2, 0.2, 0.2),
     axes=True,
     grid=(True, True, True),
     glass=False,
     tools=True)
```

---

## 参数分类

### 对象参数

控制传入对象的显示方式。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `names` | list[str] | None | 零件名称列表，与传入对象一一对应 |
| `colors` | list[str] | None | 颜色列表，CSS 颜色名或 `(r,g,b)` 元组 |
| `alphas` | list[float] | None | 透明度列表，0.0(全透明)~1.0(不透明) |
| `modes` | list[Render] | None | 渲染模式列表 |
| `materials` | list[Material] | None | 材质列表 |
| `progress` | str | None | 进度条标签 |

**Render 枚举**：

| 值 | 说明 |
|-----|------|
| `Render.FACES` | 只显示面（默认） |
| `Render.EDGES` | 只显示边线 |
| `Render.VERTICES` | 只显示顶点 |
| `Render.BOTH` | 面 + 边线 |

### UI 控制

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `glass` | bool | False | 玻璃效果面板（截图模式常用） |
| `tools` | bool | True | 是否显示工具栏 |
| `tree_width` | int | 250 | 装配树面板宽度（像素） |

### 相机

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `zoom` | float | None | 缩放级别 |
| `position` | tuple | None | 相机位置 `(x, y, z)` |
| `quaternion` | tuple | None | 相机朝向四元数 `(x, y, z, w)` |
| `target` | tuple | None | 相机目标点 `(x, y, z)` |
| `reset_camera` | Camera | Camera.RESET | 重置相机行为 |
| `ortho` | bool | True | 正交投影（False 为透视投影） |
| `up` | str | "Z" | 向上方向 |

**Camera 枚举**：

| 值 | 说明 |
|-----|------|
| `Camera.RESET` | 重置到默认视角 |
| `Camera.CENTER` | 只重置中心点 |
| `Camera.KEEP` | 保持当前视角不变 |

### 显示控制

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `axes` | bool | False | 显示坐标轴 |
| `axes0` | bool | False | 坐标轴是否在原点显示 |
| `grid` | tuple | (False, False, False) | XY/XZ/YZ 网格 |
| `transparent` | bool | False | 全局透明模式 |
| `default_opacity` | float | 1.0 | 默认透明度 |
| `black_edges` | bool | True | 边线用黑色 |
| `collapse` | Collapse | None | 装配树折叠方式 |

**Collapse 枚举**：

| 值 | 说明 |
|-----|------|
| `Collapse.ALL` | 折叠所有节点 |
| `Collapse.NONE` | 展开所有节点 |
| `Collapse.LEAVES` | 只折叠叶节点 |
| `Collapse.ROOT` | 只折叠根节点 |

### 剪裁平面

最多 3 个剪裁平面，用于查看截面。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `clip_slider_0` | float | None | 第 1 剪裁面位置 (0.0~1.0) |
| `clip_slider_1` | float | None | 第 2 剪裁面位置 |
| `clip_slider_2` | float | None | 第 3 剪裁面位置 |
| `clip_normal_0` | tuple | (-1,0,0) | 第 1 剪裁面法线方向 |
| `clip_normal_1` | tuple | (0,-1,0) | 第 2 剪裁面法线方向 |
| `clip_normal_2` | tuple | (0,0,-1) | 第 3 剪裁面法线方向 |
| `clip_intersection` | bool | False | 剪裁面交集模式 |
| `clip_planes` | bool | False | 显示剪裁平面 |

**剪裁示例**：

```python
# X 方向截面，切到中间位置
show(part,
     clip_slider_0=0.5,
     clip_normal_0=(-1, 0, 0),
     clip_planes=True)
```

### 斑马纹分析

用于检查曲面连续性。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `zebra_count` | int | 0 | 斑马纹条数（0=关闭） |
| `zebra_opacity` | float | 0.5 | 斑马纹不透明度 |
| `zebra_direction` | int | 0 | 方向（0=水平, 1=垂直） |
| `zebra_color_scheme` | str | None | 配色方案 |
| `zebra_mapping_mode` | int | None | 映射模式 |

**曲面分析示例**：

```python
# 检查圆角过渡是否光滑
show(part,
     zebra_count=15,
     zebra_direction=0,
     zebra_opacity=0.7)
```

### Studio 环境

PBR 物理渲染环境参数。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `studio_environment` | StudioEnvironment | None | 环境贴图 |
| `studio_env_intensity` | float | 1.0 | 环境光强度 |
| `studio_env_rotation` | float | 0 | 环境贴图旋转角度 |
| `studio_background` | bool | True | 显示环境背景 |
| `studio_tone_mapping` | str | None | 色调映射 |
| `studio_exposure` | float | 1.0 | 曝光值 |
| `studio_shadow_intensity` | float | 0.5 | 阴影强度 |
| `studio_shadow_softness` | float | 0.5 | 阴影柔和度 |
| `studio_ao_intensity` | float | 0.5 | 环境遮蔽强度 |
| `studio_texture_mapping` | int | None | 纹理映射模式 |
| `studio_4k_env_maps` | bool | False | 使用 4K 环境贴图 |

**StudioEnvironment 枚举**（部分）：

| 值 | 说明 |
|-----|------|
| `StudioEnvironment.AMBIENT_OCCLUSION` | 环境遮蔽 |
| `StudioEnvironment.CERAMIC` | 陶瓷 |
| `StudioEnvironment.METALLIC` | 金属 |
| `StudioEnvironment.PLASTIC` | 塑料 |

### 渲染精度

控制三角面片精度，影响显示质量和性能。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `deviation` | float | 0.1 | 弦偏差（越小越精细） |
| `angular_tolerance` | float | 0.2 | 角度公差（弧度） |
| `edge_accuracy` | float | None | 边线精度 |

**精度 vs 性能**：

| deviation | angular_tolerance | 适用场景 |
|-----------|-------------------|---------|
| 0.5 | 0.5 | 快速预览（大型装配） |
| 0.1 | 0.2 | 默认（日常使用） |
| 0.01 | 0.05 | 精细渲染（截图/演示） |

### 颜色与材质默认值

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `default_color` | str/tuple | None | 默认面颜色 |
| `default_edgecolor` | str/tuple | None | 默认边线颜色 |
| `metalness` | float | 0.3 | 金属度 (0.0~1.0) |
| `roughness` | float | 0.65 | 粗糙度 (0.0~1.0) |
| `ambient_intensity` | float | 1.0 | 环境光强度 |
| `direct_intensity` | float | 1.1 | 直射光强度 |

### 交互速度

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `pan_speed` | float | 1.0 | 平移速度 |
| `rotate_speed` | float | 1.0 | 旋转速度 |
| `zoom_speed` | float | 1.0 | 缩放速度 |

### 调试

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `debug` | bool | False | 调试模式 |
| `timeit` | bool | False | 显示渲染耗时 |

---

## 常用配置组合

| 场景 | 关键参数 | 说明 |
|------|---------|------|
| **快速预览** | `deviation=0.5, modes=[Render.FACES]` | 大型装配时提升流畅度 |
| **精细渲染** | `deviation=0.01, angular_tolerance=0.05` | 截图/演示用 |
| **大型装配优化** | `collapse=Collapse.LEAVES, modes=[Render.FACES]` | 30+ 零件时防止卡顿 |
| **截图导出** | `glass=True, tools=False` | 干净的导出画面 |
| **曲面分析** | `zebra_count=15, zebra_direction=0` | 检查曲面连续性 |
| **截面查看** | `clip_slider_0=0.5, clip_planes=True` | 查看内部结构 |
| **透明装配** | `transparent=True, default_opacity=0.3` | 查看内部零件 |
| **工程图风格** | `black_edges=True, default_color="white"` | 白底黑线 |

---

## 完整配置示例

### 日常开发

```python
from ocp_vscode import show

show(part,
     axes=True,
     grid=(True, False, False),
     deviation=0.1)
```

### 装配预览

```python
show(body, lid, bolts,
     names=["body", "lid", "bolts"],
     colors=["steelblue", "orange", "gray"],
     collapse=Collapse.LEAVES,
     tree_width=300)
```

### 高质量截图

```python
show(part,
     glass=True,
     tools=False,
     deviation=0.01,
     angular_tolerance=0.05,
     default_color="steelblue",
     default_edgecolor=(0.15, 0.15, 0.15),
     metalness=0.5,
     roughness=0.4)
```

### 调试模式

```python
show(part,
     debug=True,
     timeit=True,
     axes=True,
     axes0=True,
     grid=(True, True, False))
```

---

## show_all() 与 show_object()

| 函数 | 说明 |
|------|------|
| `show(*objects)` | 主函数，替换当前显示内容 |
| `show_all()` | 显示当前作用域内所有 build123d 对象 |
| `show_object(obj)` | CQ-editor 兼容接口（不推荐） |

```python
# show_all() 自动收集所有变量
with BuildPart() as box:
    Box(10, 10, 10)

with BuildPart() as cyl:
    Cylinder(5, 20)

# 自动显示 box 和 cyl
show_all()
```

---

## 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| 显示空白 | OCP Viewer 未启动 | VS Code 中按 Ctrl+Shift+P → "OCP CAD Viewer" |
| 颜色不生效 | 形状自带颜色覆盖 | 用 `colors` 参数显式指定 |
| 显示卡顿 | 精度太高 | 降低 `deviation` 值或用 `Collapse.LEAVES` |
| 边线锯齿 | `edge_accuracy` 不够 | 提高 `edge_accuracy` 或 `deviation` |
| 透视变形 | 默认正交投影 | 设 `ortho=False` 切换到透视 |
