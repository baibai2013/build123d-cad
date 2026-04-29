# 标准件入库全流程 Playbook（A 系列）

> **适用场景**：向 `build123d-parts-lib` 新增一类标准件（螺丝头型 / 螺母形状 / 垫圈 / 嵌件）。
> **前置条件**：`build123d-parts-lib` 已作为 submodule 挂载，`_thread_utils.py` 可用。
> **与其他 Playbook 的区别**：S 系列（单零件原创建模）→ 用于非标自制件；A 系列（标准件入库）→ 数据驱动，优先查标准 + 套模板。

---

## 阶段概览

```
A1 数据收集  →  A2 YAML 条目  →  A3 Python 模块  →  A4 三层验证  →  A5 入库收尾
```

---

## A1 — 数据收集

**目标**：建模前拿到准确的几何参数 + 可追溯的数据来源。严禁凭记忆估数字。

### A1.1 识别标准

根据用户给出的零件类型，确认所属标准：

| 类型 | 常见标准 |
|------|---------|
| 内六角圆柱头螺丝 | ISO 4762 / DIN 912 |
| 内六角沉头螺丝 | ISO 10642 |
| 内六角圆头螺丝（button） | ISO 7380 |
| 十字沉头螺丝 | ISO 7046 |
| 一字沉头螺丝 | ISO 2009 |
| 十字圆盘头螺丝（pan） | ISO 7045 |
| 一字圆盘头螺丝 | ISO 1580 |
| 六角外头螺栓 | DIN 933 / ISO 4017 |
| 六角螺母（标准 / 薄） | ISO 4032 / GB/T 6172 |
| 尼龙锁紧螺母 | DIN 985 |
| 盖形螺母 | DIN 1587 |
| 法兰螺母 | DIN 6923 |
| 蝶形螺母 | DIN 315 |
| 方形螺母 | DIN 562 |
| T 型螺母（2020 铝型材） | 市场惯例（非统一标准） |
| 平垫 | ISO 7089 |
| 弹垫 | GB/T 93 |
| FDM 热熔嵌件 | Ruthex RX / InsertEZ |
| 马车螺栓（圆头 + 方颈） | DIN 603 / ISO 8678 |
| 六角铜柱隔离柱（FF / MF） | 市场惯例（无统一标准） |
| 内六角紧定螺丝（平端 / 锥端 / 杯端） | ISO 4026 / 4027 / 4029 |
| 拉铆螺母 | 市场惯例（Blind Rivet Nut） |
| 弹簧销（开口圆管） | DIN 1481 / ISO 8752 |

先检查 skill 内 `references/data-sources/fasteners.yaml` 是否已有该 key → 有则直接读取，跳至 A2。

### A1.2 按置信度查数据源

按以下优先级查询，记录 `confidence` 分：

| 来源 | 查询方式 | confidence |
|------|---------|-----------|
| ISO / DIN 原版标准 PDF | `WebSearch: "ISO 4762" table dimensions filetype:pdf` | 5 |
| Bossard / Würth / Misumi 产品页 | `WebSearch: bossard M4 ISO 7380 dimensions` | 5 |
| SKF / IFI / 制造商技术文档 | `WebSearch + spec_lookup.py` | 4 |
| McMaster-Carr / Fastenal 规格页 | `WebSearch` | 4 |
| Wikipedia / 工程 wiki | `WebSearch` | 3 |
| 市场惯例（多厂商对比） | `WebSearch` + 工程论坛交叉验证 | 3 |

**查询关键词模板**：
```
"<标准代号> M<size> dimensions table"     # 例：ISO 7380 M4 dimensions table
"DIN 315 wing nut M4 specifications mm"
"bossard <标准代号> M<size>"
```

如果只能找到 confidence ≤ 3 的来源，在 YAML `notes` 字段加 `[unverified]` 标注。

### A1.3 必须收集的字段

**所有类型都需要**：
- `d`（螺纹公称直径 mm）
- `pitch`（粗牙螺距 mm）
- `clearance_hole.close_fit / medium_fit / loose_fit`
- `source.primary`（来源 URL）
- `source.confidence`（1–5）
- `source.last_verified`（`YYYY-MM-DD`）

