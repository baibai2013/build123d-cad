#!/usr/bin/env bash
# new_board.sh <name|dir> — 起一个新 tscircuit 项目(入口 index.circuit.tsx)。
# 工具缺失 fail-loud。用法:bash new_board.sh my-board
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=_tsci_env.sh
source "$HERE/_tsci_env.sh"

DIR="${1:-}"
if [ -z "$DIR" ]; then echo "用法: new_board.sh <name|dir>" >&2; exit 2; fi

need_tsci
echo "→ tsci init $DIR" >&2
tsci init "$DIR" -y
echo "✓ 项目就绪:$DIR/index.circuit.tsx" >&2
echo "  下一步:写电路 → bash check_all.sh $DIR/index.circuit.tsx" >&2
