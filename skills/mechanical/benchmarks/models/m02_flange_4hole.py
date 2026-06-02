"""#2 flange_4hole ★★ — 4 孔法兰盘 + 顶视 DXF。

题面:OD 80,ID 40,t 8,4×Φ6 PCD60 0/90/180/270,外圆 R1。
"""
from __future__ import annotations

from pathlib import Path

from build123d import (
    Align,
    Axis,
    BuildPart,
    BuildSketch,
    Circle,
    Cylinder,
    ExportDXF,
    Mode,
    Plane,
    PolarLocations,
    fillet,
)

from ..bench_def import bench


OD = 80.0
ID = 40.0
T = 8.0
HOLE_D = 6.0
PCD = 60.0


@bench(
    name="flange_4hole",
    suite=("fast", "full"),
    difficulty=2,
    timeout_seconds=45,
    extra_outputs=("flange_4hole.dxf",),
)
def build():
    with BuildPart() as part:
        # 主体盘(底面 Z=0)
        Cylinder(
            radius=OD / 2,
            height=T,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        # 中心通孔
        Cylinder(
            radius=ID / 2,
            height=T + 2,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.SUBTRACT,
        )
        # 4 个 PCD60 孔(0/90/180/270)
        with PolarLocations(radius=PCD / 2, count=4):
            Cylinder(
                radius=HOLE_D / 2,
                height=T + 2,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )
        # 外圆 R1 倒圆角(顶/底两条外圆)
        try:
            outer_circles = [
                e for e in part.edges()
                if e.geom_type == "CIRCLE"
                and abs(e.radius - OD / 2) < 0.01
            ]
            if outer_circles:
                fillet(outer_circles, radius=1.0)
        except Exception:
            pass
    return part.part


def export_extras(part_obj, out_dir: Path):
    """额外导出顶视 DXF。"""
    with BuildSketch(Plane.XY) as top_view:
        Circle(OD / 2)
        Circle(ID / 2, mode=Mode.SUBTRACT)
        with PolarLocations(radius=PCD / 2, count=4):
            Circle(HOLE_D / 2, mode=Mode.SUBTRACT)
    dxf_path = out_dir / "flange_4hole.dxf"
    # build123d 0.10:ExportDXF API 是 add_layer + add_shape + write
    exporter = ExportDXF()
    exporter.add_layer("flange")
    exporter.add_shape(top_view.sketch, layer="flange")
    exporter.write(str(dxf_path))
    return dxf_path
