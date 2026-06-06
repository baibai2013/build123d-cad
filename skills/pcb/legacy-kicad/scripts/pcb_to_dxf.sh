#!/usr/bin/env bash
# pcb_to_dxf.sh — 仅出板框 DXF(P3-1,给 mechanical 外壳挖孔让位)
#
# 用法:./pcb_to_dxf.sh <board>.kicad_pcb [out.dxf]
#
# 只导 Edge.Cuts 层(板边轮廓)成 DXF,mechanical 在 build123d 里读它做
# 外壳让位/挖孔。kicad-cli 缺失 → fail loud。
set -euo pipefail

find_kicad_cli() {
  local cands=(
    "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
    "kicad-cli" "kicad-cli-9.0" "/usr/bin/kicad-cli" "/usr/local/bin/kicad-cli"
  )
  for c in "${cands[@]}"; do
    if [[ "$c" == /* && -x "$c" ]]; then echo "$c"; return 0; fi
    if command -v "$c" >/dev/null 2>&1; then command -v "$c"; return 0; fi
  done
  return 1
}

if [[ $# -lt 1 ]]; then echo "用法:$0 <board>.kicad_pcb [out.dxf]" >&2; exit 2; fi
PCB="$1"
[[ -f "$PCB" ]] || { echo "✗ 找不到板文件:$PCB" >&2; exit 1; }
KICAD_CLI="$(find_kicad_cli)" || { echo "✗ 未找到 kicad-cli(KiCad 9.x):brew install --cask kicad" >&2; exit 127; }

BOARD="$(basename "$PCB" .kicad_pcb)"
OUTDIR="$(cd "$(dirname "$PCB")" && pwd)"
OUT="${2:-$OUTDIR/${BOARD}.dxf}"
# 只导板框层;--output 对 dxf 是目录,导出后取板框文件改名到 OUT。
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
"$KICAD_CLI" pcb export dxf --layers "Edge.Cuts" --output "$TMP/" "$PCB"
# kicad-cli 按层命名,板框层文件名含 Edge_Cuts;取第一个 dxf。
SRC="$(find "$TMP" -name '*.dxf' | head -1)"
[[ -n "$SRC" ]] || { echo "✗ 未生成 DXF(检查板是否有 Edge.Cuts 板框)" >&2; exit 1; }
cp "$SRC" "$OUT"
echo "✓ 板框 DXF → $OUT(交 mechanical 做外壳让位)"
