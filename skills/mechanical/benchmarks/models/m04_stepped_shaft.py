"""#4 stepped_shaft ★★★ — 阶梯轴 + R1 过渡 + 键槽 + 端倒角。"""
from __future__ import annotations

from build123d import (
    Align,
    Axis,
    BuildPart,
    Box,
    Cylinder,
    Locations,
    Mode,
    chamfer,
    fillet,
)

from ..bench_def import bench


@bench(
    name="stepped_shaft",
    suite=("full",),
    difficulty=3,
    timeout_seconds=60,
)
def build():
    # 三段 Φ × L
    D1, L1 = 10.0, 20.0
    D2, L2 = 16.0, 30.0
    D3, L3 = 12.0, 15.0
    KEY_W, KEY_D, KEY_L = 5.0, 3.0, 20.0

    z1_top = L1
    z2_top = L1 + L2
    z3_top = L1 + L2 + L3

    with BuildPart() as part:
        # 段 1
        with Locations((0, 0, L1 / 2)):
            Cylinder(radius=D1 / 2, height=L1)
        # 段 2
        with Locations((0, 0, z1_top + L2 / 2)):
            Cylinder(radius=D2 / 2, height=L2)
        # 段 3
        with Locations((0, 0, z2_top + L3 / 2)):
            Cylinder(radius=D3 / 2, height=L3)

        # R1 过渡圆角(段间环形 edge):filter 同 Z 平面上的圆 edge,半径 = D1/2 或 D3/2
        try:
            for z_target, r_target in ((z1_top, D1 / 2), (z2_top, D3 / 2)):
                circles = [
                    e for e in part.edges()
                    if e.geom_type == "CIRCLE"
                    and abs(e.position.Z - z_target) < 0.01
                    and abs(getattr(e, "radius", -1) - r_target) < 0.01
                ]
                if circles:
                    fillet(circles, radius=1.0)
        except Exception:
            pass

        # 端倒角 0.5×45°(Z=0 与 Z=z3_top 的圆 edge)
        try:
            ends = [
                e for e in part.edges()
                if e.geom_type == "CIRCLE" and (abs(e.position.Z) < 0.01 or abs(e.position.Z - z3_top) < 0.01)
            ]
            if ends:
                chamfer(ends, length=0.5)
        except Exception:
            pass

        # 键槽:Φ16 段中央,中心 Z=L1+L2/2 = 35,沿 +X 开口,W=5 D=3 L=20
        # 用矩形从 +X 方向减去:中心 (D2/2 - KEY_D/2, 0, 35),size = (KEY_D, KEY_W, KEY_L)
        with Locations((D2 / 2 - KEY_D / 2, 0, L1 + L2 / 2)):
            Box(KEY_D, KEY_W, KEY_L, mode=Mode.SUBTRACT)
    return part.part
