# Server 复用规则

> 一个 workspace 同一时刻最多一个 viewer server。第二次 `start.sh` 命中已起 server 直接返回 URL,
> 不再开新端口。复用判定沿用 [earthtojake/cad-viewer](https://github.com/earthtojake/cad-viewer) v2 协议 + 加引擎字段。

## 端口分配顺序

1. **4178**(沿用 cad-viewer 默认)
2. 4188 → 4189 → ... → 4197(共 10 个 fallback)
3. 全占且不兼容 → 退出码 4

(若本机已有外部 cad-viewer 占 4178,本 server 自动跳到 4188)

## 复用判定

`GET /__cad/server` 返回的 JSON 必须满足:

| 字段 | 要求 |
|---|---|
| `app` | 以 `build123d-cad/viewer` 起头 |
| `serverApiVersion` | `>= 2` |
| `workspaceRoot` | `path.resolve()` 后与 `--workspace-root` 严格相等 |
| `git` | 双方都有时必须相等(任一为空跳过此条) |

任一不符 → 该端口不复用,继续下一个候选。

## 探活流程(在 start.sh)

```bash
for p in 4178 4188 4189 ... 4197; do
  body="$(curl -s --max-time 1 http://127.0.0.1:$p/__cad/server)"
  [[ -n "$body" ]] && compatible_check "$body" && reuse_port=$p && break
done

if [[ -z "$reuse_port" ]]; then
  nohup node server.mjs --workspace-root <ws> >/tmp/.../server-<hash>.log 2>&1 &
  # 轮询 5s 等新 server 上来,从 health 拿端口
fi
```

## 不复用的几种场景

- **同 workspace,不同 git branch**:`git` 字段不同 → 不复用,新起。这是为了避免 branch 切换后 viewer 继续 serve 旧 branch 的文件(脏读)。
- **同路径但不同 git 仓库**(罕见):同上,`git.gitdir` 不同。
- **外部 cad-viewer 占用**:`app="cad-viewer"` 不以 `build123d-cad/viewer` 起头 → 不复用,跳到下一个端口。

## shutdown 策略

- **被动超时**:默认 `--shutdown-after 12h`,每收到一次请求重置定时器(活跃续命)。
- **主动**:`POST /__cad/shutdown`(仅 127.0.0.1)→ 200 后优雅关停,等在飞请求 ≤ 5s。
- **信号**:SIGINT / SIGTERM 同上。

## 调试

- 看 `${VIEWER_LOG_DIR:-/tmp/build123d-cad-viewer}/server-<hash>.log` 里的 stderr。
- `lsof -nP -iTCP -sTCP:LISTEN | grep -E "417|418|419"` 看实际占用。
- `curl -s http://127.0.0.1:<port>/__cad/server | jq` 看健康状态。
