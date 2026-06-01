"""
通用爆炸动画生成器 / Universal Exploded Animation Generator
用途：从多个 STEP 文件生成 OCP 爆炸动画代码
用法：python explode_generator.py part1.step part2.step [--dist 30] [--axis z]
"""
import sys
import argparse
from build123d import *

def generate_explode_code(step_files: list[str], explode_dist: float = 30,
                          axis: str = "z", timeline: str = "default"):
    """生成爆炸动画 Python 代码"""
    n = len(step_files)
    if n < 2:
        print("⚠️ 需要至少 2 个 STEP 文件")
        return

    names = [f.replace(".step", "").replace(".STEP", "") for f in step_files]
    colors = ["steelblue", "orange", "gray", "green", "red",
              "purple", "cyan", "yellow"][:n]

    # 计算每个零件的爆炸偏移
    half = explode_dist / 2
    offsets = []
    for i in range(n):
        # 均匀分布在正负方向
        offset = (i - (n - 1) / 2) * explode_dist / (n - 1) if n > 1 else 0
        offsets.append(offset)

    # 轴映射
    axis_map = {"x": 0, "y": 1, "z": 2}
    axis_idx = axis_map.get(axis.lower(), 2)

    # 时间轴
    if timeline == "default":
        t = [0, 2, 12, 14, 16]  # 默认 16s 循环
    elif timeline == "sequential":
        # 顺序拆解：每个零件 2 秒
        t_total = n * 2 + 10 + n * 2 + 2  # 拆 + 停 + 合 + 停
        t = list(range(0, t_total + 1, 2))

    print(f"# ===== 爆炸动画代码（自动生成） =====")
    print(f"# 零件: {', '.join(names)}")
    print(f"# 爆炸轴: {axis.upper()}, 距离: {explode_dist}mm")
    print(f"# 时间轴: {t}")
    print()
    print(f"from build123d import *")
    print(f"from ocp_vscode import show, Animation")
    print()

    # 导入
    print(f"# ===== 导入零件 =====")
    for i, (f, name) in enumerate(zip(step_files, names)):
        print(f"{name} = import_step(\"{f}\")")
    print()

    # Show
    print(f"# ===== 显示装配态 =====")
    print(f"show({', '.join(names)},")
    print(f"     names={names},")
    print(f"     colors={colors})")
    print()

    # Animation
    print(f"# ===== 爆炸动画 =====")
    print(f"explode_dist = {explode_dist}")
    print(f"t = {t}")
    print()
    print(f"animation = Animation()")

    for i, (name, offset) in enumerate(zip(names, offsets)):
        vec_start = [0, 0, 0]
        vec_explode = [0, 0, 0]
        vec_explode[axis_idx] = round(offset, 1)

        if timeline == "default":
            values = [vec_start, vec_explode, vec_explode, vec_start, vec_start]
        else:
            values = [vec_start, vec_explode]

        print(f"animation.add_track(\"/Group/{name}\", \"t\", t,")
        print(f"                    {values})")

    print(f"animation.animate(1)")
    print()
    print(f"print(\"爆炸动画已加载\")")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="生成爆炸动画代码")
    parser.add_argument("files", nargs="+", help="STEP 文件列表")
    parser.add_argument("--dist", type=float, default=30, help="爆炸距离 (mm)")
    parser.add_argument("--axis", default="z", choices=["x", "y", "z"], help="爆炸轴")
    parser.add_argument("--timeline", default="default",
                        choices=["default", "sequential"], help="时间轴模式")

    args = parser.parse_args()
    generate_explode_code(args.files, args.dist, args.axis, args.timeline)
