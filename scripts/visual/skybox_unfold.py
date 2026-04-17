#!/usr/bin/env python3
"""Render skybox-style 6-face unfold of a part via OCP Viewer.
通过"相机固定 + 旋转模型"生成 6 面贴图并拼成十字展开。

Face layout (cross):
            TOP
    LEFT  FRONT  RIGHT  BACK
            BOTTOM

Prerequisite: OCP Viewer must be running.
前置：OCP Viewer 必须处于运行状态。

CLI:
    python3 skybox_unfold.py <input.step> \\
        [--output-dir PATH] [--name NAME]
"""
from __future__ import annotations
import argparse
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
from PIL import Image

from ocp_vscode import show, save_screenshot, set_port, Camera  # type: ignore
from ocp_vscode.comms import port_check  # type: ignore
from ocp_vscode.state import get_ports  # type: ignore
from build123d import Axis, import_step  # type: ignore

FACE_ROTATIONS: Dict[str, List[Tuple[Axis, float]]] = {
    "FRONT": [(Axis.X, 90)],
    "BACK":  [(Axis.X, 90), (Axis.Z, 180)],
    "UP":    [(Axis.X, 180)],
    "DOWN":  [],
    "LEFT":  [(Axis.Z, 90)],
    "RIGHT": [(Axis.Z, -90)],
}

MAX_CELL_W, MAX_CELL_H = 700, 500
CANVAS_W, CANVAS_H = MAX_CELL_W * 4, MAX_CELL_H * 3


def _ensure_viewer() -> None:
    ports = list(get_ports())
    active = next((int(p) for p in ports if port_check(int(p))), None)
    if active is None:
        print(
            f"ERROR: OCP Viewer not responsive on ports {ports or '[]'}. Start OCP Viewer first.",
            file=sys.stderr,
        )
        sys.exit(2)
    set_port(active)


def _capture_face(model, face: str, out_dir: Path, name_stem: str) -> Path:
    m = model
    for axis, deg in FACE_ROTATIONS[face]:
        m = m.rotate(axis, deg)
    show(m, names=[f"skybox_{face}"], reset_camera=Camera.FRONT)
    time.sleep(0.9)
    path = out_dir / f"{name_stem}_skybox_{face}.png"
    save_screenshot(str(path))
    return path


def _trim_white(img: Image.Image, pad: int = 20, threshold: int = 250) -> Image.Image:
    gray = np.array(img.convert("L"))
    mask = gray < threshold
    if not mask.any():
        return img
    rows = np.any(mask, axis=1)
    cols = np.any(mask, axis=0)
    y0, y1 = int(np.argmax(rows)), len(rows) - 1 - int(np.argmax(rows[::-1]))
    x0, x1 = int(np.argmax(cols)), len(cols) - 1 - int(np.argmax(cols[::-1]))
    y0 = max(0, y0 - pad); y1 = min(img.height - 1, y1 + pad)
    x0 = max(0, x0 - pad); x1 = min(img.width - 1, x1 + pad)
    return img.crop((x0, y0, x1 + 1, y1 + 1))


def _fit_cell(img: Image.Image, cell_w: int, cell_h: int) -> Image.Image:
    scale = min(cell_w / img.width, cell_h / img.height)
    nw = max(1, int(img.width * scale))
    nh = max(1, int(img.height * scale))
    resized = img.resize((nw, nh), Image.LANCZOS)
    cell = Image.new("RGB", (cell_w, cell_h), "white")
    cell.paste(resized, ((cell_w - nw) // 2, (cell_h - nh) // 2))
    return cell


def compose_cross(faces: Dict[str, Image.Image]) -> Image.Image:
    canvas = Image.new("RGB", (CANVAS_W, CANVAS_H), "white")
    positions = {
        "UP":    (1, 0),
        "LEFT":  (0, 1),
        "FRONT": (1, 1),
        "RIGHT": (2, 1),
        "BACK":  (3, 1),
        "DOWN":  (1, 2),
    }
    for name, (col, row) in positions.items():
        cell = _fit_cell(_trim_white(faces[name]), MAX_CELL_W, MAX_CELL_H)
        canvas.paste(cell, (col * MAX_CELL_W, row * MAX_CELL_H))
    return canvas


def main() -> int:
    p = argparse.ArgumentParser(description="Skybox 6-face unfold.")
    p.add_argument("source", type=Path)
    p.add_argument("--output-dir", type=Path, default=Path("output"))
    p.add_argument("--name", default=None)
    args = p.parse_args()

    _ensure_viewer()
    name_stem = args.name or args.source.stem
    args.output_dir.mkdir(parents=True, exist_ok=True)

    if args.source.suffix.lower() not in {".step", ".stp"}:
        print("ERROR: skybox_unfold currently supports only .step input.", file=sys.stderr)
        return 2
    model = import_step(str(args.source))

    face_paths: Dict[str, Path] = {}
    for face in FACE_ROTATIONS:
        face_paths[face] = _capture_face(model, face, args.output_dir, name_stem)

    faces = {face: Image.open(path).convert("RGB") for face, path in face_paths.items()}
    cross = compose_cross(faces)
    cross_path = args.output_dir / f"{name_stem}_skybox_unfolded.png"
    cross.save(cross_path)
    print(f"wrote {cross_path}")
    for f, path in face_paths.items():
        print(f"  {f}: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
