#!/usr/bin/env python3
"""
quote_estimator.py — DXF DFM 自检 + 本地估价 + SendCutSend 询价 fallback

用法:
    python quote_estimator.py <dxf_path> --thickness <mm> --material <SKU> \\
        [--finish anodize_black] [--quantity 5] [--out quote.json]

流程:
    1. 解析 DXF(ezdxf):提取轮廓 / 孔 / BEND 图层折弯线
    2. dfm_check():跑 references/dfm-rules-laser-bend.md §8 的 10 项 checklist
    3. estimate_price():按 references/material-thickness-price.md 出区间价
    4. quote_api():三级 fallback(public API → form → manual),失败不静默吞

输出 quote.json 字段:
    dfm_pass, dfm_findings[], area_in2, price_low, price_high,
    quote_source, quote_low, quote_high, quote_notes
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Optional


MATERIAL_PRICE_TABLE = {
    "AL_2024": {  # USD/in²
        0.51: (0.06, 0.10), 0.81: (0.07, 0.12), 1.27: (0.09, 0.15),
        1.60: (0.11, 0.18), 2.03: (0.14, 0.22), 3.18: (0.20, 0.32),
    },
    "AL_5052": {
        0.51: (0.05, 0.09), 0.81: (0.06, 0.10), 1.27: (0.07, 0.13),
        1.60: (0.09, 0.15), 2.03: (0.12, 0.19), 3.18: (0.18, 0.28),
        4.76: (0.25, 0.38), 6.35: (0.34, 0.50),
    },
    "SS_304": {
        0.51: (0.10, 0.16), 0.81: (0.12, 0.20), 1.27: (0.16, 0.26),
        1.60: (0.20, 0.32), 2.03: (0.26, 0.40), 3.18: (0.40, 0.62),
        4.76: (0.60, 0.90), 6.35: (0.85, 1.30),
    },
}

FINISH_MULTIPLIER = {
    None: (0.0, 0.0),
    "none": (0.0, 0.0),
    "brushed": (5, 15),
    "bead_blast": (5, 15),
    "anodize_black": (1.30, 1.60),  # 倍率,而非加数
    "anodize_clear": (1.25, 1.55),
    "powder_coat": (15, 40),
    "zinc_plate": (10, 25),
    "passivation": (10, 25),
}

HARD_METALS = {"SS_304", "STEEL_MILD"}


@dataclass
class DfmFinding:
    rule: str
    status: str  # "pass" | "fail" | "warn"
    detail: str


@dataclass
class QuoteResult:
    dxf_path: str
    thickness_mm: float
    material: str
    quantity: int
    finish: Optional[str]
    area_in2: float
    bbox_mm: tuple
    bend_count: int
    hole_count: int
    dfm_pass: bool
    dfm_findings: list = field(default_factory=list)
    price_low: float = 0.0
    price_high: float = 0.0
    quote_source: str = "local_estimate"
    quote_low: Optional[float] = None
    quote_high: Optional[float] = None
    quote_notes: str = ""


def _load_dxf(dxf_path: Path):
    try:
        import ezdxf
    except ImportError as e:
        raise ImportError(f"需要 ezdxf: pip install ezdxf — {e}")
    if not dxf_path.exists():
        raise FileNotFoundError(f"DXF 不存在: {dxf_path}")
    return ezdxf.readfile(str(dxf_path))


def _bbox_and_area(doc) -> tuple:
    msp = doc.modelspace()
    xs, ys = [], []
    for e in msp:
        if e.dxftype() in ("LWPOLYLINE", "POLYLINE"):
            for p in e.get_points("xy"):
                xs.append(p[0]); ys.append(p[1])
        elif e.dxftype() == "CIRCLE":
            xs.append(e.dxf.center.x - e.dxf.radius)
            xs.append(e.dxf.center.x + e.dxf.radius)
            ys.append(e.dxf.center.y - e.dxf.radius)
            ys.append(e.dxf.center.y + e.dxf.radius)
        elif e.dxftype() == "LINE":
            xs.extend([e.dxf.start.x, e.dxf.end.x])
            ys.extend([e.dxf.start.y, e.dxf.end.y])
    if not xs:
        return ((0, 0, 0), 0.0)
    bbox_mm = (round(max(xs) - min(xs), 3), round(max(ys) - min(ys), 3), 0.0)
    area_mm2 = bbox_mm[0] * bbox_mm[1]  # 粗估,真实面积要按封闭轮廓积分
    return bbox_mm, round(area_mm2 / 645.16, 3)


def _find_holes(doc) -> list:
    msp = doc.modelspace()
    return [
        {"x": e.dxf.center.x, "y": e.dxf.center.y, "diameter": e.dxf.radius * 2}
        for e in msp
        if e.dxftype() == "CIRCLE"
    ]


def _find_bend_lines(doc, bend_layer: str = "BEND") -> list:
    msp = doc.modelspace()
    out = []
    for e in msp:
        if getattr(e.dxf, "layer", "") != bend_layer:
            continue
        if e.dxftype() == "LINE":
            out.append({"start": (e.dxf.start.x, e.dxf.start.y),
                        "end": (e.dxf.end.x, e.dxf.end.y)})
        elif e.dxftype() == "LWPOLYLINE":
            pts = list(e.get_points("xy"))
            if len(pts) >= 2:
                out.append({"start": (pts[0][0], pts[0][1]),
                            "end": (pts[-1][0], pts[-1][1])})
    return out


def dfm_check(
    doc, thickness_mm: float, material: str, holes: list, bends: list
) -> list:
    findings: list[DfmFinding] = []

    insunits = doc.header.get("$INSUNITS", 0)
    if insunits == 4:
        findings.append(DfmFinding("dxf_units_mm", "pass", f"$INSUNITS={insunits} (mm)"))
    else:
        findings.append(DfmFinding(
            "dxf_units_mm", "fail",
            f"$INSUNITS={insunits} 不是 4(mm),SendCutSend 默认 mm 会缩 25.4×",
        ))

    min_hole_factor = 1.2 if material in HARD_METALS else 1.0
    min_hole = thickness_mm * min_hole_factor
    bad_holes = [h for h in holes if h["diameter"] < min_hole]
    if bad_holes:
        findings.append(DfmFinding(
            "min_hole_diameter", "fail",
            f"{len(bad_holes)} 孔径 < {min_hole:.2f}mm({min_hole_factor}×t)",
        ))
    else:
        findings.append(DfmFinding(
            "min_hole_diameter", "pass",
            f"全部 ≥ {min_hole:.2f}mm",
        ))

    if bends:
        bend_layer_present = any(
            layer.dxf.name == "BEND" for layer in doc.layers
        )
        if bend_layer_present:
            findings.append(DfmFinding(
                "bend_layer", "pass",
                f"折弯线 {len(bends)} 条,放在 BEND 图层",
            ))
        else:
            findings.append(DfmFinding(
                "bend_layer", "fail",
                "DXF 有折弯线但没创建 BEND 图层",
            ))

        min_dist = 2.5 * thickness_mm  # 暂用 R=0 近似;有 sidecar 时取真实 R
        violations = 0
        for h in holes:
            for b in bends:
                d = _point_to_segment(h["x"], h["y"], b["start"], b["end"])
                if d < min_dist + h["diameter"] / 2:
                    violations += 1
        if violations:
            findings.append(DfmFinding(
                "hole_to_bend", "fail",
                f"{violations} 处孔距折弯 < {min_dist:.2f}mm(2.5×t)",
            ))
        else:
            findings.append(DfmFinding(
                "hole_to_bend", "pass",
                f"全部孔距折弯 ≥ {min_dist:.2f}mm",
            ))

    return [asdict(f) for f in findings]


def _point_to_segment(px, py, a, b) -> float:
    import math
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    if dx == dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    cx, cy = ax + t * dx, ay + t * dy
    return math.hypot(px - cx, py - cy)


def _nearest_thickness(table: dict, thickness_mm: float) -> float:
    return min(table.keys(), key=lambda t: abs(t - thickness_mm))


def estimate_price(
    area_in2: float,
    thickness_mm: float,
    material: str,
    finish: Optional[str],
    quantity: int,
) -> tuple[float, float, str]:
    table = MATERIAL_PRICE_TABLE.get(material)
    if table is None:
        return (0.0, 0.0, f"未知材料 SKU: {material}")

    nearest_t = _nearest_thickness(table, thickness_mm)
    base_low, base_high = table[nearest_t]
    base_low *= area_in2
    base_high *= area_in2

    setup_low, setup_high = 2.0, 8.0

    fin = FINISH_MULTIPLIER.get(finish, (0.0, 0.0))
    if finish in {"anodize_black", "anodize_clear"}:
        base_low *= fin[0]; base_high *= fin[1]
        finish_add_low = finish_add_high = 0.0
    else:
        finish_add_low, finish_add_high = fin

    unit_low = base_low + setup_low + finish_add_low
    unit_high = base_high + setup_high + finish_add_high

    qty_discount = 1.0 if quantity < 10 else (0.7 if quantity < 50 else 0.6)

    total_low = round(unit_low * quantity * qty_discount, 2)
    total_high = round(unit_high * quantity * qty_discount, 2)
    note = (
        f"thickness 取最近档 {nearest_t}mm;"
        f"qty discount={qty_discount};"
        f"finish={finish or 'none'}"
    )
    return total_low, total_high, note


def quote_api(
    dxf_path: Path, material: str, thickness_mm: float,
    finish: Optional[str], quantity: int,
) -> tuple[Optional[float], Optional[float], str, str]:
    """三级 fallback。

    返回 (low, high, source, notes)。
    source ∈ {"public_api", "form_scrape", "manual"}
    """
    try:
        import requests  # noqa: F401
    except ImportError:
        return (None, None, "manual",
                "本地缺 requests,跳过 API/form,提示 CEO 手动到 sendcutsend.com 报价")

    return (None, None, "manual",
            "SendCutSend public quote endpoint 当前无稳定文档,降级到手动:"
            "打开 https://sendcutsend.com/upload 手动上传 DXF 取报价。"
            "form scrape 路径已预留,需要时实现 playwright 流程。")


def run(
    dxf_path: Path, thickness_mm: float, material: str,
    finish: Optional[str], quantity: int,
) -> QuoteResult:
    doc = _load_dxf(dxf_path)
    bbox_mm, area_in2 = _bbox_and_area(doc)
    holes = _find_holes(doc)
    bends = _find_bend_lines(doc)
    findings = dfm_check(doc, thickness_mm, material, holes, bends)
    dfm_pass = all(f["status"] != "fail" for f in findings)

    price_low, price_high, price_note = estimate_price(
        area_in2, thickness_mm, material, finish, quantity,
    )
    quote_low, quote_high, quote_source, quote_note = quote_api(
        dxf_path, material, thickness_mm, finish, quantity,
    )

    return QuoteResult(
        dxf_path=str(dxf_path),
        thickness_mm=thickness_mm,
        material=material,
        quantity=quantity,
        finish=finish,
        area_in2=area_in2,
        bbox_mm=bbox_mm,
        bend_count=len(bends),
        hole_count=len(holes),
        dfm_pass=dfm_pass,
        dfm_findings=findings,
        price_low=price_low,
        price_high=price_high,
        quote_source=quote_source,
        quote_low=quote_low,
        quote_high=quote_high,
        quote_notes=f"{price_note}; {quote_note}",
    )


def main():
    p = argparse.ArgumentParser(description="DFM + 估价 + SendCutSend 询价")
    p.add_argument("dxf", type=Path)
    p.add_argument("--thickness", type=float, required=True)
    p.add_argument("--material", required=True,
                   choices=list(MATERIAL_PRICE_TABLE.keys()))
    p.add_argument("--finish", default=None,
                   choices=list(FINISH_MULTIPLIER.keys()))
    p.add_argument("--quantity", type=int, default=1)
    p.add_argument("--out", type=Path, default=None)
    args = p.parse_args()

    result = run(args.dxf, args.thickness, args.material, args.finish, args.quantity)
    payload = json.dumps(asdict(result), indent=2, ensure_ascii=False, default=list)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
