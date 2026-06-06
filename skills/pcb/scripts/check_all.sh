#!/usr/bin/env bash
# check_all.sh [entry] — 校验闭环:tsci check 预检 + tsci build(权威 DRC)。
# entry 默认 index.circuit.tsx。出件前应不带豁免跑一遍干净。
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=_tsci_env.sh
source "$HERE/_tsci_env.sh"

ENTRY="${1:-index.circuit.tsx}"
need_tsci

echo "== tsci check(预检,官方 under-dev,失败不致命)==" >&2
for stage in netlist placement routing; do
  echo "--- check $stage ---" >&2
  tsci check "$stage" "$ENTRY" 2>&1 || echo "(check $stage 预检未通过/未实现,继续)" >&2
done

echo "== tsci build(默认跑 DRC,权威)==" >&2
# 出件前的 check:不带 --ignore-*-drc,DRC 错 → exit 1
tsci build "$ENTRY"
echo "✓ build 通过(DRC 干净)。circuit.json 在 dist/<entry>/circuit.json" >&2