**螺丝专有**：
- `head.dk`（头外径）
- `head.k`（头高）
- `head.s`（扳手对边，内六角 / 外六角）
- `common_lengths_mm: [...]`
- `counterbore.diameter / depth`（沉孔推荐，socket head 类）
- `countersink.angle_deg / diameter`（沉头类）

**螺母专有**：
- `dimensions.s`（对边宽）
- `dimensions.m`（高度）
- 形状专有字段（例）：
  - flange nut：`flange_d`, `flange_t`
  - wing nut：`hub_d`, `wing_span`, `wing_h`, `wing_w`
  - square nut：`a`（方边长）
  - T-slot nut：`head_w`, `head_h`, `stem_w`, `stem_h`, `length`
  - cap nut：`m`（含半球顶的总高）

### A1.4 产出报告

整理为 Markdown 表格，**得到用户确认后**进入 A2：

```markdown
## A1 数据收集结果

| 参数 | M3 | M4 | M5 | 来源 | confidence |
|------|----|----|----|----- |-----------|
| d    | 3.0 | 4.0 | 5.0 | ISO 7380 | 5 |
| pitch | 0.50 | 0.70 | 0.80 | ISO 7380 | 5 |
| dk   | 5.7 | 7.6 | 9.5 | bossard.com | 5 |
| k    | 1.65 | 2.2 | 2.75 | bossard.com | 5 |
| s    | 2.0 | 2.5 | 3.0 | bossard.com | 5 |
```

---

## A2 — YAML 条目创建

**目标**：将参数写入 `build123d_parts_lib/parts/fasteners/fasteners.yaml`，供 `scripts/build_cache.py` 自动发现。

### A2.1 Key 命名规则

```
{SIZE}_{STANDARD_CODE}         例：M4_ISO7380
{SIZE}_NUT_{STANDARD_CODE}     例：M4_NUT_DIN315
```

每个规格写一条（M3 / M4 / M5 各独立条目）。

### A2.2 YAML 模板

```yaml
M4_ISO7380:
  aliases: [M4-button, M4-ISO7380, M4-button-head]
  standard: "ISO 7380"
  type: button-head-socket-screw      # ← 必须唯一，与 Python 模块 _load_specs() 中的 type 完全匹配

  thread:
    d: 4.0
    pitch: 0.70
    unit: mm

  # 螺丝专有
  head:
    dk: 7.6       # 头外径
    k: 2.2        # 头高
    s: 2.5        # 内六角对边

  # 螺母/垫圈专有（按类型选用）
  dimensions:
    s: 7.0        # 对边宽
    m: 5.0        # 高度
    # 形状专有字段按需补充

  clearance_hole:
    close_fit: 4.3
    medium_fit: 4.5
    loose_fit: 4.8

  common_lengths_mm: [6, 8, 10, 12, 16, 20]

  source:
    primary: https://www.bossard.com      # 完整 URL
    confidence: 5
    last_verified: 2026-04-28

  factory:                               # ★ scripts/build_cache.py 读取此字段
    module: build123d_parts_lib.parts.fasteners.screw_button_hex
    fn: make_button_hex_screw
    args: {size: "M4", length: 12}       # 螺母不需要 length
    cache: cache/m4_iso7380_L12.step

  notes: "ISO 7380 M4 内六角圆头螺丝（button head）。"
```

> **type tag 规则**：由 Python 模块的 `_load_specs()` 函数中 `entry.get("type") != "..."` 做路由匹配，必须一一对应。新件型须定义新 type tag（不能复用已有 tag）。

### A2.3 YAML 语法验证

```bash
cd build123d_parts_lib/parts/fasteners
python3 -c "import yaml; yaml.safe_load(open('fasteners.yaml').read()); print('YAML OK')"
```

验证通过后进入 A3。

---

## A3 — Python 模块编写

**目标**：实现 `make_xxx(size) → Part`，遵循四层结构，保证 YAML 驱动和 fallback 兜底。

