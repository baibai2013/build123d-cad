# Layer 1：合同验证算法

> Layer 0 是"写合同"，Layer 1 是"验合同"——建模代码跑完后，自动检查产出物是否满足每一条约束。

合同规范见 `references/verify/layer0-contract.md`。

---

## 1. 验证流水线架构

```
建模代码输出 solid (BRep)
         ↓
    ┌────────────────────────┐
    │  Layer 1 验证流水线     │
    │                        │
    │  Stage A: 基础体检      │  ← BRep 有效？单体？体积合理？
    │       ↓ PASS            │
    │  Stage B: 尺寸指纹      │  ← dims + _ratios 对不对？
    │       ↓ PASS            │
    │  Stage C: 空间约束      │  ← 每条 constraint 逐一验证
    │       ↓ PASS            │
    │  Stage D: STEP 精度     │  ← 导出再导入，体积偏差 < 0.1%
    │       ↓                 │
    │  综合判定 + 修复建议     │
    └────────────────────────┘
         ↓
    PASS → 进入用户选择变体
    FAIL → 自动修复循环（最多 3 轮）
```

**Stage A/D 是现有验证**（BRep + STEP），**Stage B/C 是新增核心**。

任何 Stage 不过 → 后续不跑，直接报失败位置和修复建议。

---

## 2. Stage A：基础体检

复用已有的三层验证前两层，无变化：

```python
def stage_a(solid, contract):
    """BRep 有效性 + 包围盒 + 单体检查"""
    label = contract["meta"]["product"]
    body = contract["meta"]["body_ref"]
    
    assert solid is not None,       f"{label}: solid is None"
    assert solid.is_valid,          f"{label}: BRep invalid"
    assert len(solid.solids()) == 1, f"{label}: expected 1 solid, got {len(solid.solids())}"
    
    bb = solid.bounding_box()
    # 壳体/配件外尺寸应大于基准体
    assert bb.size.Y > body["L"], f"{label}: Y too short ({bb.size.Y:.2f})"
    assert bb.size.X > body["W"], f"{label}: X too narrow ({bb.size.X:.2f})"
    
    return {"status": "PASS", "bbox": (bb.size.X, bb.size.Y, bb.size.Z)}
```

---

## 3. Stage B：尺寸指纹验证

从代码参数（通过 param_map 映射）读取每个特征的实际尺寸，与合同 dims 比对。

### 特征提取策略

**不做 BRep 特征识别**（太复杂），改为**参数回溯**——通过 `param_map` 直接从建模代码变量映射到合同字段：

```yaml
# 合同中的映射表
param_map:
  camera_cutout.w:   CAM_W       # 代码中的变量名
  camera_cutout.h:   CAM_H
  camera_cutout.r:   CAM_R
  camera_cutout.cx:  CAM_CX
  camera_cutout.cy:  CAM_CY
  volume_btn.w:      VOL_LEN
  volume_btn.from_top: VOL_DY
  # ...
```

### 比对算法

```python
def stage_b(contract, code_params):
    """尺寸指纹：绝对值 + 归一化比例"""
    body = contract["meta"]["body_ref"]
    results = []
    
    for feature in contract["features"]:
        name = feature["name"]
        errors = []
        
        # 绝对尺寸比对
        for dim_key, expected in feature["dims"].items():
            if dim_key.startswith("_"):
                continue
            actual = code_params.get(f"{name}.{dim_key}")
            if actual is None:
                errors.append({"param": dim_key, "status": "MISSING"})
                continue
            
            err_rel = abs(actual - expected) / expected if expected != 0 else abs(actual)
            errors.append({
                "param": dim_key,
                "expected": expected,
                "actual": actual,
                "err_rel": err_rel,
                "status": "PASS" if err_rel < 0.05 else
                          "WARN" if err_rel < 0.15 else "FAIL"
            })
        
        # 比例检查
        if "_ratios" in feature["dims"]:
            for rk, rv in feature["dims"]["_ratios"].items():
                actual_r = compute_ratio(code_params, name, rk, body)
                err = abs(actual_r - rv)
                errors.append({
                    "param": f"ratio:{rk}",
                    "expected": rv,
                    "actual": actual_r,
                    "err_abs": err,
                    "status": "PASS" if err < 0.03 else
                              "WARN" if err < 0.08 else "FAIL"
                })
        
        worst = max((e["status"] for e in errors if "status" in e),
                    key=lambda s: {"PASS":0,"WARN":1,"FAIL":2,"MISSING":3}[s],
                    default="PASS")
        results.append({"feature": name, "dims": errors, "status": worst})
    
    return results
```

