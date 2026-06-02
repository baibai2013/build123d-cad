# cad engine 集成

> P0 的"实跑"引擎。从 [earthtojake/cad-viewer](https://github.com/earthtojake/cad-viewer) 复刻,
> Three.js + 各 loader 客户端渲染,服务端只 serve 静态文件 + 文件代理。

## 复刻产物

- `engines/cad/dist/` — 13M 前端 SPA(Vite 打包,vanilla JS + WASM,无需 npm install)
  - `index.html` — 入口
  - `assets/index-*.js` — 主程序
  - `assets/three.module-*.js` — Three.js
  - `assets/STLLoader-*.js` `GLTFLoader-*.js` — 加载器
  - `assets/parseUrdf-*.js` `parseSrdf-*.js` `parseSdf-*.js` — robotics
  - `assets/glbMeshWorker-*.js` `stlMeshWorker-*.js` — Worker mesh 处理
- `engines/cad/backend/server.mjs` — cad-viewer 原 server(1MB bundled,提供 `/__cad/catalog` `/__cad/asset` `/__cad/step-artifact` `/__cad/download` 等 SPA 启动核心 API)。**父 server 把它 spawn 为子进程并反代请求**(见下文)。日后 dist 升级时同步从 cad-viewer 重新 cp 一份。

## 父 server 与 cad backend 的边界(spawn + 反代架构)

父 server 启动时:
1. 在 5178-5297 找一个空闲内部端口 P_internal
2. `spawn('node', [cad/backend/server.mjs, '--host', host, '--port', P_internal])`
3. 轮询 cad backend 的 `/__cad/server` 直到 ready(≤ 10s)
4. 父 server 自己 listen 在外部端口(4178/4188-4197)

请求到达父 server 后的分发顺序:

| 优先级 | 路径 | 行为 |
|---|---|---|
| (1) | `/__cad/server` GET | **父 server 自管**(覆盖 cad backend 同名响应,保 `app="build123d-cad/viewer"` 字段稳定让 start.sh 可正确判定复用) |
| (1) | `/__cad/shutdown` POST | **父 server 自管**(关掉 cad child + 自己 exit) |
| (2) | `/` `/index.html` 带 `?engine=<unknown>` | 父 server 直接 400(枚举校验) |
| (2) | `/` `/index.html` 带 `?engine=<pcb\|sch\|sim>` | 走静态占位,**不**反代 |
| (3) | `/files/*` | 父 server **自管**(后缀白名单 + 路径穿越 + dir 越界) |
| (4) | 其它一切 | **反代到 cad backend 子进程**:`/` 和 `/index.html`(无 `?engine=` 或 `?engine=cad`)、`/assets/*`、`/__cad/catalog`、`/__cad/asset`、`/favicon.ico` 等 |
| (5) | cad backend 没起来时兜底 | 静态从 `engines/cad/dist/` 直接 serve(只能加载 SPA,不能调内部 API) |

为什么这么设计:
- **完整功能** — cad SPA 启动需要 `/__cad/catalog` 等内部 API,光静态 serve dist 不够(以前的设计漏了这步,实测 SPA 跑不起来)
- **健康协议唯一**:父 server 必须自管 `/__cad/server`,否则反代会让 `app` 字段变成 cad-viewer 自己的,start.sh 复用判定失效
- **安全边界唯一**:`/files/*` 父 server 自管(白名单 + 穿越),不让 cad backend 的内部文件代理逻辑泄漏
- **stub engine 不被吞**:pcb/sch/sim 的 `?engine=` 入口必须在反代前拦截,否则被 cad SPA 接管
- **未知 engine 直接 400**:在反代前枚举校验,避免被 cad SPA 吃掉变 200

## URL 给前端

```
http://127.0.0.1:<port>/?engine=cad&dir=<abs>&file=<rel>[#frame=...&joint=...]
```

cad SPA 启动时:
1. 读 `?engine=cad`(否则不进 cad 模式)
2. 读 `?dir=` `?file=`,内部拼成 `/files/<rel>?dir=<abs>` 走父 server 文件代理拿 STEP/STL bytes
3. hash(`#`)由 cad SPA 自管 — 关节状态 / 摄像机角度等 deep-link

## 升级流程

```bash
# cad-viewer 升级到新版后(假设已 pull 到 ~/.agents/skills/cad-viewer/)
cp -R ~/.agents/skills/cad-viewer/scripts/viewer/{backend,dist} \
      ~/.agents/skills/build123d-cad/skills/viewer/scripts/engines/cad/
cd ~/.agents/skills/build123d-cad/skills/viewer
pytest tests/test_cad_engine.py -v   # 验证 dist 资产 + assets 加载
```

## 不在 cad engine 范围

- ❌ PCB 3D(走 pcb engine 调 `kicad-cli pcb export gltf` 出 GLB,再透到 cad)
- ❌ 实时仿真轨迹(走 sim engine,P3)
- ❌ FEA 应力云图(P4+)

## 头痛 / 已知问题

- cad SPA 的 `index.html` 引用绝对路径 `/assets/...`,因此父 server 的 `/assets/*` 路由 **P0 默认走 cad**。P3 真 pcb engine 落地时,要么改 dist 用相对路径,要么 server 端按 Referer 推断 engine。
