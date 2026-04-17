# Layer 0：参数合同（Parameter Contract）

> **先写合同，再写代码。合同写错，代码再对也白搭。**

合同是 `params.md` 的机器可读投影，补充了空间约束和容差。建模前锁参数，建模后跑验证。

```
传统 CAD：  工程图标注（GD&T）  →  建模  →  检测
我们的流程：Layer 0 合同       →  建模  →  Layer 1 验证
```

---

## 1. 合同在参考物建模流程中的位置

```
R1 识别产品
R2 搜集资料
R3 生成 params.md
     ↓
 ★ R3.5 Layer 0：生成合同 ★   ← 新增步骤
     ↓
R4 建模（代码参数必须与合同一一对应）
     ↓
 ★ Layer 1：合同验证 ★           ← 自动检查
     ↓
R5 导出交付
```

合同在两个时刻被使用：

| 时刻 | 用途 | 动作 |
|------|------|------|
| **建模前** | 参数锁定 | AI 从 params.md 生成合同 → 用户确认 → 才写代码 |
| **建模后** | 自动验证 | 遍历合同每条约束 → 计算误差 → PASS/WARN/FAIL |

---

## 2. YAML Schema

```yaml
# ===== Layer 0 Parameter Contract =====
# 自动从 params.md 派生 + AI 补充空间约束
# 建模前：用户确认 → 建模后：自动验证

version: "0.1"

# ── 元信息 ──
meta:
  product: string           # 产品名 "Redmi K70 Case"
  type: string              # phone_case | phone_body | bracket | enclosure ...
  body_ref:                 # 基准体尺寸（所有归一化的分母）
    L: float                # 长度 mm（Y 轴）
    W: float                # 宽度 mm（X 轴）
    T: float                # 厚度 mm（Z 轴）
  coord:                    # 坐标约定
    X: width
    Y: length
    Z: thickness
    origin: body_center     # body_center | bottom_left | top_left
  source: string            # "references/<product>/params.md"

# ── 全局参数（非特征参数）──
globals:
  wall_t: {val: 1.5, unit: mm}
  gap: {val: 0.3, unit: mm}
  # ... 工艺参数，变体中可覆盖

# ── 特征清单 ──
features:
  - name: string            # 唯一标识符 snake_case
    type: enum              # 几何类型（见 §3）
    face: enum              # 附着面（见 §4）
    dims: ...               # 自身尺寸（Block 1）
    pos: ...                # 绝对定位（Block 2）
    constraints: [...]      # 空间约束（Block 3，≥ 3 条）

# ── 参数映射（合同字段 ↔ 代码变量名）──
param_map:
  camera_cutout.w: CAM_W
  camera_cutout.cx: CAM_CX
  # ...

# ── 变体覆盖 ──
variants:
  V1_slim:
    overrides: {globals.wall_t: 1.2}
  V2_standard: {}
  V3_rugged:
    overrides: {globals.wall_t: 2.0}
```

---

## 3. 特征几何类型（feature.type）

| type | 描述 | 必需 dims 字段 |
|------|------|---------------|
| `rounded_rect` | 圆角矩形 | `w, h, r` |
| `rect` | 直角矩形 | `w, h` |
| `circle` | 圆形 | `d`（直径） |
| `slot` | 长圆孔/跑道形 | `w, h, end_r` |
| `cylinder` | 圆柱凸台/孔 | `d, depth` |
| `freeform` | 自由轮廓 | `bbox_w, bbox_h`（包围盒近似） |

每个 dims 字段同时携带**绝对值**和**归一化比例**：

```yaml
dims:
  w: 38.0                   # 绝对值 mm
  h: 38.0
  r: 8.0
  _ratios:                  # 自动计算，验证用
    w_over_W: 0.502         # w / body_W
    aspect: 1.0             # w / h
    r_over_w: 0.211         # r / w
```

`_ratios` 由工具自动生成，人不手写。

---

## 4. 附着面（feature.face）

6 个标准面，`face` 本身算一条约束，锁定 1 个平移轴 + 法线朝向：

| face | 法线方向 | 锁定轴 | 手机壳语境 |
|------|---------|--------|-----------|
| `back` | -Z | Z | 壳底面（手机背面朝的方向） |
| `front` | +Z | Z | 屏幕侧开口 |
| `right` | +X | X | 右侧壁 |
| `left` | -X | X | 左侧壁 |
| `top` | +Y | Y | 顶壁（手机听筒端） |
| `bottom` | -Y | Y | 底壁（USB-C 端） |

---

## 5. 约束类型完整目录（constraint.type）

### 5a. 定位约束 — 锁定特征位置

| type | 参数 | locks | 含义 |
|------|------|-------|------|
| `on_face` | `value: back\|front\|...` | 1轴 | 特征在哪个面上 |
| `offset` | `axis: X\|Y\|Z, value: float, tol: float` | 1轴 | 相对 body 中心的偏移量 |
| `edge_dist` | `ref: top\|bottom\|left\|right, value: float, tol: float` | 1轴 | 距指定边的距离 |
| `centered` | `plane: XZ\|YZ\|XY` | 1轴 | 在指定平面上居中（offset=0 的语法糖） |

### 5b. 朝向约束 — 锁定特征方向

| type | 参数 | 含义 |
|------|------|------|
| `normal` | `axis: X\|Y\|Z` | 开孔法线方向 |
| `parallel` | `axis: X\|Y\|Z` | 特征长轴平行于某轴 |

