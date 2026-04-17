#!/usr/bin/env python3
"""Geometric visual comparison: rendered vs preprocessed reference.
几何视角的视觉对比：渲染图 vs 预处理后的参考图。

Produces one of three outputs per invocation:
  side_by_side   两图并排
  edge_overlay   Canny 边缘叠加（红=参考，蓝=渲染，紫=吻合）
  diff_heatmap   灰度差热图

Prerequisite: reference image MUST have passed through preprocess_reference.py
            参考图必须先经过 preprocess_reference.py 得到 *_scale.json
            否则 IoU/差值无物理意义，脚本会拒绝执行。

CLI:
    python3 visual_compare.py <rendered.png> <reference_cropped.png> \\
        --reference-scale refs/clean/front_scale.json \\
        --rendered-scale auto \\
        --mode edge_overlay \\
        --output out/compare_front.png
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from typing import Tuple

import numpy as np
from PIL import Image

try:
    import cv2  # type: ignore
except ImportError:
    cv2 = None  # type: ignore


CANNY_LOW = 50
CANNY_HIGH = 150


def canny_edges(gray: np.ndarray, sigma: float = 1.0) -> np.ndarray:
    if cv2 is None:
        raise RuntimeError("opencv-python not installed; required for Canny.")
    blurred = cv2.GaussianBlur(gray, ksize=(0, 0), sigmaX=sigma)
    return cv2.Canny(blurred, CANNY_LOW, CANNY_HIGH)


def normalize_to_scale(
    a: Image.Image, mm_per_px_a: float,
    b: Image.Image, mm_per_px_b: float,
) -> Tuple[Image.Image, Image.Image]:
    """Resize both images to the coarser of the two mm/px scales."""
    target_mm_per_px = max(mm_per_px_a, mm_per_px_b)
    def _rescale(img: Image.Image, from_mm_per_px: float) -> Image.Image:
        factor = from_mm_per_px / target_mm_per_px
        new_w = max(1, int(round(img.width * factor)))
        new_h = max(1, int(round(img.height * factor)))
        return img.resize((new_w, new_h), Image.LANCZOS)
    return _rescale(a, mm_per_px_a), _rescale(b, mm_per_px_b)


def _align_shapes(a: Image.Image, b: Image.Image) -> Tuple[Image.Image, Image.Image]:
    w = max(a.width, b.width)
    h = max(a.height, b.height)
    pad_a = Image.new("RGB", (w, h), "white"); pad_a.paste(a, (0, 0))
    pad_b = Image.new("RGB", (w, h), "white"); pad_b.paste(b, (0, 0))
    return pad_a, pad_b


def compose_side_by_side(a: Image.Image, b: Image.Image) -> Image.Image:
    h = max(a.height, b.height)
    canvas = Image.new("RGB", (a.width + b.width, h), "white")
    canvas.paste(a, (0, 0))
    canvas.paste(b, (a.width, 0))
    return canvas


def compose_edge_overlay(rendered: Image.Image, reference: Image.Image) -> Image.Image:
    r, f = _align_shapes(rendered, reference)
    er = canny_edges(np.array(r.convert("L")))
    ef = canny_edges(np.array(f.convert("L")))
    rgb = np.zeros((*er.shape, 3), dtype=np.uint8)
    rgb[..., 0] = ef      # reference → red
    rgb[..., 2] = er      # rendered → blue
    rgb[(ef > 0) & (er > 0)] = [255, 0, 255]  # agreement → purple
    return Image.fromarray(rgb)


def compose_diff_heatmap(rendered: Image.Image, reference: Image.Image) -> Image.Image:
    r, f = _align_shapes(rendered, reference)
    ar = np.array(r.convert("L")).astype(np.int16)
    af = np.array(f.convert("L")).astype(np.int16)
    diff = np.abs(ar - af).astype(np.uint8)
    if cv2 is not None:
        heat = cv2.applyColorMap(diff, cv2.COLORMAP_HOT)
        heat = cv2.cvtColor(heat, cv2.COLOR_BGR2RGB)
    else:
        heat = np.stack([diff, np.zeros_like(diff), np.zeros_like(diff)], axis=-1)
    return Image.fromarray(heat)


def _load_scale(path: Path) -> float:
    data = json.loads(path.read_text())
    return float(data["mm_per_px"])


def _load_rendered_scale(spec: str, rendered: Path) -> float:
    if spec == "auto":
        return 1.0
    if spec.endswith(".json"):
        return _load_scale(Path(spec))
    return float(spec)


def main() -> int:
    p = argparse.ArgumentParser(description="Geometric visual compare.")
    p.add_argument("rendered", type=Path)
    p.add_argument("reference", type=Path)
    p.add_argument("--reference-scale", required=True, type=Path)
    p.add_argument("--rendered-scale", default="auto", help="'auto' | float | scale.json path")
    p.add_argument("--mode", choices=["side_by_side", "edge_overlay", "diff_heatmap"], default="edge_overlay")
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()

    try:
        ref_scale = _load_scale(args.reference_scale)
        ren_scale = _load_rendered_scale(args.rendered_scale, args.rendered)
        a = Image.open(args.rendered).convert("RGB")
        b = Image.open(args.reference).convert("RGB")
        a_n, b_n = normalize_to_scale(a, ren_scale, b, ref_scale)
    except (ValueError, FileNotFoundError, KeyError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    if args.mode == "side_by_side":
        out = compose_side_by_side(a_n, b_n)
    elif args.mode == "edge_overlay":
        out = compose_edge_overlay(a_n, b_n)
    else:
        out = compose_diff_heatmap(a_n, b_n)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    out.save(args.output)
    print(f"wrote {args.output} (mode={args.mode}, ref_mm_per_px={ref_scale}, ren_mm_per_px={ren_scale})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
