#!/usr/bin/env python3
"""
step_to_dxf.py — STEP 钣金件投影到 XY 平面输出 SendCutSend 合规 DXF

用法:
    python step_to_dxf.py <step_path> --thickness <mm> --material <SKU> \\
        --out <dxf_path> [--bend-layer BEND]

约定:
- STEP 必须是已展平的钣金件(由 mechanical 用 unfold/flatten 出),
  本脚本不做 unfold,只做投影 + 出 DXF。
- 折弯线在 STEP 中由 mechanical 标为单独 named edge group "BEND_*",
  本脚本读到这些 edge → 放进 DXF 的 BEND 图层并设 DASHED 线型。
- DXF 单位强制 mm($INSUNITS=4)。
- 始终导名义尺寸,**不**做 kerf 预补偿(SendCutSend CAM 端补)。

依赖:
    build123d ≥ 0.7  (import_step / Plane / project)
    ezdxf      ≥ 1.0 (写 BEND 图层 + 线型)
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional


def step_to_dxf(
    step_path: Path,
    out_path: Path,
    thickness_mm: float,
    material_sku: str,
    bend_layer: str = "BEND",
    sidecar_meta: Optional[dict] = None,
) -> dict:
    """投影 STEP 钣金件 → DXF。

    返回 summary dict:
        {dxf_path, area_in2, bbox_mm, bend_count, layers}
    """
    try:
        import build123d as b3d
        import ezdxf
        from ezdxf import units
    except ImportError as e:
        raise ImportError(
            f"需要 build123d + ezdxf,先 `pip install build123d ezdxf`: {e}"
        )

    if not step_path.exists():
        raise FileNotFoundError(f"STEP 不存在: {step_path}")

    part = b3d.import_step(str(step_path))

    bbox = part.bounding_box()
    bbox_mm = (
        round(bbox.size.X, 3),
        round(bbox.size.Y, 3),
        round(bbox.size.Z, 3),
    )

    z_min = bbox.min.Z
    bottom_face = max(
        (f for f in part.faces() if abs(f.center().Z - z_min) < 1e-3),
        key=lambda f: f.area,
        default=None,
    )
    if bottom_face is None:
        raise RuntimeError("找不到底面,STEP 可能不是平展钣金件(请上游 unfold)")

    outline_2d = bottom_face.project_to_viewport((0, 0, 1))[0]

    bend_edges_2d = []
    if sidecar_meta and "bends" in sidecar_meta:
        for edge in part.edges():
            tag = getattr(edge, "label", "") or ""
            if tag.startswith("BEND_") or tag in {b["line_id"] for b in sidecar_meta["bends"]}:
                proj = edge.project_to_viewport((0, 0, 1))[0]
                bend_edges_2d.append(proj)

    doc = ezdxf.new(setup=True)
    doc.units = units.MM
    doc.header["$INSUNITS"] = 4

    msp = doc.modelspace()
    if bend_layer not in doc.layers:
        doc.layers.add(name=bend_layer, dxfattribs={"linetype": "DASHED", "color": 1})

    for shape in outline_2d:
        for edge in shape.edges():
            verts = [(v.X, v.Y) for v in edge.vertices()]
            if len(verts) >= 2:
                msp.add_lwpolyline(verts, dxfattribs={"layer": "0"})

    for shape in bend_edges_2d:
        for edge in shape.edges():
            verts = [(v.X, v.Y) for v in edge.vertices()]
            if len(verts) >= 2:
                msp.add_lwpolyline(verts, dxfattribs={"layer": bend_layer})

    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(str(out_path))

    area_mm2 = bottom_face.area
    area_in2 = round(area_mm2 / 645.16, 3)

    summary = {
        "dxf_path": str(out_path),
        "step_path": str(step_path),
        "thickness_mm": thickness_mm,
        "material_sku": material_sku,
        "bbox_mm": bbox_mm,
        "area_in2": area_in2,
        "bend_count": len(bend_edges_2d),
        "layers": ["0", bend_layer],
        "kerf_compensation": "none (SendCutSend CAM applies)",
    }
    return summary


def _load_sidecar(step_path: Path) -> Optional[dict]:
    sidecar = step_path.with_suffix(".meta.json")
    if sidecar.exists():
        return json.loads(sidecar.read_text(encoding="utf-8"))
    return None


def main():
    p = argparse.ArgumentParser(description="STEP 钣金 → SendCutSend DXF")
    p.add_argument("step", type=Path, help="输入 STEP 路径(必须已展平)")
    p.add_argument("--thickness", type=float, required=True, help="板厚 mm")
    p.add_argument("--material", required=True, help="SendCutSend material SKU,如 AL_5052")
    p.add_argument("--out", type=Path, required=True, help="输出 DXF 路径")
    p.add_argument("--bend-layer", default="BEND", help="折弯线图层名(默认 BEND)")
    args = p.parse_args()

    sidecar = _load_sidecar(args.step)
    summary = step_to_dxf(
        args.step,
        args.out,
        thickness_mm=args.thickness,
        material_sku=args.material,
        bend_layer=args.bend_layer,
        sidecar_meta=sidecar,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
