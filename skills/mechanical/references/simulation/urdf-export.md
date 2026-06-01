# URDF 导出 (build123d → URDF)

> build123d 四足腿链 → .urdf + .stl 文件集 → PyBullet/ROS 加载

---

## 1. URDF 格式速查

URDF (Unified Robot Description Format) 由 `<link>` 和 `<joint>` 组成：

```xml
<robot name="quadruped">
  <!-- Link: 零件几何 + 物理属性 -->
  <link name="body">
    <visual>
      <geometry><mesh filename="meshes/body.stl"/></geometry>
    </visual>
    <collision>
      <geometry><mesh filename="meshes/body.stl"/></geometry>
    </collision>
    <inertial>
      <mass value="0.5"/>
      <inertia ixx="0.001" ixy="0" ixz="0" iyy="0.001" iyz="0" izz="0.001"/>
    </inertial>
  </link>

  <!-- Joint: 连接两个 link -->
  <joint name="hip_joint" type="revolute">
    <parent link="body"/>
    <child link="upper_leg"/>
    <origin xyz="0.08 0.05 0" rpy="0 0 0"/>
    <axis xyz="0 0 1"/>
    <limit lower="-0.785" upper="0.785" effort="10" velocity="5"/>
  </joint>
</robot>
```

### URDF 关键元素

| 元素 | 说明 |
|------|------|
| `<link>` | 一个刚体（含 visual/collision/inertial） |
| `<joint>` | 连接两个 link 的运动副 |
| `<visual>` | 渲染用几何（mesh 或基元） |
| `<collision>` | 碰撞检测用几何（可简化） |
| `<inertial>` | 质量 + 惯性张量 |
| `<origin>` | 子 link 相对于父 link 的变换 |
| `<axis>` | 关节运动轴（单位向量） |
| `<limit>` | 角度/速度/力矩限位 |

### Joint 类型映射

| URDF type | DOF | build123d Joint |
|-----------|-----|----------------|
| `fixed` | 0 | `RigidJoint` |
| `revolute` | 1 | `RevoluteJoint` |
| `prismatic` | 1 | `LinearJoint` |
| `continuous` | 1 | `RevoluteJoint`（无限位） |
| `floating` | 6 | — |
| `planar` | 2 | — |

> build123d `BallJoint` (3 DOF) 在 URDF 中需要拆分为 3 个虚拟 revolute joints。

---

## 2. build123d → URDF 映射

### 核心思路

```
build123d Compound
├── children[0] → <link name="body">
├── children[1] → <link name="upper_leg">
├── ...
└── joints → <joint> 列表
    ├── joint.label → name
    ├── joint 类型 → type
    ├── joint.angular_range → <limit>
    └── joint 位置 → <origin>
```

### 端到端工作流

```
build123d 四足模型
    │
    ▼ export_stl() 逐个 link
meshes/body.stl, meshes/upper_leg.stl, ...
    │
    ▼ 遍历 Compound.joints
生成 robot.urdf XML
    │
    ▼ yourdfpy 验证
可视化检查
    │
    ▼ PyBullet / ROS 加载
仿真运行
```

### 自动导出脚本

```python
"""build123d Compound → URDF"""
import xml.etree.ElementTree as ET
from build123d import *

def compound_to_urdf(compound, robot_name="robot",
                     density=1.24e-6,  # PLA kg/mm³
                     mesh_dir="meshes"):
    """
    将 build123d Compound 转换为 URDF XML。

    compound: 含 children 和 joints 的 Compound
    density: 材料密度 (kg/mm³)，PLA ≈ 1.24e-6
    mesh_dir: STL 文件存放目录
    返回: xml.etree.ElementTree
    """
    robot = ET.Element("robot", name=robot_name)

    # 遍历 children → <link>
    for i, child in enumerate(compound.children):
        link_name = child.label or f"link_{i}"
        link_elem = ET.SubElement(robot, "link", name=link_name)

        # STL mesh 路径
        stl_path = f"{mesh_dir}/{link_name}.stl"

        # Visual
        visual = ET.SubElement(link_elem, "visual")
        geom = ET.SubElement(visual, "geometry")
        ET.SubElement(geom, "mesh", filename=stl_path, scale="0.001 0.001 0.001")

        # Collision（同 visual）
        collision = ET.SubElement(link_elem, "collision")
        geom_c = ET.SubElement(collision, "geometry")
        ET.SubElement(geom_c, "mesh", filename=stl_path, scale="0.001 0.001 0.001")

        # Inertial
        mass_kg = child.volume * density  # mm³ × kg/mm³ = kg
        inertial = ET.SubElement(link_elem, "inertial")
        ET.SubElement(inertial, "mass", value=f"{mass_kg:.6f}")

        # 简化惯性（包围盒近似）
        bb = child.bounding_box()
        lx = bb.size.X / 1000  # mm → m
        ly = bb.size.Y / 1000
        lz = bb.size.Z / 1000
        ixx = mass_kg * (ly**2 + lz**2) / 12
        iyy = mass_kg * (lx**2 + lz**2) / 12
        izz = mass_kg * (lx**2 + ly**2) / 12
        ET.SubElement(inertial, "inertia",
                      ixx=f"{ixx:.8f}", ixy="0", ixz="0",
                      iyy=f"{iyy:.8f}", iyz="0",
                      izz=f"{izz:.8f}")

    # 遍历 joints → <joint>
    for jname, joint in compound.joints.items():
        joint_type = _map_joint_type(joint)
        joint_elem = ET.SubElement(robot, "joint",
                                   name=jname, type=joint_type)

        # parent/child（从 joint 的 to_part 和 label 推断）
        ET.SubElement(joint_elem, "parent", link=_get_parent(joint))
        ET.SubElement(joint_elem, "child", link=_get_child(joint))

        # Origin（mm → m）
        pos = joint.relative_to.IsSetPosition if hasattr(joint, 'relative_to') else (0, 0, 0)
        xyz = f"{pos[0]/1000:.6f} {pos[1]/1000:.6f} {pos[2]/1000:.6f}"
        ET.SubElement(joint_elem, "origin", xyz=xyz, rpy="0 0 0")

        # Axis
        if hasattr(joint, 'axis'):
            ax = joint.axis
            ET.SubElement(joint_elem, "axis", xyz=f"{ax.X} {ax.Y} {ax.Z}")
        else:
            ET.SubElement(joint_elem, "axis", xyz="0 0 1")

        # Limits
        if hasattr(joint, 'angular_range') and joint.angular_range:
            lo, hi = joint.angular_range
            import math
            ET.SubElement(joint_elem, "limit",
                          lower=f"{math.radians(lo):.4f}",
                          upper=f"{math.radians(hi):.4f}",
                          effort="10", velocity="5")

    return ET.ElementTree(robot)


def _map_joint_type(joint):
    """build123d Joint → URDF joint type"""
    type_name = type(joint).__name__
    mapping = {
        "RigidJoint": "fixed",
        "RevoluteJoint": "revolute",
        "LinearJoint": "prismatic",
        "CylindricalJoint": "revolute",  # 近似
        "BallJoint": "fixed",  # 需要拆分，此处先标 fixed
    }
    return mapping.get(type_name, "fixed")


def _get_parent(joint):
    """从 joint 推断父 link 名"""
    if hasattr(joint, 'parent') and hasattr(joint.parent, 'label'):
        return joint.parent.label or "base_link"
    return "base_link"


def _get_child(joint):
    """从 joint 推断子 link 名"""
    if hasattr(joint, 'child') and hasattr(joint.child, 'label'):
        return joint.child.label or "child_link"
    return "child_link"
```

