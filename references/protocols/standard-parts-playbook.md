# 标准件入库全流程 Playbook（A 系列）

> **适用场景**：向 `build123d-parts-lib` 新增一类标准件（螺丝头型 / 螺母形状 / 垫圈 / 嵌件）。
> **前置条件**：`build123d-parts-lib` 已作为 submodule 挂载，`_thread_utils.py` 可用。
> **与其他 Playbook 的区别**：S 系列（单零件原创建模）→ 用于非标自制件；A 系列（标准件入库）→ 数据驱动，优先查标准 + 套模板。

---

## 阶段概览

```
A1 数据收集  →  A2 YAML 条目 + Contract  →  A3 Python 模块  →  A4 三层验证  →  A5 入库收尾
```

**Contract 文件说明**：`parts/<category>/contracts/<slug>_contract.yaml`  
每 slug 一个文件，在 A2 阶段新建，描述**这一类零件的结构性约束**（与型号无关，608ZZ / 624ZZ 共用同一 contract）。  
- 有非平凡内部几何（轴承 / 齿轮 / 舵机）→ 写 `compound_structure` + `geometry_invariants`  
- 纯外形件（螺丝 / 螺母 / 垫圈）→ 也需要 contract：ISO 小径公式 / 六角不变式 / 沉孔可达条件（见 A2.4 螺丝类模板）

---

## A0 — 修改已有标准件（改动已入库的件，不是新增）

> 仅适用于修改 `build123d-parts-lib` 中**已入库**标准件的 factory 代码或 YAML。  
> 新增件从 A1 开始。

### A0.1 确定改动范围

```bash
# 判断改动文件是 slug 专有文件还是共享模块：
#   slug 专有：screw_button_hex.py / ball_bearing.py — 只影响该 slug
#   共享模块：_bearing_geometry.py / _thread_utils.py — 可能影响多个 slug

# 查找所有引用共享模块的 factory 文件（得到受影响 slug 列表）
grep -r "from.*_bearing_geometry" build123d_parts_lib/parts/ --include="*.py" -l
grep -r "import _thread_utils"    build123d_parts_lib/parts/ --include="*.py" -l
```

**范围决策树**：

```
改动文件是 slug 专有文件？
  ├─ 是（screw_button_hex.py）
  │    → 只需重跑该 slug 的 A4 验证
  │    → 提交范围：改动文件 + 对应 cache/<slug>.step/png
  │
  └─ 否（共享模块 _bearing_geometry.py）
       ├─ grep 找出所有引用该模块的 factory 文件（受影响 slug 列表）
       ├─ 对每个受影响 slug：重跑 A3.5 踩坑自查 + A4 完整三层验证
       └─ 提交范围：改动文件 + 所有受影响 slug 的 cache 文件
```

### A0.2 Contract + GEOMETRY_INVARIANTS 同步检查

当改动涉及几何参数或 g-dict 结构时，必须检查：

| 检查项 | 操作 |
|--------|------|
| `GEOMETRY_INVARIANTS` 列表是否需要更新 | 对照 A3.2 层 5 的 lambda 列表 |
| contract YAML `geometry_invariants` 是否需要同步 | contract `expr` 从 Python lambda 派生；改 lambda 必须同步 contract |
| g-dict 接口（TypedDict / docstring）是否需要更新 | 若 g-dict key 增删，对应 contract expr 全部需要重查 |
| 受影响的其他 slug 的 contract 是否也需要更新 | 共享模块几何接口变化 → 引用该模块的所有 slug contract 都要检查 |

### A0.3 执行

改动完成后，直接跳到 **A4 三层验证**（受影响的每个 slug 依次执行），通过后跳 **A5.5 commit**。  
不需要重走 A1 / A2 / A3。

---

## A1 — 数据收集

**目标**：建模前拿到准确的几何参数 + 可追溯的数据来源。严禁凭记忆估数字。

### A1.0 拓扑识别（全新类型的起点，已知类型可跳过直达 A1.1）

> 当零件不在 A1.1 已知类型表里时，从这里开始。  
> 目标：用四个问题推导出"需要收集什么"和"contract 需要写什么"，再去查数据源。

**四问法**（依次回答，每个问题的答案直接对应后续收集项和 contract 内容）：

