# P1-5 · headless 降级链(已落地)

> 状态:**已实现**(2026-06-02,P1-5)。`web_preview.snapshot()` 在没有浏览器/GPU/桌面环境时,
> 按 Tier 1 → 2 → 3 逐级降级给出**某种**预览输出,让飞书机器人 / CI / 远程 ssh 三个场景都能用。
> 权威规格见 `share/build123d-cad改造/03-viewer多引擎子技能.md` §10。

## API

```python
from web_preview import start, snapshot

start(file, workspace=None) -> str                       # 浏览器可点开的 URL(P0-3 已实现)
snapshot(file, workspace=None, mode="auto", out=None, size=None) -> dict
# 返回:{"tier":1|2|3, "kind":"url"|"png"|"json",
#        "path":<abs>, "fallback_reason":<str|None>, "duration_ms":<int>}
```

`mode` 语义:

| mode | 行为 |
|---|---|
| `auto`(默认) | Tier 1 → 2 → 3 逐级尝试,每级失败回落,三档全挂才抛 `HeadlessUnavailable` |
| `web` | 强制 Tier 1,失败抛 `HeadlessUnavailable` |
| `snapshot` | 强制 Tier 2(跳过 Tier 1) |
| `probe` | 强制 Tier 3(只解析尺寸不渲染) |

## 三档实现

| Tier | 工具 | 触发条件 | 主产物 | 备注 |
|---|---|---|---|---|
| **1** | playwright + headless chromium | playwright 可 import 且 `playwright install --dry-run chromium` exit 0 | `_viewer/preview.url`(单行 URL)+ 可选 `_viewer/snapshot.png` | 与用户浏览器所见 1:1;截图失败不影响 URL 主产物 |
| **2** | VTK / OCP 离屏渲染 | `vtk` 或 `OCP` 任一可 import | `<stem>.preview.png`(默认 1024×768,源文件同级 sibling) | `.stl` 直接渲;`.step/.brep/.iges` 先经 build123d/OCP 转临时 STL 再 VTK 离屏渲;飞书机器人主用此档 |
| **3** | OCP/build123d 或 steputils | `OCP` 或 `steputils` 任一可 import | `<stem>.dimensions.json` | 纯尺寸 JSON,任何环境(裸 docker / 无显卡)都能跑;终极兜底 |

每档不可用时内部抛 `_TierUnavailable(reason)`,编排层据此回落并把 `reason` 记进 `fallback_reason`。

## 产物路径契约(对接 03 §10.4 / 08 §2.0)

产物根目录 `base` = `out` 参数;缺省为源文件所在目录。

```
<base>/
├── _viewer/
│   ├── preview.url        # Tier 1 主产物:单行 URL 文本(飞书可直接贴链接)
│   ├── snapshot.png       # Tier 1 可选:playwright 渲染截图
│   └── tier_meta.json     # 任一 tier 跑完都写,降级链审计字段
├── <stem>.preview.png     # Tier 2 主产物(与 STEP/STL 同级 sibling)
└── <stem>.dimensions.json # Tier 3 主产物
```

`tier_meta.json` schema:`{tier, kind, path, fallback_reason, tier_attempted, duration_ms, tool, ts}`。
`dimensions.json` schema 见 03 §10.5(`bbox_mm.{min,max}` / `size_mm` 必给;
OCP 后端补全 `volume_mm3 / surface_area_mm2 / topology / centroid_mm`,steputils 后端这些字段诚实给 `null`,不瞎填 0;`mass_kg` 默认 null,待 mechanical 提供材料后由 02 脚本补)。

## 各场景默认 mode(对接 01 §1)

| 调用方 | 默认 mode | 理由 |
|---|---|---|
| 用户终端 `bash start.sh <file>` | `web` | 直接浏览器看 |
| 飞书机器人 employee_bot | `auto`(实际多落 Tier 2) | 飞书贴 PNG 体验最好;chromium 装包重,默认不上 Tier 1 除非 BOT 显式装 |
| CI(GitHub Actions ubuntu) | `auto`(实际多落 Tier 2) | playwright 装 + 跑 ≥ 90s;Tier 2 OCP/VTK < 5s |
| `python web_preview.py --probe <file>` | `probe` | 纯尺寸校验,1s 内出 |

## 依赖与环境注意

- **生产 venv 不装 CAD 依赖**:OCP / build123d / vtk / playwright / steputils 均**不进**公司 company 生产 venv,
  只在本机 CAD venv 或专门容器里装。`snapshot()` 因此写成防御式 import:缺库即回落,不 import 失败崩溃。
- playwright chromium 跑 headless 加 `--no-sandbox --use-gl=swiftshader`(macOS / Linux 容器都要)。
- 截图前等 `networkidle` + `canvas` selector 出现 + 一帧渲染时间。
- VTK 必须 `SetOffScreenRendering(1)`,否则无 DISPLAY 环境会崩。

## 验收

```bash
# 纯逻辑(无浏览器/CAD 依赖,CI 必跑):detect_tier / mode 路由 / 回落编排 / 路径 / schema
cd skills/viewer && pytest tests/test_headless_fallback.py -q   # 20 passed, 2 skipped(真渲染缺库)

# 本机装了 chromium → Tier 1 出 URL + 截图
python skills/viewer/scripts/web_preview.py --mode=web /tmp/hip_bracket.step
test -f <base>/_viewer/preview.url

# 假装无 chromium → 落 Tier 2 PNG(需 vtk/OCP)
PLAYWRIGHT_DISABLED=1 python skills/viewer/scripts/web_preview.py --mode=snapshot /tmp/hip_bracket.step
file <base>/hip_bracket.preview.png | grep -q PNG

# 强制 Tier 3 → dimensions.json(需 OCP/steputils)
python skills/viewer/scripts/web_preview.py --probe /tmp/hip_bracket.step
jq .bbox_mm.max <base>/hip_bracket.dimensions.json

# 降级审计:Tier 1 试过失败落到 2 → [1, 2]
jq .tier_attempted <base>/_viewer/tier_meta.json

# 三档全失败(裸环境无任何依赖)→ 抛 HeadlessUnavailable,不静默
```