**参考模板**：`experience/code-patterns/fasteners/standard-part-module-pattern.md`

### A3.1 文件命名

```
screw_<variant>.py      螺丝：screw_button_hex.py / screw_csk_phillips.py / screw_pan_slotted.py
nut_<shape>.py          螺母：nut_cap.py / nut_flange.py / nut_wing.py / nut_square.py / nut_tslot.py
<type>.py               其他：washer.py / threaded_insert.py / hex_bolt.py
```

### A3.2 四层结构

```python
# 层 1：Spec 数据容器
class MyPartSpec(NamedTuple):
    d: float; pitch: float
    <form_specific_dims>: float ...

# 层 2：内置 fallback（M3/M4/M5，与 A1 收集数据一致）
_FALLBACK: dict[str, MyPartSpec] = {
    "M3": MyPartSpec(...),
    "M4": MyPartSpec(...),
    "M5": MyPartSpec(...),
}

# 层 3：YAML 加载（优先 YAML，缺失 key 用 fallback 补）
def _load_specs() -> dict[str, MyPartSpec]:
    # ... 读 fasteners.yaml，过滤 type == "my-type-tag"
    # ... 对每个 size 建 MyPartSpec
    # ... 用 _FALLBACK 补全缺失 key
    ...

_SPECS = _load_specs()

# 层 4：公开工厂函数
def make_my_part(size: str = "M4") -> Part:
    spec = _SPECS[size.upper().strip()]
    # ... 建模（选 Pattern 13/14/15）
    return part

# 层 5：独立运行块（必须）
if __name__ == "__main__":
    for size, spec in _SPECS.items():
        part = make_my_part(size)
        export_step(part, f"cache/{size.lower()}_<tag>.step")
        print(f"OK: {size}  vol={part.volume:.1f} mm³")
```

### A3.3 选择几何 Pattern

按零件形态选（参考 `references/parts/patterns.md` Pattern 13/14/15）：

| 零件形态 | Pattern |
|---------|---------|
| 单体旋转对称（轴、销） | Pattern 4（revolve） |
| 多段异形（头 + 杆、法兰 + 六角柱） | **Pattern 13**（分段 BuildPart + fuse） |
| 需要选择性圆角 / 倒角 | **Pattern 14**（边过滤） |
| 含内螺纹 / 外螺纹 | **Pattern 15**（thread_utils） |

### A3.4 常用几何配方

**六角柱**（对边宽 s → 外接圆半径 r）：
```python
import math
r_hex = s / math.sqrt(3)
with BuildPart() as hex_bp:
    with BuildSketch(Plane.XY):
        RegularPolygon(radius=r_hex, side_count=6)
    extrude(amount=m)
```

**内螺纹减料**（贯通孔 / 盲孔）：
```python
from ._thread_utils import make_internal_thread
thread_sub = make_internal_thread(d, pitch, length=total_h)   # 贯通
thread_sub = make_internal_thread(d, pitch, length=bore_depth)  # 盲孔（bore_depth < total_h）
solid = solid.cut(thread_sub)
```

**外螺纹螺杆**：
```python
from ._thread_utils import make_external_thread
r_minor = (d - 1.2269 * pitch) / 2
with BuildPart() as shank_bp:
    Cylinder(radius=r_minor, height=L, align=(Align.CENTER, Align.CENTER, Align.MIN))
thread_add = make_external_thread(d, pitch, L)
shank = shank_bp.part.fuse(thread_add)
```

**多体融合（Pattern 13）**：
```python
with BuildPart() as part_a_bp:
    ...  # 下段几何
with BuildPart() as part_b_bp:
    ...  # 上段几何
solid = part_a_bp.part.fuse(part_b_bp.part.translate((0, 0, offset_z)))
```