| # | 问题 | 答案对应的收集项 | 答案对应的 contract 内容 |
|---|------|----------------|------------------------|
| Q1 | 这个零件是单体还是复合体（多个独立实体）？ | 单体 → 无需 compound 字段；复合 → 每个子件的名称和大致体积占比 | `compound_structure` 的子件列表和 `volume_pct_min` |
| Q2 | 用**机械师语言**写出建模操作序列（例："取外径圆柱 → 车内孔 → 磨滚道沟槽 → 放滚珠 → 安保持架"）。布尔减料操作**从序列里自然浮现**，不要直接问"有哪些减料" | 序列里每个"减料"步骤对应一个几何尺寸（沟槽半径 / 孔径 / 齿槽深）和一个"可达条件"（刀具必须进得去） | `geometry_invariants` 的 reachability 类 expr |
| Q3 | 有没有**标准公式关系**（螺纹小径公式 / 齿轮模数公式 / 球径比例）？ | 公式里的每一个参数 | `geometry_invariants` 的 formula 类 expr |
| Q4 | 完工后视觉上应该看到哪些**可辨认特征**（孔 / 槽 / 齿 / 滚珠）？ | 截图时应能看到的关键特征及其可见视角 | `visual_features` 列表 |

**举例（遇到一个从未见过的"凸轮轴颈"）**：

```
Q1 → 单体 → compound_structure: null
Q2 → 有键槽（矩形减料） → 需要 slot_width / slot_depth；reachability: slot_depth < shaft_r
Q3 → 轴径对应 ISO 286 配合公差 → 需要 nominal_d, tolerance_class
Q4 → 侧面可见矩形键槽，两端可见倒角
→ 收集：nominal_d, slot_w, slot_depth, tolerance_class
→ contract: 1条 reachability invariant + 1条 visual_feature
```

四问完成后进入 A1.1 确认所属标准（或标注"无标准，市场惯例"），再进 A1.2 查数据。

---

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

### A1.3.1 内部几何参数（有非平凡内部几何的类型必须额外收集）

> **判断标准**：零件内部有布尔减料特征（沟槽 / 齿形 / 球窝 / 螺旋线 / 空腔），  
> 且这些特征**不能由包络尺寸唯一推导**，需要制造商技术文档才能确认 → 必须收集。  
> 螺丝/螺母/垫圈虽无复杂内腔，但有 ISO 公式不变式（小径公式 / 六角外接圆关系 / 沉孔可达条件），  
> 须写 contract（参见 A2.4 螺丝类 contract 模板），不得标注 `[skip]`。

| 零件类型 | 必须额外收集的内部几何参数 | 推荐数据源 |
|---------|--------------------------|-----------|
| **深沟球轴承**（ball / mr / flanged） | `d_ball_mm`（钢球直径）、`n_balls`（滚珠数） | ISO 3290（钢球系列）+ SKF/NSK 技术目录 |
| **角接触球轴承** | 同上 + `contact_angle_deg` | SKF 目录 |
| **圆柱滚子轴承** | `d_roller_mm`、`l_roller_mm`、`n_rollers` | SKF 目录 |
| **直线轴承**（LM 系列） | `n_circuit`（滚珠列数）、`ball_dia_mm` | INA/THK 技术文档 |
| **标准舵机** | `shaft_spline_teeth`、`output_shaft_d` | 厂商 datasheet |
| **正齿轮 / 斜齿轮** | `m`（模数）、`z`（齿数）、`pressure_angle_deg` | ISO 54 / KHK 目录 |
| **同步带轮** | `teeth`、`pitch_mm`（GT2/GT3/T5）、`belt_width_mm` | Gates / KHK 目录 |

**收集要求**：
- 优先来源：ISO 标准（confidence 5）或制造商技术文档（confidence 4）  
- 只能找到 confidence ≤ 3 时：在 YAML `geometry` 节加 `[unverified]` 标注  
- 完全无法获取（非公开专有尺寸）：在 YAML 注明 `geometry: null  # proprietary`，A4 Layer 2 自动降级 WARN

### A1.4 产出报告

> **不产生中间 Markdown 表格**——直接输出草稿 YAML，数据来源以注释写在字段旁。  
> 用户确认草稿后即进入 A2（改字段值），无需再手动转录一次。

