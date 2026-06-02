"""#7 radial_cylinder ★★★★ — 主缸 + 径向进气管 + 法兰 + 内通连。"""
from __future__ import annotations

from build123d import (
    Align,
    BuildPart,
    Cylinder,
    Locations,
    Mode,
    PolarLocations,
    Pos,
    Rot,
)

from ..bench_def import bench


@bench(
    name="radial_cylinder",
    suite=("full",),
    difficulty=4,
    timeout_seconds=90,
)
def build():
    # 主缸
    M_OD, M_ID, M_LEN = 40.0, 20.0, 80.0
    # 进气管(从 Z=40 +X 25mm,通主缸内孔)
    INLET_OD, INLET_ID, INLET_EXT = 12.0, 9.0, 25.0
    INLET_Z = 40.0
    # 法兰
    F_OD, F_T, F_HOLE_D, F_PCD = 60.0, 8.0, 5.0, 45.0
    F_Z = M_LEN  # 80~88

    with BuildPart() as part:
        # 主缸外
        Cylinder(radius=M_OD / 2, height=M_LEN, align=(Align.CENTER, Align.CENTER, Align.MIN))
        # 进气管外(从主缸表面 X=M_OD/2 起,沿 +X 方向 INLET_EXT)
        # 圆柱默认沿 Z,Rot(Y=90) 沿 X;中心 X=M_OD/2 + INLET_EXT/2,Z=INLET_Z
        with Locations(Pos(M_OD / 2 + INLET_EXT / 2, 0, INLET_Z) * Rot(0, 90, 0)):
            Cylinder(radius=INLET_OD / 2, height=INLET_EXT + M_OD / 2)  # 多伸入主缸内 M_OD/2 保贯通
        # 法兰
        with Locations((0, 0, F_Z)):
            Cylinder(radius=F_OD / 2, height=F_T, align=(Align.CENTER, Align.CENTER, Align.MIN))
        # 主缸内孔
        Cylinder(
            radius=M_ID / 2,
            height=M_LEN + F_T + 2,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.SUBTRACT,
        )
        # 进气管内孔
        with Locations(Pos(M_OD / 2 + INLET_EXT / 2, 0, INLET_Z) * Rot(0, 90, 0)):
            Cylinder(radius=INLET_ID / 2, height=INLET_EXT + M_OD / 2 + 2, mode=Mode.SUBTRACT)
        # 法兰 4 孔
        with Locations((0, 0, F_Z)):
            with PolarLocations(radius=F_PCD / 2, count=4):
                Cylinder(
                    radius=F_HOLE_D / 2,
                    height=F_T + 2,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                    mode=Mode.SUBTRACT,
                )
    return part.part
