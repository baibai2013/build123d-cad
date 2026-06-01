# 机电一体化安装实战

> 从 CAD 几何到真实硬件的安装经验，覆盖舵机、PCB、传感器、线缆、电池仓。

---

## 1. 舵机/马达安装

### 常见舵机尺寸表

| 型号 | 尺寸 (L×W×H mm) | 输出轴高 | 安装孔距 | 扭矩 | 典型用途 |
|------|----------------|---------|---------|------|---------|
| SG90 | 22.8 × 12.2 × 22.7 | 27.7 | 双侧耳 27.6 | 1.2 kg·cm | 微型项目、机械猫耳朵 |
| MG90S | 22.8 × 12.2 × 28.5 | 31.0 | 同 SG90 | 1.8 kg·cm | 小型关节 |
| MG996R | 40.7 × 19.7 × 42.9 | 48.5 | 双侧耳 49.5 | 13 kg·cm | 中型关节、机械猫腿部 |
| DS3218 | 40.0 × 20.0 × 40.5 | 45.0 | 双侧耳 54.0 | 21 kg·cm | 大扭矩关节 |

### 安装座设计要点

```python
from build123d import *

# ===== SG90 舵机安装座参数 =====
servo_l, servo_w, servo_h = 22.8, 12.2, 22.7
ear_w = 32.2                    # 含耳朵总宽
ear_h = 2.5                     # 耳朵厚度
ear_z = 15.5                    # 耳朵到底部距离
mount_gap = 0.3                 # 装配间隙（FDM 打印）
wall = 2.5                      # 安装座壁厚

# ===== 建模 =====
cavity_l = servo_l + 2 * mount_gap
cavity_w = servo_w + 2 * mount_gap
outer_l = cavity_l + 2 * wall
outer_w = cavity_w + 2 * wall

with BuildPart() as mount:
    # 外壳
    Box(outer_l, outer_w, servo_h + wall)
    # 内腔
    with BuildSketch(mount.faces().sort_by(Axis.Z)[-1]):
        Rectangle(cavity_l, cavity_w)
    extrude(amount=-servo_h, mode=Mode.SUBTRACT)
    # 耳朵槽（侧面开槽让舵机耳朵卡入）
    with BuildSketch(mount.faces().sort_by(Axis.Z)[-1]):
        Rectangle(ear_w + 2 * mount_gap, cavity_w)
    extrude(amount=-ear_h, mode=Mode.SUBTRACT)

export_step(mount.part, "sg90_mount.step")
```

### 关键设计规则

- **输出轴对齐**：RevoluteJoint 的 axis 必须与舵机输出轴同轴
- **装配间隙**：FDM 打印每侧 +0.2~0.3mm，SLA 打印 +0.1mm
- **固定方式**：螺丝孔 > 卡扣 > 胶粘（可维护性优先）
- **减震**：高扭矩舵机加橡胶垫片，避免振动传递
- **出线口**：预留舵机线缆出口（宽度 ≥ 8mm）

---

## 2. PCB 安装

### 从 PCB 尺寸反推壳体

```python
from build123d import *

# ===== PCB 参数（从 Gerber/DXF 获取） =====
pcb_l, pcb_w, pcb_h = 50, 30, 1.6   # PCB 外形尺寸
comp_h = 8                            # 元器件最高高度
hole_positions = [                     # 安装孔坐标 (x, y)
    (-20, -10), (20, -10),
    (-20, 10),  (20, 10),
]
hole_r = 1.25                          # M2.5 安装孔半径

# ===== 壳体设计 =====
clearance = 1.0                        # PCB 到壳体间隙
wall_t = 2.0
standoff_h = 5                         # 固定柱高度

inner_l = pcb_l + 2 * clearance
inner_w = pcb_w + 2 * clearance
inner_h = standoff_h + pcb_h + comp_h + clearance
outer_l = inner_l + 2 * wall_t
outer_w = inner_w + 2 * wall_t
outer_h = inner_h + wall_t

with BuildPart() as enclosure:
    Box(outer_l, outer_w, outer_h)
    # 抽壳
    shell(enclosure.faces().sort_by(Axis.Z)[-1], thickness=-wall_t)
    # PCB 固定柱
    bottom = enclosure.faces().sort_by(Axis.Z)[0]
    with BuildSketch(bottom):
        with Locations(*hole_positions):
            Circle(hole_r + 1.5)       # 固定柱外径
    extrude(amount=standoff_h)
    # 固定柱螺纹孔
    with Locations(*hole_positions):
        Hole(radius=hole_r, depth=standoff_h)

export_step(enclosure.part, "pcb_enclosure.step")
```

### PCB 安装检查清单

| 检查项 | 要求 |
|--------|------|
| 安装孔对齐 | 固定柱中心与 PCB 安装孔误差 < 0.1mm |
| 接插件开口 | USB-C: 9.5×3.5mm, USB-A: 14×7mm, FPC: 按宽度+1mm |
| 最小间隙 | PCB 边缘到壳体壁 ≥ 1mm |
| 固定柱规格 | M2: Ø4×h, M2.5: Ø5×h, M3: Ø6×h |
| ESD 防护 | 金属壳体需预留接地柱 |

---

## 3. 传感器定位

### IMU（惯性测量单元）

- **安装方向**：水平放置，Z 轴朝上
- **避免振动**：用橡胶减震垫隔离
- **距重心**：尽量靠近机器人质心
- **远离磁场**：远离马达/喇叭 ≥ 30mm