### Stage B 判定阈值

| 误差范围 | 判定 | 说明 |
|---------|------|------|
| err_rel < 5% | PASS | 在容差内 |
| 5% ≤ err_rel < 15% | WARN | 可接受但提示 |
| err_rel ≥ 15% | FAIL | 需要修正 |

### 输出示例

```
=== Stage B: Dimension Fingerprint ===

camera_cutout
  w:      38.0 ≈ 38.0  err=0.0%   PASS
  h:      38.0 ≈ 38.0  err=0.0%   PASS
  r:       8.0 ≈  8.0  err=0.0%   PASS
  ratio:aspect  1.00 ≈ 1.00       PASS
  ratio:w_over_W 0.502 ≈ 0.502    PASS

volume_btn
  w:      24.0 ≈ 24.0  err=0.0%   PASS
  h:       4.0 ≈  4.0  err=0.0%   PASS

Stage B: 7/7 PASS | 0 WARN | 0 FAIL
```

---

## 4. Stage C：空间约束验证（核心新增）

逐条遍历合同中每个特征的 constraints，计算误差。

### 约束评估器

每种约束类型一个评估函数，返回 `{status, error, detail}`：

```python
class ConstraintEvaluator:
    
    def __init__(self, contract, code_params, solid):
        self.contract = contract
        self.params = code_params
        self.solid = solid
        self.body = contract["meta"]["body_ref"]
        self._build_pos_cache()
    
    def _build_pos_cache(self):
        """预算每个特征的中心位置"""
        self._pos = {}
        for f in self.contract["features"]:
            name = f["name"]
            self._pos[name] = {
                "cx": self.params.get(f"{name}.cx", 0),
                "cy": self.params.get(f"{name}.cy", 0),
                "from_top": self.params.get(f"{name}.from_top"),
                "face": f["face"],
            }
    
    def evaluate(self, feature, constraint):
        """路由到对应评估函数"""
        fn = getattr(self, f"_eval_{constraint['type']}", None)
        if fn is None:
            return {"status": "SKIP", "error": 0, "detail": f"unknown: {constraint['type']}"}
        return fn(feature, constraint)
```

### 各约束类型评估逻辑

#### on_face — 面归属检查

```python
def _eval_on_face(self, feature, c):
    ok = (feature["face"] == c["value"])
    return {"status": "PASS" if ok else "FAIL", "error": 0 if ok else 1.0,
            "detail": f"face={feature['face']}, expected={c['value']}"}
```

#### offset — 轴向偏移

```python
def _eval_offset(self, feature, c):
    if c["value"] == "side_center":
        return {"status": "PASS", "error": 0, "detail": "side_center (structural)"}
    actual = self._get_axis_value(feature["name"], c["axis"])
    err = abs(actual - c["value"])
    tol = c.get("tol", 2.0)
    return {"status": "PASS" if err <= tol else "WARN" if err <= tol*2 else "FAIL",
            "error": err, "detail": f"axis={c['axis']} actual={actual:.1f} expected={c['value']} ±{tol}"}
```

#### edge_dist — 边距

```python
def _eval_edge_dist(self, feature, c):
    ref, expected, tol = c["ref"], c["value"], c.get("tol", 2.0)
    pos = self._pos[feature["name"]]
    
    if ref == "top":
        actual = self.body["L"]/2 - (pos.get("cy") or (self.body["L"]/2 - pos.get("from_top", 0)))
    elif ref == "bottom":
        actual = self.body["L"]/2 + pos.get("cy", 0)
    elif ref == "left":
        actual = self.body["W"]/2 + pos.get("cx", 0)
    elif ref == "right":
        actual = self.body["W"]/2 - pos.get("cx", 0)
    
    err = abs(actual - expected)
    return {"status": "PASS" if err <= tol else "WARN" if err <= tol*2 else "FAIL",
            "error": err, "detail": f"dist_to_{ref}={actual:.1f} expected={expected:.1f} ±{tol}"}
```

