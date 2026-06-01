# 反馈闭环：验证失败诊断与修复路由

> 验证失败后最关键的问题：**错在哪一层？** 数据源不对？合同写错？还是代码实现错？
>
> 本文件定义根因分类、诊断算法、修复路由和循环上限。

---

## 1. 三种根因

任何验证失败归根到底只有三种原因：

| 根因 | 含义 | 修复对象 | 回到哪 |
|:---:|------|---------|-------|
| **A** | 数据源错误 | params.md 中的数值本身不对 | R2/R3（重新搜集） |
| **B** | 合同错误 | 参数对但约束写错 / 缺失 / 容差太宽 | Layer 0（修改 contract.yaml） |
| **C** | 建模错误 | 合同对但代码实现不对 | 建模代码 |

---

## 2. Layer 1 失败 → 根因判断

| Stage | 失败症状 | 根因 | 修复 |
|-------|---------|:---:|------|
| **A: BRep 无效** | solid is None / invalid / 多体 | C | 修代码（布尔运算/几何操作） |
| **B: 尺寸偏差** | actual ≠ expected | 先查 param_map → 映射对 = **C**（代码变量用错），映射错 = **B**（合同映射写错） | 修代码 或 修合同映射 |
| **B: 尺寸偏差** | 合同和代码一致但都与参考不符 | A | 回 params.md 修数值 |
| **C: on_face 错** | 特征在错误的面上 | C | 修代码切割方向 |
| **C: edge_dist 错** | 位置偏移超容差 | A 或 C | 先确认 params.md，再查代码 |
| **C: ordering 错** | 排列顺序反了 | C | 修代码坐标系正负 |
| **C: symmetric 错** | 对称偏差 | C | 修代码偏移量符号 |
| **D: STEP 偏差** | 重导入体积差 > 0.1% | — | 简化几何（与合同/参数无关） |

### 判断决策树

```
Layer 1 失败
    ↓
Stage A 失败？ ─── YES → 根因 C（代码），修代码
    │ NO
    ↓
Stage B 失败？ ─── YES → 检查 param_map
    │ NO                   ↓
    ↓              映射指向正确变量？
Stage C 失败？      ╱        ╲
    │ NO          YES         NO
    ↓              ↓           ↓
Stage D 失败？   变量值 =     根因 B
    │            合同值？     修合同映射
    ↓            ╱    ╲
  简化几何     YES     NO
              ↓       ↓
          都与参考不符？  根因 C
           ╱    ╲      修代码
         YES    NO
          ↓      ↓
       根因 A   根因 C
       修params  修代码
```

---

## 3. Layer 2 失败 → 根因判断

Layer 2 失败更微妙——"看着不对"的原因更多样：

| 视觉症状 | 根因 | 修复 |
|---------|:---:|------|
| **特征缺失**（图有模型没有） | A+B | 回 R2 补数据 → Layer 0 加特征 + ≥3 约束 |
| **特征多余**（模型有图没有） | A+B | 删 params.md 多余条目 → 删合同特征 |
| **形状类型错**（方变圆） | A | 修 params.md 特征类型描述 |
| **大小不对**（看着太大/小） | A | 修 params.md 数值 |
| **位置不对（Layer 1 过了）** | B | 合同 tol 太宽，收紧容差 |
| **整体比例失调** | A | body_ref 基准尺寸有误，回 R2 确认 |
| **曲面/倒圆不自然** | C | 调代码 fillet/chamfer 参数，不改合同 |

### 关键洞察

> **Layer 2 失败但 Layer 1 通过 → 大概率是根因 A（数据源）或根因 B（约束太松）。**
>
> 因为如果合同约束够紧且数据正确，Layer 1 就能拦住大部分问题。
> Layer 2 "漏网"说明约束覆盖不足或源数据本身就不准。

---

## 4. 诊断算法