### 接近/距离传感器

```python
# 传感器开窗设计
sensor_r = 5          # 传感器发射窗直径
cone_angle = 15       # 视角锥半角（度）
mount_depth = 10      # 嵌入壳体深度

# 壳体上挖窗口
with BuildSketch(enclosure.faces().sort_by(Axis.Y)[-1]):
    Circle(sensor_r + 0.5)          # 传感器孔 + 间隙
extrude(amount=-mount_depth, mode=Mode.SUBTRACT)
```

### 触摸传感器

- **贴合表面**：传感器面与壳体外表面平齐或微凸
- **壳体壁厚**：电容式触摸穿透 ≤ 3mm 壁厚
- **导电层**：壳体材料非导电时无需特殊处理

---

## 4. 线缆通道设计

### 穿线孔设计规则

| 规则 | 值 |
|------|-----|
| 最小孔径 | 线束直径 × 1.5 |
| 圆角 | 入口 R ≥ 1mm（防割线） |
| FPC 弯折半径 | ≥ 1mm（单次弯折），≥ 5mm（反复弯折） |
| 硅胶线弯折半径 | ≥ 3× 线径 |

### 应力释放设计

```python
# 穿线孔 + 入口倒角 + 夹线槽
cable_d = 3           # 线束直径
hole_d = cable_d * 1.5
chamfer_r = 1.5       # 入口倒角

with BuildSketch(wall_face):
    Circle(hole_d / 2)
extrude(amount=-wall_t, mode=Mode.SUBTRACT)

# 入口两侧倒角（防止线缆被锐边切割）
hole_edges = enclosure.edges().filter_by(GeomType.CIRCLE).sort_by(SortBy.RADIUS)
fillet(hole_edges, radius=chamfer_r)
```

### 线缆管理建议

- **关节处**：线缆沿旋转轴通过，减少弯折
- **多线束**：使用扁平线缆（FPC）减少体积
- **固线点**：每 30mm 设置一个夹线槽/卡扣
- **预留长度**：关节线缆长度 = 展开最大距离 × 1.2

---

## 5. 电池仓设计

### 常见电池尺寸

| 型号 | 尺寸 (Ø×L 或 L×W×H mm) | 电压 | 容量 | 典型用途 |
|------|-------------------------|------|------|---------|
| 18650 | Ø18.5 × 65.5 | 3.7V | 2000-3500mAh | 中型机器人 |
| 14500 | Ø14.5 × 53.0 | 3.7V | 800-1200mAh | 小型项目 |
| LiPo 1S 500mAh | 30 × 20 × 6 | 3.7V | 500mAh | 微型项目 |
| LiPo 2S 1000mAh | 55 × 30 × 12 | 7.4V | 1000mAh | 机械猫/小型机器人 |
| LiPo 3S 2200mAh | 105 × 34 × 24 | 11.1V | 2200mAh | 中大型机器人 |

### 电池仓设计模板

```python
from build123d import *

# ===== 18650 电池仓 =====
bat_d, bat_l = 18.5, 65.5
gap = 0.5                       # 装配间隙
spring_space = 3                # 弹簧触点空间
wall = 2

cavity_d = bat_d + 2 * gap
cavity_l = bat_l + 2 * spring_space
outer_d = cavity_d + 2 * wall

with BuildPart() as bat_holder:
    Cylinder(radius=outer_d / 2, height=cavity_l + wall)
    # 内腔
    with BuildSketch(bat_holder.faces().sort_by(Axis.Z)[-1]):
        Circle(cavity_d / 2)
    extrude(amount=-cavity_l, mode=Mode.SUBTRACT)
    # 散热通风口（侧面长槽）
    with PolarLocations(radius=outer_d / 2 - wall / 2, count=4):
        with BuildSketch(Plane.XZ):
            Rectangle(2, cavity_l * 0.6)
        extrude(amount=wall + 1, both=True, mode=Mode.SUBTRACT)

export_step(bat_holder.part, "battery_holder_18650.step")
```

### 电池仓设计要点

| 要点 | 说明 |
|------|------|
| 弹簧空间 | 每端 2-3mm（弹片触点）或 3-5mm（弹簧触点） |
| 极性标识 | 正极端壳体内壁加"+"凸起标记 |
| 散热 | 大功率放电时需开通风槽 |
| 可拆卸 | 电池仓盖用卡扣或螺丝固定 |
| 安全 | LiPo 电池需阻燃材料（PC/ABS），预留膨胀空间 |

---

## 6. 综合案例：机械猫腿部安装

```
腿部装配层级：
├── hip_mount（髋关节舵机座）— MG996R 安装座
│   └── RevoluteJoint("hip_pitch", axis=Axis.Y)
├── upper_leg（大腿）
│   ├── servo_pocket（膝关节舵机嵌入槽）
│   ├── cable_channel（线缆通道）
│   └── RevoluteJoint("knee_pitch", axis=Axis.Y)
├── lower_leg（小腿）
│   ├── sensor_window（距离传感器开窗）
│   └── RevoluteJoint("ankle_pitch", axis=Axis.Y)
└── foot_pad（足垫）— TPU 柔性打印
```

**关键设计约束**：
- 舵机力臂长度决定关节力矩 → 影响大腿/小腿长度
- 线缆沿关节旋转轴通过 → 减少弯折疲劳
- 距离传感器朝向前方 → 开窗位置在小腿前面板
- 足垫用 TPU 打印 → 增加抓地力，需预留多材料接合面