**边过滤圆角（Pattern 14）—— 容差必须用 0.1–0.5，不能用 1e-3**：
```python
# 顶底引入倒角（闭合边）
top_z = solid.bounding_box().max.Z
chamfer_edges = [e for e in solid.edges()
                 if e.is_closed and abs(e.center().Z - top_z) < 0.2]
if chamfer_edges:
    solid = solid.chamfer(c, None, chamfer_edges)

# 竖棱倒角（开放边，长度 ≈ 高度）
ht = solid.bounding_box().size.Z
vert_edges = [e for e in solid.edges()
              if not e.is_closed
              and abs(e.center().Z - ht / 2) < ht * 0.45
              and abs(e.length - ht) < 0.3]
if vert_edges:
    solid = solid.chamfer(c, None, vert_edges)
```

### A3.5 踩坑清单（必查）

- [ ] 边过滤容差用 `0.1–0.5 mm`，**绝对不能用 `1e-3`**（OCC fuse 后顶点坐标有浮动）
- [ ] 翼片 / 凸台 Z 锚点从 `z=0`（底面）开始，不是顶面 → `z_center = feature_h / 2`
- [ ] `make_internal_thread` 已含中心圆柱，直接 `cut`，无需先打预孔；盲孔 `depth ≤ total_h`
- [ ] `RegularPolygon(radius=r)` 中 `r` 是**外接圆半径**（顶点到中心），对边宽 `s → r = s / math.sqrt(3)`
- [ ] 同一 `BuildPart` 内混合 `Cylinder` + `RegularPolygon extrude` 可能不稳定 → 分开建再 fuse
- [ ] `fillet` / `chamfer` 的 `if edges:` 保护：过滤结果为空时静默跳过，不会报错

---

## A4 — 三层验证

**顺序**：Layer 0 通过 → Layer 1 通过 → Layer 2 通过。任一层失败先修复再往下。

### Layer 0 — 语法 + 导出

```bash
cd /path/to/build123d-parts-lib

# 独立运行模块，确认无报错 + STEP 正常写出
python3 -m build123d_parts_lib.parts.fasteners.<module_name>

# 预期每行输出：
# OK: m3_<tag>.step  vol=XXX.X mm³
# OK: m4_<tag>.step  vol=XXX.X mm³
# OK: m5_<tag>.step  vol=XXX.X mm³
```

**常见报错 → 修复**：

| 报错 | 原因 | 修复 |
|------|------|------|
| `ValueError: Unknown size` | YAML type tag 不匹配 | 检查 `_load_specs()` 中 `type` 字符串与 YAML 完全一致 |
| `StdFail_NotDone` / `BRep_API` | 几何 boolean 操作失败 | 检查 fuse 体积是否重叠正确；尝试分开建体 |
| `AssertionError: fillet` | 边过滤为空 | 打印 `solid.edges()` center 坐标，调整过滤条件 |
| `volume == 0` | 实体生成空体 | BuildPart 内无有效几何；检查参数正负 |

### Layer 1 — 视觉检查（OCP Viewer 优先 → VTK 兜底）

```python
# 推荐：自动探测 OCP 端口（3939 / 4567），失败转 VTK 离屏
from build123d_parts_lib.parts.fasteners.<module_name> import make_xxx
from build123d_parts_lib._preview_ocp import save_preview_png_auto

part = make_xxx("M4")
png_path, backend = save_preview_png_auto(
    part,
    "build123d_parts_lib/parts/fasteners/cache/m4_<tag>.png",
    title="<Standard>  M4",
)
print(f"Preview PNG saved via {backend}")
```

**两种后端的取舍**：

| 后端 | 输出特征 | 何时用 |
|---|---|---|
| **OCP**（`_preview_ocp.save_preview_png_ocp`） | WebGL 渲染，**带 edge-line 描边**，齿/螺纹/棱线清晰可数 | 交互 IDE（Cursor / VS Code + OCP CAD Viewer 插件）：新增零件、人工核对 |
| **VTK**（`_preview.save_preview_png`） | `vtkPolyDataNormals + feature_angle=60°`，Phong 平滑但无边线 | CI / headless 服务器 / 无 Viewer 环境 |

实测 OCP 输出 PNG 约 120~330 KB（比 VTK 的 30~90 KB 大 3~5 倍），**齿形判读可靠性远高于 VTK**——
新增齿轮类零件务必用 OCP 截图核对齿数。

