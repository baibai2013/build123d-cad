# viewer — 开发者说明

## 目录结构

```
skills/viewer/
├── SKILL.md                       # 给 Claude 看的入口(用法 + 路由表 + URL 协议)
├── README.md                      # 本文(给开发者:怎么加新引擎/调试)
├── references/                    # 设计/协议参考(高扇入)
│   ├── url-protocol.md            # URL 协议字段约束(对外稳定接口)
│   ├── routing.md                 # 后缀 → 引擎 映射表(扩展核心)
│   ├── server-reuse.md            # 端口 / pid / git / workspace 复用规则
│   ├── cad-engine.md              # cad engine 集成细节
│   ├── headless-fallback.md       # P1:headless 降级链
│   ├── viewer-features.md         # 关节滑块 / 截面 / 测量(P3 补)
│   ├── moveit2-server.md          # 机器人规划集成(从 cad-viewer 复刻)
│   ├── pcb-engine.md              # P3:tracespace + KiCad GLTF
│   ├── sch-engine.md              # P3:KiCanvas
│   └── sim-engine.md              # P3:plotly + URDF playback
├── scripts/
│   ├── backend/
│   │   ├── server.mjs             # 父 HTTP server(5 endpoint + 端口探活复用)
│   │   └── router.mjs             # 后缀 → 引擎 纯函数(可单测,零依赖)
│   ├── engines/
│   │   ├── cad/                   # ✅ Three.js SPA(从 ~/.agents/skills/cad-viewer 复刻)
│   │   │   ├── backend/server.mjs # cad-viewer 原 server(父 server spawn 为子进程,反代 SPA 内部 API)
│   │   │   └── dist/              # 13M 前端打包产物(SPA,直接 commit)
│   │   ├── pcb/index.html         # ⏳ P3 占位(纯 HTML + 内嵌 CSS,≤ 50 行)
│   │   ├── sch/index.html         # ⏳ P3 占位
│   │   └── sim/index.html         # ⏳ P3 占位
│   ├── package.json               # type:module,无 npm install
│   ├── start.sh                   # 父级 wrapper,与引擎无关
│   └── web_preview.py             # Python launcher(飞书/CI 调用入口)
└── tests/
    ├── conftest.py                # session 级 fixture:workspace_dir / server
    ├── test_routing.py            # 后缀路由(纯函数,无 server)
    ├── test_url_assembly.py       # URL 拼装编码(空格/中文/?#&)
    ├── test_placeholders.py       # pcb/sch/sim 占位页 200 + "待实现"
    ├── test_start.py              # bash start.sh 端到端
    ├── test_server_reuse.py       # 同 workspace 复用 / 不同 workspace 新起
    ├── test_cad_engine.py         # cad SPA + assets 加载(headless 截图归 P1-5)
    └── test_{pcb,sch,sim}_engine.py # P3 占位(pytest.skip)
```

## 添加新引擎(P3 加 pcb/sch/sim 时怎么填)

1. 在 `scripts/backend/router.mjs` 的 `ENGINE_ROUTES` 加一行(把后缀映到引擎名)。
2. 把前端打包产物放到 `scripts/engines/<name>/dist/`(必须有 `index.html`)。
   - 如果是纯 HTML 占位(无 SPA),放 `scripts/engines/<name>/index.html` 即可。
3. 在 `scripts/backend/server.mjs` 的 `/assets/*` 路由策略可能需要调整(P0 只有 cad SPA,默认走 cad)。
4. 把 `tests/test_<name>_engine.py` 的 `pytest.skip` 改成真测试。
5. 更新 `SKILL.md` / `README.md` / `references/<name>-engine.md`。
6. 在 `shared/dependencies.md` 登记本次后缀路由变更(@全员)。

## 调试

- **server 起不来**:看 `${VIEWER_LOG_DIR:-/tmp/build123d-cad-viewer}/server-<hash>.log` 里的 stderr。
- **复用未命中**:GET `/__cad/server` 看 `workspaceRoot` 和 `git` 是否真匹配。
- **路径穿越被挡 / 文件代理 415**:看 `references/url-protocol.md` §安全约束。

## 升级 cad engine

cad SPA 来自 [earthtojake/cad-viewer](https://github.com/earthtojake/cad-viewer)。升级流程:

```bash
# 假设新版本已落到 ~/.agents/skills/cad-viewer/
cp -R ~/.agents/skills/cad-viewer/scripts/viewer/{backend,dist} \
      skills/viewer/scripts/engines/cad/
# 验证:
cd skills/viewer && pytest tests/test_cad_engine.py -v
```

## dist 大小红线

当 `engines/*/dist/` 总和 > 80M 或 `.git/` > 200M 时,重启评审是否转 LFS(规格 §11)。
