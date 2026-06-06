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
  echo "usage: bash start.sh <file_path> [workspace_root] [--trajectory <rel_file>]" >&2
  echo "  --trajectory: 仿真 3D 回放——cad 引擎加载 URDF 后按该轨迹文件(同 dir 下相对名)自动回放" >&2
  exit 2
}

[[ $# -ge 1 ]] || usage
FILE_PATH="$1"
WORKSPACE_ROOT=""
TRAJECTORY=""
shift
while [[ $# -gt 0 ]]; do
  case "$1" in
    --trajectory) TRAJECTORY="${2:-}"; shift 2 ;;
    *) [[ -z "$WORKSPACE_ROOT" ]] && WORKSPACE_ROOT="$1"; shift ;;
  esac
done

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

# 1.5) cad 引擎 + STEP 源:确保 GLB 预览 sidecar 就位。
# cad 引擎渲染读隐藏 sidecar `.<name>.step.glb`(正常由 cadpy 生成);项目 venv 没装
# cadpy 时,用 build123d 自带 export_gltf 兜底生成,否则前端会 404。
# 找不到 build123d → 自动装进【隔离专用 venv】(绝不碰 company 生产 venv,见内存约定)。
# 关 VIEWER_AUTO_INSTALL=0 可禁用自动安装。日志全走 stderr,保持 stdout 唯一一行 URL。
VIEWER_CAD_VENV="${VIEWER_CAD_VENV:-$HOME/.cache/build123d-cad/viewer-venv}"

_find_build123d_py() {
  local cand
  for cand in "${VIEWER_PY:-}" "$VIEWER_CAD_VENV/bin/python" python3 python; do
    [[ -n "$cand" ]] || continue
    if command -v "$cand" >/dev/null 2>&1 && "$cand" -c "import build123d" >/dev/null 2>&1; then
      printf '%s' "$cand"; return 0
    fi
  done
  return 1
}

_provision_build123d_py() {
  # 「自动添加」:找不到库 → 在隔离 venv 装 build123d。一次性,后续复用。
  [[ "${VIEWER_AUTO_INSTALL:-1}" != "0" ]] || { echo "warn: VIEWER_AUTO_INSTALL=0,跳过自动安装" >&2; return 1; }
  local base_py
  base_py="$(command -v python3 || command -v python || true)"
  [[ -n "$base_py" ]] || { echo "warn: 无 python3,无法自动装 build123d" >&2; return 1; }
  echo "info: 未找到带 build123d 的 python → 自动安装到隔离 venv(一次性,体积较大)" >&2
  echo "info: venv=$VIEWER_CAD_VENV (隔离,不碰 company 生产 venv)" >&2
  if [[ ! -x "$VIEWER_CAD_VENV/bin/python" ]]; then
    "$base_py" -m venv "$VIEWER_CAD_VENV" >&2 2>&1 || { echo "warn: venv 创建失败" >&2; return 1; }
  fi
  "$VIEWER_CAD_VENV/bin/python" -m pip install -q --upgrade pip >&2 2>&1 || true
  if "$VIEWER_CAD_VENV/bin/python" -m pip install -q build123d >&2 2>&1 \
     && "$VIEWER_CAD_VENV/bin/python" -c "import build123d" >/dev/null 2>&1; then
    printf '%s' "$VIEWER_CAD_VENV/bin/python"; return 0
  fi
  echo "warn: build123d 自动安装失败(网络?)" >&2; return 1
}

ensure_step_sidecar() {
  local src="$1" ext_lc dir base sidecar py
  ext_lc="$(printf '%s' "${src##*.}" | tr '[:upper:]' '[:lower:]')"
  [[ "$ENGINE" == "cad" && ( "$ext_lc" == "step" || "$ext_lc" == "stp" ) ]] || return 0
  dir="$(dirname "$src")"; base="$(basename "$src")"
  sidecar="$dir/.${base}.glb"
  [[ -f "$sidecar" ]] && return 0          # cadpy 或上次已生成,不重复
  py="$(_find_build123d_py || true)"
  [[ -z "$py" ]] && py="$(_provision_build123d_py || true)"
  if [[ -z "${py:-}" ]]; then
    echo "warn: 缺 GLB 预览 sidecar 且无可用 build123d;cad 引擎可能 404" >&2
    return 0
  fi
  echo "info: 生成 GLB 预览 sidecar via $py export_gltf …" >&2
  if "$py" - "$src" "$sidecar" >&2 2>&1 <<'PY'
import sys
from build123d import import_step, export_gltf
src, out = sys.argv[1], sys.argv[2]
export_gltf(import_step(src), out, binary=True)
PY
  then
    echo "info: sidecar 就位 $sidecar" >&2
  else
    rm -f "$sidecar"   # 半成品清掉,避免坏文件
    echo "warn: sidecar 生成失败;cad 引擎可能 404" >&2
  fi
}
ensure_step_sidecar "$FILE_PATH"

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
  local traj_qs=""
  if [[ -n "$TRAJECTORY" ]]; then
    local url_traj
    url_traj="$(node -e 'process.stdout.write(encodeURIComponent(process.argv[1]))' "$TRAJECTORY")"
    traj_qs="&trajectory=${url_traj}"
  fi
  echo "http://127.0.0.1:${port}/?engine=${ENGINE}&dir=${url_dir}&file=${url_file}${traj_qs}"
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
