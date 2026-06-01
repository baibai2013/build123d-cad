#!/usr/bin/env python3
"""Generate 7 orthographic + 4 ISO screenshots via OCP Viewer.
通过 OCP Viewer 生成 7 正交视图 + 4 ISO 变体截图。

Prerequisite: OCP Viewer must be running (port 3939 or 4567).
前置：OCP Viewer 必须处于运行状态（端口 3939 或 4567）。

CLI:
    python3 multi_view_screenshot.py <input.step|input.py> \\
        [--output-dir PATH] \\
        [--name NAME] \\
        [--mode ortho|iso|both] \\
        [--face-mapping PATH] \\
        [--views FRONT,BACK,...]
"""
from __future__ import annotations
import argparse
import subprocess
import sys
import time
from pathlib import Path
from typing import List

from scripts.visual.face_mapping import load_face_mapping, FaceMapping

from ocp_vscode import show, save_screenshot, set_port, Camera  # type: ignore
from ocp_vscode.comms import port_check  # type: ignore
from ocp_vscode.state import get_ports  # type: ignore

ORTHO_SEMANTIC = ["FRONT", "BACK", "LEFT", "RIGHT", "TOP", "BOTTOM"]
ISO_VARIANTS = [
    ("ISO_FRONT_TOP",    Camera.ISO,  (30,   0,  30)),
    ("ISO_FRONT_BOTTOM", Camera.ISO,  (-30,  0,  30)),
    ("ISO_BACK_TOP",     Camera.ISO,  (30,   0, 210)),
    ("ISO_BACK_BOTTOM",  Camera.ISO,  (-30,  0, 210)),
]


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


def _load_model(path: Path):
    if path.suffix.lower() in {".step", ".stp"}:
        from build123d import import_step
        return import_step(str(path))
    if path.suffix.lower() == ".py":
        result = subprocess.run(
            [sys.executable, str(path)], check=False, capture_output=True, text=True
        )
        if result.returncode != 0:
            print(result.stderr, file=sys.stderr)
            sys.exit(2)
        return None
    raise ValueError(f"unsupported input: {path.suffix}")


def _camera_for(name: str):
    return getattr(Camera, name)


def capture_orthographic(
    model, name_stem: str, output_dir: Path, mapping: FaceMapping, views: List[str]
) -> List[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    produced: List[Path] = []
    for sem in views:
        cam_name = mapping.semantic_to_camera(sem)
        if model is not None:
            show(model, reset_camera=_camera_for(cam_name))
        time.sleep(0.9)
        path = output_dir / f"{name_stem}_{sem}.png"
        save_screenshot(str(path))
        produced.append(path)
    if model is not None:
        show(model, reset_camera=Camera.ISO)
        time.sleep(0.9)
    iso_path = output_dir / f"{name_stem}_ISO.png"
    save_screenshot(str(iso_path))
    produced.append(iso_path)
    return produced


def capture_iso_variants(model, name_stem: str, output_dir: Path) -> List[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    produced: List[Path] = []
    for label, cam, _hint in ISO_VARIANTS:
        if model is not None:
            show(model, reset_camera=cam)
        time.sleep(0.9)
        path = output_dir / f"{name_stem}_{label}.png"
        save_screenshot(str(path))
        produced.append(path)
    return produced


def main() -> int:
    p = argparse.ArgumentParser(description="Multi-view screenshot via OCP Viewer.")
    p.add_argument("source", type=Path, help="input.step or input.py")
    p.add_argument("--output-dir", type=Path, default=Path("output"))
    p.add_argument("--name", default=None)
    p.add_argument("--mode", choices=["ortho", "iso", "both"], default="ortho")
    p.add_argument("--face-mapping", type=Path, default=None)
    p.add_argument("--views", default=",".join(ORTHO_SEMANTIC))
    args = p.parse_args()

    _ensure_viewer()
    name_stem = args.name or args.source.stem
    mapping = load_face_mapping(args.face_mapping)
    if mapping.is_default:
        print(
            "WARNING: no --face-mapping supplied; view names = coord axes (may not match part semantics).",
            file=sys.stderr,
        )

    model = _load_model(args.source)
    views = [v.strip() for v in args.views.split(",") if v.strip()]

    produced: List[Path] = []
    if args.mode in ("ortho", "both"):
        produced += capture_orthographic(model, name_stem, args.output_dir, mapping, views)
    if args.mode in ("iso", "both"):
        produced += capture_iso_variants(model, name_stem, args.output_dir)

    for p_ in produced:
        print(p_)
    return 0


if __name__ == "__main__":
    sys.exit(main())
