"""
PyBullet URDF 预览工具
加载 URDF → 地面 → 关节控制循环 → GUI 预览

用法：
    python pybullet_preview.py robot.urdf [--gait trot] [--duration 10]

参数：
    robot.urdf      URDF 文件路径
    --gait          步态类型: stand/trot/crawl (默认 stand)
    --duration      仿真时长秒 (默认 10)
    --fixed         固定基座 (调试用)
"""
import argparse
import sys
import os
import math
import time

try:
    import pybullet as p
    import pybullet_data
except ImportError:
    print("错误: 请安装 PyBullet")
    print("  pip install pybullet")
    sys.exit(1)

import numpy as np


# ===== 步态定义 =====
GAITS = {
    "stand": {
        "phases": [0, 0, 0, 0],
        "duty": 1.0,
        "stride": 0,
        "clearance": 0,
        "period": 1.0,
    },
    "trot": {
        "phases": [0, 0.5, 0.5, 0],
        "duty": 0.5,
        "stride": 0.04,
        "clearance": 0.03,
        "period": 0.8,
    },
    "crawl": {
        "phases": [0, 0.25, 0.5, 0.75],
        "duty": 0.75,
        "stride": 0.03,
        "clearance": 0.02,
        "period": 2.0,
    },
}


def get_joint_info(robot_id):
    """获取关节映射表"""
    joint_map = {}
    n = p.getNumJoints(robot_id)
    for i in range(n):
        info = p.getJointInfo(robot_id, i)
        name = info[1].decode()
        jtype = info[2]
        lower = info[8]
        upper = info[9]
        joint_map[name] = {
            "index": i,
            "type": jtype,
            "lower": lower,
            "upper": upper,
        }
    return joint_map


def print_robot_info(robot_id, joint_map):
    """打印机器人信息"""
    print(f"\n{'='*50}")
    print(f"Robot joints: {len(joint_map)}")
    for name, info in joint_map.items():
        type_str = {0: "revolute", 1: "prismatic", 4: "fixed"}.get(info["type"], "other")
        print(f"  [{info['index']}] {name:20s} type={type_str:10s} "
              f"range=[{math.degrees(info['lower']):+.0f}°, {math.degrees(info['upper']):+.0f}°]")
    print(f"{'='*50}\n")


def main():
    parser = argparse.ArgumentParser(description="PyBullet URDF 预览")
    parser.add_argument("urdf", help="URDF 文件路径")
    parser.add_argument("--gait", default="stand", choices=GAITS.keys(),
                        help="步态类型")
    parser.add_argument("--duration", type=float, default=10,
                        help="仿真时长 (秒)")
    parser.add_argument("--fixed", action="store_true",
                        help="固定基座")
    args = parser.parse_args()

    if not os.path.exists(args.urdf):
        print(f"错误: 文件不存在 {args.urdf}")
        sys.exit(1)

    # 初始化 PyBullet
    print(f"加载 URDF: {args.urdf}")
    client = p.connect(p.GUI)
    p.setAdditionalSearchPath(pybullet_data.getDataPath())
    p.setGravity(0, 0, -9.81)
    p.setTimeStep(1/240)

    # 加载地面
    plane = p.loadURDF("plane.urdf")

    # 加载机器人
    robot = p.loadURDF(
        args.urdf,
        basePosition=[0, 0, 0.3],
        useFixedBase=args.fixed,
        flags=p.URDF_USE_SELF_COLLISION
    )

    # 获取关节信息
    joint_map = get_joint_info(robot)
    print_robot_info(robot, joint_map)

    # 设置相机
    p.resetDebugVisualizerCamera(
        cameraDistance=0.5,
        cameraYaw=45,
        cameraPitch=-30,
        cameraTargetPosition=[0, 0, 0.1]
    )

    # 步态参数
    gait = GAITS[args.gait]
    print(f"步态: {args.gait}")
    print(f"仿真时长: {args.duration}s")

    # GUI 参数滑块
    if args.gait != "stand":
        stride_id = p.addUserDebugParameter("stride", 0.01, 0.10, gait["stride"])
        clearance_id = p.addUserDebugParameter("clearance", 0.01, 0.05, gait["clearance"])
    else:
        stride_id = clearance_id = None

    # 可活动关节列表
    movable_joints = {name: info for name, info in joint_map.items()
                      if info["type"] in (0, 1)}  # revolute or prismatic

    # 仿真循环
    dt = 1/240
    t = 0
    n_steps = int(args.duration / dt)
    max_force = 5.0

    print(f"\n开始仿真... (按 Ctrl+C 退出)")

    try:
        for step in range(n_steps):
            # 默认站立角度
            for name, info in movable_joints.items():
                mid_angle = (info["lower"] + info["upper"]) / 2
                p.setJointMotorControl2(
                    robot, info["index"],
                    p.POSITION_CONTROL,
                    targetPosition=mid_angle,
                    force=max_force
                )

            p.stepSimulation()
            t += dt

            # 每秒打印状态
            if step % 240 == 0:
                pos, orn = p.getBasePositionAndOrientation(robot)
                euler = p.getEulerFromQuaternion(orn)
                print(f"  t={t:.1f}s  pos=({pos[0]:+.3f}, {pos[1]:+.3f}, {pos[2]:+.3f})  "
                      f"rpy=({math.degrees(euler[0]):+.1f}°, "
                      f"{math.degrees(euler[1]):+.1f}°, "
                      f"{math.degrees(euler[2]):+.1f}°)")

            time.sleep(dt)

    except KeyboardInterrupt:
        print("\n仿真中断")

    print(f"\n仿真完成: {t:.1f}s")
    p.disconnect()


if __name__ == "__main__":
    main()
