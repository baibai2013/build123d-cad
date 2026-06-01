"""
URDF 自动导出工具
遍历 build123d Compound 的 children/joints → 生成 URDF XML + STL meshes

用法：
    python export_urdf.py input.step [--name robot] [--density 1.24e-6] [--output output/]

参数：
    input.step      输入 STEP 文件（含多体 Compound）
    --name          机器人名称（默认: robot）
    --density       材料密度 kg/mm³（默认: 1.24e-6 PLA）
    --output        输出目录（默认: output/）
"""
import argparse
import os
import sys
import math
import xml.etree.ElementTree as ET
from xml.dom import minidom

# build123d 导入
from build123d import import_step, export_stl


def estimate_inertia(volume_mm3, bbox_size, density):
    """从体积和包围盒估算惯性张量"""
    mass = volume_mm3 * density
    lx = bbox_size.X / 1000  # mm → m
    ly = bbox_size.Y / 1000
    lz = bbox_size.Z / 1000
    ixx = mass * (ly**2 + lz**2) / 12
    iyy = mass * (lx**2 + lz**2) / 12
    izz = mass * (lx**2 + ly**2) / 12
    return mass, ixx, iyy, izz


def compound_to_urdf(compound, robot_name, density, output_dir):
    """
    将 Compound 转换为 URDF 文件 + STL meshes。
    """
    mesh_dir = "meshes"
    mesh_path = os.path.join(output_dir, mesh_dir)
    os.makedirs(mesh_path, exist_ok=True)

    robot = ET.Element("robot", name=robot_name)

    # 遍历 children → links
    children = list(compound.children) if hasattr(compound, 'children') else [compound]

    for i, child in enumerate(children):
        link_name = getattr(child, 'label', None) or f"link_{i}"

        # 导出 STL
        stl_file = f"{link_name}.stl"
        stl_path = os.path.join(mesh_path, stl_file)
        export_stl(child, stl_path)
        print(f"  Link: {link_name} → {stl_file} ({child.volume:.0f} mm³)")

        # URDF link
        link = ET.SubElement(robot, "link", name=link_name)

        visual = ET.SubElement(link, "visual")
        geom = ET.SubElement(visual, "geometry")
        ET.SubElement(geom, "mesh",
                      filename=f"{mesh_dir}/{stl_file}",
                      scale="0.001 0.001 0.001")

        collision = ET.SubElement(link, "collision")
        geom_c = ET.SubElement(collision, "geometry")
        ET.SubElement(geom_c, "mesh",
                      filename=f"{mesh_dir}/{stl_file}",
                      scale="0.001 0.001 0.001")

        mass, ixx, iyy, izz = estimate_inertia(
            child.volume, child.bounding_box().size, density
        )
        inertial = ET.SubElement(link, "inertial")
        ET.SubElement(inertial, "mass", value=f"{mass:.6f}")
        ET.SubElement(inertial, "inertia",
                      ixx=f"{ixx:.8f}", ixy="0", ixz="0",
                      iyy=f"{iyy:.8f}", iyz="0", izz=f"{izz:.8f}")

    # 遍历 joints
    if hasattr(compound, 'joints'):
        for jname, joint in compound.joints.items():
            jtype = _map_joint_type(joint)
            joint_elem = ET.SubElement(robot, "joint", name=jname, type=jtype)

            # parent/child
            parent_name = "base_link"
            child_name = "child_link"
            if hasattr(joint, 'parent') and hasattr(joint.parent, 'label'):
                parent_name = joint.parent.label or parent_name
            if hasattr(joint, 'to_part') and hasattr(joint.to_part, 'label'):
                child_name = joint.to_part.label or child_name

            ET.SubElement(joint_elem, "parent", link=parent_name)
            ET.SubElement(joint_elem, "child", link=child_name)
            ET.SubElement(joint_elem, "origin", xyz="0 0 0", rpy="0 0 0")
            ET.SubElement(joint_elem, "axis", xyz="0 0 1")

            if hasattr(joint, 'angular_range') and joint.angular_range:
                lo, hi = joint.angular_range
                ET.SubElement(joint_elem, "limit",
                              lower=f"{math.radians(lo):.4f}",
                              upper=f"{math.radians(hi):.4f}",
                              effort="10", velocity="5")
    else:
        # 没有 joints 信息：用 fixed joint 串联所有 link
        for i in range(1, len(children)):
            prev_name = getattr(children[i-1], 'label', None) or f"link_{i-1}"
            curr_name = getattr(children[i], 'label', None) or f"link_{i}"
            joint_elem = ET.SubElement(robot, "joint",
                                       name=f"joint_{i}", type="fixed")
            ET.SubElement(joint_elem, "parent", link=prev_name)
            ET.SubElement(joint_elem, "child", link=curr_name)
            ET.SubElement(joint_elem, "origin", xyz="0 0 0", rpy="0 0 0")

    # 写入 URDF 文件
    urdf_path = os.path.join(output_dir, f"{robot_name}.urdf")
    xml_str = ET.tostring(robot, encoding="unicode")
    pretty = minidom.parseString(xml_str).toprettyxml(indent="  ")
    lines = pretty.split("\n")
    if lines[0].startswith("<?xml"):
        pretty = "\n".join(lines[1:])

    with open(urdf_path, "w") as f:
        f.write('<?xml version="1.0" ?>\n')
        f.write(pretty)

    return urdf_path


def _map_joint_type(joint):
    mapping = {
        "RigidJoint": "fixed",
        "RevoluteJoint": "revolute",
        "LinearJoint": "prismatic",
        "CylindricalJoint": "revolute",
        "BallJoint": "fixed",
    }
    return mapping.get(type(joint).__name__, "fixed")


def main():
    parser = argparse.ArgumentParser(description="build123d STEP → URDF 导出")
    parser.add_argument("input", help="输入 STEP 文件")
    parser.add_argument("--name", default="robot", help="机器人名称")
    parser.add_argument("--density", type=float, default=1.24e-6,
                        help="材料密度 kg/mm³ (默认 PLA: 1.24e-6)")
    parser.add_argument("--output", default="output", help="输出目录")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"错误: 文件不存在 {args.input}")
        sys.exit(1)

    print(f"加载 STEP: {args.input}")
    compound = import_step(args.input)
    print(f"  Children: {len(list(compound.children)) if hasattr(compound, 'children') else 1}")

    print(f"\n生成 URDF ({args.name})...")
    urdf_path = compound_to_urdf(compound, args.name, args.density, args.output)
    print(f"\n完成: {urdf_path}")


if __name__ == "__main__":
    main()