```python
def diagnose_failure(layer1_result, layer2_result, contract, code_params):
    """
    根据 Layer 1/2 失败症状，自动判断根因。
    返回: [{root_cause, target, detail, fix_action, severity}]
    """
    diagnoses = []
    
    # ── Layer 1 失败分析 ──
    if layer1_result and layer1_result.get("verdict") == "FAIL":
        stage = layer1_result.get("stage", "")
        
        if stage == "A":
            diagnoses.append({
                "root_cause": "C",
                "target": "建模代码",
                "detail": "BRep 构建失败，检查布尔运算和几何操作",
                "fix_action": "fix_code",
                "severity": "HIGH"
            })
        
        elif stage == "B":
            for f in layer1_result.get("failures", []):
                for d in f.get("dims", []):
                    if d.get("status") == "FAIL":
                        param_key = f"{f['feature']}.{d['param']}"
                        mapped_var = contract.get("param_map", {}).get(param_key)
                        
                        if mapped_var and code_params.get(mapped_var) == d.get("actual"):
                            # 映射正确但值错 → 可能数据源不对
                            diagnoses.append({
                                "root_cause": "A",
                                "target": f"params.md → {param_key}",
                                "detail": f"期望 {d['expected']}，代码 {mapped_var}={d['actual']}",
                                "fix_action": "update_params_md",
                                "severity": "MEDIUM"
                            })
                        else:
                            diagnoses.append({
                                "root_cause": "B",
                                "target": f"contract.param_map.{param_key}",
                                "detail": "param_map 映射不正确或缺失",
                                "fix_action": "fix_contract_mapping",
                                "severity": "MEDIUM"
                            })
        
        elif stage == "C":
            for f in layer1_result.get("failures", []):
                for c in f.get("constraints", []):
                    if c.get("status") == "FAIL":
                        ctype = c.get("type", "")
                        if ctype == "on_face":
                            diagnoses.append({
                                "root_cause": "C",
                                "target": f"代码:{f['feature']}",
                                "detail": f"特征在错误的面上: {c['detail']}",
                                "fix_action": "fix_code_face",
                                "severity": "HIGH"
                            })
                        elif ctype in ("edge_dist", "offset"):
                            diagnoses.append({
                                "root_cause": "A_or_C",
                                "target": f"{f['feature']} position",
                                "detail": c.get("detail", ""),
                                "fix_action": "check_params_then_code",
                                "severity": "MEDIUM"
                            })
                        elif ctype == "ordering":
                            diagnoses.append({
                                "root_cause": "C",
                                "target": f"代码:{f['feature']}",
                                "detail": "排列顺序错误，检查坐标系正负方向",
                                "fix_action": "fix_code_coordinates",
                                "severity": "HIGH"
                            })
    
    # ── Layer 2 失败分析 ──
    if layer2_result and layer2_result.get("verdict") == "FAIL":
        for issue in layer2_result.get("issues", []):
            issue_text = issue.get("issue", "")
            feature = issue.get("feature", "")
            
            if "缺失" in issue_text or "missing" in issue_text.lower():
                diagnoses.append({
                    "root_cause": "A+B",
                    "target": f"params.md + contract: {feature}",
                    "detail": f"特征 {feature} 在参考图中存在但模型中缺失",
                    "fix_action": "add_to_params_and_contract",
                    "severity": "HIGH"
                })
            elif "比例" in issue_text or "proportion" in issue_text.lower():
                diagnoses.append({
                    "root_cause": "A",
                    "target": "params.md → body_ref",
                    "detail": "整体比例不对，检查基准尺寸",
                    "fix_action": "verify_body_dimensions",
                    "severity": "HIGH"
                })
            elif issue.get("position_match") == "poor" or issue.get("position") == "poor":
                diagnoses.append({
                    "root_cause": "B",
                    "target": f"contract: {feature}.constraints.tol",
                    "detail": "Layer 1 通过但视觉位置偏差明显，约束容差过宽",
                    "fix_action": "tighten_constraint_tolerance",
                    "severity": "MEDIUM"
                })
            elif issue.get("shape_match") == "poor" or issue.get("shape") == "poor":
                diagnoses.append({
                    "root_cause": "A",
                    "target": f"params.md → {feature} type/dims",
                    "detail": "特征形状不匹配（如方变圆）",
                    "fix_action": "update_feature_type_in_params",
                    "severity": "HIGH"
                })
    
    # 去重 + 排序
    seen = set()
    unique = []
    for d in diagnoses:
        key = (d["root_cause"], d["target"])
        if key not in seen:
            seen.add(key)
            unique.append(d)
    unique.sort(key=lambda x: {"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(x.get("severity", "LOW"), 2))
    
    return unique
```

---

## 5. 修复路由表

每种 `fix_action` 对应一条完整修复路径：

| fix_action | 回到 | 动作 | 之后 |
|-----------|------|------|------|
| `update_params_md` | R2/R3 | 搜集更可靠数据源，更新 params.md | 重新生成合同 → 建模 → 全流程验证 |
| `fix_contract_mapping` | Layer 0 | 修正 contract.yaml 的 param_map | 静态检查 → 运行时验证 |
| `add_to_params_and_contract` | R2 + Layer 0 | params.md 补特征，合同新增特征 + ≥3 约束 | 全流程：静态 → 建模 → L1 → L2 |
| `tighten_constraint_tolerance` | Layer 0 | 收紧 tol 值（如 3.0→1.5） | Layer 1 重跑（可能触发代码修正） |
| `fix_code` | 建模代码 | 修复布尔运算/几何操作 | 从 Layer 1 开始验证 |
| `fix_code_face` | 建模代码 | 修正切割平面和方向 | 从 Layer 1 开始验证 |
| `fix_code_coordinates` | 建模代码 | 检查坐标系正负，修正偏移量符号 | 从 Layer 1 开始验证 |
| `check_params_then_code` | 先 params.md 再代码 | 确认数值正确 → 确认代码使用正确变量 | 对应层开始验证 |
| `verify_body_dimensions` | R2 | 重新确认 L/W/T，交叉验证多数据源 | 更新 params.md → 重新生成合同 → 全流程 |
| `update_feature_type_in_params` | R2/R3 | 修正特征形状描述（如矩形→正方形） | 更新合同 type/dims → 建模 → 全流程 |

---

## 6. 修复次数上限

防止无限循环：