```yaml
# ── 草稿 YAML（用户确认后直接复制进 fasteners.yaml）──
M4_ISO7380:
  standard: "ISO 7380"
  type: button-head-socket-screw
  thread:
    d: 4.0        # ISO 7380 Table 1, confidence=5
    pitch: 0.70   # ISO 7380 Table 1, confidence=5
    unit: mm
  head:
    dk: 7.6       # bossard.com/ISO7380-M4, confidence=5
    k: 2.2        # bossard.com/ISO7380-M4, confidence=5
    s: 2.5        # bossard.com/ISO7380-M4, confidence=5
  source:
    primary: https://www.bossard.com/...
    confidence: 5
    last_verified: 2026-04-30
  # geometry（有内部几何的类型）：
  # d_ball_mm: 3.969  # ISO 3290 G20, confidence=5
  # n_balls: 9        # NSK catalog p.12, confidence=4
```

用户只需回复「OK」或「改 dk=7.5」——不需要读表格再想 YAML 怎么写。  
有任何 `[unverified]` 字段：在该行末尾注释 `# [unverified] 来源: ...`，进入 A2 后同步到 `notes`。

### ✋ [dave-gate D0 + D1]（进 A2 前必须通过）

```bash
# D0：操作序列文档检查（首次新增 slug 时先 --init 生成模板并填写）
python scripts/check_d0_ops.py --slug <slug> --category <cat>

# D1：YAML 内部几何字段完整性检查
python scripts/check_d1_yaml.py \
  --yaml build123d_parts_lib/parts/<cat>/<cat>.yaml \
  --slug <slug> --model <代表型号> \
  --contract build123d_parts_lib/parts/<cat>/contracts/<slug>_contract.yaml
```

两个检查均 PASS 后进入 A2。D0 FAIL → 补填 `d0/<slug>_ops.yaml`；D1 FAIL → 回 A1.2 补查缺失字段。

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

### A2.4 Contract 文件（所有标准件必须）

**文件路径约定**：

```
parts/<category>/contracts/<slug>_contract.yaml
```

例：
```
parts/bearings/contracts/ball_bearing_contract.yaml
parts/bearings/contracts/mr_bearing_contract.yaml
parts/servos/contracts/standard_servo_contract.yaml
parts/transmission/contracts/spur_gear_contract.yaml
```

**何时新建 / 何时复用**：

| 情况 | 操作 |
|------|------|
| 该 slug 已有 contract | 直接复用，**不修改**（型号变化不影响结构约束） |
| 新 slug，有内部几何 | 必须新建，进入 A3 之前完成 |
| 新 slug，纯外形件（螺丝 / 螺母 / 垫圈） | 必须新建 ISO 公式 contract（见下方螺丝类模板） |

**Contract 内容说明**：描述**结构性约束**，不含型号尺寸数值（尺寸数值在 YAML 里）。

---

#### 轴承类 contract 模板

```yaml
# ball_bearing_contract.yaml
slug: ball_bearing
part_class: deep-groove-ball-bearing

# Compound 子件结构（对应 compound_check.py COMPOUND_SCHEMAS）
compound_structure:
  outer_ring:    {volume_pct_min: 15}
  inner_ring:    {volume_pct_min: 8}
  cage:          {volume_pct_min: 3}
  ball_prefix:   "ball_"
  ball_count:    {min: 6, max: 20}

# 视觉特征约束（Claude Vision 对照检查）
visual_features:
  - name: inner_groove
    description: "外圈内侧和内圈外侧各有一道环形沟槽"
    required: true
    views: [FRONT, RIGHT]          # 必须在这几个视角可见

  - name: balls_visible
    description: "截面或透视可见均匀分布的滚珠"
    required: true
    views: [ISO, TOP]

  - name: cage_structure
    description: "保持架网格结构可见"
    required: false                # 遮挡时可豁免，降为 WARN
    views: [ISO]

# 几何不变式：A1 数据收集后在此处写定，A3 工厂函数据此实现 Python 断言
# 格式：description（人读）+ expr（Python g-dict 表达式，工厂函数直接对应）
geometry_invariants:
  - description: "外圈内壁必须在滚道环面覆盖范围内（沟槽布尔减料可达）"
    expr: "g['r_outer_inner'] < g['r_pc'] + g['r_groove']"
  - description: "内圈外壁必须在滚道环面覆盖范围内"
    expr: "g['r_inner_outer'] > g['r_pc'] - g['r_groove']"
  - description: "滚珠直径必须小于径向间隙"
    expr: "g['d_ball'] < g['r_o'] - g['r_i']"
```