**OCP 后端需要**：VS Code / Cursor 中 OCP CAD Viewer 扩展已启动（监听 3939 端口）。
`save_preview_png_auto` 会先 `get_ports() + port_check()` 探测，没活跃端口自动转 VTK。

**视觉检查清单**（逐项确认）：

| 特征 | 检查标准 |
|------|---------|
| **整体外形** | 与该类型实物外观一致（圆柱头 / 盖形 / 翼片 / T 截面等） |
| **外螺纹（螺丝/螺栓）** | 侧面可见锯齿螺牙纹路，杆端有倒角 |
| **内螺纹（螺母）** | 从顶面孔口看到螺纹凹槽纹路 |
| **驱动槽 — 内六角** | 顶面六棱孔可见，深度合理 |
| **驱动槽 — 十字** | 十字槽有明显锥度（顶宽底窄），两道槽相互正交 |
| **驱动槽 — 一字** | 贯穿头部直径的通槽，深度合理 |
| **盖形螺母** | 顶部半球 dome 可见，底部六角柱清晰 |
| **法兰螺母** | 底部圆盘法兰明显宽于六角柱 |
| **蝶形螺母** | 两侧翼片对称，从底面延伸，外端圆角可见 |
| **T 型螺母** | T 截面清晰（宽头在下、窄茎在上，呈阶梯形） |
| **无破面 / 无穿透** | 实体无异常镂空或凹陷 |

### Layer 2 — Cache 集成（build_cache.py 统一入口）

先在 `scripts/build_cache.py` 的 `_rep_bundle()` 清单中加入新 factory 的**代表规格**条目：

```python
# scripts/build_cache.py (_rep_bundle 返回项)
("fasteners", "<slug>", make_xxx,
 dict(size="M4"), "<Standard>  M4"),
```

然后运行：

```bash
cd /path/to/build123d-parts-lib
python3 scripts/build_cache.py          # 重建全部 cache（purge + 全部重生成）

# cache 规范：每类 factory 只存 1 对代表文件
ls build123d_parts_lib/parts/fasteners/cache/<slug>.step
ls build123d_parts_lib/parts/fasteners/cache/<slug>.png
```

❌ 不要为每个规格（M3/M4/M5）都入 cache；只入代表规格（M4），其他规格运行时按需生成。

### A4 产出报告

验证完成后输出（复制给用户）：

```
──────────────────────────────────────────
新增标准件：<件型名称>（<标准代号>）
规格：M3 / M4 / M5

Layer 0 — 导出：
  m3_<tag>.step  vol=XXX mm³  ✅
  m4_<tag>.step  vol=XXX mm³  ✅
  m5_<tag>.step  vol=XXX mm³  ✅

Layer 1 — 视觉（VTK 离屏）：
  预览：cache/<slug>.png
  外形正确 ✅ | 螺纹可见 ✅ | 关键特征：<逐条列出> ✅

Layer 2 — Cache 集成：
  scripts/build_cache.py 全部 ✅（代表规格 1 step + 1 png）

数据来源：<source.primary>（confidence=N，last_verified=YYYY-MM-DD）
──────────────────────────────────────────
```

---

## A5 — 入库收尾

**目标**：A4 三层验证全部通过后，把新件型正式写入索引、文档、技能数据源，并提交两个 repo。

> A5 是强制步骤，不能跳过。未完成 A5 = 零件只在本机，其他人拿不到。

### A5.1 生成 canonical cache（STEP + PNG）

> 每个 factory 只出**一个代表规格**，用短名（不带 size/length 后缀）。
> 这是 `parts-index.md` 预览图引用的规范路径，其他规格需要时直接调 factory 重新生成。

**规格选择约定**：