#### centered — 居中检查

```python
def _eval_centered(self, feature, c):
    plane, tol = c["plane"], c.get("tol", 1.0)
    pos = self._pos[feature["name"]]
    err = abs(pos.get("cx", 0)) if plane == "XZ" else abs(pos.get("cy", 0))
    return {"status": "PASS" if err <= tol else "FAIL",
            "error": err, "detail": f"centered on {plane}, offset={err:.1f} ±{tol}"}
```

#### ordering — 排列顺序

```python
def _eval_ordering(self, feature, c):
    axis, sequence = c["axis"], c["sequence"]
    values = []
    for fname in sequence:
        pos = self._pos[fname]
        if axis == "Y":
            val = pos.get("cy") or (self.body["L"]/2 - pos.get("from_top", 0))
        else:
            val = pos.get("cx", 0)
        values.append((fname, val))
    
    # Y 轴从上到下 = cy 从大到小；X 轴从左到右 = cx 从小到大
    nums = [v for _, v in values]
    if axis == "Y":
        ok = all(a > b for a, b in zip(nums, nums[1:]))
    else:
        ok = all(a < b for a, b in zip(nums, nums[1:]))
    
    return {"status": "PASS" if ok else "FAIL", "error": 0 if ok else 1.0,
            "detail": f"order({axis}): {[f'{n}={v:.1f}' for n,v in values]}"}
```

#### colinear — 共线对齐

```python
def _eval_colinear(self, feature, c):
    name, target, axis = feature["name"], c["target"], c["axis"]
    tol = c.get("tol", 1.0)
    a = self._pos[name].get("cx" if axis=="X" else "cy", 0)
    b = self._pos[target].get("cx" if axis=="X" else "cy", 0)
    err = abs(a - b)
    return {"status": "PASS" if err <= tol else "FAIL",
            "error": err, "detail": f"{name}.{axis}={a:.1f} vs {target}.{axis}={b:.1f} ±{tol}"}
```

#### inter_dist — 特征间距

```python
def _eval_inter_dist(self, feature, c):
    name, target = feature["name"], c["target"]
    axis, expected, tol = c["axis"], c["value"], c.get("tol", 2.0)
    
    pos_a, pos_b = self._pos[name], self._pos[target]
    dim_a = self.params.get(f"{name}.w", 0)
    
    if axis == "Y":
        top_a = pos_a.get("from_top", 0)
        top_b = pos_b.get("from_top", 0)
        gap = top_b - (top_a + dim_a) if top_a < top_b else top_a - (top_b + self.params.get(f"{target}.w", 0))
    else:
        gap = abs(pos_a.get("cx", 0) - pos_b.get("cx", 0))
    
    err = abs(gap - expected)
    return {"status": "PASS" if err <= tol else "WARN" if err <= tol*2 else "FAIL",
            "error": err, "detail": f"gap({name}↔{target})={gap:.1f} expected={expected:.1f} ±{tol}"}
```

#### same_face — 同面检查

```python
def _eval_same_face(self, feature, c):
    b_face = next(f["face"] for f in self.contract["features"] if f["name"] == c["target"])
    ok = (feature["face"] == b_face)
    return {"status": "PASS" if ok else "FAIL", "error": 0 if ok else 1.0,
            "detail": f"{feature['name']}={feature['face']} vs {c['target']}={b_face}"}
```

#### symmetric_pair — 对称检查

```python
def _eval_symmetric_pair(self, feature, c):
    cx_a = self._pos[feature["name"]].get("cx", 0)
    cx_b = self._pos[c["target"]].get("cx", 0)
    tol = c.get("tol", 3.0)
    err = abs(abs(cx_a) - abs(cx_b))
    sign_ok = (cx_a * cx_b) < 0   # 符号相反
    return {"status": "PASS" if (err <= tol and sign_ok) else "FAIL",
            "error": err, "detail": f"cx={cx_a:.1f} vs {cx_b:.1f} mirror ±{tol}"}
```

