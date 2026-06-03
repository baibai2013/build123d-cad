#!/usr/bin/env bash
# vendor_assets.sh — 拉 pcb 引擎前端 bundle(KiCanvas + tracespace)进本目录。
#
# 项目红线:不 npm install,预构建 vendoring(00 §6)。本脚本用 curl 拉预构建 ESM。
# 联网失败不致命 —— index.html 会降级为「未 vendoring」提示页。
#
# 用法:bash vendor_assets.sh
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"

# 版本锁定(升级时改这里,保持可复现)。
KICANVAS_VER="0.0.5"
KICANVAS_URL="https://cdn.jsdelivr.net/npm/kicanvas@${KICANVAS_VER}/dist/kicanvas.js"
# tracespace view 的预构建 ESM(@tracespace/view UMD/ESM bundle)。
TRACESPACE_VER="5.0.0"
TRACESPACE_URL="https://cdn.jsdelivr.net/npm/@tracespace/view@${TRACESPACE_VER}/dist/tracespace-view.mjs"

fetch() {  # fetch <url> <dest>
  local url="$1" dest="$2"
  echo "→ $url"
  if curl -fsSL "$url" -o "$dest"; then
    echo "✓ $(basename "$dest")  ($(wc -c <"$dest") bytes)"
  else
    echo "⚠ 拉取失败:$url(网络/版本?)。引擎将降级提示,不阻塞。" >&2
    rm -f "$dest"
    return 1
  fi
}

rc=0
fetch "$KICANVAS_URL"   "$HERE/kicanvas.js"   || rc=1
fetch "$TRACESPACE_URL" "$HERE/tracespace.js" || rc=1

if [[ $rc -eq 0 ]]; then
  echo "✅ vendoring 完成。可把 index.html + vendor/ 提升到 engines/pcb/dist/ 标 ready(见 README.md)。"
else
  echo "部分 bundle 未就位;先解决网络/版本再重跑。" >&2
fi
exit $rc