### STL Mesh 批量导出

```python
"""逐 link 导出 STL"""
import os

def export_meshes(compound, output_dir="meshes"):
    """将 Compound 的每个 child 导出为 STL"""
    os.makedirs(output_dir, exist_ok=True)

    for i, child in enumerate(compound.children):
        name = child.label or f"link_{i}"
        path = os.path.join(output_dir, f"{name}.stl")
        export_stl(child, path)
        print(f"  {name} → {path} ({child.volume:.0f} mm³)")
```

---

## 3. BallJoint 拆分策略

URDF 不支持 3-DOF 球铰，需要拆分为 3 个虚拟 revolute joints：

```xml
<!-- BallJoint → 3 个虚拟关节 -->
<link name="ball_virtual_rx"><inertial><mass value="0.001"/>...</inertial></link>
<link name="ball_virtual_ry"><inertial><mass value="0.001"/>...</inertial></link>

<joint name="ball_rx" type="revolute">
  <parent link="parent_link"/>
  <child link="ball_virtual_rx"/>
  <axis xyz="1 0 0"/>
</joint>

<joint name="ball_ry" type="revolute">
  <parent link="ball_virtual_rx"/>
  <child link="ball_virtual_ry"/>
  <axis xyz="0 1 0"/>
</joint>

<joint name="ball_rz" type="revolute">
  <parent link="ball_virtual_ry"/>
  <child link="child_link"/>
  <axis xyz="0 0 1"/>
</joint>
```

虚拟 link 质量设为极小值（0.001 kg），避免影响动力学。

---

## 4. yourdfpy 验证

```python
"""URDF 验证 — yourdfpy"""
# pip install yourdfpy
import yourdfpy

# 加载并可视化
urdf = yourdfpy.URDF.load("robot.urdf")

# 检查结构
print(f"Links:  {[l.name for l in urdf.link_map.values()]}")
print(f"Joints: {[j.name for j in urdf.joint_map.values()]}")

# 可视化（需要 trimesh 后端）
urdf.show()

# 设置关节角度
cfg = {"hip_joint": 0.0, "upper_joint": -0.5, "lower_joint": 1.0}
urdf.update_cfg(cfg)
urdf.show()
```

---

## 5. 常见陷阱

| 陷阱 | 说明 | 解决 |
|------|------|------|
| **单位不一致** | build123d 用 mm，URDF 用 m | STL mesh 用 `scale="0.001 0.001 0.001"` |
| **坐标系方向** | build123d Z-up，URDF 无强制但 ROS 惯例 Z-up | 一般无需转换 |
| **mesh 路径** | PyBullet 要求相对路径或绝对路径 | 用 `package://` 或同目录相对路径 |
| **质心偏移** | STL 原点可能不在质心 | `<inertial>` 中加 `<origin>` 偏移 |
| **关节轴线** | DH 的 z 轴 vs URDF 的 axis | 确认轴向一致 |
| **多余 link** | BallJoint 拆分产生虚拟 link | 质量设极小值 |

---

## 6. 参考工具

| 工具 | 安装 | 用途 |
|------|------|------|
| yourdfpy | `pip install yourdfpy` | URDF 读写/可视化 |
| urchin | `pip install urchin` | 新一代 URDF 库 |
| onshape-to-robot | GitHub | CAD→URDF 参考架构 |
| urdf-viz (Rust) | `cargo install urdf-viz` | 轻量 URDF 查看器 |
