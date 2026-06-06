#!/usr/bin/env bash
# 共享:定位 tsci(依赖 bun)。缺失则 fail-loud 给安装提示并退出。
# 用法:source "$(dirname "$0")/_tsci_env.sh" ; need_tsci
set -euo pipefail

need_tsci() {
  # bun 常装在 ~/.bun/bin;把它纳入 PATH
  if [ -d "$HOME/.bun/bin" ]; then export PATH="$HOME/.bun/bin:$PATH"; fi
  if ! command -v bun >/dev/null 2>&1; then
    cat >&2 <<'EOF'
✗ 缺 bun 运行时(tscircuit 依赖)。安装:
    curl -fsSL https://bun.sh/install | bash
EOF
    exit 3
  fi
  if ! command -v tsci >/dev/null 2>&1; then
    cat >&2 <<'EOF'
✗ 缺 tsci(tscircuit CLI)。安装(务必用 bun 装,Rosetta 机用 npm 会原生库架构不匹配):
    bun add -g tscircuit
EOF
    exit 3
  fi
}
