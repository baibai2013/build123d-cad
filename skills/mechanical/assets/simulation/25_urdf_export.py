"""
URDF 导出 — build123d 四足腿链 → .urdf + .stl 文件集
从 build123d Compound 自动生成 URDF 文件。

用法：python 25_urdf_export.py
输出：output/quadruped.urdf + output/meshes/*.stl
"""
from build123d import *
import xml.etree.ElementTree as ET
from xml.dom import minidom
import os
import math

# ===== 参数 =====
OUTPUT_DIR = "output"
MESH_DIR = "meshes"
ROBOT_NAME = "quadruped_leg"
DENSITY = 1.24e-6  # PLA kg/mm³

# 腿参数 (mm)
d1 = 55
L1 = 100
L2 = 100
JOINT_R = 8    # 关节球半径
BONE_R = 5     # 骨骼半径


# ===== 构建四足单腿模型 =====
print("构建 build123d 腿链模型...")

# 身体连接块
body_block = Box(40, 40, 20)
body_block.label = "body"

# 大腿
upper_leg = Cylinder(radius=BONE_R, height=L1)
upper_leg.label = "upper_leg"

# 小腿
lower_leg = Cylinder(radius=BONE_R, height=L2)
lower_leg.label = "lower_leg"

# 足端
foot = Sphere(radius=10)
foot.label = "foot"

# 装配
parts = [body_block, upper_leg, lower_leg, foot]
assembly = Compound(children=parts)


# ===== 生成 URDF XML =====
print("生成 URDF...")

robot = ET.Element("robot", name=ROBOT_NAME)
robot.set("xmlns:xacro", "http://www.ros.org/wiki/xacro")

# --- Links ---
link_specs = [
    ("body",      body_block),
    ("upper_leg", upper_leg),
    ("lower_leg", lower_leg),
    ("foot",      foot),
]

for link_name, part in link_specs:
    link = ET.SubElement(robot, "link", name=link_name)

    # Visual
    visual = ET.SubElement(link, "visual")
    geom_v = ET.SubElement(visual, "geometry")
    ET.SubElement(geom_v, "mesh",
                  filename=f"{MESH_DIR}/{link_name}.stl",
                  scale="0.001 0.001 0.001")

    # Collision
    collision = ET.SubElement(link, "collision")
    geom_c = ET.SubElement(collision, "geometry")
    ET.SubElement(geom_c, "mesh",
                  filename=f"{MESH_DIR}/{link_name}.stl",
                  scale="0.001 0.001 0.001")

    # Inertial
    mass_kg = part.volume * DENSITY
    bb = part.bounding_box()
    lx, ly, lz = bb.size.X / 1000, bb.size.Y / 1000, bb.size.Z / 1000
    ixx = mass_kg * (ly**2 + lz**2) / 12
    iyy = mass_kg * (lx**2 + lz**2) / 12
    izz = mass_kg * (lx**2 + ly**2) / 12

    inertial = ET.SubElement(link, "inertial")
    ET.SubElement(inertial, "mass", value=f"{mass_kg:.6f}")
    ET.SubElement(inertial, "inertia",
                  ixx=f"{ixx:.8f}", ixy="0", ixz="0",
                  iyy=f"{iyy:.8f}", iyz="0", izz=f"{izz:.8f}")

# --- Joints ---
joint_specs = [
    {
        "name": "hip_joint",
        "type": "revolute",
        "parent": "body",
        "child": "upper_leg",
        "xyz": f"0 {d1/1000:.4f} 0",
        "axis": "0 0 1",
        "lower": str(math.radians(-45)),
        "upper": str(math.radians(45)),
    },
    {
        "name": "knee_joint",
        "type": "revolute",
        "parent": "upper_leg",
        "child": "lower_leg",
        "xyz": f"0 0 {-L1/1000:.4f}",
        "axis": "0 1 0",
        "lower": str(math.radians(-90)),
        "upper": str(math.radians(0)),
    },
    {
        "name": "ankle_joint",
        "type": "revolute",
        "parent": "lower_leg",
        "child": "foot",
        "xyz": f"0 0 {-L2/1000:.4f}",
        "axis": "0 1 0",
        "lower": str(math.radians(-30)),
        "upper": str(math.radians(120)),
    },
]

for js in joint_specs:
    joint = ET.SubElement(robot, "joint", name=js["name"], type=js["type"])
    ET.SubElement(joint, "parent", link=js["parent"])
    ET.SubElement(joint, "child", link=js["child"])
    ET.SubElement(joint, "origin", xyz=js["xyz"], rpy="0 0 0")
    ET.SubElement(joint, "axis", xyz=js["axis"])
    ET.SubElement(joint, "limit",
                  lower=js["lower"], upper=js["upper"],
                  effort="10", velocity="5")


# ===== 输出文件 =====
os.makedirs(os.path.join(OUTPUT_DIR, MESH_DIR), exist_ok=True)

# 导出 STL meshes
print("导出 STL meshes...")
for link_name, part in link_specs:
    stl_path = os.path.join(OUTPUT_DIR, MESH_DIR, f"{link_name}.stl")
    export_stl(part, stl_path)
    print(f"  {link_name}.stl ({part.volume:.0f} mm³)")

# 导出 URDF XML（美化格式）
urdf_path = os.path.join(OUTPUT_DIR, f"{ROBOT_NAME}.urdf")
xml_str = ET.tostring(robot, encoding="unicode")
pretty_xml = minidom.parseString(xml_str).toprettyxml(indent="  ")
# 移除多余的 XML 声明行
lines = pretty_xml.split("\n")
if lines[0].startswith("<?xml"):
    pretty_xml = "\n".join(lines[1:])

with open(urdf_path, "w") as f:
    f.write('<?xml version="1.0" ?>\n')
    f.write(pretty_xml)

print(f"\n导出完成: {urdf_path}")

# ===== 验证 =====
print("\n===== URDF 结构 =====")
print(f"Robot: {ROBOT_NAME}")
print(f"Links:  {[ls[0] for ls in link_specs]}")
print(f"Joints: {[js['name'] for js in joint_specs]}")
print(f"Files:")
print(f"  {urdf_path}")
for link_name, _ in link_specs:
    print(f"  {OUTPUT_DIR}/{MESH_DIR}/{link_name}.stl")

# yourdfpy 验证（可选）
try:
    import yourdfpy
    urdf = yourdfpy.URDF.load(urdf_path)
    print(f"\nyourdfpy 验证: OK")
    print(f"  Links:  {list(urdf.link_map.keys())}")
    print(f"  Joints: {list(urdf.joint_map.keys())}")
except ImportError:
    print("\n提示: pip install yourdfpy 可进行 URDF 可视化验证")
except Exception as e:
    print(f"\nyourdfpy 验证失败: {e}")

# OCP 预览
from ocp_vscode import show
show(assembly, names=["quadruped_leg"], colors=["steelblue"])
print("\nDone: URDF exported and model displayed in OCP Viewer")