> 注：平面特征（开孔/凸台）的 `on_face` 已隐含 `normal`，一般不需单独写。

### 5c. 特征间约束 — 锁定相对关系

| type | 参数 | 含义 |
|------|------|------|
| `inter_dist` | `target: str, axis: X\|Y, value: float, tol: float` | 两特征沿指定轴的间距 |
| `ordering` | `axis: X\|Y, sequence: [str, str, ...]` | 排列顺序 |
| `colinear` | `target: str, axis: X\|Y\|Z, tol: float` | 两特征在指定轴上对齐 |
| `same_face` | `target: str` | 两特征在同一面上 |
| `symmetric_pair` | `target: str, plane: XZ\|YZ, tol: float` | 两特征关于指定面镜像对称 |
| `concentric` | `target: str, tol: float` | 两特征同心 |

### 5d. 比例约束 — 验证形状合理性

| type | 参数 | 含义 |
|------|------|------|
| `ratio` | `param: str, expected: float, tol: float` | 归一化比例检查 |
| `size_range` | `param: str, min: float, max: float` | 绝对值范围检查 |

---

## 6. 约束完备性规则

合同生成后必须通过的**静态检查**（不需要跑模型）：

```
规则 1：每个特征 ≥ 3 条约束
规则 2：三轴覆盖 — constraints.locks 的并集 ⊇ {X, Y, Z}
规则 3：无矛盾 — 同轴不能有两条冲突约束
         （如 offset_x=10 和 centered:YZ 不能同时存在）
规则 4：dims 完整 — type 要求的 dims 字段不能缺
```

静态检查输出示例：

```
=== Contract Static Check ===
camera_cutout   dims:✅  constraints:5  axes:{X,Y,Z} ✅
volume_btn      dims:✅  constraints:5  axes:{X,Y,Z} ✅
power_btn       dims:✅  constraints:4  axes:{X,Y,Z} ✅
usb_c           dims:✅  constraints:4  axes:{X,Y,Z} ✅
speaker         dims:✅  constraints:4  axes:{X,Y,Z} ✅
sim_tray        dims:✅  constraints:4  axes:{X,Y,Z} ✅
ir_blaster      dims:✅  constraints:3  axes:{X,Y,Z} ✅
Static check: PASS (7/7 features, 29 constraints, 0 conflicts)
```

---

## 7. 合同生成规则（AI 侧）

从 params.md 自动派生合同时 AI 遵循：

| 步骤 | 动作 | 自动/需确认 |
|------|------|-----------|
| 1 | 从 params.md 提取 body_ref + features 列表 | 自动 |
| 2 | 填 dims（直接抄数值） | 自动 |
| 3 | 填 pos（从边距/偏移量转换） | 自动 |
| 4 | 计算 _ratios | 自动 |
| 5 | 补充 constraints（AI 根据产品布局推断） | **需确认** |
| 6 | 生成 param_map（合同字段 ↔ 代码变量名） | 自动 |
| 7 | 跑静态检查（完备性 + 矛盾检测） | 自动 |
| 8 | 输出合同 → 用户确认 | **需确认** |

步骤 5 是 AI 的核心增值点——从产品常识推断空间约束关系（如"USB-C 居中""音量键在电源键上方"）。用户只需要看约束是否合理，不需要自己写 YAML。

---

## 8. 合同 vs params.md

| 维度 | params.md | contract.yaml |
|------|-----------|--------------|
| 面向 | 人类阅读 | 机器验证 |
| 内容 | 原始参数 + 来源 + 置信度 | 参数 + 约束 + 容差 + 归一化比例 |
| 格式 | Markdown 表格 | YAML（可解析） |
| 来源 | 搜集阶段 R2-R3 | 从 params.md 自动派生 + AI 补充约束 |
| 时机 | 人工确认 | 建模后自动验证 |

**params.md 是给人看的，contract.yaml 是给验证算法看的。**

---

## 9. 参考约束理论

合同的约束体系源自传统 CAD 的 3-2-1 定位原则：

- **3 点定面**（消耗 3 DOF：1 平移 + 2 旋转）
- **2 点定线**（消耗 2 DOF：1 平移 + 1 旋转）
- **1 点定位**（消耗 1 DOF：最后 1 个平移）

对于平面特征（开孔/凸台），`on_face` 约束已将其锁定在一个平面上（消耗 3 DOF），剩余只需 2 个面内坐标（X, Y）即完全定位。因此 **3 条约束是最小完备集**。

完整 CAD 约束类型映射：

| 传统 CAD 层级 | 合同中的对应 | 作用 |
|-------------|-------------|------|
| 草图几何约束 | dims._ratios（尺寸比例） | 验证特征形状 |
| 草图尺寸约束 | dims（绝对值） | 验证特征大小 |
| 特征定位约束 | on_face + offset/edge_dist | 验证特征位置 |
| 装配约束 | inter_dist + ordering + colinear | 验证特征间关系 |
| 3-2-1 定位 | 每特征 ≥ 3 约束覆盖 XYZ | 保证位置完全确定 |

---

完整示例合同见 `references/verify/examples/k70-contract.yaml`。

验证算法见 `references/verify/layer1-verification.md`。

验证脚本见 `scripts/validate/contract_verify.py`。
