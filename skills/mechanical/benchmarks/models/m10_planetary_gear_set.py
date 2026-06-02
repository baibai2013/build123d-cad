"""#10 planetary_gear_set ★★★★★ — 行星齿轮组装配体(简化齿形)。

简化:齿轮用节圆圆柱替代(齿廓近似圆),保持中心距 18 与外径关系,装配 5 solid。
"""
from __future__ import annotations

import math

from build123d import (
    Align,
    Compound,
    Cylinder,
    Pos,
)

from ..bench_def import bench


@bench(
    name="planetary_gear_set",
    suite=("full",),
    difficulty=5,
    timeout_seconds=150,
)
def build():
    # m=1, T=18 → 节圆 Φ18;T=54 → Φ54
    SUN_PR = 9.0          # pitch radius
    PLANET_PR = 9.0
    RING_PR = 27.0
    THICKNESS = 8.0
    PCD_PLANET = SUN_PR + PLANET_PR  # 18

    # 5 个独立 solid,装入 Compound
    parts = []

    # 太阳轮(简化为节圆 + 齿顶高 0.5 = 圆柱 R 9.5)
    sun = Cylinder(radius=SUN_PR + 0.5, height=THICKNESS,
                   align=(Align.CENTER, Align.CENTER, Align.MIN))
    parts.append(sun)

    # 3 行星轮(均布 120°,半径 9.5)
    for k in range(3):
        ang = math.radians(k * 120)
        x = PCD_PLANET * math.cos(ang)
        y = PCD_PLANET * math.sin(ang)
        planet = Cylinder(
            radius=PLANET_PR + 0.5,
            height=THICKNESS,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        ).move(Pos(x, y, 0))
        parts.append(planet)

    # 内齿圈(外径 R=29 厚 8,内孔 R = 26.5 = 节圆-齿高 0.5)
    ring_outer = Cylinder(
        radius=RING_PR + 2.0,
        height=THICKNESS,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    ring_inner = Cylinder(
        radius=RING_PR - 0.5,
        height=THICKNESS + 1,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    ring = ring_outer - ring_inner
    parts.append(ring)

    # 装入 Compound — 5 个独立 solid
    return Compound(children=parts)
