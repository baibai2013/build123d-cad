"""#1 calibration_block ★ — 立方 + 4 角孔,基准健康检查。

题面:60×40×20 长方体 + 4 个 Φ4 通孔(中心距外缘 5 mm),无倒角圆角。
完整 prompt 见 prompts/01_calibration_block.md。
"""
from __future__ import annotations

from build123d import (
    Align,
    BuildPart,
    Box,
    Cylinder,
    Locations,
    Mode,
)

from ..bench_def import bench


@bench(
    name="calibration_block",
    suite=("fast", "full"),
    difficulty=1,
    timeout_seconds=30,
)
def build():
    L, W, H = 60.0, 40.0, 20.0
    margin = 5.0
    hole_d = 4.0
    with BuildPart() as part:
        # 角点对齐到原点(MIN/MIN/MIN)
        Box(L, W, H, align=(Align.MIN, Align.MIN, Align.MIN))
        # 4 角孔(贯穿 Z),孔中心 (5,5)/(55,5)/(5,35)/(55,35)
        with Locations(
            (margin, margin, H / 2),
            (L - margin, margin, H / 2),
            (margin, W - margin, H / 2),
            (L - margin, W - margin, H / 2),
        ):
            Cylinder(
                radius=hole_d / 2,
                height=H + 2,
                mode=Mode.SUBTRACT,
            )
    return part.part
