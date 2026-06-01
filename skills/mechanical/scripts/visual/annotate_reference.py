#!/usr/bin/env python3
"""Draw dimension lines + feature boxes + confidence colors on a reference photo.
在参考图上叠加尺寸线 + 特征框 + 置信度颜色。

CLI:
    python3 annotate_reference.py <photo.png> --annotations FILE.json --output PATH

annotations.json:
    {
      "scale": {"pixels": 1080, "mm": 162.2},
      "origin": [540, 820],
      "features": [
        {"name": "camera_module", "center_px": [320, 150], "size_mm": [38, 38],
         "confidence": 4, "color": "red"},
        ...
      ]
    }
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


CONFIDENCE_COLORS = {
    5: (  0,   0, 200),  # blue  = 官方参数
    4: (200,   0,   0),  # red   = 反推
    3: (200, 140,   0),  # orange
    2: (200, 200,   0),  # yellow = 低置信
    1: (128, 128, 128),  # grey
}


def _pick_color(spec: str | None, confidence: int) -> tuple:
    if spec == "blue":   return (0, 0, 200)
    if spec == "red":    return (200, 0, 0)
    if spec == "yellow": return (200, 200, 0)
    if spec in ("orange", "amber"): return (200, 140, 0)
    return CONFIDENCE_COLORS.get(confidence, (0, 0, 0))


def annotate(image_path: Path, annotations_path: Path, output_path: Path) -> Path:
    data: dict[str, Any] = json.loads(annotations_path.read_text())
    img = Image.open(image_path).convert("RGB").copy()
    draw = ImageDraw.Draw(img)

    scale = data.get("scale", {})
    mm_per_px = scale["mm"] / scale["pixels"] if scale else None
    origin = data.get("origin")

    if origin:
        ox, oy = origin
        draw.line([(ox - 20, oy), (ox + 20, oy)], fill=(0, 0, 0), width=2)
        draw.line([(ox, oy - 20), (ox, oy + 20)], fill=(0, 0, 0), width=2)
        draw.text((ox + 8, oy + 8), "O", fill=(0, 0, 0))

    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    for feat in data.get("features", []):
        conf = int(feat.get("confidence", 3))
        if conf < 1 or conf > 5:
            raise ValueError(f"confidence must be 1..5, got {conf}")
        color = _pick_color(feat.get("color"), conf)
        cx, cy = feat["center_px"]
        sw_mm, sh_mm = feat["size_mm"]
        if mm_per_px is None:
            raise ValueError("annotations.scale required to convert size_mm → px")
        sw_px = sw_mm / mm_per_px
        sh_px = sh_mm / mm_per_px
        draw.rectangle(
            [cx - sw_px / 2, cy - sh_px / 2, cx + sw_px / 2, cy + sh_px / 2],
            outline=color, width=2,
        )
        label = f"{feat['name']} [{ '★' * conf }]"
        draw.text((cx + sw_px / 2 + 4, cy - sh_px / 2), label, fill=color, font=font)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)
    return output_path


def main() -> int:
    p = argparse.ArgumentParser(description="Annotate a reference photo with dims + features.")
    p.add_argument("photo", type=Path)
    p.add_argument("--annotations", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    try:
        out = annotate(args.photo, args.annotations, args.output)
    except (ValueError, FileNotFoundError, KeyError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
