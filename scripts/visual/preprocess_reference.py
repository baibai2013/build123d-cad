#!/usr/bin/env python3
"""Preprocess a real-world reference photo into comparable form.
参考图预处理：裁剪 + 比例尺 + 输出干净图 / 元数据。

CLI:
    python3 preprocess_reference.py <photo.png> \\
        --bbox "x,y,w,h" \\
        --physical-length "160.0mm" \\
        --physical-axis height \\
        --output-dir refs/clean/

产出：
    {stem}_cropped.png   裁剪后的部件图
    {stem}_bbox.json     {"bbox_xywh": [x, y, w, h], "source_image": "..."}
    {stem}_scale.json    {"mm_per_px": <float>, "physical_axis": "height"|"width", "physical_length_mm": <float>}
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path
from typing import Tuple

from PIL import Image


def _parse_length(text: str) -> float:
    m = re.match(r"^\s*([0-9]+(?:\.[0-9]+)?)\s*mm\s*$", text, re.IGNORECASE)
    if not m:
        raise ValueError(f"physical-length must look like '160.0mm', got {text!r}")
    return float(m.group(1))


def preprocess(
    image_path: Path,
    bbox: Tuple[int, int, int, int],
    physical_length_mm: float,
    physical_axis: str,
    output_dir: Path,
) -> dict:
    if physical_axis not in ("height", "width"):
        raise ValueError(f"physical-axis must be 'height' or 'width', got {physical_axis!r}")
    x, y, w, h = bbox
    if w <= 0 or h <= 0:
        raise ValueError(f"bbox w/h must be positive, got {bbox}")
    img = Image.open(image_path).convert("RGB")
    iw, ih = img.size
    if x < 0 or y < 0 or x + w > iw or y + h > ih:
        raise ValueError(f"bbox {bbox} out of image bounds {(iw, ih)}")

    cropped = img.crop((x, y, x + w, y + h))
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = image_path.stem
    cropped_path = output_dir / f"{stem}_cropped.png"
    bbox_path = output_dir / f"{stem}_bbox.json"
    scale_path = output_dir / f"{stem}_scale.json"

    cropped.save(cropped_path)
    axis_len_px = h if physical_axis == "height" else w
    mm_per_px = physical_length_mm / axis_len_px

    bbox_path.write_text(json.dumps({
        "bbox_xywh": [x, y, w, h],
        "source_image": str(image_path),
    }, indent=2))
    scale_path.write_text(json.dumps({
        "mm_per_px": mm_per_px,
        "physical_axis": physical_axis,
        "physical_length_mm": physical_length_mm,
        "reference_image": str(cropped_path),
    }, indent=2))
    return {
        "cropped_path": cropped_path,
        "bbox_path": bbox_path,
        "scale_path": scale_path,
        "mm_per_px": mm_per_px,
    }


def _parse_bbox(text: str) -> Tuple[int, int, int, int]:
    parts = [p.strip() for p in text.split(",")]
    if len(parts) != 4:
        raise ValueError(f"bbox must be 'x,y,w,h' with 4 comma-separated ints, got {text!r}")
    return tuple(int(p) for p in parts)  # type: ignore[return-value]


def main() -> int:
    p = argparse.ArgumentParser(description="Preprocess reference photo for Layer 2 visual compare.")
    p.add_argument("photo", type=Path)
    p.add_argument("--bbox", required=True, help="'x,y,w,h' pixel coordinates of the part.")
    p.add_argument("--physical-length", required=True, help="e.g. '160.26mm'")
    p.add_argument("--physical-axis", choices=["height", "width"], default="height")
    p.add_argument("--output-dir", type=Path, default=Path("refs/clean"))
    args = p.parse_args()

    try:
        bbox = _parse_bbox(args.bbox)
        length_mm = _parse_length(args.physical_length)
        out = preprocess(
            image_path=args.photo,
            bbox=bbox,
            physical_length_mm=length_mm,
            physical_axis=args.physical_axis,
            output_dir=args.output_dir,
        )
    except (ValueError, FileNotFoundError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    print(f"cropped: {out['cropped_path']}")
    print(f"bbox:    {out['bbox_path']}")
    print(f"scale:   {out['scale_path']} (mm_per_px={out['mm_per_px']:.4f})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
