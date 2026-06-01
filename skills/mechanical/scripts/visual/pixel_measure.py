#!/usr/bin/env python3
"""Convert pixel coordinates to millimeters using a known scale.
基于已知比例尺把像素坐标换算为部件本地坐标系下的毫米值。

CLI (batch):
    python3 pixel_measure.py <image.png> \\
        --scale refs/clean/xxx_scale.json \\
        --points "120,340;560,210" \\
        --origin "center"  # or "x_px,y_px"
        [--y-axis up|down]  # default down (image convention)
        [--output csv_path]

Interactive mode (matplotlib click collection) is TODO — see
ISSUE: interactive mode not yet implemented; use CLI points for now.
"""
from __future__ import annotations
import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Iterable, List, Tuple

from PIL import Image


def measure_points(
    points_px: Iterable[Tuple[int, int]],
    mm_per_px: float,
    origin_px: Tuple[int, int],
    y_axis_up: bool = False,
) -> List[dict]:
    ox, oy = origin_px
    out = []
    for px, py in points_px:
        dx_px = px - ox
        dy_px = py - oy
        x_mm = dx_px * mm_per_px
        y_mm = (-dy_px if y_axis_up else dy_px) * mm_per_px
        out.append({
            "x_px": px, "y_px": py,
            "x_mm": round(x_mm, 3), "y_mm": round(y_mm, 3),
        })
    return out


def _parse_points(text: str) -> List[Tuple[int, int]]:
    pts = []
    for pair in text.split(";"):
        pair = pair.strip()
        if not pair:
            continue
        xs, ys = pair.split(",")
        pts.append((int(xs), int(ys)))
    return pts


def _resolve_origin(spec: str, image_path: Path) -> Tuple[int, int]:
    if spec == "center":
        w, h = Image.open(image_path).size
        return (w // 2, h // 2)
    xs, ys = spec.split(",")
    return (int(xs), int(ys))


def main() -> int:
    p = argparse.ArgumentParser(description="Convert pixel coords to millimeters.")
    p.add_argument("image", type=Path)
    p.add_argument("--scale", required=True, type=Path, help="scale.json from preprocess_reference")
    p.add_argument("--points", required=True, help="'x1,y1;x2,y2;...'")
    p.add_argument("--origin", default="center", help="'center' or 'x,y'")
    p.add_argument("--y-axis", choices=["up", "down"], default="down")
    p.add_argument("--output", type=Path, default=None, help="write CSV (stdout if omitted)")
    args = p.parse_args()

    try:
        scale = json.loads(args.scale.read_text())
        mm_per_px = float(scale["mm_per_px"])
        origin = _resolve_origin(args.origin, args.image)
        points = _parse_points(args.points)
    except (ValueError, KeyError, FileNotFoundError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    results = measure_points(
        points_px=points,
        mm_per_px=mm_per_px,
        origin_px=origin,
        y_axis_up=(args.y_axis == "up"),
    )

    fieldnames = ["x_px", "y_px", "x_mm", "y_mm"]
    if args.output:
        with args.output.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(results)
        print(f"wrote {args.output} ({len(results)} rows)")
    else:
        w = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(results)
    return 0


if __name__ == "__main__":
    sys.exit(main())