| 类别 | 代表规格 | 说明 |
|------|---------|------|
| **紧固件**（螺丝/螺母/螺栓/垫圈/嵌件） | **M4** | 最常用，覆盖所有头型/形状 |
| **轴承**（bearings） | 工厂默认型号（608ZZ / MR85ZZ / F688ZZ / LM8UU） | 不用 M4，用型号名 |
| **销与光轴**（pins） | 工厂默认直径+长度（D4 / L20 等） | 不用 M4，用 diameter+length |
| **舵机**（servos） | 工厂默认型号（SG90 / single horn） | 不用 M4，用型号名 |
| **传动件**（transmission） | 工厂默认参数（20T 带轮 / L200 同步带 / 5×5 平行键） | 不用 M4 |
| **卡簧**（retainers） | 工厂默认直径（shaft_d=8 / hole_d=12） | 不用 M4 |
| **密封件**（seals） | 工厂默认参数（d1=10, d2=2.0） | 不用 M4 |

**紧固件（fasteners）代码模板**（VTK 离屏渲染，不依赖任何浏览器）：

```python
from pathlib import Path
from build123d import export_step
from build123d_parts_lib.parts.fasteners.<module_name> import make_xxx
from build123d_parts_lib._preview import save_preview_png

cache = Path("build123d_parts_lib/parts/fasteners/cache")
cache.mkdir(exist_ok=True)

part = make_xxx("M4")                              # 紧固件代表规格 = M4

# STEP（canonical 短名；每类 1 对 step + png）
export_step(part, str(cache / "<slug>.step"))

# PNG（VTK 离屏渲染，Phong 平滑，feature_angle=60° 保尖角）
save_preview_png(
    part,
    cache / "<slug>.png",
    title="<Standard>  M4",
    size=(480, 480),
    elev=25,
    azim=-55,
)
```

> **推荐入口**：不要自己手写上面这段；加一条 `(category, slug, fn, kwargs, title)`
> 到 `scripts/build_cache.py` 的 `_rep_bundle()`，然后 `python scripts/build_cache.py`
> 会自动处理 STEP + PNG 生成 + 打印 volume。这是 parts-lib 的**唯一正规入口**。

**非紧固件类目**用 `scripts/gen_nonfastener_cache.py` 中的批量模板（所有 factory 调默认参数）。

**cache/ 目录规范**：每个 factory 只保留一个 `<slug>.step` + `<slug>.png`，
任何带尺寸后缀（`m4_xxx`, `d4_xxx`）或 `_verify` 的临时文件**必须删除**后再提交。

**命名规则**：

| 类型 | canonical slug（短名） | 示例 |
|------|----------------------|------|
| `screw_<variant>.py` | `screw_<variant>` | `screw_set`, `screw_carriage` |
| `nut_<shape>.py` | `nut_<shape>` | `nut_cap`, `nut_wing` |
| `standoff_hex.py` | `standoff_hex` | — |
| `rivet_nut.py` | `rivet_nut` | — |
| `pin_spring.py` | `pin_spring` | — |
| `ball_bearing.py` | `ball_bearing` | — |
| `timing_pulley_gt2.py` | `timing_pulley_gt2` | — |

### A5.2 更新 parts-index.md

文件路径：`build123d_parts_lib/../docs/parts-index.md`（repo 根目录下的 `docs/`）

**操作**：在对应 category 的 Markdown 表格里添加一行：

```markdown
| `<slug>`<br><中文名> | `make_xxx(size, ...)` | M3 / M4 / M5（标准代号） | ![](../build123d_parts_lib/parts/fasteners/cache/<slug>.png) |
```

- 预览图路径 = `../build123d_parts_lib/parts/<category>/cache/<slug>.png`（相对 `docs/` 目录）
- 如果零件已在「计划 / 待补」等占位行 → 直接改为正式行（不要留注释或 "pending" 字样）

**更新统计行**（文件末尾）：

```markdown
- **Factory 文件**：NN 个 `.py`（MM 紧固 + ...）   # 每新增一个 .py +1
- **YAML 条目**：NNN+ 条                            # 每批入库 +条目数
```

### A5.3 更新 fasteners/README.md

文件路径：`build123d_parts_lib/parts/fasteners/README.md`

**操作清单**：

