#!/usr/bin/env bash
# export_fab.sh — 一把出 fab 文件(P3-1,build123d-cad · pcb 子技能)
#
# 用法:
#   ./export_fab.sh <board>.kicad_pcb [out_dir]
#
# 产出(out_dir 默认 = 板文件同级的 fab/):
#   <board>-gerbers.zip   Gerber(全铜/丝印/阻焊层)+ 钻孔(打包)
#   <board>.step          3D(含元件,给 mechanical 装配验证)
#   <board>.glb           3D glTF(给 viewer cad 引擎预览)
#   <board>-pos.csv       贴片坐标(给贴片厂)
#   <board>-bom.csv       BOM(给贴片厂 / 成本钩子)
#
# 设计:纯 kicad-cli(命令行稳定),不碰 IPC API。kicad-cli 缺失 → fail loud
# 给安装提示,不静默(对齐 gcode/slice_precheck 约定)。DRC 不在此跑(归 drc 子技能)。
set -euo pipefail

# ── kicad-cli 检测(与 pcb_common.py 候选一致)──────────────────────────────
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

if [[ $# -lt 1 ]]; then
  echo "用法:$0 <board>.kicad_pcb [out_dir]" >&2
  exit 2
fi

PCB="$1"
if [[ ! -f "$PCB" ]]; then
  echo "✗ 找不到板文件:$PCB" >&2
  exit 1
fi

KICAD_CLI="$(find_kicad_cli)" || {
  cat >&2 <<'EOF'
✗ 未找到 kicad-cli(KiCad 9.x)。安装:
  macOS : brew install --cask kicad   (或官网 dmg https://www.kicad.org/download/)
  Linux : sudo apt install kicad
装完确认:kicad-cli version  → 应 ≥ 9.0
EOF
  exit 127
}

BOARD="$(basename "$PCB" .kicad_pcb)"
DIR="$(cd "$(dirname "$PCB")" && pwd)"
OUT="${2:-$DIR/fab}"
mkdir -p "$OUT"
GERBER_TMP="$(mktemp -d)"
trap 'rm -rf "$GERBER_TMP"' EXIT

echo "→ kicad-cli: $KICAD_CLI"
echo "→ 板:$BOARD  输出:$OUT"

# 1) Gerber + 钻孔 → 打包 zip
"$KICAD_CLI" pcb export gerbers --output "$GERBER_TMP/" "$PCB"
"$KICAD_CLI" pcb export drill   --output "$GERBER_TMP/" "$PCB"
( cd "$GERBER_TMP" && zip -q -r "$OUT/${BOARD}-gerbers.zip" . )
echo "✓ ${BOARD}-gerbers.zip"

# 2) 3D:STEP(给 mechanical)+ glTF/glb(给 viewer)
"$KICAD_CLI" pcb export step --output "$OUT/${BOARD}.step" "$PCB"
echo "✓ ${BOARD}.step"
"$KICAD_CLI" pcb export glb  --output "$OUT/${BOARD}.glb"  "$PCB" 2>/dev/null \
  || echo "⚠ glb 导出跳过(KiCad < 9.0 可能不支持 export glb;3D 仍可用 .step)"

# 3) 贴片坐标 + BOM
"$KICAD_CLI" pcb export pos --output "$OUT/${BOARD}-pos.csv" --format csv --units mm "$PCB"
echo "✓ ${BOARD}-pos.csv"
"$KICAD_CLI" sch export bom --output "$OUT/${BOARD}-bom.csv" "${DIR}/${BOARD}.kicad_sch" 2>/dev/null \
  || echo "⚠ BOM 跳过(需同名 .kicad_sch;无原理图时仅出 PCB 侧文件)"

echo "✅ fab 出件完成 → $OUT"
echo "   下一步:DRC 走 drc 子技能 run_drc.sh;预览 viewer/start.sh ${OUT}/${BOARD}.glb"