> **`geometry_invariants.expr` 的作用**：A3 工厂函数里的 `_assert_geometry_invariants(g)` 必须覆盖每一条 `expr`。  
> Contract 是规格，Python 断言是实现。二者不得静默分叉——A3 改断言必须同步核对 contract 里的 expr。

---

#### 舵机类 contract 模板

```yaml
# standard_servo_contract.yaml
slug: standard_servo
part_class: rc-servo

compound_structure:
  body:          {volume_pct_min: 40}
  output_shaft:  {volume_pct_min: 1}
  optional_exact: [connector, screws]

visual_features:
  - name: output_shaft
    description: "顶面可见输出轴，带花键或齿形"
    required: true
    views: [TOP, ISO]

  - name: body_rectangular
    description: "主体为长方体外壳，尺寸比例符合 L×W×H 规格"
    required: true
    views: [FRONT, RIGHT]

geometry_invariants:
  - description: "输出轴直径必须小于主体短边宽度"
    expr: "g['shaft_d'] < g['body_w']"
```

---

#### 正齿轮类 contract 模板

```yaml
# spur_gear_contract.yaml
slug: spur_gear
part_class: spur-gear

compound_structure: null           # 单体 Part，无 Compound 子件

visual_features:
  - name: tooth_profile
    description: "侧面可见均匀渐开线齿形，齿数可数"
    required: true
    views: [FRONT, ISO]

  - name: bore_hole
    description: "中心通孔可见"
    required: true
    views: [TOP]

geometry_invariants:
  - description: "齿顶圆直径符合模数标准公式"
    expr: "abs(g['d_tip'] - g['m'] * (g['z'] + 2)) < 0.01"
  - description: "齿根圆直径符合标准全齿高"
    expr: "abs(g['d_root'] - g['m'] * (g['z'] - 2.5)) < 0.01"
```

---

#### 螺丝类 contract 模板（slug=screw_socket_head，其他头型同理）

```yaml
# screw_socket_head_contract.yaml
slug: screw_socket_head
part_class: socket-head-cap-screw

compound_structure: null           # 单体 Part，无 Compound 子件

visual_features:
  - name: hex_socket
    description: "顶面可见内六角凹槽，六棱清晰，深度合理"
    required: true
    views: [TOP, ISO]

  - name: external_thread
    description: "杆部侧面可见外螺纹锯齿纹路"
    required: true
    views: [FRONT, RIGHT]

  - name: head_chamfer
    description: "头部底边有过渡倒角"
    required: false
    views: [FRONT]

geometry_invariants:
  - description: "螺纹小径符合 ISO 公式 r_minor = (d - 1.2269*pitch)/2"
    expr: "abs(g['r_minor'] - (g['d'] - 1.2269*g['pitch'])/2) < 0.01"
  - description: "内六角对边宽必须小于头外径（扳手可进入）"
    expr: "g['s'] < g['dk']"
  - description: "沉孔直径必须大于头外径（螺丝可沉入）"
    expr: "g['counterbore_d'] > g['dk']"
```

> **螺母 / 垫圈** 同理：螺母写六角不变式（`g['r_hex'] ≈ g['s'] / sqrt(3)`）；垫圈写内径可达条件（`g['d_inner'] > g['d_thread']`）。

---

**YAML 语法验证**：

```bash
python3 -c "
import yaml
path = 'build123d_parts_lib/parts/<category>/contracts/<slug>_contract.yaml'
yaml.safe_load(open(path).read())
print('Contract YAML OK')
"
```

验证通过后进入 A2.5。

---

## A2.5 — g-dict 接口定义（有 `geometry_invariants` 的类型必须）

> **目的**：`contract.yaml geometry_invariants[*].expr` 里的 `g['key']` 必须来自工厂函数定义的 g-dict。  
> **顺序要求**：先定义 g-dict 接口 → 再写 contract expr → 再写 Python 断言——三者一条链，不分叉。

