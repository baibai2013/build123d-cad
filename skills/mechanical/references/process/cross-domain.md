# 跨领域对接指南

> build123d 零件与 FEA 力学分析、运动学仿真、PCB 外壳、电子硬件的对接方法。

---

## 1. FEA 力学分析

### 工作流

```
build123d 建模 → export_step() → FEA 软件导入 → 网格划分 → 加载/约束 → 求解 → 结果分析
```

### 支持的 FEA 软件

| 软件 | STEP 导入 | 适合场景 | 许可证 |
|------|----------|---------|-------|
| FreeCAD FEM | ✅ AP203/214 | 简单静力学 | 开源免费 |
| ANSYS | ✅ AP203/214 | 全面分析 | 商业 |
| Abaqus | ✅ AP203/214 | 非线性/接触 | 商业 |
| Calculix (via FreeCAD) | ✅ 经 FreeCAD | 静力/热分析 | 开源免费 |

### build123d 端准备

```python
from build123d import *

# 建模时注意：
# 1. 保留面标签（用于指定载荷面和约束面）
with BuildPart() as bracket:
    Box(60, 40, 5)
    # ... 建模操作

# 2. 导出高精度 STEP
export_step(bracket.part, "bracket_fea.step",
            precision_mode=PrecisionMode.GREATEST)

# 3. 记录关键面信息（写入注释或文档）
top = bracket.faces().sort_by(Axis.Z)[-1]
bottom = bracket.faces().sort_by(Axis.Z)[0]
print(f"顶面面积: {top.area:.2f} mm²")   # 载荷施加面
print(f"底面面积: {bottom.area:.2f} mm²")  # 固定约束面
```

### 网格划分建议

| 特征 | 网格尺寸 | 说明 |
|------|---------|------|
| 全局 | 零件最小尺寸 / 10 | 基准网格大小 |
| 应力集中区 | 全局 / 3~5 | 圆角、孔边缘加密 |
| 薄壁 | 壁厚方向 ≥ 3 层 | 确保弯曲精度 |
| 接触面 | 对齐/加密 | 装配分析时 |

### 材料属性参考

| 材料 | 密度 (g/cm³) | 弹性模量 (GPa) | 泊松比 | 屈服强度 (MPa) |
|------|-------------|---------------|--------|--------------|
| PLA | 1.24 | 3.5 | 0.36 | 60 |
| ABS | 1.04 | 2.3 | 0.35 | 40 |
| 铝 6061-T6 | 2.70 | 69 | 0.33 | 276 |
| 碳钢 Q235 | 7.85 | 210 | 0.30 | 235 |
| 尼龙 PA12 | 1.01 | 1.7 | 0.40 | 50 |

### 质量/惯性矩估算

```python
# build123d 内置体积计算
volume_mm3 = part.part.volume
density = 1.24e-3  # PLA g/mm³ (1.24 g/cm³)
mass_g = volume_mm3 * density

# 惯性矩（近似）— 用包围盒估算
bb = part.part.bounding_box()
Lx, Ly, Lz = bb.size.X, bb.size.Y, bb.size.Z
# 长方体近似惯性矩 (kg·mm²)
mass_kg = mass_g / 1000
Ixx = mass_kg * (Ly**2 + Lz**2) / 12
Iyy = mass_kg * (Lx**2 + Lz**2) / 12
Izz = mass_kg * (Lx**2 + Ly**2) / 12
print(f"质量: {mass_g:.1f} g")
print(f"惯性矩: Ixx={Ixx:.1f}, Iyy={Iyy:.1f}, Izz={Izz:.1f} kg·mm²")
```

---

## 2. 运动学/动力学仿真

### build123d → URDF 映射

```
build123d Joint → URDF <joint> 映射：
├── RevoluteJoint → <joint type="revolute">
│   ├── axis → <axis xyz="...">
│   ├── angular_range → <limit lower="..." upper="...">
│   └── location → <origin xyz="..." rpy="...">
├── LinearJoint → <joint type="prismatic">
│   ├── axis → <axis xyz="...">
│   └── linear_range → <limit lower="..." upper="...">
├── RigidJoint → <joint type="fixed">
├── BallJoint → 需拆分为 3 个 revolute joints
└── CylindricalJoint → 需拆分为 revolute + prismatic
```

### URDF 生成辅助

```python
# 从 build123d Joint 参数生成 URDF 片段
def joint_to_urdf(joint, parent_link, child_link):
    """将 build123d Joint 转换为 URDF XML 片段"""
    if isinstance(joint, RevoluteJoint):
        axis = joint.relative_axis.direction
        lo, hi = joint.angular_range
        return f"""
<joint name="{joint.label}" type="revolute">
  <parent link="{parent_link}"/>
  <child link="{child_link}"/>
  <axis xyz="{axis.X:.3f} {axis.Y:.3f} {axis.Z:.3f}"/>
  <limit lower="{lo * 3.14159/180:.4f}" upper="{hi * 3.14159/180:.4f}"
         effort="10" velocity="1.0"/>
</joint>"""
    elif isinstance(joint, RigidJoint):
        return f"""
<joint name="{joint.label}" type="fixed">
  <parent link="{parent_link}"/>
  <child link="{child_link}"/>
</joint>"""
```

### 推荐仿真工具

| 工具 | 适用场景 | Python 接口 | 学习曲线 |
|------|---------|------------|---------|
| PyBullet | 快速原型，机器人 | ✅ pybullet | 低 |
| MuJoCo | 精确动力学，强化学习 | ✅ mujoco | 中 |
| Gazebo | ROS 生态，传感器仿真 | ✅ via ROS | 高 |
| Drake | 接触力学，运动规划 | ✅ pydrake | 高 |

