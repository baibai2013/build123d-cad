# parts-lib Cache Workflow

> Scope：`build123d-parts-lib` 仓库的 `parts/<category>/cache/` 缓存管理。
> 谁触发：新增 / 修改 / 验证零件时。
> 依赖脚本：`scripts/build_cache.py`（生成）、`scripts/verify_cache.py`（验证）。

---

## 两个入口脚本

| 脚本 | 作用 | 何时用 |
|------|------|--------|
| `scripts/build_cache.py` | 生成 STEP + PNG 到 `cache/` | 改了 factory / 新增零件后 |
| `scripts/verify_cache.py` | 三层断言验证 STEP 几何 | 每次 commit 前 / CI |

两个脚本**共用** `build_cache.py::_rep_bundle()` 作为"代表规格清单"—— `verify_cache.py` 直接 `from build_cache import _rep_bundle`。增删零件只改一处。

---

## 生成：`build_cache.py`

**核心特性：增量覆盖**——只覆盖 bundle 里的零件，不在 bundle 里的 cache 保留不动。不再做全局 `purge_cache`。

### 三种调用形态

```bash
# 1. 全量重建 bundle 所有条目（默认行为）
python scripts/build_cache.py

# 2. 按 category / slug 过滤（bundle 里的代表规格）
python scripts/build_cache.py --only bearings      # category 级
python scripts/build_cache.py --only ball_bearing  # slug 级

# 3. 指定具体型号（新增）—— 额外文件，不覆盖代表
python scripts/build_cache.py --only ball_bearing --model 6000ZZ
# → cache/ball_bearing_6000zz.{step,png}
```

### `--model` 用法约束

- 必须与 `--only <slug>` 搭配（单 slug 精确匹配）
- 所选 factory 的 `kwargs` 必须含 `model` 键（轴承/舵机都有；几何参数化零件如 `spur_gear(m=2, z=20)` 没有 `model`，需改用 `--only` 代表规格 + 手改 bundle）
- 输出文件名：`{slug}_{model_lower_underscored}.{step,png}`，与代表规格**并存**
- 用途：为测试 / 专项导出单独出一套文件，不污染代表规格

### 增量语义

- bundle 里条目 → 覆盖（`export_step` / `save_preview_png` 覆盖写入）
- bundle 外的 cache 文件（旧快照、别人的测试产物）→ 保留
- 某 slug 被重命名/移除 → 旧 cache 成孤儿残留，不自动清理（如需清理手动 `rm`）

---

## 验证：`verify_cache.py`

### 三层断言

| 层 | 检查 | 阈值 | 失败意味 |
|----|------|------|---------|
| L1 | `cache/<slug>.step` 存在 + `import_step()` 能读回 | 存在性 + 无异常 | 文件丢失或损坏 |
| L2 | **重导入 bbox 与 factory 原件差** | 各轴 < 0.5 mm | 外形几何丢失，**硬性失败** |
| L3 | **重导入体积（`abs(solid.volume)` 求和）与原件差** | < 10% | 体积健康度提示 |

### 为什么 L3 容差这么松

Compound 带子孔的子件（如带球窝的保持架）经 OCP XDE 导出 STEP 后，`import_step` 回来的 Solid 可能：
- 法向翻转 → `volume` 为负 → 已用 `abs()` 消除
- 球窝变浅 / 微小几何损失 → 真实体积差 1~8%

**L2 bbox 是主断言**（外形保真），L3 volume 只作健康度次级信号。

### 调用

```bash
python scripts/verify_cache.py                     # 全量
python scripts/verify_cache.py --only bearings     # 按 category
python scripts/verify_cache.py --only ball_bearing # 按 slug
```

退出码：全 PASS = 0，任意 FAIL = 1（CI 友好）。

### 输出格式

```
  [PASS] bearings/ball_bearing  L1✓ L2✓ L3✓  bbox Δ=(0.000,0.000,0.000)mm  vol Δ=0.00%
  [PASS] bearings/mr_bearing    L1✓ L2✓ L3✓  bbox Δ=(0.000,0.000,0.000)mm  vol Δ=8.42%
  [FAIL] bearings/broken        L1✓ L2✗ L3-  bbox Δ=(1.200,0.000,0.500)mm
```

L2 失败时 L3 跳过（`-`）——因为 bbox 都对不上 volume 没意义。

---

## 新增 / 修改零件的完整流程

