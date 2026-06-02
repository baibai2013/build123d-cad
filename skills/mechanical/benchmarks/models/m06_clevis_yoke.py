"""#6 clevis_yoke ★★★ — 双耳片 + 销孔同轴。"""
from __future__ import annotations

from build123d import (
    Align,
    BuildPart,
    BuildSketch,
    Box,
    Circle,
    Cylinder,
    Locations,
    Mode,
    Plane,
    Pos,
    Rectangle,
    Rot,
    extrude,
)

from ..bench_def import bench


@bench(
    name="clevis_yoke",
    suite=("full",),
    difficulty=3,
    timeout_seconds=60,
)
def build():
    BEAM_X, BEAM_Y, BEAM_Z = 30.0, 20.0, 10.0
    EAR_T = 6.0
    EAR_GAP = 14.0
    EAR_H = 30.0
    EAR_LEN_Y = 30.0
    PIN_D = 6.0
    PIN_Z = 25.0
    PIN_Y = 15.0

    with BuildPart() as part:
        # 横梁:中心在 (BEAM_X/2, BEAM_Y/2, BEAM_Z/2)
        Box(BEAM_X, BEAM_Y, BEAM_Z, align=(Align.MIN, Align.MIN, Align.MIN))

        # 双耳片:左右对称(关于 X 中线 BEAM_X/2),内侧间距 EAR_GAP
        # 每耳:厚 EAR_T 沿 X,长 EAR_LEN_Y 沿 Y,高 EAR_H 沿 Z(从 Z=BEAM_Z 起)
        # 头部 R10 半圆 → 把耳片轮廓做成 矩形(Y x Z) 顶部加圆角的形状
        for sign in (-1, 1):
            x_center = BEAM_X / 2 + sign * (EAR_GAP / 2 + EAR_T / 2)
            with BuildSketch(Plane.YZ.offset(x_center)) as ear_sketch:
                # 矩形主体 Y∈[0, EAR_LEN_Y] Z∈[BEAM_Z, BEAM_Z + EAR_H - 10]
                # 加上头部圆 (中心 Y=EAR_LEN_Y/2, Z=BEAM_Z + EAR_H - 10) R10 → 但 R10 = EAR_LEN_Y / 3 < 半矩形宽,简化:
                # 直接做成 R10 头的圆角矩形:
                Rectangle(
                    width=EAR_LEN_Y,
                    height=EAR_H,
                    align=(Align.MIN, Align.MIN),
                ).move(Pos(0, BEAM_Z))
                # 头部圆(中心位置 Y=EAR_LEN_Y/2, Z=BEAM_Z+EAR_H-10)
                with Locations((EAR_LEN_Y / 2, BEAM_Z + EAR_H - 10)):
                    Circle(10.0)
            extrude(amount=EAR_T)

        # Φ6 销孔贯穿两耳(沿 X 方向,中心 (任意, PIN_Y, PIN_Z))
        with Locations(
            Pos(BEAM_X / 2, PIN_Y, PIN_Z) * Rot(0, 90, 0),
        ):
            Cylinder(
                radius=PIN_D / 2,
                height=BEAM_X + 4,  # 贯穿全宽
                align=(Align.CENTER, Align.CENTER, Align.CENTER),
                mode=Mode.SUBTRACT,
            )
    return part.part
