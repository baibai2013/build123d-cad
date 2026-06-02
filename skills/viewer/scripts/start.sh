#!/usr/bin/env bash
# viewer 启动器 — 一句话起 server,输出唯一一行 URL
#
# 用法: bash start.sh <file_path> [workspace_root]
#
# 输出 (stdout 严格机器可读,唯一一行):
#   http://127.0.0.1:<port>/?engine=<cad|pcb|sch|sim>&dir=<abs>&file=<rel>
#
# 退出码:
#   0 成功 / 2 后缀不支持或参数错 / 3 文件不存在 / 4 端口分配/启动失败 / 1 其它
#
# 设计:
# - 先 GET /__cad/server 探活 4178 / 4188-4197,找兼容 server(同 workspace + 同 git)即复用。
# - 不命中:nohup 后台启 node server.mjs,丢日志到 /tmp,主程立即返回。
# - 轮询新端口 ≤ 5s,等到健康 → 拼 URL。
# - 不依赖 server.mjs 的 stdout(避开 fd 1 close 时机问题)。

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_MJS="$SCRIPT_DIR/backend/server.mjs"
ROUTER_MJS="$SCRIPT_DIR/backend/router.mjs"

PORTS=(4178 4188 4189 4190 4191 4192 4193 4194 4195 4196 4197)
APP_NAME="build123d-cad/viewer"
LOG_DIR="${VIEWER_LOG_DIR:-/tmp/build123d-cad-viewer}"
mkdir -p "$LOG_DIR"

usage() {
  echo "usage: bash start.sh <file_path> [workspace_root]" >&2
  exit 2
}

[[ $# -ge 1 ]] || usage
FILE_PATH="$1"
WORKSPACE_ROOT="${2:-}"

[[ -e "$FILE_PATH" ]] || { echo "error: file not found: $FILE_PATH" >&2; exit 3; }

FILE_PATH="$(cd "$(dirname "$FILE_PATH")" && pwd)/$(basename "$FILE_PATH")"

if [[ -z "$WORKSPACE_ROOT" ]]; then
  if WORKSPACE_ROOT="$(cd "$(dirname "$FILE_PATH")" && git rev-parse --show-toplevel 2>/dev/null)"; then
    :
  else
    WORKSPACE_ROOT="$(dirname "$FILE_PATH")"
  fi
fi
WORKSPACE_ROOT="$(cd "$WORKSPACE_ROOT" && pwd)"

case "$FILE_PATH" in
  "$WORKSPACE_ROOT"/*|"$WORKSPACE_ROOT") : ;;
  *) echo "error: file ($FILE_PATH) must be inside workspace_root ($WORKSPACE_ROOT)" >&2; exit 2 ;;
esac

ENGINE="$(node --input-type=module -e "
import { routeByExtension } from '$ROUTER_MJS';
const r = routeByExtension('$FILE_PATH');
process.stdout.write(r || '');
")"
[[ -n "$ENGINE" ]] || { echo "error: unsupported extension for $FILE_PATH" >&2; exit 2; }

# git ID(用于复用判定)
GIT_DIR="$(git -C "$WORKSPACE_ROOT" rev-parse --git-dir 2>/dev/null || echo '')"
if [[ -n "$GIT_DIR" ]]; then
  GIT_DIR="$(cd "$WORKSPACE_ROOT" && cd "$GIT_DIR" && pwd)"
  GIT_BRANCH="$(git -C "$WORKSPACE_ROOT" rev-parse --abbrev-ref HEAD 2>/dev/null || echo '')"
  MY_GIT="${GIT_DIR}:${GIT_BRANCH}"
else
  MY_GIT=""
fi

# 探活兼容判定 — 命中返回 0
probe_compat() {
  local port="$1"
  local body
  body="$(curl -s --max-time 1 "http://127.0.0.1:${port}/__cad/server" 2>/dev/null || true)"
  [[ -z "$body" ]] && return 1
  WORKSPACE_ROOT="$WORKSPACE_ROOT" MY_GIT="$MY_GIT" APP_NAME="$APP_NAME" \
  node --input-type=module -e "
let s = ''; for await (const c of process.stdin) s += c;
let h; try { h = JSON.parse(s); } catch { process.exit(2); }
const APP = process.env.APP_NAME;
const WS = process.env.WORKSPACE_ROOT;
const MY = process.env.MY_GIT || '';
if (typeof h.app !== 'string' || !h.app.startsWith(APP)) process.exit(2);
if ((h.serverApiVersion ?? 0) < 2) process.exit(2);
const path = await import('node:path');
if (path.resolve(h.workspaceRoot || '') !== path.resolve(WS)) process.exit(2);
if (h.git && MY && h.git !== MY) process.exit(2);
process.exit(0);
" <<<"$body" >/dev/null 2>&1
}

emit_url() {
  local port="$1"
  local dir="$(dirname "$FILE_PATH")"
  local file_rel="$(basename "$FILE_PATH")"
  local url_dir url_file
  url_dir="$(node -e 'process.stdout.write(encodeURIComponent(process.argv[1]))' "$dir")"
  url_file="$(node -e 'process.stdout.write(encodeURIComponent(process.argv[1]))' "$file_rel")"
  echo "http://127.0.0.1:${port}/?engine=${ENGINE}&dir=${url_dir}&file=${url_file}"
}

# 1) 找兼容 server
for p in "${PORTS[@]}"; do
  if probe_compat "$p"; then emit_url "$p"; exit 0; fi
done

# 2) 后台起一个新 server
WS_HASH="$(echo -n "$WORKSPACE_ROOT" | (md5sum 2>/dev/null || md5) | awk '{print $1}' | head -c 8)"
LOG_FILE="$LOG_DIR/server-${WS_HASH}.log"
nohup node "$SERVER_MJS" --workspace-root "$WORKSPACE_ROOT" >"$LOG_FILE" 2>&1 &
disown

# 3) 轮询 ≤ 5s
for _ in $(seq 1 50); do
  for p in "${PORTS[@]}"; do
    if probe_compat "$p"; then emit_url "$p"; exit 0; fi
  done
  sleep 0.1
done

echo "error: server failed to come up in 5s, see $LOG_FILE" >&2
exit 4
