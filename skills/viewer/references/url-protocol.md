# URL 协议(高扇入接口)

> viewer 对外的稳定接口。所有上游子技能(mechanical / urdf / gcode / sendcutsend)只产文件路径,
> URL 拼装由 `start.sh` / `web_preview.py` 统一生成,上游不直接拼。

## 完整 URL 形式

```
http://127.0.0.1:<port>/?engine=<cad|pcb|sch|sim>&dir=<abs-dir>&file=<rel-file>
```

## 字段约束

| 字段 | 必填 | 类型 | 约束 |
|---|---|---|---|
| `engine` | ✅ | 枚举 | `cad` / `pcb` / `sch` / `sim` 4 选 1。其它返回 400 |
| `dir`    | ✅ | 绝对路径(URL-encoded) | 必须是 `--workspace-root` 子路径或就是 workspace-root 本身。否则 403 |
| `file`   | ✅ | 相对路径(URL-encoded) | 相对 `dir`,可含子目录(`meshes/foo.stl`)。`path.resolve(dir, file)` 后必须仍在 `dir` 内,否则 403 |
| 哈希参数 | ⛔ | hash(`#`)由前端自管 | 例:`#frame=base_link&joint=hip:0.5` 由 cad engine 自管,不在 server 协议层 |

## 编码

- `dir` / `file` 使用 `encodeURIComponent` 编码,空格→`%20`,`?`→`%3F`,`&`→`%26`,`#`→`%23`
- 中文/UTF-8 直接 encode

## 路由(server 端)

父 server 起 cad backend 子进程后,按以下优先级分发:

| 优先级 | Path | Method | 行为 |
|---|---|---|---|
| 1 | `/__cad/server` | GET | 父 server 自管(覆盖 cad backend 同名,保 app 字段稳定) |
| 1 | `/__cad/shutdown` | POST | 父 server 自管,优雅关停(仅 127.0.0.1) |
| 2 | `/` `/index.html` + `?engine=<unknown>` | GET | 父 server 直接 400(枚举校验) |
| 2 | `/` `/index.html` + `?engine=<pcb\|sch\|sim>` | GET | 走 `engines/<name>/index.html` 静态占位,**不**反代 |
| 3 | `/files/*` | GET | 父 server 文件代理:`?dir=` 根读 `<rel>`,路径在 dir 内,白名单后缀 |
| 4 | 其它一切 | * | **反代到 cad backend 子进程**:`/`(`?engine=cad` 或无)、`/index.html`、`/assets/*`、`/__cad/catalog`、`/__cad/asset`、`/__cad/step-artifact`、`/__cad/download`、`/favicon.ico` 等 |
| 5 | cad backend 没起 | * | 兜底从 `engines/cad/dist/` 静态 serve(只能加载 SPA 不能调 API) |

## /__cad/server 响应 schema(serverApiVersion=2 + engines)

```json
{
  "schemaVersion": 1,
  "serverApiVersion": 2,
  "app": "build123d-cad/viewer",
  "engines": ["cad", "pcb", "sch", "sim"],
  "engineImpl": { "cad": "ready", "pcb": "stub", "sch": "stub", "sim": "stub" },
  "viewerVersion": "<git short sha 或 'unknown'>",
  "git": "<gitdir>:<branch> 或 ''",
  "workspaceRoot": "/abs/path",
  "port": 4178,
  "host": "127.0.0.1",
  "pid": 12345,
  "dynamicRoot": true,
  "url": "http://127.0.0.1:4178"
}
```

`engineImpl[<name>]` 取值:
- `ready` — `engines/<name>/dist/index.html` 存在(完整 SPA)
- `stub`  — `engines/<name>/index.html` 存在(占位 HTML)
- `missing` — 都没有(不应出现于已发布版本)

## 安全约束

1. **dir 越界**:`?dir` 必须是 `--workspace-root` 的子路径或本身,否则 403
2. **path 穿越**:`?file` 经 `path.resolve(dir, file)` 后必须仍在 `dir` 内,否则 403
3. **白名单后缀**:文件代理仅放过路由表所有后缀 + `.json/.yaml/.yml`(urdf 配套),其它 415
4. **绑定地址**:仅监听 `127.0.0.1`,不绑公网;远程访问走 SSH 隧道或 ngrok
5. **shutdown 限制**:`POST /__cad/shutdown` 仅接受 127.0.0.1 / ::1 来源

## 退出码契约(start.sh)

| 退出码 | 含义 |
|---|---|
| 0 | 成功,stdout 唯一一行 URL |
| 1 | 其它错误 |
| 2 | 后缀不支持 / 参数错 |
| 3 | 文件不存在 |
| 4 | 端口分配失败(4178 + 4188-4197 全占且不兼容) |

## 改动须知(高扇入提示)

本协议被 mechanical / urdf / gcode / sendcutsend / 飞书机器人 / CI 全部消费。
任何字段约束改动都必须:
1. 在本文同步
2. 在 `shared/dependencies.md` 登记
3. @全员
4. 提升 `serverApiVersion`(避免与老 cad-viewer / 旧版自我复用错位)
