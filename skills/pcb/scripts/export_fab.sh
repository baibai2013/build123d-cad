#!/usr/bin/env bash
# export_fab.sh <entry> [task] — 一键出件。
#   build + 导出 gerbers/step/glb/pcb-svg/schematic-svg,并从 circuit.json 派生 BOM/CPL,
#   全落 output/<task>/electrical/{fab,3d,preview}/。
# entry 默认 index.circuit.tsx;task 默认取 entry 所在目录名。
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=_tsci_env.sh
source "$HERE/_tsci_env.sh"

ENTRY="${1:-index.circuit.tsx}"
[ -f "$ENTRY" ] || { echo "✗ 找不到 entry: $ENTRY" >&2; exit 2; }
STEM="$(basename "$ENTRY")"; STEM="${STEM%.circuit.tsx}"; STEM="${STEM%.tsx}"
TASK="${2:-$(basename "$(cd "$(dirname "$ENTRY")" && pwd)")}"
BOARD="$TASK"

OUT="output/$TASK/electrical"
mkdir -p "$OUT/fab" "$OUT/3d" "$OUT/preview"
need_tsci

echo "== build(含 DRC)==" >&2
tsci build "$ENTRY"
CJSON="dist/$STEM/circuit.json"
[ -f "$CJSON" ] || CJSON="$(find dist -name circuit.json | head -1)"

echo "== 导出各格式 → $OUT ==" >&2
tsci export "$ENTRY" -f gerbers       -o "$OUT/fab/$BOARD-gerbers.zip"
tsci export "$ENTRY" -f step          -o "$OUT/3d/$BOARD.step"
tsci export "$ENTRY" -f glb           -o "$OUT/3d/$BOARD.glb"
tsci export "$ENTRY" -f pcb-svg       -o "$OUT/preview/$BOARD.pcb.svg"
tsci export "$ENTRY" -f schematic-svg -o "$OUT/preview/$BOARD.schematic.svg"

echo "== 从 circuit.json 派生 BOM/CPL(无独立导出格式)==" >&2
python3 "$HERE/dfm_check.py" "$CJSON" || echo "(DFM 有问题,见上;出件继续,但下单前须修)" >&2
BOARD="$BOARD" OUT="$OUT" CJSON="$CJSON" python3 - <<'PY'
import csv, json, os, re
cj = json.load(open(os.environ["CJSON"], encoding="utf-8"))
out, board = os.environ["OUT"], os.environ["BOARD"]
by = lambda t: [e for e in cj if e.get("type") == t]

src = {e["source_component_id"]: e for e in by("source_component") if "source_component_id" in e}

def jlc(e):
    sp = e.get("supplier_part_numbers") or {}
    for k in ("jlcpcb", "jlc", "lcsc"):
        if sp.get(k):
            return sp[k][0] if isinstance(sp[k], list) else sp[k]
    m = re.search(r"C\d{4,}", json.dumps(e))
    return m.group(0) if m else ""

# BOM:每个 source_component 一行
with open(f"{out}/fab/{board}-bom.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["Designator", "Comment", "Footprint", "LCSC"])
    for e in src.values():
        val = e.get("display_value") or e.get("resistance") or e.get("capacitance") or e.get("ftype", "")
        w.writerow([e.get("name", ""), val, e.get("ftype", ""), jlc(e)])

# CPL(pick&place):每个 pcb_component 一行(位置/角度/层)
with open(f"{out}/fab/{board}-cpl.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["Designator", "Mid X", "Mid Y", "Rotation", "Layer"])
    for p in by("pcb_component"):
        c = p.get("center", {}); s = src.get(p.get("source_component_id"), {})
        w.writerow([s.get("name", ""), c.get("x", ""), c.get("y", ""),
                    p.get("rotation", 0), p.get("layer", "top")])
print(f"✓ BOM/CPL 派生完成:{out}/fab/{board}-bom.csv / -cpl.csv")
PY

echo "== 统一预览产物(circuit.json + BOM 报价 sidecar)==" >&2
cp "$CJSON" "$OUT/$BOARD.circuit.json"
python3 "$HERE/bom_price.py" "$CJSON" --out "$OUT/$BOARD.bom.json" --board-qty "${QTY:-5}" \
  || echo "(BOM 定价降级:见上;预览仍可看,只是无价)" >&2

echo "✓ 出件完成 → $OUT" >&2
echo "  fab/$BOARD-gerbers.zip  fab/$BOARD-bom.csv  fab/$BOARD-cpl.csv" >&2
echo "  3d/$BOARD.{step,glb}    preview/$BOARD.{pcb,schematic}.svg" >&2
echo "  $BOARD.circuit.json + $BOARD.bom.json(统一预览用)" >&2
echo "  统一预览(PCB+原理图+3D+BOM/总价):" >&2
echo "    bash ../viewer/scripts/start.sh $OUT/$BOARD.circuit.json" >&2
echo "  报价/下单:python3 $HERE/jlc_order.py $OUT/fab/$BOARD-gerbers.zip" >&2
