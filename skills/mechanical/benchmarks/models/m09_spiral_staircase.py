"""#9 spiral_staircase ★★★★★ — 12 阶螺旋楼梯 + 中柱。

简化:踏板用 R100 厚 30 圆柱再裁出 22.5° 扇形;旋转 + 升起阵列 12 次。
"""
from __future__ import annotations

import math

from build123d import (
    Align,
    BuildLine,
    BuildPart,
    BuildSketch,
    Cylinder,
    Locations,
    Mode,
    Plane,
    Polyline,
    Pos,
    Rot,
    extrude,
    make_face,
)

from ..bench_def import bench


@bench(
    name="spiral_staircase",
    suite=("full",),
    difficulty=5,
    timeout_seconds=120,
)
def build():
    COL_OD = 60.0
    COL_H = 2200.0
    STEP_R = 100.0
    STEP_T = 30.0
    STEP_ANGLE_DEG = 22.5
    STEP_RISE = 180.0
    STEPS = 12
    Z_BASE = 20.0
    CAP_OD = 70.0
    CAP_T = 5.0

    with BuildPart() as part:
        # 中柱
        Cylinder(radius=COL_OD / 2, height=COL_H, align=(Align.CENTER, Align.CENTER, Align.MIN))
        # 顶/底封板
        with Locations((0, 0, 0)):
            Cylinder(radius=CAP_OD / 2, height=CAP_T, align=(Align.CENTER, Align.CENTER, Align.MIN))
        with Locations((0, 0, COL_H - CAP_T)):
            Cylinder(radius=CAP_OD / 2, height=CAP_T, align=(Align.CENTER, Align.CENTER, Align.MIN))

        # 12 阶踏板:每阶在 Plane.XY @ z=Z_BASE+i*STEP_RISE,绕 Z 旋转 i*22.5°,
        # 形状 = 22.5° 扇形(R = STEP_R,内径 = COL_OD/2)
        for i in range(STEPS):
            z = Z_BASE + i * STEP_RISE
            theta_start = i * STEP_ANGLE_DEG
            # 用 Polyline 描扇形(中心 + 外圆弧两点)简化为三角扇形
            # 实际更准:用 BuildSketch 中的 RegularPolygon 不行,要 Arc
            # 简化版:用 Polyline 直接画三角 + 外侧弧近似 4 段:
            theta_end = theta_start + STEP_ANGLE_DEG
            # 内点(中柱内圆与角度交点)
            r0 = COL_OD / 2
            r1 = STEP_R
            # 4 段折线近似圆弧(误差 < 0.05 mm 在 R100 内)
            arc_pts = []
            for k in range(5):
                a = math.radians(theta_start + k * STEP_ANGLE_DEG / 4)
                arc_pts.append((r1 * math.cos(a), r1 * math.sin(a)))
            inner_pts = []
            for k in range(5):
                a = math.radians(theta_start + (4 - k) * STEP_ANGLE_DEG / 4)
                inner_pts.append((r0 * math.cos(a), r0 * math.sin(a)))
            poly_pts = arc_pts + inner_pts
            with BuildSketch(Plane.XY.offset(z)) as ssk:
                with BuildLine():
                    Polyline(*poly_pts, close=True)
                make_face()
            extrude(amount=STEP_T)
    return part.part