### OCP 动画作为初步运动验证

在进入完整仿真之前，用 OCP Animation 快速验证关节范围和运动合理性：

```python
# 验证四足腿部运动范围
animation = Animation()
# 髋关节：前后摆动 ±30°
animation.add_track("/Group/upper_leg", "rz",
                    [0, 1, 2, 3, 4],
                    [0, 30, 0, -30, 0])
# 膝关节：弯曲 0~90°
animation.add_track("/Group/lower_leg", "rz",
                    [0, 1, 2, 3, 4],
                    [0, -45, -90, -45, 0])
animation.animate(1)
```

---

## 3. PCB 外壳对接

### 从 Gerber/DXF 提取 PCB 信息

```python
# 从 DXF 文件导入 PCB 外轮廓
pcb_outline = import_svg("pcb_outline.dxf")  # 或手动输入尺寸

# PCB 关键参数（从 EDA 软件导出）
pcb_params = {
    "length": 50,        # mm
    "width": 30,
    "thickness": 1.6,
    "mount_holes": [     # 安装孔坐标 (x, y, diameter)
        (-20, -10, 2.5),  # M2.5
        (20, -10, 2.5),
        (-20, 10, 2.5),
        (20, 10, 2.5),
    ],
    "connectors": [      # 接插件 (x, y, type, width, height)
        (25, 0, "USB-C", 9.5, 3.5),
        (-25, 5, "FPC-10P", 12, 1.5),
    ],
}
```

### 常见接插件开口尺寸

| 接插件 | 开口宽度 | 开口高度 | 备注 |
|--------|---------|---------|------|
| USB-C | 9.5mm | 3.5mm | +0.5mm 间隙 |
| USB-A | 14mm | 7mm | +0.5mm 间隙 |
| Micro USB | 8mm | 3mm | +0.5mm 间隙 |
| 3.5mm 耳机 | Ø7mm | — | 圆孔 |
| FPC 10P (0.5mm) | 7mm | 2mm | +0.3mm 间隙 |
| FPC 20P (0.5mm) | 12mm | 2mm | +0.3mm 间隙 |
| 排针 2.54mm 1×4 | 11mm | 9mm | +0.5mm 间隙 |

### 散热开口设计

```python
# 散热通风面积估算
power_w = 5           # 发热功率 (W)
temp_rise = 20        # 允许温升 (°C)
# 自然对流: 通风面积 ≈ 功率 × 15 cm² / 温升
vent_area_cm2 = power_w * 15 / temp_rise    # 3.75 cm²

# 实现：长条通风口阵列
slot_w, slot_l = 1.5, 15    # 单个通风槽 mm
slot_area = slot_w * slot_l  # 22.5 mm²
n_slots = int(vent_area_cm2 * 100 / slot_area) + 1  # ~17 个槽
```

---

## 4. 电子硬件尺寸参考

### 常见舵机

| 型号 | L×W×H (mm) | 输出轴 | 扭矩 | 重量 |
|------|-----------|--------|------|------|
| SG90 | 22.8×12.2×22.7 | 单侧 | 1.2 kg·cm | 9g |
| MG90S | 22.8×12.2×28.5 | 单侧 | 1.8 kg·cm | 14g |
| MG996R | 40.7×19.7×42.9 | 单侧 | 13 kg·cm | 55g |
| DS3218 | 40×20×40.5 | 双侧 | 21 kg·cm | 60g |

### 常见 MCU 板

| 板型 | L×W (mm) | 安装孔 | 接口 |
|------|---------|--------|------|
| Arduino Nano | 45×18 | 无标准 | Mini USB |
| Arduino Uno | 69×53 | 4×Ø3.2 | USB-B |
| ESP32-DevKit | 52×28 | 无标准 | Micro USB |
| RPi Pico | 51×21 | 4×Ø2.1 | Micro USB |
| RPi Zero 2W | 65×30 | 4×Ø2.75 | Mini HDMI + USB |
| Teensy 4.0 | 36×18 | 无标准 | Micro USB |

### 常见电池

| 型号 | 尺寸 | 电压 | 容量 | 重量 |
|------|------|------|------|------|
| 18650 | Ø18.5×65.5mm | 3.7V | 2000-3500mAh | 45-50g |
| 14500 | Ø14.5×53mm | 3.7V | 800-1200mAh | 22g |
| LiPo 1S 500mAh | ~30×20×6mm | 3.7V | 500mAh | 15g |
| LiPo 2S 1000mAh | ~55×30×12mm | 7.4V | 1000mAh | 55g |
| LiPo 3S 2200mAh | ~105×34×24mm | 11.1V | 2200mAh | 180g |

---

## 5. 对接工作流总结

```
CAD 设计 (build123d)
├── 零件建模 → export_step()
├── 装配验证 → show() + do_children_intersect()
│
├── FEA 分析
│   └── STEP → FreeCAD FEM → 应力/变形 → 修改设计
│
├── 运动仿真
│   ├── Joint 参数 → URDF 生成
│   └── STEP → STL(低精度) → PyBullet/MuJoCo
│
├── PCB 对接
│   ├── PCB DXF → 壳体内腔设计
│   └── 接插件尺寸 → 开口定位
│
└── 制造
    ├── CNC → STEP → CAM 软件
    ├── 3D 打印 → STL/3MF → 切片软件
    └── 激光切割 → DXF → 切割机
```
