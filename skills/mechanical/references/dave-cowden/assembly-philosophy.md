# Dave Cowden 装配哲学

> CadQuery 创始人 Dave Cowden 关于多体零件、装配设计和工具边界的思维框架。

---

## 1. 为什么没有约束求解器

build123d / CadQuery **刻意不提供**传统 CAD 的装配约束求解器（如 SolidWorks 的"配合"系统）。

这是设计选择，不是功能缺失：

- **约束求解器超出 BREP 几何范围**：BREP 内核（OpenCASCADE）负责几何和拓扑，不负责物理关系
- **避免过度约束/欠约束的调试地狱**：传统 CAD 的约束系统是最大的用户痛点之一
- **Python 编排更灵活**：用代码逻辑组织装配，比声明式约束更透明

> *"如果你发现自己在写约束求解器，你可能在做不该做的事。用 Python 函数组合零件位置，比任何内置约束系统都更清晰。"*

---

## 2. 装配逻辑在 Python 中编排

### 核心原则：函数组合 > 内置约束系统

```python
# ✅ Python 编排：逻辑清晰，可调试
def assemble_hinge(leaf_a, leaf_b, pin, angle=0):
    """铰链装配 — 纯 Python 函数"""
    assy_b = Rot(0, 0, angle) * Pos(0, 0, 0) * leaf_b
    return Compound(children=[leaf_a, assy_b, pin])

# 改变角度只需改一个参数
open_hinge = assemble_hinge(leaf_a, leaf_b, pin, angle=90)
closed_hinge = assemble_hinge(leaf_a, leaf_b, pin, angle=0)
```

### Joints 系统的定位

Joints 是 **辅助定位工具**，不是约束求解器：
- `connect_to()` 执行的是一次性的位置计算
- 它不会自动更新、不会求解冲突、不会保持约束关系
- 它是 Python 编排的便利工具，不是替代品

```python
# Joints 只是简化了位置计算
base.joints["top"].connect_to(arm.joints["bottom"])
# 等价于手动计算：
# arm.locate(计算出的 Location)
```

---

## 3. 设计意图跨越多体

选择器在 Compound 中仍然有效：

```python
assembly = Compound(children=[body, lid, screws])

# 选择器穿透装配层级
all_holes = assembly.faces().filter_by(GeomType.CYLINDER)
top_faces = assembly.faces().sort_by(Axis.Z)[-5:]  # 最高的5个面
```

**关键洞察**：设计意图不因零件拆分而丢失。`sort_by` / `filter_by` 在单体和多体上行为一致。

---

## 4. STEP 作为装配知识载体

### 多体 STEP 保留拓扑关系

```python
# 导出多体 STEP — 保留零件层级
assembly = Compound(children=[body, lid, pin])
assembly.label = "hinge_assembly"
body.label = "body"
lid.label = "lid"
pin.label = "pin"
export_step(assembly, "hinge_assembly.step")

# 导入后零件层级完整
imported = import_step("hinge_assembly.step")
for child in imported.children:
    print(child.label)  # body, lid, pin
```

### STEP vs 多个独立文件

| 方式 | 优点 | 缺点 |
|------|------|------|
| 单个多体 STEP | 保留层级关系，一个文件 | 修改单个零件需重新导出 |
| 多个独立 STEP | 零件独立修改 | 需要脚本管理装配关系 |
| **混合（推荐）** | 零件独立 STEP + 装配脚本 | 最灵活 |

---

## 5. 诚实边界

Dave Cowden 的核心品质之一：**明确说清什么不能做**。

### build123d 装配能力边界

| 能力 | build123d 范围 | 超出范围 → 推荐工具 |
|------|---------------|-------------------|
| 零件定位 | ✅ Pos/Rot/Location 算术 | — |
| 关节建模 | ✅ 5 种 Joint 类型 | — |
| 简单干涉检查 | ✅ `do_children_intersect()` | 精密碰撞分析 → MeshLab/FreeCAD |
| 打印排版 | ✅ `pack()` | — |
| **约束求解** | ❌ 无 | SolidWorks / Fusion 360 |
| **运动仿真** | ❌ 无 | PyBullet / MuJoCo / Gazebo |
| **有限元分析** | ❌ 无 | FreeCAD FEM / ANSYS / Abaqus |
| **GCode 生成** | ❌ 无 | FreeCAD Path / Fusion 360 CAM |
| **精密齿轮** | ⚠️ 近似 | 专业齿轮软件 (KISSsoft) |
| **大型装配 (>50件)** | ⚠️ 性能下降 | SolidWorks / Creo |

### 表达方式

Dave Cowden 的原则：**说"还不行"，不说"不可能"**。

```
❌ "build123d 不能做运动仿真"
✅ "运动仿真超出 BREP 几何建模范围。build123d 可以导出 STEP 给 PyBullet/MuJoCo，
    Joint 参数可以映射到 URDF 关节描述。"
```

---

## 6. 装配设计决策树

```
用户需求
├── 单个零件 → BuildPart 直接建模
├── 2-5 个零件
│   ├── 固定关系 → Compound + Pos/Rot 定位
│   └── 运动关系 → Joints + connect_to
├── 5-20 个零件
│   ├── 简单层级 → Compound.children + labels
│   └── 关节链（如四足腿）→ 串联 RevoluteJoint
└── 20+ 个零件
    ├── 拆分子装配 → 每个子装配一个 Compound
    ├── 命名规范 → "{subsystem}_{part}_{index}"
    ├── 独立 STEP 文件 → 装配脚本管理
    └── 性能优化 → copy.copy() 减少内存
```

---

## 7. 核心态度

1. **几何是基础**：先把每个零件的几何做对，装配是第二步
2. **Python 是粘合剂**：装配逻辑用 Python 函数，不用 DSL
3. **STEP 是交付物**：零件和装配都以 STEP 为最终输出
4. **承认边界**：该交给专业工具的就交出去，不在 BREP 层做不该做的事
5. **简单胜过复杂**：能用 `Pos * Rot * Shape` 解决的，不引入 Joints；能用 Joints 的，不引入约束求解器
