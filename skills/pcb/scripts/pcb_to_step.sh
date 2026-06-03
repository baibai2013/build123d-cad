#!/usr/bin/env bash
# pcb_to_step.sh — 仅出 STEP(P3-1,薄包装,给 mechanical 装配验证让位)
#
# 用法:./pcb_to_step.sh <board>.kicad_pcb [out.step]
#
# 比 export_fab.sh 轻:只出一个含元件 3D 的 STEP,mechanical 在 build123d 里
# 读它做外壳间隙/装配验证。kicad-cli 缺失 → fail loud。
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

if [[ $# -lt 1 ]]; then echo "用法:$0 <board>.kicad_pcb [out.step]" >&2; exit 2; fi
PCB="$1"
[[ -f "$PCB" ]] || { echo "✗ 找不到板文件:$PCB" >&2; exit 1; }
KICAD_CLI="$(find_kicad_cli)" || { echo "✗ 未找到 kicad-cli(KiCad 9.x):brew install --cask kicad" >&2; exit 127; }

BOARD="$(basename "$PCB" .kicad_pcb)"
OUT="${2:-$(cd "$(dirname "$PCB")" && pwd)/${BOARD}.step}"
"$KICAD_CLI" pcb export step --output "$OUT" "$PCB"
echo "✓ STEP → $OUT"