### 操作

在 factory 文件（或共享几何模块）里，用 TypedDict 或 docstring 明确记录 `_compute_xxx_geometry()` 的返回 dict：

```python
# 选项 A：TypedDict（推荐，IDE 自动补全 + 类型检查）
from typing import TypedDict

class BearingGeometry(TypedDict):
    r_o:           float  # 外圈外半径 = D/2
    r_i:           float  # 内孔半径 = d/2
    r_pc:          float  # 节圆半径 = (r_o + r_i) / 2
    r_groove:      float  # 沟槽管半径 ≈ d_ball/2 × 1.07
    r_outer_inner: float  # 外圈内壁半径（ring_wall_offset 决定）
    r_inner_outer: float  # 内圈外壁半径
    d_ball:        float  # 钢球直径（来自 YAML 或比例估算）
    n_balls:       int    # 滚珠数

# 选项 B：docstring（最少改动，不依赖 typing）
def _compute_bearing_geometry(d, D, B, d_ball=None, n_balls=None) -> dict:
    """Returns dict with keys:
      r_o, r_i, r_pc, r_groove, r_outer_inner, r_inner_outer, d_ball, n_balls
    """
    ...
```

### 一致性检查（新建 contract 后运行一次）

```bash
# 从 contract YAML 提取 expr 引用的所有 g-dict key，对比 TypedDict/docstring
python3 -c "
import yaml, re
contract = yaml.safe_load(open('parts/bearings/contracts/ball_bearing_contract.yaml'))
keys = set(re.findall(r\"g\['(\w+)'\]\", ' '.join(
    inv['expr'] for inv in contract.get('geometry_invariants', []))))
print('contract 引用的 g-dict key:', keys)
# 手工对照 TypedDict 字段，确认每个 key 都有定义
"
```

完成后进入 A3。

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
# ⚠️ 内部几何字段（d_ball_mm / n_balls 等）从比例估算时必须打印 WARNING，不得静默降级：
#    import warnings
#    warnings.warn(
#        f"[FALLBACK] {slug}: d_ball_mm not in YAML, using ratio estimate {d_ball:.3f} mm."
#        " 请在 YAML geometry 节补充此值以消除警告。",
#        stacklevel=3,
#    )
def _load_specs() -> dict[str, MyPartSpec]:
    # ... 读 fasteners.yaml，过滤 type == "my-type-tag"
    # ... 对每个 size 建 MyPartSpec
    # ... 用 _FALLBACK 补全缺失 key，内部几何字段补全时发出 WARNING
    ...

_SPECS = _load_specs()

# 层 4：公开工厂函数
def make_my_part(size: str = "M4") -> Part:
    spec = _SPECS[size.upper().strip()]
    # ... 建模（选 Pattern 13/14/15）
    return part

# 层 5：几何不变式（Single Truth）
#
# GEOMETRY_INVARIANTS 是约束的**唯一真相**——Python lambda 是权威定义。
# contract.yaml geometry_invariants[*].expr 从本列表派生（文档用），不独立维护。
# 增删约束：只改本列表 → 同步更新 contract YAML 的 expr 字段 → 不需要同时改两处 assert。
# 禁止 try/except 吞断言；断言失败直接中止，不导出 STEP。
#
# ── 深沟球轴承示例 ──────────────────────────────────────────────────────
GEOMETRY_INVARIANTS = [
    # (描述文本,                              test lambda)
    ("外圈内壁必须在滚道环面覆盖范围内",
     lambda g: g["r_outer_inner"] < g["r_pc"] + g["r_groove"]),
    ("内圈外壁必须在滚道环面覆盖范围内",
     lambda g: g["r_inner_outer"] > g["r_pc"] - g["r_groove"]),
    ("滚珠直径必须小于径向间隙",
     lambda g: g["d_ball"] < g["r_o"] - g["r_i"]),
]

def _assert_geometry_invariants(g: dict) -> None:
    for desc, test in GEOMETRY_INVARIANTS:
        assert test(g), f"Invariant FAIL: {desc}\n  g={g}"
