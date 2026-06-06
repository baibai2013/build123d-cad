#!/usr/bin/env python3
"""本地 DFM 检测 — 读 tscircuit 的 circuit.json,比对嘉立创工艺能力。

免 key、免导出、免上传:几何全在 circuit.json 里(pcb_trace.width / pcb_smtpad /
pcb_plated_hole / pcb_board)。这是出件前第一道闸,**不替代**嘉立创官方审核(权威)。

用法:
    python3 dfm_check.py <circuit.json> [--process jlcpcb_standard] [--json]
退出码:0 = 通过(可有 warning);1 = 有 violation;2 = 用法/文件错。

注意:这是 DRC 之外的「可制造性」检查(tscircuit 不做 DFM)。规则值为嘉立创标准
2 层 1oz 的保守阈值,实际下单以官方 audit_info 为准。
"""
from __future__ import annotations
import argparse
import json
import sys

# 嘉立创工艺阈值(mm)。标准 2 层 1oz 的保守值;改厂/改工艺时调这里。
PROCESSES = {
    "jlcpcb_standard": {
        "min_trace_width_mm": 0.127,   # 最小线宽 (~5mil)
        "min_hole_mm": 0.20,           # 最小成品孔径
        "min_annular_ring_mm": 0.13,   # 最小环宽
        "copper_to_edge_mm": 0.20,     # 铜/焊盘到板边最小间距
    }
}


def load(path: str) -> list:
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    if not isinstance(d, list):
        raise ValueError("circuit.json 顶层应是元素数组(tsci build 产物)")
    return d


def _of(elements, t):
    return [e for e in elements if e.get("type") == t]


def check(elements: list, rules: dict) -> dict:
    violations, warnings = [], []

    # 板框 bbox(铜到边用)
    board = next(iter(_of(elements, "pcb_board")), None)
    bbox = None
    if board and "width" in board and "height" in board:
        c = board.get("center", {"x": 0, "y": 0})
        hw, hh = board["width"] / 2, board["height"] / 2
        bbox = (c["x"] - hw, c["y"] - hh, c["x"] + hw, c["y"] + hh)

    # 1) 线宽
    mt = rules["min_trace_width_mm"]
    for tr in _of(elements, "pcb_trace"):
        for seg in tr.get("route", []):
            w = seg.get("width")
            if isinstance(w, (int, float)) and w < mt:
                violations.append(f"线宽 {w}mm < 最小 {mt}mm (trace {tr.get('pcb_trace_id','?')})")
                break

    # 2) 孔径 + 环宽
    mh, mar = rules["min_hole_mm"], rules["min_annular_ring_mm"]
    for h in _of(elements, "pcb_plated_hole") + _of(elements, "pcb_hole"):
        hole = h.get("hole_diameter") or h.get("diameter")
        outer = h.get("outer_diameter")
        if isinstance(hole, (int, float)) and hole < mh:
            violations.append(f"孔径 {hole}mm < 最小 {mh}mm @({h.get('x')},{h.get('y')})")
        if isinstance(hole, (int, float)) and isinstance(outer, (int, float)):
            ring = (outer - hole) / 2
            if ring < mar:
                violations.append(f"环宽 {ring:.3f}mm < 最小 {mar}mm @({h.get('x')},{h.get('y')})")

    # 3) 铜到板边
    if bbox:
        m = rules["copper_to_edge_mm"]
        x0, y0, x1, y1 = bbox
        for p in _of(elements, "pcb_smtpad"):
            px, py = p.get("x", 0), p.get("y", 0)
            pw, ph = p.get("width", 0) / 2, p.get("height", 0) / 2
            if (px - pw < x0 + m or px + pw > x1 - m or
                    py - ph < y0 + m or py + ph > y1 - m):
                warnings.append(f"焊盘距板边 < {m}mm @({px},{py})(疑似铜到边不足)")

    # 4) tscircuit 自身的供应商封装不匹配警告(透传)
    for w in _of(elements, "supplier_footprint_mismatch_warning"):
        warnings.append("封装与供应商不符: " + str(w.get("message", ""))[:100])

    return {"violations": violations, "warnings": warnings,
            "passed": len(violations) == 0, "has_board": bbox is not None}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="本地 DFM 检测(读 circuit.json)")
    ap.add_argument("circuit_json")
    ap.add_argument("--process", default="jlcpcb_standard", choices=list(PROCESSES))
    ap.add_argument("--json", action="store_true", help="机器可读输出")
    a = ap.parse_args(argv)

    try:
        elements = load(a.circuit_json)
    except FileNotFoundError:
        print(f"✗ 找不到 {a.circuit_json};先 tsci build 出 dist/<entry>/circuit.json", file=sys.stderr)
        return 2
    except ValueError as e:
        print(f"✗ {e}", file=sys.stderr)
        return 2

    res = check(elements, PROCESSES[a.process])
    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        for v in res["violations"]:
            print(f"  ✗ {v}")
        for w in res["warnings"]:
            print(f"  ⚠ {w}")
        print(f"DFM[{a.process}]: {'PASS' if res['passed'] else 'FAIL'} "
              f"({len(res['violations'])} violation, {len(res['warnings'])} warning)")
        if not res["has_board"]:
            print("  (注:未见 pcb_board,跳过铜到边检查)")
    return 0 if res["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
