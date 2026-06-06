#!/usr/bin/env python3
"""从 circuit.json 派生 BOM 并用 jlcpcb-mcp(免 key)定价,写 <board>.bom.json。

供 viewer 的 BOM/总价面板读取(sidecar,解耦:viewer 只读文件,pcb 管定价)。
免 key 即可跑物料报价(实测);MCP 不可用时降级写 unpriced(不假装价格)。

用法:
    python3 bom_price.py <circuit.json> [--out <board>.bom.json] [--board-qty 5]
输出 bom.json:{currency, board_qty, items:[{ref,value,footprint,lcsc,qty,unit_price,line_total,available}],
              material_total, priced_via: "jlcpcb-mcp" | "unpriced"}
"""
from __future__ import annotations
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def derive_bom(circuit_json_path: str) -> list[dict]:
    cj = json.load(open(circuit_json_path, encoding="utf-8"))
    src = [e for e in cj if e.get("type") == "source_component"]

    def lcsc_of(e):
        sp = e.get("supplier_part_numbers") or {}
        for k in ("jlcpcb", "jlc", "lcsc"):
            v = sp.get(k)
            if v:
                return v[0] if isinstance(v, list) else v
        m = re.search(r"C\d{4,}", json.dumps(e))
        return m.group(0) if m else ""

    items = []
    for e in src:
        items.append({
            "ref": e.get("name", ""),
            "value": e.get("display_value") or e.get("resistance")
                     or e.get("capacitance") or e.get("ftype", ""),
            "footprint": e.get("ftype", ""),
            "lcsc": lcsc_of(e),
            "qty": 1,
        })
    return items


def price_tier(tiers: list[dict], qty: int):
    """取 qty 落在的阶梯价:最大的 ladder<=qty,否则最小档。"""
    if not tiers:
        return None
    elig = [t for t in tiers if t.get("qty", t.get("ladder", 0)) <= qty]
    chosen = max(elig, key=lambda t: t.get("qty", 0)) if elig else min(
        tiers, key=lambda t: t.get("qty", 1e9))
    return chosen.get("price")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="BOM 派生 + jlcpcb-mcp 免 key 定价")
    ap.add_argument("circuit_json")
    ap.add_argument("--out")
    ap.add_argument("--board-qty", type=int, default=5)
    ap.add_argument("--timeout", type=int, default=300)
    a = ap.parse_args(argv)

    if not os.path.exists(a.circuit_json):
        print(f"✗ 找不到 {a.circuit_json};先 tsci build", file=sys.stderr)
        return 2
    out = a.out or a.circuit_json.replace(".circuit.json", "").rsplit(".", 1)[0] + ".bom.json"
    items = derive_bom(a.circuit_json)

    priced_via = "unpriced"
    try:
        from jlc_order import mcp_call
        total_qty = lambda it: it["qty"] * a.board_qty
        for it in items:
            if not it["lcsc"]:
                continue
            r = mcp_call("jlcpcb_get_component_pricing",
                         {"lcsc": it["lcsc"], "quantity": total_qty(it)}, a.timeout)
            # MCP 返回 {content:[{text: "<json string>"}]}
            txt = (r.get("content") or [{}])[0].get("text", "{}") if isinstance(r, dict) else "{}"
            data = json.loads(txt)
            up = price_tier(data.get("tiers", []), total_qty(it))
            it["unit_price"] = up
            it["available"] = data.get("available")
            it["line_total"] = round(up * total_qty(it), 4) if up is not None else None
        priced_via = "jlcpcb-mcp"
    except Exception as e:  # noqa: BLE001
        print(f"⚠ 定价降级(MCP 不可用:{e});只出 BOM 不出价", file=sys.stderr)

    material_total = None
    if priced_via == "jlcpcb-mcp":
        lts = [it.get("line_total") for it in items if it.get("line_total") is not None]
        material_total = round(sum(lts), 4) if lts else 0.0

    doc = {"currency": "USD", "board_qty": a.board_qty, "items": items,
           "material_total": material_total, "priced_via": priced_via}
    json.dump(doc, open(out, "w"), ensure_ascii=False, indent=2)
    print(f"✓ 写 {out}(priced_via={priced_via}, material_total={material_total})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