```
┌────────────────┐
│ 1. 写/改 factory │   parts/<cat>/<part>.py
└──────┬─────────┘
       │
       ▼
┌────────────────────┐
│ 2. 更新 YAML + init │   parts/<cat>/<cat>.yaml、__init__.py
└──────┬─────────────┘
       │
       ▼
┌─────────────────────────────────┐
│ 3. 更新 _rep_bundle 新增条目     │   scripts/build_cache.py
│    (除非复用已有 factory+kwargs) │
└──────┬──────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────┐
│ 4. 生成：python scripts/build_cache.py        │
│    --only <slug>  ← 建议用,避免误刷其他零件   │
└──────┬───────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────┐
│ 5. 验证：python scripts/verify_cache.py       │
│    --only <slug>                              │
│    → 必须 PASS 才能 commit                    │
└──────┬───────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────────┐
│ 6. 语义视觉验证（取代纯人工目视）                                  │
│                                                                  │
│    python3 ~/.claude/skills/cad-vision-verify/scripts/           │
│            verify_loop.py                                        │
│      --mode standard-part                                        │
│      --slug <slug>                                               │
│      --model <代表型号>                                           │
│      --yaml parts/<cat>/<cat>.yaml                               │
│      --verify-temp ./verify_temp                                 │
│      --cache-verify-result <步骤5输出的 json>（可选）             │
│                                                                  │
│    → PASS / WARN → commit                                        │
│    → FAIL → 查 issues 列表，修 factory 代码后回步骤 4            │
└──────────────────────────────────────────────────────────────────┘
```

**步骤 6 验证内容**（`standard-part` 模式，无需参考图）：

| 检查项 | 工具 | 说明 |
|--------|------|------|
| Compound 子件语义 | `compound_check.py` | 验证 outer_ring / inner_ring / cage / ball_N 标签和体积占比 |
| 7 视角 AI Vision | `compare.py` | YAML 规格驱动，Claude 判断"外径/宽度/内部结构是否可见且正确" |
| verify_cache 联动 | `verify_loop.py` | L2 PASS → +10，L3 PASS → +5；L2 FAIL 直接强制 FAIL |
| 诊断输出 | `diagnose.py` | FAIL 时输出 ≤3 条 S/M/L 分类诊断，含 `fix_action` 具体路径 |

**容易踩的坑**：

| 坑 | 症状 | 解决 |
|----|------|------|
| 不加 `--only` 跑 `build_cache.py` | 所有 bundle 零件全被重建（包含你没改的） | 养成 `--only <slug>` 习惯 |
| 跑完忘了 verify | STEP 看着 OK，实际 bbox 错 | `verify_cache.py --only <slug>` 必跑 |
| 只跑 verify_cache 跳过步骤 6 | bbox/volume 通过但内部几何错（如滚道缺失） | `verify_loop.py --mode standard-part` 必跑 |
| Compound 返回 factory | `.volume` 算不对（Compound 不递归） | `verify_cache` 已用 `solids()` 平铺规避 |
| STEP export 出现 `Unknown Compound type` 警告 | 无色 + 复杂子孔件 volume 往返丢失 | bbox 断言是主，volume 放宽到 10% |

---

## PNG 后端选择（OCP 优先 / VTK 兜底）

`_preview_ocp.py::save_preview_png_auto()` 自动选：

| 后端 | 何时用 | 画质 | 依赖 |
|------|--------|------|------|
| OCP CAD Viewer (WebGL) | 面板开着 + 端口 3939/4567 活着 | 边线清晰，金属质感 | Cursor / VS Code OCP 扩展 |
| VTK offscreen | OCP 连不上时 | Phong 平滑，无边线 | `vtk` Python 包 |

**OCP 后端一个易踩坑**：面板窗口像素 = 截图像素。面板被最小化 / 侧边细条 → PNG 是条形（2412×28）。跑 `build_cache.py` 前把 OCP 面板拉成接近正方形。

**`show() → save_screenshot()` 异步问题**：WebGL 渲染需要时间，`time.sleep(2.0)` 对简单零件够，对多 child Compound（10+ 滚珠）可能抓到上一帧残像。症状：三张图顺序错乱或内容互串。需要时把 `wait_s` 调大到 4s。

---

## 与 build123d-cad skill 的接口

- **单部件 Playbook 验收门** 引用 `verify_cache.py`：新零件 commit 前必过
- **多部件 Playbook M4 cache 入库** 引用 `build_cache.py --only <slug>`
- **参考物建模 R5** 里 STEP 导出后可选跑 `verify_cache` 确认导出没丢
- **步骤 6 语义视觉验证** 调用 `cad-vision-verify` 的 `standard-part` 模式：
  `verify_cache.py` 结果（JSON）通过 `--cache-verify-result` 传入，两层验证联动