#### ratio — 比例检查

```python
def _eval_ratio(self, feature, c):
    actual = self._compute_ratio(feature["name"], c["param"])
    err = abs(actual - c["expected"])
    tol = c.get("tol", 0.05)
    return {"status": "PASS" if err <= tol else "WARN" if err <= tol*2 else "FAIL",
            "error": err, "detail": f"ratio:{c['param']}={actual:.3f} expected={c['expected']:.3f} ±{tol}"}
```

### Stage C 主流程

```python
def stage_c(contract, code_params, solid):
    evaluator = ConstraintEvaluator(contract, code_params, solid)
    results = []
    
    for feature in contract["features"]:
        f_result = {"feature": feature["name"], "constraints": [], "axes_locked": set()}
        
        for c in feature["constraints"]:
            r = evaluator.evaluate(feature, c)
            r["type"] = c["type"]
            if "locks" in c:
                f_result["axes_locked"] |= set(c["locks"])
            f_result["constraints"].append(r)
        
        f_result["xyz_complete"] = f_result["axes_locked"] >= {"X", "Y", "Z"}
        
        statuses = [c["status"] for c in f_result["constraints"]]
        f_result["status"] = "FAIL" if "FAIL" in statuses else "WARN" if "WARN" in statuses else "PASS"
        
        errors = [c["error"] for c in f_result["constraints"] if isinstance(c.get("error"), (int, float))]
        f_result["E_feature"] = sum(errors) / len(errors) if errors else 0
        
        results.append(f_result)
    
    return results
```

### 输出示例

```
=== Stage C: Spatial Constraints ===

camera_cutout    [5 constraints, XYZ ✓]
  on_face:back                              PASS
  edge_dist:top  26.4 ≈ 26.4 ±2.0          PASS  err=0.0
  edge_dist:left 24.9 ≈ 24.9 ±2.0          PASS  err=0.0
  ratio:aspect   1.000 ≈ 1.000 ±0.1        PASS  err=0.000
  ordering:Y     [cam=55, vol=41, pwr=27]   PASS
  ▸ E_feature = 0.000                       ✅ PASS

volume_btn       [5 constraints, XYZ ✓]     ✅ PASS
power_btn        [4 constraints, XYZ ✓]     ✅ PASS
usb_c            [4 constraints, XYZ ✓]     ✅ PASS
speaker          [4 constraints, XYZ ✓]     ✅ PASS
sim_tray         [4 constraints, XYZ ✓]     ✅ PASS
ir_blaster       [3 constraints, XYZ ✓]     ✅ PASS

Stage C: 7/7 PASS | E_total = 0.000
```

---

## 5. Stage D：STEP 精度

复用已有验证，无变化：

```python
def stage_d(solid, step_path):
    export_step(solid, step_path)
    ri = import_step(step_path)
    vd = abs(ri.volume - solid.volume) / solid.volume
    assert vd < 0.001, f"STEP precision loss: {vd:.4%}"
    return {"status": "PASS", "deviation": vd}
```

---

## 6. 综合判定

```python
def layer1_verify(solid, contract, code_params, step_path):
    """Layer 1 完整验证流水线"""
    
    a = stage_a(solid, contract)
    if a["status"] != "PASS":
        return {"verdict": "FAIL", "stage": "A", "detail": a}
    
    b = stage_b(contract, code_params)
    b_fails = [r for r in b if r["status"] == "FAIL"]
    if b_fails:
        return {"verdict": "FAIL", "stage": "B", "failures": b_fails,
                "fix_hints": generate_dim_hints(b_fails)}
    
    c = stage_c(contract, code_params, solid)
    c_fails = [r for r in c if r["status"] == "FAIL"]
    if c_fails:
        return {"verdict": "FAIL", "stage": "C", "failures": c_fails,
                "fix_hints": generate_constraint_hints(c_fails)}
    
    d = stage_d(solid, step_path)
    if d["status"] != "PASS":
        return {"verdict": "FAIL", "stage": "D", "detail": d}
    
    # 全部通过
    c_warns = [r for r in c if r["status"] == "WARN"]
    E_total = sum(r["E_feature"] for r in c) / len(c)
    
    return {
        "verdict": "PASS" if not c_warns else "PASS_WITH_WARN",
        "E_total": E_total,
        "warnings": c_warns,
        "summary": {
            "features": len(c),
            "constraints": sum(len(r["constraints"]) for r in c),
            "all_xyz_complete": all(r["xyz_complete"] for r in c),
        }
    }
```

