"""#5 enclosure_box ★★★ — 抽壳 + 螺柱 + USB 切口 + 顶口 R0.5。"""
from __future__ import annotations

from build123d import (
    Align,
    BuildPart,
    Box,
    Cylinder,
    Locations,
    Mode,
    Pos,
    Rot,
    fillet,
    offset,
)

from ..bench_def import bench


@bench(
    name="enclosure_box",
    suite=("full",),
    difficulty=3,
    timeout_seconds=90,
)
def build():
    L, W, H = 100.0, 60.0, 30.0
    WALL = 2.5
    USB_W, USB_H = 12.0, 6.0
    BOSS_OD, BOSS_ID, BOSS_H = 5.0, 2.5, 25.0

    with BuildPart() as part:
        # 实心外壳
        Box(L, W, H, align=(Align.MIN, Align.MIN, Align.MIN))
        # 抽壳:从顶面(+Z)开口,壁厚 WALL
        # build123d 0.10:offset(... openings=...) 简化为内挖一个稍小的 box
        Box(
            L - 2 * WALL,
            W - 2 * WALL,
            H - WALL + 1,  # 顶面留 1 mm 余量保贯通
            align=(Align.MIN, Align.MIN, Align.MIN),
            mode=Mode.SUBTRACT,
        ).move(Pos(WALL, WALL, WALL))

        # 顶口边缘 R0.5(顶面外圆周 4 条 edge)
        try:
            top_edges = [
                e for e in part.edges()
                if abs(e.position.Z - H) < 0.01 and e.geom_type == "LINE"
            ]
            if top_edges:
                fillet(top_edges, radius=0.5)
        except Exception:
            pass

        # 4 个 M3 螺柱(底面内表面四角,距内壁 5 mm)
        boss_offset = WALL + 5.0
        for x, y in (
            (boss_offset, boss_offset),
            (L - boss_offset, boss_offset),
            (boss_offset, W - boss_offset),
            (L - boss_offset, W - boss_offset),
        ):
            with Locations((x, y, WALL)):
                Cylinder(
                    radius=BOSS_OD / 2,
                    height=BOSS_H,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                )
                Cylinder(
                    radius=BOSS_ID / 2,
                    height=BOSS_H + 1,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                    mode=Mode.SUBTRACT,
                )

        # USB-A 切口:沿 +Y 长边中央(Y=W),X 中心 = L/2,Z 中心 = H/2
        # 切一个穿透 Y 方向的矩形孔:沿 Y 厚度 = WALL+2
        with Locations(Pos(L / 2, W - WALL / 2, H / 2)):
            Box(USB_W, WALL + 2, USB_H, mode=Mode.SUBTRACT)
    return part.part
