"""#3 l_bracket ★★ — L 支架 + 加强肋 + 安装孔。

题面:水平 50×50×5 + 竖直 50×40×5(夹角 90°)+ 2 三角肋 t=3 ext=30 + 4 Φ5 安装孔。
"""
from __future__ import annotations

from build123d import (
    Align,
    BuildLine,
    BuildPart,
    BuildSketch,
    Box,
    Cylinder,
    Line,
    Locations,
    Mode,
    Plane,
    Pos,
    Rot,
    extrude,
    make_face,
)

from ..bench_def import bench


@bench(
    name="l_bracket",
    suite=("fast", "full"),
    difficulty=2,
    timeout_seconds=45,
)
def build():
    H_L, H_W, T = 50.0, 50.0, 5.0
    V_W, V_H = 50.0, 40.0
    GUSSET_T = 3.0
    GUSSET_EXT = 30.0
    HOLE_D = 5.0

    with BuildPart() as part:
        # 水平翼板 X∈[0,50] Y∈[0,50] Z∈[0,5]
        Box(H_L, H_W, T, align=(Align.MIN, Align.MIN, Align.MIN))
        # 竖直翼板 X∈[0,5] Y∈[0,50] Z∈[0,40]
        Box(T, V_W, V_H, align=(Align.MIN, Align.MIN, Align.MIN))

        # 2 三角加强肋:贴 Y=10 / Y=40,YZ 平面三角形 → 沿 +Y 拉伸 GUSSET_T
        for y in (10.0, V_W - 10.0):
            with BuildSketch(Plane.YZ.offset(y)) as gs:
                with BuildLine():
                    Line((T, T), (T + GUSSET_EXT, T))
                    Line((T + GUSSET_EXT, T), (T, T + GUSSET_EXT))
                    Line((T, T + GUSSET_EXT), (T, T))
                make_face()
            extrude(amount=GUSSET_T)

        # 水平翼板 2 安装孔(沿 Z 贯穿 T)
        with Locations((15.0, 10.0, 0), (35.0, 40.0, 0)):
            Cylinder(
                radius=HOLE_D / 2,
                height=T + 2,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )

        # 竖直翼板 2 安装孔(沿 X 贯穿 T):
        # 圆柱默认沿 Z 轴,Rot(Y=90) 旋转后沿 X 轴。
        # 中心 X=T/2 = 2.5,Y/Z 给孔位
        with Locations(
            Pos(T / 2, 10.0, 15.0) * Rot(0, 90, 0),
            Pos(T / 2, 40.0, 30.0) * Rot(0, 90, 0),
        ):
            Cylinder(
                radius=HOLE_D / 2,
                height=T + 2,
                align=(Align.CENTER, Align.CENTER, Align.CENTER),
                mode=Mode.SUBTRACT,
            )
    return part.part