```python
MAX_FIX_ROUNDS = {
    "layer1": 3,       # Layer 1 自动修复最多 3 轮
    "layer2": 2,       # Layer 2 视觉修复最多 2 轮
    "cross_layer": 2,  # Layer 2 反馈到 Layer 0/1 最多 2 次
    "total": 5,        # 整个验证-修复循环总上限
}
```

达到上限后停止自动修复，输出诊断报告，**交给人工决策**。

---

## 7. 完整验证-修复循环

```python
def verification_loop(solid_fn, contract, code_params, ref_images_dir, output_dir, step_path):
    """
    带上限的完整验证-修复循环。
    solid_fn: 建模函数，接受 code_params 返回 solid
    """
    total_rounds = 0
    
    while total_rounds < MAX_FIX_ROUNDS["total"]:
        solid = solid_fn(code_params)
        
        # Layer 1
        l1 = layer1_verify(solid, contract, code_params, step_path)
        if l1["verdict"] == "FAIL":
            diag = diagnose_failure(l1, None, contract, code_params)
            if not can_auto_fix(diag):
                return report_manual_intervention(l1, None, diag)
            contract, code_params = apply_fixes(diag, contract, code_params)
            total_rounds += 1
            continue
        
        # Layer 2
        mode = decide_layer2_mode(contract, ref_images_dir)
        if mode == "skip":
            return {"verdict": l1["verdict"], "layer1": l1, "layer2": "skipped"}
        
        l2 = layer2_verify(solid, contract, ref_images_dir, output_dir, mode)
        
        if l2.get("verdict") == "MANUAL_REVIEW":
            return {"verdict": "MANUAL_REVIEW", "layer1": l1, "layer2": l2}
        
        if l2.get("verdict") in ("PASS", "SKIP"):
            return {"verdict": "PASS", "layer1": l1, "layer2": l2}
        
        if l2.get("verdict") == "WARN":
            return {"verdict": "PASS_WITH_WARN", "layer1": l1, "layer2": l2,
                    "message": "视觉偏差在可接受范围，用户决定是否继续"}
        
        # Layer 2 FAIL → 诊断 + 反馈
        diag = diagnose_failure(l1, l2, contract, code_params)
        if not can_auto_fix(diag):
            return report_manual_intervention(l1, l2, diag)
        
        contract, code_params = apply_fixes(diag, contract, code_params)
        total_rounds += 1
    
    return {"verdict": "FAIL",
            "message": f"达到修复上限 ({MAX_FIX_ROUNDS['total']} 轮)，需要人工介入"}


def can_auto_fix(diagnoses):
    """判断是否可以自动修复（根因 C 可自动，根因 A 需人工）"""
    for d in diagnoses:
        if d["root_cause"] in ("A", "A+B"):
            return False  # 数据源问题需要人工搜集
    return True
```

---

## 8. 状态机全景图

```
                    ┌──────────────┐
                    │  R2 搜集资料  │◄───── 根因 A（数据源错误）
                    └──────┬───────┘
                           ↓
                    ┌──────────────┐
                    │ R3 params.md │◄───── 根因 A（数值不准）
                    └──────┬───────┘
                           ↓
                ┌────────────────────┐
                │ R3.5 Layer 0 合同  │◄─── 根因 B（约束错/缺/松）
                └────────┬───────────┘
                         ↓
                  ┌──────────────┐
                  │   建模代码    │◄───── 根因 C（代码实现错）
                  └──────┬───────┘
                         ↓
              ┌─────────────────┐
              │   Layer 1 验证   │── FAIL → 诊断根因 → 路由修复
              └────────┬────────┘
                       ↓ PASS
              ┌─────────────────┐
              │   Layer 2 视觉   │── FAIL → 诊断根因 → 路由修复
              └────────┬────────┘
                       ↓ PASS
              ┌─────────────────┐
              │   变体选择导出    │
              └─────────────────┘

    修复次数上限：L1×3 + L2×2 + 跨层×2 = 总计≤5 轮
    超限 → 输出诊断报告 → 人工介入
```

---

## 9. 诊断报告输出格式

```
╔══════════════════════════════════════════════╗
║  Failure Diagnosis Report                     ║
║  Redmi K70 Case — V2_standard                 ║
╠══════════════════════════════════════════════╣
║                                               ║
║  诊断 #1 [HIGH] 根因 A（数据源）              ║
║  位置: params.md → camera_cutout               ║
║  症状: 摄像头模组形状不匹配（矩形 vs 正方形）   ║
║  修复: 回 R2 搜集更清晰参考图                  ║
║        更新 params.md → 重新生成合同 → 全流程    ║
║                                               ║
║  诊断 #2 [MEDIUM] 根因 B（合同）              ║
║  位置: contract → volume_btn.edge_dist.tol     ║
║  症状: Layer 1 通过但视觉位置偏差明显           ║
║  修复: 收紧 tol 3.0 → 1.5 → Layer 1 重跑      ║
║                                               ║
╠══════════════════════════════════════════════╣
║  修复优先级: #1 → #2（先修数据源再收紧约束）    ║
║  可自动修复: 否（根因 A 需人工搜集数据）         ║
╚══════════════════════════════════════════════╝
```