#
# ── 齿轮示例 ────────────────────────────────────────────────────────────
# GEOMETRY_INVARIANTS = [
#     ("齿顶圆直径符合标准公式",
#      lambda g: abs(g["d_tip"] - g["m"] * (g["z"] + 2)) < 0.01),
#     ("齿根圆直径符合标准全齿高",
#      lambda g: abs(g["d_root"] - g["m"] * (g["z"] - 2.5)) < 0.01),
# ]

# 层 6：独立运行块（必须）
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

> ⚠️ **螺纹必须先查工具函数，禁止重新推导**
>
> | 场景 | 正确用法 |
> |------|---------|
> | 外螺纹螺杆 | `make_external_thread(d, pitch, L)` → `fuse` 到杆 |
> | 内螺纹（贯通/盲孔） | `make_internal_thread(d, pitch, length)` → `cut` 实体 |
>
> 查 `_thread_utils.py` 是 A3 的**第 0 步**，未查就推导 Helix / V槽公式 = 违规，立即停止推导，改为 `from ._thread_utils import ...`。

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

### ✋ [dave-gate D2]（进 A4 前必须通过）

```bash
# D2：代码结构检查（GEOMETRY_INVARIANTS / assert 结构 / fallback warning）
python scripts/check_d2_code.py build123d_parts_lib/parts/<cat>/<module>.py
```

PASS 后进入 A4。FAIL 时修复对应条目（见输出的 ✗ 行），不得绕过进验证层。

---

### A3.5 踩坑清单（必查）

- [ ] **有内部几何的类型**：`make_xxx()` 末尾必须调用 `_assert_geometry_invariants(g)`；断言失败即报错，不得用 `try/except` 吞掉
- [ ] 边过滤容差用 `0.1–0.5 mm`，**绝对不能用 `1e-3`**（OCC fuse 后顶点坐标有浮动）
- [ ] 翼片 / 凸台 Z 锚点从 `z=0`（底面）开始，不是顶面 → `z_center = feature_h / 2`
- [ ] `make_internal_thread` 已含中心圆柱，直接 `cut`，无需先打预孔；盲孔 `depth ≤ total_h`
- [ ] `RegularPolygon(radius=r)` 中 `r` 是**外接圆半径**（顶点到中心），对边宽 `s → r = s / math.sqrt(3)`
- [ ] 同一 `BuildPart` 内混合 `Cylinder` + `RegularPolygon extrude` 可能不稳定 → 分开建再 fuse
- [ ] `fillet` / `chamfer` 的 `if edges:` 保护：过滤结果为空时静默跳过，不会报错

---

## A4 — 三层验证

**顺序**：Layer 0 通过 → Layer 1 通过 → Layer 2 通过。任一层失败先修复再往下。

> ⛔ **入库门控（强制）**：Layer 2 `verify_standard_part()` 必须返回 `verdict=PASS` 才能进入 A5 入库。
> WARN 需用户明确确认；FAIL 必须修复至 PASS，**不得绕过直接提交**。

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

### Layer 2 — 视觉规格验证（**所有有 YAML 规格文件的标准件，无豁免**）

> **强制执行**：所有新增标准件（轴承 / 密封件 / 螺丝 / 螺母 / 舵机 / 销轴 / 传动件等），
> 只要有 YAML 规格文件，**必须**调用 `verify_standard_part()`，不得以"非 Compound"为由跳过。
> Compound 类会自动做子件检查；非 Compound 类（Part）跳过子件检查，但 7 视角截图 + AI Vision 评估**仍须执行**。

**调用方式（Python）**：

```python
import sys
sys.path.insert(0, "/Users/liyijiang/.agents/skills/cad-vision-verify/scripts")
from verify_loop import verify_standard_part

# 示例：轴承（Compound，有 contract）
from build123d_parts_lib.parts.bearings.ball_bearing import make_ball_bearing
solid = make_ball_bearing("608ZZ")

result = verify_standard_part(
    solid         = solid,
    slug          = "ball_bearing",
    model         = "608ZZ",
    yaml_path     = "build123d_parts_lib/parts/bearings/bearings.yaml",
    contract_path = "build123d_parts_lib/parts/bearings/contracts/ball_bearing_contract.yaml",
    verify_temp   = "./verify_temp",
)
print(result["verdict"])   # PASS / WARN / FAIL

# 示例：O 型圈（Part，纯外形件，无 contract）
from build123d_parts_lib.parts.seals.oring import make_oring
solid = make_oring(d1=40.0, d2=2.0)

result = verify_standard_part(
    solid         = solid,
    slug          = "oring",
    model         = "OR_40x20",
    yaml_path     = "build123d_parts_lib/parts/seals/oring.yaml",
    contract_path = None,              # 纯外形件：显式传 None，跳过 visual_features 检查
    verify_temp   = "./verify_temp",
)
print(result["verdict"])
```

