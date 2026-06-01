# OCP 视觉验证

> 使用 OCP CAD Viewer 进行零件和装配的视觉检查方法。

---

## 1. 截图对比

```python
from ocp_vscode import show, save_screenshot

# 显示零件
show(part,
     glass=True,
     tools=False,
     reset_camera=Camera.ISO)

# 保存截图（用于与设计意图对比）
save_screenshot("part_view.png")
```

### 多角度截图

```python
from ocp_vscode import Camera

# 正视图
show(part, reset_camera=Camera.FRONT)
save_screenshot("front.png")

# 俯视图
show(part, reset_camera=Camera.TOP)
save_screenshot("top.png")

# 等轴测
show(part, reset_camera=Camera.ISO)
save_screenshot("iso.png")
```

---

## 2. 剖面检查

使用 `clip_slider` 切开零件查看内部结构：

```python
# 沿 Z 轴切半 — 查看内部壁厚和空腔
show(part,
     clip_slider_0=0.5,       # Z 方向切到一半
     clip_normal_0=(0, 0, -1),  # 切面法向量
     clip_planes=True,         # 显示切面辅助线
     clip_object_colors=True)  # 切面用零件颜色

# 沿 X 轴切 — 查看截面轮廓
show(part,
     clip_slider_1=0.5,
     clip_normal_1=(-1, 0, 0),
     clip_planes=True)
```

### 剖面检查要点

| 检查内容 | 方法 | 期望结果 |
|---------|------|---------|
| 壁厚均匀性 | Z 轴剖面 | 各处壁厚一致 |
| 空腔形状 | 多方向剖面 | 空腔与设计一致 |
| 孔贯通性 | 沿孔轴剖切 | 孔完全贯通（或盲孔深度正确） |
| 布尔运算残留 | 各方向剖面 | 无多余实体残留 |
| Shell 质量 | 任意方向剖面 | 无穿透/薄壁缺陷 |

---

## 3. 斑马纹曲面分析

斑马纹（Zebra Stripes）模拟反射条纹，用于检查曲面连续性：

```python
# 基本斑马纹检查
show(part,
     zebra_count=9,            # 条纹数量（2-50）
     zebra_direction=0,        # 条纹方向角（0-90°）
     zebra_opacity=1.0,        # 条纹不透明度
     zebra_color_scheme="blackwhite")  # 颜色方案
```

### 如何解读斑马纹

| 条纹表现 | 连续性等级 | 含义 |
|---------|----------|------|
| 条纹断裂（错位） | G0 | 面相连但不光滑 |
| 条纹连续但有折角 | G1 | 切线连续，曲率不连续 |
| 条纹平滑流畅 | G2 | 曲率连续（工业级光滑） |

### 多方向检查

```python
# 方向 1：水平条纹
show(part, zebra_count=15, zebra_direction=0)

# 方向 2：45° 斜条纹
show(part, zebra_count=15, zebra_direction=45)

# 方向 3：垂直条纹
show(part, zebra_count=15, zebra_direction=90)
```

> 三个方向都平滑 → 曲面质量优秀

### 颜色方案

| 方案 | 值 | 适用场景 |
|------|-----|---------|
| 黑白 | `"blackwhite"` | 默认，对比度最高 |
| 灰度 | `"grayscale"` | 柔和，适合曲面细节 |
| 彩色 | `"colorful"` | 装饰性，演示用 |

---

## 4. 装配间隙可视化

```python
# 半透明显示 — 检查零件间干涉
show(body, lid, pin,
     names=["body", "lid", "pin"],
     colors=["steelblue", "orange", "gray"],
     transparent=True,
     default_opacity=0.4)

# 可以旋转查看是否有零件重叠（干涉）
# 重叠区域颜色会变深
```

### 配合检查

```python
# 显示轴和孔的配合关系
show(shaft, housing,
     names=["shaft", "housing"],
     colors=["red", "blue"],
     transparent=True,
     default_opacity=0.3,
     axes=True)
```

---

## 5. 关节运动检查

```python
from ocp_vscode import show

# 显示关节轴线和范围
show(assembly,
     render_joints=True,      # 渲染关节符号
     helper_scale=0.5)        # 关节符号大小

# 关节符号说明：
# - RevoluteJoint: 圆环 + 轴线
# - LinearJoint: 直线 + 圆环
# - BallJoint: 三个正交圆环 (XYZ)
# - RigidJoint: XYZ 坐标轴指示器
```

### 运动范围验证

```python
from ocp_vscode import Animation

# 用动画验证关节运动范围
animation = Animation()

# RevoluteJoint 旋转范围测试
# 从最小角度到最大角度
min_angle, max_angle = joint.angular_range
animation.add_track("/Group/part_name", "rz",
                    [0, 2, 4],
                    [min_angle, max_angle, min_angle])
animation.animate(0.5)  # 慢速播放，仔细检查
```

---

## 6. 视觉验证清单

| 检查项 | 方法 | 通过标准 |
|--------|------|---------|
| 外形正确 | 等轴测截图 | 与设计草图一致 |
| 内部结构 | 剖面检查 | 壁厚均匀，无残留 |
| 曲面质量 | 斑马纹（3方向） | G1 以上连续 |
| 装配干涉 | 半透明叠加 | 无重叠区域 |
| 关节范围 | 动画验证 | 运动范围内无碰撞 |
| 对称性 | 正视/侧视截图 | 对称特征一致 |
| 孔位分布 | 俯视截图 | 孔位与设计图一致 |