### 判定阈值

| E_total | 判定 | 动作 |
|---------|------|------|
| < 0.02 | **PASS** | 直接进入变体选择 |
| 0.02 ~ 0.08 | **PASS_WITH_WARN** | 提示偏差，用户决定 |
| 0.08 ~ 0.15 | **WARN** | 建议修正，列出 top-3 偏差 |
| > 0.15 | **FAIL** | 进入自动修复循环 |

---

## 7. 自动修复循环

Stage B 或 C 出现 FAIL 时，尝试贪心调参：

```python
def auto_fix_loop(contract, code_params, build_fn, step_path, max_rounds=3):
    """每轮修正偏差最大的 top-3 参数"""
    
    for round_i in range(max_rounds):
        solid = build_fn(code_params)
        result = layer1_verify(solid, contract, code_params, step_path)
        
        if result["verdict"] in ("PASS", "PASS_WITH_WARN"):
            print(f"Auto-fix: converged in round {round_i + 1}")
            return solid, code_params, result
        
        # 收集 FAIL 约束，按 error 降序取 top-3
        failures = collect_failures(result)
        failures.sort(key=lambda x: x["error"], reverse=True)
        top3 = failures[:3]
        
        print(f"Round {round_i + 1}: fixing top-3 deviations:")
        for fix in top3:
            print(f"  {fix['feature']}.{fix.get('param', fix.get('type'))}  err={fix['error']:.2f}")
            apply_fix(code_params, fix, contract)
    
    print(f"Auto-fix: did not converge after {max_rounds} rounds")
    return solid, code_params, result
```

### 修复策略

| 失败类型 | 修复方法 |
|---------|---------|
| dims FAIL | 将 actual 改为 expected（直接替换） |
| offset/edge_dist FAIL | 调整对应 pos 参数 |
| ordering FAIL | 交换违反顺序的两个参数 |
| symmetric_pair FAIL | 取两者绝对值均值，对称化 |
| ratio FAIL | 按比例缩放 dims 中的源参数 |

---

## 8. 最终报告格式

```
╔══════════════════════════════════════════╗
║     Layer 1 Verification Report          ║
║     Redmi K70 Case — V2_standard         ║
╠══════════════════════════════════════════╣
║  Stage A: Basic Check          ✅ PASS   ║
║  Stage B: Dimension Fingerprint ✅ PASS  ║
║  Stage C: Spatial Constraints   ✅ PASS  ║
║  Stage D: STEP Precision        ✅ PASS  ║
╠══════════════════════════════════════════╣
║  Features:    7/7 PASS                   ║
║  Constraints: 29/29 PASS                 ║
║  XYZ Complete: 7/7                       ║
║  E_total:     0.000                      ║
║  STEP deviation: 0.0003%                 ║
╠══════════════════════════════════════════╣
║  Verdict: ✅ PASS                        ║
║  Auto-fix rounds: 0 (direct pass)        ║
╚══════════════════════════════════════════╝
```

---

## 9. 与现有验证体系的关系

Layer 1 验证是对现有三层验证的**扩展**，不是替换：

| 现有验证 | Layer 1 对应 | 变化 |
|---------|-------------|------|
| Layer 1（语法/执行） | 前置条件 | 不变 |
| Layer 2（几何/BRep） | **Stage A** | 不变，直接复用 |
| Layer 3（语义/尺寸） | **Stage B + C** | 扩展：从简单包围盒断言 → 完整约束验证 |
| STEP 重导入 | **Stage D** | 不变，直接复用 |
| 视觉验证 | Layer 2（未来） | 预留接口 |

验证脚本见 `scripts/validate/contract_verify.py`。
