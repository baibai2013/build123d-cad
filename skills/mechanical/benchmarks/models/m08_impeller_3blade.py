"""#8 impeller_3blade ★★★★ — 三叶离心叶轮(P0 占位,扫掠暂用简化叶片)。

P0 简化版:用 3 块矩形叶片(BuildSketch 拉伸)代替螺旋扫掠,保拓扑/装配关系。
P1 升级:用 Helix path + sweep 真做螺旋叶片。
"""
from __future__ import annotations

import math

from build123d import (
    Align,
    BuildPart,
    Box,
    Cylinder,
    Locations,
    Mode,
    Pos,
    Rot,
)

from ..bench_def import bench


@bench(
    name="impeller_3blade",
    suite=("full",),
    difficulty=4,
    timeout_seconds=120,
)
def build():
    HUB_OD = 20.0
    HUB_H = 30.0
    BORE_D = 8.0
    BLADE_T = 2.0
    BLADE_LEN = 30.0   # 弦(径向)
    BLADE_H = HUB_H

    with BuildPart() as part:
        # 轮毂
        Cylinder(radius=HUB_OD / 2, height=HUB_H, align=(Align.CENTER, Align.CENTER, Align.MIN))
        # 中心通孔
        Cylinder(
            radius=BORE_D / 2,
            height=HUB_H + 2,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.SUBTRACT,
        )
        # 3 叶片均布 120°(P0 简化为直叶片)
        for k in range(3):
            ang = k * 120
            # 叶片中心:从 hub 表面径向外延 BLADE_LEN/2 + HUB_OD/2
            r_center = HUB_OD / 2 + BLADE_LEN / 2
            ang_rad = math.radians(ang)
            x = r_center * math.cos(ang_rad)
            y = r_center * math.sin(ang_rad)
            with Locations(Pos(x, y, HUB_H / 2) * Rot(0, 0, ang)):
                Box(BLADE_LEN, BLADE_T, BLADE_H)
    return part.part