1. **Section 2（类型表）**：在对应子节（螺丝 / 螺栓 / 螺母 / 隔离柱 / 其他）添加新模块行
2. **Section 3（Quick Start）**：添加新类型的 import + 示例调用
3. **Section 4（文件索引）**：在 `threaded_insert.py` 行之后添加新文件行
4. **计划章节（若有）**：如果新类型曾列在"待实现"章节，删除对应行；若该章节全部清空则删除整个章节

### A5.4 更新 skill 数据源

文件路径：`~/.agents/skills/build123d-cad/references/data-sources/fasteners.yaml`

**追加新类型条目**（以 M4 代表，格式如下）：

```yaml
M4_<TAG>:
  aliases: [M4-<alias>, ...]
  standard: "<标准代号>"
  type: <type-tag>                        # 与 Python _load_specs() type 一致
  thread: {d: 4.0, pitch: 0.70, unit: mm}
  # 几何专有字段（head / dimensions / tip 等）
  source: {primary: <URL>, confidence: N, last_verified: YYYY-MM-DD}
  parts_lib:
    module: build123d_parts_lib.parts.fasteners.<module_name>
    fn: make_<xxx>
    args: {size: "M4", ...}              # 若有 tip/style/length 参数也加进去
  notes: "<一句话说明>"
```

> **parts_lib 字段是 A5 的核心产出**：它让技能在未来生成装配时能自动调用工厂函数，而不需要手工查表。

### A5.5 Commit 两个 repo

```bash
# ① parts-lib repo
cd /path/to/build123d-parts-lib
git add \
  build123d_parts_lib/parts/fasteners/cache/<slug>.step \
  build123d_parts_lib/parts/fasteners/cache/<slug>.png \
  build123d_parts_lib/parts/fasteners/README.md \
  docs/parts-index.md
git commit -m "docs+cache: <件型名> M4 canonical cache + index/README update"

# ② skill repo
cd ~/.agents/skills/build123d-cad
git add references/data-sources/fasteners.yaml
git commit -m "feat(fasteners): add <件型名> entries to skill fasteners.yaml"
```

**Push 注意**：
- parts-lib 若历史 commit 含 `.github/workflows/` 变更 → 需先 `gh auth refresh -s workflow` 再 push
- skill repo 正常 push 即可

### A5 产出清单（完成标志）

```
✅ cache/<slug>.step           M4 代表规格 STEP（短名）
✅ cache/<slug>.png            M4 代表规格 OCP 截图（短名）
✅ docs/parts-index.md         新行已添加，预览图链接有效，统计数字已更新
✅ fasteners/README.md         Section 2/3/4 已更新，计划章节已清理
✅ skill fasteners.yaml        新条目含 parts_lib 指针
✅ parts-lib repo commit        含 STEP + PNG + README + index
✅ skill repo commit           含 fasteners.yaml
```

---

### ISO 粗牙螺距 + 小径

| 规格 | d (mm) | pitch (mm) | r_minor = (d − 1.2269p)/2 |
|------|--------|-----------|--------------------------|
| M2 | 2.0 | 0.40 | 0.755 |
| M2.5 | 2.5 | 0.45 | 0.974 |
| M3 | 3.0 | 0.50 | 1.193 |
| M4 | 4.0 | 0.70 | 1.572 |
| M5 | 5.0 | 0.80 | 1.827 |
| M6 | 6.0 | 1.00 | 2.388 |

### 六角外接圆半径

```
r_circumscribed = s / sqrt(3)      # 对边宽 → 顶点到中心距离
```

| 对边 s | 外接圆 r |
|--------|---------|
| 5.5 | 3.175 |
| 7.0 | 4.041 |
| 8.0 | 4.619 |
| 10.0 | 5.774 |
| 13.0 | 7.506 |

### 边过滤容差推荐

| 用途 | 容差值 |
|------|-------|
| 闭合边 Z 位置（顶 / 底面） | `0.1 mm` |
| 开放边中心位置（X / Y / Z） | `0.3–0.5 mm` |
| 开放边长度匹配 | `0.5–2.0 mm` |
| **不要用** | `1e-3 mm`（OCC fuse 后坐标有浮动） |
