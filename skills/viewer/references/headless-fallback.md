# P1 · headless 降级链

> P1-5 任务(目标 2026-06-15)。`web_preview.snapshot()` 在没有浏览器时降级到 PNG。

## API

```python
web_preview.start(file, workspace=None, mode="web") -> URL          # P0 已实现
web_preview.snapshot(file, workspace=None, mode="auto") -> PNG path # P1-5 待实现
```

`snapshot()` 在 `mode="auto"` 下按顺序尝试三级,每级失败回落:

1. **Web Viewer + headless Chrome**(首选,1:1 一致)
   - 起 server → playwright 截图 → 关 server
   - 优:和真实预览一致;缺:chromium ≈ 300M
2. **OCP Python**(中间)
   - 飞书/CI 用现有 OCP 后端直接渲 PNG
   - 优:无浏览器;缺:仅 STEP/STL,不支持 PCB/sch/sim 后缀
3. **VTK**(兜底)
   - 纯 Python 渲染,依赖最薄
   - 缺:材质/光照粗糙

## 调用上下文

- **CI**:默认 `mode=auto`,优先级 1>2>3
- **飞书机器人**:已装 chromium → `mode=web` 拿到完整 URL(用户点开看实时);否则降级 PNG

## 实现注意(P1 落地时)

- playwright chromium 跑 headless,需 `--no-sandbox`(macOS / Linux 容器都要)
- 截图前等 `networkidle` + 关键 selector 出现(如 `canvas` ready 事件)
- OCP / VTK 走 `~/.agents/skills/build123d-cad/skills/mechanical/scripts/render.py`(假设 mechanical 已实现)

## 验收(P1 落地时)

- 装 chromium → snapshot STEP 输出 PNG ≥ 200px
- pip 卸载 playwright → snapshot 走第 2 级仍能出图
- pip 卸载 OCP → snapshot 走第 3 级 VTK 出图
- 三级全失败 → 抛 `RuntimeError` 不静默