**`contract_path` 降级规则**：

| 情况 | 效果 |
|------|------|
| `contract_path` 指向已存在的文件 | 读取 `visual_features` 列表，作为 Claude Vision 评分依据 |
| `contract_path=None`（显式跳过） | 仅凭 YAML 包络尺寸生成临时 auto_contract，正常评分 |
| `contract_path` 指向不存在的文件 | 直接 **FAIL**；日志输出 `[CONTRACT_MISSING] <path> not found — 请先完成 A2.4` |

> ⛔ **第三种情况是硬性门控**：contract 文件缺失 = FAIL，无法进入 A5。  
> 质量门要么立，要么不立。WARN 不是门——它只是把问题推迟到下一个人发现。

**调用方式（CLI）**：

```bash
python3 /Users/liyijiang/.agents/skills/cad-vision-verify/scripts/verify_loop.py \
  --mode standard-part \
  --slug ball_bearing \
  --model 608ZZ \
  --yaml build123d_parts_lib/parts/bearings/bearings.yaml \
  --contract build123d_parts_lib/parts/bearings/contracts/ball_bearing_contract.yaml \
  --verify-temp ./verify_temp
```

**验证内容**（自动执行）：
1. **Contract 视觉特征约束**（`visual_features` 逐条）→ 有文件时加载，无文件时用 YAML 自动生成
2. Compound 子件检查（外圈/内圈/保持架/滚珠数量）—— 仅 Compound 类执行，Part 类自动跳过
3. 7 视角截图（ISO/FRONT/BACK/TOP/BOTTOM/RIGHT/LEFT）→ `verify_temp/<session>/` —— **所有类型必须执行**
4. Claude Vision 对照 contract 规格评估 → `overall_score` —— **所有类型必须执行**
5. FAIL 时输出 ≤ 3 条量化诊断（fix_size S/M/L，含具体 fix_action）

**判定阈值**：score ≥ 80 → PASS；60–79 → WARN；< 60 → FAIL

**修复上限**：FAIL 最多 2 轮视觉修复（`MAX_FIX_ROUNDS["layer2"] = 2`）

---

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
规格：M3 / M4 / M5   （轴承用型号名，如 608ZZ）

Layer 0 — 导出：
  <tag>.step  vol=XXX mm³  ✅

Layer 1 — 视觉（VTK 离屏）：
  预览：cache/<slug>.png
  外形正确 ✅ | 关键特征：<逐条列出> ✅

Layer 2 — 视觉规格验证（所有有 YAML 规格的标准件，无豁免）：
  contract: parts/<cat>/contracts/<slug>_contract.yaml ✅ / [skip]纯外形件 / ❌ 缺失→FAIL
  verdict=PASS  score=XX/100  子件检查=✅（Compound）/ N/A（Part）
  session: verify_temp/<ts>_<slug>_<model>/
  ⛔ verdict ≠ PASS 不得进入 A5
  ⛔ contract 缺失且有内部几何 → verdict=FAIL，禁止进入 A5

Layer 2 — Cache 集成：
  scripts/build_cache.py 全部 ✅（代表规格 1 step + 1 png）

数据来源：<source.primary>（confidence=N，last_verified=YYYY-MM-DD）
──────────────────────────────────────────
```

---

## A5 — 入库收尾

**目标**：A4 三层验证全部通过后，把新件型正式写入索引、文档、技能数据源，并提交两个 repo。

> A5 是强制步骤，不能跳过。未完成 A5 = 零件只在本机，其他人拿不到。
>
> ⛔ **前置条件**：A4 Layer 2 `verdict=PASS`（或 WARN 经用户确认）才可开始 A5。
> 未跑 Layer 2 / verdict=FAIL 时，**禁止执行任何 A5 步骤**，必须先修复至 PASS。

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
